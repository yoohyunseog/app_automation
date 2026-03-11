import sys
import os
import time
import re
import html  # ← 이거 추가
import urllib.parse
import pyperclip
from writers.ollama_api import call_ollama_api, call_ollama_api_category
import json
import random
import requests
from PIL import Image
import pytesseract

from io import BytesIO
from bs4 import BeautifulSoup
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    WebDriverException,
    TimeoutException,
    SessionNotCreatedException,
    StaleElementReferenceException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

# 프로젝트 루트 경로 설정 (상대 경로)
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_dir)  # ver0.2.0.0 폴더
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# 프로젝트 내부 모듈 우선 import
try:
    # 프로젝트 내부에서 먼저 찾기
    from core.image_search import naver_image_search_with_rotation, download_image_with_timestamp, upload_image_to_github, google_image_search_safe
    # create_image_prompt_from_korean_topic은 core.image_search에 없을 수 있음
    try:
        from core.image_search import create_image_prompt_from_korean_topic
    except ImportError:
        create_image_prompt_from_korean_topic = None
except ImportError:
    # 외부 경로에서 찾기 (하위 호환성)
    _external_paths = [
        os.path.join(os.path.dirname(_project_root), "nb_wfa", "core", "collect"),
        os.path.join(os.path.dirname(_project_root), "nb_wfa", "chatbot"),
    ]
    for path in _external_paths:
        if os.path.exists(path) and path not in sys.path:
            sys.path.append(path)
    from image_search import naver_image_search_with_rotation, download_image_with_timestamp, upload_image_to_github, google_image_search_safe
    try:
        from image_search import create_image_prompt_from_korean_topic
    except ImportError:
        create_image_prompt_from_korean_topic = None

# 외부 모듈 import (프로젝트 내부에 없으면 외부 경로에서)
# generate_filepath 모듈 (선택적)
try:
    try:
        from collectors.generate_filepath import collect_trending_articles_as_text, translate_keyword
        GENERATE_FILEPATH_AVAILABLE = True
    except ImportError:
        from generate_filepath import collect_trending_articles_as_text, translate_keyword
        GENERATE_FILEPATH_AVAILABLE = True
except ImportError as e:
    GENERATE_FILEPATH_AVAILABLE = False
    print(f"⚠️ generate_filepath 불러오기 실패: {e}. 해당 기능은 비활성화됩니다.")
    def collect_trending_articles_as_text(*args, **kwargs):
        print("⚠️ generate_filepath 모듈이 필요합니다. 이 기능은 건너뜁니다.")
        return []
    def translate_keyword(*args, **kwargs):
        print("⚠️ generate_filepath 모듈이 필요합니다. 원본 키워드를 반환합니다.")
        return args[0] if args else kwargs.get('keyword', '')

# pinterest_image_scraper 모듈 (선택적)
try:
    try:
        from collectors.pinterest_image_scraper import get_564x_pinterest_images_and_upload, generate_clean_illustration_prompt, sanitize_filename
        PINTEREST_AVAILABLE = True
    except ImportError:
        from pinterest_image_scraper import get_564x_pinterest_images_and_upload, generate_clean_illustration_prompt, sanitize_filename
        PINTEREST_AVAILABLE = True
except ImportError:
    PINTEREST_AVAILABLE = False
    print("⚠️ pinterest_image_scraper 모듈을 찾을 수 없습니다. Pinterest 이미지 기능은 사용할 수 없습니다.")
    def get_564x_pinterest_images_and_upload(*args, **kwargs):
        print("⚠️ pinterest_image_scraper 모듈이 필요합니다. 이 기능은 건너뜁니다.")
        return []
    def generate_clean_illustration_prompt(*args, **kwargs):
        print("⚠️ pinterest_image_scraper 모듈이 필요합니다. 기본 프롬프트를 반환합니다.")
        return args[0] if args else kwargs.get('prompt', '')
    def sanitize_filename(*args, **kwargs):
        import re
        filename = args[0] if args else kwargs.get('filename', '')
        # 기본 파일명 정리
        return re.sub(r'[^\w\-_\.]', '_', filename)

# bing_image_scraper 모듈 (선택적)
try:
    try:
        from collectors.bing_image_scraper import bing_image_search_illustration, extract_single_entity_from_title
        BING_SCRAPER_AVAILABLE = True
    except ImportError:
        from bing_image_scraper import bing_image_search_illustration, extract_single_entity_from_title
        BING_SCRAPER_AVAILABLE = True
except ImportError:
    BING_SCRAPER_AVAILABLE = False
    print("⚠️ bing_image_scraper 모듈을 찾을 수 없습니다. Bing 이미지 스크래퍼 기능은 사용할 수 없습니다.")
    def bing_image_search_illustration(*args, **kwargs):
        print("⚠️ bing_image_scraper 모듈이 필요합니다. 이 기능은 건너뜁니다.")
        return []
    def extract_single_entity_from_title(*args, **kwargs):
        print("⚠️ bing_image_scraper 모듈이 필요합니다. 원본 제목을 반환합니다.")
        return args[0] if args else kwargs.get('title', '')


import logging
import inspect

# main.py - keyboard_blocker는 선택적 모듈
try:
    import keyboard_blocker
    KEYBOARD_BLOCKER_AVAILABLE = True
except ImportError:
    KEYBOARD_BLOCKER_AVAILABLE = False
    print("⚠️ keyboard_blocker 모듈을 사용할 수 없습니다. 계속 진행합니다.")


# 로거 설정 (로그 파일 저장)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s - %(filename)s - %(funcName)s',
    filename='app.log',  # 로그를 파일에 저장
    filemode='w'  # 파일을 덮어쓰기 모드로 설정
)

# 로그를 기록할 함수
def log_function():
    current_function = inspect.currentframe().f_code.co_name  # 현재 함수명
    current_file = inspect.currentframe().f_globals["__file__"]  # 현재 파일명
    print(f"현재 파일: {current_file}, 현재 함수: {current_function}")

def another_function():
    current_function = inspect.currentframe().f_code.co_name
    current_file = inspect.currentframe().f_globals["__file__"]
    print(f"현재 파일: {current_file}, 현재 함수: {current_function}")

# 함수 호출
log_function()
another_function()

_driver = None
LAUNCH_LOG = "naver_launch_log.txt"
LOG_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "naver_selenium_chrome_action_log.txt")




