# 📖 올리브영 크롤러 v2.0 사용 가이드

## 🚀 빠른 시작 (3단계)

### 1단계: 터미널 열기 및 이동
```bash
cd /Users/changhyunpark/Documents/Oliveyoung
source venv/bin/activate
```

### 2단계: Streamlit 앱 실행
```bash
streamlit run app.py
```

### 3단계: 브라우저에서 사용
자동으로 브라우저가 열립니다! (http://localhost:8501)

---

## 🎯 사용 시나리오

### 시나리오 1: 특정 상품 검색하여 이미지 수집

**목표**: "한율 달빛유자 비타민 톤업팩폼" 상품의 상세 이미지 수집

**단계**:
1. Streamlit 앱 실행
2. 사이드바에서 **"시작"** 버튼 클릭
3. **"키워드 검색"** 탭 선택
4. 검색창에 `한율 달빛유자 비타민 톤업팩폼` 입력
5. **"검색 및 크롤링 시작"** 클릭
6. 잠시 기다리면... 완료! 🎉

**결과**:
```
data/한율_달빛유자_비타민_톤업팩폼_20251112_213045/
├── product_detail_merged.jpg  ← 이것!
├── product_info.json
└── product_info.csv
```

---

### 시나리오 2: 상품 URL로 직접 크롤링

**목표**: 이미 알고 있는 상품 페이지의 이미지 수집

**단계**:
1. 올리브영에서 원하는 상품 페이지 열기
2. URL 복사 (예: `https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo=A000000237817`)
3. Streamlit 앱에서 **"URL 직접 입력"** 탭 선택
4. 복사한 URL 붙여넣기
5. **"URL로 크롤링 시작"** 클릭
6. 완료! 🎉

**장점**: 정확한 상품을 바로 지정 가능

---

## 🎨 Streamlit GUI 화면 설명

### 사이드바 (왼쪽)

```
⚙️ 설정
├─ [ ] 브라우저 표시      # 체크하면 Chrome이 보임
├─ 저장 형식
│  ├─ ○ json             # JSON만 저장
│  ├─ ○ csv              # CSV만 저장
│  └─ ● both             # 둘 다 저장 (추천)
│
🔧 크롤러 상태
├─ ▶️ 실행 중 / ⏸️ 중지됨
├─ [시작] [종료]
│
📜 크롤링 히스토리
└─ 최근 5개 기록
```

### 메인 화면

#### 🔍 키워드 검색 탭
```
┌─────────────────────────────────┐
│ 검색 키워드                      │
│ [예: 한율 달빛유자...]           │
│                                  │
│ [🔍 검색 및 크롤링 시작]        │
└─────────────────────────────────┘

↓ 결과

📋 상품 정보
- 상품명: ...
- 저장 폴더: data/...
- 이미지 개수: 15개

🖼️ 병합된 이미지
[긴 세로 이미지 미리보기]
```

#### 🔗 URL 직접 입력 탭
```
┌─────────────────────────────────┐
│ 상품 URL                         │
│ [https://www.oliveyoung...]     │
│                                  │
│ 상품명 (선택사항)                │
│ [비워두면 자동 추출]             │
│                                  │
│ [🔗 URL로 크롤링 시작]          │
└─────────────────────────────────┘
```

---

## 💡 사용 팁

### Tip 1: 브라우저 표시 vs 숨김

**브라우저 표시 ✅ (권장: 처음 사용 시)**
- 장점: 크롤링 과정을 눈으로 확인 가능
- 장점: 문제 발생 시 디버깅 쉬움
- 단점: 느림

**브라우저 숨김 ❌ (권장: 익숙해진 후)**
- 장점: 빠름 (30% 이상 속도 향상)
- 장점: 백그라운드에서 조용히 작동
- 단점: 문제 발생 시 원인 파악 어려움

### Tip 2: 저장 형식 선택

- **JSON**: 프로그래밍으로 처리할 때 (추천: 개발자)
- **CSV**: 엑셀에서 바로 열어볼 때 (추천: 일반 사용자)
- **Both**: 둘 다 필요할 때 (추천: 대부분의 경우)

### Tip 3: 이미지가 너무 클 때

병합된 이미지가 수십 MB가 될 수 있습니다.
- 파일 크기가 걱정되면 화질을 낮출 수 있습니다
- `product_detail_crawler.py`의 `quality=95`를 `quality=85`로 수정

---

## 🔍 실전 예제

### 예제 1: 여러 상품 순차적으로 크롤링

```python
# CLI로 여러 상품 크롤링
from src.oliveyoung_crawler import OliveyoungIntegratedCrawler

products = [
    "https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo=A000000237817",
    "https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo=A000000233879",
    "https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo=A000000219553"
]

crawler = OliveyoungIntegratedCrawler(headless=True)
crawler.start()

for url in products:
    try:
        result = crawler.crawl_product_by_url(url, save_format="both")
        print(f"✅ 완료: {result['상품명']}")
    except Exception as e:
        print(f"❌ 실패: {e}")

crawler.stop()
```

### 예제 2: 검색 결과 여러 개 크롤링

```python
# 현재는 첫 번째 결과만 가져오지만, 확장 가능
from src.oliveyoung_crawler import OliveyoungIntegratedCrawler

keywords = ["토너", "선크림", "로션"]

crawler = OliveyoungIntegratedCrawler(headless=True)
crawler.start()

for keyword in keywords:
    try:
        result = crawler.crawl_product_by_keyword(keyword, save_format="json")
        print(f"✅ {keyword}: {result['이미지_개수']}개 이미지")
    except:
        print(f"❌ {keyword}: 실패")

crawler.stop()
```

---

## ⚠️ 주의사항 및 해결책

### 문제 1: "브라우저를 시작할 수 없습니다"
**원인**: Chrome 브라우저가 설치되지 않음
**해결**: Chrome 브라우저 설치

### 문제 2: "이미지를 찾을 수 없습니다"
**원인**: 웹사이트 구조 변경 또는 "더보기" 버튼 실패
**해결**:
1. 브라우저 표시 옵션 켜기
2. 수동으로 페이지 확인
3. CSS selector 수정 필요할 수 있음

### 문제 3: "너무 느려요"
**해결책**:
1. `headless=True` 사용 (브라우저 숨김)
2. 인터넷 연결 확인
3. 다른 프로그램 종료

### 문제 4: "Streamlit이 실행되지 않아요"
**원인**: 가상환경 활성화 안 됨
**해결**:
```bash
source venv/bin/activate  # 다시 활성화
streamlit run app.py
```

### 문제 5: "병합된 이미지가 깨져요"
**원인**: 일부 이미지 다운로드 실패
**해결**: 로그에서 실패한 이미지 확인 후 다시 시도

---

## 🎓 고급 사용법

### 커스터마이징 1: 이미지 품질 조절

[src/product_detail_crawler.py:195](src/product_detail_crawler.py#L195)
```python
# 현재
merged_image.save(output_path, 'JPEG', quality=95, optimize=True)

# 파일 크기 줄이기
merged_image.save(output_path, 'JPEG', quality=85, optimize=True)

# 최고 품질
merged_image.save(output_path, 'JPEG', quality=100, optimize=False)
```

### 커스터마이징 2: 더 많은 이미지 정보 수집

상품 정보에 리뷰, 평점 등 추가 정보를 수집하고 싶다면
[src/product_detail_crawler.py](src/product_detail_crawler.py)의
`extract_product_info_from_detail` 함수 수정

### 커스터마이징 3: 페이지 넘김 (추후 추가 예정)

현재는 검색 결과 첫 번째 상품만 가져옵니다.
여러 상품을 자동으로 크롤링하려면 기능 확장 필요.

---

## 📊 성능 참고

**테스트 환경**: MacBook Air M1, 100Mbps 인터넷

| 항목 | 시간 | 비고 |
|-----|------|------|
| 브라우저 시작 | 3-5초 | 최초 1회 |
| 검색 및 이동 | 5-8초 | 네트워크 속도에 따라 |
| 이미지 URL 추출 | 2-3초 | |
| 이미지 다운로드 | 10-30초 | 이미지 개수에 따라 |
| 이미지 병합 | 1-3초 | |
| **총 소요 시간** | **21-49초** | 상품 1개 기준 |

**파일 크기**:
- 병합된 이미지: 2MB ~ 15MB (이미지 개수/해상도에 따라)
- JSON: 1KB 미만
- CSV: 1KB 미만

---

## 🙋 FAQ

**Q: 몇 개까지 이미지를 수집할 수 있나요?**
A: 상품 페이지에 있는 모든 이미지를 수집합니다. 보통 10~30개 정도입니다.

**Q: 동영상도 수집되나요?**
A: 아니요, 현재는 이미지만 수집합니다.

**Q: 여러 상품을 한 번에 크롤링할 수 있나요?**
A: GUI에서는 한 번에 하나씩만 가능합니다. CLI로 스크립트를 작성하면 가능합니다.

**Q: 이미지 순서가 원래 순서와 같나요?**
A: 네, 웹페이지에 표시된 순서대로 위에서 아래로 병합됩니다.

**Q: 저작권 문제는 없나요?**
A: 수집한 이미지는 개인 학습/연구 목적으로만 사용하세요. 상업적 사용은 금지됩니다.

---

## 🎉 성공 사례

### Before
- 수동으로 상품 페이지 접속
- 하나씩 이미지 우클릭 → 저장
- 20개 이미지 = 20번 반복
- 소요 시간: **10분 이상**

### After
- 검색어만 입력
- 크롤링 시작 버튼 클릭
- 자동으로 모든 이미지 수집 및 병합
- 소요 시간: **30초**

---

**Happy Crawling! 🛒✨**
