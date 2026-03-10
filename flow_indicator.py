import streamlit as st
import subprocess
import os
import threading
from datetime import datetime

def run_github_xml_uploader():
    """GitHub XML Uploader를 실행하는 함수"""
    try:
        # chatbot 디렉토리 경로 설정
        chatbot_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../chatbot'))
        
        st.info(f"📂 실행 디렉토리: {chatbot_dir}")
        
        # subprocess로 python 스크립트 실행
        result = subprocess.run(
            ['python', 'github_xml_uploader.py'],
            cwd=chatbot_dir,
            capture_output=True,
            text=True,
            timeout=60  # 60초 타임아웃
        )
        
        if result.returncode == 0:
            st.success("✅ GitHub XML Uploader 실행 성공!")
            if result.stdout:
                st.code(result.stdout, language='text')
        else:
            st.error(f"❌ 실행 실패 (반환 코드: {result.returncode})")
            if result.stderr:
                st.error("오류 내용:")
                st.code(result.stderr, language='text')
                
    except subprocess.TimeoutExpired:
        st.error("⏰ 실행 시간 초과 (60초)")
    except Exception as e:
        st.error(f"❌ 실행 중 오류 발생: {str(e)}")

def run_github_xml_uploader_async():
    """비동기로 GitHub XML Uploader를 실행하는 함수"""
    def background_task():
        try:
            chatbot_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../chatbot'))
            
            result = subprocess.run(
                ['python', 'github_xml_uploader.py'],
                cwd=chatbot_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # 결과를 세션 스테이트에 저장
            st.session_state['uploader_result'] = {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            st.session_state['uploader_result'] = {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
    
    # 백그라운드 스레드로 실행
    thread = threading.Thread(target=background_task)
    thread.daemon = True
    thread.start()
    
    st.info("🔄 백그라운드에서 실행 중... 잠시 후 결과를 확인해주세요.")
    st.balloons()

def main():
    st.set_page_config(
        page_title="GitHub XML Uploader",
        page_icon="🚀",
        layout="wide"
    )
    
    st.title("🚀 GitHub XML Uploader")
    st.markdown("---")
    
    # 설명
    st.markdown("""
    ### 📋 기능 설명
    - Google Trends XML을 다운로드하고 GitHub 저장소에 업로드합니다
    - 실행 경로: `E:\\Ai project\\nb_wfa\\chatbot`
    - 실행 명령: `python github_xml_uploader.py`
    """)
    
    # 실행 버튼들
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 실행 (동기)", type="primary", width='stretch'):
            with st.spinner("실행 중..."):
                run_github_xml_uploader()
    
    with col2:
        if st.button("⚡ 실행 (비동기)", width='stretch'):
            run_github_xml_uploader_async()
    
    with col3:
        if st.button("🔍 결과 새로고침", width='stretch'):
            st.rerun()
    
    # 비동기 실행 결과 표시
    if 'uploader_result' in st.session_state:
        st.markdown("---")
        st.subheader("📊 최근 실행 결과")
        
        result = st.session_state['uploader_result']
        
        # 실행 시간 표시
        st.info(f"⏰ 실행 시간: {result['timestamp']}")
        
        if result['success']:
            st.success("✅ 실행 성공!")
            if 'stdout' in result and result['stdout']:
                st.subheader("📤 출력 내용:")
                st.code(result['stdout'], language='text')
        else:
            if 'error' in result:
                st.error(f"❌ 실행 중 오류: {result['error']}")
            else:
                st.error(f"❌ 실행 실패 (반환 코드: {result.get('returncode', 'Unknown')})")
                if 'stderr' in result and result['stderr']:
                    st.subheader("🚨 오류 내용:")
                    st.code(result['stderr'], language='text')
    
    # 파일 경로 정보
    st.markdown("---")
    st.subheader("📁 파일 경로 정보")
    
    current_dir = os.path.dirname(__file__)
    chatbot_dir = os.path.abspath(os.path.join(current_dir, '../chatbot'))
    uploader_file = os.path.join(chatbot_dir, 'github_xml_uploader.py')
    
    st.info(f"📂 현재 디렉토리: {current_dir}")
    st.info(f"🎯 실행 디렉토리: {chatbot_dir}")
    st.info(f"📄 스크립트 파일: {uploader_file}")
    
    # 파일 존재 여부 확인
    if os.path.exists(uploader_file):
        st.success("✅ github_xml_uploader.py 파일이 존재합니다")
    else:
        st.error("❌ github_xml_uploader.py 파일을 찾을 수 없습니다")
        st.error(f"예상 경로: {uploader_file}")

if __name__ == "__main__":
    main() 
