import sys, os
import pyperclip
import time
import pygetwindow as gw
import pyautogui

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.driver_manager import get_driver, force_kill_all_chrome_drivers
from ui.components.prompt_generator.content_prompt_scraper import open_codepen_page, open_codepen_Courses_page
from urllib.parse import urlparse
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

# 📂 기본 경로 설정
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../data'))
CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.txt")
BLOG_URL_FILE = os.path.join(BASE_DIR, "blog_url.txt")

def log_action(message):
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)

    with open("../data/selenium_chrome_action_log.txt", 'a', encoding='utf-8') as f:
        f.write(log_entry + "\n")

def get_chrome_offset():
    for w in gw.getWindowsWithTitle("Chrome"):
        if not w.isMinimized:
            try:
                w.restore()
                time.sleep(0.3)
                w.activate()
                log_action("✅ 크롬 창 activate 성공")
            except Exception as e:
                log_action(f"⚠️ activate 실패: {e}")
                pyautogui.click(150, 105)  # 수동 포커스 보정
                log_action("🖱️ 크롬 제목바 클릭으로 포커스 시도")
            
            # 위치와 크기 반환
            return w.left, w.top, w.width, w.height

    return None  # 크롬 창이 없거나 실패한 경우

def get_subject_position(driver, subject):
    log_action(f"🔍 subject 위치 탐색 시작: '{subject}'")
    try:
        wait = WebDriverWait(driver, 10)
        trend_titles = wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "h3.u_ni_trend_title")
        ))

        log_action(f"✅ '.u_ni_trend_title' 요소 수: {len(trend_titles)}")

        for idx, title in enumerate(trend_titles, start=1):
            text = title.text.strip()
            loc = title.location
            size = title.size
            log_action(f"[{idx}] '{text}' - 위치({loc['x']},{loc['y']}), 크기({size['width']}x{size['height']})")

            if text == subject:
                center_x = int(loc["x"] + size["width"] / 2)
                center_y = int(loc["y"] + size["height"] / 2)
                log_action(f"✅ subject 일치: '{subject}' → 중심 좌표: ({center_x}, {center_y})")
                return center_x, center_y

        log_action(f"❌ subject '{subject}'를 찾을 수 없음")
        return None

    except Exception as e:
        log_action(f"❌ subject 위치 탐색 오류: {e}")
        return None

def simulate_swiper_drag(start_x=1000, start_y=500, distance=400, extra_offset=100):
    """화면 swiper를 좌측으로 길게 드래그"""
    end_x = start_x - distance - extra_offset
    pyautogui.moveTo(start_x, start_y, duration=0.2)
    pyautogui.mouseDown()
    pyautogui.moveTo(end_x, start_y, duration=0.4)
    pyautogui.mouseUp()
    log_action(f"🖱️ 드래그 시도: ({start_x}→{end_x}, {start_y})")

def drag_subject_to_left(driver, subject, drag_distance=300, max_attempts=8):
    log_action(f"🚀 드래그 시작: subject='{subject}'")

    left, top, width, height = get_chrome_offset()
    start_x = left + int(width * 0.75)
    start_y = top + int(height * 0.5)

    wait = WebDriverWait(driver, 10)
    button = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[contains(text(), '설정순 보기') and contains(@class, 'u_ni_tab_btn')]")
    ))
    button.click()
    time.sleep(5)

    # subject 위치 확인
    attempt = 0
    pos = get_subject_position(driver, subject)

    while (not pos or pos[0] > 3000) and attempt < max_attempts:
        log_action(f"🔄 드래그 재시도 {attempt + 1}/{max_attempts} - 현재 좌표: {pos}")
        simulate_swiper_drag(start_x=start_x, start_y=start_y, distance=600, extra_offset=200)
        time.sleep(1.2)
        pos = get_subject_position(driver, subject)
        attempt += 1

    if not pos:
        log_action(f"❌ 드래그 실패 - subject '{subject}'의 위치를 찾을 수 없음")
        return

    if pos[0] > 3000:
        log_action(f"❌ subject '{subject}'는 너무 오른쪽에 위치함 ({pos[0]}px)")
        return

    abs_x = pos[0] + 100
    abs_y = pos[1] + 100

    log_action(f"📍 subject 위치 확인됨: ({abs_x}, {abs_y})")

    try:
        # subject가 이미 보이는 위치라면 드래그 생략
        if pos[0] > drag_distance:
            log_action(f"🖱️ 드래그 실행: {pos[0]} → {pos[0] - drag_distance}px")
            simulate_swiper_drag(start_x=abs_x, start_y=abs_y, distance=drag_distance, extra_offset=150)
            time.sleep(1.2)
        
        # subject 기준 키워드 추출
        extract_trend_keywords_under_subject(driver, subject=subject)
        log_action("✅ 키워드 추출 완료")
    except Exception as e:
        log_action(f"❌ 오류 발생: {e}")


