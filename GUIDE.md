# 📖 올리브영 크롤러 초보자 가이드

크롤링이 처음이신가요? 걱정하지 마세요! 차근차근 따라하면 쉽게 사용할 수 있습니다.

## 🎯 크롤링이란?

웹사이트에서 정보를 자동으로 수집하는 것입니다.
이 프로그램은 올리브영 웹사이트에서 상품 정보를 자동으로 가져와서 엑셀 파일로 저장해줍니다.

## 🚀 시작하기 (5단계)

### 1단계: 터미널(명령 프롬프트) 열기

**Mac의 경우:**
- Spotlight 검색 (Cmd + Space) → "터미널" 입력 → 실행

**Windows의 경우:**
- 시작 메뉴 → "cmd" 또는 "명령 프롬프트" 검색 → 실행

### 2단계: 프로젝트 폴더로 이동

```bash
cd /Users/changhyunpark/Documents/Oliveyoung
```

**팁:** 폴더를 터미널 창에 드래그하면 경로가 자동으로 입력됩니다!

### 3단계: 가상환경 활성화

```bash
source venv/bin/activate
```

성공하면 앞에 `(venv)`가 표시됩니다:
```
(venv) user@computer:~/Oliveyoung$
```

### 4단계: 프로그램 실행

```bash
python main.py
```

### 5단계: 질문에 답하기

프로그램이 몇 가지 질문을 합니다:

```
🔍 검색할 상품명을 입력하세요: 스킨케어
📊 추출할 상품 개수를 입력하세요 (기본값: 10): 10
👀 브라우저를 화면에 표시할까요? (y/n, 기본값: n): n
💾 저장 형식을 선택하세요 (json/csv/both, 기본값: both): csv
```

**질문 설명:**
- **상품명**: 검색하고 싶은 제품 (예: 토너, 선크림, 립스틱)
- **개수**: 몇 개의 상품을 가져올지 (10~20개 권장)
- **브라우저 표시**:
  - `y`: 크롬 브라우저가 열려서 작동하는 모습을 볼 수 있음
  - `n`: 백그라운드에서 조용히 실행 (더 빠름)
- **저장 형식**:
  - `csv`: 엑셀에서 바로 열 수 있는 파일
  - `json`: 프로그래밍용 데이터 파일
  - `both`: 둘 다 저장

## 📂 결과 확인하기

프로그램이 끝나면 `data` 폴더에 파일이 생성됩니다:

```
Oliveyoung/
└── data/
    ├── oliveyoung_토너_20251112_125441.json
    └── oliveyoung_토너_20251112_125457.csv  ← 이 파일을 엑셀로 열기
```

### CSV 파일 열기

1. `data` 폴더로 이동
2. `.csv` 파일을 더블클릭
3. 엑셀이나 Numbers가 자동으로 열립니다

## 💡 실전 예제

### 예제 1: 선크림 10개 수집

```bash
python main.py
```

입력:
- 상품명: `선크림`
- 개수: `10`
- 브라우저: `n`
- 형식: `csv`

결과: `data/oliveyoung_선크림_날짜시간.csv` 파일 생성

### 예제 2: 브라우저를 보면서 토너 5개 수집

```bash
python main.py
```

입력:
- 상품명: `토너`
- 개수: `5`
- 브라우저: `y`  ← 크롬이 열립니다
- 형식: `both`

결과: JSON과 CSV 파일 둘 다 생성

## ❓ 자주 하는 실수

### 1. "command not found: python"

**해결:**
```bash
python3 main.py  # python 대신 python3 사용
```

### 2. "No module named 'selenium'"

**해결:** 가상환경을 활성화하지 않았습니다
```bash
source venv/bin/activate  # 다시 활성화
python main.py
```

### 3. 한글이 깨져요

CSV 파일은 이미 한글을 지원하도록 설정되어 있습니다.
만약 깨진다면:
- 엑셀에서 열 때: 데이터 → 텍스트 나누기 → UTF-8 선택

### 4. 너무 느려요

**해결책:**
- 브라우저 표시를 `n`으로 설정 (더 빠름)
- 개수를 줄이기 (5~10개)
- 인터넷 연결 확인

## 🎓 더 배우고 싶다면

### 코드 이해하기

`src/crawler_selenium.py` 파일을 열어보세요. 각 함수에 주석이 달려 있습니다:

```python
def search_product(self, keyword: str):
    """제품 검색 - 올리브영에서 키워드로 검색"""

def extract_product_info(self, max_products: int = 10):
    """상품 정보 추출 - 상품명, 가격, 브랜드 등을 가져옴"""

def save_to_csv(self, data, filename):
    """CSV 저장 - 엑셀로 열 수 있는 파일로 저장"""
```

### 코드 수정하기

더 많은 정보를 수집하고 싶다면 `crawler_selenium.py` 파일의 `extract_product_info` 함수를 수정하세요.

예를 들어, 리뷰 개수를 추가하려면:
```python
# 리뷰 개수 추출
try:
    review_elem = product.find_element(By.CSS_SELECTOR, ".review_count")
    review_count = review_elem.text.strip()
except:
    review_count = "0"

product_data = {
    "순번": idx + 1,
    "상품명": name,
    "브랜드": brand,
    "가격": price,
    "리뷰수": review_count,  # 새로 추가!
    "URL": url,
    "수집시각": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}
```

## 📞 도움이 필요하면

1. **README.md 파일** 확인 - 더 자세한 기술 문서
2. **오류 메시지 읽기** - 문제의 힌트가 있습니다
3. **브라우저 표시 모드** - `y`로 설정하면 무엇이 일어나는지 볼 수 있음

## 🎉 성공 체크리스트

- ✅ 가상환경 활성화 완료
- ✅ 프로그램 실행 성공
- ✅ 상품 검색 성공
- ✅ CSV 파일 생성 확인
- ✅ 엑셀에서 파일 열기 성공

모두 체크하셨다면 축하합니다! 🎊
이제 올리브영 크롤러를 자유롭게 사용하실 수 있습니다!

---

**다음 단계:**
- 다른 검색어로 여러 번 실행해보기
- 코드를 조금씩 수정하며 배우기
- 필요한 기능 추가하기

화이팅! 💪
