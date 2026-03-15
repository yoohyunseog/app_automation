# -*- coding: utf-8 -*-
"""
네이버 블로그 업로드 모듈
네이버 블로그에 콘텐츠를 업로드하는 기능을 제공합니다.
"""
import os
from datetime import datetime
import traceback

def log_action(title, message, status):
    """로깅 함수 (간단한 콘솔 로그)"""
    status_emoji = {
        "success": "✅",
        "warning": "⚠️",
        "error": "❌",
        "process": "🔄",
        "start": "🚀"
    }
    emoji = status_emoji.get(status, "ℹ️")
    print(f"{emoji} [{title}] {message}")

class NaverBlogUploader:
    """네이버 블로그 업로드 클래스"""
    
    def __init__(self, config, sanitize_and_fix_links_func=None, chat_log_append_func=None):
        """
        초기화
        
        Args:
            config (dict): 설정 정보
            sanitize_and_fix_links_func (callable): 링크 정리 함수 (선택)
            chat_log_append_func (callable): 채팅 로그 출력 함수 (선택)
        """
        self.config = config
        self.sanitize_and_fix_links = sanitize_and_fix_links_func
        self.chat_log_append = chat_log_append_func or (lambda x: None)

    def get_naver_id(self):
        """네이버 ID 가져오기 (설정 파일 > 환경변수 > 기본값)"""
        naver_id = self.config.get("naver_id", "").strip()
        
        # 설정 파일에 없으면 환경변수에서 가져오기
        return naver_id

import os
from datetime import datetime
import traceback


def log_action(title, message, status):
    """로깅 함수 (간단한 콘솔 로그)"""
    status_emoji = {
        "success": "✅",
        "warning": "⚠️",
        "error": "❌",
        "process": "🔄",
        "start": "🚀"
    }
    emoji = status_emoji.get(status, "ℹ️")
    print(f"{emoji} [{title}] {message}")


