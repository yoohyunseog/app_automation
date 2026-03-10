import streamlit as st
from PIL import Image
import os
import json
import pytesseract
import uuid
import time
import re
from datetime import datetime
import pytz

from core.boost.blog_poster import post_to_blog
from core.collect.generate_filepath import collect_trending_articles_as_text
from components.prompt_generator.subject_trigger import open_and_click_subject_button, open_blog_trend_url, open_blog_Courses_url
from components.prompt_generator.image_prompt_scraper import open_codepen_page
from components.prompt_generator.content_prompt_scraper import open_codepen_Courses_page
from components.prompt_generator.content_prompt_format import openPromptGeneratorPage

# Tesseract 실행 경로
pytesseract.pytesseract.tesseract_cmd = r"E:\Tesseract-OCR\tesseract.exe"

# 자동 저장 디렉토리
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../nb_wfa/"))  # nb_wfa 루트
SAVE_DIR = os.path.join(ROOT_DIR, "data", "autosave")
MAX_IMAGES = 5
os.makedirs(SAVE_DIR, exist_ok=True)

# 카테고리 목록
MENU_OPTIONS = [
    "스탑 매치", "NPC", "America First", "EU", "스탑 매치 - 천공의 요새",
    "K MUSIC N/B AI", "비공개방", "드라마", "괴물딴지.com", "하늘궁.com",
    "2024 미국대선", "추천비디오.com", "참소식.com", "포켓몬빵.com",
    "애니메.com", "게임순위.com", "늘봄.com", "8비트.com", "증권"
]

# 🎯 과목 → 도메인-분기유형 매핑
# 🎯 과목 → 정보 묶음 구조 (도메인 + 분기)
SUBJECT_GROUP = {
    "📘 국어": {"domain": "참소식.com", "mode": "discover"},
    "📗 수학": {"domain": "참소식.com", "mode": "discover"},
    "📙 영어": {"domain": "참소식.com", "mode": "discover"},
    "🔬 과학": {"domain": "참소식.com", "mode": "discover"},
    "🎬 드라마": {"domain": "드라마", "mode": "trend"},
    "🎞️ 영화": {"domain": "하늘궁.com", "mode": "trend"},
    "📚 만화·애니": {"domain": "애니메.com", "mode": "trend"},
    "🎮 게임": {"domain": "게임순위.com", "mode": "trend"},
    "🍜 맛집": {"domain": "포켓몬빵.com", "mode": "trend"},
    "🧒 0-12세": {"domain": "참소식.com", "mode": "Courses"},
    "👧 13-18세": {"domain": "참소식.com", "mode": "Courses"},
    "📈 트렌드": {"domain": "trend.com", "mode": "trend"}
}  

# 이미지 흑백 전처리
def preprocess_image(image):
    return image.convert("L")

# 자동 저장용 임시 상태 저장
def save_state(menu, title, content, images, link_url="", img_url=""):
    json_path = os.path.join(SAVE_DIR, "autosave.json")
    data = {}

    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

    data.update({
        "menu": menu,
        "title": title,
        "content": content,
        "link_url": link_url,
        "img_url": img_url
    })

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

    if images:
        try:
            img_path = os.path.join(SAVE_DIR, "autosave_img.png")
            img = images[0]
            if not isinstance(img, Image.Image):
                img = Image.open(img).copy()
            img.save(img_path)
        except Exception as e:
            print(f"❌ 이미지 저장 실패: {e}")

    # 🚀 금지어 불러오기
    # banned_words_path는 상단 전역
    banned_words_path = os.path.join(SAVE_DIR, "banned_words.json")

