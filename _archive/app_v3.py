"""
올리브영 크롤러 Streamlit GUI v2
진행 상황 표시 및 폴더 열기 기능 추가
"""
import streamlit as st
import sys
import os
import subprocess
import platform

# 현재 파일의 디렉토리를 기준으로 src 폴더 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from oliveyoung_crawler import OliveyoungIntegratedCrawler
from PIL import Image
import pandas as pd
import json
import time


# 페이지 설정
st.set_page_config(
    page_title="올리브영 크롤러",
    page_icon="🛒",
    layout="wide"
)


def open_folder(folder_path):
    """폴더를 파일 탐색기에서 열기"""
    try:
        system = platform.system()
        if system == "Darwin":  # macOS
            subprocess.run(["open", folder_path])
        elif system == "Windows":
            subprocess.run(["explorer", folder_path])
        elif system == "Linux":
            subprocess.run(["xdg-open", folder_path])
        return True
    except Exception as e:
        st.error(f"폴더를 열 수 없습니다: {e}")
        return False


# 세션 상태 초기화
if 'crawler' not in st.session_state:
    st.session_state.crawler = None
if 'results' not in st.session_state:
    st.session_state.results = []
if 'headless' not in st.session_state:
    st.session_state.headless = False  # 봇 감지 회피를 위해 항상 GUI 모드


def init_crawler():
    """크롤러 초기화"""
    if st.session_state.crawler is None:
        # headless 옵션 적용
        headless = st.session_state.headless
        st.session_state.crawler = OliveyoungIntegratedCrawler(headless=headless)
        st.session_state.crawler.start()
        return True
    return False


def stop_crawler():
    """크롤러 종료"""
    if st.session_state.crawler is not None:
        st.session_state.crawler.stop()
        st.session_state.crawler = None


# 타이틀
st.title("🛒 올리브영 상품 크롤러 v2.0")
st.markdown("---")