import json
import re

import openai
import re
import json


def extract_hashtags_json(content: str) -> dict:
    # 요청할 프롬프트 생성
    prompt_1 = f"""
    다음 글을 감성적으로 바꿔줘. 아래 조건을 반드시 지켜줘:

    1. 중요하거나 핵심이 되는 문장 앞에는 아래 이모지 중 하나를 무작위로 붙여줘.  
       단, 모든 문장에 붙이지 말고 의미상 강조가 필요한 문장만 골라 써줘.  
       사용 가능한 이모지 목록:  
       ✦ ✧ ✩ ✪ ✫ ✬ ✭ ✮ ✯ ✰ ✱ ✲ ✴ ✵ ❀ ❁ ✿ ❃ ❋ ❊ ❉ 𓂃 ◌ 𓈒 𓏸  

    2. 문단이 끝날 때마다 반드시 `<br>` 태그를 넣어서 줄바꿈을 해줘.  
       특히 `<h2>` 태그 앞에는 항상 `<br><br>`가 있도록 해줘.  
       만약 `<br>`이 2개 미만일 경우, 자동으로 추가해서 가독성을 높여줘.  
       전체 문장이 자연스럽고 읽기 편하게 보이도록 `<br>` 태그를 적절히 배치해줘.

    3. 마지막 줄에는 감성 키워드 해시태그를 `#`로 시작해 한 줄로 이어서 출력해줘.  
       예: `#장마#감성#여행`

    4. 전체 응답은 아래 JSON 형식처럼 구성해줘. 절대 백틱(```json)으로 감싸지 말고 순수 JSON으로만 반환해:
    {{
      "formatted_html": "감성 문장들<br>...",
      "hashtags": "#장마 #우산 #여행"
    }}

    5. 줄바꿈 처리가 자연스럽게 `<br>`로 반영되었는지 다시 확인해줘.

    6. 문장은 모두 한국어로 번역해서 작성해줘.

    7. ⚠️ 링크는 **네이버 검색 링크만** 사용해줘. 다른 사이트 링크는 절대 하지 말 것!
       - 반드시 단어 1개가 아니라, 문장(또는 문장 일부) 전체를 질문형으로 만들어 네이버 검색 링크를 걸어줘.
       - 예시: `<a href="https://search.naver.com/search.naver?query=이+행사의+의미는+무엇인가요" target="_blank" style="color:#0066cc; text-decoration:underline;">이 행사의 의미는 무엇인가요?</a>`
       - 각 문단마다 1~2개 정도, 너무 과하지 않게 자연스럽게 질문형 링크를 추가해줘.

    8. 문체는 MZ 세대 감성에 맞되, 가볍고 세련되면서도 **존칭을 유지**해 주세요.  
       너무 딱딱하지 않게, 감정 표현은 솔직하게 해주시되 자연스러운 높임말을 사용해 주세요.  
       예: "괜히 울컥하셨던 날 있으시죠." 같은 따뜻한 존댓말 문장으로 감성적으로 풀어주세요.

    내용:
    {content}
    """

    # ✅ Ollama API 호출 (OpenAI 대체)
    response_text = call_ollama_api(prompt_1, model="gpt-oss:120b-cloud")
    if not response_text or response_text.strip() == "":
        print("❌ Ollama 응답이 비어 있습니다. AI 응답을 확인하세요.")
        return {"formatted_html": "", "hashtags": ""}

    # ✅ JSON 파싱 - 여러 시도 방법
    result = None
    
    # 1단계: 백틱 제거 (예: ```json 또는 ```로 감싼 경우)
    clean_json_text = re.sub(r"^```(?:json)?|```$", "", response_text, flags=re.MULTILINE).strip()
    # 2단계: 첫 번째 { 부터 마지막 }까지만 추출
    json_match = re.search(r'\{.*\}', clean_json_text, re.DOTALL)
    if json_match:
        clean_json_text = json_match.group(0)
    # 3단계: 문제 있는 문자 정리
    clean_json_text = clean_json_text.replace('\n', ' ')
    # 4단계: 연속 공백 정리
    clean_json_text = re.sub(r'\s+', ' ', clean_json_text)
    # 5단계: JSON 파싱 시도
    try:
        result = json.loads(clean_json_text)
    except Exception as e:
        print(f"❌ JSON 파싱 실패: {e}\nOllama 원문 응답: {response_text}")
        return {"formatted_html": "", "hashtags": ""}
    # 필수 키 확인
    if not result or "formatted_html" not in result or "hashtags" not in result:
        print(f"❌ JSON 파싱 실패 또는 필수 키 누락. Ollama 원문 응답: {response_text}")
        return {"formatted_html": "", "hashtags": ""}
    # 본문 맨 상단에 참소식.com 이동 질문형 문장 링크 추가
    if result and "formatted_html" in result:
        chamsosik_link = '<a href="https://참소식.com" target="_blank" style="color:#0066cc; text-decoration:underline;">더 많은 소식이 궁금하다면 참소식 포켓 뉴스에서 확인해보시겠어요?</a><br><br>'
        result["formatted_html"] = chamsosik_link + result["formatted_html"]
    return result


def log_action(message):
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)

    # 로그 디렉토리 생성
    os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)
    with open(LOG_FILE_PATH, 'a', encoding='utf-8') as f:
        f.write(log_entry + "\n")

# HTML 태그 제거 함수
def strip_html_tags(text):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

def get_chrome_version():
    """Chrome 브라우저 버전을 확인합니다."""
    try:
        # 방법 1: 레지스트리에서 확인 (Windows)
        try:
            import winreg
            key_path = r"SOFTWARE\Google\Chrome\BLBeacon"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path)
            version = winreg.QueryValueEx(key, "version")[0]
            winreg.CloseKey(key)
            print(f"📋 Chrome 버전 확인: {version}")
            return version
        except Exception:
            pass
        
        # 방법 2: 파일 시스템에서 확인
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ]
        
        for chrome_path in chrome_paths:
            if os.path.exists(chrome_path):
                try:
                    import subprocess
                    result = subprocess.run(
                        [chrome_path, "--version"],
                        capture_output=True,
                        text=True,
                        timeout=3,
                        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                    )
                    if result.returncode == 0:
                        version_output = result.stdout.strip()
                        print(f"📋 Chrome 버전 확인: {version_output}")
                        return version_output
                except Exception:
                    pass
        
        return None
    except Exception as e:
        print(f"⚠️ Chrome 버전 확인 실패: {e}")
        return None

