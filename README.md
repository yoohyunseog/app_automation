# NB WFA UI

이 프로젝트는 NB WFA(Workflow Automation) 시스템의 UI 및 자동화 도구를 포함합니다.

## 주요 폴더 및 파일
- `components/` : Streamlit 기반 UI 컴포넌트 및 자동화 기능
- `writers/` : 블로그/티스토리/네이버 등 외부 서비스 업로드 모듈
- `apps/` : 분석, 자동화, 수집 관련 모듈
- `layout/` : 메인 레이아웃 및 UI 배치
- `data/` : 로그, 임시 데이터, 자동저장 파일 등
- `auto_git_upload.bat` : 전체 폴더를 GitHub에 자동 업로드하는 배치 파일

## 자동 업로드 사용법
1. Git 사용자 정보 등록 (최초 1회)
   ```
   git config --global user.name "Your Name"
   git config --global user.email "your@email.com"
   ```
2. GitHub Personal Access Token(PAT) 발급 및 최초 push 시 입력
3. `auto_git_upload.bat` 실행 시 전체 폴더가 자동 업로드됨

## OpenAI API Key 관리
- writers/tistory_auto_writer.py 등에서 환경변수 `OPENAI_API_KEY`를 사용
- Windows 환경에서 환경변수 등록 방법:
  1. 시스템 환경변수에 OPENAI_API_KEY 추가
  2. 값에 OpenAI에서 발급받은 키 입력

## 주의사항
- 비밀키, 토큰 등은 코드에 직접 남기지 마세요.
- __pycache__ 및 *.pyc 파일은 .gitignore로 관리됩니다.

## 문의
- 개발/운영 관련 문의: yoohyunseog@gmail.com
