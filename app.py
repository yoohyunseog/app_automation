import streamlit as st
import streamlit.components.v1 as components
import sys
import tempfile
import subprocess
import threading
from datetime import datetime
import xml.etree.ElementTree as ET

from components.nb_chart import render_nb_chart
from components.signal_badge import render_signal_badge
from blog_automation.naver_login import (
    naver_login,
    after_login_action,
    is_driver_alive,
    is_logged_in,
    load_credentials,
    save_credentials,
    go_to_write_page
)
from components.naver_blog_login_ui import render_blog_ui
from components.blog_automation import render_write_ui
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
from datetime import datetime
import os
import re
import math
try:
    from streamlit_keyup import st_keyup  # per-key input component
except Exception:
    st_keyup = None

_driver = None
LAUNCH_LOG = "../data/selenium_chrome_launch_time.txt"  # 실행 정보 저장 파일

def extract_detailed_trends_from_xml(filename):
    """XML에서 상세한 트렌드 정보를 추출하는 함수"""
    try:
        if not os.path.exists(filename):
            return []
            
        tree = ET.parse(filename)
        root = tree.getroot()
        
        items_data = []
        
        for item in root.findall('./channel/item'):
            title = item.findtext('title', '').strip()
            description = item.findtext('description', '').strip()
            link = item.findtext('link', '').strip()
            pub_date = item.findtext('pubDate', '').strip()
            
            if title:
                # HTML 태그 정리
                clean_desc = description.replace('<![CDATA[', '').replace(']]>', '')
                clean_desc = clean_desc.replace('<b>', '').replace('</b>', '')
                clean_desc = clean_desc.replace('<br>', ' ').replace('<br/>', ' ')
                clean_desc = clean_desc.strip()
                
                items_data.append({
                    'title': title,
                    'description': clean_desc,
                    'link': link,
                    'pub_date': pub_date
                })
        
        return items_data
        
    except Exception as e:
        st.warning(f"XML 파싱 중 오류: {e}")
        return []

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
            
            # 결과 저장
            save_uploader_result(result.stdout, True)
            
            # 결과 출력
            if result.stdout:
                st.subheader("📤 실행 결과:")
                st.code(result.stdout, language='text')
                
                # 트렌드 키워드 파싱 및 표시
                display_trend_keywords(result.stdout)
                
        else:
            st.error(f"❌ 실행 실패 (반환 코드: {result.returncode})")
            
            # 실패 결과도 저장
            save_uploader_result(result.stderr, False)
            
            if result.stderr:
                st.error("오류 내용:")
                st.code(result.stderr, language='text')
                
    except subprocess.TimeoutExpired:
        st.error("⏰ 실행 시간 초과 (60초)")
        save_uploader_result("실행 시간 초과 (60초)", False)
    except Exception as e:
        st.error(f"❌ 실행 중 오류 발생: {str(e)}")
        save_uploader_result(f"실행 중 오류 발생: {str(e)}", False)

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
            
            # 파일로도 저장
            save_uploader_result(result.stdout if result.returncode == 0 else result.stderr, result.returncode == 0)
            
        except Exception as e:
            st.session_state['uploader_result'] = {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # 오류도 파일로 저장
            save_uploader_result(f"실행 중 오류: {str(e)}", False)
    
    # 백그라운드 스레드로 실행
    thread = threading.Thread(target=background_task)
    thread.daemon = True
    thread.start()
    
    st.info("🔄 백그라운드에서 실행 중... 잠시 후 결과를 확인해주세요.")
    st.balloons()

def save_uploader_result(output, success):
    """실행 결과를 파일로 저장하는 함수"""
    try:
        # 저장 디렉토리 설정
        save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/save'))
        os.makedirs(save_dir, exist_ok=True)
        
        # 파일명에 타임스탬프 포함
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        status = "success" if success else "failed"
        filename = f"github_uploader_{status}_{timestamp}.txt"
        filepath = os.path.join(save_dir, filename)
        
        # 파일 저장
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"실행 상태: {'성공' if success else '실패'}\n")
            f.write("=" * 50 + "\n")
            f.write(output)
        
        # 최신 결과도 별도 파일로 저장 (덮어쓰기)
        latest_file = os.path.join(save_dir, "github_uploader_latest.txt")
        with open(latest_file, 'w', encoding='utf-8') as f:
            f.write(f"최근 실행: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"실행 상태: {'성공' if success else '실패'}\n")
            f.write("=" * 50 + "\n")
            f.write(output)
            
        print(f"결과 저장 완료: {filepath}")
        
    except Exception as e:
        print(f"결과 저장 실패: {e}")

def display_trend_keywords(output):
    """트렌드 키워드를 파싱하여 보기 좋게 표시하는 함수"""
    try:
        lines = output.split('\n')
        
        for i, line in enumerate(lines):
            if "[트렌드] 오늘의 트렌드 키워드:" in line:
                # 다음 줄이 키워드 목록
                if i + 1 < len(lines):
                    keywords_line = lines[i + 1].strip()
                    if keywords_line:
                        # // 로 분리된 키워드들을 파싱
                        if '//' in keywords_line:
                            keywords = [kw.strip() for kw in keywords_line.split('//')[0].split(',')]
                        else:
                            keywords = [kw.strip() for kw in keywords_line.split(',')]
                        
                        st.markdown("---")
                        st.subheader("🔥 오늘의 트렌드 키워드")
                        
                        # 키워드를 배지 형태로 표시
                        cols = st.columns(5)
                        for idx, keyword in enumerate(keywords):
                            if keyword:
                                with cols[idx % 5]:
                                    st.markdown(f"""
                                    <div style="
                                        background-color: #e1f5fe;
                                        border: 1px solid #01579b;
                                        border-radius: 20px;
                                        padding: 5px 15px;
                                        margin: 2px;
                                        text-align: center;
                                        font-weight: bold;
                                        color: #01579b;
                                        font-size: 14px;
                                    ">
                                        #{keyword}
                                    </div>
                                    """, unsafe_allow_html=True)
                        
                        # XML에서 상세 트렌드 정보 추출 및 표시
                        chatbot_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../chatbot'))
                        xml_file = os.path.join(chatbot_dir, 'google_trend.xml')
                        
                        if os.path.exists(xml_file):
                            st.markdown("---")
                            st.subheader("📊 트렌드 키워드별 상세 정보 (검색량 포함)")
                            
                            detailed_trends = extract_detailed_trends_from_xml(xml_file)
                            
                            if detailed_trends:
                                # 검색량별로 정렬 (높은 순)
                                def get_volume_number(trend):
                                    volume = trend.get('search_volume', '')
                                    if volume and any(char.isdigit() for char in volume):
                                        return int(''.join(filter(str.isdigit, volume)))
                                    return 0
                                
                                detailed_trends.sort(key=get_volume_number, reverse=True)
                                
                                # 검색량별 카드 형태로 표시
                                for trend in detailed_trends[:10]:  # 상위 10개만
                                    volume_info = trend.get('search_volume', '').replace('+', '+검색')
                                    
                                    # 검색량에 따른 색상 결정
                                    volume_num = get_volume_number(trend)
                                    if volume_num >= 1000:
                                        color = "#ff4444"  # 빨강 (높음)
                                        icon = "🔥"
                                    elif volume_num >= 200:
                                        color = "#ff8800"  # 주황 (중간)
                                        icon = "📈"
                                    else:
                                        color = "#0088ff"  # 파랑 (낮음)
                                        icon = "📊"
                                    
                                    with st.expander(f"{icon} **{trend['title']}** {volume_info}", expanded=True):
                                        col1, col2 = st.columns([1, 2])
                                        
                                        with col1:
                                            st.markdown(f"""
                                            <div style="
                                                background: linear-gradient(135deg, {color}22, {color}11);
                                                border-left: 4px solid {color};
                                                padding: 15px;
                                                border-radius: 8px;
                                                margin: 10px 0;
                                            ">
                                                <h3 style="color: {color}; margin: 0;">🎯 {trend['title']}</h3>
                                                <p style="font-size: 18px; font-weight: bold; color: {color}; margin: 5px 0;">{volume_info}</p>
                                                <p style="color: #666; margin: 0;">📅 {trend.get('pub_date', '')[:16]}...</p>
                                            </div>
                                            """, unsafe_allow_html=True)
                                        
                                        with col2:
                                            if trend.get('articles'):
                                                st.markdown("**📰 관련 기사:**")
                                                for j, article in enumerate(trend['articles'][:5], 1):
                                                    if article.get('title'):
                                                        source_badge = ""
                                                        if article.get('source'):
                                                            source_color = {
                                                                '조선일보': '#1e40af',
                                                                '연합뉴스': '#059669', 
                                                                'MBC 뉴스': '#dc2626',
                                                                'KBS 뉴스': '#7c3aed',
                                                                '한겨레': '#0891b2',
                                                                '경향신문': '#ea580c',
                                                                '네이트': '#16a34a'
                                                            }.get(article['source'], '#6b7280')
                                                            
                                                            source_badge = f"""
                                                            <span style="
                                                                background-color: {source_color};
                                                                color: white;
                                                                padding: 2px 8px;
                                                                border-radius: 12px;
                                                                font-size: 11px;
                                                                font-weight: bold;
                                                                margin-right: 8px;
                                                            ">{article['source']}</span>
                                                            """
                                                        
                                                        article_title = article['title'][:60] + "..." if len(article['title']) > 60 else article['title']
                                                        
                                                        if article.get('link'):
                                                            st.markdown(f"""
                                                            <div style="margin: 8px 0; padding: 8px; background: #f8f9fa; border-radius: 6px;">
                                                                {source_badge}
                                                                <a href="{article['link']}" target="_blank" style="text-decoration: none; color: #1f2937;">
                                                                    📄 {article_title}
                                                                </a>
                                                            </div>
                                                            """, unsafe_allow_html=True)
                                                        else:
                                                            st.markdown(f"""
                                                            <div style="margin: 8px 0; padding: 8px; background: #f8f9fa; border-radius: 6px;">
                                                                {source_badge}📄 {article_title}
                                                            </div>
                                                            """, unsafe_allow_html=True)
                                            else:
                                                st.info("관련 기사 정보 없음")
                                
                                # 검색량별 통계 표시
                                st.markdown("---")
                                st.subheader("📈 검색량 통계")
                                
                                high_volume = [t for t in detailed_trends if get_volume_number(t) >= 1000]
                                mid_volume = [t for t in detailed_trends if 200 <= get_volume_number(t) < 1000]
                                low_volume = [t for t in detailed_trends if get_volume_number(t) < 200]
                                
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("🔥 고검색량 (1000+)", len(high_volume))
                                with col2:
                                    st.metric("📈 중검색량 (200-999)", len(mid_volume))
                                with col3:
                                    st.metric("📊 저검색량 (200미만)", len(low_volume))
                                
                        # 3가지 형태로 쉼표 구분 출력 (검색량 정보 포함)
                        st.markdown("---")
                        st.subheader("📋 쉼표 구분 출력 (검색량 포함)")
                        
                        if detailed_trends:
                            # 1. 키워드만
                            keywords_only = ", ".join([trend['title'] for trend in detailed_trends])
                            st.markdown("**🏷️ 키워드만:**")
                            st.code(keywords_only, language='text')
                            
                            # 2. 키워드 + 검색량
                            keywords_with_volume = ", ".join([
                                f"{trend['title']} ({trend.get('search_volume', 'N/A')})" 
                                for trend in detailed_trends
                            ])
                            st.markdown("**🔥 키워드 + 검색량:**")
                            st.code(keywords_with_volume, language='text')
                            
                            # 3. 키워드 + 주요 언론사
                            keywords_with_source = []
                            for trend in detailed_trends:
                                sources = list(set([article.get('source', '') for article in trend.get('articles', []) if article.get('source')]))
                                source_info = f" [{', '.join(sources[:2])}]" if sources else ""
                                keywords_with_source.append(f"{trend['title']}{source_info}")
                            
                            keywords_with_source_str = ", ".join(keywords_with_source)
                            st.markdown("**📰 키워드 + 주요 언론사:**")
                            st.code(keywords_with_source_str, language='text')
                            
                            # 4. 기사 제목 (언론사별)
                            all_articles = []
                            for trend in detailed_trends:
                                for article in trend.get('articles', []):
                                    if article.get('title') and article.get('source'):
                                        all_articles.append(f"{article['title']} - {article['source']}")
                            
                            if all_articles:
                                articles_str = ", ".join(all_articles)
                                st.markdown("**📄 모든 기사 제목 + 언론사:**")
                                st.code(articles_str, language='text')
                        
                        else:
                            # 기존 방식 (fallback)
                            titles_only = ", ".join(keywords)
                            st.markdown("**🏷️ 제목:**")
                            st.code(titles_only, language='text')
                            
                            keywords_only = ", ".join(keywords)
                            st.markdown("**🔑 키워드:**")
                            st.code(keywords_only, language='text')
                            
                            title_plus_keywords = ", ".join([f"{kw} {kw}" for kw in keywords])
                            st.markdown("**🏷️+🔑 제목 + 키워드:**")
                            st.code(title_plus_keywords, language='text')
                        
                        # 원래 키워드 목록도 유지
                        st.markdown("**💡 키워드 목록:**")
                        st.info(" • ".join(keywords))
                        
                        # 복사하기 쉽도록 텍스트 영역으로도 제공
                        st.markdown("---")
                        st.subheader("📝 복사용 텍스트")
                        
                        if detailed_trends:
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                keywords_simple = ", ".join([trend['title'] for trend in detailed_trends])
                                st.text_area("키워드", keywords_simple, height=120, key="keywords_simple")
                            
                            with col2:
                                keywords_volume = ", ".join([
                                    f"{trend['title']} ({trend.get('search_volume', 'N/A')})" 
                                    for trend in detailed_trends
                                ])
                                st.text_area("키워드+검색량", keywords_volume, height=120, key="keywords_volume")
                            
                            with col3:
                                all_articles_titles = []
                                for trend in detailed_trends:
                                    for article in trend.get('articles', []):
                                        if article.get('title'):
                                            all_articles_titles.append(article['title'])
                                articles_titles_str = ", ".join(all_articles_titles)
                                st.text_area("기사제목", articles_titles_str, height=120, key="articles_titles")
                            
                            with col4:
                                all_sources = []
                                for trend in detailed_trends:
                                    for article in trend.get('articles', []):
                                        if article.get('source'):
                                            all_sources.append(article['source'])
                                unique_sources = list(set(all_sources))
                                sources_str = ", ".join(unique_sources)
                                st.text_area("언론사", sources_str, height=120, key="sources")
                        
                        else:
                            # fallback
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.text_area("제목", ", ".join(keywords), height=100, key="titles_text")
                            
                            with col2:
                                st.text_area("키워드", ", ".join(keywords), height=100, key="keywords_text")
                            
                            with col3:
                                title_plus_keywords = ", ".join([f"{kw} {kw}" for kw in keywords])
                                st.text_area("제목+키워드", title_plus_keywords, height=100, key="combined_text")
                            
                            with col4:
                                st.text_area("기사제목", "상세 정보 없음", height=100, key="articles_titles_text")
                        
                        # 트렌드 키워드를 별도 파일로 저장 (상세 정보 포함)
                        xml_file_path = xml_file if os.path.exists(xml_file) else None
                        save_trend_keywords_enhanced(keywords, detailed_trends, xml_file_path)
                        
                        break
                        
    except Exception as e:
        st.warning(f"트렌드 키워드 파싱 중 오류: {e}")

def save_trend_keywords_enhanced(keywords, detailed_trends, xml_file_path):
    """트렌드 키워드를 3가지 형태로 별도 파일에 저장하는 함수"""
    try:
        # 검색량 숫자 추출 함수
        def get_volume_number(trend):
            volume = trend.get('search_volume', '')
            if volume and any(char.isdigit() for char in volume):
                return int(''.join(filter(str.isdigit, volume)))
            return 0
        
        # 저장 디렉토리 설정
        save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/save'))
        os.makedirs(save_dir, exist_ok=True)
        
        # 오늘 날짜로 파일명 생성
        today = datetime.now().strftime("%Y%m%d")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 상세 파일 저장
        filename = f"trend_keywords_{today}.txt"
        filepath = os.path.join(save_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"날짜: {timestamp}\n")
            f.write("=" * 50 + "\n\n")
            
            f.write("🏷️ 제목 (쉼표 구분):\n")
            f.write(f"{', '.join(keywords)}\n\n")
            
            f.write("🔑 키워드 (쉼표 구분):\n")
            f.write(f"{', '.join(keywords)}\n\n")
            
            f.write("🏷️+🔑 제목 + 키워드 (쉼표 구분):\n")
            f.write(f"{', '.join([f'{kw} {kw}' for kw in keywords])}\n\n")
            
            f.write("📋 개별 키워드 목록:\n")
            for i, keyword in enumerate(keywords, 1):
                f.write(f"{i}. {keyword}\n")

            # 상세 트렌드 정보 추가
            if detailed_trends:
                f.write("\n" + "=" * 50 + "\n")
                f.write("📊 상세 트렌드 정보:\n\n")
                
                # 키워드별 상세 정보
                for trend in detailed_trends:
                    volume_info = trend.get('search_volume', '').replace('+', '+검색')
                    volume_num = get_volume_number(trend)
                    
                    if volume_num >= 1000:
                        icon = "🔥"
                    elif volume_num >= 200:
                        icon = "📈"
                    else:
                        icon = "📊"
                    
                    f.write(f"{icon} {trend['title']} {volume_info}\n")
                    f.write("-" * 30 + "\n")
                    
                    if trend.get('pub_date'):
                        f.write(f"📅 발행시간: {trend['pub_date']}\n")
                    
                    if trend.get('articles'):
                        f.write("📰 관련 기사:\n")
                        for j, article in enumerate(trend['articles'][:5], 1):
                            if article.get('title'):
                                source_info = f" - {article['source']}" if article.get('source') else ""
                                f.write(f"  {j}. {article['title']}{source_info}\n")
                                if article.get('link'):
                                    f.write(f"     링크: {article['link']}\n")
                    f.write("\n")
                
                # 쉼표 구분 형태들
                f.write("=" * 50 + "\n")
                f.write("📋 쉼표 구분 출력:\n\n")
                
                # 키워드만
                keywords_simple = ", ".join([trend['title'] for trend in detailed_trends])
                f.write("🏷️ 키워드만:\n")
                f.write(f"{keywords_simple}\n\n")
                
                # 키워드 + 검색량
                keywords_with_volume = ", ".join([
                    f"{trend['title']} ({trend.get('search_volume', 'N/A')})" 
                    for trend in detailed_trends
                ])
                f.write("🔥 키워드 + 검색량:\n")
                f.write(f"{keywords_with_volume}\n\n")
                
                # 키워드 + 주요 언론사
                keywords_with_source = []
                for trend in detailed_trends:
                    sources = list(set([article.get('source', '') for article in trend.get('articles', []) if article.get('source')]))
                    source_info = f" [{', '.join(sources[:2])}]" if sources else ""
                    keywords_with_source.append(f"{trend['title']}{source_info}")
                
                keywords_with_source_str = ", ".join(keywords_with_source)
                f.write("📰 키워드 + 주요 언론사:\n")
                f.write(f"{keywords_with_source_str}\n\n")
                
                # 모든 기사 제목
                all_articles = []
                for trend in detailed_trends:
                    for article in trend.get('articles', []):
                        if article.get('title') and article.get('source'):
                            all_articles.append(f"{article['title']} - {article['source']}")
                
                if all_articles:
                    articles_str = ", ".join(all_articles)
                    f.write("📄 모든 기사 제목 + 언론사:\n")
                    f.write(f"{articles_str}\n\n")
                
                # 검색량별 통계
                f.write("=" * 50 + "\n")
                f.write("📈 검색량 통계:\n")
                
                high_volume = [t for t in detailed_trends if get_volume_number(t) >= 1000]
                mid_volume = [t for t in detailed_trends if 200 <= get_volume_number(t) < 1000]
                low_volume = [t for t in detailed_trends if get_volume_number(t) < 200]
                
                f.write(f"🔥 고검색량 (1000+): {len(high_volume)}개\n")
                f.write(f"📈 중검색량 (200-999): {len(mid_volume)}개\n")
                f.write(f"📊 저검색량 (200미만): {len(low_volume)}개\n")
                
                if high_volume:
                    f.write("\n고검색량 키워드:\n")
                    for trend in high_volume:
                        f.write(f"  - {trend['title']} ({trend.get('search_volume', 'N/A')})\n")
                
            if xml_file_path:
                f.write(f"\n📄 연결된 XML 파일: {xml_file_path}\n")
        
        # 각 형태별로 별도 파일 저장
        formats = {
            'keywords_simple': ', '.join([trend['title'] for trend in detailed_trends]) if detailed_trends else ', '.join(keywords),
            'keywords_volume': ', '.join([f"{trend['title']} ({trend.get('search_volume', 'N/A')})" for trend in detailed_trends]) if detailed_trends else ', '.join(keywords),
            'articles_titles': ', '.join([article['title'] for trend in detailed_trends for article in trend.get('articles', []) if article.get('title')]) if detailed_trends else '',
            'sources': ', '.join(list(set([article['source'] for trend in detailed_trends for article in trend.get('articles', []) if article.get('source')]))) if detailed_trends else ''
        }
        
        for format_name, content in formats.items():
            if content:  # 내용이 있을 때만 저장
                format_file = os.path.join(save_dir, f"trend_{format_name}_{today}.txt")
                with open(format_file, 'w', encoding='utf-8') as f:
                    f.write(f"날짜: {timestamp}\n")
                    f.write(f"형태: {format_name}\n")
                    f.write("=" * 30 + "\n")
                    f.write(content)
        
        # 누적 히스토리 파일에도 추가
        history_file = os.path.join(save_dir, "trend_keywords_history.txt")
        with open(history_file, 'a', encoding='utf-8') as f:
            f.write(f"\n[{timestamp}]\n")
            f.write(f"기본키워드: {', '.join(keywords)}\n")
            
            if detailed_trends:
                keywords_simple = ", ".join([trend['title'] for trend in detailed_trends])
                f.write(f"상세키워드: {keywords_simple}\n")
                
                keywords_volume = ", ".join([f"{trend['title']} ({trend.get('search_volume', 'N/A')})" for trend in detailed_trends])
                f.write(f"키워드+검색량: {keywords_volume}\n")
                
                all_sources = list(set([article['source'] for trend in detailed_trends for article in trend.get('articles', []) if article.get('source')]))
                f.write(f"언론사: {', '.join(all_sources)}\n")
            
            f.write("-" * 50 + "\n")
            
        print(f"트렌드 키워드 저장 완료: {filepath}")
        
    except Exception as e:
        print(f"트렌드 키워드 저장 실패: {e}")

def save_trend_keywords(keywords):
    """기존 함수는 호환성을 위해 유지 (사용되지 않음)"""
    pass

def render_gpu_automation():
    """GPU 자동화 도구 UI 렌더링"""
    st.title("⚡ GPU 자동화 도구 (NB 그룹화 버전)")
    st.markdown("---")
    
    # 설명
    st.markdown("""
    ### 📋 기능 설명
    - NB 알고리즘을 사용한 스마트 GPU 자원 할당
    - 프로세스 그룹화 및 자동 최적화
    - 실시간 GPU 사용률 모니터링
    - 동적 CPU/GPU 우선순위 조정
    """)
    
    # GPU 자동화 도구 실행
    if st.button("🚀 GPU 자동화 도구 실행", type="primary", width='stretch'):
        run_gpu_automation()
    
    # GPU 상태 확인
    if st.button("📊 GPU 상태 확인", width='stretch'):
        check_gpu_status()
    
    # NB 그룹화 상태 확인
    if st.button("🏷️ NB 그룹화 상태", width='stretch'):
        check_nb_grouping_status()

def run_gpu_automation():
    """GPU 자동화 도구 실행"""
    try:
        # GPU 자동화 도구 경로 설정
        gpu_tool_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../gpu-automation-tool'))
        
        st.info(f"📂 실행 디렉토리: {gpu_tool_dir}")
        
        # subprocess로 python 스크립트 실행
        result = subprocess.run(
            ['python', 'gpu_process_automation.py'],
            cwd=gpu_tool_dir,
            capture_output=True,
            text=True,
            timeout=30  # 30초 타임아웃
        )
        
        if result.returncode == 0:
            st.success("✅ GPU 자동화 도구 실행 성공!")
            
            # 결과 출력
            if result.stdout:
                st.subheader("📤 실행 결과:")
                st.code(result.stdout, language='text')
        else:
            st.error(f"❌ 실행 실패 (반환 코드: {result.returncode})")
            
            if result.stderr:
                st.error("오류 내용:")
                st.code(result.stderr, language='text')
                
    except subprocess.TimeoutExpired:
        st.error("⏰ 실행 시간 초과 (30초)")
    except Exception as e:
        st.error(f"❌ 실행 중 오류 발생: {str(e)}")

def check_gpu_status():
    """GPU 상태 확인"""
    try:
        import torch
        
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            st.success(f"✅ CUDA 사용 가능 - GPU 개수: {gpu_count}")
            
            for i in range(gpu_count):
                gpu_name = torch.cuda.get_device_name(i)
                gpu_memory = torch.cuda.get_device_properties(i).total_memory / 1024**3
                st.info(f"GPU {i}: {gpu_name} ({gpu_memory:.1f}GB)")
        else:
            st.warning("⚠️ CUDA를 사용할 수 없습니다.")
            
    except ImportError:
        st.error("❌ PyTorch가 설치되지 않았습니다.")
    except Exception as e:
        st.error(f"❌ GPU 상태 확인 중 오류: {str(e)}")

def check_nb_grouping_status():
    """NB 그룹화 상태 확인"""
    try:
        # GPU 자동화 도구에서 NB 그룹화 상태 확인
        gpu_tool_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../gpu-automation-tool'))
        
        # 간단한 상태 확인 스크립트 실행
        result = subprocess.run(
            ['python', '-c', 'import gpu_process_automation; automation = gpu_process_automation.GPUProcessAutomation(); automation.show_nb_grouping_status()'],
            cwd=gpu_tool_dir,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            st.success("✅ NB 그룹화 상태 확인 완료!")
            st.code(result.stdout, language='text')
        else:
            st.error("❌ NB 그룹화 상태 확인 실패")
            if result.stderr:
                st.code(result.stderr, language='text')
                
    except Exception as e:
        st.error(f"❌ NB 그룹화 상태 확인 중 오류: {str(e)}")


# =============================
# 🔤 텍스트 유사도 (NB 알고리즘) 페이지
# =============================

# NB 알고리즘 보조 변수
SUPER_BIT = 0.0

def _initialize_arrays(length):
    return {
        'BIT_START_A50': [0.0] * length,
        'BIT_START_A100': [0.0] * length,
        'BIT_START_B50': [0.0] * length,
        'BIT_START_B100': [0.0] * length,
        'BIT_START_NBA100': [0.0] * length,
    }

def _calculate_bit(nb, bit=5.5, reverse=False):
    try:
        if nb is None or len(nb) == 0:
            return bit / 100.0
        if len(nb) < 2:
            return bit / 100.0

        BIT_NB = float(bit)
        nb_values = [float(v) for v in nb]
        max_v = max(nb_values)
        min_v = min(nb_values)
        COUNT = 50
        BIT_END = 1

        negative_range = abs(min_v) if min_v < 0 else 0.0
        positive_range = max_v if max_v > 0 else 0.0

        denom = (COUNT * len(nb_values) - 1)
        if denom <= 0:
            return bit / 100.0
        negative_increment = negative_range / denom
        positive_increment = positive_range / denom

        arrays = _initialize_arrays(COUNT * len(nb_values))
        count = 0
        total_sum = 0.0

        for value in nb_values:
            for _ in range(COUNT):
                A50 = (min_v + negative_increment * (count + 1)) if value < 0 else (min_v + positive_increment * (count + 1))
                A100 = (count + 1) * BIT_NB / (COUNT * len(nb_values))
                B50 = (A50 - negative_increment * 2) if value < 0 else (A50 - positive_increment * 2)
                B100 = (A50 + negative_increment) if value < 0 else (A50 + positive_increment)
                NBA100 = A100 / (len(nb_values) - BIT_END)

                arrays['BIT_START_A50'][count] = A50
                arrays['BIT_START_A100'][count] = A100
                arrays['BIT_START_B50'][count] = B50
                arrays['BIT_START_B100'][count] = B100
                arrays['BIT_START_NBA100'][count] = NBA100
                count += 1
            total_sum += value

        if reverse:
            arrays['BIT_START_NBA100'].reverse()

        NB50 = 0.0
        for value in nb_values:
            for a in range(len(arrays['BIT_START_NBA100'])):
                if arrays['BIT_START_B50'][a] <= value <= arrays['BIT_START_B100'][a]:
                    NB50 += arrays['BIT_START_NBA100'][min(a, len(arrays['BIT_START_NBA100']) - 1)]
                    break

        if len(nb_values) == 2:
            return BIT_NB - NB50

        return NB50
    except Exception:
        return bit / 100.0

def _update_super_bit(new_value):
    global SUPER_BIT
    try:
        SUPER_BIT = float(new_value)
    except Exception:
        pass

def _bit_max_nb(nb, bit=5.5):
    try:
        result = _calculate_bit(nb, bit, False)
        if not math.isfinite(result) or math.isnan(result) or result > 100 or result < -100:
            return SUPER_BIT
        _update_super_bit(result)
        return result
    except Exception:
        return SUPER_BIT

def _bit_min_nb(nb, bit=5.5):
    try:
        result = _calculate_bit(nb, bit, True)
        if not math.isfinite(result) or math.isnan(result) or result > 100 or result < -100:
            return SUPER_BIT
        _update_super_bit(result)
        return result
    except Exception:
        return SUPER_BIT

def _identify_language(s: str) -> str:
    if not s:
        return 'None'
    counts = {
        'Japanese': 0.0,
        'Korean': 0.0,
        'English': 0.0,
        'Russian': 0.0,
        'Chinese': 0.0,
        'Hebrew': 0.0,
        'Vietnamese': 0.0,
        'Thai': 0.0,
        'Portuguese': 0.0,
        'Others': 0.0,
    }
    portuguese_chars = set([
        0x00C0, 0x00C1, 0x00C2, 0x00C3, 0x00C7, 0x00C8, 0x00C9, 0x00CA, 0x00CB,
        0x00CC, 0x00CD, 0x00CE, 0x00CF, 0x00D2, 0x00D3, 0x00D4, 0x00D5, 0x00D9,
        0x00DA, 0x00DB, 0x00DC, 0x00DD, 0x00E0, 0x00E1, 0x00E2, 0x00E3, 0x00E7,
        0x00E8, 0x00E9, 0x00EA, 0x00EB, 0x00EC, 0x00ED, 0x00EE, 0x00EF, 0x00F2,
        0x00F3, 0x00F4, 0x00F5, 0x00F9, 0x00FA, 0x00FB, 0x00FC, 0x00FD, 0x0107,
        0x0113, 0x012B, 0x014C, 0x016B, 0x1ECD, 0x1ECF, 0x1ED1, 0x1ED3, 0x1ED5,
        0x1ED7, 0x1ED9, 0x1EDB, 0x1EDD, 0x1EDF, 0x1EE1, 0x1EE3, 0x1EE5, 0x1EE7,
        0x1EE9, 0x1EEB, 0x1EED, 0x1EEF, 0x1EF1,
    ])
    for ch in s:
        u = ord(ch)
        if u in portuguese_chars:
            counts['Portuguese'] += 10
        elif 0xAC00 <= u <= 0xD7AF:
            counts['Korean'] += 100
        elif (0x3040 <= u <= 0x309F) or (0x30A0 <= u <= 0x30FF) or (0x4E00 <= u <= 0x9FFF):
            counts['Japanese'] += 10
        elif 0x4E00 <= u <= 0x9FFF:
            counts['Chinese'] += 1
        elif (0x0041 <= u <= 0x005A) or (0x0061 <= u <= 0x007A):
            counts['English'] += 1
        elif (0x00C0 <= u <= 0x00FF) or (0x0102 <= u <= 0x01B0):
            counts['Vietnamese'] += 10
        elif 0x0410 <= u <= 0x044F:
            counts['Russian'] += 10
        elif 0x0590 <= u <= 0x05FF:
            counts['Hebrew'] += 10
        elif 0x0E00 <= u <= 0x0E7F:
            counts['Thai'] += 10
        else:
            counts['Others'] += 1
    total = sum(counts.values())
    if total == 0:
        return 'None'
    ratios = {k: (v / total if total > 0 else 0.0) for k, v in counts.items()}
    sorted_lang = sorted(ratios.items(), key=lambda x: x[1], reverse=True)
    top_lang, top_ratio = sorted_lang[0]
    if top_lang == 'Others' or top_ratio == 0:
        return sorted_lang[1][0] if len(sorted_lang) > 1 and sorted_lang[1][1] > 0 else 'None'
    return top_lang

def _are_languages_same(a: str, b: str) -> bool:
    return _identify_language(a) == _identify_language(b)

def _word_nb_unicode_format(domain: str):
    default_prefix = 'NB DEFAULT PREFIX'
    if not domain:
        domain = default_prefix
    else:
        domain = default_prefix + ':' + domain
    chars = list(domain)
    lang_ranges = [
        {'range': (0xAC00, 0xD7AF), 'prefix': 1_000_000},
        {'range': (0x3040, 0x309F), 'prefix': 2_000_000},
        {'range': (0x30A0, 0x30FF), 'prefix': 3_000_000},
        {'range': (0x4E00, 0x9FFF), 'prefix': 4_000_000},
        {'range': (0x0410, 0x044F), 'prefix': 5_000_000},
        {'range': (0x0041, 0x007A), 'prefix': 6_000_000},
        {'range': (0x0590, 0x05FF), 'prefix': 7_000_000},
        {'range': (0x00C0, 0x00FD), 'prefix': 8_000_000},
        {'range': (0x0E00, 0x0E7F), 'prefix': 9_000_000},
    ]
    out = []
    for ch in chars:
        u = ord(ch)
        prefix = 0
        for lr in lang_ranges:
            lo, hi = lr['range']
            if lo <= u <= hi:
                prefix = lr['prefix']
                break
        out.append(prefix + u)
    return out

def _word_sim(nb_max=100.0, nb_min=50.0, max_v=100.0, min_v=50.0):
    sim_max = (nb_max / max_v * 100.0) if nb_max <= max_v else (max_v / nb_max * 100.0)
    sim_max = 99.99 if nb_max == max_v else (100 - abs(sim_max) if abs(sim_max) > 100 else sim_max)
    sim_min = (nb_min / min_v * 100.0) if nb_min <= min_v else (min_v / nb_min * 100.0)
    sim_min = 99.99 if nb_min == min_v else (100 - abs(sim_min) if abs(sim_min) > 100 else sim_min)
    return abs((sim_max + sim_min) / 2.0)

def _calculate_array_similarity(array1, array2):
    s1 = list(array1)
    s2 = list(array2)
    intersection = [v for v in s1 if v in s2]
    union = list({*s1, *s2})
    jaccard = (len(intersection) / len(union) * 100.0) if len(union) > 0 else 0.0
    ordered = 0.0
    if len(s1) > 0 and len(s1) == len(s2):
        ordered_matches = sum(1 for i in range(len(s1)) if s1[i] == s2[i])
        ordered = (ordered_matches / len(s1) * 100.0)
    return jaccard * 0.5 + ordered * 0.5

def _calculate_similarity(word1: str, word2: str) -> float:
    arrs1 = _word_nb_unicode_format(word1)
    nb_max = _bit_max_nb(arrs1)
    nb_min = _bit_min_nb(arrs1)
    arrs2 = _word_nb_unicode_format(word2)
    max_v = _bit_max_nb(arrs2)
    min_v = _bit_min_nb(arrs2)
    similarity1 = _word_sim(nb_max, nb_min, max_v, min_v)
    similarity2 = _calculate_array_similarity(arrs1, arrs2)
    if _are_languages_same(word1, word2):
        return max(similarity1, similarity2)
    return min(similarity1, similarity2)

def _calculate_sentence_bits(sentence: str):
    arr = _word_nb_unicode_format(sentence)
    return {
        'bitMax': _bit_max_nb(arr),
        'bitMin': _bit_min_nb(arr)
    }

def _clean_text(s: str) -> str:
    if s is None:
        return ''
    s2 = re.sub(r"\s+", " ", s)
    return re.sub(r"[^0-9A-Za-z\uAC00-\uD7AF\u3040-\u30FF\u4E00-\u9FFF\u0410-\u044F\u0590-\u05FF\u0E00-\u0E7F\s\[\]#]", "", s2).strip()

def render_text_similarity_page():
    st.title("🔤 NB BIT 계산 (실시간)")
    st.markdown("---")

    if st_keyup is not None:
        text_input = st_keyup("문장 (키 입력마다 계산)", key="nb_bit_single_input")
    else:
        text_input = st.text_input(
            "문장 (Enter로 확정)",
            key="nb_bit_single_input",
            placeholder="키 입력 즉시 반영을 원하면 'pip install streamlit-keyup' 설치"
        )
    cleaned = _clean_text(text_input)

    if cleaned:
        arr = _word_nb_unicode_format(cleaned)
        bit_max = _bit_max_nb(arr)
        bit_min = _bit_min_nb(arr)

        col1, col2 = st.columns(2)
        with col1:
            st.metric("BIT_MAX_NB", f"{bit_max:.5f}")
        with col2:
            st.metric("BIT_MIN_NB", f"{bit_min:.5f}")
    else:
        st.info("문장을 입력하면 BIT_MAX_NB / BIT_MIN_NB 값을 실시간으로 계산합니다 (소수점 5자리).")

def render_github_xml_uploader():
    """GitHub XML Uploader UI 렌더링"""
    st.title("🚀 GitHub XML Uploader")
    st.markdown("---")
    
    # 설명
    st.markdown("""
    ### 📋 기능 설명
    - Google Trends XML을 다운로드하고 GitHub 저장소에 업로드합니다
    - 실행 경로: `E:\\Ai project\\nb_wfa\\chatbot`
    - 실행 명령: `python github_xml_uploader.py`
    - 결과는 자동으로 `../data/save/` 폴더에 저장됩니다
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
                
                # 트렌드 키워드 파싱 및 표시
                display_trend_keywords(result['stdout'])
        else:
            if 'error' in result:
                st.error(f"❌ 실행 중 오류: {result['error']}")
            else:
                st.error(f"❌ 실행 실패 (반환 코드: {result.get('returncode', 'Unknown')})")
                if 'stderr' in result and result['stderr']:
                    st.subheader("🚨 오류 내용:")
                    st.code(result['stderr'], language='text')
    
    # 저장된 결과 파일 표시
    st.markdown("---")
    st.subheader("💾 저장된 결과 파일")
    
    save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/save'))
    
    if os.path.exists(save_dir):
        files = [f for f in os.listdir(save_dir) if f.startswith('github_uploader_') or f.startswith('trend_keywords_')]
        files.sort(reverse=True)  # 최신 파일부터 표시
        
        if files:
            # 최근 5개 파일만 표시
            for file in files[:5]:
                file_path = os.path.join(save_dir, file)
                file_size = os.path.getsize(file_path)
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
                
                with st.expander(f"📄 {file} ({file_size} bytes) - {file_time}"):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            st.text(content)
                    except Exception as e:
                        st.error(f"파일 읽기 오류: {e}")
        else:
            st.info("저장된 결과 파일이 없습니다.")
    else:
        st.info("저장 디렉토리가 존재하지 않습니다.")
    
    # 파일 경로 정보
    st.markdown("---")
    st.subheader("📁 파일 경로 정보")
    
    current_dir = os.path.dirname(__file__)
    chatbot_dir = os.path.abspath(os.path.join(current_dir, '../chatbot'))
    uploader_file = os.path.join(chatbot_dir, 'github_xml_uploader.py')
    
    st.info(f"📂 현재 디렉토리: {current_dir}")
    st.info(f"🎯 실행 디렉토리: {chatbot_dir}")
    st.info(f"📄 스크립트 파일: {uploader_file}")
    st.info(f"💾 저장 디렉토리: {save_dir}")
    
    # 파일 존재 여부 확인
    if os.path.exists(uploader_file):
        st.success("✅ github_xml_uploader.py 파일이 존재합니다")
    else:
        st.error("❌ github_xml_uploader.py 파일을 찾을 수 없습니다")
        st.error(f"예상 경로: {uploader_file}")

def get_driver(headless=False):  # headless=False로 설정
    global _driver

    # 기존 드라이버가 살아있는지 확인하고, 살아있으면 종료
    if _driver is not None:
        try:
            if _driver.window_handles:
                _driver.quit()  # 기존 드라이버 종료
        except WebDriverException:
            pass  # 드라이버가 정상적으로 종료되지 않으면 새로 시작

    # 크롬 드라이버 설정
    chrome_path = "C:/chromedriver.exe"
    service = Service(executable_path=chrome_path)

    options = Options()
    if headless:
        options.add_argument("--headless")
    else:
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-features=site-per-process")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-infobars")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_experimental_option("detach", True)

    # 유저 프로필 디렉토리 설정
    profile_dir = "E:/selenium_profiles/naver"
    options.add_argument(f"user-data-dir={profile_dir}")

    # 알림, 이미지 로딩 제한
    prefs = {
        "profile.default_content_setting_values.notifications": 2,
        "profile.managed_default_content_settings.images": 1
    }
    options.add_experimental_option("prefs", prefs)

    # 크롬 실행
    _driver = webdriver.Chrome(service=service, options=options)

    # 실행 로그 파일 초기화
    try:
        with open("../data/selenium_chrome_action_log.txt", "w", encoding="utf-8") as f:
            pass  # 기존 로그 비우기

        launch_time = datetime.now().isoformat()
        start_url = _driver.current_url if _driver.current_url else "N/A"

        with open(LAUNCH_LOG, 'w', encoding='utf-8') as f:
            f.write(f"launch_time: {launch_time}\n")
            f.write(f"start_url: {start_url}\n")

        print(f"📄 실행 정보 저장 완료: {LAUNCH_LOG}")
    except Exception as e:
        print(f"⚠️ 실행 정보 저장 실패: {e}")

    # 창을 맨 앞으로 가져오기
    _driver.execute_script("window.focus();")  # 자바스크립트로 창 포커스

    return _driver

def create_driver_if_needed():
    return get_driver(headless=False)  # headless=False로 설정하여 실제 브라우저 창을 띄움

# 콘솔 한글 깨짐 방지를 위한 설정 (선택사항)
sys.stdout.reconfigure(encoding='utf-8')

# 상태 메시지 설정 함수
def set_bottom_message(message: str):
    st.session_state.bottom_message = message

def main():
    st.set_page_config(page_title="N/B 분석기 with 자동화", layout="wide")

    # 세션 상태 초기화
    if "page" not in st.session_state:
        st.session_state.page = "nb"
    if "bottom_message" not in st.session_state:
        st.session_state.bottom_message = "🧾 상태 메시지: 이 영역은 항상 하단에 고정됩니다."

    # 사이드바 메뉴
    st.sidebar.markdown("## 📂 메뉴")
    menu_items = {
        "nb": "🔍 N/B 분석기",
        "blog": "📝 블로그 자동화",
        "write": "글쓰기",
        "nb_scout": "🛰 NB-Scout 자동 실행",
        "github_uploader": "🚀 GitHub XML Uploader",
        "gpu_automation": "⚡ GPU 자동화 도구",  # ✅ GPU 자동화 메뉴 추가
        "text_sim": "🔤 텍스트 유사도 (NB)"
    }

    for key, label in menu_items.items():
        if st.sidebar.button(label, key=f"menu_{key}"):
            st.session_state.page = key

    st.sidebar.markdown("---")

    # 페이지 렌더링
    if st.session_state.page == "nb":
        from apps.nb_analyzer.ui import render_nb_analysis_ui
        render_nb_analysis_ui()

    elif st.session_state.page == "blog":
        render_blog_ui()

    elif st.session_state.page == "write":
        render_write_ui(set_bottom_message)  # ✅ 메시지 설정 함수 전달

    elif st.session_state.page == "nb_scout":
        from apps.nb_scout.ui import render_nb_scout_page
        render_nb_scout_page()

    elif st.session_state.page == "github_uploader":  # ✅ GitHub Uploader 페이지 추가
        render_github_xml_uploader()
        
    elif st.session_state.page == "gpu_automation":  # ✅ GPU 자동화 페이지 추가
        render_gpu_automation()

    elif st.session_state.page == "text_sim":
        render_text_similarity_page()

    # ✅ 하단 상태 메시지 출력
    st.markdown(f"""
        <div style="
            position: fixed;
            bottom: 0px;
            left: 0px;
            width: 100%;
            height: 40px;
            background-color: rgb(231, 231, 231);
            border-top: 1px solid rgb(221, 221, 221);
            padding: 10px 20px;
            font-size: 16px;
            color: rgb(51, 51, 51);
            z-index: 9999;
            text-align: right;">
            {st.session_state.bottom_message}
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