# 사이드바
with st.sidebar:
    st.header("⚙️ 설정")

    # 브라우저 표시 옵션 (봇 감지 회피를 위해 항상 ON)
    # show_browser = st.checkbox(
    #     "브라우저 표시",
    #     value=True,
    #     disabled=True,
    #     help="봇 감지 회피를 위해 항상 표시됩니다",
    #     key="show_browser_checkbox"
    # )
    st.caption("✅ 브라우저 표시: 항상 ON (봇 감지 회피)")

    # headless는 항상 False (GUI 모드)
    st.session_state.headless = False

    # 저장 형식
    save_format = st.radio(
        "저장 형식",
        options=["json", "csv", "both"],
        index=2,
        help="상품 정보를 저장할 파일 형식"
    )

    st.markdown("#### 📦 수집 항목 선택")
    st.caption("상품 기본 정보는 항상 수집됩니다")

    # 이미지 수집 옵션
    collect_images = st.checkbox(
        "상세페이지 이미지 수집",
        value=True,
        help="상품 상세 페이지의 이미지를 수집하여 병합합니다"
    )

    # 리뷰 수집 옵션
    collect_reviews = st.checkbox(
        "리뷰 텍스트 수집",
        value=False,
        help="상품 리뷰 텍스트를 수집합니다 (시간이 더 걸릴 수 있음)"
    )

    # 리뷰 수집 날짜 범위 (리뷰 수집이 체크된 경우만 표시)
    review_end_date = None
    if collect_reviews:
        from datetime import datetime, timedelta

        use_date_filter = st.checkbox(
            "날짜 범위 설정",
            value=False,
            help="특정 날짜까지의 리뷰만 수집합니다"
        )

        if use_date_filter:
            # 기본값: 1개월 전
            default_date = datetime.now() - timedelta(days=30)

            review_end_date_input = st.date_input(
                "수집 종료 날짜",
                value=default_date,
                help="이 날짜 이후의 리뷰만 수집합니다 (이 날짜 포함하지 않음)"
            )

            # YYYY.MM.DD 형식으로 변환
            review_end_date = review_end_date_input.strftime("%Y.%m.%d")
            st.caption(f"📅 {review_end_date} 이후 리뷰 수집")

    # 이미지 분할 모드 (이미지 수집이 체크된 경우만 표시)
    if collect_images:
        st.markdown("#### 🖼️ 이미지 분할 모드")
        split_mode = st.radio(
            "분할 방식",
            options=["conservative", "aggressive", "tile"],
            index=1,  # aggressive가 기본값
            format_func=lambda x: {
                "conservative": " 최대한 합치기",
                "aggressive": "🎨 색상 경계로 분할 (기본)",
                "tile": "🖥️ 타일 레이아웃"
            }.get(x, x),
            help="최대한 합치기: 이미지 최대 높이까지 합침 | 색상 경계로 분할: 디자인이 바뀌면 분할 | 타일 레이아웃: 16:9 비율로 분할"
        )
    else:
        split_mode = "aggressive"  # 기본값

    st.markdown("---")

    # 크롤러 상태
    st.subheader("🔧 크롤러 상태")
    if st.session_state.crawler is None:
        st.warning("⏸️ 중지됨")

        if st.button("▶️ 시작", use_container_width=True):
            with st.spinner("브라우저 시작 중..."):
                if init_crawler():
                    st.success("✅ 브라우저 시작 완료!")
                    st.rerun()
    else:
        st.success("▶️ 실행 중")

        if st.button("⏹️ 종료", use_container_width=True):
            stop_crawler()
            st.info("브라우저가 종료되었습니다.")
            st.rerun()

    st.markdown("---")

    # 작업 폴더 열기
    st.subheader("📂 작업 폴더")
    if st.button("📁 전체 작업 폴더 열기", use_container_width=True):
        data_folder = os.path.join(os.getcwd(), "data")
        if os.path.exists(data_folder):
            open_folder(data_folder)
        else:
            st.warning("아직 크롤링한 데이터가 없습니다")

    st.markdown("---")

    # 히스토리
    st.subheader("📜 크롤링 히스토리")
    if st.session_state.results:
        for idx, result in enumerate(reversed(st.session_state.results[-5:])):
            with st.expander(f"{len(st.session_state.results)-idx}. {result['상품명'][:20]}..."):
                st.text(f"⭐ 별점: {result.get('별점', 'N/A')}점")
                st.text(f"📊 총 리뷰: {result.get('리뷰_총개수', 0)}개")
                if result.get('수집된_리뷰_개수', 0) > 0:
                    st.text(f"📝 수집된 리뷰: {result['수집된_리뷰_개수']}개")
                if st.button(f"📁 폴더 열기", key=f"open_{idx}"):
                    open_folder(result['폴더'])
    else:
        st.info("크롤링 기록이 없습니다")


# 메인 영역
tab1, tab2 = st.tabs(["🔗 URL 직접 입력", "🔍 키워드 검색"])

