# 🛒 올리브영 상품 크롤러 v2.0

올리브영 온라인몰에서 **상품 상세 이미지를 자동으로 수집하고 병합**하는 Python 크롤러입니다.

## ✨ 주요 기능

- 🔍 **키워드 검색**: 상품명으로 검색하여 첫 번째 결과 크롤링
- 🔗 **URL 직접 입력**: 상품 페이지 URL로 직접 크롤링
- 📸 **상세 이미지 수집**: 상품 설명의 모든 이미지 자동 다운로드
- 🖼️ **이미지 병합**: 여러 이미지를 하나의 긴 세로 이미지로 자동 병합
- 💾 **데이터 저장**: JSON/CSV 형식으로 상품 정보 저장
- 🎨 **Streamlit GUI**: 직관적인 웹 인터페이스 제공
- 📁 **자동 폴더 관리**: `data/상품명_날짜/` 형태로 자동 정리

## 🆕 v2.0 업데이트

1. **상품 상세 이미지 크롤링**: 상품 설명 페이지의 모든 이미지 수집
2. **이미지 자동 병합**: PIL을 사용하여 하나의 세로 이미지로 병합
3. **더보기 버튼 자동 클릭**: 숨겨진 이미지도 자동으로 펼쳐서 수집
4. **Streamlit GUI**: 웹 브라우저에서 사용할 수 있는 GUI 제공
5. **폴더 구조 자동 생성**: 상품별로 폴더 자동 생성 및 관리

## 🚀 빠른 시작

### 1. 설치

```bash
# 가상환경 활성화
source venv/bin/activate

# 패키지가 설치되어 있지 않다면
pip install -r requirements.txt
```

### 2. Streamlit GUI 실행 (권장 ⭐)

```bash
streamlit run app.py
```

브라우저가 자동으로 열리고 `http://localhost:8501`에서 GUI를 사용할 수 있습니다!

### 3. 사용 방법

#### 방법 1: 키워드 검색
1. 사이드바에서 "시작" 버튼 클릭
2. "키워드 검색" 탭에서 상품명 입력
3. "검색 및 크롤링 시작" 버튼 클릭
4. 결과 확인 및 이미지 다운로드

#### 방법 2: URL 직접 입력
1. 사이드바에서 "시작" 버튼 클릭
2. "URL 직접 입력" 탭 선택
3. 올리브영 상품 페이지 URL 붙여넣기
4. "URL로 크롤링 시작" 버튼 클릭
5. 결과 확인 및 이미지 다운로드

## 📁 프로젝트 구조

```
Oliveyoung/
├── app.py                          # Streamlit GUI 앱 ⭐
├── main.py                         # CLI 버전 (구버전)
├── venv/                           # Python 가상환경
├── src/
│   ├── crawler_selenium.py        # 기본 검색 크롤러
│   ├── product_detail_crawler.py  # 상세 페이지 크롤러 🆕
│   └── oliveyoung_crawler.py      # 통합 크롤러 🆕
├── data/                           # 크롤링 결과 저장
│   └── 상품명_날짜시간/            # 상품별 폴더
│       ├── product_detail_merged.jpg  # 병합된 이미지 🆕
│       ├── product_info.json      # 상품 정보 (JSON)
│       └── product_info.csv       # 상품 정보 (CSV)
├── requirements.txt
└── README.md
```

## 🖼️ 이미지 병합 기능

상품 상세 페이지의 모든 설명 이미지를 자동으로 수집하여:
1. 각 이미지를 개별 다운로드
2. 동일한 너비로 정렬
3. 세로로 이어붙여 하나의 긴 이미지 생성
4. `product_detail_merged.jpg`로 저장

### 예시

```
원본:
  image1.jpg (800x600)
  image2.jpg (800x400)
  image3.jpg (800x700)

병합 결과:
  product_detail_merged.jpg (800x1700)
```

## 📊 데이터 저장 형식

