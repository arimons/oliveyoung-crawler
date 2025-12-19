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
import random
import math
import json
import os
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
        - 파일이 이미 존재하면 초기화하지 않음
        """
        if os.path.exists(output_path):
            return

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"총 0개의 리뷰 (수집 중...)\n")
                f.write("=" * 80 + "\n\n")
            print(f"📝 리뷰 파일 초기화: {output_path}")
        except Exception as e:
            print(f"❌ 리뷰 파일 초기화 실패: {e}")

    def get_existing_info(self, output_path: str) -> Tuple[int, int]:
        """기존 파일에서 마지막 리뷰 번호와 다음 시작할 페이지 번호 반환"""
        if not os.path.exists(output_path):
            return 0, 1
        
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                first_line = f.readline()
                if not first_line:
                    return 0, 1
                
                # 헤더에서 "총 N개의 리뷰" 추출
                match = re.search(r'총 (\d+)개의 리뷰', first_line)
                if match:
                    count = int(match.group(1))
                    # 페이지당 10개씩이므로 다음 페이지 계산
                    next_page = (count // 10) + 1
                    return count, next_page
        except Exception as e:
            print(f"⚠️ 기존 리뷰 정보 읽기 실패: {e}")
        
        return 0, 1

    def append_reviews_to_file(self, reviews: list, output_path: str, start_index: int):
        """리뷰를 파일에 추가 (날짜 표시 제거)"""
        try:
            with open(output_path, 'a', encoding='utf-8') as f:
                for i, review in enumerate(reviews):
                    idx = start_index + i
                    f.write(f"[리뷰 {idx}]\n")
                    f.write(f"{review['text']}\n")
                    f.write("-" * 80 + "\n")
        except Exception as e:
            print(f"❌ 리뷰 추가 실패: {e}")

    def save_review(self, reviews: list, output_path: str, current_count: int) -> int:
        """리뷰 리스트 저장 (날짜 표시 제거)"""
        if not reviews:
            return current_count
        
        with open(output_path, 'a', encoding='utf-8') as f:
            for i, review in enumerate(reviews):
                idx = current_count + i + 1
                f.write(f"[리뷰 {idx}]\n")
                f.write(f"{review['text']}\n")
                f.write("-" * 80 + "\n")
                
        return current_count + len(reviews)

    def update_review_count(self, output_path: str, total_count: int, target_date: str = None):
        """리뷰 파일의 총 개수 업데이트 (날짜 정보 제거)"""
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()

            lines = content.split('\n')
            lines[0] = f"총 {total_count}개의 리뷰"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))

            print(f"✅ 리뷰 파일 최종 저장 완료: {output_path} ({total_count}개)")

        except Exception as e:
            print(f"❌ 리뷰 개수 업데이트 실패: {e}")

    def save_review(self, output_path: str, review: dict):
        """단일 리뷰 저장 (append)"""
        try:
            with open(output_path, 'a', encoding='utf-8') as f:
                date_str = review.get('날짜', '날짜없음')
                f.write(f"[{date_str}]\n")
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

                                    rating = 0
                                    try:
                                        # div.rating 안에 있는 채워진 별 아이콘 개수로 별점 계산
                                        rating_icons = shadow.find_elements(By.CSS_SELECTOR, "div.rating oy-review-star-icon")
                                        rating = len(rating_icons)
                                    except:
                                        pass # 실패 시 별점은 0으로 유지

                                    review_key = f"{review_date}_{review_text[:20]}"
                                    if review_key not in collected_reviews:
                                        self.save_review(output_path, {"날짜": review_date, "내용": review_text, "별점": rating})
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
        API를 직접 호출하여 리뷰 수집 (Selenium 쿠키 사용)
        - 429 에러 등 일시적인 오류에 대해 10회 재시도 로직 포함
        - 실패 시 예외를 발생시켜 작업을 중단시킴
        """
        total_count = 0
        
        print("\n🚀 API 기반 리뷰 수집 시작 (Hybrid 방식)")
        
        try:
            # 1. 상품 번호(goodsNo) 추출
            current_url = self.driver.current_url
            goods_no_match = re.search(r'goodsNo=([a-zA-Z0-9]+)', current_url)
            if not goods_no_match:
                raise Exception("URL에서 goodsNo를 찾을 수 없습니다. API 수집을 진행할 수 없습니다.")
            goods_no = goods_no_match.group(1)
            print(f"  🔍 감지된 상품 번호: {goods_no}")
        except Exception as e:
            print(f"❌ 상품 번호 추출 중 오류 발생: {e}")
            raise e # 상위로 에러 전파
            
        # 2. 날짜 설정
        end_date_obj = None
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, "%Y.%m.%d")
                print(f"  📅 수집 종료 날짜: {end_date}")
            except:
                print(f"  ⚠️ 날짜 형식 오류, 전체 수집: {end_date}")
        
        # 3. 리뷰 파일 초기화
        self.init_review_file(output_path)
        
        # 4. API 호출 루프
        page_idx = 1
        reached_end_date = False
        
        while not reached_end_date:
            print(f"  📖 페이지 {page_idx} 처리 중 (Browser API)...")

            # 65회 요청마다 20초 대기
            if page_idx > 0 and page_idx % 65 == 0:
                print("  ⏳ 65회 요청 도달, 서버 부하 감소를 위해 20초 대기합니다.")
                time.sleep(20)
            
            js_script = """
            const callback = arguments[arguments.length - 1];
            const goodsNo = arguments[0];
            const pageIdx = arguments[1];
            
            const params = new URLSearchParams({
                'goodsNo': goodsNo,
                'gdasSort': '02', // 최신순
                'itemNo': 'all',
                'pageIdx': pageIdx,
                'pagingSize': '10',
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
                if (!response.ok) {
                    // response.text()를 통해 body를 읽어야 에러 메시지 확인 가능
                    return response.text().then(text => {
                         return {success: false, status: response.status, error: text};
                    });
                }
                return response.json().then(data => ({success: true, data: data}));
            })
            .then(result => callback(result))
            .catch(err => callback({success: false, error: err.message, status: 'NetworkError'}));
            """
    def log(self, message: str):
        """로그 출력 및 콜백 호출"""
        print(message)
        if self.log_callback:
            self.log_callback(message)

    def crawl_reviews_via_api(self, output_path: str, end_date: str = None, max_count: int = 300) -> int:
        """
        API를 직접 호출하여 리뷰 수집 (Selenium 쿠키 사용)
        - max_count: 최대 수집할 리뷰 개수 (기본 300개)
        """
        total_count = 0
        
        self.log(f"\n🚀 API 기반 리뷰 수집 시작 (목표: {max_count}개)")
        
        try:
            # 1. 상품 번호(goodsNo) 추출
            current_url = self.driver.current_url
            goods_no_match = re.search(r'goodsNo=([a-zA-Z0-9]+)', current_url)
            if not goods_no_match:
                raise Exception("URL에서 goodsNo를 찾을 수 없습니다.")
            goods_no = goods_no_match.group(1)
            self.log(f"  🔍 상품 번호: {goods_no}")
        except Exception as e:
            self.log(f"❌ 상품 번호 추출 오류: {e}")
            raise e
            
        # 2. 날짜 설정 (필요시 백업용으로 유지하지만 파일 저장시엔 제외)
        end_date_obj = None
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, "%Y.%m.%d")
            except: pass

        # 기존 수집 정보 확인
        existing_count, start_page = self.get_existing_info(output_path)
        
        if existing_count > 0:
            # 프론트엔드 식별용 태그 추가
            self.log(f"CONTINUE_CRAWL_PROMPT: 기존에 {existing_count}개의 리뷰가 수집되어 있습니다. 이어서 수집을 진행합니다.")
            total_count = existing_count
            page_idx = start_page
        else:
            self.init_review_file(output_path)
            total_count = 0
            page_idx = 1
        
        # 목표 개수는 '기존 개수 + 이번 요청 개수'로 설정하여 추가 수집을 수행
        target_limit = existing_count + max_count
        reached_end = False
        session_pages = 0 # 이번 세션에서 처리한 페이지 수
        
        while not reached_end:
            session_pages += 1
            # --- 429 에러 방지 레이트 리미팅 조정 ---
            # 이번 세션에서 50페이지(약 500개) 이상 수집 시 안전 모드 가동
            if session_pages > 50:
                # 안전 모드: 총 대기 3~5초 수준
                base_wait = 1.0
                random_wait = random.uniform(1.0, 3.0)
                wait_time = base_wait + random_wait
                self.log(f"  ⏳ [안전 모드] {wait_time:.1f}초 대기 중...")
                time.sleep(wait_time)
                
                # 절대 페이지 수 기준으로 100페이지마다 휴식 (서버 차단 방지)
                if page_idx % 100 == 0:
                    self.log("  💤 [심층 안전 모드] 20초 긴 휴식 중...")
                    time.sleep(20)
            elif page_idx > 1:
                # 일반 대기: 0.3~1.0초
                time.sleep(0.3 + random.uniform(0.1, 0.7))

            print(f"  📖 페이지 {page_idx} 처리 중...")
            
            js_script = """
            const callback = arguments[arguments.length - 1];
            const goodsNo = arguments[0];
            const pageIdx = arguments[1];
            
            const params = new URLSearchParams({
                'goodsNo': goodsNo,
                'gdasSort': '02',
                'itemNo': 'all',
                'pageIdx': pageIdx,
                'pagingSize': '10',
                'colData': '', 'keyword': '', 'type': ''
            });

            fetch('/store/goods/getGdasNewListJson.do', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: params.toString()
            })
            .then(res => {
                if (!res.ok) throw new Error('HTTP Status ' + res.status);
                return res.json();
            })
            .then(data => callback({success: true, data: data}))
            .catch(err => callback({success: false, error: err.message}));
            """
            
            result = None
            try:
                result = self.driver.execute_async_script(js_script, goods_no, page_idx)
            except Exception as e:
                print(f"  ⚠️ JS 실행 오류: {e}")
                break

            if not result or not result.get('success'):
                error_msg = result.get('error', 'Unknown Error')
                print(f"  ❌ API 요청 실패: {error_msg}")
                if "429" in error_msg:
                    print("  🚨 429 Too Many Requests 감지! 60초 대기 후 종료합니다.")
                    time.sleep(60)
                break

            # 데이터 추출
            raw_data = result.get('data', {})
            data_body = raw_data if 'gdasList' in raw_data else raw_data.get('data', {})
            
            review_list = data_body.get('gdasList', [])
            if not review_list and isinstance(data_body, dict):
                for key in ['gdasNewList', 'gdasPagingList']:
                    if key in data_body:
                        review_list = data_body[key].get('gdasList', [])
                        break

            if not review_list:
                print("  ✅ 모든 리뷰를 수집했습니다.")
                break
            
            processed_reviews = []
            for review in review_list:
                content = (review.get('gdasCont') or review.get('revwCont') or 
                          review.get('cont') or "내용 없음").strip()
                content = re.sub('<[^>]*>', '', html.unescape(content))
                
                date = (review.get('registDt') or review.get('gdasRegistDt') or 
                        review.get('dispRegDt') or review.get('regDt') or "")
                
                # 날짜 정보는 가져오되 파일 저장 로직에서 걸러짐
                processed_reviews.append({"text": content, "date": date})
                
                # 날짜 조건 체크 (백업 기능으로 유지)
                if end_date_obj and date:
                    try:
                        clean_date = date.replace('-', '.')
                        if datetime.strptime(clean_date[:10], "%Y.%m.%d") < end_date_obj:
                            reached_end = True
                            print(f"  🛑 종료 날짜 도달 ({date})")
                            break
                    except: pass
                
                # 개수 조건 체크
                if total_count + len(processed_reviews) >= target_limit:
                    reached_end = True
                    print(f"  🛑 최대 수집 개수 도달 ({target_limit}개)")
                    break
            
            if processed_reviews:
                self.append_reviews_to_file(processed_reviews, output_path, total_count + 1)
                total_count += len(processed_reviews)
                print(f"    ✅ 수집 중: {total_count}/{target_limit}")
            
            if reached_end: break
            page_idx += 1

        self.update_review_count(output_path, total_count, end_date)
        return total_count
