import streamlit as st
import base64
import os
import time
import random

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import InvalidSessionIdException
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from utils.driver_manager import get_driver

# ------------------ 설정 파일 경로 ------------------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data'))
CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.txt")
BLOG_URL_FILE = os.path.join(BASE_DIR, "blog_url.txt")
driver = None  # 전역 드라이버

# ------------------ 자격 증명 저장/불러오기 ------------------
def save_credentials(user_id, password):
    encoded_pw = base64.b64encode(password.encode()).decode()
    with open(CREDENTIALS_FILE, "w") as f:
        f.write(f"{user_id}\n{encoded_pw}")

def load_credentials():
    try:
        with open(CREDENTIALS_FILE, "r") as f:
            user_id = f.readline().strip()
            encoded_pw = f.readline().strip()
            password = base64.b64decode(encoded_pw).decode()
            return user_id, password
    except:
        return "", ""

# ------------------ 블로그 주소 저장/불러오기 ------------------
def save_blog_url(url):
    with open(BLOG_URL_FILE, "w", encoding="utf-8") as f:
        f.write(url.strip())

def load_blog_url():
    if os.path.exists(BLOG_URL_FILE):
        with open(BLOG_URL_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""

def is_driver_alive():
    global driver
    try:
        return driver is not None and driver.current_url
    except:
        return False

# ------------------ 로그인 여부 확인 ------------------
def is_logged_in():
    try:
        driver = get_driver()
        return "nidlogin" not in driver.current_url
    except:
        return False

# ------------------ 타이핑 애니메이션 ------------------
def slow_typing(element, text, min_delay=0.1, max_delay=1.0):
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(min_delay, max_delay))

# ------------------ 네이버 로그인 ------------------
def naver_login():
    global driver
    driver = get_driver()
    driver.get("https://nid.naver.com/nidlogin.login")
    time.sleep(2)

    user_id, user_pw = load_credentials()
    if user_id and user_pw:
        try:
            id_input = driver.find_element(By.ID, 'id')
            pw_input = driver.find_element(By.ID, 'pw')
            slow_typing(id_input, user_id, 0.1, 0.3)
            time.sleep(0.5)
            slow_typing(pw_input, user_pw, 0.1, 0.3)

            st.warning("🤖 CAPTCHA 또는 인증이 필요한 경우, 브라우저에서 직접 입력해 주세요.")
            st.info("입력이 완료되면 [다음 단계로] 버튼을 눌러주세요.")
            driver.find_element(By.CLASS_NAME, 'btn_login').click()
        except Exception as e:
            st.error(f"[자동 로그인 실패] {e}")


# ------------------ 블로그 주소로 이동 ------------------
def after_login_action():
    if not is_driver_alive():
        return "❌ 브라우저 세션이 종료되었습니다."

    driver = get_driver()
    try:
        blog_url = load_blog_url()
        if not blog_url:
            return "⚠️ 저장된 블로그 주소가 없습니다."

        driver.get(blog_url)
        time.sleep(2)
        return "✅ 블로그 주소로 이동 완료!"
    except Exception as e:
        st.error(f"❌ 이동 중 오류 발생: {e}")
        return f"❌ 오류: {e}"

# ------------------ 글쓰기 페이지 이동 ------------------
def go_to_write_page():
    if not is_driver_alive():
        return "❌ 브라우저 세션이 종료되었습니다."

    driver = get_driver()
    try:
        driver.get("https://blog.naver.com/PostWriteForm.naver")
        time.sleep(2)
        return "✅ 글쓰기 페이지로 이동했습니다."
    except Exception as e:
        st.error(f"❌ 이동 중 오류 발생: {e}")
        return f"❌ 오류: {e}"

