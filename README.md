# 🛒 올리브영 상품 크롤러 & AI 분석기 v4.2

올리브영 온라인몰에서 **상품 상세 정보와 이미지를 자동으로 수집**하고, **AI를 활용하여 리뷰와 이미지를 분석**하는 올인원 도구입니다.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)
![Selenium](https://img.shields.io/badge/Selenium-4.18+-yellow.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-orange.svg)

## ✨ 주요 기능

### 1. 강력한 크롤링 엔진 (True Hybrid Engine)
- **True Hybrid API 수집**: 브라우저 컨텍스트 내에서 직접 API를 호출하여 **403 Forbidden 에러를 완벽하게 우회**하고 초고속으로 리뷰를 수집
- **자동 레이아웃 감지 & 캐싱**: 구형(Legacy) 및 신형(New) 페이지 레이아웃을 자동으로 인식하고 캐싱하여 중복 연산 방지
- **스마트 이미지 병합**: 상세 페이지의 긴 이미지들을 분석하여 최적의 비율로 자동 병합 (65,000px 자동 분할 기술 적용)
- **지능형 서버 로딩**: 무거운 AI 라이브러리를 지연 로딩(Lazy Loading)하여 서버 초기 시작 속도를 300% 이상 향상

### 2. 다양한 수집 모드
- **🔗 URL 직접 입력**: 상품 페이지 URL로 즉시 크롤링
- **🚀 병렬 크롤링**: 최대 5개의 URL을 동시에 고속으로 수집
- **🔍 키워드 검색**: 상품명 검색으로 상위 상품 자동 수집
- **📝 리뷰 전용 모드**: 상세 이미지는 건너뛰고 리뷰 데이터와 썸네일만 빠르게 수집

### 3. 개선된 히스토리 및 병합 로직
- **똑똑한 중복 병합**: 동일 상품의 여러 수집 결과가 있을 때, **최신 리뷰 데이터와 과거의 이미지/분석 결과**를 유실 없이 하나로 결합
- **실시간 진행 상황**: 크롤링 진행률과 상세 로그를 대시보드에서 즉시 확인
- **히스토리 갤러리**: 수집된 상품들을 썸네일과 함께 직관적으로 관리

### 4. AI 분석 (Advanced)
- **리뷰 요약**: 수집된 리뷰를 AI가 분석하여 장단점 및 핵심 요약 제공
- **이미지 분석**: 상품 상세 이미지를 분석하여 마케팅 포인트 추출
- **GPT-4o / GPT-5(o1) 지원**: 최신 추론형 모델까지 완벽 대응
- **자동 전처리**: [YYYY.MM.DD] 날짜 태그 및 구분선 자동 제거로 토큰 효율 극대화

## 🚀 설치 및 실행

### 1. 필수 요구사항
- Python 3.10 이상
- Chrome 브라우저 (최신 버전)

### 2. 설치
```bash
# 저장소 클론
git clone https://github.com/your-repo/oliveyoung-crawler.git
cd oliveyoung-crawler

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 3. 실행
```bash
# 윈도우
start_server.bat

# 맥/리눅스
python run_server.py
```
브라우저에서 `http://127.0.0.1:8000`으로 접속하세요.

## 📖 사용 가이드

### 기본 크롤링
1. **URL 직접 입력** 탭 선택
2. 올리브영 상품 URL 붙여넣기 (자동으로 `goodsNo`만 추출하여 최적화됨)
3. **상세 정보 추출** 버튼 클릭

### 병렬 크롤링
1. **다중 URL (병렬)** 탭 선택
2. 여러 상품 URL 입력 (최대 5개)
3. 동시 실행 수 조절 후 **병렬 추출 시작** 클릭

### AI 분석 사용하기
1. **AI 리뷰/이미지 분석** 탭으로 이동
2. OpenAI API Key 입력 및 모델 선택
3. 분석할 상품 선택 후 **리뷰 분석** 또는 **이미지 분석** 클릭

## 📁 데이터 저장 구조
```
data/
└── [날짜]_[상품명]/
    ├── product_info.json        # 상품 상세 정보 (가격, 성분, 평점 등)
    ├── product_info.csv         # 데이터 분석용 CSV
    ├── reviews.txt              # 수집된 리뷰 텍스트
    ├── thumbnail.jpg            # 상품 썸네일
    ├── product_detail_merged.jpg # 병합된 상세 이미지
    └── product_detail_part*.jpg  # (너무 긴 경우) 분할된 이미지
```

## ⚠️ 주의사항
- 본 도구는 개인 학습 및 연구 목적으로 제작되었습니다.
- 과도한 크롤링은 대상 서버에 부하를 줄 수 있으므로 주의해서 사용하세요.
- 수집된 데이터의 상업적 이용은 올리브영의 이용약관을 확인하시기 바랍니다.

## 📝 라이선스
MIT License
