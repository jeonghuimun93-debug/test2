import pandas as pd
import numpy as np
import random

np.random.seed(42)
random.seed(42)

# ─── 기초 데이터 ───────────────────────────────────────────────
last_names  = ['김','이','박','최','정','강','조','윤','장','임','한','오','서','신','권','황','안','송','류','전','홍','고','문','양','손','배','백','허','유','엄']
male_firsts = ['민준','서준','도윤','예준','시우','주원','하준','지호','지후','준서','준우','현우','도현','지훈','건우','우진','선우','서진','민재','현준','태양','진우','성민','재원','동현','성준','지원','승현','현진','태민']
female_firsts=['서연','서윤','지우','서현','하윤','민서','하은','예은','수아','지아','채원','지민','수빈','다은','지현','은서','예린','지유','나은','수연','민지','소연','예지','지영','수진','은지','혜진','미래','소희','다혜']
departments  = ['DS부문 메모리사업부','DS부문 시스템LSI사업부','DS부문 파운드리사업부',
                'MX사업부 무선개발팀','MX사업부 SW개발팀','VD사업부','DA사업부',
                '선행기술연구원','종합기술원','삼성리서치','DX부문 AI센터','네트워크사업부']

chest_normal = ['정상', '이상 없음']
chest_c      = ['경미한 석회화 소견','흉막 비후 의심','경미한 폐결절 의심']
chest_d2     = ['폐결절 의심(추적관찰 필요)','결핵 반흔 의심','심비대 의심','폐문부 임파선 비대 의심']
hear_normal  = ['양측 정상','정상 범위']
hear_c       = ['우측 고음역 경도 난청','좌측 고음역 경도 난청','양측 고음역 경도 난청','우측 경도 난청','좌측 경도 난청']
hear_d2      = ['우측 중등도 난청','좌측 중등도 난청','양측 중등도 난청']

NAME_ROMAN = {
    '김':'k','이':'l','박':'p','최':'c','정':'j','강':'g','조':'j','윤':'y','장':'j','임':'i',
    '한':'h','오':'o','서':'s','신':'s','권':'k','황':'h','안':'a','송':'s','류':'r','전':'j',
    '홍':'h','고':'g','문':'m','양':'y','손':'s','배':'b','백':'b','허':'h','유':'y','엄':'e'
}
_used_knox: set = set()

def gen_knox(last_name: str) -> str:
    prefix = NAME_ROMAN.get(last_name, 's')
    while True:
        kid = prefix + str(random.randint(1000000, 9999999))
        if kid not in _used_knox:
            _used_knox.add(kid)
            return kid

def rn(m,s,lo,hi): return float(np.clip(np.random.normal(m,s),lo,hi))
def ri(m,s,lo,hi): return int(np.clip(np.random.normal(m,s),lo,hi))
def r1(x): return round(float(x),1)

