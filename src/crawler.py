"""
Oliveyoung 크롤러 메인 클래스
"""
from playwright.sync_api import sync_playwright, Page, Browser
import time
import json
from datetime import datetime
from typing import List, Dict


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
        self.playwright = None
        self.browser = None
        self.page = None

    def start(self):
        """브라우저 시작"""
        print("🚀 브라우저 시작 중...")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        self.page = self.browser.new_page()
        print("✅ 브라우저 시작 완료")

    def stop(self):
        """브라우저 종료"""
        if self.page:
            self.page.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        print("🛑 브라우저 종료")

    def navigate_to_home(self):
        """올리브영 홈페이지로 이동"""
        print(f"🌐 {self.base_url} 접속 중...")
        self.page.goto(self.base_url)
        time.sleep(2)  # 페이지 로딩 대기
        print("✅ 홈페이지 접속 완료")

    def search_product(self, keyword: str):
        """
        제품 검색

        Args:
            keyword: 검색할 제품명
        """
        print(f"🔍 '{keyword}' 검색 중...")
        # 검색 구현 예정
        pass

    def extract_product_info(self) -> List[Dict]:
        """
        상품 정보 추출

        Returns:
            상품 정보 리스트
        """
        print("📊 상품 정보 추출 중...")
        # 추출 로직 구현 예정
        return []

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
