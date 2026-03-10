import streamlit as st
from components.nb_scout_launcher import launch_nb_scout, open_trend_page  # open_trend_page 함수 import
import os
import json

SAVE_PATH = r"E:\Ai project\nb_wfa\data\blog_keyword\searched_keywords.json"

def render_nb_scout_page():
    st.markdown("## 🛰 NB-Scout: 키워드 분석기")
    st.write("키워드를 입력하거나 아래 목록에서 선택해 실행하세요.")

    # 초기화
    if "searched_keywords" not in st.session_state:
        if os.path.exists(SAVE_PATH):
            with open(SAVE_PATH, "r", encoding="utf-8") as f:
                st.session_state.searched_keywords = json.load(f)
        else:
            st.session_state.searched_keywords = []

    # 키워드 상태를 별도 처리
    if "selected_keyword" not in st.session_state:
        st.session_state.selected_keyword = ""

    # 입력 위젯 (선택된 키워드가 있으면 기본값으로 설정)
    keyword = st.text_input("🔑 분석할 키워드 입력", value=st.session_state.selected_keyword, key="input_box")

    if st.button("🚀 실행"):
        keyword = keyword.strip()
        if keyword:
            launch_nb_scout(keyword)
            if keyword not in st.session_state.searched_keywords:
                st.session_state.searched_keywords.insert(0, keyword)
                with open(SAVE_PATH, "w", encoding="utf-8") as f:
                    json.dump(st.session_state.searched_keywords, f, ensure_ascii=False, indent=2)
            st.success(f"'{keyword}' 실행 완료!")
        else:
            st.warning("키워드를 입력해주세요.")


    # 트렌드 페이지로 이동하는 버튼 추가
    if st.button("🔗 트렌드 페이지로 이동"):
        # open_trend_page() 호출
        open_trend_page()


    # 최근 키워드
    if st.session_state.searched_keywords:
        st.markdown("### 📚 최근 키워드")
        cols = st.columns(3)
        for idx, kw in enumerate(st.session_state.searched_keywords):
            if cols[idx % 3].button(kw, key=f"kw_{idx}"):
                launch_nb_scout(kw)
                st.session_state.selected_keyword = kw  # 선택된 키워드를 입력란 기본값으로 반영
                # 입력란에 선택된 키워드를 기본값으로 설정
                st.experimental_rerun()  # 리렌더링이 아닌 선택된 키워드를 입력란에 바로 반영하도록 st.experimental_rerun() 사용
