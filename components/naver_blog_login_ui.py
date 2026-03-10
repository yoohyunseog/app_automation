import streamlit as st
from blog_automation.naver_login import (
    naver_login,
    after_login_action,
    is_driver_alive,
    load_credentials,
    save_credentials,
    load_blog_url,
    save_blog_url
)

def render_blog_ui():
    st.title("📝 블로그 자동화 도구")
    st.write("🔧 여기서 블로그 관련 자동화 기능이 실행됩니다.")

    if "naver_logged_in" not in st.session_state:
        st.session_state.naver_logged_in = False

    if st.session_state.naver_logged_in and not is_driver_alive():
        st.session_state.naver_logged_in = False
        st.warning("❗ 브라우저 세션이 종료되어 다시 로그인해야 합니다.")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("🔐 네이버 로그인 정보 입력")

        saved_id, saved_pw = load_credentials()

        user_id = st.text_input("아이디", value=saved_id, key="user_id_input")
        user_pw = st.text_input("비밀번호", value=saved_pw, type="password", key="user_pw_input")

        if st.button("💾 아이디/비밀번호 저장"):
            save_credentials(user_id, user_pw)
            st.success("✅ 저장 완료")

        if saved_id:
            st.text(f"📌 저장된 아이디: {saved_id}")

        st.markdown("---")
        st.subheader("🔗 내 블로그 주소 설정")

        saved_blog_url = load_blog_url()
        blog_url_input = st.text_input("블로그 주소 입력", value=saved_blog_url, placeholder="예: https://blog.naver.com/내아이디")

        if st.button("💾 블로그 주소 저장"):
            if blog_url_input:
                save_blog_url(blog_url_input)
                st.success("✅ 블로그 주소가 저장되었습니다.")
            else:
                st.warning("❗ 블로그 주소를 입력해주세요.")

    with col1:
        if not st.session_state.naver_logged_in:
            st.warning("🚫 아직 로그인하지 않았습니다.")
            if st.button("🔐 로그인 시작", key="login_btn"):
                naver_login()
                st.session_state.naver_logged_in = True
                st.rerun()
        else:
            st.success("✅ 네이버 로그인 상태 유지 중")

    with col2:
        if st.session_state.naver_logged_in:
            if st.button("🏠 내 블로그 이동", key="after_action_btn"):
                if not is_driver_alive():
                    st.error("❌ 브라우저 세션이 종료되어 작업을 실행할 수 없습니다.")
                    st.session_state.naver_logged_in = False
                    st.rerun()
                else:
                    after_login_action()
        else:
            st.button("🏠 내 블로그 이동", disabled=True, key="after_action_btn_disabled")
