"""
삼성전자 R&D센터 부속의원
TCG (Total Care Group) 자동 분류 및 메일 발송 시스템
"""

import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from collections import Counter
import sys
import os

# ════════════════════════════════════════════════════════════════
#  ★ 사용 전 반드시 아래 설정값을 수정하세요
# ════════════════════════════════════════════════════════════════
SMTP_SERVER  = "smtp.samsung.com"       # 사내 SMTP 서버 주소
SMTP_PORT    = 587                      # 포트 (STARTTLS: 587 / SSL: 465)
USE_TLS      = True                     # STARTTLS 사용 여부

SENDER_EMAIL = "nurse@samsung.com"      # 발신자 이메일 (본인 메일로 변경)
SENDER_PASS  = ""                       # 발신자 비밀번호

EXCEL_PATH   = "samsung_health_raw_data.xlsx"   # 건강검진 로우데이터 파일

# True  → 발송 없이 선별 결과·샘플 메일 미리보기만
# False → 확인 후 실제 발송
DRY_RUN = True
# ════════════════════════════════════════════════════════════════


# ── TCG 기준 분류 ─────────────────────────────────────────────

def parse_bp(bp_str):
    """'수축기/이완기' 문자열 파싱"""
    try:
        s, d = str(bp_str).split('/')
        return int(s.strip()), int(d.strip())
    except Exception:
        return 0, 0


def classify_tcg(row) -> list[str]:
    """
    TCG 해당 기준 목록 반환 (해당 없으면 빈 리스트)

    기준① 뇌심최고위험군 : 고혈압 D2 + 당뇨 D2
    기준② 중증고혈압     : 수축기 ≥ 160 or 이완기 ≥ 100
    기준③ 중증비만       : 비만 D2 + BMI ≥ 35
    기준④ 복합유소견     : 당뇨·이상지질혈증·간장질환·혈색소이상 중 D2 ≥ 3개
    """
    sbp, dbp = parse_bp(row.get('혈압', '0/0'))
    bmi = float(row.get('체질량 지수') or 0)

    def v(col):
        return str(row.get(col) or '').strip()

    groups = []

    if v('고혈압') == 'D2' and v('당뇨') == 'D2':
        groups.append('뇌심최고위험군')

    if sbp >= 160 or dbp >= 100:
        groups.append('중증고혈압')

    if v('비만') == 'D2' and bmi >= 35:
        groups.append('중증비만')

    if sum([v('당뇨') == 'D2', v('이상지질혈증') == 'D2',
            v('간장질환') == 'D2', v('혈색소 이상') == 'D2']) >= 3:
        groups.append('복합유소견')

    return groups


# ── 이메일 제목 ────────────────────────────────────────────────

PRIORITY = ['뇌심최고위험군', '중증고혈압', '중증비만', '복합유소견']

SUBJECT_MAP = {
    '뇌심최고위험군': '[부속의원 긴급] 뇌심혈관질환 최고위험군 건강관리 안내',
    '중증고혈압':     '[부속의원] 중증 고혈압 집중관리 대상자 안내',
    '중증비만':       '[부속의원] 고도비만 집중관리 대상자 안내',
    '복합유소견':     '[부속의원] 복합 유소견 집중관리 대상자 안내',
}

def get_subject(groups: list[str]) -> str:
    for p in PRIORITY:
        if p in groups:
            return SUBJECT_MAP[p]
    return "[부속의원] TCG 건강관리 안내"


# ── 이메일 본문 생성 ───────────────────────────────────────────

