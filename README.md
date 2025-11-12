# 🛒 올리브영 상품 크롤러

올리브영 온라인몰에서 상품 정보를 검색하고 수집하는 Python 크롤러입니다.

## 📋 기능

- ✅ 상품명으로 검색
- ✅ 상품 정보 자동 수집 (상품명, 브랜드, 가격, URL)
- ✅ JSON/CSV 형식으로 데이터 저장
- ✅ 브라우저 표시/숨김 모드 지원
- ✅ 사용자 친화적인 대화형 인터페이스

## 🚀 설치 방법

### 1. 필수 요구사항

- Python 3.10 이상
- Chrome 브라우저

### 2. 가상환경 생성 및 활성화

```bash
# 가상환경 생성 (Python 3.10 사용 권장)
python3.10 -m venv venv

# 가상환경 활성화
source venv/bin/activate  # Mac/Linux
# 또는
venv\Scripts\activate  # Windows
```

### 3. 패키지 설치

```bash
pip install -r requirements.txt
```

## 💻 사용 방법

### 기본 사용법

```bash
# 가상환경 활성화
source venv/bin/activate

# 메인 스크립트 실행
python main.py
```

실행하면 다음 질문들이 나옵니다:
1. 검색할 상품명
2. 추출할 상품 개수
3. 브라우저 표시 여부
4. 저장 형식 (JSON/CSV/Both)

### 예시

```
🔍 검색할 상품명을 입력하세요: 토너
📊 추출할 상품 개수를 입력하세요 (기본값: 10): 5
👀 브라우저를 화면에 표시할까요? (y/n, 기본값: n): n
💾 저장 형식을 선택하세요 (json/csv/both, 기본값: both): both
```

## 📁 프로젝트 구조

```
Oliveyoung/
├── venv/                    # 가상환경 (설치 후 생성됨)
├── src/
│   ├── __init__.py
│   └── crawler_selenium.py  # 크롤러 핵심 코드
├── data/                    # 수집된 데이터 저장 폴더
│   ├── .gitkeep
│   └── (크롤링 결과 파일들)
├── main.py                  # 메인 실행 스크립트
├── requirements.txt         # 필요한 패키지 목록
├── .gitignore
└── README.md
```

## 📊 출력 데이터 형식

### JSON 형식
```json
[
  {
    "순번": 1,
    "상품명": "라네즈 크림스킨 토너",
    "브랜드": "라네즈",
    "가격": "33,000원 26,400원",
    "URL": "https://www.oliveyoung.co.kr/store/goods/...",
    "수집시각": "2025-11-12 12:54:41"
  }
]
```

### CSV 형식
| 순번 | 상품명 | 브랜드 | 가격 | URL | 수집시각 |
|-----|-------|-------|-----|-----|---------|
| 1 | 라네즈 크림스킨 토너 | 라네즈 | 33,000원 26,400원 | https://... | 2025-11-12 12:54:41 |

## 🔧 테스트 스크립트

프로젝트에는 여러 테스트 스크립트가 포함되어 있습니다:

```bash
# 기본 접속 테스트
python test_selenium.py

# 검색 기능 테스트
python test_search.py

# 상품 추출 테스트
python test_extract.py

# 전체 프로세스 테스트
python test_full_process.py
```

## ⚠️ 주의사항

1. **속도 제한**: 너무 많은 요청을 보내면 IP가 차단될 수 있습니다. 적절한 대기 시간을 유지하세요.

2. **웹사이트 변경**: 올리브영 웹사이트 구조가 변경되면 크롤러가 작동하지 않을 수 있습니다.

3. **법적 책임**: 크롤링한 데이터는 개인적인 용도로만 사용하세요. 상업적 사용 전에 올리브영의 이용약관을 확인하세요.

4. **Chrome 브라우저**: Chrome 브라우저가 설치되어 있어야 합니다. ChromeDriver는 자동으로 다운로드됩니다.

## 🐛 문제 해결

### Chrome 관련 오류
```bash
# ChromeDriver 캐시 삭제
rm -rf ~/.wdm
```

### 상품을 찾을 수 없음
- 검색어를 더 일반적인 단어로 변경해보세요
- 브라우저 표시 모드(y)로 실행하여 페이지를 직접 확인하세요

### 느린 속도
- headless 모드(n)로 실행하면 더 빠릅니다
- 추출할 상품 개수를 줄여보세요

## 📝 코드 이해하기

### 주요 클래스: `OliveyoungCrawler`

```python
from src.crawler_selenium import OliveyoungCrawler

# 크롤러 초기화
crawler = OliveyoungCrawler(headless=True)

# 브라우저 시작
crawler.start()

# 홈페이지 접속
crawler.navigate_to_home()

# 상품 검색
crawler.search_product("토너")

# 상품 정보 추출
products = crawler.extract_product_info(max_products=10)

# 데이터 저장
crawler.save_to_json(products, "my_data")
crawler.save_to_csv(products, "my_data")

# 브라우저 종료
crawler.stop()
```

## 🙋 FAQ

**Q: 몇 개까지 상품을 추출할 수 있나요?**
A: 검색 결과 페이지에 표시되는 상품만 추출 가능합니다 (보통 24~48개). 더 많은 상품이 필요하면 페이지 넘김 기능을 추가해야 합니다.

**Q: 특정 카테고리의 상품만 수집할 수 있나요?**
A: 현재는 검색 기능만 지원합니다. 카테고리별 수집 기능은 추후 추가할 수 있습니다.

**Q: 데이터를 엑셀로 바로 저장할 수 있나요?**
A: CSV 파일을 생성하면 엑셀에서 바로 열 수 있습니다. UTF-8 BOM 인코딩을 사용하여 한글이 깨지지 않습니다.

## 📄 라이선스

이 프로젝트는 개인 학습 및 연구 목적으로 제작되었습니다.

## 👨‍💻 개발 정보

- Python 3.10
- Selenium 4.15.2
- pandas 2.1.3

---

**만든 날짜**: 2025-11-12
**버전**: 1.0.0