def extract_naver_blog_id(blog_url):
    try:
        parsed_url = urlparse(blog_url)
        path = parsed_url.path.strip("/")
        if parsed_url.netloc.endswith("naver.com") and path:
            return path
        else:
            raise ValueError("네이버 블로그 주소 형식이 아닙니다.")
    except Exception as e:
        print(f"⚠️ 블로그 ID 추출 실패: {e}")
        return None

def extract_trend_keywords_under_subject(driver, subject="만화·애니"):
    try:
        wait = WebDriverWait(driver, 1)

        # 1️⃣ 제목 요소 찾기
        title_element = wait.until(EC.presence_of_element_located(
            (By.XPATH, f"//h3[@class='u_ni_trend_title' and normalize-space(text())='{subject}']")
        ))
        log_action(f"🔍 '{subject}' 제목 요소 찾기 성공")

        # 2️⃣ 해당 subject 아래의 트렌드 키워드(span) 추출
        trend_items = title_element.find_elements(
            By.XPATH, "../ul//span[@class='u_ni_trend_text']"
        )

        if not trend_items:
            log_action(f"⚠️ '{subject}' 아래 트렌드 항목이 없습니다.")
            return

        # 3️⃣ 추출 및 로그 출력
        keywords = [item.text.strip() for item in trend_items if item.text.strip()]
        for idx, keyword in enumerate(keywords, 1):
            log_action(f"{idx}. {keyword}")

        # 4️⃣ 클립보드 복사
        joined = "\n".join(keywords)
        pyperclip.copy(joined)
        log_action("📎 클립보드 복사 완료!")

        # 프롬프트 생성기 실행
        open_codepen_page()
        
    except Exception as e:
        log_action(f"❌ 트렌드 키워드 추출 오류: {e}")

def select_age_dropdown(driver, age_label="13-18세"):
    try:
        wait = WebDriverWait(driver, 5)

        # 1. 드롭다운 열기 (연령 선택 박스 클릭)
        dropdown_box = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='선택 보기']")))
        dropdown_box.click()    

        # 2. 드롭다운 항목 중 일치 텍스트 찾기
        options = wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "ul.u_ni_select_list li.u_ni_select_item div.u_ni_select_link")
        ))

        found = False
        for opt in options:
            if opt.text.strip() == age_label:
                opt.click()
                print(f"✅ 연령 선택 완료: '{age_label}'")
                found = True
                break

        if not found:
            print(f"❌ '{age_label}' 항목을 찾을 수 없습니다.")

        trend_elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span.u_ni_trend_text")))

        # 텍스트 추출 및 출력
        keywords = [elem.text.strip() for elem in trend_elements if elem.text.strip()]
        for idx, keyword in enumerate(keywords, 1):
            print(f"{idx}. {keyword}")

        # 클립보드에 복사
        pyperclip.copy("\n".join(keywords))
        print("📎 클립보드에 복사 완료! (Ctrl + V로 붙여넣기 가능)")

        # 프롬프트 생성기 실행
        open_codepen_Courses_page()

    except Exception as e:
        print(f"❌ 연령 선택 중 오류 발생: {e}")