def get_driver(headless=False):
    global _driver
    if _driver is not None:
        try:
            if _driver.window_handles:
                print("✅ 기존 브라우저 세션에서 여는 중입니다.")
                return _driver
        except WebDriverException:
            _driver = None  # 기존 드라이버가 유효하지 않으면 None으로 설정

    # Chrome 버전 확인
    chrome_version = get_chrome_version()
    
    # chrome_path 변수 초기화
    chrome_path = None
    service = None
    
    # 프로필 디렉토리 초기화
    profile_dir = r"E:/selenium_profiles/naver_login_profile"
    
    # webdriver-manager를 사용하여 Chrome 버전에 맞는 ChromeDriver 자동 다운로드
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        print("🔍 webdriver-manager를 사용하여 ChromeDriver를 자동으로 다운로드합니다...")
        
        # Chrome 버전에서 메이저 버전 추출 (예: 142.0.7444.176 -> 142)
        chrome_major_version = None
        if chrome_version:
            try:
                chrome_major_version = chrome_version.split('.')[0]
                print(f"   Chrome 메이저 버전: {chrome_major_version}")
            except:
                pass
        
        chrome_path = ChromeDriverManager().install()
        print(f"✅ ChromeDriver 자동 다운로드 완료: {chrome_path}")
        
        # ChromeDriver 버전 확인 (경로에서 추출)
        if chrome_version:
            print(f"   Chrome 버전: {chrome_version}")
        
        # Service에 verbose 로그 추가 (디버깅용)
        service = Service(chrome_path)
        # verbose 로그는 기본적으로 비활성화 (너무 많은 출력 방지)
    except ImportError:
        print("⚠️ webdriver-manager가 설치되지 않았습니다. 수동 경로를 사용합니다...")
        # webdriver-manager가 없으면 기존 방식 사용
        chrome_paths = [
            "C:/chromedriver.exe",
            r"C:\chromedriver.exe",
            os.path.join(os.path.dirname(__file__), "chromedriver.exe"),
            "chromedriver.exe"  # PATH에서 찾기
        ]
        
        for path in chrome_paths:
            if os.path.exists(path):
                chrome_path = path
                print(f"✅ ChromeDriver 발견: {chrome_path}")
                break
        
        # Service 설정
        if chrome_path:
            try:
                # Selenium 4.x 방식: Service()에 직접 경로 전달
                service = Service(chrome_path)
            except TypeError:
                # 구버전 호환성: executable_path 사용
                service = Service(executable_path=chrome_path)
        else:
            print("⚠️ ChromeDriver를 찾을 수 없습니다. PATH에서 찾기를 시도합니다...")
            service = None  # PATH에서 자동으로 찾기
    except Exception as e:
        print(f"⚠️ webdriver-manager 사용 실패: {e}, 수동 경로를 시도합니다...")
        # webdriver-manager 실패 시 기존 방식 사용
        chrome_paths = [
            "C:/chromedriver.exe",
            r"C:\chromedriver.exe",
            os.path.join(os.path.dirname(__file__), "chromedriver.exe"),
            "chromedriver.exe"
        ]
        
        for path in chrome_paths:
            if os.path.exists(path):
                chrome_path = path
                print(f"✅ ChromeDriver 발견: {chrome_path}")
                break
        
        if chrome_path:
            try:
                service = Service(chrome_path)
            except TypeError:
                service = Service(executable_path=chrome_path)
        else:
            service = None

    options = Options()

    # 공통 옵션
    options.add_argument("--window-size=1920,3000")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--enable-unsafe-swiftshader")  # ✅ WebGL 문제 해결용
    options.add_argument("--no-sandbox")  # 모든 경우에 추가
    options.add_argument("--disable-dev-shm-usage")  # 모든 경우에 추가
    options.add_argument("--disable-software-rasterizer")  # 소프트웨어 래스터라이저 비활성화
    options.add_argument("--disable-extensions")  # 확장 프로그램 비활성화 (충돌 방지)
    # remote-debugging-port는 다른 Chrome 인스턴스와 충돌할 수 있으므로 제거하거나 다른 포트 사용
    # options.add_argument("--remote-debugging-port=9222")  # 디버깅 포트 설정

    # headless 여부에 따라 분기
    if headless:
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
    else:
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-features=site-per-process")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-infobars")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_experimental_option("detach", True)

    # ✅ 고정된 사용자 데이터 디렉토리 설정 (로그인 상태 유지용)
    try:
        os.makedirs(profile_dir, exist_ok=True)
        # 프로필 디렉토리 경로를 절대 경로로 변환
        profile_dir = os.path.abspath(profile_dir)
        options.add_argument(f"user-data-dir={profile_dir}")
        print(f"✅ 프로필 디렉토리 설정: {profile_dir}")
    except Exception as e:
        print(f"⚠️ 프로필 디렉토리 설정 실패: {e}")
        # 프로필 디렉토리 설정 실패 시 임시 디렉토리 사용
        import tempfile
        profile_dir = tempfile.mkdtemp(prefix="selenium_chrome_")
        options.add_argument(f"user-data-dir={profile_dir}")
        print(f"⚠️ 임시 프로필 디렉토리 사용: {profile_dir}")

    # ✅ 팝업/이미지/알림 설정 (한 번만 설정)
    prefs = {
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_setting_values.geolocation": 2,
        "profile.managed_default_content_settings.images": 1
    }
    options.add_experimental_option("prefs", prefs)

    # ✅ 드라이버 실행 (재시도 로직 포함)
    max_retries = 3
    for attempt in range(max_retries):
        try:
            if service:
                _driver = webdriver.Chrome(service=service, options=options)
            else:
                _driver = webdriver.Chrome(options=options)
            
            # 드라이버가 정상적으로 시작되었는지 확인
            _driver.get("about:blank")  # 간단한 페이지로 테스트
            print(f"✅ ChromeDriver 초기화 성공 (시도 {attempt + 1}/{max_retries})")
            break
            
        except SessionNotCreatedException as e:
            error_msg = str(e)
            print(f"❌ ChromeDriver 초기화 실패 (시도 {attempt + 1}/{max_retries}): {error_msg}")
            
            # 버전 불일치 에러인지 확인
            if "version" in error_msg.lower() or "supports Chrome version" in error_msg:
                print(f"⚠️ ChromeDriver와 Chrome 브라우저 버전이 일치하지 않습니다.")
                if chrome_version:
                    print(f"   현재 Chrome 버전: {chrome_version}")
                print(f"   💡 Chrome 브라우저를 최신 버전으로 업데이트하거나,")
                print(f"      ChromeDriver를 Chrome 버전에 맞게 다운로드하세요.")
            
            # "Chrome instance exited" 오류 처리
            if "Chrome instance exited" in error_msg:
                print(f"⚠️ Chrome 인스턴스가 시작 후 종료되었습니다.")
                print(f"   가능한 원인:")
                print(f"   1. 프로필 디렉토리 문제")
                print(f"   2. Chrome 옵션 충돌")
                print(f"   3. 다른 Chrome 인스턴스와의 충돌")
                print(f"   4. 권한 문제")
                
                # 프로필 디렉토리 재생성 시도
                if attempt < max_retries - 1:
                    try:
                        import shutil
                        if os.path.exists(profile_dir):
                            print(f"   🔄 프로필 디렉토리 정리 중...")
                            try:
                                shutil.rmtree(profile_dir, ignore_errors=True)
                                os.makedirs(profile_dir, exist_ok=True)
                                print(f"   ✅ 프로필 디렉토리 재생성 완료")
                            except Exception as profile_error:
                                print(f"   ⚠️ 프로필 디렉토리 정리 실패: {profile_error}")
                    except Exception:
                        pass
            
            if attempt < max_retries - 1:
                # Chrome 프로세스 종료 시도
                try:
                    import subprocess
                    subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"], 
                                 capture_output=True, timeout=5)
                    subprocess.run(["taskkill", "/F", "/IM", "chromedriver.exe"], 
                                 capture_output=True, timeout=5)
                    time.sleep(3)  # 프로세스 종료 대기 시간 증가
                    print("🔄 Chrome 프로세스 종료 후 재시도...")
                except Exception as cleanup_error:
                    print(f"⚠️ 프로세스 정리 실패: {cleanup_error}")
            else:
                default_path = "C:/chromedriver.exe"
                error_help = f"ChromeDriver 초기화 실패: {error_msg}\n"
                error_help += f"해결 방법:\n"
                error_help += f"1. Chrome 브라우저가 설치되어 있는지 확인\n"
                if chrome_version:
                    error_help += f"2. 현재 Chrome 버전: {chrome_version}\n"
                error_help += f"3. ChromeDriver 버전이 Chrome 브라우저 버전과 일치하는지 확인\n"
                error_help += f"4. Chrome 브라우저를 최신 버전으로 업데이트하세요\n"
                error_help += f"5. webdriver-manager가 설치되어 있는지 확인: pip install webdriver-manager\n"
                error_help += f"6. 다른 Chrome 인스턴스가 실행 중이면 종료 후 재시도"
                raise Exception(error_help)
        
        except Exception as e:
            print(f"❌ 예상치 못한 오류 (시도 {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                raise

    # ✅ 실행 로그 저장
    try:
        with open(LAUNCH_LOG, 'w', encoding='utf-8') as f:
            f.write(f"launch_time: {datetime.now().isoformat()}\n")
            f.write(f"start_url: {_driver.current_url if _driver.current_url else 'N/A'}\n")
            f.write(f"chrome_path: {chrome_path or 'PATH에서 자동 검색'}\n")
        print(f"📄 실행 정보 저장 완료: {LAUNCH_LOG}")
    except Exception as e:
        print(f"⚠️ 실행 정보 저장 실패: {e}")

    return _driver

def run_local_html_editor(title, content, ca_name, keyword, use_pinterest_image):
    # 1. 드라이버 옵션 설정
    options = Options()
    options.add_argument('--allow-file-access-from-files')  # 로컬 JS 접근 허용

    # 2. 드라이버 실행
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 10)

    try:
        # ca_name이 CATEGORY_LIST에 있는지 확인
        try:
            from prompt_functions import CATEGORY_LIST
            valid_ca_names = [item["ca_name"] for item in CATEGORY_LIST]
            
            if ca_name not in valid_ca_names:
                print(f"⚠️ 유효하지 않은 ca_name: {ca_name}")
                ca_name = "일반"  # 기본값 사용
                print(f"✅ 기본값으로 변경: {ca_name}")
            else:
                print(f"✅ 유효한 ca_name 확인: {ca_name}")
        except ImportError:
            print(f"⚠️ prompt_functions 모듈을 찾을 수 없어 ca_name 검증을 건너뜁니다: {ca_name}")

        # 3. 로컬 파일 경로 설정 및 로딩
        local_path = r"E:\Ai project\ver0.2.0.0\demo_html\gpt-v-0-7\dist\index.html"
        file_url = 'file:///' + local_path.replace('\\', '/')
        driver.get(file_url)
        time.sleep(2)  # 충분한 로딩 대기

        # 4. 제목 입력 (BMP 문자만 허용)
        para_input = driver.find_element(By.ID, "exampleFormControlTextarea")
        para_input.clear()
        para_input.send_keys(filter_bmp(title))
        time.sleep(1)  # 충분한 로딩 대기

        # 5. 본문 입력 전 이미지 GitHub URL 변환 (file:/// 및 ./images/* 모두 처리)
        try:
            from core.image_search import upload_image_to_github
            import re, urllib.parse
            
            modified_content = content
            github_url_map = {}
            
            # 5-1) file:/// 경로 업로드 및 치환
            file_urls = re.findall(r'src\s*=\s*"(file:\/\/\/[^\"]+)"', content)
            for furl in file_urls:
                try:
                    decoded = urllib.parse.unquote(furl.replace('file:///', ''))
                    local_path = decoded.replace('/', '\\')
                    if os.path.exists(local_path):
                        print(f"  ⏳ 파일 업로드: {local_path}")
                        github_url, _ = upload_image_to_github(local_path)
                        if github_url:
                            modified_content = modified_content.replace(furl, github_url)
                            print(f"  ✅ {os.path.basename(local_path)} → {github_url}")
                    else:
                        print(f"  ⚠️ 로컬 경로 없음: {local_path}")
                except Exception as e:
                    print(f"  ❌ file:/// 처리 실패: {str(e)[:80]}")
            
            # 5-2) ./images/filename 형식 처리 (현재 글 폴더 내 상대경로 가정)
            rel_imgs = re.findall(r'src\s*=\s*"\.?\/images\/([^\"]+)"', content)
            if rel_imgs:
                # 포스트 루트 추정: post_datas 안에서 이미지가 있는 폴더 탐색
                post_root = os.path.join(_project_root, 'post_datas')
                candidates = []
                for root, _, files in os.walk(post_root):
                    if os.path.basename(root) == 'images':
                        candidates.append(root)
                for img_name in rel_imgs:
                    for cand in candidates:
                        local_path = os.path.join(cand, img_name)
                        if os.path.exists(local_path):
                            try:
                                print(f"  ⏳ 상대경로 업로드: {local_path}")
                                github_url, _ = upload_image_to_github(local_path)
                                if github_url:
                                    modified_content = modified_content.replace(f"./images/{img_name}", github_url)
                                    modified_content = modified_content.replace(f"images/{img_name}", github_url)
                                    print(f"  ✅ {img_name} → {github_url}")
                                    break
                            except Exception as e:
                                print(f"  ❌ 상대경로 처리 실패({img_name}): {str(e)[:80]}")
            
            content = modified_content
        except ImportError:
            print("⚠️ upload_image_to_github 함수를 찾을 수 없습니다. 로컬 경로로 진행합니다.")
        except Exception as e:
            print(f"⚠️ GitHub 업로드 중 오류: {e}")
        
        # 5. 본문 입력 (BMP 문자만 허용)
        keyword_input = driver.find_element(By.ID, "exampleFormControlTextarea1")
        keyword_input.clear()
        keyword_input.send_keys(filter_bmp(content))
        time.sleep(5)

        # 6. ca_name 입력 (CATEGORY_LIST의 유효한 값만 전달, BMP 문자만 허용)
        keyword_input = driver.find_element(By.ID, "exampleFormControlTextarea2")
        keyword_input.clear()
        keyword_input.send_keys(filter_bmp(ca_name))
        time.sleep(1)  # 충분한 로딩 대기

        keyword_input = driver.find_element(By.ID, "exampleFormControlTextarea2_1")
        keyword_input.clear()
        keyword_input.send_keys(filter_bmp(keyword))

        time.sleep(3)

        textarea = driver.find_element(By.ID, "exampleFormControlTextarea3_1")
        value = textarea.get_attribute("value")
        print("📋 복사된 HTML:\n", value)
        
        # 6. "출력만 보기" 버튼 클릭 (스크롤 + JS 클릭)
        fullscreen_btn = wait.until(EC.presence_of_element_located((By.ID, "fullscreenOutput")))
        driver.execute_script("arguments[0].scrollIntoView(true);", fullscreen_btn)
        time.sleep(3)
        driver.execute_script("arguments[0].click();", fullscreen_btn)
        print("✅ 출력만 보기 버튼 클릭 완료")
        time.sleep(3)
        
        # 7. outputArea 요소 클릭 후 Ctrl+A → Ctrl+C
        output_area = wait.until(EC.presence_of_element_located((By.ID, "outputArea")))
        driver.execute_script("arguments[0].scrollIntoView(true);", output_area)
        output_area.click()
        time.sleep(3)

        actions = ActionChains(driver)
        actions.key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).perform()
        time.sleep(3)
        actions.key_down(Keys.CONTROL).send_keys('c').key_up(Keys.CONTROL).perform()
        time.sleep(3)
        print("✅ outputArea 전체 복사 완료 (Ctrl+A → Ctrl+C)")

    except Exception as e:
        print("❌ 예외 발생:", e)
        return None  # 예외 발생 시 None 반환

    finally:
        # 9. 드라이버 종료
        driver.quit()

    return value  # 성공 시 복사된 HTML 반환

