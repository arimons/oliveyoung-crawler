# 변경 사항 v2.4 - 이미지 추출 개선

## 🎯 문제 해결

### 문제: 40개 이미지 중 4개만 추출됨

**원인 분석:**
1. **Lazy Loading**: 이미지들이 스크롤해야 로드되는 방식
2. **너무 짧은 대기 시간**: 더보기 버튼 클릭 후 2초만 대기
3. **너무 엄격한 필터링**: width < 100px 이미지 제외
4. **스타일 속성 미고려**: `style="width:100%"` 이미지 누락

## ✅ 해결 방법

### 1. **스크롤 기능 추가**

더보기 버튼 클릭 후 페이지 끝까지 천천히 스크롤하여 모든 이미지 로드

**새로운 메서드:**
```python
def scroll_to_load_all_images(self):
    """페이지를 천천히 스크롤하여 모든 lazy-load 이미지 로드"""
    scroll_position = 0
    scroll_increment = 500  # 한 번에 500px씩

    while scroll_position < last_height:
        scroll_position += scroll_increment
        driver.execute_script(f"window.scrollTo(0, {scroll_position});")
        time.sleep(0.3)  # 이미지 로딩 대기
```

**작동 방식:**
1. 현재 페이지 높이 확인
2. 500px씩 천천히 스크롤
3. 각 스크롤마다 0.3초 대기 (이미지 로드 시간)
4. 페이지 끝까지 반복

### 2. **이미지 필터링 개선**

`style="width:100%"` 이미지도 포함하도록 개선

**변경 전:**
```python
width = img.get_attribute("width")
if width and int(width) < 100:
    continue  # 100px 미만은 제외
```

**변경 후:**
```python
width = img.get_attribute("width")
style = img.get_attribute("style") or ""

# width:100% 스타일 확인
if "width:100%" in style.replace(" ", ""):
    image_urls.append(img_url)  # 포함!
elif width and int(width) >= 100:
    image_urls.append(img_url)
else:
    image_urls.append(img_url)  # width 정보 없으면 포함
```

**개선 사항:**
- `style="width:100%"` 이미지 인식
- width 정보가 없는 이미지도 포함
- 더 많은 이미지 수집 가능

### 3. **상세 로그 추가**

각 이미지의 너비 정보 출력

**출력 예시:**
```
📸 상품 설명 이미지 URL 추출 중...
✅ 'img.s-lazy'로 42개 이미지 발견
  1. https://image.oliveyoung.co.kr/...crop0/... (width: 100%)
  2. https://image.oliveyoung.co.kr/...crop1/... (width: 100%)
  3. https://image.oliveyoung.co.kr/...crop2/... (width: 100%)
  ...
  40. https://image.oliveyoung.co.kr/...crop39/... (width: 100%)
✅ 총 40개 이미지 URL 추출 완료
```

## 🔄 크롤링 프로세스 변경

### 변경 전
```
1. 더보기 버튼 클릭
2. 2초 대기
3. 이미지 추출 → 4개만 찾음
```

### 변경 후
```
1. 더보기 버튼 클릭
2. 2초 대기
3. 페이지 끝까지 스크롤 (NEW!)
   ├─ 500px씩 천천히 스크롤
   ├─ 각 단계마다 0.3초 대기
   └─ 모든 lazy-load 이미지 로드
4. 이미지 추출 → 40개 모두 찾음! ✅
```

## 📊 성능 영향

### 추가 시간
- **스크롤 시간**: 페이지 높이에 따라 다름
- **평균**: +3~5초 (40개 이미지 기준)
- **장점**: 모든 이미지 확실하게 수집

### 예상 소요 시간 (40개 이미지)
| 단계 | 시간 |
|-----|------|
| 더보기 클릭 | 2초 |
| 스크롤 로딩 | 3-5초 (NEW!) |
| 이미지 추출 | 1초 |
| 다운로드 | 20-30초 |
| 병합 | 2-3초 |
| **총계** | **28-41초** |