def build_email(row, groups: list[str]) -> str:
    name    = row.get('성명', '')
    sbp, dbp = parse_bp(row.get('혈압', '0/0'))
    today   = datetime.now().strftime('%Y년 %m월 %d일')

    def v(col): return row.get(col, '-') if pd.notna(row.get(col)) else '-'

    # ── 개인 검진 결과 블록
    result_block = f"""\
┌─────────────────────────────────────────┐
│            개인 검진 결과 요약              │
└─────────────────────────────────────────┘
  혈      압 : {v('혈압')} mmHg
  공복혈당   : {v('식전 혈당')} mg/dL
  BMI        : {v('체질량 지수')} kg/m²
  허리둘레   : {v('허리 둘레')} cm
  총콜레스테롤: {v('총콜레스테롤')} mg/dL  |  중성지방 : {v('중성지방')} mg/dL
  HDL : {v('HDL')}  |  LDL : {v('LDL')}
  AST : {v('AST')}  |  ALT : {v('ALT')}  |  γ-GTP : {v('감마지티피')}
  혈색소     : {v('혈색소')} g/dL
  판    정   : {v('판정 합')}
"""

    # ── 그룹별 관리 지침
    guide_blocks = []

    if '뇌심최고위험군' in groups:
        guide_blocks.append(f"""\
◈ 뇌심혈관질환 최고위험군 관리 안내
─────────────────────────────────────────────────
고혈압(D2)과 당뇨(D2)가 동반 확진되어 뇌졸중·심근경색 위험이
일반인 대비 최대 10배 이상 높은 최고위험군으로 분류되었습니다.

  1. 혈압약 및 혈당약을 매일 빠짐없이 규칙적으로 복용하세요.
  2. 가능한 빠른 시일 내 부속의원을 방문하여 상담을 받으세요.
  3. 목표 혈압 : 130/80 mmHg 이하 유지
     목표 공복혈당 : 100 mg/dL 이하 유지
  4. 저염식이(하루 소금 5g 이하), 금연, 절주를 반드시 실천하세요.
  5. 주 3회 이상, 1회 30분 유산소 운동을 권장합니다.
  6. 어지러움·두통·가슴 통증 발생 시 즉시 부속의원을 방문하세요.

""")

    if '중증고혈압' in groups:
        guide_blocks.append(f"""\
◈ 중증 고혈압 집중관리 안내
─────────────────────────────────────────────────
현재 혈압({v('혈압')} mmHg)이 중증 고혈압 기준
(수축기 160 이상 또는 이완기 100 이상)에 해당합니다.

  1. 즉시 전문의 진료를 통해 혈압약 처방을 확인·시작하세요.
  2. 매일 같은 시간(아침·저녁) 자가 혈압 측정 후 기록하세요.
  3. 고염식이·과음·흡연을 즉시 중단하세요.
  4. 갑작스러운 두통, 어지러움, 시야 이상 시 즉시 응급실을 방문하세요.
  5. 혈압이 안정될 때까지 격렬한 운동은 제한하세요.

""")

    if '중증비만' in groups:
        guide_blocks.append(f"""\
◈ 고도비만 집중관리 안내
─────────────────────────────────────────────────
현재 BMI({v('체질량 지수')} kg/m²)가 고도비만 기준(35 이상)에 해당합니다.
고도비만은 당뇨·고혈압·이상지질혈증·관절 질환·수면 무호흡 등
다양한 합병증을 유발합니다.

  1. 부속의원 영양상담 프로그램 참여를 적극 권장합니다.
  2. 주 0.5~1 kg 이내의 점진적 체중 감량 목표를 설정하세요.
  3. 탄수화물·지방 섭취를 줄이고 단백질·채소 위주 식단을 유지하세요.
  4. 걷기·수영 등 관절 부담이 적은 저강도 유산소 운동부터 시작하세요.
  5. 현재 체중의 5~10% 감량만으로도 합병증 위험이 크게 감소합니다.

""")

    if '복합유소견' in groups:
        d2_list = []
        if str(row.get('당뇨') or '').strip() == 'D2':        d2_list.append('당뇨')
        if str(row.get('이상지질혈증') or '').strip() == 'D2': d2_list.append('이상지질혈증')
        if str(row.get('간장질환') or '').strip() == 'D2':    d2_list.append('간장질환')
        if str(row.get('혈색소 이상') or '').strip() == 'D2': d2_list.append('혈색소 이상(빈혈)')
        cond_str = ', '.join(d2_list)
        guide_blocks.append(f"""\
◈ 복합 유소견 집중관리 안내
─────────────────────────────────────────────────
복합 질환({cond_str})이 동반 진단되어
통합적 건강관리가 필요합니다.

  1. 각 질환별 전문의 진료 및 처방 약물을 성실히 복용하세요.
  2. 정기적인 추적 혈액검사(3~6개월 간격)를 시행하세요.
  3. 음주는 간장질환 및 혈당 악화의 주요 원인입니다. 절주·금주하세요.
  4. 철분·단백질이 풍부한 식단으로 빈혈 예방에 힘쓰세요.
  5. 부속의원에서 복합 질환 통합 관리 상담을 받으시기 바랍니다.

""")

    body = f"""\
안녕하세요, {name} 님.
삼성전자 R&D센터 부속의원입니다.

{today} 건강검진 결과 분석을 통해 {name} 님께서는
건강 집중관리 대상(TCG: Total Care Group)으로 선정되었습니다.
아래 내용을 확인하시고 건강관리에 적극 임해 주시기 바랍니다.

{result_block}
{''.join(guide_blocks)}\
═══════════════════════════════════════════════════
■ 부속의원 방문 및 문의
  위  치 : ○○동 ○층 부속의원
  진  료 : 평일 08:30 ~ 17:30
  내  선 : ○○○○
─────────────────────────────────────────────────
본 메일은 임직원 건강관리 목적으로 발송된 자동 안내 메일입니다.
건강한 직장생활을 위해 부속의원이 함께하겠습니다.
═══════════════════════════════════════════════════

삼성전자 R&D센터 부속의원 드림
"""
    return body