def wait_for_manual_login(driver):
    print("🔐 네이버 로그인 페이지를 열었습니다.")
    print("✅ 로그인 후, 엔터 키를 한 번 눌러주세요.")
    #input("▶ 로그인 완료 후 엔터: ")
    print("✅ 사용자 로그인 완료 감지됨.")

def is_logged_in(driver, naver_id):
    driver.get(f"https://blog.naver.com/{naver_id}/postwrite")
    time.sleep(0.5)  # 2 → 0.5초

    # 로그인한 경우에는 글쓰기 에디터가 보이고, 로그인 안 하면 로그인 페이지로 리다이렉트됨
    current_url = driver.current_url.lower()
    
    # 로그인 페이지로 이동했으면 로그인 안 된 상태
    if "nidlogin" in current_url:
        print("❌ 로그인 상태 아님 (redirected to login)")
        return False

    # 글쓰기 에디터 요소가 로드되었는지 확인 (타임아웃 추가)
    try:
        WebDriverWait(driver, 3).until(  # find_element → WebDriverWait로 변경
            EC.presence_of_element_located((By.CSS_SELECTOR, "[contenteditable='true']"))
        )
        print("✅ 로그인 상태 확인됨")
        return True
    except TimeoutException:
        print("❌ 로그인된 것 같지만 에디터 없음")
        return False


