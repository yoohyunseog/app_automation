@echo off
REM Auto upload script for this ui repository
REM Prerequisites: git user.name/user.email and GitHub auth (PAT or credential manager)

setlocal
set REPO_DIR=E:\Ai project\nb_wfa\ui
set GIT_EXE=git
set REMOTE_URL=https://github.com/yoohyunseog/app_automation.git
set DEFAULT_BRANCH=master
set COMMIT_MSG=Auto upload ui %DATE% %TIME%

cd /d "%REPO_DIR%"
if errorlevel 1 (
    echo [ERROR] Cannot cd to %REPO_DIR%
    goto :END
)

%GIT_EXE% config --global --add safe.directory "E:/Ai project/nb_wfa/ui" >nul 2>&1

if not exist .git (
    %GIT_EXE% init
    %GIT_EXE% remote add origin %REMOTE_URL%
) else (
    %GIT_EXE% remote set-url origin %REMOTE_URL%
)

set CURRENT_BRANCH=
for /f %%b in ('%GIT_EXE% rev-parse --abbrev-ref HEAD 2^>nul') do set CURRENT_BRANCH=%%b
if "%CURRENT_BRANCH%"=="" set CURRENT_BRANCH=%DEFAULT_BRANCH%
if /I "%CURRENT_BRANCH%"=="HEAD" set CURRENT_BRANCH=%DEFAULT_BRANCH%

%GIT_EXE% add .
if errorlevel 1 (
    echo [ERROR] git add failed.
    goto :END
)

%GIT_EXE% diff --cached --quiet
if %ERRORLEVEL%==0 (
    echo [INFO] No staged changes to commit.
) else (
    %GIT_EXE% commit -m "%COMMIT_MSG%"
    if errorlevel 1 (
        echo [ERROR] Commit failed.
        goto :END
    )
)

%GIT_EXE% push origin %CURRENT_BRANCH%
if errorlevel 1 (
    echo [ERROR] Push failed: origin/%CURRENT_BRANCH%
) else (
    echo [OK] Upload complete: origin/%CURRENT_BRANCH%
)

:END
endlocal
pause

