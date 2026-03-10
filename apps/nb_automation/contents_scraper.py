from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import os
import pandas as pd
from utils.driver_manager import get_driver
from bs4 import BeautifulSoup

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 한글 폰트 설정 (윈도우 기준)
plt.rcParams['font.family'] = 'Malgun Gothic'  # 또는 'NanumGothic', 'AppleGothic' (macOS)
plt.rcParams['axes.unicode_minus'] = False  # 마이너스 깨짐 방지


# 블로그 주소 불러오기
BLOG_URL_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../data/blog_url.txt'))
SAVE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../data/blog_contents'))

def load_blog_url():
    if os.path.exists(BLOG_URL_FILE):
        with open(BLOG_URL_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""

def save_blog_contents_by_date(data: list):
    import json
    import pandas as pd

    os.makedirs(SAVE_DIR, exist_ok=True)

    latest_records = []

    for entry in data:
        date_str = entry["date"].split("(")[0].strip()
        try:
            date_formatted = pd.to_datetime(date_str, format="%Y.%m.%d.").strftime("%Y-%m-%d")
        except:
            date_formatted = date_str  # 실패 시 원본 유지

        file_path = os.path.join(SAVE_DIR, f"{date_formatted}.json")

        content_record = {
            "date": date_formatted,
            "title": entry.get("title", ""),
            "views": entry.get("views", ""),
            "url": entry.get("url", ""),
            "content": entry.get("content", "")
        }

        latest_records.append(content_record)

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                existing = f.read()
                if existing == str(content_record):
                    print(f"🔁 {date_formatted} 동일한 콘텐츠로 저장 건너뜀")
                    continue

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(content_record, f, ensure_ascii=False, indent=2)
        print(f"✅ {date_formatted} 콘텐츠 저장 완료")

    # ✅ 최신 전체 목록 CSV 저장
    latest_csv_path = os.path.join(SAVE_DIR, "latest_contents.csv")
    pd.DataFrame(latest_records).to_csv(latest_csv_path, index=False)

def contents_scraper():
    global driver
    driver = get_driver()

    blog_url = load_blog_url()
    if not blog_url:
        raise Exception("❌ 블로그 주소가 설정되지 않았습니다.")

    blog_id = blog_url.split("/")[-1]
    url = f"https://admin.blog.naver.com/{blog_id}/stat/rank_pv"
    driver.get(url)
    time.sleep(2)

    # iframe 진입
    try:
        iframe = driver.find_element(By.ID, "statmain")
        driver.switch_to.frame(iframe)
    except Exception as e:
        raise Exception(f"❌ iframe 접근 실패: {e}")

    # HTML 파싱
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("table tbody tr")

    content_data = []

    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 5:
            continue

        try:
            rank = int(cols[0].text.strip())
            title_tag = cols[1].find("a")
            if not title_tag or not title_tag.text.strip():
                continue

            title = title_tag.text.strip()
            href = title_tag["href"]
            views = int(cols[2].text.strip().replace(",", ""))
            date_raw = cols[4].text.strip()  # 💡 날짜를 그대로 저장

            content_data.append({
                "rank": rank,
                "title": title,
                "views": views,
                "url": "https://blog.naver.com" + href,
                "date": date_raw
            })

        except Exception as e:
            print("❌ 콘텐츠 파싱 오류:", e)

    driver.switch_to.default_content()

    # ✅ 중복 제거 (URL 기준)
    if content_data:
        df = pd.DataFrame(content_data)
        df = df.drop_duplicates(subset="url")
        result = df.to_dict(orient="records")
    else:
        result = []

    save_blog_contents_by_date(result)

    return result

def load_saved_contents():
    csv_path = os.path.join(SAVE_DIR, "latest_contents.csv")
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            if df.empty or df.columns.size == 0:
                print("⚠️ CSV 파일은 존재하지만 데이터가 없습니다.")
                return pd.DataFrame()
            return df
        except pd.errors.EmptyDataError:
            print("⚠️ CSV 파일이 비어 있어 로드할 수 없습니다.")
            return pd.DataFrame()
        except Exception as e:
            print(f"❌ CSV 로드 중 오류 발생: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