def click_element_by_text(driver, tag: str, text: str, timeout=3):
    """주어진 태그와 정확한 텍스트를 가진 요소를 찾아 클릭합니다."""
    try:
        xpath = f"//{tag}[normalize-space(text())='{text}']"
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        element.click()
        print(f"✅ '{text}' 클릭 완료")
        return True
    except Exception as e:
        print(f"❌ '{text}' 클릭 실패: {e}")
        return False

def publish_post(driver):
    try:
        # 1. '발행' 버튼 (첫 번째 단계) 클릭
        click_element_by_text(driver, "button", "발행", timeout=3)
        time.sleep(0.5)  # 카테고리 목록 로드 대기

        # 2. 카테고리 '공지사항' 클릭
        click_element_by_text(driver, "span", "공지사항", timeout=3)
        time.sleep(0.3)  # 카테고리 펼침 대기

        # 3. 카테고리 'NPC' 클릭
        click_element_by_text(driver, "span", "NPC", timeout=3)
        time.sleep(0.3)  # 선택 처리 대기

        # 4. 최종 '발행' 버튼 클릭 (data-testid가 있는 버튼이 아닌 텍스트 "발행")
        click_element_by_text(driver, "button", "발행", timeout=5)
        print("🚀 게시물 발행 완료")
    except Exception as e:
        print(f"❌ 게시물 발행 중 오류 발생: {e}")


