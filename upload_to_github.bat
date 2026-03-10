@echo off
chcp 65001 > nul
echo ========================================
echo GitHub 자동 업로드
echo ========================================
echo.

cd /d "e:\Ai project\사이트"

:: Git 상태 확인
echo [1/5] Git 상태 확인 중...
git status
echo.

:: 모든 변경사항 추가
echo [2/5] 변경된 파일 추가 중...
git add .
echo.

:: 커밋 메시지 입력 (현재 날짜/시간 포함)
echo [3/5] 커밋 생성 중...
set datetime=%date% %time%
git commit -m "Update: %datetime%"
echo.

:: 원격 저장소 확인 및 설정
echo [4/5] 원격 저장소 확인 중...
git remote -v
git remote | findstr origin > nul
if errorlevel 1 (
    echo 원격 저장소 추가 중...
    git remote add origin https://github.com/yoohyunseog/HANKOOKINTERNET-CHAMSOSIK.git
)
echo.

:: Push 실행
echo [5/5] GitHub에 업로드 중...
git push -u origin main
echo.

if errorlevel 1 (
    echo.
    echo ❌ 업로드 실패!
    echo Git 인증 정보를 확인하거나 수동으로 push 해주세요.
    echo.
    pause
    exit /b 1
) else (
    echo.
    echo ✅ GitHub 업로드 완료!
    echo Repository: https://github.com/yoohyunseog/HANKOOKINTERNET-CHAMSOSIK
    echo.
)

pause