# Tab 1: 키워드 검색
with tab2:
    st.header("키워드로 상품 검색")

    keyword = st.text_input(
        "검색 키워드",
        placeholder="예: 한율 달빛유자 비타민 톤업팩폼",
        help="올리브영에서 검색할 상품명을 입력하세요",
        key="keyword_input"
    )

    if st.button("🔍 검색 및 크롤링 시작", use_container_width=True, type="primary"):
        if not keyword:
            st.error("❌ 검색어를 입력해주세요!")
        else:
            # 크롤러가 없거나 드라이버가 종료된 경우 자동으로 시작
            if st.session_state.crawler is None or st.session_state.crawler.base_crawler.driver is None:
                with st.spinner("브라우저 재시작 중..."):
                    stop_crawler()  # 기존에 문제가 있는 크롤러가 있다면 완전히 종료
                    if init_crawler():
                        st.success("✅ 브라우저 시작 완료!")
                        time.sleep(0.5)  # UI 업데이트 대기
            # 진행 상황 표시 영역
            progress_bar = st.progress(0)
            status_text = st.empty()

            try:
                # 1. 검색
                status_text.text("🔍 상품 검색 중...")
                progress_bar.progress(0.1)

                st.session_state.crawler.base_crawler.navigate_to_home()
                progress_bar.progress(0.2)

                st.session_state.crawler.base_crawler.search_product(keyword)
                progress_bar.progress(0.3)

                # 2. 첫 번째 상품 가져오기
                status_text.text("📋 상품 정보 추출 중...")
                products = st.session_state.crawler.base_crawler.extract_product_info(max_products=1)

                if not products:
                    st.error("❌ 검색 결과가 없습니다")
                    progress_bar.empty()
                    status_text.empty()
                else:
                    first_product = products[0]
                    product_url = first_product["URL"]
                    product_name = first_product["상품명"].split('\n')[0][:50]

                    progress_bar.progress(0.4)

                    # 3. 폴더 생성
                    status_text.text("📁 폴더 생성 중...")
                    save_folder = st.session_state.crawler.create_product_folder(product_name)
                    progress_bar.progress(0.5)

                    # 4. 상세 페이지 이동
                    status_text.text("🔗 상품 페이지로 이동 중...")
                    st.session_state.crawler.detail_crawler.go_to_product_detail(product_url)
                    progress_bar.progress(0.5)

                    # 5. 리뷰 메타데이터 추출 (항상 실행)
                    status_text.text("📊 리뷰 정보 추출 중...")
                    review_metadata = st.session_state.crawler.detail_crawler.extract_review_metadata()
                    product_info = {
                        "상품명": product_name,
                        "리뷰_총개수": review_metadata.get("리뷰_총개수", 0),
                        "별점": review_metadata.get("별점", 0.0)
                    }
                    progress_bar.progress(0.6)

                    # 6. 이미지 수집 (옵션)
                    if collect_images:
                        # 더보기 버튼 클릭
                        status_text.text("🔘 '더보기' 버튼 클릭 중...")
                        st.session_state.crawler.detail_crawler.click_more_button()
                        progress_bar.progress(0.65)

                        # 이미지 URL 추출
                        status_text.text("📸 이미지 URL 추출 중...")
                        image_urls = st.session_state.crawler.detail_crawler.extract_product_images()
                        progress_bar.progress(0.7)

                        # 이미지 다운로드 및 병합
                        if not image_urls:
                            st.warning("⚠️  추출된 이미지가 없습니다")
                        else:
                            try:
                                def update_download_progress(message, current, total):
                                    """다운로드 진행 상황 업데이트"""
                                    status_text.text(message)
                                    # 0.7 ~ 0.8 범위에서 진행률 표시
                                    progress = 0.7 + (current / total) * 0.1
                                    progress_bar.progress(progress)

                                output_image_path = os.path.join(save_folder, "product_detail_merged.jpg")
                                saved_path = st.session_state.crawler.detail_crawler.download_and_merge_images(
                                    image_urls, output_image_path, progress_callback=update_download_progress,
                                    split_mode=split_mode
                                )

                                product_info["이미지_경로"] = saved_path
                                product_info["이미지_개수"] = len(image_urls)
                            except Exception as e:
                                st.error(f"⚠️  이미지 병합 중 오류 발생: {e}")

                    progress_bar.progress(0.8)

                    # 7. 리뷰 텍스트 수집 (옵션)
                    if collect_reviews:
                        status_text.text("📝 리뷰 텍스트 수집 중...")
                        review_file = os.path.join(save_folder, "reviews.txt")
                        review_count = st.session_state.crawler.review_crawler.crawl_all_reviews(
                            output_path=review_file,
                            end_date=review_end_date
                        )
                        product_info["수집된_리뷰_개수"] = review_count

                    progress_bar.progress(0.9)

                    # 8. 데이터 저장
                    status_text.text("💾 데이터 저장 중...")
                    st.session_state.crawler.save_product_info(product_info, save_folder, save_format)

                    progress_bar.progress(1.0)
                    status_text.text("✅ 완료!")

                    # 결과 저장
                    result = {
                        "상품명": product_name,
                        "폴더": save_folder,
                        "이미지": product_info.get("이미지_경로", ""),
                        "별점": product_info.get("별점", 0.0),
                        "리뷰_총개수": product_info.get("리뷰_총개수", 0),
                        "수집된_리뷰_개수": product_info.get("수집된_리뷰_개수", 0)
                    }
                    st.session_state.results.append(result)

                    # 성공 메시지
                    st.success("🎉 크롤링 완료!")

                    # 수집 결과 요약
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("⭐ 별점", f"{product_info.get('별점', 0.0)}점")
                    with col2:
                        st.metric("📊 총 리뷰", f"{product_info.get('리뷰_총개수', 0)}개")

                    if product_info.get('수집된_리뷰_개수', 0) > 0:
                        st.info(f"📝 {product_info['수집된_리뷰_개수']}개의 리뷰를 수집했습니다")

                    # 진행 표시 제거
                    progress_bar.empty()
                    status_text.empty()

            except Exception as e:
                st.error(f"❌ 크롤링 중 오류 발생: {e}")
                import traceback
                with st.expander("오류 상세 정보"):
                    st.code(traceback.format_exc())
                progress_bar.empty()
                status_text.empty()


