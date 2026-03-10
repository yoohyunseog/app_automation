# apps/nb_analyzer/ui.py
import sys
import os
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from components.signal_badge import render_signal_badge
from components.nb_chart import render_nb_chart
from apps.nb_automation.contents_scraper import contents_scraper, load_saved_contents
from apps.nb_automation.view_scraper import scrape_views
from apps.nb_math.bitCalculation_v_0_2 import BIT_MAX_NB, BIT_MIN_NB
import xml.etree.ElementTree as ET
from datetime import datetime
import shutil

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def log_action(message):
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)

    with open("../../../data/selenium_chrome_action_log.txt", 'a', encoding='utf-8') as f:
        f.write(log_entry + "\n")

def render_nb_analysis_ui():
    df_saved = None  # 💡 명시적으로 초기화
    st.title("🧠 STOP-MATCH 기반 N/B 유사도 분석기")

    # 👉 사용자 입력
    bit_value = st.sidebar.slider("BIT 값", 1.0, 10.0, 5.5, step=0.1)
    user_input = st.sidebar.text_area("🔍 비교할 문장", "예시 문장 입력...")
    
    # 👉 저장 폴더 입력 필드 추가
    st.sidebar.markdown("### 📂 저장 설정")
    save_folder = st.sidebar.text_input(
        "💾 저장 폴더 경로", 
        value=st.session_state.get('save_folder', ''),
        placeholder="예: E:/Ai project/custom_save",
        help="XML 파일이 저장될 폴더 경로를 입력하세요"
    )
    
    # 👉 폴더 입력 시 자동 저장 감지
    if save_folder and save_folder != st.session_state.get('save_folder', ''):
        st.session_state['save_folder'] = save_folder
        st.sidebar.success(f"📁 저장 폴더 설정: {save_folder}")
        # 자동 새로고침을 위한 상태 저장
        st.session_state['auto_save_trigger'] = True
        st.rerun()

    col1, col2 = st.columns([1, 3])
    with col1:
        render_signal_badge(signal_type="STOP", status="ACTIVE")
    with col2:
        st.info("현재 분석 문장 또는 시그널 흐름을 기반으로 NB 상태를 분석합니다.")

    # 👉 분석 로그
    st.markdown("### 📝 분석 로그")
    st.code(f"입력한 문장: {user_input}\nBIT 값: {bit_value}\n저장 폴더: {save_folder or '기본 폴더'}")
    
    # 👉 조회수 크롤링 버튼 + 시간 태그 입력
    # 👉 조회수 수동 입력란 + 버튼
    st.markdown("### 📡 수동 조회수 기록")
    col_btn, col_input = st.columns([1, 3])
    with col_input:
        manual_view_count = st.text_input("현재 조회수 수동 입력", placeholder="예: 1234")

    # 👉 조회수 크롤링 버튼
    if st.button("📡 조회수 데이터 크롤링 실행"):
        with st.spinner("조회수 데이터를 수집 중입니다..."):
            try:
                log_action(f"🧠 조회수 데이터를 수집 중입니다")
                data = scrape_views()  # 리스트 형태 [{"date": ..., "views": ...}, ...]

                # 👉 수동 입력이 있을 경우, 가장 첫줄에 삽입
                if manual_view_count.strip().isdigit():
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    data.insert(0, {
                        "date": now,
                        "views": int(manual_view_count)
                    })

                # 👉 views 배열 추출
                views_array = [entry["views"] for entry in data if "views" in entry]

                # 👉 BIT 계산
                today_veiw_bit_max = BIT_MAX_NB(views_array, bit_value)
                today_veiw_bit_min = BIT_MIN_NB(views_array, bit_value)

                # 👉 출력
                st.success("✅ 조회수 데이터 수집 및 BIT 계산 완료!")
                # st.json(data)

                st.markdown("### 🧠 BIT 계산 결과")
                st.metric(label="BIT_MAX_NB", value=f"{today_veiw_bit_max:.4f}")
                st.metric(label="BIT_MIN_NB", value=f"{today_veiw_bit_min:.4f}")

            except Exception as e:
                st.error(f"❌ 크롤링 실패: {e}")

    # 👉 앱 시작 시 최신 콘텐츠 테이블 표시
    if df_saved is None:
        df_saved = load_saved_contents()
    if not df_saved.empty:
        st.markdown("### 📁 저장된 콘텐츠 목록 (최근 수집본)")
        st.dataframe(df_saved)

        if "views" in df_saved.columns:
            views_array = df_saved["views"].tolist()
            st.markdown("### 🔢 저장된 콘텐츠 조회수 배열")

            # 👉 BIT 계산
            today_veiw_bit_max = BIT_MAX_NB(views_array, bit_value)
            today_veiw_bit_min = BIT_MIN_NB(views_array, bit_value)

            # 👉 결과 출력
            st.markdown("### 🧠 BIT 기반 분석 결과")
            st.metric(label="BIT_MAX_NB", value=f"{today_veiw_bit_max:.4f}")
            st.metric(label="BIT_MIN_NB", value=f"{today_veiw_bit_min:.4f}")
        else:
            st.warning("⚠️ 'views' 컬럼이 존재하지 않습니다.")
    else:
        st.info("📭 아직 저장된 콘텐츠 데이터가 없습니다.")

    # 👉 콘텐츠 수집 버튼
    if st.button("📰 콘텐츠 랭킹 수집 실행"):
        with st.spinner("콘텐츠 데이터를 수집 중입니다..."):
            try:
                data = contents_scraper()
                st.success("✅ 콘텐츠 수집 완료! (날짜별 저장됨)")

                if data:
                    df = pd.DataFrame(data)

                    # 👉 조회수 배열 추출
                    if "views" in df.columns:
                        views_array = df["views"].tolist()

                        # 👉 배열 출력
                        st.markdown("### 🔢 조회수 배열")

                        # 👉 BIT 계산
                        con_rank_bit_max = BIT_MAX_NB(views_array, bit_value)
                        con_rank_bit_min = BIT_MIN_NB(views_array, bit_value)

                        # 👉 BIT 결과 출력
                        st.markdown("### 🧠 BIT 기반 분석 결과")
                        st.metric(label="BIT_MAX_NB", value=f"{con_rank_bit_max:.4f}")
                        st.metric(label="BIT_MIN_NB", value=f"{con_rank_bit_min:.4f}")

                    else:
                        st.warning("⚠️ 'views' 컬럼이 존재하지 않습니다.")
                else:
                    st.info("ℹ️ 수집된 콘텐츠가 없습니다.")
            except Exception as e:
                st.error(f"❌ 콘텐츠 수집 실패: {e}")

    # 👉 저장된 방문자 수 데이터 시각화
    st.markdown("### 📊 저장된 블로그 방문자 수 변화")

    blog_view_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../data/blog_views'))

    if os.path.exists(blog_view_dir):
        csv_files = [f for f in os.listdir(blog_view_dir) if f.endswith(".csv")]
        all_data = []

        for file in csv_files:
            file_path = os.path.join(blog_view_dir, file)
            try:
                df = pd.read_csv(file_path)
                all_data.append(df)
            except Exception as e:
                st.warning(f"⚠️ {file} 불러오기 실패: {e}")

    if all_data:
        df_all = pd.concat(all_data)
        df_all["date"] = pd.to_datetime(df_all["date"])
        df_all = df_all.sort_values("date")
        df_all = df_all.set_index("date")

        # 👉 집계 단위 선택
        view_mode = st.selectbox("집계 단위 선택", ["일간", "주간", "월간"])

        if view_mode == "일간":
            chart_df = df_all

            # 👉 7일 단위로 나누어 BIT 계산
            st.markdown("### 🧠 7일 단위 BIT 분석 테이블 (일간 데이터 기준)")
            weekly_results = []
            start_idx = 0
            rows = chart_df.shape[0]

            while start_idx + 7 <= rows:
                week_df = chart_df.iloc[start_idx:start_idx + 7]
                nb_list = week_df["views"].tolist()
                bit_max = BIT_MAX_NB(nb_list, bit_value)
                bit_min = BIT_MIN_NB(nb_list, bit_value)
                week_range = f"{week_df.index[0].date()} ~ {week_df.index[-1].date()}"

                weekly_results.append({
                    "기간": week_range,
                    "BIT_MAX_NB": round(bit_max, 4),
                    "BIT_MIN_NB": round(bit_min, 4),
                })

                start_idx += 7

            st.dataframe(pd.DataFrame(weekly_results))

            # 👉 시각화
            st.markdown("### 📈 일간 방문자 수 추이")
            fig, ax = plt.subplots()
            ax.plot(chart_df.index, chart_df["views"], marker="o")
            ax.set_title("📊 일간 블로그 방문자 수")
            ax.set_xlabel("날짜")
            ax.set_ylabel("방문자 수")
            plt.xticks(rotation=45)
            st.pyplot(fig)

        elif view_mode == "주간":
            chart_df = df_all.resample("W").sum()
        elif view_mode == "월간":
            chart_df = df_all.resample("M").sum()

        if view_mode in ["주간", "월간"]:
            nb_list = chart_df["views"].tolist()
            bit_max = BIT_MAX_NB(nb_list, bit_value)
            bit_min = BIT_MIN_NB(nb_list, bit_value)

            st.markdown("### 🧠 BIT 기반 시간 흐름 분석 결과")
            st.metric(label=f"{view_mode} 기준 BIT_MAX_NB", value=f"{bit_max:.4f}")
            st.metric(label=f"{view_mode} 기준 BIT_MIN_NB", value=f"{bit_min:.4f}")

            fig, ax = plt.subplots()
            ax.plot(chart_df.index, chart_df["views"], marker="o")
            ax.set_title(f"📊 {view_mode} 블로그 방문자 수")
            ax.set_xlabel(view_mode)
            ax.set_ylabel("방문자 수")
            plt.xticks(rotation=45)
            st.pyplot(fig)

        if st.button("💾 화면 정보 XML로 저장"):
            with st.spinner("콘텐츠 데이터를 수집 중입니다..."):
                try:
                    data = contents_scraper()
                    st.success("✅ 콘텐츠 수집 완료! (날짜별 저장됨)")

                    df = pd.DataFrame(data) if data else pd.DataFrame()
                    views_array = df["views"].tolist() if "views" in df.columns else []

                    con_rank_bit_max = BIT_MAX_NB(views_array, bit_value) if views_array else 0
                    con_rank_bit_min = BIT_MIN_NB(views_array, bit_value) if views_array else 0

                except Exception as e:
                    st.error(f"❌ 콘텐츠 수집 실패: {e}")
                    df = pd.DataFrame()
                    views_array = []
                    con_rank_bit_max = con_rank_bit_min = 0
                    data = []

            with st.spinner("조회수 데이터를 수집 중입니다..."):
                try:
                    log_action(f"🧠 조회수 데이터를 수집 중입니다")
                    data = scrape_views()  # 리스트 형태 [{"date": ..., "views": ...}, ...]

                    # 👉 수동 입력이 있을 경우, 가장 첫줄에 삽입
                    if manual_view_count.strip().isdigit():
                        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        data.insert(0, {
                            "date": now,
                            "views": int(manual_view_count)
                        })

                    # 👉 views 배열 추출
                    views_array = [entry["views"] for entry in data if "views" in entry]

                    # 👉 BIT 계산
                    today_veiw_bit_max = BIT_MAX_NB(views_array, bit_value)
                    today_veiw_bit_min = BIT_MIN_NB(views_array, bit_value)

                    # 👉 출력
                    st.success("✅ 조회수 데이터 수집 및 BIT 계산 완료!")
                    # st.json(data)

                    st.markdown("### 🧠 BIT 계산 결과")
                    st.metric(label="BIT_MAX_NB", value=f"{today_veiw_bit_max:.4f}")
                    st.metric(label="BIT_MIN_NB", value=f"{today_veiw_bit_min:.4f}")

                except Exception as e:
                    st.error(f"❌ 크롤링 실패: {e}")
                    
            # ✅ 기본값 보장
            weekly_results = weekly_results if 'weekly_results' in locals() else None
            view_mode = view_mode if 'view_mode' in locals() else "일간"
            chart_df = chart_df if 'chart_df' in locals() else None

            if df_saved is not None and "views" in df_saved.columns:
                xml_path = save_analysis_to_xml(
                    bit_value=bit_value,
                    user_input=user_input,
                    df_saved=df_saved,
                    con_rank_bit_max=con_rank_bit_max,
                    con_rank_bit_min=con_rank_bit_min,
                    today_veiw_bit_max=today_veiw_bit_max,
                    today_veiw_bit_min=today_veiw_bit_min,
                    weekly_results=weekly_results,
                    view_mode=view_mode,
                    chart_df=chart_df,
                    collected_data=data,
                    save_folder=save_folder
                )
                st.success(f"📦 XML 저장 완료: {xml_path}")
                
                # 👉 자동으로 기본 폴더에도 덮어쓰기 저장
                try:
                    # 기본 저장 폴더 경로
                    current_dir = os.path.dirname(__file__)
                    default_save_dir = os.path.abspath(os.path.join(current_dir, "../../../data/save/m.naver.blog/xml"))
                    default_filename = "nb_analysis_output.xml"
                    default_save_path = os.path.join(default_save_dir, default_filename)
                    
                    # 기본 폴더가 다른 경로인 경우에만 추가 저장
                    if os.path.normpath(xml_path) != os.path.normpath(default_save_path):
                        # 기본 폴더 생성
                        os.makedirs(default_save_dir, exist_ok=True)
                        
                        # 파일 복사 (덮어쓰기)
                        shutil.copy2(xml_path, default_save_path)
                        st.success(f"✅ 기본 폴더에도 자동 저장 완료!")
                        st.info(f"📂 기본 저장 위치: {default_save_path}")
                    else:
                        st.info(f"📂 이미 기본 폴더에 저장되어 있습니다")
                        
                except Exception as e:
                    st.warning(f"⚠️ 기본 폴더 자동 저장 실패: {e}")
                    st.info("💡 수동 다운로드 버튼을 사용해주세요")
                
                # 👉 수동 다운로드 옵션 (자동 저장 실패 시 사용)
                with st.expander("🔧 수동 다운로드 옵션 (자동 저장 실패 시)", expanded=False):
                    st.info("💡 위의 자동 저장이 실패한 경우에만 사용하세요")
                    
                    if st.button("📥 수동으로 기본 폴더에 저장"):
                        # 수동 다운로드 전용 경로 설정
                        current_dir = os.path.dirname(__file__)
                        download_target_dir = os.path.abspath(os.path.join(current_dir, "../../../data/save/m.naver.blog/xml"))
                        download_filename = "nb_analysis_output.xml"
                        download_path = os.path.join(download_target_dir, download_filename)
                        
                        st.info("🔄 수동 XML 다운로드 시작...")
                        try:
                            # 현재 상태 로그
                            st.info(f"📁 원본 파일: {xml_path}")
                            st.info(f"📁 대상 파일: {download_path}")
                            
                            # 원본 파일 존재 확인
                            if not os.path.exists(xml_path):
                                st.error(f"❌ 원본 파일이 존재하지 않습니다: {xml_path}")
                                return
                            
                            st.success(f"✅ 원본 파일 확인 완료")
                            
                            # 다운로드 폴더 생성
                            st.info(f"📂 대상 폴더 생성 중: {download_target_dir}")
                            os.makedirs(download_target_dir, exist_ok=True)
                            st.success(f"✅ 대상 폴더 준비 완료")
                            
                            # 파일 복사 (덮어쓰기)
                            st.info("📋 파일 복사 중...")
                            shutil.copy2(xml_path, download_path)
                            st.success(f"✅ 파일 복사 완료")
                            
                            # 결과 확인
                            if os.path.exists(download_path):
                                st.success(f"🎉 XML 수동 다운로드 성공!")
                                st.success(f"📂 저장 위치: {download_path}")
                                
                                # 파일 크기 정보 표시
                                file_size = os.path.getsize(download_path)
                                st.info(f"📏 파일 크기: {file_size:,} bytes")
                                
                                # 파일 수정 시간 정보
                                import time
                                mod_time = os.path.getmtime(download_path)
                                readable_time = time.ctime(mod_time)
                                st.info(f"⏰ 수정 시간: {readable_time}")
                                
                            else:
                                st.error("❌ 파일 저장 실패 - 파일이 생성되지 않았습니다")
                                
                        except PermissionError as e:
                            st.error(f"❌ 권한 오류: {e}")
                            st.error("💡 해결 방법: 관리자 권한으로 실행하거나 다른 폴더를 선택하세요")
                        except FileNotFoundError as e:
                            st.error(f"❌ 파일을 찾을 수 없음: {e}")
                            st.error("💡 해결 방법: 경로를 확인하고 다시 시도하세요")
                        except Exception as e:
                            st.error(f"❌ XML 다운로드 실패: {e}")
                            st.error(f"🔍 상세 오류: {str(e)}")
                            st.error(f"🔍 오류 타입: {type(e).__name__}")
                
                # 👉 브라우저 다운로드 (기존 방식) - 다른 용도
                with st.expander("🌐 브라우저 다운로드 (다른 위치에 저장)", expanded=False):
                    st.info("💡 다운로드 폴더나 다른 위치에 저장하려면 사용하세요")
                with open(xml_path, "rb") as f:
                        st.download_button("📥 브라우저 다운로드", data=f, file_name="nb_analysis_output.xml")
            else:
                st.warning("⚠️ 저장된 데이터가 부족합니다.")

        else:
            st.info("ℹ️ 아직 저장된 방문자 수 데이터가 없습니다.")
    else:
        st.warning("⚠️ blog_views 폴더를 찾을 수 없습니다.")

