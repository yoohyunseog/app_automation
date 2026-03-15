import json
import subprocess
import sys
from pathlib import Path

import streamlit as st


def _resolve_python(repo_root: Path) -> str:
    venv_python = repo_root / ".venv" / "Scripts" / "python.exe"
    return str(venv_python) if venv_python.exists() else sys.executable


def _run_collector(query: str, max_results: int, visible_browser: bool) -> tuple[int, str, str]:
    repo_root = Path(__file__).resolve().parents[1]
    python_exe = _resolve_python(repo_root)
    work_root = repo_root / "data" / "selenium_runtime"
    work_root.mkdir(parents=True, exist_ok=True)

    cmd = [
        python_exe,
        "-m",
        "writers.youtube_today_transcript",
        "--query",
        query,
        "--max-results",
        str(max_results),
        "--driver-path",
        r"C:\chromedriver.exe",
        "--work-root",
        str(work_root),
    ]
    if visible_browser:
        cmd.append("--no-headless")

    proc = subprocess.run(
        cmd,
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        timeout=600,
    )
    return proc.returncode, proc.stdout, proc.stderr


def main() -> None:
    st.set_page_config(page_title="YouTube 오늘 자막 수집", layout="wide")
    st.title("YouTube 오늘 자막 수집")
    st.caption("기본: C:\\chromedriver.exe, 런타임은 E:\\Ai project\\nb_wfa\\ui\\data\\selenium_runtime")

    query = st.text_input("검색어", value="어도비 주가 급락 원인 2026")
    max_results = st.slider("최대 영상 수", min_value=1, max_value=20, value=5, step=1)
    visible_browser = st.checkbox("브라우저 창 보기(디버그)", value=False)

    if st.button("자막 수집 실행", type="primary", use_container_width=True):
        q = (query or "").strip()
        if not q:
            st.warning("검색어를 입력해 주세요.")
            return

        with st.spinner("수집 중..."):
            code, out, err = _run_collector(q, max_results, visible_browser)

        if code != 0:
            st.error("실행 실패")
            st.code(err or "(stderr empty)", language="text")
            return

        try:
            data = json.loads(out)
        except Exception:
            st.error("결과 JSON 파싱 실패")
            st.code(out or "(stdout empty)", language="text")
            return

        st.success(f"완료: {len(data)}개")
        st.json(data)


if __name__ == "__main__":
    main()
