@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0\.."

set "PY_EXE=%CD%\.venv\Scripts\python.exe"
if not exist "%PY_EXE%" (
  echo [INFO] .venv python not found. Using system python.
  set "PY_EXE=python"
)

set "YT_EXT_SEARCH_HOST=0.0.0.0"
set "YT_EXT_SEARCH_PORT=8091"
set "YT_EXT_SEARCH_API_KEY=yt-external-key"
set "YT_EXT_SEARXNG_URL=http://localhost:8081/search"
set "YT_EXT_SEARXNG_LANGUAGE=auto"
set "YT_EXT_SEARXNG_CATEGORIES=general"
set "YT_SELENIUM_WORK_ROOT=E:\Ai project\nb_wfa\ui\data\selenium_runtime"
set "YT_EXT_VERBOSE=1"
set "YT_MAX_TRANSCRIPT_RESULTS=2"
set "YT_EXT_LOG_FILE=E:\Ai project\nb_wfa\ui\AI_Search\logs\yt_external_server.log"
set "YT_EXT_ERROR_LOG_FILE=E:\Ai project\nb_wfa\ui\AI_Search\logs\yt_external_server.error.log"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
rem Optional: set YT_HTTPS_PROXY before running, e.g. http://127.0.0.1:7890
if not "%YT_HTTPS_PROXY%"=="" (
  set "HTTPS_PROXY=%YT_HTTPS_PROXY%"
  set "HTTP_PROXY=%YT_HTTPS_PROXY%"
  echo [INFO] Proxy enabled: %YT_HTTPS_PROXY%
)

echo [INFO] Cleaning old listeners on port %YT_EXT_SEARCH_PORT%...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":%YT_EXT_SEARCH_PORT% " ^| findstr "LISTENING"') do (
  taskkill /PID %%p /F >nul 2>&1
)

echo [INFO] Starting youtube external search server on port %YT_EXT_SEARCH_PORT%
echo [INFO] Verbose log: %YT_EXT_VERBOSE%
echo [INFO] YT transcripts per query: %YT_MAX_TRANSCRIPT_RESULTS%
echo [INFO] SearXNG URL : %YT_EXT_SEARXNG_URL%
echo [INFO] SearXNG Lang: %YT_EXT_SEARXNG_LANGUAGE%
echo [INFO] SearXNG Cat : %YT_EXT_SEARXNG_CATEGORIES%
echo [INFO] Work root   : %YT_SELENIUM_WORK_ROOT%
echo [INFO] Log file    : %YT_EXT_LOG_FILE%
echo [INFO] Error log   : %YT_EXT_ERROR_LOG_FILE%
if not exist "AI_Search\logs" mkdir "AI_Search\logs"
type nul > "%YT_EXT_LOG_FILE%"
type nul > "%YT_EXT_ERROR_LOG_FILE%"
start "" "http://localhost:3000"
"%PY_EXE%" -u "AI_Search\youtube_external_search_server.py"

endlocal