def save_analysis_to_xml(bit_value, user_input, df_saved, 
    con_rank_bit_max, con_rank_bit_min, 
    today_veiw_bit_max, today_veiw_bit_min,
                         weekly_results=None, view_mode=None, chart_df=None, collected_data=None, save_folder=None):
    root = ET.Element("NB_Analysis")

    meta = ET.SubElement(root, "Meta")
    ET.SubElement(meta, "Timestamp").text = datetime.now().isoformat()
    ET.SubElement(meta, "BIT_Value").text = str(bit_value)
    ET.SubElement(meta, "User_Input").text = user_input

    if df_saved is not None:
        saved_elem = ET.SubElement(root, "SavedContents")
        for _, row in df_saved.iterrows():
            content = ET.SubElement(saved_elem, "Content")
            for col in df_saved.columns:
                ET.SubElement(content, col).text = str(row[col])

    bit_elem = ET.SubElement(root, "BIT_Results")
    ET.SubElement(bit_elem, "CON_RANK_BIT_MAX_NB").text = f"{con_rank_bit_max:.4f}"
    ET.SubElement(bit_elem, "CON_RANK_BIT_MIN_NB").text = f"{con_rank_bit_min:.4f}"

    # 👉 추가: TODAY_VIEW BIT 결과
    ET.SubElement(bit_elem, "TODAY_VIEW_BIT_MAX_NB").text = f"{today_veiw_bit_max:.4f}"
    ET.SubElement(bit_elem, "TODAY_VIEW_BIT_MIN_NB").text = f"{today_veiw_bit_min:.4f}"

    if weekly_results:
        weekly_elem = ET.SubElement(root, "WeeklyBIT")
        for entry in weekly_results:
            period = ET.SubElement(weekly_elem, "Period", name=entry["기간"])
            ET.SubElement(period, "BIT_MAX_NB").text = str(entry["BIT_MAX_NB"])
            ET.SubElement(period, "BIT_MIN_NB").text = str(entry["BIT_MIN_NB"])

    if chart_df is not None and view_mode:
        chart_elem = ET.SubElement(root, "ViewTrend", mode=view_mode)
        for date, row in chart_df.iterrows():
            record = ET.SubElement(chart_elem, "Record")
            ET.SubElement(record, "Date").text = str(date.date())
            ET.SubElement(record, "Views").text = str(row["views"])

    # 👉 파일명은 고정하여 같은 이름으로 덮어쓰기 가능하게 함
    filename = f"nb_analysis_BIT.xml"
    
    # 👉 저장 폴더 결정 (사용자 입력 우선, 없으면 기본 폴더)
    if save_folder and save_folder.strip():
        output_dir = os.path.abspath(save_folder.strip())
        st.info(f"📁 사용자 지정 폴더에 저장: {output_dir}")
    else:
        output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/save/m.naver.blog/xml"))
        st.info(f"📁 기본 폴더에 저장: {output_dir}")

    # 💡 디렉토리가 없으면 생성
    try:
        os.makedirs(output_dir, exist_ok=True)
        st.success(f"✅ 저장 폴더 준비 완료: {output_dir}")
    except Exception as e:
        st.error(f"❌ 저장 폴더 생성 실패: {e}")
        # 폴더 생성 실패 시 기본 폴더 사용
        output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/save/m.naver.blog/xml"))
        os.makedirs(output_dir, exist_ok=True)
        st.warning(f"⚠️ 기본 폴더로 대체: {output_dir}")

    xml_path = os.path.join(output_dir, filename)

    # 👉 중복 파일이 있으면 덮어쓰기 경고 메시지
    if os.path.exists(xml_path):
        st.warning(f"🔄 기존 파일을 덮어쓰기합니다: {filename}")
    else:
        st.info(f"📝 새 파일을 생성합니다: {filename}")
    
    # 👉 XML 파일 저장 (기존 파일이 있으면 자동으로 덮어쓰기됨)
    tree = ET.ElementTree(root)
    try:
        tree.write(xml_path, encoding="utf-8", xml_declaration=True)
        st.success(f"✅ XML 파일 저장 완료! 📂 {xml_path}")
    except Exception as e:
        st.error(f"❌ XML 파일 저장 실패: {e}")
        raise e
    
    return xml_path
