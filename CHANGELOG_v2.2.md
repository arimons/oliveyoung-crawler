# 변경 사항 v2.2

## 🎯 주요 개선 사항

### 1. 폴더명 형식 변경

**변경 전:**
```
data/한율_달빛유자_비타민_톤업팩폼_20251112_153045/
```
- 타임스탬프 포함 (년월일_시분초)
- 같은 상품을 여러 번 크롤링하면 폴더가 여러 개 생김

**변경 후:**
```
data/251112_한율 달빛유자 비타민 톤업팩폼/
```
- 날짜만 포함 (YYMMDD 형식)
- 공백 유지 (가독성 향상)
- 같은 날 같은 상품은 같은 폴더에 저장 (덮어쓰기)

**장점:**
- 폴더명이 짧고 깔끔함
- 같은 날 재크롤링 시 자동으로 업데이트
- 파일 탐색기에서 읽기 쉬움

### 2. 전체 작업 폴더 열기 기능

**위치:** 사이드바 → "📂 작업 폴더" 섹션

**기능:**
- "📁 전체 작업 폴더 열기" 버튼 클릭
- `data/` 폴더가 파일 탐색기에서 자동으로 열림
- 모든 크롤링 결과를 한눈에 확인 가능

**사용 시나리오:**
- 여러 상품을 크롤링한 후 한 번에 확인
- 과거 크롤링 데이터 찾기
- 폴더 정리 및 백업

### 3. 이미지 셀렉터 대폭 확장

**변경 전:** 4개 셀렉터
```python
selectors = [
    ".detail_cont img",
    "#artcInfo img",
    ".goods_detail_cont img",
    "#detail_img_expand img"
]
```

**변경 후:** 10개 셀렉터
```python
selectors = [
    ".detail_cont img",                    # 상세 설명 컨테이너
    "#artcInfo img",                        # 상품 정보 영역
    ".prd_detail_box img",                  # 상품 상세 박스
    ".detail_info_wrap img",                # 상세 정보 래퍼
    "#gdasDetail img",                      # 상품 상세 ID
    ".goods_detail_cont img",               # 상품 상세 컨텐츠
    "#detail_img_expand img",               # 확장 이미지 영역
    ".prd_detail img",                      # 상품 상세
    "div[class*='detail'] img",             # detail 클래스 포함
    "div[id*='detail'] img",                # detail ID 포함
]
```

**효과:**
- 올리브영 페이지 구조 변경에도 대응 가능
- 다양한 상품 페이지 레이아웃 지원
- 이미지 추출 성공률 향상

## 📁 폴더 구조 예시

### 변경 후
```
Oliveyoung/
├── data/
│   ├── 251112_한율 달빛유자 비타민 톤업팩폼/
│   │   ├── product_detail_merged.jpg
│   │   ├── product_info.json
│   │   └── product_info.csv
│   ├── 251112_라운드랩 자작나무 수분 토너/
│   │   ├── product_detail_merged.jpg
│   │   ├── product_info.json
│   │   └── product_info.csv
│   └── 251113_메디힐 티트리 마스크팩/
│       ├── product_detail_merged.jpg
│       ├── product_info.json
│       └── product_info.csv
```

## 🎨 UI 개선

### 사이드바 구조
```
⚙️ 설정
├─ [ ] 브라우저 표시
└─ 저장 형식: ● both

🔧 크롤러 상태
├─ ▶️ 실행 중
└─ [종료]

📂 작업 폴더              ← NEW!
└─ [📁 전체 작업 폴더 열기]  ← NEW!

📜 크롤링 히스토리
├─ 1. 한율 달빛유자...
│  └─ [📁 폴더 열기]
└─ 2. 라운드랩 자작나무...
   └─ [📁 폴더 열기]
```

## 🔧 기술적 세부사항

### 폴더명 생성 로직
```python
# 파일명에 사용할 수 없는 문자 제거
safe_name = "".join(c for c in product_name
                   if c.isalnum() or c in (' ', '-', '_')).strip()
safe_name = safe_name.replace(' ', ' ')  # 공백 유지

# 날짜만 추가 (YYMMDD 형식)
date_str = datetime.now().strftime("%y%m%d")
folder_name = f"{date_str}_{safe_name}"
```

### 작업 폴더 열기
```python
data_folder = os.path.join(os.getcwd(), "data")
if os.path.exists(data_folder):
    open_folder(data_folder)  # 플랫폼별 명령어 자동 처리
else:
    st.warning("아직 크롤링한 데이터가 없습니다")
```

## 📊 사용 예시

### 같은 날 재크롤링
```
1차 크롤링: 251112_한율 달빛유자 비타민 톤업팩폼/
            → product_detail_merged.jpg (2.5MB)

2차 크롤링: 251112_한율 달빛유자 비타민 톤업팩폼/  (같은 폴더)
            → product_detail_merged.jpg (2.5MB, 덮어쓰기됨)
```

### 다른 날 크롤링
```
11월 12일: 251112_한율 달빛유자 비타민 톤업팩폼/
11월 13일: 251113_한율 달빛유자 비타민 톤업팩폼/  (새 폴더)
```

## ⚠️ 주의사항

### 덮어쓰기 동작
- **같은 날 같은 상품**: 자동으로 덮어쓰기됨
- **다른 날 같은 상품**: 별도 폴더에 저장
- **중요 데이터**: 크롤링 전에 백업 권장

### 폴더명 규칙
- 알파벳, 숫자, 공백, `-`, `_`만 사용
- 특수문자는 자동으로 제거됨
- 예: `"한율/달빛유자"` → `"한율달빛유자"`

## 🚀 업그레이드 방법

기존 v2.1에서 v2.2로 업그레이드:
1. 코드는 자동으로 업데이트됨
2. 기존 data 폴더는 그대로 유지됨
3. 새로 크롤링하는 데이터부터 새 형식 적용

## 버전 비교

| 기능 | v2.1 | v2.2 |
|-----|------|------|
| 폴더명 | `상품명_20251112_153045` | `251112_상품명` |
| 공백 처리 | `_`로 변환 | 공백 유지 |
| 시간 정보 | 시분초 포함 | 날짜만 |
| 전체 폴더 열기 | ❌ | ✅ |
| 이미지 셀렉터 | 4개 | 10개 |
| 재크롤링 | 중복 폴더 생성 | 덮어쓰기 |

---

**v2.2 업데이트 완료! 🎉**