# Tab 2: URL 직접 입력
with tab1:
    st.header("상품 URL 직접 입력")

    product_url = st.text_input(
        "상품 URL",
        placeholder="https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo=...",
        help="올리브영 상품 페이지의 전체 URL을 입력하세요",
        key="url_input"
    )

    product_name_input = st.text_input(
        "상품명 (선택사항)",
        placeholder="폴더명으로 사용할 상품명",
        help="비워두면 자동으로 추출됩니다",
        key="product_name_input"
    )

    if st.button("🔗 URL로 크롤링 시작", use_container_width=True, type="primary"):
        if not product_url:
            st.error("❌ 상품 URL을 입력해주세요!")
        elif not product_url.startswith("https://www.oliveyoung.co.kr"):
            st.error("❌ 올바른 올리브영 URL이 아닙니다!")
        else:
            # 크롤러가 없거나 드라이버가 종료된 경우 자동으로 시작
            if st.session_state.crawler is None or st.session_state.crawler.base_crawler.driver is None:
                with st.spinner("브라우저 재시작 중..."):
                    stop_crawler() # 기존에 문제가 있는 크롤러가 있다면 완전히 종료
                    if init_crawler():
                        st.success("✅ 브라우저 시작 완료!")
                        time.sleep(0.5)  # UI 업데이트 대기
            # 진행 상황 표시 영역
            progress_bar = st.progress(0)
            status_text = st.empty()

            try:
                # 1. 상세 페이지 이동
                status_text.text("🔗 상품 페이지로 이동 중...")
                progress_bar.progress(0.1)

                st.session_state.crawler.detail_crawler.go_to_product_detail(product_url)
                progress_bar.progress(0.2)

                # 2. 상품명 추출 (입력 안 됐으면)
                if not product_name_input:
                    status_text.text("📝 상품명 추출 중...")
                    detail_info = st.session_state.crawler.detail_crawler.extract_product_info_from_detail()
                    product_name = detail_info.get("상품명", "Unknown_Product").split('\n')[0][:50]
                else:
                    product_name = product_name_input

                progress_bar.progress(0.3)

                # 3. 리뷰 메타데이터 추출 (항상 실행)
                status_text.text("📊 리뷰 정보 추출 중...")
                review_metadata = st.session_state.crawler.detail_crawler.extract_review_metadata()
                product_info = {
                    "상품명": product_name,
                    "리뷰_총개수": review_metadata.get("리뷰_총개수", 0),
                    "별점": review_metadata.get("별점", 0.0)
                }
                progress_bar.progress(0.4)

                # 4. 폴더 생성
                status_text.text("📁 폴더 생성 중...")
                save_folder = st.session_state.crawler.create_product_folder(product_name)
                progress_bar.progress(0.5)

                # 5. 이미지 수집 (옵션)
                if collect_images:
                    # 더보기 버튼 클릭
                    status_text.text("🔘 '더보기' 버튼 클릭 중...")
                    st.session_state.crawler.detail_crawler.click_more_button()
                    progress_bar.progress(0.55)

                    # 이미지 URL 추출
                    status_text.text("📸 이미지 URL 추출 중...")
                    image_urls = st.session_state.crawler.detail_crawler.extract_product_images()
                    progress_bar.progress(0.6)

                    # 이미지 다운로드 및 병합
                    if not image_urls:
                        st.warning("⚠️  추출된 이미지가 없습니다")
                    else:
                        try:
                            def update_download_progress_url(message, current, total):
                                """다운로드 진행 상황 업데이트"""
                                status_text.text(message)
                                # 0.6 ~ 0.75 범위에서 진행률 표시
                                progress = 0.6 + (current / total) * 0.15
                                progress_bar.progress(progress)

                            output_image_path = os.path.join(save_folder, "product_detail_merged.jpg")
                            saved_path = st.session_state.crawler.detail_crawler.download_and_merge_images(
                                image_urls, output_image_path, progress_callback=update_download_progress_url,
                                split_mode=split_mode
                            )

                            product_info["이미지_경로"] = saved_path
                            product_info["이미지_개수"] = len(image_urls)
                        except Exception as e:
                            st.error(f"⚠️  이미지 병합 중 오류 발생: {e}")

                progress_bar.progress(0.75)

                # 6. 리뷰 텍스트 수집 (옵션)
                if collect_reviews:
                    status_text.text("📝 리뷰 텍스트 수집 중...")
                    review_file = os.path.join(save_folder, "reviews.txt")
                    review_count = st.session_state.crawler.review_crawler.crawl_all_reviews(
                        output_path=review_file,
                        end_date=review_end_date
                    )
                    product_info["수집된_리뷰_개수"] = review_count

                progress_bar.progress(0.85)

                # 7. 데이터 저장
                status_text.text("💾 데이터 저장 중...")
                st.session_state.crawler.save_product_info(product_info, save_folder, save_format)

                progress_bar.progress(1.0)
                status_text.text("✅ 완료!")

                # 결과 저장
                result = {
                    "상품명": product_name,
                    "폴더": save_folder,
                    "이미지": product_info.get("이미지_경로", ""),
                    "별점": product_info.get("별점", 0.0),
                    "리뷰_총개수": product_info.get("리뷰_총개수", 0),
                    "수집된_리뷰_개수": product_info.get("수집된_리뷰_개수", 0)
                }
                st.session_state.results.append(result)

                # 성공 메시지
                st.success("🎉 크롤링 완료!")

                # 수집 결과 요약
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("⭐ 별점", f"{product_info.get('별점', 0.0)}점")
                with col2:
                    st.metric("📊 총 리뷰", f"{product_info.get('리뷰_총개수', 0)}개")

                if product_info.get('수집된_리뷰_개수', 0) > 0:
                    st.info(f"📝 {product_info['수집된_리뷰_개수']}개의 리뷰를 수집했습니다")

                # 진행 표시 제거
                progress_bar.empty()
                status_text.empty()

            except Exception as e:
                st.error(f"❌ 크롤링 중 오류 발생: {e}")
                import traceback
                with st.expander("오류 상세 정보"):
                    st.code(traceback.format_exc())
                progress_bar.empty()
                status_text.empty()


# --- 최신 결과 표시 ---
if st.session_state.results:
    st.markdown("---")
    st.header("📄 최신 크롤링 결과")

    latest_result = st.session_state.results[-1]

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.subheader("📋 상품 정보")
        st.text(f"상품명: {latest_result['상품명']}")

    with col2:
        st.subheader("📂 저장 위치")
        st.code(latest_result['폴더'], language="text")

    with col3:
        st.subheader("🔧 작업")
        if st.button("📁 폴더 열기", key="open_latest_result_folder"):
            open_folder(latest_result['폴더'])

    # 이미지 미리보기
    if latest_result['이미지'] and os.path.exists(latest_result['이미지']):
        st.subheader("🖼️ 병합된 이미지 미리보기")
        try:
            img = Image.open(latest_result['이미지'])
            st.image(img, use_column_width=True)
        except Exception as e:
            st.error(f"이미지 표시 중 오류: {e}")


# 푸터
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>🛒 올리브영 상품 크롤러 v2.0 - Streamlit 진행 상황 표시 지원</p>
</div>
""", unsafe_allow_html=True)
