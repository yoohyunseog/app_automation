@echo off
setlocal
cd /d "%~dp0\.."

echo [1/2] Starting YouTube external search server...
start "YT External Search" cmd /c "call AI_Search\run_youtube_external_search_server.bat"

echo [1.5/2] Waiting for external search health...
set "HEALTH_OK="
for /L %%i in (1,1,30) do (
  powershell -NoProfile -Command ^
    "try { $r=Invoke-RestMethod -Uri 'http://localhost:8091/health' -Method Get -TimeoutSec 2; if($r.ok -eq $true){ exit 0 } else { exit 1 } } catch { exit 1 }"
  if not errorlevel 1 (
    set "HEALTH_OK=1"
    goto :health_ready
  )
  timeout /t 1 /nobreak >nul
)

:health_ready
if not defined HEALTH_OK (
  echo [WARN] External search server health check failed. Web search may show intermittent errors.
) else (
  echo [OK] External search server is ready.
)

echo [2/2] Restarting Open WebUI...
docker compose -f AI_Search\docker-compose.yml restart open-webui

echo.
echo Done.
echo - Open WebUI: http://localhost:3000
echo - External search API: http://localhost:8091/search
echo.
pause

endlocal