def _escape_for_xpath(value: str) -> str:
    return value.replace("'", "\\'")


def _generate_category_xpaths(name: str) -> list[str]:
    trimmed = name.strip()
    plain = _escape_for_xpath(trimmed)
    lower = _escape_for_xpath(trimmed.lower())
    xpaths = []

    if plain:
        xpaths.extend(
            [
                f"//label[normalize-space(text())='{plain}']",
                f"//span[normalize-space(text())='{plain}']",
                f"//button[normalize-space(text())='{plain}']",
            ]
        )
    if lower:
        xpaths.extend(
            [
                f"//label[translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')='{lower}']",
                f"//span[translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')='{lower}']",
                f"//button[translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')='{lower}']",
                f"//label[contains(translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), '{lower}')]",
                f"//span[contains(translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), '{lower}')]",
                f"//button[contains(translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), '{lower}')]",
                f"//label[contains(@for, '{lower}')]",
            ]
        )

    return xpaths


def select_category_by_name(driver, wait, naver_id, ca_name, fallback=None) -> bool:
    """카테고리 선택 (최적화된 버전)"""
    names = []
    if ca_name and ca_name.strip():
        names.append(ca_name.strip())
    if fallback and fallback.strip():
        names.append(fallback.strip())
    
    if not names:
        return False
    
    last_exception = None

    for name in names:
        xpaths = _generate_category_xpaths(name)
        for xpath in xpaths:
            try:
                # 타임아웃을 3초로 단축 (더 빠른 응답)
                element = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(0.1)  # 0.2 → 0.1초로 단축
                driver.execute_script("arguments[0].click();", element)
                time.sleep(0.1)  # 0.2 → 0.1초로 단축
                log_action(f"✅ [{naver_id}] 카테고리 '{name}' 선택 완료")
                return True
            except Exception as exc:
                last_exception = exc
                continue

    log_action(
        f"⚠️ [{naver_id}] 카테고리 선택 실패: {type(last_exception).__name__} (대상: {ca_name})"
    )
    return False


def click_publish_button_with_retry(driver, wait, naver_id, retries=2) -> bool:
    """최종 발행 버튼 클릭 (최적화된 버전)"""
    last_exception = None
    for attempt in range(1, retries + 1):
        try:
            # 타임아웃을 5초로 단축 (10초는 너무 김)
            publish_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='seOnePublishBtn']"))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", publish_button)
            time.sleep(0.1)  # 0.3 → 0.1초로 단축
            publish_button.click()
            log_action(f"✅ [{naver_id}] 최종 발행 버튼 클릭 완료")
            return True
        except (TimeoutException, StaleElementReferenceException) as exc:
            last_exception = exc
            if attempt < retries:
                log_action(
                    f"⚠️ [{naver_id}] 발행 시도 {attempt} 실패, {0.2}초 후 재시도..."
                )
                time.sleep(0.2)  # 0.5 → 0.2초로 단축
            continue

    log_action(f"❌ [{naver_id}] 최종 발행 버튼 클릭 실패: {type(last_exception).__name__}")
    return False

def filter_bmp(text):
    return ''.join(c for c in text if ord(c) <= 0xFFFF)

def has_text_in_image(url):
    try:
        response = requests.get(url, timeout=5)
        image = Image.open(BytesIO(response.content))
        text = pytesseract.image_to_string(image, lang='eng+kor')
        
        cleaned = re.sub(r'[^가-힣a-zA-Z0-9]', '', text)  # 의미 있는 문자만 남김
        print("🔍 OCR 추출 결과:", cleaned)

        return len(cleaned) > 5
    except Exception as e:
        print(f"🛑 OCR 예외: {e}")
        return True  # 예외시 보수적으로 "텍스트 있음" 처리

