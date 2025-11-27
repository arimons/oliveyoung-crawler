# 🛒 올리브영 크롤러 v4.0

올리브영 온라인몰에서 상품 정보와 리뷰를 수집하는 Python 크롤러입니다.

## ✨ 주요 기능

- ✅ **상품 정보 수집**: 상품명, 브랜드, 가격, 이미지 등
- ✅ **리뷰 수집**: Shadow DOM 지원으로 안정적인 리뷰 크롤링
- ✅ **실시간 수집**: 가상 스크롤 대응, 최신 리뷰 누락 방지
- ✅ **정확한 날짜 필터링**: 원하는 기간의 리뷰만 수집
- ✅ **Web UI**: 브라우저에서 편리하게 사용
- ✅ **CLI 모드**: 터미널에서 빠른 실행

## 🚀 빠른 시작 (Windows)

### 방법 1: 자동 설치 (권장)

1. `install.bat` 다운로드 및 실행
   - 자동으로 Git clone, 가상환경 생성, 패키지 설치
   - 바탕화면에 바로가기 생성

2. 바탕화면의 "Olive Young Crawler" 실행
   - 브라우저에서 `http://localhost:8000` 자동 접속

### 방법 2: 수동 설치

```bash
# 1. 저장소 클론
git clone https://github.com/arimons/oliveyoung-crawler.git
cd oliveyoung-crawler

# 2. 가상환경 생성 및 활성화
python -m venv venv
venv\Scripts\activate

# 3. 패키지 설치 (uv 사용 권장)
pip install uv
uv pip install -r requirements.txt

# 4. 서버 실행
python run_server.py
```

## 💻 사용 방법

### Web UI 모드 (권장)

```bash
# start_server.bat 실행 또는
python run_server.py
```

브라우저에서 `http://localhost:8000` 접속하여 사용

### CLI 모드

```bash
python main.py
```

대화형으로 검색어, 상품 개수, 저장 형식 등을 입력

## 📁 프로젝트 구조

```
oliveyoung-crawler/
├── backend/                 # FastAPI 백엔드
│   ├── api/                # API 라우트
│   ├── models/             # 데이터 모델
│   └── services/           # 크롤러 서비스
├── frontend/               # Web UI
│   ├── static/            # CSS, JS
│   └── templates/         # HTML
├── src/                    # 크롤러 핵심 로직
│   ├── crawler_selenium.py
│   ├── oliveyoung_crawler.py
│   ├── review_crawler.py
│   └── product_detail_crawler.py
├── data/                   # 수집 데이터 저장
├── chrome_profile/         # Chrome 프로필 (Cloudflare 우회)
├── main.py                 # CLI 진입점
├── run_server.py          # Web UI 진입점
├── start_server.bat       # 서버 실행 스크립트
└── requirements.txt       # 패키지 목록
```

## 🔧 v4.0 주요 개선사항

### 1. Shadow DOM 지원
- JavaScript 재귀 탐색으로 깊은 Shadow DOM 내 요소 탐지
- 정렬 버튼, 리뷰 아이템 안정적 접근

### 2. 실시간 리뷰 수집
- 스크롤 중 즉시 수집하여 가상 스크롤 대응
- 초기 리뷰 누락 문제 해결

### 3. 정확한 날짜 필터링
- `end_date` 도달 시 즉시 중단
- 불필요한 오래된 데이터 수집 방지

### 4. 중복 방지
- Set 기반 중복 체크
- 동일 리뷰 재수집 방지

## 📊 출력 데이터

### 상품 정보 (JSON)
```json
{
  "상품명": "라네즈 크림스킨 토너",
  "브랜드": "라네즈",
  "가격": "26,400원",
  "URL": "https://www.oliveyoung.co.kr/...",
  "수집시각": "2025-11-27 13:30:00"
}
```

### 리뷰 (TXT)
```
[2025.11.26]
정말 좋아요! 피부가 촉촉해졌어요.
--------------------------------------------------------------------------------

[2025.11.25]
재구매 의사 있습니다.
--------------------------------------------------------------------------------
```

## ⚙️ 필수 요구사항

- **Python**: 3.8 이상
- **Chrome**: 최신 버전
- **OS**: Windows (배치 파일), Mac/Linux (수동 설치)

## ⚠️ 주의사항

1. **Cloudflare**: 초기 접속 시 수동 검증 필요 (Chrome 프로필 저장으로 재사용)
2. **속도 제한**: 과도한 요청 시 IP 차단 가능
3. **웹사이트 변경**: 올리브영 구조 변경 시 업데이트 필요
4. **개인 용도**: 크롤링 데이터는 개인 학습/연구 목적으로만 사용

## 🐛 문제 해결

### 서버가 시작되지 않음
```bash
# 가상환경 활성화 확인
venv\Scripts\activate

# 패키지 재설치
uv pip install -r requirements.txt
```

### Cloudflare 검증 반복
- `chrome_profile/` 폴더 삭제 후 재시작
- 수동 검증 후 프로필 저장 확인

### 리뷰가 누락됨
- v4.0에서 대부분 해결됨
- 네트워크 지연 시 대기 시간 증가 필요

## 📝 변경 이력

- **v4.0** (2025-11-27): Shadow DOM 지원, 실시간 수집, Web UI 추가
- **v3.0**: 리뷰 크롤링 기능 추가
- **v2.0**: 상품 상세 정보 수집
- **v1.0**: 기본 검색 및 상품 목록 수집

## 📄 라이선스

개인 학습 및 연구 목적으로 제작되었습니다.

---

**Repository**: https://github.com/arimons/oliveyoung-crawler  
**Version**: 4.0.0  
**Last Updated**: 2025-11-27
