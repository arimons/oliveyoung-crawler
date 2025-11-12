"""
올리브영 리뷰 크롤러
상품 리뷰를 모든 페이지에서 수집
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import List, Dict
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

    def get_total_pages(self) -> int:
        """
        총 페이지 수 확인

        Returns:
            총 페이지 수
        """
        try:
            # 페이지 번호 링크들 찾기
            page_links = self.driver.find_elements(By.CSS_SELECTOR, "a[data-page-no]")

            if not page_links:
                print("페이지 번호를 찾을 수 없습니다. 1페이지만 존재하는 것으로 가정합니다.")
                return 1

            # 가장 큰 페이지 번호 찾기
            max_page = 1
            for link in page_links:
                try:
                    page_no = int(link.get_attribute("data-page-no"))
                    max_page = max(max_page, page_no)
                except:
                    continue

            print(f"📄 총 {max_page}개 페이지 발견")
            return max_page

        except Exception as e:
            print(f"⚠️  페이지 수 확인 중 오류: {e}")
            return 1

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
            total_elements = len(review_elements)

            print(f"  현재 페이지에서 {total_elements}개 리뷰 발견")

            # Stale Element 에러 방지: 텍스트를 즉시 추출하여 리스트로 저장
            review_texts = []
            for element in review_elements:
                try:
                    text = element.text.strip()
                    review_texts.append(text)
                except Exception:
                    review_texts.append("")  # 실패 시 빈 문자열

            # 추출한 텍스트 처리
            for idx, review_text in enumerate(review_texts):
                if review_text:
                    reviews.append(review_text)
                    print(f"    [{idx+1}] {review_text[:50]}...")  # 처음 50자만 출력
                else:
                    print(f"    ⚠️  리뷰 {idx+1} 추출 실패 (Stale Element 또는 빈 텍스트)")

        except Exception as e:
            print(f"⚠️  리뷰 추출 중 오류: {e}")

        return reviews

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

    def crawl_all_reviews(self) -> List[str]:
        """
        모든 페이지의 리뷰 수집

        Returns:
            전체 리뷰 텍스트 리스트
        """
        all_reviews = []

        try:
            print("\n🔍 리뷰 크롤링 시작...")

            # 1. 리뷰 탭 클릭
            if not self.click_review_tab():
                print("❌ 리뷰 탭을 찾을 수 없습니다")
                return []

            # 2. 총 페이지 수 확인
            total_pages = self.get_total_pages()

            # 3. 각 페이지별 리뷰 수집
            for page in range(1, total_pages + 1):
                print(f"\n📖 {page}/{total_pages} 페이지 처리 중...")

                # 첫 페이지가 아니면 페이지 이동
                if page > 1:
                    if not self.click_next_page(page):
                        print(f"⚠️  {page}페이지 이동 실패, 건너뜀")
                        continue

                # 현재 페이지의 리뷰 추출
                page_reviews = self.extract_reviews_from_current_page()
                all_reviews.extend(page_reviews)

                print(f"  ✅ {len(page_reviews)}개 리뷰 수집 완료 (누적: {len(all_reviews)}개)")

            print(f"\n✅ 총 {len(all_reviews)}개 리뷰 수집 완료!")

        except Exception as e:
            print(f"❌ 리뷰 크롤링 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()

        return all_reviews

    def save_reviews_to_file(self, reviews: List[str], output_path: str):
        """
        리뷰를 텍스트 파일로 저장

        Args:
            reviews: 리뷰 텍스트 리스트
            output_path: 저장할 파일 경로
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"총 {len(reviews)}개의 리뷰\n")
                f.write("=" * 80 + "\n\n")

                for idx, review in enumerate(reviews, 1):
                    f.write(f"[리뷰 {idx}]\n")
                    f.write(review + "\n")
                    f.write("-" * 80 + "\n\n")

            print(f"✅ 리뷰 저장 완료: {output_path}")

        except Exception as e:
            print(f"❌ 리뷰 저장 실패: {e}")
