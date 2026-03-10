import sys, os, time, pyperclip
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.driver_manager import get_driver, force_kill_all_chrome_drivers

def openPromptGeneratorPage():

    # 드라이버 실행 및 페이지 열기
    driver = get_driver(headless=False)
    url = "file:///E:/Ai%20project/nb_wfa/naver_influencer_crawler/v-0-2/dist/index.html"
    driver.get(url)
    print(f"✅ CodePen 페이지 열림: {url}")
    
    # 페이지 로딩 대기
    time.sleep(3)
    
    # textarea1에 Ctrl+V
    textarea1 = driver.find_element(By.ID, "exampleFormControlTextarea1")
    textarea1.click()
    textarea1.send_keys(Keys.CONTROL, 'v')

    time.sleep(1)

    # textarea3에 텍스트 입력 후 Ctrl+C
    textarea3 = driver.find_element(By.ID, "exampleFormControlTextarea3")
    textarea3.send_keys("복사할 내용")
    textarea3.click()
    textarea3.send_keys(Keys.CONTROL, 'a')
    textarea3.send_keys(Keys.CONTROL, 'c')

    # 클립보드에서 복사된 텍스트 확인
    copied = pyperclip.paste()
    print("📋 클립보드에 복사된 내용:", copied)