# ─── 수치·판정 생성 함수 ───────────────────────────────────────
def gen(gender, htn, dm, dyslip, liver, obesity, kidney, hgb_ab, chest_ab, hear_ab,
        bp_severe=False, bmi_severe=False):

    # 혈압
    if bp_severe:
        sbp = ri(170,8,160,200); dbp = ri(104,5,100,120); htn='D2'
    elif htn=='D2':
        sbp = ri(148,6,140,159); dbp = ri(93,4,90,99)
    elif htn=='C':
        sbp = ri(133,3,130,139); dbp = ri(86,2,85,89)
    else:
        sbp = ri(118,10,90,129); dbp = ri(74,8,55,84)

    # 식전 혈당 / 당뇨
    if dm=='D2':   glucose = r1(rn(158,32,126,300))
    elif dm=='C':  glucose = r1(rn(112,8,100,125))
    else:          glucose = r1(rn(87,9,65,99))

    # 체질량지수 / 허리둘레 / 비만
    if bmi_severe:
        bmi=r1(rn(37.5,2,35,46)); obesity='D2'
        waist=r1(rn(110 if gender=='남' else 104,5,98,135))
    elif obesity=='D2':
        bmi=r1(rn(30.5,1.5,25,34.9))
        waist=r1(rn(95 if gender=='남' else 90,4,90 if gender=='남' else 85,115))
    elif obesity=='C':
        bmi=r1(rn(26.8,1,25,29.9))
        waist=r1(rn(87 if gender=='남' else 82,2,85 if gender=='남' else 80,89 if gender=='남' else 84))
    else:
        bmi=r1(rn(21.8,2.2,15.5,24.9))
        waist=r1(rn(78 if gender=='남' else 70,7,55,84 if gender=='남' else 79))

    # 간효소
    if liver=='D2':
        ast=ri(102,30,81,260); alt=ri(108,30,81,260); ggt=ri(125,40,81,380)
    elif liver=='C':
        ast=ri(58,10,41,80);   alt=ri(60,10,41,80);   ggt=ri(65,12,41,80)
    else:
        ast=ri(24,8,8,40);     alt=ri(21,7,5,40);      ggt=ri(27,10,8,40)

    # 지질
    if dyslip=='D2':
        tc=ri(260,18,240,340); tg=ri(235,65,200,700)
        hdl=ri(37 if gender=='남' else 44,5,25,50)
    elif dyslip=='C':
        tc=ri(218,10,200,239); tg=ri(168,14,150,199)
        hdl=ri(44 if gender=='남' else 52,5,35,60)
    else:
        tc=ri(182,20,120,199); tg=ri(108,28,40,149)
        hdl=ri(56 if gender=='남' else 65,10,40,90)
    ldl=int(np.clip(tc-hdl-tg/5,40,290))

    # 신장
    if kidney=='D2':
        creat=round(rn(1.78 if gender=='남' else 1.40,0.2,1.5 if gender=='남' else 1.2,3.2),2)
        up=random.choice(['2+','3+'])
    elif kidney=='C':
        creat=round(rn(1.37 if gender=='남' else 1.1,0.05,1.3 if gender=='남' else 1.0,1.49 if gender=='남' else 1.19),2)
        up=random.choice(['+','±'])
    else:
        creat=round(rn(0.94 if gender=='남' else 0.74,0.14,0.5,1.29 if gender=='남' else 0.99),2)
        up=np.random.choice(['-','±'],p=[0.93,0.07])

    # 혈색소
    if hgb_ab=='D2':
        hgb=r1(rn(9.5 if gender=='남' else 8.5,0.6,6.0,10.9 if gender=='남' else 9.9))
    elif hgb_ab=='C':
        hgb=r1(rn(12.0 if gender=='남' else 11.0,0.5,11.0 if gender=='남' else 10.0,12.9 if gender=='남' else 11.9))
    else:
        hgb=r1(rn(15.0 if gender=='남' else 13.2,1.0,13.0 if gender=='남' else 12.0,18.5 if gender=='남' else 16.5))

    # 흉부/청력
    cf = random.choice(chest_d2 if chest_ab=='D2' else chest_c if chest_ab=='C' else chest_normal)
    hd = random.choice(hear_d2  if hear_ab=='D2'  else hear_c  if hear_ab=='C'  else hear_normal)

    return dict(htn=htn,dm=dm,dyslip=dyslip,liver=liver,obesity=obesity,
                kidney=kidney,hgb_ab=hgb_ab,chest_ab=chest_ab,hear_ab=hear_ab,
                sbp=sbp,dbp=dbp,glucose=glucose,bmi=bmi,waist=waist,
                ast=ast,alt=alt,ggt=ggt,tc=tc,tg=tg,hdl=hdl,ldl=ldl,
                hgb=hgb,up=up,creat=creat,chest_finding=cf,hear_detail=hd)

# ─── TCG 35명 명시적 생성 ──────────────────────────────────────
pool = []

# 기준2: 혈압 수축기≥160 or 이완기≥100  → 12명
for _ in range(12):
    g   = random.choice(['남','남','남','여'])
    age = random.randint(38,58)
    dm_v      = random.choice(['','','C','D2'])
    dyslip_v  = random.choice(['','C','D2'])
    liver_v   = random.choice(['','','C'])
    obesity_v = random.choice(['','C','D2'])
    chest_v   = random.choice(['','','D2'])
    v = gen(g,'',dm_v,dyslip_v,liver_v,obesity_v,'','',chest_v,'',bp_severe=True)
    pool.append({'g':g,'age':age,**v})

