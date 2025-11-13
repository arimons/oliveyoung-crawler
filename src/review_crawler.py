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


class ReviewCrawler:
    """리뷰 크롤링 클래스"""

    def __init__(self, driver):
        """
        Args:
            driver: Selenium WebDriver 인스턴스
        """
        self.driver = driver

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
        리뷰 정렬을 '최신순'으로 변경

        Returns:
            성공 여부
        """
        try:
            print("🔄 리뷰 정렬을 '최신순'으로 변경 중...")

            # '최신순' 버튼 찾기 (data-sort-type-code="latest")
            latest_button = self.driver.find_element(
                By.CSS_SELECTOR, "a[data-sort-type-code='latest']"
            )

            # 버튼이 보이도록 스크롤
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", latest_button)
            time.sleep(0.5)

            # 클릭
            latest_button.click()
            print("✅ '최신순' 정렬 선택 완료")
            time.sleep(2)  # 리뷰 재로딩 대기

            return True

        except Exception as e:
            print(f"⚠️  정렬 변경 실패: {e}")
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
                    current_page = self.driver.execute_script("""
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
            self.update_review_count(output_path, total_count)

        except Exception as e:
            print(f"❌ 리뷰 크롤링 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            # 오류 발생 시에도 지금까지 수집한 리뷰 개수 업데이트
            if total_count > 0:
                self.update_review_count(output_path, total_count)

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
                for idx, review in enumerate(reviews, start_idx):
                    f.write(f"[리뷰 {idx}] {review['date']}\n")
                    f.write(review['text'] + "\n")
                    f.write("-" * 80 + "\n\n")
        except Exception as e:
            print(f"❌ 리뷰 추가 실패: {e}")

    def update_review_count(self, output_path: str, total_count: int):
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
            lines[0] = f"총 {total_count}개의 리뷰"

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))

            print(f"✅ 리뷰 파일 최종 저장 완료: {output_path} ({total_count}개)")

        except Exception as e:
            print(f"❌ 리뷰 개수 업데이트 실패: {e}")
