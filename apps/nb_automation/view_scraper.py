from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time
import os
import pandas as pd
from datetime import datetime  # ✅ 여기 추가!
from utils.driver_manager import get_driver

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import traceback

# 한글 폰트 설정 (윈도우 기준)
plt.rcParams['font.family'] = 'Malgun Gothic'  # 또는 'NanumGothic', 'AppleGothic' (macOS)
plt.rcParams['axes.unicode_minus'] = False  # 마이너스 깨짐 방지


# 블로그 주소 불러오기
BLOG_URL_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../data/blog_url.txt'))
SAVE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../data/blog_views'))
LOG_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../data/selenium_chrome_action_log.txt'))

def log_action(message):
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)

    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_entry + "\n")
    except Exception as e:
        print(f"[ERROR] 로그 파일 저장 실패: {e}")

def load_blog_url():
    if os.path.exists(BLOG_URL_FILE):
        with open(BLOG_URL_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""

def save_blog_views_by_date(data: list):
    os.makedirs(SAVE_DIR, exist_ok=True)

    for entry in data:
        # 날짜 포맷 정리
        date_str = entry["date"].split("(")[0].strip()  # '2025.05.04.'
        date_formatted = pd.to_datetime(date_str, format="%Y.%m.%d.").strftime("%Y-%m-%d")

        # 저장 파일 경로
        file_path = os.path.join(SAVE_DIR, f"{date_formatted}.csv")

        new_row = {"date": date_formatted, "views": int(entry["views"])}
        df_new = pd.DataFrame([new_row])

        # 중복 확인
        if os.path.exists(file_path):
            df_existing = pd.read_csv(file_path)
            if df_existing.equals(df_new):
                print(f"🔁 {date_formatted} 이미 저장된 데이터와 동일하여 건너뜀")
                continue

        # 저장
        df_new.to_csv(file_path, index=False, encoding="utf-8-sig")
        print(f"✅ {date_formatted} 저장 완료")

import time
from datetime import datetime
from selenium.webdriver.common.by import By

def scrape_views(category_name="기본"):
    log_action(f"🚀 블로그 자동 포스팅 시작 (카테고리: {category_name})")

    global driver
    try:
        driver = get_driver()
        log_action("✅ Selenium 드라이버 로드 완료")
    except Exception as e:
        log_action(f"❌ 드라이버 초기화 실패: {e}")
        return

    blog_url = load_blog_url()
    if not blog_url:
        log_action("❌ 블로그 주소가 설정되지 않았습니다.")
        return

    blog_id = blog_url.split("/")[-1]
    visit_url = f"https://admin.blog.naver.com/{blog_id}/stat/visit_pv"
    log_action(f"🌐 방문자 통계 페이지 접속: {visit_url}")
    driver.get(visit_url)
    time.sleep(2)

    try:
        iframe = driver.find_element(By.ID, "statmain")
        driver.switch_to.frame(iframe)
        log_action("🔍 iframe(statmain) 진입 성공")
    except Exception as e:
        log_action(f"❌ iframe 진입 실패: {e}")
        return

    # 방문자 통계 테이블 수집
    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    data = []
    log_action(f"📊 테이블 행 수집 시작 (총 {len(rows)}행)")

    for row in rows:
        try:
            th_elements = row.find_elements(By.CSS_SELECTOR, "th")
            td_elements = row.find_elements(By.CSS_SELECTOR, "td.u_ni_bgcolor_4__2psUU")

            if not th_elements or not td_elements:
                log_action("⚠️ 해당 행에 유효한 th 또는 조회수(td) 요소 없음, 스킵됨")
                continue

            date = th_elements[0].text
            total = td_elements[0].text
            views = int(total.replace(",", ""))

            data.append({"date": date, "views": views})
            log_action(f"📅 {date} | 조회수: {views}")

        except Exception as e:
            log_action(f"⚠️ 테이블 파싱 오류: {e}")


    # 실시간 조회수 수집
    today_url = f"https://admin.blog.naver.com/{blog_id}/stat/today"
    log_action(f"🌐 실시간 통계 페이지 접속: {today_url}")
    driver.get(today_url)
    time.sleep(2)


    try:
        items = driver.find_elements(By.CSS_SELECTOR, 'li.u_ni_item__W6KnJ')
        found = False
        log_action(f"🔄 항목 개수: {len(items)}"
            )       
        for item in items:
            try:
                title_span = item.find_element(By.CSS_SELECTOR, 'span.u_ni_title__1WgpG')
                log_action(f"🔄 제목 ({title_span})")                 
                if title_span.text.strip() == "조회수":
                    value_str = item.find_element(By.CSS_SELECTOR, 'strong.u_ni_value__2kc_T').text.strip()
                    today_views_int = int(value_str.replace(",", ""))
                    today_date = datetime.now().strftime("%Y.%m.%d.")
 
                    updated = False
                    for entry in data:
                        if entry["date"] == today_date:
                            entry["views"] = today_views_int
                            updated = True
                            log_action(f"🔄 실시간 조회수 업데이트 ({today_date}): {today_views_int}")
                            break

                    if not updated:
                        data.append({"date": today_date, "views": today_views_int})
                        log_action(f"🆕 실시간 조회수 추가 ({today_date}): {today_views_int}")

                    found = True
                    break

            except Exception:
                continue

        if not found:
            log_action("⚠️ '조회수' 항목을 찾지 못했습니다.")

    except Exception as e:
        import traceback
        log_action(f"❌ 실시간 조회수 파싱 실패:\n{traceback.format_exc()}")


    try:
        save_blog_views_by_date(data)
        log_action(f"💾 데이터 저장 완료 (총 {len(data)}건)")
    except Exception as e:
        log_action(f"❌ 데이터 저장 실패: {e}")


    return data
