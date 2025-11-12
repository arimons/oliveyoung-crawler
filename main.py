"""
올리브영 크롤러 - 메인 실행 스크립트

사용법:
    python main.py

실행하면 대화형으로 검색어와 옵션을 입력할 수 있습니다.
"""
import sys
sys.path.append('src')

from crawler_selenium import OliveyoungCrawler


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("🛒 올리브영 상품 크롤러")
    print("=" * 60)

    # 사용자 입력 받기
    search_keyword = input("\n🔍 검색할 상품명을 입력하세요: ").strip()

    if not search_keyword:
        print("❌ 검색어를 입력해야 합니다.")
        return

    try:
        max_products = int(input(f"📊 추출할 상품 개수를 입력하세요 (기본값: 10): ").strip() or "10")
    except ValueError:
        max_products = 10
        print(f"⚠️  올바른 숫자가 아닙니다. 기본값 {max_products}개로 설정합니다.")

    # headless 모드 선택
    show_browser = input("\n👀 브라우저를 화면에 표시할까요? (y/n, 기본값: n): ").strip().lower()
    headless = show_browser != 'y'

    # 저장 형식 선택
    save_format = input("💾 저장 형식을 선택하세요 (json/csv/both, 기본값: both): ").strip().lower()
    if save_format not in ['json', 'csv', 'both']:
        save_format = 'both'

    print("\n" + "=" * 60)
    print("크롤링을 시작합니다...")
    print("=" * 60)

    # 크롤러 실행
    crawler = OliveyoungCrawler(headless=headless)

    try:
        # 브라우저 시작
        crawler.start()

        # 홈페이지 접속
        crawler.navigate_to_home()

        # 제품 검색
        crawler.search_product(search_keyword)

        # 상품 정보 추출
        products = crawler.extract_product_info(max_products=max_products)

        if products:
            print(f"\n✅ 추출 성공! 총 {len(products)}개 상품")

            # 데이터 저장
            saved_files = []

            if save_format in ['json', 'both']:
                json_file = crawler.save_to_json(products, f"oliveyoung_{search_keyword}")
                saved_files.append(json_file)

            if save_format in ['csv', 'both']:
                csv_file = crawler.save_to_csv(products, f"oliveyoung_{search_keyword}")
                saved_files.append(csv_file)

            # 결과 출력
            print("\n" + "=" * 60)
            print("🎉 크롤링 완료!")
            print("=" * 60)
            print(f"검색어: {search_keyword}")
            print(f"추출 상품 수: {len(products)}개")
            print(f"저장된 파일:")
            for file in saved_files:
                print(f"  - {file}")
            print("=" * 60)

        else:
            print("\n⚠️  추출된 상품이 없습니다.")
            print("   다른 검색어로 다시 시도해보세요.")

    except KeyboardInterrupt:
        print("\n\n⚠️  사용자가 중단했습니다.")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        print("\n문제가 계속되면 다음을 확인하세요:")
        print("  1. 인터넷 연결 상태")
        print("  2. 올리브영 웹사이트 접속 가능 여부")
        print("  3. Chrome 브라우저 설치 여부")

        import traceback
        traceback.print_exc()

    finally:
        crawler.stop()


if __name__ == "__main__":
    main()
