@echo off
chcp 65001 >nul
echo ========================================
echo   Streamlit 앱 실행 중...
echo ========================================
echo.

cd /d "%~dp0"

REM 가상환경 활성화
echo 가상환경 활성화 중...
call "E:\python_env\Scripts\activate.bat"
if errorlevel 1 (
    echo [오류] 가상환경 활성화에 실패했습니다.
    echo 경로 확인: E:\python_env\Scripts\activate.bat
    pause
    exit /b 1
)
echo 가상환경 활성화 완료!
echo.

REM Streamlit이 설치되어 있는지 확인
python -c "import streamlit" 2>nul
if errorlevel 1 (
    echo [오류] Streamlit이 설치되어 있지 않습니다.
    echo 설치 중: pip install streamlit
    pip install streamlit
    if errorlevel 1 (
        echo [오류] Streamlit 설치에 실패했습니다.
        pause
        exit /b 1
    )
)

echo.
echo 앱을 시작합니다...
echo 브라우저가 자동으로 열립니다.
echo 종료하려면 Ctrl+C를 누르세요.
echo.

streamlit run app.py

pause