# 기준3: 비만D2 + BMI≥35  → 8명
for _ in range(8):
    g   = random.choice(['남','남','여'])
    age = random.randint(30,55)
    htn_v    = random.choice(['','C','D2'])
    dm_v     = random.choice(['','C','D2'])
    dyslip_v = random.choice(['','C','D2'])
    liver_v  = random.choice(['','C'])
    v = gen(g,htn_v,dm_v,dyslip_v,liver_v,'D2','','','','',bmi_severe=True)
    pool.append({'g':g,'age':age,**v})

# 기준4: 당뇨·이상지질·간장·혈색소 중 D2가 3개  → 10명
for _ in range(10):
    g   = random.choice(['남','남','여'])
    age = random.randint(35,58)
    quad = random.sample(['dm','dyslip','liver','hgb'],3)
    htn_v    = random.choice(['','C'])
    obesity_v= random.choice(['','C','D2'])
    dm_v     = 'D2' if 'dm'     in quad else random.choice(['','C'])
    dyslip_v = 'D2' if 'dyslip' in quad else random.choice(['','C'])
    liver_v  = 'D2' if 'liver'  in quad else random.choice(['','C'])
    hgb_v    = 'D2' if 'hgb'   in quad else random.choice(['','C'])
    v = gen(g,htn_v,dm_v,dyslip_v,liver_v,obesity_v,'',hgb_v,'','')
    pool.append({'g':g,'age':age,**v})

# 기준1: 뇌심 최고위험군 (고혈압D2 + 당뇨D2)  → 5명
for _ in range(5):
    g   = random.choice(['남','남','여'])
    age = random.randint(42,58)
    dyslip_v = random.choice(['C','D2'])
    liver_v  = random.choice(['','C','D2'])
    obesity_v= random.choice(['','C'])
    v = gen(g,'D2','D2',dyslip_v,liver_v,obesity_v,'','','','')
    pool.append({'g':g,'age':age,**v})

# ─── 비TCG 865명 생성 ─────────────────────────────────────────
for _ in range(865):
    g   = random.choice(['남','남','남','여','여'])
    age = random.randint(26,61)

    # 혈압: 최대 D2 mild (140-159/90-99), SBP<160 보장
    r=random.random()
    htn_v = 'D2' if r<0.09 else 'C' if r<0.22 else ''

    # 당뇨: 고혈압D2와 동시 D2 금지 (기준1 방지)
    r=random.random()
    if r<0.04:
        dm_v = 'C' if htn_v=='D2' else 'D2'
    elif r<0.14:
        dm_v = 'C'
    else:
        dm_v = ''

    r=random.random()
    dyslip_v = 'D2' if r<0.09 else 'C' if r<0.22 else ''

    r=random.random()
    liver_v  = 'D2' if r<0.07 else 'C' if r<0.20 else ''

    r=random.random()
    hgb_v    = 'D2' if r<0.02 else 'C' if r<0.07 else ''

    # 기준4 방지: 당뇨·이상지질·간장·혈색소 D2가 3개 이상이면 하나 C로 내림
    metabolic = [dm_v,dyslip_v,liver_v,hgb_v]
    if metabolic.count('D2') >= 3:
        idxs = [i for i,x in enumerate(metabolic) if x=='D2']
        metabolic[random.choice(idxs)] = 'C'
        dm_v,dyslip_v,liver_v,hgb_v = metabolic

    r=random.random()
    obesity_v= 'D2' if r<0.12 else 'C' if r<0.32 else ''
    # 비만D2여도 BMI<35 보장 → bmi_severe=False

    r=random.random()
    kidney_v = 'D2' if r<0.025 else 'C' if r<0.07 else ''

    r=random.random()
    chest_v  = 'D2' if r<0.05 else 'C' if r<0.13 else ''

    r=random.random()
    hear_v   = 'D2' if r<0.03 else 'C' if r<0.13 else ''

    v = gen(g,htn_v,dm_v,dyslip_v,liver_v,obesity_v,kidney_v,hgb_v,chest_v,hear_v)
    pool.append({'g':g,'age':age,**v})