def post_to_naver(naver_id, title, content, ca_name, keyword, use_pinterest_image=False, use_bing_image=False, auto_quit=True, check_login=True):
    """
    네이버 블로그에 포스트를 업로드하는 함수
    
    Args:
        naver_id: 네이버 블로그 ID
        title: 포스트 제목
        content: 포스트 내용 (HTML)
        ca_name: 카테고리 이름
        keyword: 키워드
        use_pinterest_image: Pinterest 이미지 사용 여부
        use_bing_image: Bing 이미지 사용 여부
        auto_quit: 자동 종료 여부
        check_login: 로그인 상태 확인 여부 (True면 확인 후 수동 로그인, False면 확인 안함)
    """
    driver = get_driver()
    wait = WebDriverWait(driver, 20)
    actions = ActionChains(driver)

    query = urllib.parse.quote(title)
    youtube_url = f"https://www.youtube.com/results?search_query={query}"

    try:
        driver = get_driver()
        wait = WebDriverWait(driver, 20)
        actions = ActionChains(driver)

        # ✅ 로그인 상태 확인 (옵션이 활성화된 경우만)
        if check_login:
            if not is_logged_in(driver, naver_id):
                # 로그인 페이지로 이동
                print("🔐 로그인이 필요합니다. 수동 로그인 페이지를 엽니다.")
                driver.get("https://nid.naver.com/nidlogin.login")
                wait_for_manual_login(driver)
        else:
            print("ℹ️ 로그인 상태 확인을 건너뜁니다.")

        time.sleep(1)

        # 1. GPT로 감성 문장 + 해시태그 생성 extract_hashtags_json(content)
        result = content
        print(f"✅ 감성 문장 및 해시태그 생성 결과: {result}")

        # 2. 분리해서 변수에 담기
        formatted_html = result["formatted_html"]
        hashtags = result["hashtags"]

        # 3. 최종 HTML 조합
        final_content = formatted_html + "<br>" + hashtags + "<br>"
        
        # 3-1. 네이버 안전 HTML로 정리 (div/section 제거, 과도한 속성 제거, 문단 줄바꿈 보장)
        def sanitize_for_naver(html: str) -> str:
            import re
            s = html
            # style/class 등 속성 제거 (img의 src 제외)
            s = re.sub(r'<(\w+)([^>]*)>', lambda m: re.sub(r'\s+(?:style|class|id)="[^"]*"', '', m.group(0)), s)
            # div/section/article를 p로 대체
            s = re.sub(r'<\s*(div|section|article)[^>]*>', '<p>', s, flags=re.IGNORECASE)
            s = re.sub(r'<\s*\/\s*(div|section|article)\s*>', '</p>', s, flags=re.IGNORECASE)
            # 연속 공백 <br> 3개 이상 → 2개
            s = re.sub(r'(?:<br\s*\/?>\s*){3,}', '<br><br>', s, flags=re.IGNORECASE)
            # </p> 뒤에 줄바꿈 보장
            s = re.sub(r'<\/p>\s*(?!<br\b)', '</p><br>', s, flags=re.IGNORECASE)
            return s
        
        final_content = sanitize_for_naver(final_content)
        print(f"✅ 최종 HTML 내용: {final_content[:200]}...")  # 처음 200자만 출력

        # ✅ 이모지 제거
        final_content = filter_bmp(final_content)
        print(f"✅ 이모지 제거 후 내용: {final_content[:200]}...")

        title = filter_bmp(title)
        # 제목과 본문에서 *, # 특수문자 전부 제거 (다음 블로그 자동 게시에도 적용)
        import re
        def remove_star_hash(text):
            return re.sub(r'[\*#]', '', text)
        title = remove_star_hash(title)
        final_content = remove_star_hash(final_content)

        # keyboard_blocker 사용 (있으면)
        if KEYBOARD_BLOCKER_AVAILABLE:
            keyboard_blocker.start_overlay_only()

        # 4. GPT로 카테고리 추천 받기 (선택적)
        try:
            from prompt_functions import build_category_prompt_with_system
            system_prompt, user_prompt, category_list = build_category_prompt_with_system(title, final_content)
            # ✅ Ollama API 호출 (OpenAI 대체)
            recommended_category = call_ollama_api_category(system_prompt, user_prompt, model="gpt-oss:120b-cloud")
            # 추천된 카테고리가 CATEGORY_LIST에 있는지 확인
            valid_ca_names = [item["ca_name"] for item in category_list]
            if recommended_category in valid_ca_names:
                ca_name = recommended_category
                print(f"🤖 Ollama 카테고리 추천: {ca_name}")
            else:
                print(f"⚠️ 추천된 카테고리가 유효하지 않음: {recommended_category}, 기존값 사용: {ca_name}")
        except Exception as e:
            print(f"⚠️ 카테고리 추천 실패: {e}, 기존값 사용: {ca_name}")

        # 5. 에디터 실행 및 자동 복사
        final_content = run_local_html_editor(title, final_content, ca_name, keyword, use_pinterest_image)
        time.sleep(1)

        # 글쓰기 페이지 로드 (재시도: 10초 대기 후 3회)
        page_loaded = False
        for attempt in range(1, 4):
            try:
                driver.get(f"https://blog.naver.com/{naver_id}/postwrite")
                time.sleep(2)  # 페이지 로드 대기
                
                # 에디터 요소 확인 (로드 확인)
                editor_div = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[contenteditable='true']")))
                print(f"✅ 글쓰기 페이지 로드 성공 (시도 {attempt}회)")
                page_loaded = True
                break
            except TimeoutException:
                if attempt < 3:
                    print(f"⚠️ 글쓰기 페이지 로드 실패, 10초 후 재시도... (시도 {attempt}/3)")
                    time.sleep(10)
                else:
                    print(f"❌ 글쓰기 페이지 로드 실패 (3회 시도 모두 실패)")
                    page_loaded = False
        
        if not page_loaded:
            log_action("❌ 글쓰기 페이지를 열 수 없습니다")
            return False

        # 본문 입력
        try:
            editor_div = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[contenteditable='true']")))

            driver.execute_script("arguments[0].scrollIntoView(true);", editor_div)
            time.sleep(0.3)

            # ✅ 본문 입력 (단어 단위 처리)
            ActionChains(driver).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
            time.sleep(5)
            
            # 이미지 로딩 대기 (준비중 상태 해제)
            print("⏳ 이미지 로딩 중... (최대 15초)")
            for i in range(15):
                try:
                    # "준비중" 텍스트가 없어질 때까지 대기
                    if "준비중" not in driver.page_source:
                        print(f"✅ 이미지 로딩 완료 ({i+1}초)")
                        break
                    time.sleep(1)
                except:
                    pass
            
            time.sleep(2)  # 추가 안정화 대기

            log_action("✅ 본문 입력 완료")

            # 전체 선택 후 글자 크기 변경
            actions.key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).perform()
            time.sleep(0.3)

            # 1. 정렬 드롭다운 열기 버튼 클릭
            if naver_id == "dbghwns2":
                try:
                    align_dropdown_btn = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "button.se-align-center-toolbar-button"))
                    )
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", align_dropdown_btn)
                    time.sleep(0.3)
                    driver.execute_script("arguments[0].click();", align_dropdown_btn)
                    print("✅ 정렬 드롭다운 열기 버튼 클릭 완료")
                except Exception as e:
                    print("❌ 정렬 드롭다운 클릭 실패:", repr(e))

            # 옵션이 로드됐는지 확인 (진단용)
            html = driver.page_source
            if 'data-value="left"' in html:
                print("ℹ️ 정렬 옵션이 로드된 것으로 보입니다.")

            # 2. 왼쪽 정렬 버튼 클릭
            try:
                align_left_btn = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "button.se-toolbar-option-align-left-button"))
                )
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", align_left_btn)
                time.sleep(0.3)
                driver.execute_script("arguments[0].click();", align_left_btn)
                print("✅ 왼쪽 정렬 버튼 클릭 완료")
            except Exception as e:
                print("❌ 왼쪽 정렬 클릭 실패:", repr(e))

            # 사이드바 닫기 (옵션 - 더 빠른 타임아웃)
            try:
                close_btn = WebDriverWait(driver, 2).until(  # 5 → 2초로 단축
                    EC.element_to_be_clickable((By.CLASS_NAME, "se-sidebar-close-button"))
                )
                driver.execute_script("arguments[0].click();", close_btn)
                time.sleep(0.1)  # 짧은 대기
                log_action("✅ 사이드바 닫기 완료")
            except Exception as e:
                # 사이드바 닫기는 선택사항이므로 실패해도 계속 진행
                log_action(f"ℹ️ 사이드바 닫기 스킵 (선택사항): {type(e).__name__}")

        except Exception as e:
            log_action(f"❌ 본문 입력 실패: {repr(e)}")
            driver.save_screenshot("editor_fail.png")
            return


        # ✅ 제목 입력
        try:
            title_div = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.se-title-text p.se-text-paragraph")))
            driver.execute_script("arguments[0].focus();", title_div)
            title_div.click()
            time.sleep(0.2)  # 0.5 → 0.2초로 단축

            for char in title:
                actions.send_keys(char).perform()
                time.sleep(0.005)  # 0.01 → 0.005초로 단축 (더 빠르게)

            log_action("✅ 제목 입력 완료")
            actions.send_keys(Keys.TAB).perform()
            time.sleep(0.2)  # 0.5 → 0.2초로 단축
        except Exception as e:
            log_action(f"❌ 제목 입력 실패: {e}")

        # ✅ 4. 발행 설정 → 카테고리 선택
        if naver_id == "dbghwns2":
            try:
                publish_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.publish_btn__m9KHH")))
                publish_btn.click()
                log_action(f"📰 [{naver_id}] 발행 버튼 클릭 완료")
                time.sleep(0.3)  # 1 → 0.3초로 단축

                stopmatch_label = wait.until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//span[@data-testid='categoryItemText_125' and text()='공지사항']")
                    )
                )
                stopmatch_label.click()
                log_action(f"✅ [{naver_id}] 카테고리 '공지사항' 클릭 완료")
                time.sleep(0.3)  # 1 → 0.3초로 단축, 추가 대기는 함수에서 처리

                select_category_by_name(driver, wait, naver_id, ca_name, fallback="NPC")

                click_publish_button_with_retry(driver, wait, naver_id)

            except Exception as e:
                log_action(f"❌ [{naver_id}] 전체 발행 프로세스 실패: {repr(e)}")

        if naver_id == "dbghwns4":
            try:
                publish_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.publish_btn__m9KHH")))
                publish_btn.click()
                log_action(f"📰 [{naver_id}] 발행 버튼 클릭 완료")
                time.sleep(0.3)  # 1 → 0.3초

                # 상위 카테고리 '공지사항'
                try:
                    stopmatch_label = WebDriverWait(driver, 5).until(  # 기본 wait → 5초
                        EC.element_to_be_clickable(
                            (By.XPATH, "//span[@data-testid='categoryItemText_18' and text()='공지사항']")
                        )
                    )
                    parent_button = stopmatch_label.find_element(By.XPATH, "./ancestor::button")
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", parent_button)
                    time.sleep(0.1)  # 0.3 → 0.1초
                    driver.execute_script("arguments[0].click();", parent_button)
                    log_action(f"✅ [{naver_id}] 카테고리 '공지사항' 클릭 완료")
                    time.sleep(0.3)  # 1 → 0.3초
                except Exception as e:
                    log_action(f"⚠️ [{naver_id}] '공지사항' 선택 실패: {repr(e)}")

                # NPC 카테고리
                try:
                    npc_label = WebDriverWait(driver, 5).until(  # find_element → WebDriverWait
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'label[for="19_NPC"]'))
                    )
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", npc_label)
                    time.sleep(0.1)  # 0.2 → 0.1초
                    driver.execute_script("arguments[0].click();", npc_label)
                    log_action(f"✅ [{naver_id}] NPC 카테고리 선택 완료")
                except Exception as e:
                    log_action(f"⚠️ [{naver_id}] NPC 카테고리 선택 실패: {repr(e)}")

                # 최종 발행 버튼
                try:
                    publish_button = WebDriverWait(driver, 5).until(  # 10 → 5초
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='seOnePublishBtn']"))
                    )
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", publish_button)
                    time.sleep(0.1)  # 0.3 → 0.1초
                    driver.execute_script("arguments[0].click();", publish_button)
                    log_action(f"✅ [{naver_id}] 최종 발행 버튼 클릭 완료")

                    sys.exit()
                except Exception as e:
                    log_action(f"❌ [{naver_id}] 발행 버튼 클릭 실패: {repr(e)}")

            except Exception as e:
                log_action(f"❌ [{naver_id}] 전체 발행 프로세스 실패: {repr(e)}")

    except Exception as e:
        log_action(f"❌ 전체 예외 발생: {repr(e)}")
        return content  # 실패 시 원본 반환

    return final_content  # 성공 시 최종 HTML 반환


