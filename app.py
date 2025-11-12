"""
올리브영 크롤러 Streamlit GUI
"""
import streamlit as st
import sys
import os

# 현재 파일의 디렉토리를 기준으로 src 폴더 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from oliveyoung_crawler import OliveyoungIntegratedCrawler
from PIL import Image
import pandas as pd
import json


# 페이지 설정
st.set_page_config(
    page_title="올리브영 크롤러",
    page_icon="🛒",
    layout="wide"
)

# 세션 상태 초기화
if 'crawler' not in st.session_state:
    st.session_state.crawler = None
if 'results' not in st.session_state:
    st.session_state.results = []


def init_crawler(headless=True):
    """크롤러 초기화"""
    if st.session_state.crawler is None:
        with st.spinner("브라우저 시작 중..."):
            st.session_state.crawler = OliveyoungIntegratedCrawler(headless=headless)
            st.session_state.crawler.start()
        st.success("✅ 브라우저 시작 완료!")


def stop_crawler():
    """크롤러 종료"""
    if st.session_state.crawler is not None:
        st.session_state.crawler.stop()
        st.session_state.crawler = None
        st.info("브라우저가 종료되었습니다.")


# 타이틀
st.title("🛒 올리브영 상품 크롤러")
st.markdown("---")

# 사이드바
with st.sidebar:
    st.header("⚙️ 설정")

    # 브라우저 표시 옵션
    show_browser = st.checkbox("브라우저 표시", value=False,
                              help="체크하면 크롬 브라우저가 화면에 표시됩니다")

    # 저장 형식
    save_format = st.radio(
        "저장 형식",
        options=["json", "csv", "both"],
        index=2,
        help="상품 정보를 저장할 파일 형식"
    )

    st.markdown("---")

    # 크롤러 상태
    st.subheader("🔧 크롤러 상태")
    if st.session_state.crawler is None:
        st.warning("⏸️ 중지됨")
    else:
        st.success("▶️ 실행 중")

    # 크롤러 제어 버튼
    col1, col2 = st.columns(2)
    with col1:
        if st.button("시작", use_container_width=True):
            init_crawler(headless=not show_browser)
    with col2:
        if st.button("종료", use_container_width=True):
            stop_crawler()

    st.markdown("---")

    # 히스토리
    st.subheader("📜 크롤링 히스토리")
    if st.session_state.results:
        for idx, result in enumerate(reversed(st.session_state.results[-5:])):
            with st.expander(f"{len(st.session_state.results)-idx}. {result['상품명'][:20]}..."):
                st.text(f"폴더: {result['폴더']}")
                st.text(f"이미지: {result['이미지_개수']}개")
    else:
        st.info("크롤링 기록이 없습니다")


# 메인 영역
tab1, tab2 = st.tabs(["🔍 키워드 검색", "🔗 URL 직접 입력"])