def open_blog_Courses_url(subject, banned_words=None):
    """blog_url.txt에 저장된 블로그 주소를 브라우저로 엽니다."""
    try:
        with open(BLOG_URL_FILE, "r", encoding="utf-8") as f:
            blog_url = f.read().strip()
            if not blog_url.startswith("http"):
                raise ValueError("유효한 URL이 아닙니다.")
    except Exception as e:
        print(f"📛 블로그 주소 불러오기 실패: {e}")
        return

    driver = get_driver(headless=False)

    blog_id = extract_naver_blog_id(blog_url)
    if blog_id:
        print(f"🧾 블로그 ID: {blog_id}")

        url = f"https://creator-advisor.naver.com/naver_blog/{blog_id}/trends#trend-by-categories"
        driver.get(url)
        time.sleep(1)

        select_age_dropdown(driver, subject)

    try:
        wait = WebDriverWait(driver, 5)
        print(f"✅ 블로그 열기 성공: {blog_url}")
    except Exception as e:
        print(f"⚠️ 블로그 열기 실패: {e}")

def open_blog_trend_url(subject, banned_words=None):
    """blog_url.txt에 저장된 블로그 주소를 브라우저로 엽니다."""
    try:
        with open(BLOG_URL_FILE, "r", encoding="utf-8") as f:
            blog_url = f.read().strip()
            if not blog_url.startswith("http"):
                raise ValueError("유효한 URL이 아닙니다.")
    except Exception as e:
        print(f"📛 블로그 주소 불러오기 실패: {e}")
        return

    driver = get_driver(headless=False)

    blog_id = extract_naver_blog_id(blog_url)
    if blog_id:
        print(f"🧾 블로그 ID: {blog_id}")

        url = f"https://creator-advisor.naver.com/naver_blog/{blog_id}/trends#trend-by-categories"
        driver.get(url)
        time.sleep(1)

        drag_subject_to_left(driver, subject, drag_distance=400)

    try:
        wait = WebDriverWait(driver, 5)
        print(f"✅ 블로그 열기 성공: {blog_url}")
    except Exception as e:
        print(f"⚠️ 블로그 열기 실패: {e}")

def open_and_click_subject_button(subject, banned_words=None):
    banned_words = banned_words or []

    url = "https://in.naver.com/discover/170711606808352"
    driver = get_driver(headless=False)
    driver.get(url)

    wait = WebDriverWait(driver, 10)

    try:
        # 버튼 클릭
        xpath = f"//button[contains(text(), '{subject}') and contains(@class, 'CollectionFilter__button_category')]"
        subject_button = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        subject_button.click()
        print(f"✅ '{subject}' 버튼 클릭 완료")

        # 콘텐츠 로드 대기
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "CollectionSpecialtyCard__title_content___hxoT5")))

        # 카드 추출
        cards = driver.find_elements(By.CSS_SELECTOR, "a.CollectionSpecialtyCard__link_content___kn2Mk")
        results = []

        print(f"\n📋 '{subject}' 콘텐츠 목록:\n")

        for idx, card in enumerate(cards, start=1):
            try:
                title = card.find_element(By.CLASS_NAME, "CollectionSpecialtyCard__title_content___hxoT5").text.strip()

                # ⛔ 금지어 또는 길이 필터링
                if len(title) < 5:
                    print(f"{idx}. ⛔ 제목이 너무 짧아 제외됨: '{title}'")
                    continue

                if any(banned_word in title for banned_word in banned_words):
                    print(f"{idx}. ⛔ 금지어 포함 제외: '{title}'")
                    continue

                href = card.get_attribute("href")
                result = f"{idx}. {title}\n"
                print(result + "\n")
                results.append(result)
            except Exception as e:
                print(f"{idx}. 제목 또는 링크 추출 실패: {e}")

        # 클립보드 복사
        final_clip = "\n\n".join(results)
        pyperclip.copy(final_clip)
        print("📎 클립보드에 복사 완료! (Ctrl + V로 붙여넣기 가능)")

        # 프롬프트 생성기 실행
        open_codepen_page()

    except Exception as e:
        print(f"❌ '{subject}' 버튼 클릭 실패 또는 콘텐츠 로드 실패: {e}")

    return driver
