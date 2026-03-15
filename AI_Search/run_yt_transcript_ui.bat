@echo off
setlocal
cd /d "%~dp0\.."

set "PY_EXE=%CD%\.venv\Scripts\python.exe"
if not exist "%PY_EXE%" (
  echo [INFO] .venv python not found. Using system python.
  set "PY_EXE=python"
)

echo [INFO] Launching YouTube transcript button UI...
"%PY_EXE%" -m streamlit run "AI_Search\yt_transcript_button_ui.py" --server.port 8510

endlocal
