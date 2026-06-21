'''import streamlit as st
import pandas as pd
import time
import os

from src.tracker import process_video
from src.ball_touch import BallTouchReferee
import config

st.set_page_config(page_title="SPaiKE V - 배구 경기 분석", layout="wide")


# ==========================================
# [초기화] 기본값 및 상태 저장소 (🚀 F5 새로고침 완벽 방어)
# ==========================================
def reset_params():
    """파라미터 초기화 버튼을 누르면 슬라이더 값들만 기본값으로 되돌립니다."""
    st.session_state.p_conf = config.DEFAULT_P_CONF
    st.session_state.p_buf = config.DEFAULT_P_BUF
    st.session_state.p_match = config.DEFAULT_P_MATCH
    st.session_state.b_conf = config.DEFAULT_B_CONF
    st.session_state.b_buf = config.DEFAULT_B_BUF
    st.session_state.b_match = config.DEFAULT_B_MATCH
    st.session_state.b_detect_conf = config.DEFAULT_B_DETECT_CONF

# 💡 [핵심 수정] p_conf 하나만 검사하는 게 아니라, 각각의 변수가 있는지 꼼꼼하게 독립적으로 검사합니다!
if 'p_conf' not in st.session_state: st.session_state.p_conf = float(st.query_params.get("p_conf", config.DEFAULT_P_CONF))
if 'p_buf' not in st.session_state: st.session_state.p_buf = int(st.query_params.get("p_buf", config.DEFAULT_P_BUF))
if 'p_match' not in st.session_state: st.session_state.p_match = float(st.query_params.get("p_match", config.DEFAULT_P_MATCH))
if 'b_conf' not in st.session_state: st.session_state.b_conf = float(st.query_params.get("b_conf", config.DEFAULT_B_CONF))
if 'b_buf' not in st.session_state: st.session_state.b_buf = int(st.query_params.get("b_buf", config.DEFAULT_B_BUF))
if 'b_match' not in st.session_state: st.session_state.b_match = float(st.query_params.get("b_match", config.DEFAULT_B_MATCH))
if 'b_detect_conf' not in st.session_state: st.session_state.b_detect_conf = float(st.query_params.get("b_detect_conf", config.DEFAULT_B_DETECT_CONF))
if 'model_choice' not in st.session_state: st.session_state.model_choice = st.query_params.get("model_choice", "직접 학습시킨 모델 (Fine-Tuned)")
if 'ball_track_method' not in st.session_state: st.session_state.ball_track_method = st.query_params.get("ball_track_method", "Frame-by-frame detection")

if 'applied_params' not in st.session_state:
    st.session_state.applied_params = None

# 💡 [핵심] UI 락(잠금)과 결과 유지를 위한 상태 변수
if 'clicked_start' not in st.session_state: st.session_state.clicked_start = False
if 'is_running' not in st.session_state: st.session_state.is_running = False
if 'is_completed' not in st.session_state: st.session_state.is_completed = False
if 'final_video_path' not in st.session_state: st.session_state.final_video_path = None

# ==========================================
# 좌측 사이드바 (컨트롤 패널)
# ==========================================
with st.sidebar:
    st.header("⚙️ 분석 설정")
    is_locked = st.session_state.is_running 
    
    model_choice = st.selectbox("모델 설정", ("직접 학습시킨 모델 (Fine-Tuned)", "기본 모델 (YOLOv8s)"), key="model_choice", disabled=is_locked)
    ball_track_method = st.selectbox("공 위치 추정 방식", ("Frame-by-frame detection", "ByteTrack"), key="ball_track_method", disabled=is_locked)
    st.caption("※ ByteTrack은 성능 비교를 위해 제공되는 옵션입니다. 배구공의 빠른 이동 및 가림 현상으로 인해 최종 시스템에서는 frame-by-frame detection 방식을 채택했습니다.")
    st.divider()
    
    st.header("객체 탐지 및 추적 임계값")    
    st.subheader("🏃‍♂️ 선수 트래커 (BoT-SORT)")
    p_conf = st.slider("객체 탐지 임계값(Confidence)", 0.0, 1.0, value=st.session_state.p_conf, key="p_conf", step=0.05, disabled=is_locked)
    p_buf = st.slider("추적 유지 프레임 (Track Buffer)", 0, 150, value=st.session_state.p_buf, key="p_buf", step=5, disabled=is_locked)
    p_match = st.slider("매칭 임계값 (Match Threshold)", 0.0, 1.0, value=st.session_state.p_match, key="p_match", step=0.05, disabled=is_locked)
    st.divider() 

    if ball_track_method == "ByteTrack":
        st.subheader("🏐 공 트래커 (ByteTrack)")
        b_conf = st.slider("객체 탐지 임계값(Confidence)", 0.0, 1.0, value=st.session_state.b_conf, key="b_conf", step=0.01, disabled=is_locked)
        b_buf = st.slider("추적 유지 프레임 (Track Buffer)", 0, 100, value=st.session_state.b_buf, key="b_buf", step=5, disabled=is_locked)
        b_match = st.slider("매칭 임계값 (Match Threshold)", 0.0, 1.0, value=st.session_state.b_match, key="b_match", step=0.05, disabled=is_locked)
    else:
        st.subheader("🏐 공 Frame-by-frame detection") 
        b_conf = st.slider('객체 탐지 임계값(Confidence)', 0.0, 1.0, value=st.session_state.b_detect_conf, key="b_detect_conf", step=0.01, disabled=is_locked)
        b_buf = config.DEFAULT_B_BUF
        b_match = config.DEFAULT_B_MATCH

    st.button("파라미터 설정 초기화", on_click=reset_params, use_container_width=True, disabled=is_locked)
    
    st.query_params["p_conf"] = st.session_state.p_conf
    st.query_params["p_buf"] = st.session_state.p_buf
    st.query_params["p_match"] = st.session_state.p_match
    st.query_params["b_conf"] = st.session_state.b_conf
    st.query_params["b_buf"] = st.session_state.b_buf
    st.query_params["b_match"] = st.session_state.b_match
    st.query_params["b_detect_conf"] = st.session_state.b_detect_conf
    st.query_params["model_choice"] = st.session_state.model_choice
    st.query_params["ball_track_method"] = st.session_state.ball_track_method
    
    st.divider()
    
    # 5. 파일 업로드 및 분석 시작
    uploaded_file = st.file_uploader("분석할 경기 영상 업로드", disabled=is_locked)
    is_valid_file = False
    if uploaded_file is not None:
        if uploaded_file.name.lower().endswith(('.mp4', '.avi')): is_valid_file = True
        else: st.error("❌ 지원하지 않는 파일 형식입니다. (mp4 또는 avi 권장)")

    # 💡 버튼 클릭 시 분석 신호 전달
    def click_analyze(): st.session_state.clicked_start = True
    st.button("분석 시작", type="primary", use_container_width=True, on_click=click_analyze, disabled=is_locked)

    if st.session_state.clicked_start:
        if uploaded_file is None:
            st.warning("⚠️ 분석할 영상을 먼저 업로드해주세요.")
            st.session_state.clicked_start = False
        elif not is_valid_file:
            st.error("❌ 파일 형식이 잘못되었습니다.") 
            st.session_state.clicked_start = False
        else:
            st.session_state.is_running = True
            st.session_state.is_completed = False
            st.session_state.clicked_start = False
            st.session_state.applied_params = {
                "모델": model_choice, "방식": ball_track_method,
                "선수 Conf": p_conf, "선수 Buffer": p_buf, "선수 Match": p_match,
                "공 Conf": b_conf, 
                "공 Buffer": b_buf if ball_track_method == "ByteTrack" else "해당 없음",
                "공 Match": b_match if ball_track_method == "ByteTrack" else "해당 없음"
            }
            st.rerun()

    if st.session_state.applied_params:
        st.success("✅ 현재 적용된 파라미터")
        for key, value in st.session_state.applied_params.items():
            st.write(f"**{key}:** {value}")

# ==========================================
# 메인 화면 (결과 대시보드)
# ==========================================
st.title("지능형 배구 경기 분석 대시보드: SPaiKE V")
st.markdown("동영상을 업로드하고 사이드바에서 설정을 마친 뒤, 아래의 **분석 시작** 버튼을 누르세요.")

if not os.path.exists("temp"): os.makedirs("temp")

# 🔄 1. 분석 진행 중 화면
if st.session_state.is_running:
    temp_video_path = os.path.join("temp", uploaded_file.name)
    with open(temp_video_path, "wb") as f: f.write(uploaded_file.getbuffer())

    col1, col2 = st.columns([1, 1]) 
    with col1:
        st.subheader("1. 경기 분석 시각화")
        status_msg = st.empty()
        progress_bar = st.progress(0)
        st_frame = st.empty() 
        
        output_video_path, df, ball_trajectory, player_tracks_history= process_video(
            video_path=temp_video_path, model_choice=model_choice, ball_track_method=ball_track_method,
            p_conf=p_conf, p_buf=p_buf, p_match=p_match, b_conf=b_conf, b_buf=b_buf, b_match=b_match,
            st_frame=st_frame, progress_bar=progress_bar, status_msg=status_msg
        )
        
        st.session_state.final_video_path = output_video_path
        st.session_state.ball_trajectory = ball_trajectory
        st.session_state.player_tracks_history = player_tracks_history
        st.session_state.is_completed = True
        st.session_state.is_running = False
        st.rerun()

# ✨ 2. 분석 완료 화면 (💡 대망의 해결책 적용!)
elif st.session_state.is_completed:
    col1, col2 = st.columns([1, 1]) 
    with col1:
        st.subheader("1. 경기 분석 시각화")
        st.success("✨ 분석이 완료되었습니다!")
        
        # 💡 [핵심] OS가 파일을 완전히 저장할 시간을 0.5초 벌어준 뒤, 바이트로 읽어서 강제 송출!
        time.sleep(0.5) 
        with open(st.session_state.final_video_path, 'rb') as video_file:
            video_bytes = video_file.read()
            
        st.video(video_bytes, format="video/mp4")

    with col2:
        st.subheader("2. 선수 별 공 터치 카운트")
        # 2. 선수 별 공 터치 카운트 로직 구현
        if st.session_state.is_completed:
            # 설정값 정의 (적절한 임계값으로 튜닝 필요)
            FRAME_WINDOW = 5
            SPEED_THRESH = 2.0
            ANGLE_THRESH = 0.5
            
            # BallTouchReferee 실행
            # 주의: video_path는 분석이 완료된 경로, 임계값은 필요에 따라 조절
            referee = BallTouchReferee(
                st.session_state.ball_trajectory,
                st.session_state.player_tracks_history,
                FRAME_WINDOW,
                SPEED_THRESH,
                ANGLE_THRESH
            )
            
            # start() 대신 직접 함수들을 호출하거나 내부 데이터를 활용하여 카운팅
            referee.start()
            
            # 선수별 터치 횟수 집계
            touch_counts = {}
            for f in referee.change_frames:
                pid, dist = referee.find_closest_player(f, referee.ball_positions.get(f, (0,0)))
                if pid:
                    touch_counts[pid] = touch_counts.get(pid, 0) + 1
            
            # 결과 DataFrame 생성
            if touch_counts:
                df_touches = pd.DataFrame(
                    list(touch_counts.items()), 
                    columns=["선수 ID", "터치 횟수"]
                ).set_index("선수 ID")
                
                # 차트 표시
                st.bar_chart(df_touches, color="#ff4b4b")
                
                # 요약 정보
                max_id = df_touches["터치 횟수"].idxmax()
                max_val = df_touches["터치 횟수"].max()
                st.info(f"🏆 **가장 많이 공을 터치한 선수:** ID:{max_id} ({max_val}회)")
            else:
                st.warning("분석된 터치 데이터가 없습니다. 임계값을 조정해보세요.")

'''


