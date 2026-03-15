import json
import os
import re
import time
import traceback
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse

import requests
from youtube_transcript_api import YouTubeTranscriptApi


HOST = os.getenv("YT_EXT_SEARCH_HOST", "0.0.0.0")
PORT = int(os.getenv("YT_EXT_SEARCH_PORT", "8091"))
API_KEY = os.getenv("YT_EXT_SEARCH_API_KEY", "yt-external-key")
SEARXNG_URL = os.getenv("YT_EXT_SEARXNG_URL", "http://localhost:8081/search")
SEARXNG_LANGUAGE = os.getenv("YT_EXT_SEARXNG_LANGUAGE", "auto")
SEARXNG_CATEGORIES = os.getenv("YT_EXT_SEARXNG_CATEGORIES", "general")
VERBOSE = os.getenv("YT_EXT_VERBOSE", "1").lower() not in ("0", "false", "no")
YT_MAX_TRANSCRIPT_RESULTS = max(
    1, min(int(os.getenv("YT_MAX_TRANSCRIPT_RESULTS", "2")), 2)
)

BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent
WORK_ROOT = Path(
    os.getenv("YT_SELENIUM_WORK_ROOT", str(REPO_ROOT / "data" / "selenium_runtime"))
)
WORK_ROOT.mkdir(parents=True, exist_ok=True)

LOG_FILE = Path(
    os.getenv("YT_EXT_LOG_FILE", str(BASE_DIR / "logs" / "yt_external_server.log"))
)
ERR_LOG_FILE = Path(
    os.getenv(
        "YT_EXT_ERROR_LOG_FILE", str(BASE_DIR / "logs" / "yt_external_server.error.log")
    )
)
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
ERR_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


def _log(msg: str, req_id: str = "-") -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}][req:{req_id}] {msg}"
    if VERBOSE:
        print(line, flush=True)
    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def _log_error(msg: str, req_id: str = "-", exc: Exception | None = None) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}][req:{req_id}][ERROR] {msg}"
    print(line, flush=True)
    tb = ""
    if exc is not None:
        tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        if tb:
            print(tb, flush=True)
    try:
        with ERR_LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
            if tb:
                f.write(tb + "\n")
    except Exception:
        pass


def _extract_video_id(url: str) -> str:
    m = re.search(r"[?&]v=([a-zA-Z0-9_-]{11})", url or "")
    if m:
        return m.group(1)
    m2 = re.search(r"/shorts/([a-zA-Z0-9_-]{11})", url or "")
    return m2.group(1) if m2 else ""


def _extract_yt_meta_from_html(html: str) -> Dict[str, str]:
    channel = ""
    views = ""
    date_text = ""

    m_channel = re.search(r'"ownerChannelName":"([^"]+)"', html)
    if m_channel:
        channel = m_channel.group(1).encode("utf-8").decode("unicode_escape")

    m_views = re.search(r'"shortViewCountText":\{"simpleText":"([^"]+)"\}', html)
    if m_views:
        views = m_views.group(1).encode("utf-8").decode("unicode_escape")
    else:
        m_views2 = re.search(r'"viewCount":"([^"]+)"', html)
        if m_views2:
            views = m_views2.group(1).encode("utf-8").decode("unicode_escape")

    m_date = re.search(r'"dateText":\{"simpleText":"([^"]+)"\}', html)
    if m_date:
        date_text = m_date.group(1).encode("utf-8").decode("unicode_escape")
    else:
        m_pub = re.search(r'"publishDate":"([^"]+)"', html)
        if m_pub:
            date_text = m_pub.group(1)

    return {"channel": channel, "view_count_text": views, "age_text": date_text}


def _fetch_yt_meta(video_id: str) -> Dict[str, str]:
    try:
        resp = requests.get(
            f"https://www.youtube.com/watch?v={video_id}",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15,
        )
        if resp.status_code != 200:
            return {"channel": "", "view_count_text": "", "age_text": ""}
        return _extract_yt_meta_from_html(resp.text)
    except Exception:
        return {"channel": "", "view_count_text": "", "age_text": ""}


def _has_non_ascii(text: str) -> bool:
    return any(ord(ch) > 127 for ch in text or "")


