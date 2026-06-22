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
        # value=float(st.session_state.p_conf),
        key="p_conf",
        step=0.05,
        disabled=is_locked,
    )

    p_buf = st.slider(
        "선수 추적 유지 프레임 Track Buffer",
        0,
        150,
        # value=int(st.session_state.p_buf),
        key="p_buf",
        step=5,
        disabled=is_locked,
    )

    p_match = st.slider(
        "선수 매칭 임계값 Match Threshold",
        0.0,
        1.0,
        # value=float(st.session_state.p_match),
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
            # value=float(st.session_state.b_conf),
            key="b_conf",
            step=0.01,
            disabled=is_locked,
        )

        b_buf = st.slider(
            "공 추적 유지 프레임 Track Buffer",
            0,
            100,
            # value=int(st.session_state.b_buf),
            key="b_buf",
            step=5,
            disabled=is_locked,
        )

        b_match = st.slider(
            "공 매칭 임계값 Match Threshold",
            0.0,
            1.0,
            # value=float(st.session_state.b_match),
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
            # value=float(st.session_state.b_detect_conf),
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