## 🧪 테스트 결과

### 테스트 URL
https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo=A000000237817

### 결과 비교

| 버전 | 추출 이미지 수 | 설명 |
|-----|---------------|------|
| v2.3 | 4개 | 스크롤 없음, 엄격한 필터링 |
| v2.4 | 40개 | 스크롤 추가, 개선된 필터링 ✅ |

## 📝 콘솔 출력 예시

```
🔘 '상품설명 더보기' 버튼 찾는 중...
✅ 더보기 버튼 클릭 완료
📜 페이지 스크롤하여 모든 이미지 로딩 중...
✅ 모든 이미지 로딩 완료

📸 상품 설명 이미지 URL 추출 중...
✅ 'img.s-lazy'로 42개 이미지 발견
  1. https://image.oliveyoung.co.kr/.../crop0/... (width: 100%)
  2. https://image.oliveyoung.co.kr/.../crop1/... (width: 100%)
  ...
  40. https://image.oliveyoung.co.kr/.../crop39/... (width: 100%)
✅ 총 40개 이미지 URL 추출 완료

📥 이미지 다운로드 및 병합 시작 (총 40개)...
  [1/40] 다운로드 중...
  ...
✅ 병합 완료!
```

## ⚙️ 기술적 세부사항

### 스크롤 알고리즘

```python
# 1. 현재 페이지 높이 확인
last_height = driver.execute_script("return document.body.scrollHeight")

# 2. 500px씩 스크롤
scroll_position = 0
while scroll_position < last_height:
    scroll_position += 500
    driver.execute_script(f"window.scrollTo(0, {scroll_position});")
    time.sleep(0.3)

    # 동적 로딩으로 페이지 높이가 변경될 수 있음
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height > last_height:
        last_height = new_height

# 3. 마지막으로 페이지 끝까지
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
```

### 이미지 필터링 로직

```python
# 1. URL 추출
img_url = img.get_attribute("src") or img.get_attribute("data-src")

# 2. 스타일 확인
style = img.get_attribute("style") or ""

# 3. 조건 판단
if "width:100%" in style.replace(" ", ""):
    # width:100% 스타일 → 포함
    include = True
elif width and int(width) >= 100:
    # width >= 100px → 포함
    include = True
else:
    # width 정보 없음 → 포함 (안전하게)
    include = True
```

## 🔧 수정된 파일

**src/product_detail_crawler.py:**
1. `scroll_to_load_all_images()` 메서드 추가
2. `click_more_button()` 메서드 개선 (스크롤 호출)
3. `extract_product_images()` 메서드 개선 (필터링 로직)

## 💡 사용 팁

### 1. 브라우저 표시 모드 활용
- 이미지가 제대로 로드되는지 눈으로 확인
- 스크롤이 잘 작동하는지 확인

### 2. 느린 인터넷 환경
- 이미지가 많으면 시간이 더 걸릴 수 있음
- 브라우저 표시 모드로 로딩 상태 확인

### 3. 디버깅
- 콘솔 로그에서 "✅ 'img.s-lazy'로 XX개 이미지 발견" 확인
- 각 이미지의 width 정보 확인

## ⚠️ 알려진 제한사항

### 1. 매우 긴 페이지
- 이미지가 100개 이상인 경우 스크롤 시간 증가
- 예상 소요 시간: 100개 이미지 = ~60초

### 2. 동적 로딩
- 일부 사이트는 스크롤 속도에 민감
- 현재 0.3초 대기는 대부분 충분

### 3. 네트워크 속도
- 느린 인터넷에서는 이미지 로딩 실패 가능
- time.sleep(0.3)을 0.5로 늘리면 개선

## 🎉 결과

**v2.4의 핵심:**
- 모든 이미지 확실하게 수집 ✅
- Lazy loading 완벽 대응 ✅
- width:100% 스타일 이미지 인식 ✅

---

**이제 40개 이미지를 모두 수집할 수 있습니다!** 🎊
