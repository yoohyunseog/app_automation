# PowerShell 스크립트 - Streamlit 앱 실행
# UTF-8 인코딩 설정
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Streamlit 앱 실행 중..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 현재 스크립트가 있는 디렉토리로 이동
Set-Location $PSScriptRoot

# 가상환경 활성화
Write-Host "가상환경 활성화 중..." -ForegroundColor Yellow
$venvActivate = "E:\python_env\Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
    & $venvActivate
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[오류] 가상환경 활성화에 실패했습니다." -ForegroundColor Red
        Read-Host "아무 키나 눌러 종료"
        exit 1
    }
    Write-Host "가상환경 활성화 완료!" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "[경고] 가상환경을 찾을 수 없습니다: $venvActivate" -ForegroundColor Yellow
    Write-Host "배치 파일 방식으로 활성화 시도..." -ForegroundColor Yellow
    & "E:\python_env\Scripts\activate.bat"
}

# Streamlit이 설치되어 있는지 확인
try {
    python -c "import streamlit" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[경고] Streamlit이 설치되어 있지 않습니다." -ForegroundColor Yellow
        Write-Host "설치 중: pip install streamlit" -ForegroundColor Yellow
        pip install streamlit
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[오류] Streamlit 설치에 실패했습니다." -ForegroundColor Red
            Read-Host "아무 키나 눌러 종료"
            exit 1
        }
    }
} catch {
    Write-Host "[오류] Python을 찾을 수 없습니다." -ForegroundColor Red
    Read-Host "아무 키나 눌러 종료"
    exit 1
}

Write-Host ""
Write-Host "앱을 시작합니다..." -ForegroundColor Green
Write-Host "브라우저가 자동으로 열립니다." -ForegroundColor Green
Write-Host "종료하려면 Ctrl+C를 누르세요." -ForegroundColor Yellow
Write-Host ""

# Streamlit 실행
streamlit run app.py

# 종료 대기
Read-Host "아무 키나 눌러 종료"

