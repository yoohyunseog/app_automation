import streamlit as st
from PIL import Image
import time
from datetime import datetime
import pytz
import os
from components.blog_automation import save_to_blog_folder, load_state, MENU_OPTIONS

def render_auto_posting_ui(set_bottom_message=None):
    st.title("🔁 블로그 자동포스팅 반복 도우미")
    st.markdown("### ⏰ 반복 주기 선택 및 자동포스팅")

    # Ollama 모델 선택 (기본값: gpt-oss:120b-cloud)
    ollama_models = [
        "news-singleline:latest",
        "deepseek-r1:8b",
        "gpt-oss:20b",
        "gpt-oss:120b-cloud",
        "gemma3:4b",
        "gemma3:12b",
        "gemma3:1b",
        "gemma3:27b",
        "qwen2.5:latest",
        "mistral:latest"
    ]
    default_model_index = ollama_models.index("gpt-oss:120b-cloud") if "gpt-oss:120b-cloud" in ollama_models else 0
    selected_ollama_model = st.selectbox(
        "Ollama AI 모델 선택 (직접 입력 가능)",
        ollama_models,
        index=default_model_index,
        key="auto_ollama_model_select"
    )
    custom_model = st.text_input("직접 입력 (선택사항)", value="", key="auto_ollama_custom_model")
    if custom_model.strip():
        selected_ollama_model = custom_model.strip()

