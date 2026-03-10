import streamlit as st
from PIL import Image
import time
from datetime import datetime
import pytz
from components.blog_automation import save_to_blog_folder, load_state, MENU_OPTIONS

def render_auto_posting_ui(set_bottom_message=None):
    st.title("🔁 블로그 자동포스팅 반복 도우미")
    st.markdown("### ⏰ 반복 주기 선택 및 자동포스팅")

    # 반복 주기 선택
    interval_map = {"1분": 60, "10분": 600, "30분": 1800, "60분": 3600}
    interval_label = st.selectbox("반복 주기", list(interval_map.keys()), index=1)
    interval_sec = interval_map[interval_label]

    # 반복 상태 관리
    if "auto_posting_running" not in st.session_state:
        st.session_state.auto_posting_running = False
    if "auto_posting_last_time" not in st.session_state:
        st.session_state.auto_posting_last_time = 0

    # 기존 입력란 재사용
    saved_menu, saved_title, saved_content, saved_images, saved_link_url, saved_img_url = load_state()
    title = st.text_input("📌 블로그 제목 (자동)", value=saved_title, key="auto_blog_title_input")
    content = st.text_area("📝 본문 (자동)", value=saved_content, height=500, key="auto_blog_content_input")
    images = st.file_uploader("🖼 이미지 업로드 (자동)", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="auto_images")
    exclude_images = st.checkbox("이미지 제외 (ON/OFF, 자동)", value=False, key="auto_exclude_images")
    prev_category = st.session_state.get("auto_selected_category", MENU_OPTIONS[0])
    menu_selection = st.selectbox(
        "📁 카테고리 선택 (자동)",
        MENU_OPTIONS,
        index=MENU_OPTIONS.index(prev_category) if prev_category in MENU_OPTIONS else 0,
        key="auto_menu_selection"
    )
    st.session_state["auto_selected_category"] = menu_selection

    # 반복 시작/중지 버튼
    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶️ 자동포스팅 반복 시작", key="auto_start_btn"):
            st.session_state.auto_posting_running = True
            st.session_state.auto_posting_last_time = 0
    with col2:
        if st.button("⏹️ 자동포스팅 반복 중지", key="auto_stop_btn"):
            st.session_state.auto_posting_running = False

    # 반복 실행 로직
    if st.session_state.auto_posting_running:
        now = time.time()
        last = st.session_state.auto_posting_last_time
        if last == 0 or now - last >= interval_sec:
            # 실제 자동포스팅 실행 (여기서는 블로그에 자동 게시와 동일하게 처리)
            images_pil = [] if exclude_images else ([Image.open(img) for img in images] if images else saved_images)
            try:
                from writers.naver_uploader import upload_to_naver_blog
                config = {
                    "naver_enabled": True,
                    "image_source": "none" if exclude_images else "bing",
                    "check_naver_login": True,
                }
                result = upload_to_naver_blog(
                    config,
                    title,
                    content,
                    menu_selection,
                    title,
                    ca_name_value=menu_selection
                )
                if result:
                    st.success(f"✅ [{interval_label} 반복] 네이버 블로그에 업로드 완료!")
                else:
                    st.warning(f"⚠️ [{interval_label} 반복] 네이버 블로그 업로드 실패!")
            except Exception as e:
                st.error(f"블로그 업로드 중 오류 발생: {e}")
            save_to_blog_folder(title, content, images_pil, menu_selection)
            st.session_state.auto_posting_last_time = now
        else:
            remain = int(interval_sec - (now - last))
            st.info(f"다음 자동포스팅까지 {remain}초 남음...")
    else:
        st.info("자동포스팅 반복이 중지됨.")

    # 수동 즉시 실행 버튼
    if st.button("🚀 블로그에 자동 게시 (즉시)", key="auto_post_now_btn"):
        images_pil = [] if exclude_images else ([Image.open(img) for img in images] if images else saved_images)
        try:
            from writers.naver_uploader import upload_to_naver_blog
            config = {
                "naver_enabled": True,
                "image_source": "none" if exclude_images else "bing",
                "check_naver_login": True,
            }
            result = upload_to_naver_blog(
                config,
                title,
                content,
                menu_selection,
                title,
                ca_name_value=menu_selection
            )
            if result:
                st.success("✅ [즉시] 네이버 블로그에 업로드 완료!")
            else:
                st.warning("⚠️ [즉시] 네이버 블로그 업로드 실패!")
        except Exception as e:
            st.error(f"블로그 업로드 중 오류 발생: {e}")
        save_to_blog_folder(title, content, images_pil, menu_selection)

    st.markdown("---")
    st.info("이 페이지는 자동포스팅 반복 및 즉시 실행 기능을 제공합니다. 반복 주기와 입력값을 설정 후 시작하세요.")