if __name__ == "__main__":

    # result = extract_hashtags_json('엔터스포츠LIVE경제쇼핑투데이구독언론사연합뉴스비트코인, 사상 최초로 12만달러선 돌파초대내각 청문회 파행으로 얼룩…국힘 "갑질왕"·與 "인청내')
    # print(result)
    class MockUI:
        def __init__(self):
            # Mock user inputs
            self.naver_id_input = "dbghwns2"  # Simulating the input
            self.pinterest_checkbox = True  # Simulating the Pinterest checkbox (checked)
            self.bing_checkbox = True  # Simulating the Bing checkbox (checked)

        # Simulate getting the text from the input field
        def naver_id_input_text(self):
            return self.naver_id_input.strip()

        # Simulate checking the Pinterest checkbox
        def pinterest_checkbox_isChecked(self):
            return self.pinterest_checkbox

        # Simulate checking the Bing checkbox
        def bing_checkbox_isChecked(self):
            return self.bing_checkbox

    # Instantiate the mock UI
    mock_ui = MockUI()

    # Test data
    title = "테스트 제목"
    content = "여기에는 테스트 내용이 들어갑니다."
    ca_name = "테스트 카테고리"
    keyword = "테스트 키워드"
    final_content = "#태그#태그#태그"
    # Get values from the mock UI
    naver_id = mock_ui.naver_id_input_text()  # Mocked Naver ID
    use_pinterest_image = mock_ui.pinterest_checkbox_isChecked()  # Pinterest checkbox status
    use_bing_image = mock_ui.bing_checkbox_isChecked()  # Bing checkbox status

    # ✅ 인자 추가하여 호출
    from naver_auto_writer import post_to_naver


    # Testing with additional values
    test_naver_id = "dbghwns2"  # 또는 "dbghwns4"
    test_title = "GPT 테스트 제목"
    test_content = "이것은 본문 내용 테스트입니다.\n\nAI가 자동으로 업로드합니다."
    test_ca_name = "테스트카테고리"
    test_keyword = "주술회전 사멸회유"
    post_to_naver(test_naver_id, test_title, test_content, test_ca_name, test_keyword)
    #run_local_html_editor(title, final_content, ca_name, keyword, use_pinterest_image)