class NaverBlogUploader:
    """네이버 블로그 업로드 클래스"""
    
    def __init__(self, config, sanitize_and_fix_links_func=None, chat_log_append_func=None):
        """
        초기화
        
        Args:
            config (dict): 설정 정보
            sanitize_and_fix_links_func (callable): 링크 정리 함수 (선택)
            chat_log_append_func (callable): 채팅 로그 출력 함수 (선택)
        """
        self.config = config
        self.sanitize_and_fix_links = sanitize_and_fix_links_func
        self.chat_log_append = chat_log_append_func or (lambda x: None)
    
    def get_naver_id(self):
        """네이버 ID 가져오기 (설정 파일 > 환경변수 > 기본값)"""
        naver_id = self.config.get("naver_id", "").strip()
        
        # 설정 파일에 없으면 환경변수에서 가져오기
        if not naver_id:
            naver_id = os.getenv("NAVER_ID", "").strip()
        
        # 환경변수에도 없으면 기본값 사용
        if not naver_id:
            # 기본 네이버 ID (사용자가 변경 가능)
            naver_id = "dbghwns2"  # 기본값
            info_msg = f"ℹ️ 네이버 ID가 설정되지 않아 기본값을 사용합니다: {naver_id}\n"
            info_msg += "💡 다른 ID를 사용하려면 설정 파일(gpt_blog_config.json)에 'naver_id' 필드를 추가하거나\n"
            info_msg += "   환경변수 NAVER_ID를 설정하세요.\n"
            info_msg += "   예: \"naver_id\": \"your_naver_id\"\n"
            self.chat_log_append(info_msg)
            print(f"ℹ️ 네이버 ID가 설정되지 않아 기본값을 사용합니다: {naver_id}")
            print("💡 다른 ID를 사용하려면 설정 파일(gpt_blog_config.json)에 'naver_id' 필드를 추가하거나")
            print("   환경변수 NAVER_ID를 설정하세요.")
            print("   예: \"naver_id\": \"your_naver_id\"")
        
        return naver_id
    
    def save_to_file_fallback(self, title, content, ca_name_value, keyword_for_naver):
        """naver_auto_writer 모듈이 없을 때 대체 방법: 파일로 저장"""
        self.chat_log_append("ℹ️ naver_auto_writer 모듈이 없어 파일로 저장합니다. (MySQL 저장은 계속 진행)\n")
        print("ℹ️ naver_auto_writer 모듈이 없어 파일로 저장합니다. (MySQL 저장은 계속 진행)")
        print("📁 대체 방법: 파일로 저장")
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"naver_upload_{timestamp}.html"
            
            # HTML 파일로 저장
            html_content = f"""<!DOCTYPE html>
                            <html>
                            <head>
                                <meta charset="UTF-8">
                                <title>{title}</title>
                            </head>
                            <body>
                                <h1>{title}</h1>
                                <p><strong>카테고리:</strong> {ca_name_value}</p>
                                <p><strong>키워드:</strong> {keyword_for_naver}</p>
                                <hr>
                                {content}
                            </body>
                            </html>
                            """
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.chat_log_append(f"✅ 대체 업로드 완료: {filename}\n")
            print(f"✅ 대체 업로드 완료: {filename}")
            return True
            
        except Exception as e:
            self.chat_log_append(f"❌ 대체 업로드 실패: {str(e)}\n")
            print(f"❌ 대체 업로드 실패: {str(e)}")
            return False
    
    def upload_to_naver(self, title, content, category, keyword, bo_table_value="free", ca_name_value="일반"):
        """
        네이버 블로그에 업로드하는 함수
        
        Args:
            title (str): 글 제목
            content (str): 글 내용 (HTML 형식)
            category (str): 카테고리
            keyword (str): 키워드
            bo_table_value (str): 게시판 테이블 (기본값: "free")
            ca_name_value (str): 카테고리 이름 (기본값: "일반")
            
        Returns:
            bool: 업로드 성공 여부
        """
        if not self.config.get("naver_enabled", False):
            log_action("네이버 업로드 건너뜀", "네이버 업로드가 비활성화되어 있음", "warning")
            return False
        
        log_action("네이버 블로그 업로드 시작", f"제목: {title[:50]}..., 카테고리: {category}, 키워드: {keyword}", "process")
        self.chat_log_append("📝 네이버 블로그에 업로드 중...\n")
        print("📝 네이버 블로그에 업로드 중...")
        
        try:
            # naver_auto_writer 모듈 import 시도
            post_to_naver = None
            try:
                from writers.naver_auto_writer import post_to_naver
                print("✅ naver_auto_writer 모듈 import 성공!")
            except ImportError as import_error:
                self.chat_log_append(f"⚠️ naver_auto_writer 모듈 import 실패: {import_error}\n")
                print(f"⚠️ naver_auto_writer 모듈 import 실패: {import_error}")
                print("⚠️ 대체 업로드 방법을 사용합니다.")
                post_to_naver = None
            
            # image_search 모듈 import 시도 (선택적)
            image_search_available = False
            try:
                import core.image_search as image_search
                image_search_available = True
                print("✅ image_search 모듈 import 성공!")
            except ImportError as import_error:
                print(f"⚠️ image_search 모듈 import 실패: {import_error}")
                print("⚠️ 이미지 검색 기능 없이 업로드를 진행합니다.")
                image_search_available = False

            # 네이버 ID 가져오기
            naver_id = self.get_naver_id()
            
            # 이미지 소스 설정에 따라 플래그 설정
            image_source = self.config.get("image_source", "bing")
            use_pinterest_image = (image_source == "pinterest")
            use_bing_image = (image_source == "bing" or image_source == "bing_sora" or image_source == "bing + sora")

            print(f"🔧 네이버 업로드 설정:")
            print(f"   - 네이버 ID: {naver_id}")
            print(f"   - 제목: {title}")
            print(f"   - 카테고리: {category}")
            print(f"   - 키워드: {keyword}")
            print(f"   - Pinterest 이미지: {use_pinterest_image}")
            print(f"   - Bing 이미지: {use_bing_image}")

            print(f"🔧 카테고리 설정:")
            print(f"   - bo_table: {bo_table_value}")
            print(f"   - ca_name: {ca_name_value}")
            
            # 네이버 업로드용 키워드 길이 제한 (100자 내외)
            keyword_for_naver = keyword.strip()
            if len(keyword_for_naver) > 100:
                keyword_for_naver = keyword_for_naver[:100]
                self.chat_log_append(f"🔧 키워드가 100자를 초과하여 잘렸습니다: {keyword_for_naver}\n")
                print(f"🔧 키워드가 100자를 초과하여 잘렸습니다: {keyword_for_naver}")
            
            # 네이버 업로드 함수 호출 (ca_name 사용)
            if post_to_naver:
                print("🚀 post_to_naver 함수 호출 중...")
                print(f"   - 사용할 네이버 ID: {naver_id}")
                # 로그인 상태 확인 옵션 가져오기
                check_login = self.config.get("check_naver_login", True)
                print(f"   - 로그인 상태 확인: {'활성화' if check_login else '비활성화'}")
                
                # 포스팅 전에 콘텐츠의 링크를 설정에 맞게 한 번 더 교체
                if self.sanitize_and_fix_links:
                    content = self.sanitize_and_fix_links(content)
                    print(f"🔧 [포스팅 전 링크 처리] 콘텐츠 길이: {len(content)}자")
                
                try:
                    uploaded_content = post_to_naver(
                        naver_id,
                        title,
                        content,
                        ca_name_value,  # category 대신 ca_name 사용
                        keyword_for_naver,
                        use_pinterest_image,
                        use_bing_image,
                        auto_quit=True,
                        check_login=check_login
                    )

                    if uploaded_content:
                        self.chat_log_append("✅ 네이버 블로그에 업로드 완료!\n")
                        print("✅ 네이버 블로그에 업로드 완료!")
                        print(f"📄 업로드된 내용 길이: {len(uploaded_content)}자")
                        return True
                    else:
                        self.chat_log_append("⚠️ 네이버 블로그 업로드 실패 (MySQL 저장은 계속 진행)\n")
                        print("⚠️ 네이버 블로그 업로드 실패 (MySQL 저장은 계속 진행)")
                        return True  # MySQL 저장은 계속 진행
                except Exception as e:
                    self.chat_log_append(f"⚠️ 네이버 블로그 업로드 중 오류 발생: {str(e)} (MySQL 저장은 계속 진행)\n")
                    print(f"⚠️ 네이버 블로그 업로드 중 오류 발생: {str(e)} (MySQL 저장은 계속 진행)")
                    traceback.print_exc()
                    return True  # MySQL 저장은 계속 진행
            else:
                # naver_auto_writer 모듈이 없을 때 대체 방법: 파일로 저장
                return self.save_to_file_fallback(title, content, ca_name_value, keyword_for_naver)
                
        except Exception as e:
            self.chat_log_append(f"❌ 네이버 업로드 오류: {str(e)}\n")
            print(f"❌ 네이버 업로드 오류: {str(e)}")
            traceback.print_exc()
            # 오류가 발생해도 MySQL 저장은 계속 진행
            return True


# 편의 함수: 직접 호출 가능한 래퍼
def upload_to_naver_blog(config, title, content, category, keyword, 
                         bo_table_value="free", ca_name_value="일반",
                         sanitize_and_fix_links_func=None, chat_log_append_func=None):
    """
    네이버 블로그 업로드 편의 함수
    
    Args:
        config (dict): 설정 정보
        title (str): 글 제목
        content (str): 글 내용 (HTML 형식)
        category (str): 카테고리
        keyword (str): 키워드
        bo_table_value (str): 게시판 테이블 (기본값: "free")
        ca_name_value (str): 카테고리 이름 (기본값: "일반")
        sanitize_and_fix_links_func (callable): 링크 정리 함수 (선택)
        chat_log_append_func (callable): 채팅 로그 출력 함수 (선택)
        
    Returns:
        bool: 업로드 성공 여부
    """
    uploader = NaverBlogUploader(config, sanitize_and_fix_links_func, chat_log_append_func)
    return uploader.upload_to_naver(title, content, category, keyword, bo_table_value, ca_name_value)