# --- 참소식.com/feed.xml Ollama AI 자동 포스팅 버튼 ---
    st.markdown("---")
    st.subheader("🌐 Ollama AI로 참소식.com/feed.xml 자동 포스팅")
    if st.button("🌐 Ollama AI로 참소식.com/feed.xml 자동 포스팅", key="auto_chamsosik_btn"):
        import requests
        import ollama
        from xml.etree import ElementTree as ET
        try:
            with st.spinner("참소식.com/feed.xml 데이터 불러오는 중..."):
                feed_url = "https://참소식.com/feed.xml"
                resp = requests.get(feed_url, timeout=10)
                resp.raise_for_status()
                root = ET.fromstring(resp.content)
                items = root.findall('.//item')
                if not items:
                    st.warning("RSS에서 item을 찾을 수 없습니다.")
                else:
                    item = items[0]
                    xml_title = item.findtext('title', '').strip()
                    description = item.findtext('description', '').strip()
                    link = item.findtext('link', '').strip()
                    content_for_ai = f"제목: {xml_title}\n내용: {description}"
            diagram_path = r"E:\Ai project\사이트\web\public\한국인터넷.한국\참소식.com\website_diagram.mmd"
            diagram_content = ""
            try:
                with open(diagram_path, "r", encoding="utf-8") as f:
                    diagram_content = f.read()
            except Exception as e:
                diagram_content = f"(다이어그램 파일 읽기 오류: {e})"
            with st.spinner(f"Ollama AI({selected_ollama_model})로 포스팅 내용 생성 중..."):
                ollama_prompt = (
                    "다음 뉴스 내용을 블로그 포스팅용으로 요약 및 재구성해줘.\n"
                    f"{content_for_ai}\n\n"
                    "아래는 관련 사이트의 구조/흐름도(mermaid 다이어그램)야. 이 정보도 참고해서 인사이트, 구조적 설명, 트렌드, 결론 등을 추가해줘.\n"
                    f"[Mermaid Diagram]\n{diagram_content}"
                )
                response = ollama.chat(model=selected_ollama_model, messages=[{"role": "user", "content": ollama_prompt}])
                ai_post_content = response['message']['content'] if 'message' in response and 'content' in response['message'] else "AI 생성 실패"
            import random
            from urllib.parse import quote_plus
            import re as _re
            def random_search_link(query):
                r = random.random()
                if r < 0.6:
                    url = f"https://www.google.com/search?q={quote_plus(query)}"
                    label = f'구글에서 "{query}" 검색'
                elif r < 0.8:
                    url = f"https://www.bing.com/search?q={quote_plus(query)}"
                    label = f'빙에서 "{query}" 검색'
                elif r < 0.9:
                    url = f"https://search.naver.com/search.naver?query={quote_plus(query)}"
                    label = f'네이버에서 "{query}" 검색'
                else:
                    r2 = random.random()
                    if r2 < 0.6:
                        url = f"https://www.google.com/search?q={quote_plus(query)}"
                        label = f'구글에서 "{query}" 검색'
                    elif r2 < 0.8:
                        url = f"https://www.bing.com/search?q={quote_plus(query)}"
                        label = f'빙에서 "{query}" 검색'
                    else:
                        url = f"https://search.naver.com/search.naver?query={quote_plus(query)}"
                        label = f'네이버에서 "{query}" 검색'
                return url, label
            sentences = [s.strip() for s in _re.split(r'(?<=[.!?])\s+', ai_post_content) if s.strip()]
            linked_sentences = []
            for s in sentences:
                url, label = random_search_link(s)
                linked_sentences.append(f'<a href="{url}" target="_blank">{s}</a> <span style="font-size:0.9em;color:#888;">({label})</span>')
            content_linked = '<br>'.join(linked_sentences)
            url, label = random_search_link(xml_title)
            content_linked += f'<br><br>✪ 이 주제에 대해 더 알아보기: <a href="{url}" target="_blank">{xml_title}</a> <span style="font-size:0.9em;color:#888;">({label})</span>'
            st.success("Ollama AI 포스팅 생성 완료!")
            st.text_area("📝 Ollama AI 생성 포스팅", content_linked, height=400)
            # 제목/본문 자동 입력 (입력란에 반영)
            st.session_state["auto_blog_ai_title"] = xml_title
            st.session_state["auto_blog_ai_content"] = content_linked
            # 입력란에도 즉시 반영
            st.session_state["auto_blog_title_input"] = xml_title
            st.session_state["auto_blog_content_input"] = content_linked
            st.rerun()
        except Exception as e:
            st.error(f"오류: {e}")

    # 반복 주기 선택
    interval_map = {"1분": 60, "10분": 600, "30분": 1800, "60분": 3600}
    interval_label = st.selectbox("반복 주기", list(interval_map.keys()), index=1)
    interval_sec = interval_map[interval_label]

    # 반복 상태 관리
    if "auto_posting_running" not in st.session_state:
        st.session_state.auto_posting_running = False
    if "auto_posting_last_time" not in st.session_state:
        st.session_state.auto_posting_last_time = 0

    # 기존 입력란 재사용 (카테고리 기본값: NPC)
    default_category = "NPC" if "NPC" in MENU_OPTIONS else MENU_OPTIONS[0]
    saved_menu, saved_title, saved_content, saved_images, saved_link_url, saved_img_url = load_state()
    title = st.text_input("📌 블로그 제목 (자동)", value=st.session_state.get("auto_blog_ai_title", saved_title), key="auto_blog_title_input")
    content = st.text_area("📝 본문 (자동)", value=st.session_state.get("auto_blog_ai_content", saved_content), height=500, key="auto_blog_content_input")
    images = st.file_uploader("🖼 이미지 업로드 (자동)", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="auto_images")
    exclude_images = st.checkbox("이미지 제외 (ON/OFF, 자동)", value=False, key="auto_exclude_images")
    prev_category = st.session_state.get("auto_selected_category", default_category)
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
            st.rerun()
    with col2:
        if st.button("⏹️ 자동포스팅 반복 중지", key="auto_stop_btn"):
            st.session_state.auto_posting_running = False

    # 반복 실행 로직
    if st.session_state.auto_posting_running:
        now = time.time()
        last = st.session_state.auto_posting_last_time
        if last == 0 or now - last >= interval_sec:
            # 1. 참소식 xml 기반 Ollama AI 본문/제목 생성 → 입력란에 반영
            import requests
            import ollama
            from xml.etree import ElementTree as ET
            try:
                with st.spinner("참소식.com/feed.xml 데이터 불러오는 중..."):
                    feed_url = "https://참소식.com/feed.xml"
                    resp = requests.get(feed_url, timeout=10)
                    resp.raise_for_status()
                    root = ET.fromstring(resp.content)
                    items = root.findall('.//item')
                    if not items:
                        st.warning("RSS에서 item을 찾을 수 없습니다.")
                        xml_title = title
                        description = content
                    else:
                        item = items[0]
                        xml_title = item.findtext('title', '').strip()
                        description = item.findtext('description', '').strip()
                        link = item.findtext('link', '').strip()
                    content_for_ai = f"제목: {xml_title}\n내용: {description}"
                diagram_path = r"E:\Ai project\사이트\web\public\한국인터넷.한국\참소식.com\website_diagram.mmd"
                diagram_content = ""
                try:
                    with open(diagram_path, "r", encoding="utf-8") as f:
                        diagram_content = f.read()
                except Exception as e:
                    diagram_content = f"(다이어그램 파일 읽기 오류: {e})"
                with st.spinner(f"Ollama AI({selected_ollama_model})로 포스팅 내용 생성 중..."):
                    ollama_prompt = (
                        "다음 뉴스 내용을 블로그 포스팅용으로 요약 및 재구성해줘.\n"
                        f"{content_for_ai}\n\n"
                        "아래는 관련 사이트의 구조/흐름도(mermaid 다이어그램)야. 이 정보도 참고해서 인사이트, 구조적 설명, 트렌드, 결론 등을 추가해줘.\n"
                        f"[Mermaid Diagram]\n{diagram_content}"
                    )
                    response = ollama.chat(model=selected_ollama_model, messages=[{"role": "user", "content": ollama_prompt}])
                    ai_post_content = response['message']['content'] if 'message' in response and 'content' in response['message'] else "AI 생성 실패"
                import random
                from urllib.parse import quote_plus
                import re as _re
                def random_search_link(query):
                    r = random.random()
                    if r < 0.6:
                        url = f"https://www.google.com/search?q={quote_plus(query)}"
                        label = f'구글에서 "{query}" 검색'
                    elif r < 0.8:
                        url = f"https://www.bing.com/search?q={quote_plus(query)}"
                        label = f'빙에서 "{query}" 검색'
                    elif r < 0.9:
                        url = f"https://search.naver.com/search.naver?query={quote_plus(query)}"
                        label = f'네이버에서 "{query}" 검색'
                    else:
                        r2 = random.random()
                        if r2 < 0.6:
                            url = f"https://www.google.com/search?q={quote_plus(query)}"
                            label = f'구글에서 "{query}" 검색'
                        elif r2 < 0.8:
                            url = f"https://www.bing.com/search?q={quote_plus(query)}"
                            label = f'빙에서 "{query}" 검색'
                        else:
                            url = f"https://search.naver.com/search.naver?query={quote_plus(query)}"
                            label = f'네이버에서 "{query}" 검색'
                    return url, label
                sentences = [s.strip() for s in _re.split(r'(?<=[.!?])\s+', ai_post_content) if s.strip()]
                linked_sentences = []
                for s in sentences:
                    url, label = random_search_link(s)
                    linked_sentences.append(f'<a href="{url}" target="_blank">{s}</a> <span style="font-size:0.9em;color:#888;">({label})</span>')
                content_linked = '<br>'.join(linked_sentences)
                url, label = random_search_link(xml_title)
                content_linked += f'<br><br>✪ 이 주제에 대해 더 알아보기: <a href="{url}" target="_blank">{xml_title}</a> <span style="font-size:0.9em;color:#888;">({label})</span>'
                # 제목/본문 자동 입력 (입력란에 반영)
                st.session_state["auto_blog_ai_title"] = xml_title
                st.session_state["auto_blog_ai_content"] = content_linked
                # 아래 포스팅은 xml 기반 AI 생성 결과로 진행
                post_title = xml_title
                post_content = content_linked
            except Exception as e:
                st.error(f"참소식 xml 기반 AI 생성 오류: {e}")
                post_title = title
                post_content = content
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
                    post_title,
                    post_content,
                    menu_selection,
                    post_title,
                    ca_name_value=menu_selection
                )
                if result:
                    st.success(f"✅ [{interval_label}] 네이버 블로그에 업로드 완료!")
                else:
                    st.warning(f"⚠️ [{interval_label}] 네이버 블로그 업로드 실패!")
            except Exception as e:
                st.error(f"블로그 업로드 중 오류 발생: {e}")
            save_to_blog_folder(post_title, post_content, images_pil, menu_selection)
            st.session_state.auto_posting_last_time = now
            # Trigger next cycle countdown without requiring manual interaction.
            st.rerun()
        else:
            remain = int(interval_sec - (now - last))
            st.info(f"다음 자동포스팅까지 {remain}초 남음...")
            # Keep auto-repeat alive in Streamlit's single-threaded model.
            time.sleep(1)
            st.rerun()
    else:
        st.info("자동포스팅 반복이 중지됨.")

    # 수동 즉시 실행 버튼 (자동 게시)
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