def _build_query_variants(query: str, youtube_mode: bool = False) -> List[str]:
    q = " ".join((query or "").split())
    variants = [q]
    if youtube_mode:
        variants.extend([f"{q} youtube", f"youtube {q}"])
    else:
        variants.extend([f"{q} news", f"{q} latest"])
    if _has_non_ascii(q):
        variants.append(f"{q} 뉴스")
        variants.append(f"{q} 유튜브" if youtube_mode else f"{q} 소식")
    uniq: List[str] = []
    seen = set()
    for v in variants:
        if v and v not in seen:
            seen.add(v)
            uniq.append(v)
    return uniq


def _fetch_searxng(query: str, count: int, req_id: str, youtube_mode: bool = False) -> List[Dict[str, str]]:
    params = {
        "format": "json",
        "pageno": 1,
        "language": SEARXNG_LANGUAGE,
        "categories": SEARXNG_CATEGORIES,
        "safesearch": 1,
    }
    for qv in _build_query_variants(query, youtube_mode=youtube_mode):
        params["q"] = qv
        _log(f"searxng query={qv!r} count={count}", req_id)
        try:
            resp = requests.get(SEARXNG_URL, params=params, timeout=20)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            _log_error(f"searxng request failed: {type(e).__name__}: {e}", req_id, e)
            continue

        items: List[Dict[str, str]] = []
        for row in data.get("results", [])[:count]:
            link = row.get("url") or ""
            title = row.get("title") or ""
            snippet = row.get("content") or ""
            if link:
                items.append({"link": link, "title": title, "snippet": snippet})

        _log(f"searxng results={len(items)} (variant={qv!r})", req_id)
        if items:
            return items
    return []


def _extract_transcript_api(video_id: str) -> Tuple[str, str]:
    try:
        # Support both old and new youtube-transcript-api versions.
        if hasattr(YouTubeTranscriptApi, "get_transcript"):
            rows = YouTubeTranscriptApi.get_transcript(
                video_id, languages=["ko", "en"]
            )
        else:
            api = YouTubeTranscriptApi()
            rows = api.fetch(video_id, languages=["ko", "en"])

        if hasattr(rows, "to_raw_data"):
            rows_iter = rows.to_raw_data()
        else:
            rows_iter = rows

        chunks: List[str] = []
        for x in rows_iter:
            if isinstance(x, dict):
                t = str(x.get("text", "")).strip()
            else:
                t = str(getattr(x, "text", "")).strip()
            if t:
                chunks.append(t)
        text = " ".join(chunks).strip()
        if text:
            return text, "ok"
        return "", "empty"
    except Exception as e:
        ename = type(e).__name__
        return "", ename


def _fetch_youtube_transcripts_api(
    query: str, count: int, req_id: str
) -> Tuple[List[Dict[str, str]], Dict[str, int]]:
    yt_links = _fetch_searxng(
        f"site:youtube.com {query}",
        max(10, count * 2),
        req_id,
        youtube_mode=True,
    )
    candidates: List[Dict[str, str]] = []
    seen = set()
    for item in yt_links:
        link = item.get("link", "")
        if "youtube.com/watch" not in link and "youtube.com/shorts/" not in link:
            continue
        vid = _extract_video_id(link)
        if not vid or vid in seen:
            continue
        seen.add(vid)
        candidates.append(
            {"video_id": vid, "link": link, "title": item.get("title", "")}
        )
        if len(candidates) >= YT_MAX_TRANSCRIPT_RESULTS:
            break

    _log(f"youtube candidates={len(candidates)}", req_id)

    results: List[Dict[str, str]] = []
    stats = {"ok": 0, "blocked": 0, "failed": 0}
    for idx, c in enumerate(candidates, start=1):
        vid = c["video_id"]
        transcript_text, status = _extract_transcript_api(vid)
        meta = _fetch_yt_meta(vid)
        ch = meta.get("channel", "") or "unknown"
        vw = meta.get("view_count_text", "") or "unknown"
        dt = meta.get("age_text", "") or "unknown"
        meta_text = f"channel={ch} | views={vw} | date={dt}"

        if transcript_text:
            stats["ok"] += 1
            snippet = f"[YouTube Transcript:API] {meta_text}\n{transcript_text[:1800]}"
        else:
            if status in ("RequestBlocked", "IpBlocked"):
                stats["blocked"] += 1
            else:
                stats["failed"] += 1
            snippet = f"[YouTube:API] {meta_text} (transcript={status})"

        _log(
            f"candidate#{idx} vid={vid} status={status} title={c.get('title','')[:60]}",
            req_id,
        )
        results.append(
            {
                "link": c["link"],
                "title": c["title"] or f"YouTube Video {vid}",
                "snippet": snippet,
            }
        )

    results.sort(
        key=lambda x: 0 if "[YouTube Transcript:API]" in x.get("snippet", "") else 1
    )
    return results, stats