# ── 메일 발송 ──────────────────────────────────────────────────

def send_one(server, sender, to_addr, subject, body):
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From']    = sender
    msg['To']      = to_addr
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    server.sendmail(sender, to_addr, msg.as_string())


# ── 메인 ───────────────────────────────────────────────────────

def main():
    SEP = '=' * 64

    print(SEP)
    print('  삼성전자 R&D센터 부속의원')
    print('  TCG 자동 분류 및 메일 발송 시스템')
    print(SEP)

    # 1. 엑셀 로드
    print(f'\n📂 데이터 로딩: {EXCEL_PATH}')
    if not os.path.exists(EXCEL_PATH):
        print(f'❌ 파일 없음: {EXCEL_PATH}')
        sys.exit(1)

    df = pd.read_excel(EXCEL_PATH)
    print(f'   총 {len(df):,}명 로드 완료\n')

    # 2. TCG 분류
    targets = []
    for _, row in df.iterrows():
        groups = classify_tcg(row)
        if groups:
            knox = str(row.get('Knox ID', '') or '').strip()
            targets.append({
                'row':    row,
                'groups': groups,
                'email':  f'{knox}@samsung.com',
            })

    print(f'✅ TCG 선별 완료 : {len(targets)}명\n')

    # 3. 그룹별 집계
    gc = Counter(g for t in targets for g in t['groups'])
    label_map = {
        '뇌심최고위험군': '기준① 뇌심 최고위험군',
        '중증고혈압':     '기준② 중증 고혈압',
        '중증비만':       '기준③ 중증 비만 (BMI≥35)',
        '복합유소견':     '기준④ 복합 유소견 3개 이상',
    }
    print('── TCG 그룹별 인원 ────────────────────────────────────')
    for p in PRIORITY:
        if p in gc:
            print(f'   {label_map[p]}: {gc[p]}명')

    # 4. 발송 대상 목록
    print('\n── 발송 대상 목록 ─────────────────────────────────────')
    for i, t in enumerate(targets, 1):
        r   = t['row']
        grp = ' / '.join(t['groups'])
        print(f"  {i:2d}. {str(r.get('성명','')):<6s}  "
              f"{str(r.get('부서','')):<22s}  "
              f"{t['email']:<32s}  [{grp}]")

    print()

    # 5. DRY RUN 모드
    if DRY_RUN:
        print('⚠️  DRY_RUN = True  →  미리보기 모드 (실제 발송 없음)')
        print('   실제 발송하려면 파일 상단의 DRY_RUN = False 로 변경하세요.\n')
        if targets:
            s = targets[0]
            print('── 샘플 메일 미리보기 (1번 대상자) ───────────────────')
            print(f"수신 : {s['email']}")
            print(f"제목 : {get_subject(s['groups'])}")
            print('─' * 60)
            print(build_email(s['row'], s['groups']))
        return

    # 6. 실제 발송
    if not SENDER_EMAIL or not SENDER_PASS:
        print('❌ SENDER_EMAIL / SENDER_PASS 를 설정해주세요.')
        sys.exit(1)

    ans = input(f'📨 {len(targets)}명에게 메일을 발송하시겠습니까? (yes 입력 시 발송): ')
    if ans.strip().lower() != 'yes':
        print('발송이 취소되었습니다.')
        return

    print('\n📨 메일 발송 시작...\n')
    ok, fail_list, logs = 0, [], []

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        if USE_TLS:
            server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASS)

        for t in targets:
            name = t['row'].get('성명', '')
            try:
                subject = get_subject(t['groups'])
                body    = build_email(t['row'], t['groups'])
                send_one(server, SENDER_EMAIL, t['email'], subject, body)
                print(f"  ✅ {name:<6s} → {t['email']}")
                logs.append(f"OK   | {name} | {t['email']} | {','.join(t['groups'])}")
                ok += 1
            except Exception as e:
                print(f"  ❌ {name:<6s} → 실패: {e}")
                logs.append(f"FAIL | {name} | {t['email']} | {e}")
                fail_list.append(name)

        server.quit()

    except Exception as e:
        print(f'\n❌ SMTP 연결 실패: {e}')
        return

    # 7. 로그 저장
    ts       = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_path = f'tcg_mail_log_{ts}.txt'
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write(f'발송일시 : {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
        f.write(f'성공 : {ok}건 / 실패 : {len(fail_list)}건\n\n')
        f.write('\n'.join(logs))

    print(f'\n{SEP}')
    print(f'  ✅ 발송 완료  성공 {ok}건 / 실패 {len(fail_list)}건')
    if fail_list:
        print(f'  ❌ 실패 대상: {", ".join(fail_list)}')
    print(f'  📄 로그 저장: {log_path}')
    print(SEP)


if __name__ == '__main__':
    main()
