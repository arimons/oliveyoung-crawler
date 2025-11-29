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

    def __init__(self, headless: bool = True, log_callback=None):
        """
        Args:
            headless: 브라우저 백그라운드 실행 여부
            log_callback: 로그 출력 콜백 함수 (optional)
        """
        self.base_crawler = OliveyoungCrawler(headless=headless)
        self.detail_crawler = None
        self.review_crawler = None
        self.log_callback = log_callback

    def log(self, message: str):
        """로그 출력"""
        print(message)
        if self.log_callback:
            self.log_callback(message)

    def start(self):
        """크롤러 시작"""
        self.base_crawler.start()
        self.detail_crawler = ProductDetailCrawler(self.base_crawler.driver, log_callback=self.log_callback)
        self.review_crawler = ReviewCrawler(self.base_crawler.driver, log_callback=self.log_callback)

    def stop(self):
        """크롤러 종료"""
        self.base_crawler.stop()
        self.detail_crawler = None
        self.review_crawler = None

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

        # 프로젝트 루트 기준 절대 경로 설정
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(project_root, "data")
        
        folder_path = os.path.join(data_dir, folder_name)
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

    def crawl_product_detail_by_url(self, product_url: str, save_folder: str, split_mode: str = "aggressive", collect_reviews: bool = False, review_end_date: str = None, reviews_only: bool = False, skip_navigation: bool = False, initial_info: Dict = None) -> Dict:
        """
        URL로 상품 상세 정보 크롤링
        """
        print(f"\n{'='*60}")
        print(f"상품 상세 크롤링 시작")
        print(f"{'='*60}")

        # 상세 페이지로 이동 (skip_navigation이 False일 때만)
        if not skip_navigation:
            self.detail_crawler.go_to_product_detail(product_url)
        else:
            print("ℹ️  페이지 이동 건너뜀 (이미 접속 중)")

        # 상품 정보 추출 (initial_info가 없으면 추출)
        if initial_info:
            product_info = initial_info
            print("ℹ️  기존 추출된 상품 정보 사용")
        else:
            product_info = self.detail_crawler.extract_product_info_from_detail()

        # 이미지 수집 (Smart Image Skip 적용)
        # reviews_only 파라미터는 더 이상 사용하지 않음 (이미지 존재 여부로 판단)
        
        output_image_path = os.path.join(save_folder, "product_detail_merged.jpg")
        part1_path = os.path.join(save_folder, "product_detail_merged_part1.jpg")
        
        # 이미지가 이미 존재하는지 확인
        if os.path.exists(output_image_path) or os.path.exists(part1_path):
            print(f"ℹ️  이미지가 이미 존재하여 다운로드를 건너뜁니다.")
            # 경로 설정 (존재하는 파일 기준)
            if os.path.exists(output_image_path):
                product_info["이미지_경로"] = output_image_path
            else:
                product_info["이미지_경로"] = part1_path # part1이 있으면 그걸 대표 경로로
            
            # 이미지 개수는 정확히 알 수 없으므로 1개 이상으로 가정하거나 기존 메타데이터를 읽어야 하지만,
            # 여기서는 단순 스킵이 목적이므로 패스
            product_info["이미지_개수"] = 1 
        else:
            # 더보기 버튼 클릭
            self.detail_crawler.click_more_button()

            # 이미지 URL 추출
            image_urls = self.detail_crawler.extract_product_images()

            if not image_urls:
                print("⚠️  추출된 이미지가 없습니다")
                product_info["이미지_경로"] = ""
                product_info["이미지_개수"] = 0
            else:
                # 이미지 다운로드 및 병합
                self.detail_crawler.download_and_merge_images(image_urls, output_image_path, split_mode=split_mode)

                # 썸네일 다운로드
                if product_info.get("썸네일_URL"):
                    try:
                        import requests
                        thumb_url = product_info["썸네일_URL"]
                        thumb_path = os.path.join(save_folder, "thumbnail.jpg")
                        
                        response = requests.get(thumb_url, stream=True)
                        if response.status_code == 200:
                            with open(thumb_path, 'wb') as f:
                                for chunk in response.iter_content(1024):
                                    f.write(chunk)
                            print(f"  🖼️ 썸네일 다운로드 완료: {thumb_path}")
                            product_info["썸네일_경로"] = thumb_path
                        else:
                            print(f"  ⚠️ 썸네일 다운로드 실패 (Status: {response.status_code})")
                    except Exception as e:
                        print(f"  ⚠️ 썸네일 다운로드 중 오류: {e}")

        product_info["수집시각"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 리뷰 메타데이터 (별점, 리뷰수) 추출
        review_meta = self.detail_crawler.extract_review_metadata()
        if review_meta:
            product_info.update(review_meta)

        # 추가 정보 추출 (사용자 요청: 상품정보 탭의 특정 행)
        specific_info = self.detail_crawler.extract_specific_info()
        if specific_info:
            product_info.update(specific_info)

        # 리뷰 텍스트 수집 (옵션)
        if collect_reviews:
            print(f"📝 리뷰 텍스트 수집 중... (종료일: {review_end_date})")
            review_file = os.path.join(save_folder, "reviews.txt")
            
            # New Layout (Infinite Scroll) 시도
            try:
                review_count = self.review_crawler.crawl_reviews_infinite_scroll(
                    output_path=review_file,
                    end_date=review_end_date
                )
            except Exception as e:
                print(f"⚠️ 무한 스크롤 수집 실패, 기존 방식 시도: {e}")
                review_count = self.review_crawler.crawl_all_reviews(
                    output_path=review_file,
                    end_date=review_end_date
                )
                
            product_info["수집된_리뷰_개수"] = review_count


        return product_info

    def crawl_product_by_keyword(self, keyword: str, save_format: str = "json", split_mode: str = "aggressive", collect_reviews: bool = False, review_end_date: str = None, reviews_only: bool = False) -> Dict:
        """
        키워드로 상품 검색 및 크롤링

        Args:
            keyword: 검색 키워드
            save_format: 저장 형식 (json/csv/both)
            split_mode: 이미지 분할 모드
            collect_reviews: 리뷰 수집 여부
            review_end_date: 리뷰 수집 종료 날짜
            reviews_only: 리뷰만 수집 (이미지 건너뛰기)

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
        product_name = first_product.get("상품명", "Unknown")
        if product_name:
            product_name = product_name.split('\n')[0][:50]  # 상품명 앞부분만 사용
        else:
            product_name = "Unknown"
        save_folder = self.create_product_folder(product_name)

        # 상세 크롤링
        product_info = self.crawl_product_detail_by_url(product_url, save_folder, split_mode=split_mode, collect_reviews=collect_reviews, review_end_date=review_end_date, reviews_only=reviews_only)

        # 데이터 저장
        self.save_product_info(product_info, save_folder, save_format)

        result = {
            "상품명": product_info.get("상품명", ""),
            "폴더": save_folder,
            "이미지": product_info.get("이미지_경로", ""),
            "이미지_개수": product_info.get("이미지_개수", 0)
        }

        return result

    def crawl_product_by_url(self, product_url: str, product_name: str = None, save_format: str = "json", split_mode: str = "conservative", collect_reviews: bool = False, review_end_date: str = None, reviews_only: bool = False) -> Dict:
        """
        URL로 상품 크롤링

        Args:
            product_url: 상품 URL
            product_name: 상품명 (폴더명 생성용, None이면 자동 추출)
            save_format: 저장 형식 (json/csv/both)
            split_mode: 이미지 분할 모드
            collect_reviews: 리뷰 수집 여부
            review_end_date: 리뷰 수집 종료 날짜
            reviews_only: 리뷰만 수집 (이미지 건너뛰기)

        Returns:
            크롤링 결과 딕셔너리
        """
        print(f"\n{'='*60}")
        print(f"URL 크롤링")
        print(f"{'='*60}\n")

        # 상품명이 제공되지 않은 경우, 페이지에서 먼저 추출
        initial_info = None
        if not product_name:
            print("ℹ️  상품명을 페이지에서 추출합니다...")
            # 상세 페이지로 이동
            self.detail_crawler.go_to_product_detail(product_url)
            # 상품 정보에서 상품명만 먼저 추출
            initial_info = self.detail_crawler.extract_product_info_from_detail()
            product_name = initial_info.get("상품명", "Unknown")
            
            if product_name and product_name != "Unknown":
                # 상품명 정리 (첫 줄, 최대 50자)
                product_name = product_name.split('\n')[0][:50]
                print(f"✅ 상품명 추출 완료: {product_name}")
            else:
                product_name = f"product_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                print(f"⚠️  상품명을 찾을 수 없어 임시 이름 사용: {product_name}")

        # 폴더 생성 (이제 실제 상품명으로)
        save_folder = self.create_product_folder(product_name)

        # 1. 폴더 생성 직후 기본 정보 즉시 저장 (사용자 요청)
        if initial_info:
            print("💾 기본 상품 정보 즉시 저장...")
            self.save_product_info(initial_info, save_folder, save_format)

        # 상세 크롤링 (이미 로드된 정보와 페이지 상태 활용)
        # skip_navigation=True: 이미 go_to_product_detail을 호출했으므로
        # initial_info: 이미 추출한 정보를 전달하여 중복 추출 방지
        skip_nav = (initial_info is not None)
        
        product_info = self.crawl_product_detail_by_url(
            product_url, 
            save_folder, 
            split_mode=split_mode, 
            collect_reviews=collect_reviews, 
            review_end_date=review_end_date, 
            reviews_only=reviews_only,
            skip_navigation=skip_nav,
            initial_info=initial_info
        )

        # 데이터 저장 (최종 업데이트된 정보로 덮어쓰기)
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