import time

import pandas as pd
import streamlit as st

import config
from src.pipeline import process_video
# from src.video_io import ensure_directories, save_uploaded_video
from src.video_io import (
    ensure_directories,
    save_uploaded_video,
    request_stop,
    clear_stop_request,
)



st.set_page_config(
    page_title="SPaiKE V - 배구 경기 분석",
    layout="wide"
)


# ==========================================
# 상태 초기화
# ==========================================
def init_session_state():
    defaults = {
        "p_conf": config.DEFAULT_P_CONF,
        "p_buf": config.DEFAULT_P_BUF,
        "p_match": config.DEFAULT_P_MATCH,
        "b_conf": config.DEFAULT_B_CONF,
        "b_buf": config.DEFAULT_B_BUF,
        "b_match": config.DEFAULT_B_MATCH,
        "b_detect_conf": config.DEFAULT_B_DETECT_CONF,
        "model_choice": config.MODEL_FINE_TUNED,
        "ball_track_method": config.BALL_METHOD_FRAME,
        "is_running": False,
        "is_completed": False,
        "result": None,
        "applied_params": None,
        "pending_video_path": None,
        "run_params": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_params():
    st.session_state.p_conf = config.DEFAULT_P_CONF
    st.session_state.p_buf = config.DEFAULT_P_BUF
    st.session_state.p_match = config.DEFAULT_P_MATCH
    st.session_state.b_conf = config.DEFAULT_B_CONF
    st.session_state.b_buf = config.DEFAULT_B_BUF
    st.session_state.b_match = config.DEFAULT_B_MATCH
    st.session_state.b_detect_conf = config.DEFAULT_B_DETECT_CONF


init_session_state()
ensure_directories()


# ==========================================
# 사이드바
# ==========================================
with st.sidebar:
    st.header("⚙️ 분석 설정")

    is_locked = st.session_state.is_running

    model_choice = st.selectbox(
        "모델 설정",
        (config.MODEL_FINE_TUNED, config.MODEL_BASE),
        key="model_choice",
        disabled=is_locked,
    )

    ball_track_method = st.selectbox(
        "공 위치 추정 방식",
        (config.BALL_METHOD_FRAME, config.BALL_METHOD_BYTETRACK),
        key="ball_track_method",
        disabled=is_locked,
    )

    st.caption(
        "※ ByteTrack은 성능 비교용입니다. 배구공은 빠르게 이동하고 가려지는 경우가 많아 "
        "최종 시스템에서는 Frame-by-frame detection 방식이 더 안정적일 수 있습니다."
    )

    st.divider()

    st.header("객체 탐지 및 추적 임계값")

    st.subheader("🏃‍♂️ 선수 트래커: BoT-SORT")

    p_conf = st.slider(
        "선수 탐지 임계값 Confidence",
        0.0,
        1.0,
        value=float(st.session_state.p_conf),
        key="p_conf",
        step=0.05,
        disabled=is_locked,
    )

    p_buf = st.slider(
        "선수 추적 유지 프레임 Track Buffer",
        0,
        150,
        value=int(st.session_state.p_buf),
        key="p_buf",
        step=5,
        disabled=is_locked,
    )

    p_match = st.slider(
        "선수 매칭 임계값 Match Threshold",
        0.0,
        1.0,
        value=float(st.session_state.p_match),
        key="p_match",
        step=0.05,
        disabled=is_locked,
    )

    st.divider()

    if ball_track_method == config.BALL_METHOD_BYTETRACK:
        st.subheader("🏐 공 트래커: ByteTrack")

        b_conf = st.slider(
            "공 탐지 임계값 Confidence",
            0.0,
            1.0,
            value=float(st.session_state.b_conf),
            key="b_conf",
            step=0.01,
            disabled=is_locked,
        )

        b_buf = st.slider(
            "공 추적 유지 프레임 Track Buffer",
            0,
            100,
            value=int(st.session_state.b_buf),
            key="b_buf",
            step=5,
            disabled=is_locked,
        )

        b_match = st.slider(
            "공 매칭 임계값 Match Threshold",
            0.0,
            1.0,
            value=float(st.session_state.b_match),
            key="b_match",
            step=0.05,
            disabled=is_locked,
        )

    else:
        st.subheader("🏐 공 Frame-by-frame detection")

        b_conf = st.slider(
            "공 탐지 임계값 Confidence",
            0.0,
            1.0,
            value=float(st.session_state.b_detect_conf),
            key="b_detect_conf",
            step=0.01,
            disabled=is_locked,
        )

        b_buf = config.DEFAULT_B_BUF
        b_match = config.DEFAULT_B_MATCH

    st.button(
        "파라미터 설정 초기화",
        on_click=reset_params,
        use_container_width=True,
        disabled=is_locked,
    )

    st.divider()

    uploaded_file = st.file_uploader(
        "분석할 경기 영상 업로드",
        disabled=is_locked,
    )

    is_valid_file = False

    if uploaded_file is not None:
        file_name = uploaded_file.name.lower()

        if file_name.endswith((".mp4", ".avi")):
            is_valid_file = True
        else:
            st.error("❌ 파일 형식이 잘못되었습니다. mp4 또는 avi 파일만 업로드해주세요.")

    start_clicked = st.button(
        "분석 시작",
        type="primary",
        use_container_width=True,
        disabled=is_locked,
    )

    if is_locked:
        stop_clicked = st.button(
            "분석 중단",
            type="secondary",
            use_container_width=True,
        )

        if stop_clicked:
            request_stop()
            st.warning("⏹ 분석 중단 요청을 보냈습니다.")

    if st.session_state.applied_params:
        st.divider()
        st.success("📌 현재 적용된 파라미터")
        for key, value in st.session_state.applied_params.items():
            st.write(f"**{key}:** {value}")


# ==========================================
# 메인 화면
# ==========================================
st.title("지능형 배구 경기 분석 대시보드: SPaiKE V")
st.markdown("동영상을 업로드하고 사이드바에서 설정을 마친 뒤 **분석 시작** 버튼을 누르세요.")

main_left, main_right = st.columns([1, 1])

with main_left:
    st.subheader("1. 경기 분석 시각화")
    status_msg = st.empty()
    progress_bar = st.progress(0)
    st_frame = st.empty()

with main_right:
    st.subheader("2. 선수별 공 터치 카운트")
    result_area = st.empty()


# ==========================================
# 분석 실행
# ==========================================
if start_clicked:
    if uploaded_file is None:
        st.warning("⚠️ 분석할 영상을 먼저 업로드해주세요.")

    elif not is_valid_file:
        st.error("❌ 파일 형식이 잘못되었습니다. mp4 또는 avi 파일만 업로드해주세요.")

    else:
        clear_stop_request()

        input_video_path = save_uploaded_video(uploaded_file)

        st.session_state.pending_video_path = str(input_video_path)

        st.session_state.run_params = {
            "model_choice": model_choice,
            "ball_track_method": ball_track_method,
            "p_conf": p_conf,
            "p_buf": p_buf,
            "p_match": p_match,
            "b_conf": b_conf,
            "b_buf": b_buf,
            "b_match": b_match,
        }

        st.session_state.applied_params = {
            "모델": model_choice,
            "공 위치 추정 방식": ball_track_method,
            "선수 Conf": p_conf,
            "선수 Buffer": p_buf,
            "선수 Match": p_match,
            "공 Conf": b_conf,
            "공 Buffer": b_buf if ball_track_method == config.BALL_METHOD_BYTETRACK else "해당 없음",
            "공 Match": b_match if ball_track_method == config.BALL_METHOD_BYTETRACK else "해당 없음",
        }

        st.session_state.is_running = True
        st.session_state.is_completed = False
        st.session_state.result = None

        st.rerun()

if st.session_state.is_running and st.session_state.pending_video_path is not None:
    params = st.session_state.run_params

    try:
        result = process_video(
            video_path=st.session_state.pending_video_path,
            model_choice=params["model_choice"],
            ball_track_method=params["ball_track_method"],
            p_conf=params["p_conf"],
            p_buf=params["p_buf"],
            p_match=params["p_match"],
            b_conf=params["b_conf"],
            b_buf=params["b_buf"],
            b_match=params["b_match"],
            st_frame=st_frame,
            progress_bar=progress_bar,
            status_msg=status_msg,
        )

        st.session_state.result = result
        st.session_state.is_completed = True
        status_msg.success("✨ 분석이 완료되었습니다!")

    except Exception as e:
        st.session_state.is_completed = False
        st.session_state.result = None

        if "분석이 중단" in str(e):
            status_msg.warning("⏹ 분석이 중단되었습니다.")
        else:
            status_msg.error(f"❌ 분석 중 오류가 발생했습니다: {e}")

    finally:
        clear_stop_request()
        st.session_state.is_running = False
        st.session_state.pending_video_path = None
        st.session_state.run_params = None
        st.rerun()

        
# ==========================================
# 결과 출력
# ==========================================
if st.session_state.result is not None:
    result = st.session_state.result

    output_video_path = result["output_video_path"]
    touch_counts = result["touch_counts"]
    touch_events = result["touch_events"]

    with main_left:
        time.sleep(0.3)

        try:
            with open(output_video_path, "rb") as f:
                video_bytes = f.read()

            st.video(video_bytes, format="video/mp4")

        except FileNotFoundError:
            st.error("결과 영상 파일을 찾을 수 없습니다.")

    with main_right:
        if touch_counts:
            df_touches = pd.DataFrame(
                sorted(touch_counts.items(), key=lambda x: int(x[0]) if str(x[0]).isdigit() else str(x[0])),
                columns=["선수 ID", "터치 횟수"],
            ).set_index("선수 ID")

            st.bar_chart(df_touches)

            max_id = df_touches["터치 횟수"].idxmax()
            max_val = df_touches["터치 횟수"].max()

            st.info(f"🏆 가장 많이 공을 터치한 선수: ID {max_id} / {max_val}회")

            with st.expander("터치 이벤트 상세 보기"):
                if touch_events:
                    df_events = pd.DataFrame(touch_events)
                    st.dataframe(df_events, use_container_width=True)
                else:
                    st.write("터치 이벤트가 없습니다.")

        else:
            st.warning("분석된 터치 데이터가 없습니다.")