random.shuffle(pool)

# ─── DataFrame 조립 ───────────────────────────────────────────
rows=[]
for d in pool:
    g   = d['g']
    age = d['age']
    svc  = max(1, min(age-25+random.randint(-2,4), 35))
    last = random.choice(last_names)
    name = last + (random.choice(male_firsts) if g=='남' else random.choice(female_firsts))
    knox = gen_knox(last)
    dept = random.choice(departments)

    # 확진대상 Y: 고혈압·당뇨·이상지질혈증·간장질환·신장질환 중 D2
    confirmed = 'Y' if any([d['htn']=='D2',d['dm']=='D2',d['dyslip']=='D2',
                             d['liver']=='D2',d['kidney']=='D2']) else 'N'

    all_cls=[d['htn'],d['dm'],d['dyslip'],d['liver'],d['obesity'],
             d['kidney'],d['hgb_ab'],d['chest_ab'],d['hear_ab']]
    d2n = all_cls.count('D2')

    if d2n>=2: measure='9'
    elif d2n==1: measure='4'
    elif 'C' in all_cls: measure='1'
    else: measure='1'

    verdict=', '.join(c for c in all_cls if c) or '정상'

    rows.append({
        '확진대상': confirmed,
        '부서': dept, '성명': name, 'Knox ID': knox, '성별': g, '연령': age, '근속년수': svc,
        '고혈압': d['htn'], '당뇨': d['dm'], '이상지질혈증': d['dyslip'],
        '간장질환': d['liver'], '비만': d['obesity'], '신장질환': d['kidney'],
        '혈색소 이상': d['hgb_ab'], '흉부 질환': d['chest_ab'], '청력': d['hear_ab'],
        '혈압': f"{d['sbp']}/{d['dbp']}",
        '식전 혈당': d['glucose'], '허리 둘레': d['waist'], '체질량 지수': d['bmi'],
        'AST': d['ast'], 'ALT': d['alt'], '감마지티피': d['ggt'],
        '총콜레스테롤': d['tc'], '중성지방': d['tg'], 'HDL': d['hdl'], 'LDL': d['ldl'],
        '혈색소': d['hgb'], '요단백': d['up'], '혈청크레아티닌': d['creat'],
        '흉부 방사선 판독 소견': d['chest_finding'], '청력 상세': d['hear_detail'],
        '조치 사항': measure, '판정 합': verdict,
    })

df = pd.DataFrame(rows)
df.to_excel('/Users/jeonghui/dev/test2/samsung_health_raw_data.xlsx', index=False, engine='openpyxl')

# ─── 검증 출력 ────────────────────────────────────────────────
tcg=0
reasons=[]
for d in pool:
    c1 = d['htn']=='D2' and d['dm']=='D2'
    c2 = d['sbp']>=160 or d['dbp']>=100
    c3 = d['bmi']>=35 and d['obesity']=='D2'
    c4 = sum([d['dm']=='D2',d['dyslip']=='D2',d['liver']=='D2',d['hgb_ab']=='D2'])>=3
    if c1 or c2 or c3 or c4:
        tcg+=1
        r=[]
        if c1: r.append('뇌심최고위험군')
        if c2: r.append(f"혈압{d['sbp']}/{d['dbp']}")
        if c3: r.append(f"비만BMI{d['bmi']}")
        if c4: r.append('유소견3개')
        reasons.append('/'.join(r))

print(f"총 {len(df)}명 생성 완료")
print(f"TCG 해당자: {tcg}명")
print(f"확진대상 Y: {(df['확진대상']=='Y').sum()}명")
print(f"확진대상 N: {(df['확진대상']=='N').sum()}명")
print()
print("── 질환별 현황 ──")
for col in ['고혈압','당뇨','이상지질혈증','간장질환','비만','신장질환','혈색소 이상','흉부 질환','청력']:
    d2=(df[col]=='D2').sum(); c=(df[col]=='C').sum()
    print(f"  {col}: D2={d2}, C={c}")
print()
print("── TCG 사유 분포 ──")
from collections import Counter
for k,v in Counter(reasons).most_common():
    print(f"  {k}: {v}명")