# 🚀 금지어 불러오기 함수
def load_banned_words(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

# 💾 금지어 저장 함수
def save_banned_words(words, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False)

# 임시 상태 불러오기
def load_state():
    title, content, menu, images = "", "", MENU_OPTIONS[0], []
    link_url, img_url = "", ""
    json_path = os.path.join(SAVE_DIR, "autosave.json")

    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            title = data.get("title", "")
            content = data.get("content", "")
            menu = data.get("menu", MENU_OPTIONS[0])
            link_url = data.get("link_url", "")
            img_url = data.get("img_url", "")

    img_path = os.path.join(SAVE_DIR, "autosave_img.png")
    if os.path.exists(img_path):
        images.append(Image.open(img_path))

    return menu, title, content, images, link_url, img_url

# 게시 시 로컬 블로그 폴더 저장
def save_to_blog_folder(title, content, images_pil, category):
    base_path = r"E:\Filemora\blog"
    category_path = os.path.join(base_path, category)

    # ⏰ 타임스탬프 (HHMMSS 기준)
    timestamp = datetime.now().strftime("%H%M%S")

    # 📁 폴더 생성
    image_dir = os.path.join(category_path, "images")
    content_dir = os.path.join(category_path, "contents")
    os.makedirs(image_dir, exist_ok=True)
    os.makedirs(content_dir, exist_ok=True)

    # 📝 제목 & 본문 저장
    with open(os.path.join(content_dir, f"{timestamp}_title.txt"), "w", encoding="utf-8") as f:
        f.write(title)
    with open(os.path.join(content_dir, f"{timestamp}_content.txt"), "w", encoding="utf-8") as f:
        f.write(content)

    # 🖼 이미지 저장
    for idx, img in enumerate(images_pil):
        img.save(os.path.join(image_dir, f"{timestamp}_img_{idx+1}.png"))

    print(f"✅ 저장 완료: {category_path}")

def save_link_inputs(link_url, img_url):
    save_path = os.path.join(SAVE_DIR, "autosave.json")
    if os.path.exists(save_path):
        with open(save_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}
    data["link_url"] = link_url
    data["img_url"] = img_url
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

# Streamlit UI
def render_write_ui(set_bottom_message):
    st.title("📝 블로그 수동 + 자동 작성 도우미")

    # 🔒 금지어 필터링 입력란
    st.markdown("### 🔒 금지어 필터링")
    banned_words_path = os.path.join(SAVE_DIR, "banned_words.json")

    # 금지어 세션 초기화
    if "banned_words" not in st.session_state:
        st.session_state.banned_words = load_banned_words(banned_words_path)

    # 저장
    # 금지어 입력 받기
    banned_words_input = st.text_input(
        "쉼표(,)로 구분된 금지어 목록을 입력하세요",
        value=", ".join(st.session_state.banned_words),
        placeholder="예: 욕설1, 욕설2, 불건전단어"
    )

    # 입력 → 리스트로 변환
    new_banned_words = [word.strip() for word in banned_words_input.split(",") if word.strip()]

    # 이전과 다르면 저장
    if new_banned_words != st.session_state.banned_words:
        st.session_state.banned_words = new_banned_words
        save_banned_words(new_banned_words, banned_words_path)  # ✅ 이 위치여야 함
        st.info("💾 금지어 목록이 자동 저장되었습니다.")

    # 🎯 과목 버튼 (UI 내 상단에 배치)
    st.markdown("### 🎯 과목 바로가기")

    banned_words = st.session_state.get("banned_words", [])
    BUTTONS_PER_ROW = 4
    subject_items = list(SUBJECT_GROUP.items())

    for row_start in range(0, len(subject_items), BUTTONS_PER_ROW):
        row_items = subject_items[row_start:row_start + BUTTONS_PER_ROW]
        cols = st.columns(len(row_items))

        for col, (subject, info) in zip(cols, row_items):
            with col:
                if st.button(f"{subject}"):
                    subject_name = subject.split()[-1]
                    domain = info["domain"]
                    mode = info["mode"]

                    st.session_state["selected_menu"] = {
                        "subject": subject_name,
                        "domain": domain,
                        "mode": mode
                    }

                    # 분기 처리
                    if mode == "discover":
                        open_and_click_subject_button(subject_name, banned_words)
                    elif mode == "trend":
                        open_blog_trend_url(subject_name, banned_words)
                    elif mode == "Courses":
                        open_blog_Courses_url(subject_name, banned_words)
                    else:
                        st.warning(f"⚠️ '{subject_name}'의 모드 '{mode}'는 알 수 없습니다.")

                    st.success(f"✅ '{subject}' 실행됨")



    # Ollama AI + 참소식.com/feed.xml 자동 포스팅 기능 (항상 노출)

    st.markdown("---")
    st.subheader("🤖 Ollama AI 기반 자동 포스팅")
    # Ollama 모델 선택 드롭다운
    # Ollama 설치 모델 전체 선택 가능하게 확장
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
    selected_ollama_model = st.selectbox(
        "Ollama AI 모델 선택 (직접 입력 가능)",
        ollama_models,
        key="ollama_model_select"
    )
    # 직접 입력 기능 추가
    custom_model = st.text_input("직접 입력 (선택사항)", value="", key="ollama_custom_model")
    if custom_model.strip():
        selected_ollama_model = custom_model.strip()
    if st.button("🌐 Ollama AI로 참소식.com/feed.xml 자동 포스팅"):
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
                    return
                # 최신 기사 1개만 예시로 사용
                item = items[0]
                title = item.findtext('title', '').strip()
                description = item.findtext('description', '').strip()
                link = item.findtext('link', '').strip()
                content_for_ai = f"제목: {title}\n내용: {description}"

            # Mermaid 다이어그램 파일 읽기
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

            # 본문 내 주요 키워드(제목 단어)마다 네이버 검색 링크 삽입

            # 제목 전체 문장으로 네이버 검색 링크 생성
            import random
            from urllib.parse import quote_plus

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
                    # 나머지 10%는 구글/빙/네이버 중 하나로 랜덤
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


            # 문장 단위로 분리 후 각 문장에 랜덤 검색 링크 삽입 (문장 자체에 링크)
            import re as _re
            sentences = [s.strip() for s in _re.split(r'(?<=[.!?])\s+', ai_post_content) if s.strip()]
            linked_sentences = []
            for s in sentences:
                url, label = random_search_link(s)
                # 문장 자체에 링크, 괄호 안에 검색엔진명
                linked_sentences.append(f'<a href="{url}" target="_blank">{s}</a> <span style="font-size:0.9em;color:#888;">({label})</span>')
            content_linked = '<br>'.join(linked_sentences)

            # 마지막 안내문도 동일하게 적용
            url, label = random_search_link(title)
            content_linked += f'<br><br>✪ 이 주제에 대해 더 알아보기: <a href="{url}" target="_blank">{title}</a> <span style="font-size:0.9em;color:#888;">({label})</span>'

            st.success("Ollama AI 포스팅 생성 완료!")
            st.text_area("📝 Ollama AI 생성 포스팅", content_linked, height=400)

            # 제목/본문 자동 입력
            # 블로그 제목/본문 입력란에 바로 반영 (rerun 없이 값만 업데이트)
            st.session_state["blog_ai_title"] = title
            st.session_state["blog_ai_content"] = content_linked
            st.session_state["input_keyword"] = title
            st.session_state["link_url_input"] = link
        except Exception as e:
            st.error(f"오류: {e}")

    # Ollama AI 결과를 블로그 입력란에 반영하는 버튼
    if "blog_ai_title" in st.session_state and "blog_ai_content" in st.session_state:
        if st.button("⬇️ Ollama 결과를 블로그 입력란에 반영"):
            st.session_state["input_keyword"] = st.session_state["blog_ai_title"]
            st.session_state["blog_ai_content"] = st.session_state["blog_ai_content"]
            st.success("Ollama AI 결과가 블로그 입력란에 반영되었습니다.")


    # ⬇️ 이 부분은 항상 먼저 선언되어야 합니다!
    saved_menu, saved_title, saved_content, saved_images, saved_link_url, saved_img_url = load_state()
    selected_menu = st.session_state.get("selected_menu", saved_menu)  # ✅ 여기서 selected_menu 초기화

    def auto_save_links():
        save_link_inputs(
            st.session_state.link_url_input,
            st.session_state.img_url_input
        )

    st.text_input("🔗 링크 주소 입력", key="link_url_input", value=saved_link_url, on_change=auto_save_links)
    st.text_input("🖼 이미지 주소 입력", key="img_url_input", value=saved_img_url, on_change=auto_save_links)

    # 세션 상태에서 domain 값만 꺼내기
    selected_menu_domain = st.session_state.get("selected_menu", {}).get("domain", "")

    menu_selection = st.selectbox(
        "📁 카테고리 선택",
        MENU_OPTIONS,  # 예: ["참소식.com", "포켓몬빵.com", "애니메.com", ...]
        index=MENU_OPTIONS.index(selected_menu_domain) if selected_menu_domain in MENU_OPTIONS else 0
    )


    # 🖼 기능별 버튼 한 줄 구성
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🖼 문단 프롬프트 생성", kwargs={"width": "stretch"}):
            open_codepen_Courses_page()

    with col2:
        if st.button("🖼 이미지 프롬프트 생성", kwargs={"width": "stretch"}):
            prompt = open_codepen_page()

    with col3:
        if st.button("🖼 문단 포멧 생성", kwargs={"width": "stretch"}):
            openPromptGeneratorPage()

    # Ollama 결과가 있으면 입력란에 자동 반영
    # Ollama 결과가 있으면 입력란에 강제 반영 (session_state 직접 업데이트)
    if "blog_ai_title" in st.session_state:
        st.session_state["blog_title_input"] = st.session_state["blog_ai_title"]
    if "blog_ai_content" in st.session_state:
        st.session_state["blog_content_input"] = st.session_state["blog_ai_content"]
    title = st.text_input("📌 블로그 제목", value=st.session_state.get("blog_title_input", saved_title), key="blog_title_input")
    content = st.text_area("📝 본문", value=st.session_state.get("blog_content_input", saved_content), height=500, key="blog_content_input")
    # 이미지 업로드 및 이미지 제외 on/off 스위치 추가
    images = st.file_uploader("🖼 이미지 업로드", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
    exclude_images = st.checkbox("이미지 제외 (ON/OFF)", value=False, help="체크 시 이미지가 블로그에 포함되지 않습니다.")

    # 세션 상태 초기화
    if "last_save_time" not in st.session_state:
        st.session_state.last_save_time = 0
    if "last_content" not in st.session_state:
        st.session_state.last_content = ""


    # 현재 시각
    current_time = time.time()
    kst = pytz.timezone("Asia/Seoul")
    kst_time = datetime.fromtimestamp(current_time, tz=pytz.UTC).astimezone(kst)
    formatted_time = kst_time.strftime("%Y-%m-%d %H:%M:%S")

    # 세션에 이전 이미지 상태 저장용
    if "last_images_count" not in st.session_state:
        st.session_state.last_images_count = 0

    images_changed = images and (len(images) != st.session_state.last_images_count)

    if (title.strip() or content.strip() or images_changed) and (
        content != st.session_state.last_content or images_changed
    ) and (current_time - st.session_state.last_save_time >= 10):

        images_pil = [Image.open(img).copy() for img in images] if images else saved_images
        inserted_text_flag = False

        if re.search(r"이미지\s*복사", content) is None:
            replacements = ["📌 이미지를 클릭하면", "🖼️ 이미지를 클릭하면", "❋ 이미지를 클릭하면", "이미지를 클릭하면"]
            for marker in replacements:
                content = content.replace(marker, f"이미지 복사{marker}")
            st.session_state.content = content
            inserted_text_flag = True

        save_state(
            menu_selection,
            title,
            content,
            images_pil,
            st.session_state.get("link_url_input", ""),
            st.session_state.get("img_url_input", "")
        )

        st.session_state.last_save_time = current_time
        st.session_state.last_content = content
        st.session_state.last_images_count = len(images) if images else 0

        if inserted_text_flag:
            st.warning("자동 저장! '이미지 복사📌' 문구가 본문에 자동 추가되었습니다.")
        else:
            st.info(f"✅ 자동 저장 완료! ({formatted_time} KST)")

    if st.button("✅ 게시 준비 완료", kwargs={"width": "stretch"}):
        if not title or not content:
            st.warning("제목과 본문을 모두 입력하세요.")
        else:
            st.success(f"✅ '{menu_selection}' 카테고리로 준비 완료!")
            st.write(content)
            if images:
                for img in images:
                    st.image(img, caption=img.name)

    if st.button("🚀 블로그에 자동 게시", kwargs={"width": "stretch"}):
        if not title or not content:
            st.warning("내용이 없습니다!")
        else:
            # 이미지 제외 옵션 적용
            images_pil = [] if exclude_images else ([Image.open(img) for img in images] if images else saved_images)

            # writers/naver_uploader.py의 upload_to_naver_blog 사용
            try:
                from writers.naver_uploader import upload_to_naver_blog
                # config 예시: 실제 환경에 맞게 수정 가능
                config = {
                    "naver_enabled": True,
                    "image_source": "none" if exclude_images else "bing",  # 이미지 소스 제어
                    "check_naver_login": True,
                }
                # 카테고리명은 menu_selection, 키워드는 제목 사용(예시)
                result = upload_to_naver_blog(
                    config,
                    title,
                    content,
                    menu_selection,
                    title,  # 키워드 예시: 제목 사용
                    ca_name_value=menu_selection
                )
                if result:
                    st.success("✅ 네이버 블로그에 업로드 완료!")
                else:
                    st.warning("⚠️ 네이버 블로그 업로드 실패!")
            except Exception as e:
                st.error(f"블로그 업로드 중 오류 발생: {e}")

            # 로컬 저장도 이미지 제외 옵션 반영
            save_to_blog_folder(title, content, images_pil, menu_selection)

    # 이미지 소스 결정
    current_images = [Image.open(img) for img in images] if images else saved_images

    # OCR 인터페이스
    st.markdown("---")
    st.markdown("## 🧠 OCR: 이미지 내 텍스트 추출")

    if current_images:
        for idx, img in enumerate(current_images):
            st.image(img, caption=f"🖼 이미지 {idx+1}", width='stretch')
            unique_key = f"ocr_{idx}_{uuid.uuid4()}"
            if st.button(f"🔍 텍스트 추출 - 이미지 {idx+1}", key=unique_key):
                processed_img = preprocess_image(img)
                extracted_text = pytesseract.image_to_string(processed_img, lang='kor')
                st.text_area("📝 추출된 텍스트", value=extracted_text, height=200, key=f"ocr_output_{idx}")
