# -*- coding: utf-8 -*-
"""
MySQL 저장 모듈
MySQL 데이터베이스에 블로그 콘텐츠를 저장하는 기능을 제공합니다.
"""

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


class MySQLUploader:
    """MySQL 저장 클래스"""
    
    def __init__(self, chat_log_append_func=None):
        """
        초기화
        
        Args:
            chat_log_append_func (callable): 채팅 로그 출력 함수 (선택)
        """
        self.chat_log_append = chat_log_append_func or (lambda x: None)
    
    def save_to_mysql(self, title, content, category, keyword):
        """
        MySQL에 저장하는 함수
        
        Args:
            title (str): 글 제목
            content (str): 글 내용 (HTML 형식)
            category (str): 카테고리
            keyword (str): 키워드
            
        Returns:
            bool: 저장 성공 여부
        """
        log_action("MySQL 저장 시작", f"제목: {title[:50]}..., 카테고리: {category}, 키워드: {keyword}", "process")
        
        try:
            from core.mysql_handler import MySQLHandler
            handler = MySQLHandler()

            # wr_1 컬럼 길이 제한 반영 (25자)
            clean_keyword = keyword[:25] if isinstance(keyword, str) and len(keyword) > 25 else (keyword or "")

            success = handler.insert_to_mysql_with_fallback(
                title, content, category, clean_keyword
            )

            if success:
                log_action("MySQL 저장 완료", f"제목: {title[:50]}...", "success")
                self.chat_log_append("✅ MySQL 저장 완료\n")
                print("✅ MySQL 저장 완료")
                return True
            else:
                self.chat_log_append("❌ MySQL 저장 실패\n")
                print("❌ MySQL 저장 실패")
                return False
                
        except ImportError as e:
            error_msg = f"⚠️ MySQLHandler 모듈을 찾을 수 없습니다: {str(e)}\n"
            self.chat_log_append(error_msg)
            print(error_msg)
            return False
            
        except Exception as e:
            self.chat_log_append(f"❌ MySQL 저장 오류: {str(e)}\n")
            print(f"❌ MySQL 저장 오류: {str(e)}")
            traceback.print_exc()
            return False
    
    def test_connection(self):
        """
        MySQL 연결 테스트
        
        Returns:
            bool: 연결 성공 여부
        """
        try:
            self.chat_log_append("🗄️ MySQL 핸들러 테스트를 시작합니다...\n")
            print("🗄️ MySQL 핸들러 테스트를 시작합니다...")
            
            from core.mysql_handler import MySQLHandler
            
            # 핸들러 인스턴스 생성
            handler = MySQLHandler()
            
            # 연결 테스트
            if handler.test_connection():
                self.chat_log_append("✅ MySQL 연결 테스트 성공\n")
                print("✅ MySQL 연결 테스트 성공")
                return True
            else:
                self.chat_log_append("⚠️ MySQL 연결 실패 - 로컬 파일 저장 모드\n")
                print("⚠️ MySQL 연결 실패 - 로컬 파일 저장 모드")
                return False
                
        except ImportError as e:
            error_msg = f"⚠️ MySQLHandler 모듈을 찾을 수 없습니다: {str(e)}\n"
            self.chat_log_append(error_msg)
            print(error_msg)
            return False
            
        except Exception as e:
            self.chat_log_append(f"❌ MySQL 연결 테스트 중 오류: {str(e)}\n")
            print(f"❌ MySQL 연결 테스트 중 오류: {str(e)}")
            traceback.print_exc()
            return False
    
    def test_mysql_handler(self):
        """
        MySQL 핸들러 전체 테스트 (연결 + 데이터 저장)
        
        Returns:
            bool: 테스트 성공 여부
        """
        try:
            self.chat_log_append("🗄️ MySQL 핸들러 테스트를 시작합니다...\n")
            print("🗄️ MySQL 핸들러 테스트를 시작합니다...")
            
            from core.mysql_handler import MySQLHandler
            
            # 핸들러 인스턴스 생성
            handler = MySQLHandler()
            
            # 연결 테스트
            if handler.test_connection():
                self.chat_log_append("✅ MySQL 연결 테스트 성공\n")
                print("✅ MySQL 연결 테스트 성공")
            else:
                self.chat_log_append("⚠️ MySQL 연결 실패 - 로컬 파일 저장 모드\n")
                print("⚠️ MySQL 연결 실패 - 로컬 파일 저장 모드")
            
            # 테스트 데이터 저장
            test_subject = "MySQL 핸들러 테스트 제목"
            test_content = "이것은 MySQL 핸들러 테스트를 위한 내용입니다."
            test_category = "테스트"
            test_keyword = "mysql_test"
            
            success = handler.insert_to_mysql_with_fallback(
                test_subject, test_content, test_category, test_keyword
            )
            
            if success:
                self.chat_log_append("✅ 테스트 데이터 저장 성공\n")
                print("✅ 테스트 데이터 저장 성공")
                return True
            else:
                self.chat_log_append("❌ 테스트 데이터 저장 실패\n")
                print("❌ 테스트 데이터 저장 실패")
                return False
                
        except ImportError as e:
            error_msg = f"⚠️ MySQLHandler 모듈을 찾을 수 없습니다: {str(e)}\n"
            self.chat_log_append(error_msg)
            print(error_msg)
            return False
            
        except Exception as e:
            self.chat_log_append(f"❌ MySQL 핸들러 테스트 중 오류: {str(e)}\n")
            print(f"❌ MySQL 핸들러 테스트 중 오류: {str(e)}")
            traceback.print_exc()
            return False


# 편의 함수: 직접 호출 가능한 래퍼
def save_to_mysql_db(title, content, category, keyword, chat_log_append_func=None):
    """
    MySQL 저장 편의 함수
    
    Args:
        title (str): 글 제목
        content (str): 글 내용 (HTML 형식)
        category (str): 카테고리
        keyword (str): 키워드
        chat_log_append_func (callable): 채팅 로그 출력 함수 (선택)
        
    Returns:
        bool: 저장 성공 여부
    """
    uploader = MySQLUploader(chat_log_append_func)
    return uploader.save_to_mysql(title, content, category, keyword)


def test_mysql_connection(chat_log_append_func=None):
    """
    MySQL 연결 테스트 편의 함수
    
    Args:
        chat_log_append_func (callable): 채팅 로그 출력 함수 (선택)
        
    Returns:
        bool: 연결 성공 여부
    """
    uploader = MySQLUploader(chat_log_append_func)
    return uploader.test_connection()


def test_mysql_handler_full(chat_log_append_func=None):
    """
    MySQL 핸들러 전체 테스트 편의 함수
    
    Args:
        chat_log_append_func (callable): 채팅 로그 출력 함수 (선택)
        
    Returns:
        bool: 테스트 성공 여부
    """
    uploader = MySQLUploader(chat_log_append_func)
    return uploader.test_mysql_handler()
