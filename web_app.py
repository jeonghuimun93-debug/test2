"""
삼성전자 R&D센터 부속의원 — TCG 자동 분류 및 메일 발송 웹 서비스
실행: python3 web_app.py  →  http://localhost:5001
"""

from flask import Flask, render_template, request, jsonify
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import io

app = Flask(__name__)

# ── TCG 분류 ──────────────────────────────────────────────────

def parse_bp(s):
    try:
        a, b = str(s).split('/')
        return int(a.strip()), int(b.strip())
    except Exception:
        return 0, 0


def classify(row: dict) -> list:
    sbp, dbp = parse_bp(row.get('혈압', ''))
    bmi = float(row.get('체질량 지수') or 0)

    def d2(c): return str(row.get(c) or '').strip() == 'D2'

    g = []
    if d2('고혈압') and d2('당뇨'):                                          g.append('뇌심최고위험군')
    if sbp >= 160 or dbp >= 100:                                             g.append('중증고혈압')
    if d2('비만') and bmi >= 35:                                             g.append('중증비만')
    if sum(map(d2, ['당뇨', '이상지질혈증', '간장질환', '혈색소 이상'])) >= 3: g.append('복합유소견')
    return g


# ── 메일 생성 ──────────────────────────────────────────────────

PRIORITY = ['뇌심최고위험군', '중증고혈압', '중증비만', '복합유소견']
SUBJECTS = {
    '뇌심최고위험군': '[부속의원 긴급] 뇌심혈관질환 최고위험군 건강관리 안내',
    '중증고혈압':     '[부속의원] 중증 고혈압 집중관리 대상자 안내',
    '중증비만':       '[부속의원] 고도비만 집중관리 대상자 안내',
    '복합유소견':     '[부속의원] 복합 유소견 집중관리 대상자 안내',
}


def get_subject(groups):
    for p in PRIORITY:
        if p in groups:
            return SUBJECTS[p]
    return '[부속의원] TCG 건강관리 안내'


def sv(row, col):
    v = row.get(col)
    return str(v) if v not in (None, '', 'nan', 'None') else '-'


def build_email(row: dict, groups: list) -> str:
    name  = sv(row, '성명')
    today = datetime.now().strftime('%Y년 %m월 %d일')

    result = f"""\
┌─────────────────────────────────────────┐
│            개인 검진 결과 요약              │
└─────────────────────────────────────────┘
  혈      압 : {sv(row,'혈압')} mmHg
  공복혈당   : {sv(row,'식전 혈당')} mg/dL
  BMI        : {sv(row,'체질량 지수')} kg/m²
  허리둘레   : {sv(row,'허리 둘레')} cm
  총콜레스테롤: {sv(row,'총콜레스테롤')} mg/dL  |  중성지방: {sv(row,'중성지방')} mg/dL
  HDL : {sv(row,'HDL')}  |  LDL : {sv(row,'LDL')}
  AST : {sv(row,'AST')}  |  ALT : {sv(row,'ALT')}  |  γ-GTP : {sv(row,'감마지티피')}
  혈색소     : {sv(row,'혈색소')} g/dL
  판    정   : {sv(row,'판정 합')}
"""
    guides = []

    if '뇌심최고위험군' in groups:
        guides.append("""
◈ 뇌심혈관질환 최고위험군 관리 안내
─────────────────────────────────────────────────
고혈압(D2)과 당뇨(D2)가 동반 확진되어 뇌졸중·심근경색 위험이
일반인 대비 최대 10배 이상 높은 최고위험군으로 분류되었습니다.

  1. 혈압약·혈당약을 매일 빠짐없이 규칙적으로 복용하세요.
  2. 가능한 빠른 시일 내 부속의원 방문 상담을 받으세요.
  3. 목표 혈압: 130/80 mmHg 이하 / 목표 공복혈당: 100 mg/dL 이하
  4. 저염식이(하루 소금 5g 이하), 금연, 절주를 반드시 실천하세요.
  5. 주 3회 이상, 1회 30분 유산소 운동을 권장합니다.
  6. 어지러움·두통·가슴 통증 시 즉시 부속의원을 방문하세요.
""")

    if '중증고혈압' in groups:
        guides.append(f"""
◈ 중증 고혈압 집중관리 안내
─────────────────────────────────────────────────
현재 혈압({sv(row,'혈압')} mmHg)이 중증 고혈압 기준에 해당합니다.
(기준: 수축기 160 이상 또는 이완기 100 이상)

  1. 즉시 전문의 진료로 혈압약 처방을 확인·시작하세요.
  2. 매일 같은 시간(아침·저녁) 자가 혈압을 측정·기록하세요.
  3. 고염식이·과음·흡연을 즉시 중단하세요.
  4. 갑작스러운 두통·어지러움·시야 이상 시 즉시 응급실을 방문하세요.
  5. 혈압 안정 전까지 격렬한 운동은 제한하세요.
""")

    if '중증비만' in groups:
        guides.append(f"""
◈ 고도비만 집중관리 안내
─────────────────────────────────────────────────
현재 BMI({sv(row,'체질량 지수')} kg/m²)가 고도비만 기준(35 이상)에 해당합니다.

  1. 부속의원 영양상담 프로그램 참여를 적극 권장합니다.
  2. 주 0.5~1 kg 이내 점진적 체중 감량 목표를 설정하세요.
  3. 탄수화물·지방을 줄이고 단백질·채소 위주 식단을 유지하세요.
  4. 걷기·수영 등 저강도 유산소 운동부터 시작하세요.
  5. 현재 체중의 5~10% 감량만으로도 합병증 위험이 크게 감소합니다.
""")

    if '복합유소견' in groups:
        d2s = [k for c, k in [('당뇨','당뇨'),('이상지질혈증','이상지질혈증'),
                               ('간장질환','간장질환'),('혈색소 이상','혈색소 이상(빈혈)')]
               if str(row.get(c, '')).strip() == 'D2']
        guides.append(f"""
◈ 복합 유소견 집중관리 안내
─────────────────────────────────────────────────
복합 질환({', '.join(d2s)})이 동반 진단되어 통합적 건강관리가 필요합니다.

  1. 각 질환별 전문의 진료 및 처방 약물을 성실히 복용하세요.
  2. 정기 추적 혈액검사(3~6개월 간격)를 시행하세요.
  3. 음주는 간장질환·혈당 악화의 주요 원인입니다. 절주·금주하세요.
  4. 철분·단백질 풍부한 식단으로 빈혈 예방에 힘쓰세요.
  5. 부속의원에서 복합 질환 통합 관리 상담을 받으시기 바랍니다.
""")

    return f"""\
안녕하세요, {name} 님.
삼성전자 R&D센터 부속의원입니다.

{today} 건강검진 결과 분석을 통해 {name} 님께서는
건강 집중관리 대상(TCG: Total Care Group)으로 선정되었습니다.
아래 내용을 확인하시고 건강관리에 적극 임해 주시기 바랍니다.

{result}
{''.join(guides)}
═══════════════════════════════════════════════════
■ 부속의원 방문 및 문의
  위  치 : ○○동 ○층 부속의원
  진  료 : 평일 08:30 ~ 17:30
  내  선 : ○○○○
─────────────────────────────────────────────────
본 메일은 임직원 건강관리 목적으로 자동 발송된 안내 메일입니다.
건강한 직장생활을 위해 부속의원이 함께하겠습니다.
═══════════════════════════════════════════════════

삼성전자 R&D센터 부속의원 드림"""