# Tab 1: 키워드 검색
with tab1:
    st.header("키워드로 상품 검색")
    st.markdown("검색어를 입력하면 첫 번째 검색 결과 상품의 상세 이미지를 크롤링합니다.")

    # 입력 폼
    with st.form("keyword_form"):
        keyword = st.text_input(
            "검색 키워드",
            placeholder="예: 한율 달빛유자 비타민 톤업팩폼",
            help="올리브영에서 검색할 상품명을 입력하세요"
        )

        submitted = st.form_submit_button("🔍 검색 및 크롤링 시작", use_container_width=True)

        if submitted:
            if not keyword:
                st.error("❌ 검색어를 입력해주세요!")
            elif st.session_state.crawler is None:
                st.error("❌ 먼저 사이드바에서 크롤러를 시작해주세요!")
            else:
                # 크롤링 실행
                with st.spinner(f"'{keyword}' 크롤링 중... 잠시만 기다려주세요 ⏳"):
                    try:
                        result = st.session_state.crawler.crawl_product_by_keyword(
                            keyword=keyword,
                            save_format=save_format
                        )

                        st.session_state.results.append(result)

                        st.success("🎉 크롤링 완료!")

                        # 결과 표시
                        col1, col2 = st.columns([2, 1])

                        with col1:
                            st.subheader("📋 상품 정보")
                            st.text(f"상품명: {result['상품명']}")
                            st.text(f"저장 폴더: {result['폴더']}")
                            st.text(f"이미지 개수: {result['이미지_개수']}개")

                        with col2:
                            st.subheader("📂 파일")
                            if os.path.exists(result['폴더']):
                                files = os.listdir(result['폴더'])
                                for file in files:
                                    st.text(f"• {file}")

                        # 이미지 미리보기
                        if result['이미지'] and os.path.exists(result['이미지']):
                            st.subheader("🖼️ 병합된 이미지")
                            try:
                                img = Image.open(result['이미지'])
                                # 이미지가 너무 크면 너비를 제한
                                st.image(img, use_container_width=True)
                            except Exception as e:
                                st.error(f"이미지 표시 중 오류: {e}")

                    except Exception as e:
                        st.error(f"❌ 크롤링 중 오류 발생: {e}")
                        import traceback
                        with st.expander("오류 상세 정보"):
                            st.code(traceback.format_exc())


# Tab 2: URL 직접 입력
with tab2:
    st.header("상품 URL 직접 입력")
    st.markdown("올리브영 상품 페이지 URL을 직접 입력하여 크롤링합니다.")

    # 입력 폼
    with st.form("url_form"):
        product_url = st.text_input(
            "상품 URL",
            placeholder="https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo=...",
            help="올리브영 상품 페이지의 전체 URL을 입력하세요"
        )

        product_name = st.text_input(
            "상품명 (선택사항)",
            placeholder="폴더명으로 사용할 상품명",
            help="비워두면 자동으로 추출됩니다"
        )

        submitted = st.form_submit_button("🔗 URL로 크롤링 시작", use_container_width=True)

        if submitted:
            if not product_url:
                st.error("❌ 상품 URL을 입력해주세요!")
            elif not product_url.startswith("https://www.oliveyoung.co.kr"):
                st.error("❌ 올바른 올리브영 URL이 아닙니다!")
            elif st.session_state.crawler is None:
                st.error("❌ 먼저 사이드바에서 크롤러를 시작해주세요!")
            else:
                # 크롤링 실행
                with st.spinner("크롤링 중... 잠시만 기다려주세요 ⏳"):
                    try:
                        result = st.session_state.crawler.crawl_product_by_url(
                            product_url=product_url,
                            product_name=product_name if product_name else None,
                            save_format=save_format
                        )

                        st.session_state.results.append(result)

                        st.success("🎉 크롤링 완료!")

                        # 결과 표시
                        col1, col2 = st.columns([2, 1])

                        with col1:
                            st.subheader("📋 상품 정보")
                            st.text(f"상품명: {result['상품명']}")
                            st.text(f"저장 폴더: {result['폴더']}")
                            st.text(f"이미지 개수: {result['이미지_개수']}개")

                        with col2:
                            st.subheader("📂 파일")
                            if os.path.exists(result['폴더']):
                                files = os.listdir(result['폴더'])
                                for file in files:
                                    st.text(f"• {file}")

                        # 이미지 미리보기
                        if result['이미지'] and os.path.exists(result['이미지']):
                            st.subheader("🖼️ 병합된 이미지")
                            try:
                                img = Image.open(result['이미지'])
                                st.image(img, use_container_width=True)
                            except Exception as e:
                                st.error(f"이미지 표시 중 오류: {e}")

                    except Exception as e:
                        st.error(f"❌ 크롤링 중 오류 발생: {e}")
                        import traceback
                        with st.expander("오류 상세 정보"):
                            st.code(traceback.format_exc())


# 푸터
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>🛒 올리브영 상품 크롤러 v2.0</p>
    <p>상품 설명 이미지를 자동으로 수집하고 병합합니다</p>
</div>
""", unsafe_allow_html=True)
