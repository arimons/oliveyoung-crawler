"""
올리브영 상품 상세 페이지 크롤러
상품 설명 이미지를 수집하고 병합하는 기능
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import requests
import time
import os
from typing import List, Dict
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed


class ProductDetailCrawler:
    """상품 상세 페이지 이미지 크롤러"""

    def __init__(self, driver):
        """
        Args:
            driver: Selenium WebDriver 인스턴스
        """
        self.driver = driver

    def go_to_product_detail(self, product_url: str):
        """
        상품 상세 페이지로 이동

        Args:
            product_url: 상품 URL
        """
        print(f"🔗 상품 페이지로 이동: {product_url}")
        self.driver.get(product_url)

        # React 앱 렌더링 대기 - 상품명이 로드될 때까지
        try:
            wait = WebDriverWait(self.driver, 10)
            # h1 태그가 로드되고 텍스트가 있을 때까지 대기
            wait.until(lambda driver: driver.execute_script(
                "return document.querySelector('h1') && document.querySelector('h1').textContent.length > 0"
            ))
            print("✅ 페이지 로딩 완료")
        except:
            print("⚠️  페이지 로딩 대기 타임아웃, 계속 진행")
            time.sleep(2)

    def extract_review_metadata(self) -> Dict[str, any]:
        """
        리뷰 개수와 별점 추출 (상품 설명 근처에서 직접 추출)

        Returns:
            {"리뷰_총개수": int, "별점": float} 형태의 딕셔너리
        """
        metadata = {"리뷰_총개수": 0, "별점": 0.0}

        try:
            # 디버깅: 페이지 HTML 일부 저장
            try:
                page_html = self.driver.page_source
                with open("debug_review_metadata_page.html", "w", encoding="utf-8") as f:
                    f.write(page_html)
                print(f"📁 디버깅용 페이지 HTML 저장: debug_review_metadata_page.html")
            except:
                pass

            # JavaScript로 React 렌더링된 DOM에서 직접 추출
            result = self.driver.execute_script("""
                const debug = {};

                // 별점 추출 - <span class="rating"> 구조에서 추출
                let rating = 0.0;

                // 패턴 1: <span class="rating"> 요소에서 직접 추출
                const ratingSpan = document.querySelector('span.rating');
                if (ratingSpan) {
                    // "평점4.8" 또는 "평점 4.8" 형태에서 숫자만 추출
                    const text = ratingSpan.textContent.trim();
                    const match = text.match(/([0-9]+\\.[0-9]+)/);
                    if (match) {
                        rating = parseFloat(match[1]);
                        debug.ratingSource = 'span.rating querySelector';
                        debug.ratingText = text;
                        debug.ratingHTML = ratingSpan.outerHTML.substring(0, 150);
                    }
                }

                // 패턴 2: ReviewArea_rating 클래스 검색
                if (rating === 0.0) {
                    const reviewAreaRating = document.querySelector('[class*="ReviewArea_rating"]');
                    if (reviewAreaRating) {
                        const text = reviewAreaRating.textContent.trim();
                        const match = text.match(/([0-9]+\\.[0-9]+)/);
                        if (match) {
                            rating = parseFloat(match[1]);
                            debug.ratingSource = 'ReviewArea_rating class';
                            debug.ratingText = text;
                        }
                    }
                }

                // 리뷰수 추출 - ReviewArea_review-count 또는 "리뷰" 텍스트
                let totalCount = 0;

                // 패턴 1: ReviewArea_review-count 클래스에서 추출
                const reviewCountElem = document.querySelector('[class*="ReviewArea_review-count"]');
                if (reviewCountElem) {
                    const text = reviewCountElem.textContent;
                    const match = text.match(/([0-9,]+)/);
                    if (match) {
                        totalCount = parseInt(match[1].replace(/,/g, ''));
                        debug.reviewSource = 'ReviewArea_review-count class';
                        debug.reviewHTML = reviewCountElem.outerHTML.substring(0, 150);
                        debug.reviewText = text.substring(0, 50);
                    }
                }

                // 패턴 2: "리뷰" 텍스트가 포함된 요소에서 숫자 찾기 (fallback)
                if (totalCount === 0) {
                    const allElements = Array.from(document.querySelectorAll('*'));
                    const reviewElem = allElements.find(el => {
                        const text = el.textContent;
                        return text.includes('리뷰') && /[0-9,]+/.test(text) && text.length < 50;
                    });

                    if (reviewElem) {
                        const match = reviewElem.textContent.match(/([0-9,]+)/);
                        if (match) {
                            totalCount = parseInt(match[1].replace(/,/g, ''));
                            debug.reviewSource = 'element with 리뷰 text (fallback)';
                            debug.reviewHTML = reviewElem.outerHTML.substring(0, 150);
                            debug.reviewText = reviewElem.textContent.substring(0, 50);
                        }
                    }
                }

                return {
                    total: totalCount,
                    rating: rating,
                    debug: debug
                };
            """)

            if result:
                # 디버깅 정보 출력
                debug_info = result.get("debug", {})
                print(f"\n🔍 추출 정보:")
                print(f"  별점 출처: {debug_info.get('ratingSource', 'N/A')}")
                if debug_info.get('ratingText'):
                    print(f"  별점 텍스트: {debug_info.get('ratingText')}")
                if debug_info.get('ratingHTML'):
                    print(f"  별점 HTML: {debug_info.get('ratingHTML')}")

                print(f"\n  리뷰수 출처: {debug_info.get('reviewSource', 'N/A')}")
                if debug_info.get('reviewText'):
                    print(f"  리뷰수 텍스트: {debug_info.get('reviewText')}")
                if debug_info.get('reviewHTML'):
                    print(f"  리뷰수 HTML: {debug_info.get('reviewHTML')}")

                metadata["리뷰_총개수"] = result.get("total", 0)
                metadata["별점"] = result.get("rating", 0.0)

                if metadata["리뷰_총개수"] > 0:
                    print(f"📊 리뷰 총 개수: {metadata['리뷰_총개수']}개")
                else:
                    print(f"⚠️  리뷰 개수를 찾을 수 없음")

                if metadata["별점"] > 0:
                    print(f"⭐ 별점: {metadata['별점']}점")
                else:
                    print(f"⚠️  별점을 찾을 수 없음")
            else:
                print(f"⚠️  JavaScript 실행 결과가 없음")

        except Exception as e:
            print(f"⚠️  리뷰 메타데이터 추출 실패: {e}")
            import traceback
            traceback.print_exc()

        return metadata

    def click_more_button(self):
        """상품설명 더보기 버튼 클릭"""
        try:
            print("🔘 '상품설명 더보기' 버튼 찾는 중...")

            # 더보기 버튼 찾기
            wait = WebDriverWait(self.driver, 10)
            more_button = wait.until(
                EC.presence_of_element_located((By.ID, "btn_toggle_detail_image"))
            )

            # 버튼이 보이도록 스크롤
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", more_button)
            time.sleep(1)

            # 버튼 클릭
            more_button.click()
            print("✅ 더보기 버튼 클릭 완료")
            time.sleep(2)  # 이미지 로딩 대기

            # 페이지 끝까지 천천히 스크롤하여 모든 lazy-load 이미지 로드
            print("📜 페이지 스크롤하여 모든 이미지 로딩 중...")
            self.scroll_to_load_all_images()

            return True

        except Exception as e:
            print(f"⚠️  더보기 버튼을 찾을 수 없거나 이미 펼쳐져 있습니다: {e}")
            print("현재 페이지 URL:", self.driver.current_url)

            # 다른 가능한 버튼 ID들 시도
            alternative_buttons = [
                "btnToggleDetail",
                "btn_detail_more",
                "detail_more_btn"
            ]

            for btn_id in alternative_buttons:
                try:
                    alt_button = self.driver.find_element(By.ID, btn_id)
                    alt_button.click()
                    print(f"✅ 대체 버튼 '{btn_id}' 클릭 성공")
                    time.sleep(2)
                    return True
                except:
                    continue

            print("⚠️  모든 더보기 버튼 시도 실패 - 이미 펼쳐져 있을 수 있습니다")
            return False

    def scroll_to_load_all_images(self):
        """
        페이지를 천천히 스크롤하여 모든 lazy-load 이미지 로드
        네트워크 요청이 완료될 때까지 지능적으로 대기
        """
        try:
            # 현재 페이지 높이
            last_height = self.driver.execute_script("return document.body.scrollHeight")

            # 스크롤 위치
            scroll_position = 0
            scroll_increment = 500  # 한 번에 500px씩 스크롤
            max_wait_per_scroll = 3  # 각 스크롤마다 최대 3초 대기

            while scroll_position < last_height:
                # 조금씩 스크롤
                scroll_position += scroll_increment
                self.driver.execute_script(f"window.scrollTo(0, {scroll_position});")

                # 이미지 로딩 대기 - 네트워크 활동이 안정될 때까지
                self._wait_for_images_to_load(max_wait_per_scroll)

                # 페이지 높이가 변경되었는지 확인 (동적 로딩)
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height > last_height:
                    last_height = new_height

            # 마지막으로 페이지 끝까지 스크롤
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self._wait_for_images_to_load(max_wait_per_scroll)

            print("✅ 모든 이미지 로딩 완료")

        except Exception as e:
            print(f"⚠️  스크롤 중 오류: {e}")

    def _wait_for_images_to_load(self, max_wait=3):
        """
        이미지가 실제로 로드될 때까지 대기

        Args:
            max_wait: 최대 대기 시간 (초)
        """
        try:
            # 방법 1: img.s-lazy 이미지의 src가 data-src가 아닌 실제 URL로 변경될 때까지 대기
            wait = WebDriverWait(self.driver, max_wait)

            # 로딩되지 않은 이미지 확인
            unloaded_images_script = """
                return Array.from(document.querySelectorAll('img.s-lazy')).filter(img => {
                    const src = img.getAttribute('src') || '';
                    const dataSrc = img.getAttribute('data-src') || '';
                    // src가 비어있거나 placeholder인 경우
                    return src === '' || src.includes('placeholder') || src.includes('loading');
                }).length;
            """

            # 짧은 간격으로 체크하면서 이미지가 로드되기를 기다림
            start_time = time.time()
            while time.time() - start_time < max_wait:
                unloaded_count = self.driver.execute_script(unloaded_images_script)

                if unloaded_count == 0:
                    # 모든 이미지 로드 완료
                    break

                time.sleep(0.1)  # 100ms 간격으로 체크

        except Exception as e:
            # 타임아웃이나 다른 오류 발생 시 그냥 짧게 대기
            time.sleep(0.3)

    def extract_product_images(self) -> List[str]:
        """
        상품 설명 이미지 URL 추출

        Returns:
            이미지 URL 리스트
        """
        print("📸 상품 설명 이미지 URL 추출 중...")
        image_urls = []

        # 성능 개선: implicit wait를 임시로 0으로 설정 (빠른 검색)
        original_implicit_wait = self.driver.timeouts.implicit_wait
        self.driver.implicitly_wait(0)

        try:
            # 여러 가능한 선택자 시도 (올리브영 페이지 구조 기반)
            selectors = [
                # 상품 설명 영역의 이미지들 (실제 HTML 구조 기반)
                "img.s-lazy",                           # s-lazy 클래스 이미지 (최우선)
                ".detail_cont img",                    # 상세 설명 컨테이너
                "#artcInfo img",                        # 상품 정보 영역
                ".prd_detail_box img",                  # 상품 상세 박스
                ".detail_info_wrap img",                # 상세 정보 래퍼
                "#gdasDetail img",                      # 상품 상세 ID
                ".goods_detail_cont img",               # 상품 상세 컨텐츠
                "#detail_img_expand img",               # 확장 이미지 영역
                ".prd_detail img",                      # 상품 상세
                "div[class*='detail'] img",             # detail 클래스 포함하는 div 안의 이미지
                "div[id*='detail'] img",                # detail ID 포함하는 div 안의 이미지
                "img[src*='amc.apglobal.com']",        # AMC CDN 이미지
                "img[src*='asset']",                    # asset 경로 이미지
            ]

            # 모든 selector를 시도하고 총 이미지 면적이 가장 큰 것 선택
            best_images = []
            best_selector = None
            best_total_area = 0

            for selector in selectors:
                try:
                    found_images = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if not found_images:
                        print(f"  '{selector}': 이미지 없음")
                        continue

                    # 총 면적 계산 (width * height 합계) - JavaScript로 한 번에 계산
                    total_area = self.driver.execute_script("""
                        const images = arguments[0];
                        return images.reduce((sum, img) => {
                            const w = img.naturalWidth || img.width || 0;
                            const h = img.naturalHeight || img.height || 0;
                            return sum + (w * h);
                        }, 0);
                    """, found_images)

                    print(f"  '{selector}': {len(found_images)}개 이미지, 총 면적 {total_area:,}px²")

                    # 총 면적이 가장 큰 selector 선택
                    if total_area > best_total_area:
                        best_images = found_images
                        best_selector = selector
                        best_total_area = total_area

                except Exception as e:
                    print(f"  '{selector}': 오류 - {e}")
                    continue

            images = best_images
            if images:
                print(f"✅ 최종 선택: '{best_selector}'로 {len(images)}개 이미지 사용 (총 면적: {best_total_area:,}px²)")
            else:
                print("⚠️ 모든 selector에서 이미지를 찾지 못함")

            if not images:
                print("❌ 상품 설명 이미지를 찾을 수 없습니다")
                print("현재 페이지 URL:", self.driver.current_url)
                print("페이지 타이틀:", self.driver.title)
                # 페이지 소스 일부 저장 (디버깅용)
                try:
                    with open("debug_page_source.html", "w", encoding="utf-8") as f:
                        f.write(self.driver.page_source)
                    print("📁 디버깅용 페이지 소스 저장: debug_page_source.html")
                except:
                    pass
                return []

            # 이미지 URL 추출 (중복 제거를 위해 set 사용 후 순서 유지)
            seen_urls = set()
            for idx, img in enumerate(images):
                try:
                    # src 또는 data-src 속성 확인
                    img_url = img.get_attribute("src") or img.get_attribute("data-src")

                    if img_url and img_url.startswith("http"):
                        # 중복 URL 체크
                        if img_url in seen_urls:
                            print(f"  {idx+1}. [중복 제외] {img_url[:80]}...")
                            continue

                        # APGLOBAL 에셋 예외 처리
                        is_apglobal_asset = "amc.apglobal.com" in img_url

                        # 너무 작은 이미지는 제외 (로딩 스피너, 아이콘, 구분선 등)
                        width = img.get_attribute("width")
                        height = img.get_attribute("height")
                        style = img.get_attribute("style") or ""

                        # 필터링 로직
                        should_include = False
                        reason = ""
                        filter_reason = ""

                        # width 체크
                        width_ok = False
                        if "width:100%" in style.replace(" ", "") or "width: 100%" in style:
                            width_ok = True
                            reason = "width: 100%"
                        elif width:
                            try:
                                width_val = int(width)
                                if width_val >= 100:
                                    width_ok = True
                                    reason = f"w:{width}"
                                else:
                                    filter_reason = f"width too small: {width}px"
                            except:
                                width_ok = True
                                reason = f"w:{width}"
                        else:
                            width_ok = True
                            reason = "no width"

                        # height 체크 (무의미한 이미지 필터링)
                        height_ok = True
                        if height:
                            try:
                                height_val = int(height)
                                if height_val < 50:
                                    height_ok = False
                                    filter_reason = f"height too small: {height}px (divider/spacer)"
                                else:
                                    reason += f", h:{height}"
                            except:
                                pass

                        # aspect ratio 체크 (극단적인 비율 제외 - 예: 800x4)
                        aspect_ok = True
                        if width and height:
                            try:
                                width_val = int(width)
                                height_val = int(height)
                                if height_val > 0:
                                    aspect_ratio = width_val / height_val
                                    if aspect_ratio > 50:
                                        aspect_ok = False
                                        filter_reason = f"extreme aspect: {width_val}x{height_val} (ratio:{aspect_ratio:.0f}:1)"
                            except:
                                pass

                        should_include = width_ok and height_ok and aspect_ok

                        if should_include or is_apglobal_asset:
                            image_urls.append(img_url)
                            seen_urls.add(img_url)
                            if is_apglobal_asset and not should_include:
                                print(f"  {idx+1}. [APGLOBAL 포함] {img_url[:80]}... (필터링 규칙 무시)")
                            else:
                                print(f"  {idx+1}. {img_url[:80]}... ({reason})")
                        else:
                            print(f"  {idx+1}. [필터링 제외] {filter_reason} - {img_url[:80]}...")

                except Exception as e:
                    print(f"  ⚠️  {idx+1}번 이미지 추출 실패: {e}")
                    continue

            print(f"✅ 총 {len(image_urls)}개 이미지 URL 추출 완료 (중복 제거됨)")

            # 디버깅: URL 리스트 저장
            if image_urls:
                try:
                    with open("debug_image_urls.txt", "w", encoding="utf-8") as f:
                        for i, url in enumerate(image_urls, 1):
                            f.write(f"{i}. {url}\n")
                    print("📁 디버깅용 URL 리스트 저장: debug_image_urls.txt")
                except:
                    pass

        except Exception as e:
            print(f"❌ 이미지 추출 중 오류: {e}")

        finally:
            # implicit wait 원래대로 복구
            self.driver.implicitly_wait(original_implicit_wait)

        return image_urls

    def _calculate_color_similarity(self, img1: Image.Image, img2: Image.Image) -> float:
        """
        두 이미지의 경계 색상 유사도 계산
        img1의 마지막 줄과 img2의 첫 줄의 평균 색상을 비교

        Args:
            img1: 위쪽 이미지
            img2: 아래쪽 이미지

        Returns:
            유사도 (0.0 ~ 1.0, 1.0이 완전 동일)
        """
        try:
            # img1의 마지막 10줄 평균 색상
            bottom_crop = img1.crop((0, max(0, img1.height - 10), img1.width, img1.height))
            bottom_color = bottom_crop.resize((1, 1)).getpixel((0, 0))

            # img2의 첫 10줄 평균 색상
            top_crop = img2.crop((0, 0, img2.width, min(10, img2.height)))
            top_color = top_crop.resize((1, 1)).getpixel((0, 0))

            # RGB 차이 계산 (유클리드 거리)
            r_diff = abs(bottom_color[0] - top_color[0])
            g_diff = abs(bottom_color[1] - top_color[1])
            b_diff = abs(bottom_color[2] - top_color[2])

            # 평균 차이 (0 ~ 255)
            avg_diff = (r_diff + g_diff + b_diff) / 3

            # 유사도로 변환 (0 ~ 1.0)
            similarity = 1.0 - (avg_diff / 255.0)

            return similarity

        except Exception as e:
            print(f"    ⚠️ 색상 유사도 계산 실패: {e}")
            return 0.5  # 실패 시 중간값 반환

    def _split_images_by_context(self, images: List[Image.Image], similarity_threshold: float = 0.85) -> List[List[Image.Image]]:
        """
        이미지를 문맥(색상 유사도)에 따라 그룹으로 분할
        (수정됨: 이제 높이 제한이 있을 때만 분할을 고려)

        Args:
            images: 이미지 리스트
            similarity_threshold: 유사도 임계값 (현재는 로깅용)

        Returns:
            이미지 그룹 리스트
        """
        if not images:
            return []

        MAX_HEIGHT = 60000  # Pillow 최대 높이 (안전 마진 포함)

        groups = []
        current_group = [images[0]]
        current_height = images[0].height

        print(f"\n🎨 이미지 문맥 분석 중... (유사도 임계값: {similarity_threshold:.2f})")

        for i in range(1, len(images)):
            prev_img = images[i - 1]
            curr_img = images[i]

            # 높이 체크
            would_exceed = (current_height + curr_img.height) > MAX_HEIGHT

            # 분할 결정: 높이 초과 여부만으로 판단
            if not would_exceed:
                # 높이가 충분하면 현재 그룹에 추가
                current_group.append(curr_img)
                current_height += curr_img.height
                
                # 유사도는 참고용으로만 계산 및 로깅
                similarity = self._calculate_color_similarity(prev_img, curr_img)
                print(f"  [{i}/{len(images)-1}] 유사도: {similarity:.2f} → 같은 그룹 (누적 높이: {current_height}px)")
            else:
                # 높이 초과 시 새 그룹 시작
                groups.append(current_group)
                reason = "높이 초과"
                
                # 유사도 계산 (로깅용)
                similarity = self._calculate_color_similarity(prev_img, curr_img)
                print(f"  [{i}/{len(images)-1}] {reason} (유사도: {similarity:.2f}) → 새 그룹 시작")
                
                current_group = [curr_img]
                current_height = curr_img.height

        # 마지막 그룹 추가
        if current_group:
            groups.append(current_group)

        print(f"✅ 총 {len(groups)}개 그룹으로 분할")
        for idx, group in enumerate(groups, 1):
            total_h = sum(img.height for img in group)
            print(f"  그룹 {idx}: {len(group)}개 이미지, 총 높이 {total_h}px")

        return groups

    def _split_images_by_tile_layout(self, images: List[Image.Image], display_resolution: str = "1920x1080") -> List[List[Image.Image]]:
        """
        16:9 비율 기반 지능적 컬럼 배치로 이미지 분할

        Args:
            images: 이미지 리스트
            display_resolution: 디스플레이 해상도 ("1920x1080", "2560x1440", "3840x2160")

        Returns:
            이미지 그룹 리스트 - 각 그룹이 하나의 타일
        """
        if not images:
            return []

        print(f"\n🖥️ 16:9 비율 기반 타일 레이아웃 분할 ({display_resolution})")

        # 첫 유효 이미지의 가로 길이 확인
        first_valid_width = None
        for img in images:
            if img.width >= 100 and img.height >= 50:  # 유효한 이미지
                first_valid_width = img.width
                break

        if not first_valid_width:
            print("⚠️ 유효한 이미지가 없습니다")
            return [images]  # 전체를 하나의 그룹으로

        print(f"  첫 유효 이미지 가로: {first_valid_width}px")

        # 컬럼 개수 계산 (2열 기본)
        num_columns = 2
        total_width = first_valid_width * num_columns

        print(f"  컬럼 개수: {num_columns}개")
        print(f"  타일 가로: {total_width}px")

        # 목표 높이 범위 계산 (16:9 ~ 16:10 + 30% 여유)
        target_height_16_9 = int(total_width / 16 * 9)
        target_height_16_10 = int(total_width / 16 * 10)
        target_height_max = int(target_height_16_10 * 1.3)  # 30% 여유

        print(f"  목표 높이 범위: {target_height_16_9}px ~ {target_height_max}px")
        print(f"    (16:9={target_height_16_9}px, 16:10={target_height_16_10}px, +30%={target_height_max}px)")

        # 그룹 생성
        groups = []
        current_tile_columns = [[] for _ in range(num_columns)]
        column_heights = [0] * num_columns

        image_idx = 0

        while image_idx < len(images):
            img = images[image_idx]
            img_height = img.height

            # 가장 높이가 낮은 컬럼 찾기
            min_col_idx = column_heights.index(min(column_heights))
            min_col_height = column_heights[min_col_idx]

            # 해당 컬럼에 추가했을 때 최대 높이 계산
            would_be_height = min_col_height + img_height
            max_would_be = max(
                column_heights[i] if i != min_col_idx else would_be_height
                for i in range(num_columns)
            )

            # 추가 가능 여부 판단
            can_add = max_would_be <= target_height_max

            if can_add:
                # 컬럼에 이미지 추가
                current_tile_columns[min_col_idx].append(img)
                column_heights[min_col_idx] += img_height
                print(f"  [{image_idx+1}/{len(images)}] 컬럼{min_col_idx+1}에 추가: {img.width}x{img_height}px (컬럼높이: {column_heights[min_col_idx]}px)")
                image_idx += 1
            else:
                # 현재 타일 완성 - 모든 컬럼이 목표 범위 초과
                flat_group = []
                for col in current_tile_columns:
                    flat_group.extend(col)

                if flat_group:
                    max_height = max(column_heights)
                    groups.append(flat_group)
                    print(f"  📦 타일 {len(groups)} 완성: {len(flat_group)}개 이미지, 최대높이 {max_height}px")
                    for i, col in enumerate(current_tile_columns):
                        print(f"     컬럼{i+1}: {len(col)}개, {column_heights[i]}px")

                # 새 타일 시작
                current_tile_columns = [[] for _ in range(num_columns)]
                column_heights = [0] * num_columns

        # 마지막 타일 저장
        flat_group = []
        for col in current_tile_columns:
            flat_group.extend(col)

        if flat_group:
            max_height = max(column_heights)
            groups.append(flat_group)
            print(f"  📦 타일 {len(groups)} 완성: {len(flat_group)}개 이미지, 최대높이 {max_height}px")
            for i, col in enumerate(current_tile_columns):
                print(f"     컬럼{i+1}: {len(col)}개, {column_heights[i]}px")

        print(f"✅ 총 {len(groups)}개 타일로 분할")
        return groups

    def download_and_merge_images(self, image_urls: List[str], output_path: str, progress_callback=None,
                                   split_mode: str = "context", display_resolution: str = "1920x1080") -> str:
        """
        이미지들을 다운로드하고 선택한 모드에 따라 분할하여 병합

        Args:
            image_urls: 이미지 URL 리스트
            output_path: 저장할 파일 경로 (기본 경로, _part1, _part2 등으로 저장됨)
            progress_callback: 진행 상황을 전달할 콜백 함수 (message, current, total)
            split_mode: 분할 모드 ("context": 문맥 기반, "tile": 타일 레이아웃)
            display_resolution: 타일 모드일 때 사용할 해상도 ("1920x1080", "2560x1440", "3840x2160")

        Returns:
            저장된 파일 경로 (여러 개인 경우 첫 번째 파일 경로)
        """
        if not image_urls:
            print("❌ 병합할 이미지가 없습니다")
            return ""

        print(f"\n📥 이미지 다운로드 및 병합 시작 (총 {len(image_urls)}개)...")
        print(f"⚡ 병렬 다운로드 시작 (최대 10개 동시)")

        # 단일 이미지 다운로드 함수
        def download_single_image(url, idx):
            """단일 이미지 다운로드"""
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()

                img = Image.open(BytesIO(response.content))

                # RGB로 변환
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                return idx, img, None
            except Exception as e:
                return idx, None, str(e)

        # 병렬 다운로드 (순서 유지를 위해 idx 기반 딕셔너리 사용)
        images_dict = {}
        max_width = 0
        completed_count = 0

        with ThreadPoolExecutor(max_workers=10) as executor:
            # 모든 다운로드 작업 제출
            future_to_idx = {
                executor.submit(download_single_image, url, idx): idx
                for idx, url in enumerate(image_urls)
            }

            # 완료되는 대로 처리
            for future in as_completed(future_to_idx):
                idx, img, error = future.result()
                completed_count += 1

                if progress_callback:
                    progress_callback(
                        f"💾 이미지 다운로드 중... [{completed_count}/{len(image_urls)}]",
                        completed_count,
                        len(image_urls)
                    )

                if error:
                    print(f"  [{idx+1}/{len(image_urls)}] ⚠️  다운로드 실패: {error}")
                else:
                    images_dict[idx] = img
                    max_width = max(max_width, img.width)
                    print(f"  [{idx+1}/{len(image_urls)}] ✅ 크기: {img.width}x{img.height}")

        # 순서대로 정렬하여 리스트로 변환
        images = [images_dict[i] for i in sorted(images_dict.keys())]

        print(f"✅ 다운로드 완료: {len(images)}/{len(image_urls)}개 성공")

        if not images:
            print("❌ 다운로드된 이미지가 없습니다")
            return ""

        # 분할 모드에 따라 그룹 분할
        if split_mode == "tile":
            print(f"🖥️ 타일 레이아웃 모드 선택됨 (해상도: {display_resolution})")
            image_groups = self._split_images_by_tile_layout(images, display_resolution)
        else:
            print("🎨 문맥 기반 분할 모드 선택됨")
            image_groups = self._split_images_by_context(images, similarity_threshold=0.85)

        # 각 그룹별로 병합
        saved_paths = []
        base_path = output_path.replace('.jpg', '').replace('.jpeg', '')

        for group_idx, group in enumerate(image_groups, 1):
            # 파일명 결정
            if len(image_groups) == 1:
                # 그룹이 1개면 원본 파일명 사용
                file_path = output_path
            else:
                # 여러 그룹이면 _part1, _part2 등으로 저장
                file_path = f"{base_path}_part{group_idx}.jpg"

            if progress_callback:
                progress_callback(f"🔨 그룹 {group_idx}/{len(image_groups)} 병합 중... ({len(group)}개 이미지)",
                                len(image_urls), len(image_urls))

            print(f"\n🔨 그룹 {group_idx}/{len(image_groups)} 병합 중...")
            print(f"  이미지 개수: {len(group)}개")

            # 타일 모드일 때 컬럼 기반 배치
            if split_mode == "tile":
                # 첫 유효 이미지 가로 확인
                first_valid_width = None
                for img in group:
                    if img.width >= 100 and img.height >= 50:
                        first_valid_width = img.width
                        break

                if not first_valid_width:
                    first_valid_width = group[0].width

                # 2열 배치
                num_columns = 2
                total_width = first_valid_width * num_columns

                # 컬럼별로 이미지 분배 (타일링과 동일한 Best Fit 로직)
                columns = [[] for _ in range(num_columns)]
                column_heights = [0] * num_columns

                for img in group:
                    # 가장 높이가 낮은 컬럼에 추가
                    min_idx = column_heights.index(min(column_heights))
                    columns[min_idx].append(img)
                    column_heights[min_idx] += img.height

                # 최종 캔버스 크기 계산
                max_column_height = max(column_heights)

                print(f"  컬럼 개수: {num_columns}개")
                print(f"  병합 크기: {total_width}x{max_column_height}px")
                for i in range(num_columns):
                    print(f"    컬럼{i+1}: {len(columns[i])}개, {column_heights[i]}px")

                # 캔버스 생성
                merged_image = Image.new('RGB', (total_width, max_column_height), 'white')

                # 컬럼별로 이미지 배치
                current_x = 0
                for col_idx, column in enumerate(columns):
                    if not column:
                        continue

                    current_y = 0
                    for img in column:
                        # 왼쪽 정렬
                        merged_image.paste(img, (current_x, current_y))
                        current_y += img.height

                    current_x += first_valid_width

            else:
                # 문맥 모드 - 기존 방식 (세로로 쌓기)
                group_height = sum(img.height for img in group)
                group_width = max(img.width for img in group)

                print(f"  병합 크기: {group_width}x{group_height}px")

                # 캔버스 생성
                merged_image = Image.new('RGB', (group_width, group_height), 'white')

                # 이미지 붙이기
                current_y = 0
                for idx, img in enumerate(group):
                    # 중앙 정렬
                    x_offset = (group_width - img.width) // 2
                    merged_image.paste(img, (x_offset, current_y))
                    current_y += img.height
                    print(f"  [{idx+1}/{len(group)}] 병합 완료")

            # 저장
            merged_image.save(file_path, 'JPEG', quality=95, optimize=True)
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB

            print(f"  ✅ 저장 완료: {file_path}")
            print(f"  💾 파일 크기: {file_size:.2f} MB")

            saved_paths.append(file_path)

        # 병합 완료 알림
        if progress_callback:
            if len(saved_paths) == 1:
                progress_callback(f"✅ 병합 완료! (1개 파일)", len(image_urls), len(image_urls))
            else:
                progress_callback(f"✅ 병합 완료! ({len(saved_paths)}개 파일로 분할)", len(image_urls), len(image_urls))

        print(f"\n✅ 전체 병합 완료!")
        print(f"  📁 저장된 파일: {len(saved_paths)}개")
        for idx, path in enumerate(saved_paths, 1):
            print(f"    {idx}. {path}")

        # 첫 번째 파일 경로 반환 (호환성)
        return saved_paths[0] if saved_paths else ""

    def extract_product_info_from_detail(self) -> Dict:
        """
        상세 페이지에서 상품 기본 정보 추출

        Returns:
            상품 정보 딕셔너리
        """
        print("\n📋 상품 정보 추출 중...")
        product_info = {}

        try:
            # 상품명
            try:
                name_elem = self.driver.find_element(By.CSS_SELECTOR, ".prd_name")
                product_info["상품명"] = name_elem.text.strip()
            except:
                product_info["상품명"] = "정보 없음"

            # 브랜드
            try:
                brand_elem = self.driver.find_element(By.CSS_SELECTOR, ".prd_brand")
                product_info["브랜드"] = brand_elem.text.strip()
            except:
                product_info["브랜드"] = "정보 없음"

            # 가격
            try:
                price_elem = self.driver.find_element(By.CSS_SELECTOR, ".price")
                product_info["가격"] = price_elem.text.strip()
            except:
                product_info["가격"] = "정보 없음"

            # URL
            product_info["URL"] = self.driver.current_url

            print(f"✅ 상품명: {product_info['상품명']}")
            print(f"   브랜드: {product_info['브랜드']}")
            print(f"   가격: {product_info['가격']}")

        except Exception as e:
            print(f"⚠️  상품 정보 추출 중 오류: {e}")

        return product_info
