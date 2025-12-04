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

        # [성능 최적화] 페이지 로드 전략: eager (이미지/CSS 로딩 완료를 기다리지 않음)
        options.page_load_strategy = 'eager'

        # 기본 설정
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        
        # 봇 감지 회피 설정
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        # 영구 프로필 사용
        options.add_argument(f'--user-data-dir={self.temp_user_data}')

        if self.headless:
            options.add_argument('--headless=new')
        else:
            options.add_argument('--window-position=1850,1000')
        
        options.add_argument('--window-size=1920,1080')
        options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        # 드라이버 설정 및 시작
        try:
            import time as perf_time
            total_start = perf_time.time()
            
            print("⏳ [1/4] 드라이버 경로 확인 중...")
            step_start = perf_time.time()
            from webdriver_manager.chrome import ChromeDriverManager
            
            # 1. 기존에 다운로드된 드라이버가 있는지 먼저 확인 (20초 지연 방지)
            print("⏳ [1/4] 드라이버 캐시 확인 중...")
            step_start = perf_time.time()
            
            driver_path = ""
            # WDM 기본 캐시 경로 추정 (사용자 홈 디렉토리 기준)
            wdm_cache = os.path.join(os.path.expanduser("~"), ".wdm", "drivers", "chromedriver", "win64")
            
            if os.path.exists(wdm_cache):
                # 가장 최신 버전 폴더 찾기
                try:
                    versions = [d for d in os.listdir(wdm_cache) if os.path.isdir(os.path.join(wdm_cache, d))]
                    if versions:
                        latest_version = sorted(versions, reverse=True)[0] # 단순 문자열 정렬이지만 대략 맞음
                        potential_path = os.path.join(wdm_cache, latest_version, "chromedriver-win32", "chromedriver.exe")
                        if os.path.exists(potential_path):
                            driver_path = potential_path
                            print(f"✅ 캐시된 드라이버 발견: {driver_path}")
                except Exception as e:
                    print(f"⚠️ 캐시 검색 중 오류: {e}")

            # 캐시가 없거나 못 찾았을 때만 install() 호출
            if not driver_path:
                print("⚠️ 캐시된 드라이버가 없어 다운로드를 시도합니다 (시간이 걸릴 수 있음)...")
                try:
                    driver_path = ChromeDriverManager().install()
                except Exception as e:
                    print(f"⚠️ WebDriver Manager 설치 실패: {e}")
                    driver_path = ""
            
            print(f"   └─ 소요 시간: {perf_time.time() - step_start:.2f}초")

            # 2. 경로 유효성 검사 및 대체 경로 탐색
            print("⏳ [2/4] 실행 파일 검증 중...")
            step_start = perf_time.time()
            valid_driver_path = None
            
            # (1) 설치된 경로 확인
            if driver_path and os.path.exists(driver_path) and driver_path.endswith('.exe'):
                valid_driver_path = driver_path
            
            # (2) 같은 폴더 내 chromedriver.exe 확인 (WinError 193 대응)
            if not valid_driver_path and driver_path:
                driver_dir = os.path.dirname(driver_path)
                potential_exe = os.path.join(driver_dir, "chromedriver.exe")
                if os.path.exists(potential_exe):
                    valid_driver_path = potential_exe
                    print(f"✅ 대체 경로 사용: {valid_driver_path}")

            # (3) 프로젝트 폴더 내 chromedriver.exe 확인
            if not valid_driver_path:
                local_driver = os.path.join(os.getcwd(), "chromedriver.exe")
                if os.path.exists(local_driver):
                    valid_driver_path = local_driver
                    print(f"✅ 로컬 드라이버 사용: {valid_driver_path}")
            print(f"   └─ 소요 시간: {perf_time.time() - step_start:.2f}초")

            # 서비스 생성
            print("⏳ [3/4] 서비스 생성 중...")
            step_start = perf_time.time()
            if valid_driver_path:
                service = Service(valid_driver_path)
                print(f"   └─ 소요 시간: {perf_time.time() - step_start:.2f}초")
                
                print("⏳ [4/4] 브라우저 실행 중 (가장 오래 걸림)...")
                step_start = perf_time.time()
                self.driver = webdriver.Chrome(service=service, options=options)
            else:
                # 경로를 찾지 못한 경우, PATH에 있는 드라이버 사용 시도
                print("⚠️ 드라이버 경로를 찾지 못해 시스템 PATH의 드라이버를 사용합니다.")
                self.driver = webdriver.Chrome(options=options)
            
            elapsed = perf_time.time() - total_start
            print(f"⏱️  Chrome 총 시작 시간: {elapsed:.2f}초 (브라우저 실행: {perf_time.time() - step_start:.2f}초)")
            
            # WebDriver 속성 숨기기 (드라이버가 성공적으로 생성된 경우에만)
            if self.driver:
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                self.driver.implicitly_wait(10)
                print("✅ 브라우저 시작 완료")
            else:
                print("❌ 브라우저 드라이버가 생성되지 않았습니다.")

        except Exception as e:
            print(f"❌ 브라우저 시작 실패: {e}")
            # 드라이버 종료 시도
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None
            raise e

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
