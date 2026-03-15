"""YouTube today-only search + transcript collector using Selenium.

Usage:
    python -m writers.youtube_today_transcript --query "어도비 주가" --max-results 5
"""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
import time
from dataclasses import asdict, dataclass
from datetime import date, datetime
from typing import Iterable, List, Optional
from urllib.parse import quote_plus

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:  # pragma: no cover - handled at runtime
    YouTubeTranscriptApi = None  # type: ignore[assignment]


@dataclass
class VideoTranscript:
    video_id: str
    title: str
    url: str
    channel: str
    view_count_text: str
    age_text: str
    transcript: str
    transcript_lang: Optional[str]


def create_driver(
    headless: bool = True,
    driver_path: Optional[str] = None,
    chrome_binary: Optional[str] = None,
    work_root: Optional[str] = None,
) -> webdriver.Chrome:
    base_root = work_root or os.path.join(os.getcwd(), "data", "selenium_runtime")
    cache_dir = os.path.join(base_root, "cache")
    profile_root = os.path.join(base_root, "profiles")
    temp_dir = os.path.join(base_root, "tmp")
    os.makedirs(cache_dir, exist_ok=True)
    os.makedirs(profile_root, exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)

    # Keep Selenium/Chrome runtime files on E: workspace to reduce C: usage.
    os.environ["SE_CACHE_PATH"] = cache_dir
    os.environ["TMP"] = temp_dir
    os.environ["TEMP"] = temp_dir
    os.environ["TMPDIR"] = temp_dir

    options = Options()
    options.add_argument("--lang=ko-KR")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument(
        f"--user-data-dir={tempfile.mkdtemp(prefix='yt_chrome_profile_', dir=profile_root)}"
    )
    if chrome_binary:
        options.binary_location = chrome_binary
    if headless:
        options.add_argument("--headless=new")
    if driver_path:
        return webdriver.Chrome(service=Service(driver_path), options=options)
    return webdriver.Chrome(options=options)


def extract_video_id(url: str) -> Optional[str]:
    match = re.search(r"[?&]v=([a-zA-Z0-9_-]{11})", url or "")
    return match.group(1) if match else None


def _parse_korean_date(age_text: str) -> Optional[date]:
    m = re.search(r"(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})\.?", age_text)
    if not m:
        return None
    return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))


def _parse_english_date(age_text: str) -> Optional[date]:
    # Example: Mar 15, 2026
    cleaned = age_text.replace("Published on ", "").strip()
    for fmt in ("%b %d, %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue
    return None


def is_today_video(age_text: str, today: Optional[date] = None) -> bool:
    if not age_text:
        return False
    t = (today or date.today())
    lower = age_text.lower().strip()

    immediate_markers = (
        "방금 전",
        "초 전",
        "분 전",
        "시간 전",
        "today",
        "minute ago",
        "minutes ago",
        "hour ago",
        "hours ago",
        "streamed",
        "live",
    )
    if any(marker in lower for marker in immediate_markers):
        # Exclude "1 day ago" style.
        if "day ago" in lower or "days ago" in lower or "일 전" in lower:
            return False
        return True

    kr_date = _parse_korean_date(age_text)
    if kr_date is not None:
        return kr_date == t

    en_date = _parse_english_date(age_text)
    if en_date is not None:
        return en_date == t

    return False


def _best_age_text(metadata_parts: Iterable[str]) -> str:
    parts = [p.strip() for p in metadata_parts if p.strip()]
    if not parts:
        return ""
    for p in parts:
        if any(token in p.lower() for token in ("ago", "today", "전", "live", "streamed")):
            return p
    return parts[-1]


def _best_view_text(metadata_parts: Iterable[str]) -> str:
    parts = [p.strip() for p in metadata_parts if p.strip()]
    if not parts:
        return ""
    for p in parts:
        lower = p.lower()
        if "조회수" in p or "views" in lower or "watching" in lower:
            return p
    return ""


def search_today_youtube_videos(
    query: str,
    max_results: int = 5,
    headless: bool = True,
    driver_path: Optional[str] = None,
    chrome_binary: Optional[str] = None,
    work_root: Optional[str] = None,
    today_only: bool = True,
    wait_seconds: int = 15,
) -> List[dict]:
    driver = create_driver(
        headless=headless,
        driver_path=driver_path,
        chrome_binary=chrome_binary,
        work_root=work_root,
    )
    collected: List[dict] = []
    seen_ids = set()
    try:
        url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
        driver.get(url)

        WebDriverWait(driver, wait_seconds).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ytd-video-renderer"))
        )

        scroll_round = 0
        while len(collected) < max_results and scroll_round < 6:
            cards = driver.find_elements(By.CSS_SELECTOR, "ytd-video-renderer")
            for card in cards:
                try:
                    title_el = card.find_element(By.CSS_SELECTOR, "a#video-title")
                    video_url = title_el.get_attribute("href") or ""
                    video_id = extract_video_id(video_url)
                    if not video_id or video_id in seen_ids:
                        continue

                    title = (title_el.get_attribute("title") or title_el.text or "").strip()
                    channel = ""
                    ch_nodes = card.find_elements(By.CSS_SELECTOR, "#channel-name a")
                    if ch_nodes:
                        channel = ch_nodes[0].text.strip()

                    meta_nodes = card.find_elements(By.CSS_SELECTOR, "#metadata-line span.inline-metadata-item")
                    meta_texts = [node.text for node in meta_nodes]
                    age_text = _best_age_text(meta_texts)
                    view_count_text = _best_view_text(meta_texts)
                    if today_only and not is_today_video(age_text):
                        continue

                    seen_ids.add(video_id)
                    collected.append(
                        {
                            "video_id": video_id,
                            "title": title,
                            "url": f"https://www.youtube.com/watch?v={video_id}",
                            "channel": channel,
                            "view_count_text": view_count_text,
                            "age_text": age_text,
                        }
                    )
                    if len(collected) >= max_results:
                        break
                except Exception:
                    continue

            if len(collected) >= max_results:
                break

            driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            time.sleep(1.2)
            scroll_round += 1

    except TimeoutException:
        return []
    finally:
        driver.quit()
    return collected


