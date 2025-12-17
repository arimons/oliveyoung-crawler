"""
올리브영 리뷰 크롤러
상품 리뷰를 모든 페이지에서 수집
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import List, Dict, Tuple
from datetime import datetime
import time
import requests
import re
import math
import json
import html


class ReviewCrawler:
    """리뷰 크롤링 클래스"""

    def __init__(self, driver, log_callback=None):
        """
        Args:
            driver: Selenium WebDriver 인스턴스
        """
        self.driver = driver
        self.log_callback = log_callback

    def click_review_tab(self) -> bool:
        """
        리뷰 탭 클릭

        Returns:
            성공 여부
        """
        try:
            print("\n📝 리뷰 탭 클릭 중...")

            # 리뷰 탭 찾기
            wait = WebDriverWait(self.driver, 10)
            review_tab = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a.goods_reputation"))
            )

            # 탭이 보이도록 스크롤
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", review_tab)
            time.sleep(1)

            # 클릭
            review_tab.click()
            print("✅ 리뷰 탭 클릭 완료")
            time.sleep(2)  # 리뷰 로딩 대기

            return True

        except Exception as e:
            print(f"⚠️  리뷰 탭 클릭 실패: {e}")
            return False

    def select_latest_sort(self) -> bool:
        """
        리뷰 정렬을 '최신순'으로 변경 (JavaScript 강제 처리)

        Returns:
            성공 여부
        """
        try:
            print("🔄 리뷰 정렬을 '최신순'으로 변경 중... (JavaScript 강제 처리)")

            # JavaScript로 강력한 최신순 정렬 처리
            success = self.driver.execute_script("""
                console.log('🔄 최신순 정렬 JavaScript 처리 시작');
                
                let sortClicked = false;
                
                // ========== 기본 선택자들 ==========
                const basicSelectors = [
                    "#gdasSort > li:nth-child(3) > a",  // 사용자 제공 선택자 (최신순)
                    "a[data-sort-type-code='latest']",
                    "a[data-value='02']",
                    "a[data-sort='latest']", 
                    "button[data-sort='latest']",
                    "option[value='latest']",
                    "option[value='LATEST']"
                ];
                
                // 기본 선택자로 먼저 시도
                for (let selector of basicSelectors) {
                    try {
                        const elem = document.querySelector(selector);
                        if (elem) {
                            elem.scrollIntoView({ block: 'center', behavior: 'smooth' });
                            
                            if (elem.tagName.toLowerCase() === 'option') {
                                const select = elem.closest('select');
                                if (select) {
                                    select.value = elem.value;
                                    select.dispatchEvent(new Event('change', { bubbles: true }));
                                    console.log(`✅ 최신순 정렬 선택 (select): ${selector}`);
                                } else {
                                    elem.click();
                                    console.log(`✅ 최신순 정렬 클릭: ${selector}`);
                                }
                            } else {
                                elem.click();
                                console.log(`✅ 최신순 정렬 클릭: ${selector}`);
                            }
                            
                            sortClicked = true;
                            break;
                        }
                    } catch (e) {
                        console.log(`⚠️ 기본 선택자 실패 (${selector}): ${e.message}`);
                    }
                }
                
                // ========== 텍스트 기반 검색 ==========
                if (!sortClicked) {
                    const sortTextPatterns = [
                        '최신순', '최신 순', '최신', '최신등록순', 
                        'newest', 'latest', 'recent', '등록순'
                    ];
                    
                    const allElements = document.querySelectorAll('*');
                    for (let elem of allElements) {
                        const text = elem.textContent || '';
                        const tagName = elem.tagName.toLowerCase();
                        
                        // 클릭 가능한 요소만 확인
                        if (['button', 'a', 'option', 'li', 'span', 'div'].includes(tagName)) {
                            for (let pattern of sortTextPatterns) {
                                if (text.trim() === pattern || (text.includes(pattern) && text.length < 20)) {
                                    try {
                                        elem.scrollIntoView({ block: 'center', behavior: 'smooth' });
                                        
                                        if (tagName === 'option') {
                                            const select = elem.closest('select');
                                            if (select) {
                                                select.value = elem.value;
                                                select.dispatchEvent(new Event('change', { bubbles: true }));
                                                console.log(`✅ 최신순 정렬 선택 (텍스트기반 select): ${text.trim()}`);
                                            }
                                        } else {
                                            elem.click();
                                            console.log(`✅ 최신순 정렬 클릭 (텍스트기반 ${tagName}): ${text.trim()}`);
                                        }
                                        
                                        sortClicked = true;
                                        break;
                                    } catch (e) {
                                        console.log(`⚠️ 텍스트기반 클릭 실패 (${text.trim()}): ${e.message}`);
                                    }
                                }
                            }
                            if (sortClicked) break;
                        }
                    }
                }
                
                // ========== 정렬 드롭다운 찾기 ==========
                if (!sortClicked) {
                    const sortDropdowns = document.querySelectorAll('select, .dropdown, .sort-select');
                    for (let dropdown of sortDropdowns) {
                        const text = dropdown.textContent || '';
                        if (text.includes('정렬') || text.includes('순서') || text.includes('sort')) {
                            try {
                                // select 요소인 경우
                                if (dropdown.tagName.toLowerCase() === 'select') {
                                    const options = dropdown.querySelectorAll('option');
                                    for (let option of options) {
                                        const optText = option.textContent || '';
                                        if (optText.includes('최신')) {
                                            dropdown.value = option.value;
                                            dropdown.dispatchEvent(new Event('change', { bubbles: true }));
                                            console.log(`✅ 드롭다운에서 최신순 선택: ${optText.trim()}`);
                                            sortClicked = true;
                                            break;
                                        }
                                    }
                                } else {
                                    // 일반 드롭다운 클릭
                                    dropdown.click();
                                    console.log(`✅ 정렬 드롭다운 클릭: ${text.trim()}`);
                                    
                                    // 클릭 후 최신순 옵션 찾기
                                    setTimeout(() => {
                                        const newOptions = document.querySelectorAll('*');
                                        for (let opt of newOptions) {
                                            const optText = opt.textContent || '';
                                            if (optText.includes('최신') && optText.length < 15) {
                                                try {
                                                    opt.click();
                                                    console.log(`✅ 드롭다운에서 최신순 선택: ${optText.trim()}`);
                                                    sortClicked = true;
                                                    break;
                                                } catch (e) {}
                                            }
                                        }
                                    }, 500);
                                }
                                if (sortClicked) break;
                            } catch (e) {
                                console.log(`⚠️ 드롭다운 처리 실패: ${e.message}`);
                            }
                        }
                    }
                }
                
                console.log(`🎯 최신순 정렬 결과: ${sortClicked}`);
                return sortClicked;
            """)

            if success:
                print("  ✅ JavaScript 최신순 정렬 성공")
                time.sleep(2)  # 리뷰 재로딩 대기
                return True
            else:
                print("  ⚠️ JavaScript 최신순 정렬 실패")
                return False

        except Exception as e:
            print(f"⚠️  JavaScript 정렬 처리 실패: {e}")
            return False

    def get_current_page_numbers(self) -> List[int]:
        """
        현재 표시된 페이지 번호들 가져오기 (1-10, 11-20 등)

        Returns:
            페이지 번호 리스트
        """
        try:
            # 페이지 번호 링크들 찾기
            page_links = self.driver.find_elements(By.CSS_SELECTOR, "a[data-page-no]")
            page_numbers = []

            print(f"    🔍 총 {len(page_links)}개 페이지 링크 발견")

            for link in page_links:
                try:
                    class_name = link.get_attribute('class') or ''
                    page_no = int(link.get_attribute("data-page-no"))

                    # 디버깅: 각 링크 정보 출력
                    print(f"       - 페이지 {page_no}, class='{class_name}'", end="")

                    # 'next' 또는 'prev' 클래스가 있는 버튼은 제외
                    if 'next' in class_name or 'prev' in class_name:
                        print(" → 제외 (next/prev)")
                        continue

                    print(" → 포함")
                    page_numbers.append(page_no)
                except Exception as e:
                    print(f"       - 링크 처리 실패: {e}")
                    continue

            # 현재 활성 페이지 확인 (링크가 아닌 요소로 표시됨)
            # 여러 패턴 시도
            current_page = None

            # 방법 1: 페이지네이션 영역에서 strong 태그 찾기
            try:
                pageing_area = self.driver.find_element(By.CSS_SELECTOR, "div.pageing")
                strong_elem = pageing_area.find_element(By.CSS_SELECTOR, "strong")
                current_page = int(strong_elem.text.strip())
                print(f"       - 페이지 {current_page}, (현재 활성 페이지 - strong) → 포함")
            except:
                pass

            # 방법 2: 'on' 또는 'active' 클래스가 붙은 요소 찾기
            if current_page is None:
                try:
                    active_elem = self.driver.find_element(By.CSS_SELECTOR, "a.on, a.active, span.on, span.active")
                    current_page = int(active_elem.text.strip())
                    print(f"       - 페이지 {current_page}, (현재 활성 페이지 - on/active) → 포함")
                except:
                    pass

            # 방법 3: JavaScript로 직접 확인
            if current_page is None:
                try:
                    current_page = self.driver.execute_script(r"""
                        const pageing = document.querySelector('div.pageing');
                        if (!pageing) return null;

                        // strong 태그 찾기
                        const strong = pageing.querySelector('strong');
                        if (strong && /^\d+$/.test(strong.textContent.trim())) {
                            return parseInt(strong.textContent.trim());
                        }

                        // on/active 클래스 찾기
                        const active = pageing.querySelector('.on, .active');
                        if (active && /^\d+$/.test(active.textContent.trim())) {
                            return parseInt(active.textContent.trim());
                        }

                        return null;
                    """)
                    if current_page:
                        print(f"       - 페이지 {current_page}, (현재 활성 페이지 - JS) → 포함")
                except:
                    pass

            if current_page is None:
                print(f"       - 현재 활성 페이지 확인 실패 (모든 방법 실패)")
            else:
                page_numbers.append(current_page)

            result = sorted(set(page_numbers))  # 중복 제거 및 정렬
            print(f"    ✅ 최종 페이지 목록: {result}")
            return result

        except Exception as e:
            print(f"⚠️  페이지 번호 확인 중 오류: {e}")
            return []

    def click_next_10_pages(self) -> bool:
        """
        '다음 10 페이지' 버튼 클릭

        Returns:
            성공 여부 (버튼이 없으면 False)
        """
        try:
            # 'next' 버튼 찾기
            next_button = self.driver.find_element(By.CSS_SELECTOR, "a.next[data-page-no]")

            # 버튼이 보이도록 스크롤
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
            time.sleep(0.5)

            # 클릭
            next_button.click()
            print(f"✅ 다음 10페이지 버튼 클릭")
            time.sleep(2)  # 페이지 로딩 대기

            return True

        except Exception:
            # 버튼이 없으면 False 반환 (마지막 페이지 그룹)
            return False

    def extract_reviews_from_current_page(self) -> List[str]:
        """
        현재 페이지의 리뷰 텍스트 추출

        Returns:
            리뷰 텍스트 리스트
        """
        reviews = []

        try:
            # 리뷰 텍스트 요소들 찾기
            review_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.txt_inner")

            # Stale Element 에러 방지: 텍스트를 즉시 추출하여 리스트로 저장
            review_texts = []
            for element in review_elements:
                try:
                    text = element.text.strip()
                    review_texts.append(text)
                except Exception:
                    review_texts.append("")  # 실패 시 빈 문자열

            # 추출한 텍스트 처리
            for review_text in review_texts:
                if review_text:
                    reviews.append(review_text)

        except Exception as e:
            print(f"⚠️  리뷰 추출 중 오류: {e}")

        return reviews

    def extract_reviews_with_date_filter(self, end_date: str = None) -> Tuple[List[Dict[str, str]], bool]:
        """
        현재 페이지의 리뷰 텍스트 추출 (날짜 필터링 포함)

        Args:
            end_date: 수집 종료 날짜 (예: "2025.11.01", None이면 전체 수집)

        Returns:
            (리뷰 딕셔너리 리스트 [{"text": "...", "date": "..."}], 종료 날짜 도달 여부)
        """
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        reviews = []
        reached_end_date = False

        try:
            # 명시적 대기: 리뷰 컨테이너가 로드될 때까지 최대 10초 대기
            print(f"    ⏳ 리뷰 로딩 대기 중...")
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "ul#gdasList"))
            )
            time.sleep(1)  # 추가 안정화 대기

            # 리뷰 리스트의 li 태그들 찾기
            review_containers = self.driver.find_elements(By.CSS_SELECTOR, "ul#gdasList > li")

            if not review_containers:
                print(f"    ⚠️  리뷰 컨테이너를 찾을 수 없습니다")
                # 디버깅: ul#gdasList가 존재하는지 확인
                try:
                    gdas_list = self.driver.find_element(By.CSS_SELECTOR, "ul#gdasList")
                    print(f"    🔍 ul#gdasList 존재함, 내부 HTML: {gdas_list.get_attribute('innerHTML')[:200]}...")
                except:
                    print(f"    ❌ ul#gdasList 자체를 찾을 수 없음")
                return reviews, reached_end_date

            print(f"    🔍 {len(review_containers)}개 리뷰 컨테이너 발견")

            # end_date를 datetime으로 변환 (있는 경우)
            end_date_obj = None
            if end_date:
                try:
                    end_date_obj = datetime.strptime(end_date, "%Y.%m.%d")
                    print(f"    📅 종료 날짜: {end_date} ({end_date_obj})")
                except:
                    print(f"⚠️  잘못된 날짜 형식: {end_date}. YYYY.MM.DD 형식을 사용하세요")
                    end_date_obj = None

            # 각 리뷰 처리
            for idx, container in enumerate(review_containers, 1):
                try:
                    # 리뷰 텍스트 추출
                    text_elem = None
                    try:
                        text_elem = container.find_element(By.CSS_SELECTOR, "div.txt_inner")
                    except:
                        # 디버깅: 컨테이너 HTML 확인
                        print(f"    ⚠️  리뷰 {idx}: div.txt_inner 없음")
                        print(f"         HTML: {container.get_attribute('innerHTML')[:150]}...")
                        continue

                    review_text = text_elem.text.strip()
                    if not review_text:
                        print(f"    ⚠️  리뷰 {idx}: 텍스트 비어있음")
                        continue

                    # 날짜 추출
                    review_date_str = ""
                    try:
                        date_elem = container.find_element(By.CSS_SELECTOR, "span.date")
                        review_date_str = date_elem.text.strip()
                    except:
                        print(f"    ⚠️  리뷰 {idx}: span.date 없음 (날짜 없이 수집)")

                    print(f"    📝 리뷰 {idx}: 날짜={review_date_str}, 텍스트 길이={len(review_text)}")

                    # 날짜 필터링 체크
                    if end_date_obj and review_date_str:
                        try:
                            review_date_obj = datetime.strptime(review_date_str, "%Y.%m.%d")

                            # 리뷰 날짜가 종료 날짜보다 이전이면 중단
                            if review_date_obj < end_date_obj:
                                print(f"    🛑 종료 날짜 도달: {review_date_str} < {end_date}")
                                reached_end_date = True
                                break

                        except Exception as e:
                            # 날짜 파싱 실패 시 해당 리뷰는 수집
                            print(f"    ⚠️  리뷰 {idx}: 날짜 파싱 실패 ({review_date_str}), 수집 진행")

                    # 리뷰 추가
                    reviews.append({
                        "text": review_text,
                        "date": review_date_str if review_date_str else "날짜 없음"
                    })

                except Exception as e:
                    # 개별 리뷰 추출 실패 시 건너뛰기
                    print(f"    ⚠️  리뷰 {idx} 추출 실패: {e}")
                    import traceback
                    traceback.print_exc()
                    continue

            print(f"    ✅ 총 {len(reviews)}개 리뷰 추출 완료")

        except Exception as e:
            print(f"⚠️  리뷰 추출 중 오류: {e}")
            import traceback
            traceback.print_exc()

        return reviews, reached_end_date

    def click_next_page(self, page_number: int) -> bool:
        """
        다음 페이지 클릭

        Args:
            page_number: 이동할 페이지 번호

        Returns:
            성공 여부
        """
        try:
            print(f"\n📄 {page_number}페이지로 이동 중...")

            # 페이지 번호 링크 찾기
            page_link = self.driver.find_element(
                By.CSS_SELECTOR, f"a[data-page-no='{page_number}']"
            )

            # 링크가 보이도록 스크롤
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", page_link)
            time.sleep(0.5)

            # 클릭
            page_link.click()
            print(f"✅ {page_number}페이지 클릭 완료")
            time.sleep(2)  # 페이지 로딩 대기

            return True

        except Exception as e:
            print(f"⚠️  {page_number}페이지 클릭 실패: {e}")
            return False

    def crawl_all_reviews(self, output_path: str, end_date: str = None) -> int:
        """
        모든 페이지의 리뷰 수집 (날짜 필터링 지원, 실시간 파일 저장)

        Args:
            output_path: 리뷰를 저장할 파일 경로
            end_date: 수집 종료 날짜 (예: "2025.11.01", None이면 전체 수집)

        Returns:
            수집된 총 리뷰 개수
        """
        total_count = 0

        try:
            print("\n🔍 리뷰 크롤링 시작...")
            if end_date:
                print(f"📅 {end_date}까지의 리뷰만 수집")

            # 0. 리뷰 파일 초기화
            self.init_review_file(output_path)

            # 1. 리뷰 탭 클릭
            if not self.click_review_tab():
                print("❌ 리뷰 탭을 찾을 수 없습니다")
                return 0

            # 2. 정렬 순서를 '최신순'으로 변경
            if not self.select_latest_sort():
                print("⚠️  정렬 변경 실패, 기본 정렬로 진행합니다")

            # 3. 페이지 그룹별 반복 (1-10, 11-20, 21-30, ...)
            page_group = 1
            should_stop = False

            while not should_stop:
                # 현재 표시된 페이지 번호들 가져오기
                current_pages = self.get_current_page_numbers()

                if not current_pages:
                    print("📄 더 이상 페이지가 없습니다")
                    break

                print(f"\n📚 페이지 그룹 {page_group} (페이지 {current_pages[0]}-{current_pages[-1]})")

                # 각 페이지별 리뷰 수집
                for idx, page in enumerate(current_pages):
                    print(f"  📖 {page}페이지 처리 중...")

                    # 각 페이지 그룹의 첫 페이지는 이미 표시되어 있으므로 클릭 불필요
                    # - 페이지 그룹 1: 정렬 변경 후 1페이지에 있음
                    # - 페이지 그룹 2+: "다음 10페이지" 클릭 후 첫 페이지(11, 21 등)에 있음
                    if idx != 0:
                        if not self.click_next_page(page):
                            print(f"    ⚠️  {page}페이지 이동 실패, 건너뜀")
                            continue

                    # 현재 페이지의 리뷰 추출 (날짜 필터링)
                    page_reviews, reached_end_date = self.extract_reviews_with_date_filter(end_date)

                    # 페이지별로 바로 파일에 저장 (append)
                    if page_reviews:
                        self.append_reviews_to_file(page_reviews, output_path, total_count + 1)
                        total_count += len(page_reviews)

                    print(f"    ✅ {len(page_reviews)}개 수집 (누적: {total_count}개)")

                    # 종료 날짜에 도달하면 중단
                    if reached_end_date:
                        print(f"    🛑 종료 날짜({end_date})에 도달, 수집 중단")
                        should_stop = True
                        break

                # 종료 조건 체크
                if should_stop:
                    break

                # 다음 10페이지 버튼 클릭
                if not self.click_next_10_pages():
                    print("📄 마지막 페이지 그룹입니다")
                    break

                page_group += 1

            # 4. 최종 총 개수 업데이트
            self.update_review_count(output_path, total_count, end_date)

        except Exception as e:
            print(f"❌ 리뷰 크롤링 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            # 오류 발생 시에도 지금까지 수집한 리뷰 개수 업데이트
            if total_count > 0:
                self.update_review_count(output_path, total_count, end_date)

        return total_count

    def init_review_file(self, output_path: str):
        """
        리뷰 파일 초기화 (헤더 작성)

        Args:
            output_path: 저장할 파일 경로
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"총 0개의 리뷰 (수집 중...)\n")
                f.write("=" * 80 + "\n\n")
            print(f"📝 리뷰 파일 초기화: {output_path}")
        except Exception as e:
            print(f"❌ 리뷰 파일 초기화 실패: {e}")

    def append_reviews_to_file(self, reviews: List[Dict[str, str]], output_path: str, start_idx: int):
        """
        리뷰를 파일에 추가 (append 모드)

        Args:
            reviews: 리뷰 딕셔너리 리스트 [{"text": "...", "date": "..."}]
            output_path: 저장할 파일 경로
            start_idx: 시작 인덱스
        """
        try:
            with open(output_path, 'a', encoding='utf-8') as f:
                for review in reviews:
                    # 날짜가 비어있을 경우를 대비한 기본값 처리
                    date_str = review.get('date') or datetime.now().strftime("%Y.%m.%d")
                    f.write(f"[{date_str}]\n")
                    f.write(review['text'] + "\n")
                    f.write("-" * 80 + "\n\n")
        except Exception as e:
            print(f"❌ 리뷰 추가 실패: {e}")

    def update_review_count(self, output_path: str, total_count: int, target_date: str = None):
        """
        리뷰 파일의 총 개수 업데이트

        Args:
            output_path: 파일 경로
            total_count: 총 리뷰 개수
        """
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 첫 줄만 교체
            lines = content.split('\n')
            
            today = datetime.now().strftime("%Y.%m.%d")
            period_str = f"({target_date}~{today})" if target_date else f"(전체~{today})"
            
            lines[0] = f"총 {total_count}개의 리뷰 {period_str}"

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))

            print(f"✅ 리뷰 파일 최종 저장 완료: {output_path} ({total_count}개)")

        except Exception as e:
            print(f"❌ 리뷰 개수 업데이트 실패: {e}")

    def save_review(self, output_path: str, review: dict):
        """단일 리뷰 저장 (append)"""
        try:
            with open(output_path, 'a', encoding='utf-8') as f:
                f.write(f"[{review.get('날짜', '날짜없음')}]\n")
                f.write(f"{review.get('내용', '')}\n")
                f.write("-" * 80 + "\n\n")
        except Exception as e:
            print(f"❌ 리뷰 저장 실패: {e}")

    def crawl_reviews_infinite_scroll(self, output_path: str, end_date: str = None) -> int:
        """무한 스크롤 방식으로 리뷰 수집 (실시간 수집 + 정확한 날짜 필터링)"""
        total_count = 0
        
        try:
            end_date_obj = None
            if end_date:
                try:
                    end_date_obj = datetime.strptime(end_date, "%Y.%m.%d")
                    print(f"  📅 종료 날짜: {end_date}")
                except:
                    print(f"  ⚠️ 날짜 형식 오류, 전체 수집: {end_date}")
                    end_date_obj = None

            self.init_review_file(output_path)

            # Cloudflare 체크
            print("  🔍 페이지 로딩 확인 중...")
            max_wait = 30
            wait_count = 0
            while wait_count < max_wait:
                try:
                    if "Cloudflare" in self.driver.page_source:
                        print(f"  ⏳ Cloudflare 검증 대기 ({wait_count + 1}/{max_wait}초)")
                        time.sleep(1)
                        wait_count += 1
                    else:
                        print("  ✅ 페이지 로딩 완료")
                        break
                except:
                    time.sleep(1)
                    wait_count += 1
            
            if wait_count >= max_wait:
                print("  ❌ Cloudflare 검증 시간 초과")
                return 0

            # 리뷰 탭 클릭
            print("  🎯 리뷰 탭 탐색 중...")
            try:
                review_tab = None
                try:
                    active_tab = self.driver.find_element(By.CSS_SELECTOR, "button.GoodsDetailTabs_is-activated__FuIfl")
                    if "리뷰" in active_tab.text:
                        print("  ✅ 리뷰 탭이 이미 활성화되어 있습니다.")
                        review_tab = active_tab
                except:
                    pass

                if not review_tab:
                    for selector in ["//button[contains(., '리뷰&셔터')]", "//button[contains(., '리뷰')]"]:
                        try:
                            tab = self.driver.find_element(By.XPATH, selector)
                            if tab and "리뷰" in tab.text:
                                review_tab = tab
                                print(f"  🎯 리뷰 탭 발견")
                                break
                        except:
                            continue
                
                if review_tab:
                    if "GoodsDetailTabs_is-activated" not in review_tab.get_attribute("class"):
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", review_tab)
                        time.sleep(0.5)
                        self.driver.execute_script("arguments[0].click();", review_tab)
                        print("  ✅ 리뷰 탭 클릭 완료")
                        time.sleep(2)
                else:
                    print("❌ 리뷰 탭 없음")
                    return 0
            except Exception as e:
                print(f"⚠️ 리뷰 탭 클릭 실패: {e}")
                return 0

            # 정렬 변경 (최신순)
            print("  🔍 최신순 버튼 탐색 중...")
            
            find_sort_js = """
            function findElementRecursive(root, tagName) {
                if (!root) return null;
                let found = root.querySelector(tagName);
                if (found) return found;
                let walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
                while(walker.nextNode()) {
                    let node = walker.currentNode;
                    if (node.shadowRoot) {
                        let result = findElementRecursive(node.shadowRoot, tagName);
                        if (result) return result;
                    }
                }
                return null;
            }
            return findElementRecursive(document, 'oy-review-review-sort');
            """
            
            try:
                shadow_host = self.driver.execute_script(find_sort_js)
                if not shadow_host:
                    print("  ❌ 정렬 버튼 호스트를 찾을 수 없습니다.")
                    return 0
                
                shadow_root = self.driver.execute_script("return arguments[0].shadowRoot", shadow_host)
                if not shadow_root:
                    print("  ❌ Shadow Root를 가져올 수 없습니다.")
                    return 0
                    
                buttons = shadow_root.find_elements(By.CSS_SELECTOR, "button[class*='pc-sort-button']")
                
                sort_clicked = False
                for btn in buttons:
                    try:
                        btn_text = btn.text.strip()
                        if "최신순" in btn_text:
                            self.driver.execute_script("arguments[0].click();", btn)
                            print("  ✅ '최신순' 클릭 완료")
                            time.sleep(2)  # 1초 -> 2초 대기 (안정성 확보)
                            sort_clicked = True
                            break
                    except:
                        continue
                
                if not sort_clicked:
                    print("  ❌ '최신순' 버튼을 찾을 수 없습니다")
                    return 0

            except Exception as e:
                print(f"  ❌ 정렬 버튼 로직 오류: {e}")
                return 0

            # 무한 스크롤 + 실시간 수집
            try:
                last_height = self.driver.execute_script("return document.body.scrollHeight")
            except:
                print("  ❌ 브라우저 세션 오류")
                return 0
                
            scroll_count = 0
            max_scrolls = 100
            last_date_str = "알 수 없음"
            
            find_reviews_js = """
            function findAllElementsRecursive(root, tagName) {
                let results = [];
                if (!root) return results;
                let found = root.querySelectorAll(tagName);
                if (found.length > 0) {
                    results.push(...found);
                }
                let walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
                while(walker.nextNode()) {
                    let node = walker.currentNode;
                    if (node.shadowRoot) {
                        let childResults = findAllElementsRecursive(node.shadowRoot, tagName);
                        results.push(...childResults);
                    }
                }
                return results;
            }
            return findAllElementsRecursive(document, 'oy-review-review-item');
            """

            collected_reviews = set()
            
            while scroll_count < max_scrolls:
                try:
                    # 1. 수집 (스크롤 전에 먼저 수행하여 상단 리뷰 확보)
                    try:
                        items = self.driver.execute_script(find_reviews_js)
                        
                        if items:
                            for item in items:
                                try:
                                    shadow = self.driver.execute_script("return arguments[0].shadowRoot", item)
                                    date_elem = shadow.find_element(By.CSS_SELECTOR, "span.date")
                                    review_date = date_elem.text.strip()
                                    
                                    if end_date_obj:
                                        try:
                                            date_obj = datetime.strptime(review_date, "%Y.%m.%d")
                                            if date_obj < end_date_obj:
                                                print(f"  🛑 종료 날짜 도달 ({review_date}), 수집 중단")
                                                print(f"✅ 총 {total_count}개 리뷰 수집 완료")
                                                self.update_review_count(output_path, total_count, end_date)
                                                return total_count
                                        except:
                                            pass

                                    try:
                                        content_elem = shadow.find_element(By.CSS_SELECTOR, "oy-review-review-content")
                                        content_shadow = self.driver.execute_script("return arguments[0].shadowRoot", content_elem)
                                        text_elem = content_shadow.find_element(By.CSS_SELECTOR, "p")
                                        review_text = text_elem.text.strip()
                                    except:
                                        try:
                                            review_text = shadow.find_element(By.CSS_SELECTOR, ".review_cont").text.strip()
                                        except:
                                            review_text = "내용 추출 실패"

                                    review_key = f"{review_date}_{review_text[:20]}"
                                    if review_key not in collected_reviews:
                                        self.save_review(output_path, {"날짜": review_date, "내용": review_text})
                                        collected_reviews.add(review_key)
                                        total_count += 1
                                        if total_count % 10 == 0:
                                            print(f"  💾 {total_count}개 수집 중... (현재: {review_date})")
                                            
                                    last_date_str = review_date

                                except:
                                    continue
                    except:
                        pass

                    # 2. 스크롤
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1) # 0.5초 -> 1초 대기
                    
                    # 3. 높이 확인
                    new_height = self.driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        # 한 번 더 대기 후 확인 (네트워크 지연 대비)
                        time.sleep(1)
                        new_height = self.driver.execute_script("return document.body.scrollHeight")
                        if new_height == last_height:
                            print(f"  ✅ 스크롤 완료 (마지막: {last_date_str})")
                            break
                    last_height = new_height
                    scroll_count += 1
                    
                except Exception as e:
                    if "session" in str(e).lower():
                        break
                    time.sleep(1)
                    continue
            
            print(f"✅ 총 {total_count}개 리뷰 수집 완료")
            self.update_review_count(output_path, total_count, end_date)
            
        except Exception as e:
            print(f"❌ 크롤링 오류: {e}")
            if total_count > 0:
                self.update_review_count(output_path, total_count, end_date)
        
                
        return total_count

    def crawl_reviews_via_api(self, output_path: str, end_date: str = None) -> int:
        """
        API를 직접 호출하여 리뷰 수집 (Selenium 쿠키 사용 + requests)
        스크롤 방식보다 훨씬 빠르고 안정적임
        """
        total_count = 0
        
        try:
            print("\n🚀 API 기반 리뷰 수집 시작 (Hybrid 방식)")
            
            # 1. Selenium에서 쿠키 및헤더 정보 가져오기
            cookies = self.driver.get_cookies()
            session = requests.Session()
            
            # 쿠키 설정
            for cookie in cookies:
                session.cookies.set(cookie['name'], cookie['value'])
            
            # 헤더 설정 (User-Agent 필수)
            user_agent = self.driver.execute_script("return navigator.userAgent")
            headers = {
                'User-Agent': user_agent,
                'Referer': self.driver.current_url,
                'Origin': 'https://www.oliveyoung.co.kr',
                'Host': 'www.oliveyoung.co.kr',
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Dest': 'empty',
                'Connection': 'keep-alive'
            }
            session.headers.update(headers)
            
            # 2. 상품 번호(goodsNo) 추출
            current_url = self.driver.current_url
            goods_no_match = re.search(r'goodsNo=([a-zA-Z0-9]+)', current_url)
            if not goods_no_match:
                print("❌ URL에서 goodsNo를 찾을 수 없습니다. 기존 스크롤 방식으로 전환합니다.")
                return self.crawl_reviews_infinite_scroll(output_path, end_date)
                
            goods_no = goods_no_match.group(1)
            print(f"  🔍 감지된 상품 번호: {goods_no}")
            
            # 3. 날짜 설정
            end_date_obj = None
            if end_date:
                try:
                    end_date_obj = datetime.strptime(end_date, "%Y.%m.%d")
                    print(f"  📅 수집 종료 날짜: {end_date}")
                except:
                    print(f"  ⚠️ 날짜 형식 오류, 전체 수집: {end_date}")
            
            # 4. 리뷰 파일 초기화
            self.init_review_file(output_path)
            
            # 5. API 호출 루프 (브라우저 컨텍스트 내에서 실행하여 403 우회)
            page_idx = 1
            reached_end_date = False
            
            while True:
                print(f"  📖 페이지 {page_idx} 처리 중 (Browser API)...")
                
                # 브라우저 내에서 직접 fetch 호출 (세션/쿠키/헤더 완벽 유지)
                js_script = """
                const callback = arguments[arguments.length - 1];
                const goodsNo = arguments[0];
                const pageIdx = arguments[1];
                
                const params = new URLSearchParams({
                    'goodsNo': goodsNo,
                    'gdasSort': '02',
                    'itemNo': 'all',
                    'pageIdx': pageIdx,
                    'colData': '',
                    'keyword': '',
                    'type': ''
                });

                fetch('/store/goods/getGdasNewListJson.do', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: params.toString()
                })
                .then(response => {
                    if (!response.ok) return {success: false, status: response.status};
                    return response.json().then(data => ({success: true, data: data}));
                })
                .then(result => callback(result))
                .catch(err => callback({success: false, error: err.message}));
                """
                
                try:
                    result = self.driver.execute_async_script(js_script, goods_no, page_idx)
                    
                    if not result or not result.get('success'):
                        status = result.get('status') if result else 'Unknown'
                        error_msg = result.get('error') if result else 'No result'
                        print(f"  ⚠️ Browser API 호출 실패 (Status: {status}, Error: {error_msg})")
                        raise Exception(f"Browser API Error: {status} - {error_msg}")
                    
                    data = result.get('data')
                    
                    # 리뷰 리스트 가져오기
                    review_list = data.get('gdasList', [])
                    
                    if not review_list:
                        print("  ✅ 더 이상 리뷰가 없습니다.")
                        break
                        
                    # 첫 페이지면 총 개수 확인
                    if page_idx == 1:
                        total_expected = data.get('totalCnt', 0)
                        print(f"  📊 총 리뷰 개수(API 기준): {total_expected}개")
                    
                    print(f"  📖 페이지 {page_idx} 처리 중... ({len(review_list)}개)")
                    
                    processed_reviews = []
                    
                    for review in review_list:
                        gdas_cont = review.get('gdasCont', '').strip()
                        # HTML 태그 제거 (필요시)
                        gdas_cont = re.sub('<[^>]*>', '', gdas_cont)
                        gdas_cont = html.unescape(gdas_cont)
                        
                        regist_dt = review.get('registDt', '') # 2023.12.15 형식
                        
                        processed_reviews.append({
                            "text": gdas_cont,
                            "date": regist_dt
                        })
                        
                        # 날짜 체크
                        if end_date_obj and regist_dt:
                            try:
                                review_date_obj = datetime.strptime(regist_dt, "%Y.%m.%d")
                                if review_date_obj < end_date_obj:
                                    reached_end_date = True
                            except:
                                pass
                    
                    # 파일 저장
                    if processed_reviews:
                        self.append_reviews_to_file(processed_reviews, output_path, total_count + 1)
                        total_count += len(processed_reviews)
                        
                    print(f"    ✅ {len(processed_reviews)}개 저장 완료 (누적: {total_count}개)")
                    
                    if reached_end_date:
                        print(f"    🛑 종료 날짜({end_date})에 도달하여 수집을 중단합니다.")
                        break
                        
                    page_idx += 1
                    time.sleep(0.5) # 서버 부하 방지
                    
                except Exception as e:
                    print(f"  ⚠️ API 처리 중 오류({type(e).__name__}): {e}")
                    time.sleep(1)
                    # 예외를 상위로 전파하여 Fallback(기존 방식)이 작동하도록 함
                    raise e
            
            # 최종 업데이트
            self.update_review_count(output_path, total_count, end_date)
            return total_count
            
        except Exception as e:
            print(f"❌ API 리뷰 수집 실패: {e}")
            print("🔄 기존 스크롤 방식으로 전환 시도...")
            return self.crawl_reviews_infinite_scroll(output_path, end_date)
