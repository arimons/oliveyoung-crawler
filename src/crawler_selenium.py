"""
Oliveyoung 크롤러 - Selenium 버전
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
from datetime import datetime
from typing import List, Dict
import tempfile
import shutil
import os

class OliveyoungCrawler:
    """올리브영 웹사이트 크롤러"""

    def __init__(self, headless: bool = False):
        """
        크롤러 초기화

        Args:
            headless: 브라우저를 백그라운드에서 실행할지 여부 (False면 브라우저가 보임)
        """
        self.headless = headless
        self.base_url = "https://www.oliveyoung.co.kr"
        self.driver = None
        self.temp_user_data = None  # 임시 User Data 디렉토리

    def start(self):
        """브라우저 시작"""
        print("🚀 브라우저 시작 중...")

        # 프로세스별 고유 User Data 디렉토리 사용 (병렬 크롤링 지원)
        import os
        import multiprocessing
        process_id = multiprocessing.current_process().pid
        
        self.temp_user_data = os.path.abspath(f"chrome_profile_{process_id}")
        if not os.path.exists(self.temp_user_data):
            os.makedirs(self.temp_user_data)
        print(f"🔧 User Data 디렉토리: {self.temp_user_data} (PID: {process_id})")

        # Chrome 옵션 설정
        options = webdriver.ChromeOptions()

        # 영구 프로필 사용
        options.add_argument(f'--user-data-dir={self.temp_user_data}')
        
        # 시크릿 모드 제거 (쿠키 저장을 위해)
        # options.add_argument('--incognito')

        # 봇 감지 회피 설정
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        if self.headless:
            # 최신 헤드리스 모드 사용
            options.add_argument('--headless=new')
        else:
            # 헤드리스가 아닐 때: 화면 구석으로 이동 (사용자가 필요시 접근 가능)
            options.add_argument('--window-position=1850,1000')
        
        # 뷰포트 크기 고정 (헤드리스에서도 적용됨)
        options.add_argument('--window-size=1920,1080')
        # options.add_argument('--start-maximized') # 위치 이동을 위해 최대화 해제
        
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        # 드라이버 설정 및 시작
        try:
            # 병렬 실행 시 드라이버 설치 충돌 방지를 위한 랜덤 대기
            if self.temp_user_data and "chrome_profile_" in self.temp_user_data:
                import random
                time.sleep(random.uniform(0.5, 3.0))

            from webdriver_manager.chrome import ChromeDriverManager
            driver_path = ChromeDriverManager().install()
            
            # WinError 193 방지: 경로가 유효한지 확인
            if not os.path.exists(driver_path) or not driver_path.endswith('.exe'):
                print(f"⚠️ 잘못된 드라이버 경로: {driver_path}")
                # 기본 경로 시도 (프로젝트 폴더 내 chromedriver.exe)
                local_driver = os.path.join(os.getcwd(), "chromedriver.exe")
                if os.path.exists(local_driver):
                    driver_path = local_driver
            
            service = Service(driver_path)
            self.driver = webdriver.Chrome(service=service, options=options)
        except Exception as e:
            print(f"❌ ChromeDriver 설치 실패: {e}")
            print("재시도 중...")
            try:
                # Fallback: 시스템 PATH 또는 기본 설치 경로 시도
                self.driver = webdriver.Chrome(options=options)
            except Exception as e2:
                print(f"❌ 브라우저 시작 치명적 오류: {e2}")
                raise e2

        # WebDriver 속성 숨기기
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        self.driver.implicitly_wait(10)

        print("✅ 브라우저 시작 완료")

    def stop(self):
        """브라우저 종료"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            print("🛑 브라우저 종료")
        self.driver = None
        
        # 프로세스별 프로파일 폴더 삭제
        if self.temp_user_data and os.path.exists(self.temp_user_data):
            try:
                import shutil
                shutil.rmtree(self.temp_user_data)
                print(f"🗑️  프로파일 폴더 삭제: {self.temp_user_data}")
            except Exception as e:
                print(f"⚠️  프로파일 폴더 삭제 실패: {e}")

    def is_alive(self) -> bool:
        """브라우저 세션이 유효한지 확인"""
        if not self.driver:
            return False
        try:
            # 가벼운 명령으로 세션 확인
            _ = self.driver.window_handles
            return True
        except Exception:
            return False

    def search_product(self, keyword: str):
        """
        제품 검색

        Args:
            keyword: 검색할 제품명
        """
        print(f"🔍 '{keyword}' 검색 중...")

        try:
            # 검색창 찾기 및 클릭
            wait = WebDriverWait(self.driver, 10)
            search_box = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='검색']"))
            )

            # 검색어 입력
            search_box.clear()
            search_box.send_keys(keyword)
            search_box.send_keys(Keys.RETURN)

            time.sleep(3)  # 검색 결과 로딩 대기
            print(f"✅ 검색 완료: {self.driver.title}")

        except Exception as e:
            print(f"❌ 검색 중 오류: {e}")
            raise

    def extract_product_info(self, max_products: int = 10) -> List[Dict]:
        """
        상품 정보 추출

        Args:
            max_products: 추출할 최대 상품 개수

        Returns:
            상품 정보 리스트
        """
        print(f"📊 상품 정보 추출 중 (최대 {max_products}개)...")
        products = []

        try:
            # 상품 정보 컨테이너 찾기
            wait = WebDriverWait(self.driver, 10)
            product_elements = wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".prd_info"))
            )

            print(f"   찾은 상품 개수: {len(product_elements)}개")

            for idx, product in enumerate(product_elements[:max_products]):
                try:
                    # 상품명
                    try:
                        name_elem = product.find_element(By.CSS_SELECTOR, ".prd_name")
                        name = name_elem.text.strip()
                    except:
                        name = "상품명 없음"

                    # 가격
                    try:
                        price_elem = product.find_element(By.CSS_SELECTOR, ".prd_price")
                        price = price_elem.text.strip()
                    except:
                        price = "가격 정보 없음"

                    # 브랜드 (상품명에서 추출 시도)
                    try:
                        brand_elem = product.find_element(By.CSS_SELECTOR, ".tx_brand")
                        brand = brand_elem.text.strip()
                    except:
                        # 브랜드 정보가 별도로 없으면 상품명의 첫 부분을 브랜드로 사용
                        brand = name.split()[0] if name and name != "상품명 없음" else "브랜드 정보 없음"

                    # 상품 URL
                    try:
                        link_elem = product.find_element(By.CSS_SELECTOR, "a")
                        url = link_elem.get_attribute("href")
                        if not url.startswith("http"):
                            url = self.base_url + url
                    except:
                        url = ""

                    product_data = {
                        "순번": idx + 1,
                        "상품명": name,
                        "브랜드": brand,
                        "가격": price,
                        "URL": url,
                        "수집시각": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }

                    products.append(product_data)
                    print(f"  {idx+1}. {brand} - {name} ({price})")

                except Exception as e:
                    print(f"  ⚠️  {idx+1}번 상품 추출 실패: {e}")
                    continue

            print(f"✅ 총 {len(products)}개 상품 정보 추출 완료")

        except Exception as e:
            print(f"❌ 상품 정보 추출 중 오류: {e}")
            import traceback
            traceback.print_exc()

        return products

    def save_to_json(self, data: List[Dict], filename: str):
        """
        데이터를 JSON 파일로 저장

        Args:
            data: 저장할 데이터
            filename: 파일명
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = f"data/{filename}_{timestamp}.json"

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"💾 데이터 저장 완료: {filepath}")
        return filepath

    def save_to_csv(self, data: List[Dict], filename: str):
        """
        데이터를 CSV 파일로 저장

        Args:
            data: 저장할 데이터
            filename: 파일명
        """
        import pandas as pd

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = f"data/{filename}_{timestamp}.csv"

        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False, encoding='utf-8-sig')

        print(f"💾 데이터 저장 완료: {filepath}")
        return filepath