# ── API ────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/classify', methods=['POST'])
def api_classify():
    if 'file' not in request.files:
        return jsonify({'error': '파일을 선택해주세요'}), 400

    try:
        df = pd.read_excel(io.BytesIO(request.files['file'].read()))
    except Exception as e:
        return jsonify({'error': f'파일 읽기 오류: {e}'}), 400

    tcg = []
    for _, row in df.iterrows():
        rd = {k: (None if (isinstance(v, float) and pd.isna(v)) else v)
              for k, v in row.to_dict().items()}
        groups = classify(rd)
        if not groups:
            continue
        knox = str(rd.get('Knox ID') or '').strip()
        tcg.append({
            'name':    str(rd.get('성명', '')),
            'dept':    str(rd.get('부서', '')),
            'age':     int(rd.get('연령') or 0),
            'gender':  str(rd.get('성별', '')),
            'knox':    knox,
            'email':   f'{knox}@samsung.com',
            'groups':  groups,
            'bp':      sv(rd, '혈압'),
            'glucose': sv(rd, '식전 혈당'),
            'bmi':     sv(rd, '체질량 지수'),
            'verdict': sv(rd, '판정 합'),
            'data':    {k: (str(v) if v is not None else '-') for k, v in rd.items()},
        })

    from collections import Counter
    gc = Counter(g for t in tcg for g in t['groups'])
    return jsonify({
        'total':        len(df),
        'tcg_count':    len(tcg),
        'group_counts': dict(gc),
        'list':         tcg,
    })


@app.route('/api/preview', methods=['POST'])
def api_preview():
    d = request.json
    return jsonify({
        'subject': get_subject(d.get('groups', [])),
        'body':    build_email(d.get('data', {}), d.get('groups', [])),
    })


@app.route('/api/send', methods=['POST'])
def api_send():
    d       = request.json
    targets = d.get('targets', [])
    cfg     = d.get('smtp', {})

    results = []
    try:
        srv = smtplib.SMTP(cfg['server'], int(cfg['port']))
        if cfg.get('use_tls'):
            srv.starttls()
        srv.login(cfg['sender'], cfg['password'])

        for t in targets:
            try:
                subj = get_subject(t['groups'])
                body = build_email(t['data'], t['groups'])
                msg  = MIMEMultipart()
                msg['Subject'] = subj
                msg['From']    = cfg['sender']
                msg['To']      = t['email']
                msg.attach(MIMEText(body, 'plain', 'utf-8'))
                srv.sendmail(cfg['sender'], t['email'], msg.as_string())
                results.append({'name': t['name'], 'email': t['email'], 'ok': True})
            except Exception as e:
                results.append({'name': t['name'], 'email': t['email'], 'ok': False, 'error': str(e)})

        srv.quit()
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'results': results})


if __name__ == '__main__':
    print('\n' + '='*55)
    print('  삼성전자 R&D센터 부속의원 — TCG 분류 시스템')
    print('  브라우저에서 http://localhost:5001 로 접속하세요')
    print('='*55 + '\n')
    app.run(debug=False, port=5001)
