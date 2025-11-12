"""
올리브영 통합 크롤러
검색, 상품 정보 수집, 상세 이미지 다운로드 기능 통합
"""
import os
import sys

# src 폴더를 Python path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from crawler_selenium import OliveyoungCrawler
from product_detail_crawler import ProductDetailCrawler
from review_crawler import ReviewCrawler
import json
from datetime import datetime
from typing import Dict, List
import time


class OliveyoungIntegratedCrawler:
    """올리브영 통합 크롤러"""

    def __init__(self, headless: bool = True):
        """
        Args:
            headless: 브라우저 백그라운드 실행 여부
        """
        self.base_crawler = OliveyoungCrawler(headless=headless)
        self.detail_crawler = None
        self.review_crawler = None

    def start(self):
        """크롤러 시작"""
        self.base_crawler.start()
        self.detail_crawler = ProductDetailCrawler(self.base_crawler.driver)
        self.review_crawler = ReviewCrawler(self.base_crawler.driver)

    def stop(self):
        """크롤러 종료"""
        self.base_crawler.stop()

    def create_product_folder(self, product_name: str) -> str:
        """
        상품별 폴더 생성

        Args:
            product_name: 상품명

        Returns:
            생성된 폴더 경로
        """
        # 파일명에 사용할 수 없는 문자 제거
        safe_name = "".join(c for c in product_name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', ' ')  # 공백 유지

        # 날짜만 추가 (YYMMDD 형식)
        date_str = datetime.now().strftime("%y%m%d")
        folder_name = f"{date_str}_{safe_name}"

        folder_path = os.path.join("data", folder_name)
        os.makedirs(folder_path, exist_ok=True)

        print(f"📁 폴더 생성: {folder_path}")
        return folder_path

    def search_and_get_first_product(self, keyword: str) -> Dict:
        """
        검색하고 첫 번째 상품 정보 가져오기

        Args:
            keyword: 검색 키워드

        Returns:
            상품 정보 딕셔너리
        """
        # 홈페이지 접속
        self.base_crawler.navigate_to_home()

        # 검색
        self.base_crawler.search_product(keyword)

        # 첫 번째 상품 정보 추출
        products = self.base_crawler.extract_product_info(max_products=1)

        if not products:
            raise Exception("검색 결과가 없습니다")

        return products[0]

    def crawl_product_detail_by_url(self, product_url: str, save_folder: str) -> Dict:
        """
        URL로 상품 상세 정보 크롤링

        Args:
            product_url: 상품 URL
            save_folder: 저장 폴더 경로

        Returns:
            상품 정보 및 이미지 경로
        """
        print(f"\n{'='*60}")
        print(f"상품 상세 크롤링 시작")
        print(f"{'='*60}")

        # 상세 페이지로 이동
        self.detail_crawler.go_to_product_detail(product_url)

        # 상품 정보 추출
        product_info = self.detail_crawler.extract_product_info_from_detail()

        # 더보기 버튼 클릭
        self.detail_crawler.click_more_button()

        # 이미지 URL 추출
        image_urls = self.detail_crawler.extract_product_images()

        if not image_urls:
            print("⚠️  추출된 이미지가 없습니다")
            product_info["이미지_경로"] = ""
            product_info["이미지_개수"] = 0
            return product_info

        # 이미지 다운로드 및 병합
        output_image_path = os.path.join(save_folder, "product_detail_merged.jpg")
        saved_path = self.detail_crawler.download_and_merge_images(image_urls, output_image_path)

        product_info["이미지_경로"] = saved_path
        product_info["이미지_개수"] = len(image_urls)
        product_info["수집시각"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return product_info

    def crawl_product_by_keyword(self, keyword: str, save_format: str = "json") -> Dict:
        """
        키워드로 상품 검색 및 크롤링

        Args:
            keyword: 검색 키워드
            save_format: 저장 형식 (json/csv/both)

        Returns:
            크롤링 결과 딕셔너리
        """
        print(f"\n{'='*60}")
        print(f"키워드 크롤링: {keyword}")
        print(f"{'='*60}\n")

        # 검색 및 첫 번째 상품 가져오기
        first_product = self.search_and_get_first_product(keyword)
        product_url = first_product["URL"]

        # 폴더 생성
        product_name = first_product["상품명"].split('\n')[0][:50]  # 상품명 앞부분만 사용
        save_folder = self.create_product_folder(product_name)

        # 상세 크롤링
        product_info = self.crawl_product_detail_by_url(product_url, save_folder)

        # 데이터 저장
        self.save_product_info(product_info, save_folder, save_format)

        result = {
            "상품명": product_info.get("상품명", ""),
            "폴더": save_folder,
            "이미지": product_info.get("이미지_경로", ""),
            "이미지_개수": product_info.get("이미지_개수", 0)
        }

        return result

    def crawl_product_by_url(self, product_url: str, product_name: str = None, save_format: str = "json") -> Dict:
        """
        URL로 상품 크롤링

        Args:
            product_url: 상품 URL
            product_name: 상품명 (폴더명 생성용, None이면 자동 추출)
            save_format: 저장 형식 (json/csv/both)

        Returns:
            크롤링 결과 딕셔너리
        """
        print(f"\n{'='*60}")
        print(f"URL 크롤링")
        print(f"{'='*60}\n")

        # 폴더 생성 (임시 이름)
        if not product_name:
            product_name = f"product_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        save_folder = self.create_product_folder(product_name)

        # 상세 크롤링
        product_info = self.crawl_product_detail_by_url(product_url, save_folder)

        # 실제 상품명으로 폴더 이름 변경
        if product_info.get("상품명") and product_info["상품명"] != "정보 없음":
            actual_name = product_info["상품명"].split('\n')[0][:50]
            new_folder = self.create_product_folder(actual_name)

            # 파일 이동
            import shutil
            if os.path.exists(save_folder):
                for file in os.listdir(save_folder):
                    shutil.move(
                        os.path.join(save_folder, file),
                        os.path.join(new_folder, file)
                    )
                os.rmdir(save_folder)
                save_folder = new_folder
                product_info["이미지_경로"] = os.path.join(new_folder, "product_detail_merged.jpg")

        # 데이터 저장
        self.save_product_info(product_info, save_folder, save_format)

        result = {
            "상품명": product_info.get("상품명", ""),
            "폴더": save_folder,
            "이미지": product_info.get("이미지_경로", ""),
            "이미지_개수": product_info.get("이미지_개수", 0)
        }

        return result

    def save_product_info(self, product_info: Dict, save_folder: str, save_format: str):
        """
        상품 정보 저장

        Args:
            product_info: 상품 정보
            save_folder: 저장 폴더
            save_format: 저장 형식 (json/csv/both)
        """
        if save_format in ["json", "both"]:
            json_path = os.path.join(save_folder, "product_info.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(product_info, f, ensure_ascii=False, indent=2)
            print(f"💾 JSON 저장: {json_path}")

        if save_format in ["csv", "both"]:
            import pandas as pd
            csv_path = os.path.join(save_folder, "product_info.csv")
            df = pd.DataFrame([product_info])
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print(f"💾 CSV 저장: {csv_path}")