def fetch_transcript_text(
    video_id: str,
    languages: Optional[List[str]] = None,
) -> tuple[str, Optional[str]]:
    if YouTubeTranscriptApi is None:
        raise RuntimeError(
            "youtube-transcript-api is not installed. "
            "Install with: pip install youtube-transcript-api"
        )
    language_list = languages or ["ko", "en"]
    transcript_rows = YouTubeTranscriptApi.get_transcript(video_id, languages=language_list)
    text = " ".join(row.get("text", "").strip() for row in transcript_rows).strip()
    detected_lang = None
    if transcript_rows:
        # API does not always return language field per row.
        detected_lang = language_list[0]
    return text, detected_lang


def collect_today_video_transcripts(
    query: str,
    max_results: int = 5,
    headless: bool = True,
    driver_path: Optional[str] = None,
    chrome_binary: Optional[str] = None,
    work_root: Optional[str] = None,
    languages: Optional[List[str]] = None,
    today_only: bool = True,
) -> List[VideoTranscript]:
    videos = search_today_youtube_videos(
        query=query,
        max_results=max_results,
        headless=headless,
        driver_path=driver_path,
        chrome_binary=chrome_binary,
        work_root=work_root,
        today_only=today_only,
    )
    results: List[VideoTranscript] = []
    for item in videos:
        try:
            transcript_text, detected_lang = fetch_transcript_text(
                item["video_id"], languages=languages
            )
        except Exception:
            transcript_text, detected_lang = "", None

        results.append(
            VideoTranscript(
                video_id=item["video_id"],
                title=item["title"],
                url=item["url"],
                channel=item["channel"],
                view_count_text=item.get("view_count_text", ""),
                age_text=item["age_text"],
                transcript=transcript_text,
                transcript_lang=detected_lang,
            )
        )
    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Collect transcripts from YouTube videos uploaded today."
    )
    parser.add_argument("--query", required=True, help="YouTube search query")
    parser.add_argument("--max-results", type=int, default=5, help="Maximum number of today videos")
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Open visible Chrome window",
    )
    parser.add_argument(
        "--languages",
        default="ko,en",
        help="Comma-separated transcript language priority, e.g. ko,en",
    )
    parser.add_argument(
        "--driver-path",
        default=os.getenv("CHROMEDRIVER_PATH", r"C:\chromedriver.exe"),
        help="Path to chromedriver executable. Default: C:\\chromedriver.exe",
    )
    parser.add_argument(
        "--chrome-binary",
        default=os.getenv("CHROME_BINARY_PATH", ""),
        help="Path to chrome executable if auto-detection fails.",
    )
    parser.add_argument(
        "--work-root",
        default=os.getenv("YT_SELENIUM_WORK_ROOT", os.path.join(os.getcwd(), "data", "selenium_runtime")),
        help="Runtime folder for Selenium cache/profile/temp. Use an E: path.",
    )
    parser.add_argument(
        "--allow-non-today",
        action="store_true",
        help="If set, include non-today videos too.",
    )
    args = parser.parse_args()

    language_list = [part.strip() for part in args.languages.split(",") if part.strip()]
    data = collect_today_video_transcripts(
        query=args.query,
        max_results=args.max_results,
        headless=not args.no_headless,
        driver_path=args.driver_path or None,
        chrome_binary=args.chrome_binary or None,
        work_root=args.work_root or None,
        languages=language_list,
        today_only=not args.allow_non_today,
    )
    print(json.dumps([asdict(item) for item in data], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