### 폴더 구조
```
data/
└── 한율_달빛유자_비타민_톤업팩폼_20251112_213045/
    ├── product_detail_merged.jpg    # 병합된 이미지
    ├── product_info.json            # 상품 정보 (JSON)
    └── product_info.csv             # 상품 정보 (CSV)
```

### product_info.json
```json
{
  "상품명": "한율 달빛유자 비타민 톤업팩폼 120ml",
  "브랜드": "한율",
  "가격": "19,000원",
  "URL": "https://www.oliveyoung.co.kr/store/goods/...",
  "이미지_경로": "data/한율_달빛유자.../product_detail_merged.jpg",
  "이미지_개수": 15,
  "수집시각": "2025-11-12 21:30:45"
}
```

## 🎨 Streamlit GUI 기능

### 사이드바
- ⚙️ **설정**
  - 브라우저 표시 옵션
  - 저장 형식 선택 (JSON/CSV/Both)
- 🔧 **크롤러 제어**
  - 시작/종료 버튼
  - 실시간 상태 표시
- 📜 **히스토리**
  - 최근 크롤링 5개 기록

### 메인 화면
- 🔍 **키워드 검색 탭**
  - 상품명 입력 폼
  - 실시간 진행 상태
  - 결과 미리보기
- 🔗 **URL 입력 탭**
  - URL 직접 입력
  - 선택적 상품명 입력
  - 결과 미리보기

### 결과 화면
- 📋 상품 정보 요약
- 📂 저장된 파일 목록
- 🖼️ 병합된 이미지 미리보기 (전체 크기)

## 🔧 CLI 사용 (선택사항)

GUI 대신 커맨드라인으로도 사용 가능합니다:

```python
from src.oliveyoung_crawler import OliveyoungIntegratedCrawler

# 크롤러 생성
crawler = OliveyoungIntegratedCrawler(headless=True)
crawler.start()

# 키워드로 크롤링
result = crawler.crawl_product_by_keyword(
    keyword="토너",
    save_format="both"
)

# URL로 크롤링
result = crawler.crawl_product_by_url(
    product_url="https://www.oliveyoung.co.kr/store/goods/...",
    save_format="json"
)

crawler.stop()
```

## 📝 테스트

```bash
# 통합 크롤러 테스트
python test_integrated.py
```

## ⚠️ 주의사항

1. **Chrome 브라우저 필요**: ChromeDriver 자동 다운로드
2. **네트워크 속도**: 이미지 다운로드 시간이 소요될 수 있음
3. **저장 공간**: 병합된 이미지는 수 MB~수십 MB가 될 수 있음
4. **웹사이트 정책**: 올리브영 이용약관 준수 필요
5. **개인적 용도**: 수집한 데이터는 개인 학습/연구 목적으로만 사용

## 🐛 문제 해결

### 이미지를 찾을 수 없어요
- 상품 페이지 구조가 변경되었을 수 있습니다
- 브라우저 표시 옵션을 켜서 직접 확인해보세요
- "더보기" 버튼이 제대로 클릭되었는지 확인하세요

### 병합된 이미지가 이상해요
- 일부 이미지가 다운로드 실패했을 수 있습니다
- 로그를 확인하여 어떤 이미지가 실패했는지 확인하세요

### Streamlit이 느려요
- `headless=True`로 설정하면 더 빠릅니다 (브라우저 숨김)
- 네트워크 연결 상태를 확인하세요

## 🎓 기술 스택

- **Python 3.10**: 프로그래밍 언어
- **Selenium**: 웹 자동화
- **Pillow (PIL)**: 이미지 처리 및 병합
- **Streamlit**: 웹 GUI 프레임워크
- **pandas**: 데이터 처리
- **requests**: HTTP 요청

## 📄 라이선스

개인 학습 및 연구 목적으로 제작되었습니다.

---

**버전**: 2.0.0
**업데이트**: 2025-11-12
**개발**: Python 3.10 + Selenium + Streamlit