class SearchHandler(BaseHTTPRequestHandler):
    server_version = "YTExternalSearch/3.1"

    def _send_json(self, code: int, payload: Any) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        req_id = str(int(time.time() * 1000))[-6:]
        started = time.time()
        try:
            parsed = urlparse(self.path)
            if parsed.path != "/search":
                self._send_json(404, {"error": "not_found"})
                return

            if API_KEY:
                auth = self.headers.get("Authorization", "")
                if auth != f"Bearer {API_KEY}":
                    self._send_json(401, {"error": "unauthorized"})
                    return

            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length) if length > 0 else b"{}"
            try:
                payload = json.loads(raw.decode("utf-8"))
            except Exception:
                self._send_json(400, {"error": "invalid_json"})
                return

            query = str(payload.get("query", "")).strip()
            count = max(1, min(int(payload.get("count", 5)), 15))
            _log(f"search start query={query!r} count={count}", req_id)

            if not query:
                self._send_json(200, [])
                return

            yt_items, yt_stats = _fetch_youtube_transcripts_api(query, count, req_id)
            base_items = _fetch_searxng(query, count, req_id)

            status_item = {
                "link": "https://www.youtube.com/",
                "title": "YouTube 자막 검색 상태",
                "snippet": (
                    f"YouTubeTranscriptApi executed. "
                    f"candidates={len(yt_items)} ok={yt_stats['ok']} "
                    f"blocked={yt_stats['blocked']} failed={yt_stats['failed']} "
                    f"(fields: channel, views, date)."
                ),
            }

            merged: List[Dict[str, str]] = []
            seen = set()
            for item in [status_item] + yt_items + base_items:
                link = item.get("link", "")
                if not link or link in seen:
                    continue
                seen.add(link)
                merged.append(item)
                if len(merged) >= count:
                    break

            elapsed = time.time() - started
            _log(f"search done merged={len(merged)} elapsed={elapsed:.2f}s", req_id)
            self._send_json(200, merged)
        except Exception as e:
            _log_error("Unhandled exception in /search", req_id, e)
            self._send_json(500, {"error": "internal_error"})

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._send_json(
                200,
                {
                    "ok": True,
                    "service": "yt-external-search",
                    "mode": "youtube-transcript-api",
                },
            )
            return
        self._send_json(404, {"error": "not_found"})


def main() -> None:
    httpd = ThreadingHTTPServer((HOST, PORT), SearchHandler)
    print(f"[yt-external-search] listening on http://{HOST}:{PORT}/search", flush=True)
    print("[yt-external-search] mode: youtube-transcript-api", flush=True)
    print(f"[yt-external-search] using searxng: {SEARXNG_URL}", flush=True)
    print(
        f"[yt-external-search] searxng language={SEARXNG_LANGUAGE} categories={SEARXNG_CATEGORIES}",
        flush=True,
    )
    print(f"[yt-external-search] selenium runtime: {WORK_ROOT}", flush=True)
    print(f"[yt-external-search] log_file: {LOG_FILE}", flush=True)
    print(f"[yt-external-search] error_log_file: {ERR_LOG_FILE}", flush=True)
    print(
        f"[yt-external-search] yt_max_transcript_results={YT_MAX_TRANSCRIPT_RESULTS}",
        flush=True,
    )
    print(f"[yt-external-search] verbose={VERBOSE}", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
