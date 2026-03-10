@echo off
REM 전체 ui 폴더를 app_automation 저장소에 자동 업로드하는 스크립트
REM 최초 실행 전 git config --global user.name / user.email 및 PAT 인증 필요

setlocal
set REPO_DIR=E:\Ai project\nb_wfa\ui
set GIT_EXE=git
set REMOTE_URL=https://github.com/yoohyunseog/app_automation.git
set COMMIT_MSG=Auto upload all ui folder %DATE% %TIME%

cd /d "%REPO_DIR%"

REM git 초기화 (최초 1회만 필요)
if not exist .git (
    %GIT_EXE% init
    %GIT_EXE% remote add origin %REMOTE_URL%
) else (
    %GIT_EXE% remote set-url origin %REMOTE_URL%
)

REM 변경사항 추가
%GIT_EXE% add .

REM 커밋
%GIT_EXE% commit -m "%COMMIT_MSG%"

REM 푸시
%GIT_EXE% push origin master

endlocal
pause
