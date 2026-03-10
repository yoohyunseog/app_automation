import time
import urllib.parse
import pygetwindow as gw
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.driver_manager import get_driver

def launch_nb_scout(keyword: str):
    # get_driver를 사용하여 드라이버 인스턴스를 가져옵니다.
    driver = get_driver(headless=False)  # WebDriver 인스턴스를 가져옴
    wait = WebDriverWait(driver, 5)  # WebDriverWait 객체 생성
    actions = ActionChains(driver)  # ActionChains 객체 생성
    
    encoded_keyword = urllib.parse.quote(keyword)
    url = f"https://blackkiwi.net/service/keyword-analysis?keyword={encoded_keyword}&platform=naver"

    try:
        driver.get(url)  # get_driver로 받은 드라이버로 URL 로드

        # 페이지가 로드될 때까지 대기 (WebDriverWait 사용)
        wait.until(EC.presence_of_element_located((By.XPATH, "//body")))  # 예시: <body> 태그가 로드될 때까지 대기

        # ✅ 브라우저 창을 화면 앞으로 가져오기 (최소화 복원 + 포커스만)
        time.sleep(1)
        for window in gw.getAllWindows():
            if "Chrome" in window.title:
                if window.isMinimized:
                    window.restore()
                window.activate()  # 포커스만 줌 (maximize 제거)
                break
    except Exception as e:
        print(f"[NB-Scout 오류] 브라우저 열기 실패: {e}")

    return driver

def open_trend_page():
    driver = get_driver(headless=False)  # 브라우저 창을 띄운 상태로 실행
    url = "https://blackkiwi.net/service/trend"

    try:
        driver.get(url)

        # 페이지가 로드될 때까지 대기 (WebDriverWait 사용)
        wait = WebDriverWait(driver, 5)
        wait.until(EC.presence_of_element_located((By.XPATH, "//body")))  # 예시: <body> 태그가 로드될 때까지 대기

        # ✅ 브라우저 창을 화면 앞으로 가져오기 (최소화 복원 + 포커스만)
        time.sleep(1)
        for window in gw.getAllWindows():
            if "Chrome" in window.title:
                if window.isMinimized:
                    window.restore()
                window.activate()  # 포커스만 줌 (maximize 제거)
                break
    except Exception as e:
        print(f"[Trend 페이지 오류] 브라우저 열기 실패: {e}")

    return driver
