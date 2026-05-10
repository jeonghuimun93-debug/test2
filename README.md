# 근로자 건강검진 Total Care Group 분류 프로젝트

약 3,000명 근로자의 건강검진 데이터를 기반으로 Total Care Group을 분류하는 프로젝트입니다.
하네스 엔지니어링 방법론을 활용하여 구축합니다.

## 목표

- 근로자 건강검진 데이터 분석 및 그룹 분류
- Total Care Group 기준에 따른 위험도 분류 체계 구축

## 진행 예정

- [ ] 데이터 형식 및 항목 확인
- [ ] Total Care Group 분류 기준 정의
- [ ] 하네스 엔지니어링 기반 파이프라인 설계
- [ ] 분류 로직 구현
- [ ] 결과 리포트/시각화

## Netlify 배포

이 프로젝트는 Flask 앱을 Netlify Functions로 실행하도록 설정되어 있습니다.

### 1) 로컬 실행 확인

```bash
python3 web_app.py
```

브라우저에서 `http://localhost:5001` 접속이 되면 정상입니다.

### 2) Netlify 연동

프로젝트 루트에서:

```bash
netlify init
```

또는 Netlify 웹 UI에서 저장소를 연결해도 됩니다.

### 3) 배포

```bash
netlify deploy --prod
```

배포 시 `netlify.toml` 기준으로 아래가 자동 적용됩니다.
- Python 의존성 설치: `requirements.txt`
- 함수 엔트리포인트: `netlify/functions/app.py`
- 모든 경로를 Flask 앱으로 라우팅
