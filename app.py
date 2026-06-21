import streamlit as st
from ultralytics import YOLO
import cv2
import os
import pandas as pd
import shutil
import yaml

import utils.config as config
from utils.utils import upload_video

from tasks.botsort_yaml_make import BotsortYamlMaker
from tasks.player_tracking import PlayerTracker
from tasks.ball_detection  import BallDetector
from tasks.ball_touch import BallTouchReferee
from tasks.draw_frame_with_ids import draw_frame_with_ids

# 모델 로딩 함수 (캐싱 적용)
@st.cache_resource
def load_model(model_path):
    return YOLO(model_path)

# [1] Title & Setup
st.set_page_config(page_title="YOLOv8s + Object tracking", layout="wide")
st.title("🏐 지능형 배구 경기 분석 대시보드: SPaiKE V")
st.write("동영상을 업로드하고 '분석 시작' 버튼을 눌러 AI의 분석 결과를 확인하세요.")

st.divider()

# [2] Sidebar: 모델 설정 및 파라미터 조절
st.sidebar.header("SPaiKE V 모델 설정")

# Confidence Threshold 슬라이더
conf_thres = st.sidebar.slider("conf_thresh 설정",
                                 min_value=0.0, max_value=1.0, value=0.3, step=0.05)

# IoU Threshold 슬라이더
iou_thres = st.sidebar.slider("iou_thresh 설정",
                                 min_value=0.0, max_value=1.0, value=0.5, step=0.05)

# frame_window 슬라이더
frame_window = st.sidebar.slider("frame_window 설정",
                                 min_value=1, max_value=30, value=15, step=1)

# speed_thresh 슬라이더
speed_thresh = st.sidebar.slider("speed_thresh 설정",
                                 min_value=0.0, max_value=1.0, value=0.05, step=0.005)

# angle_thresh 슬라이더
angle_thresh = st.sidebar.slider("angle_thresh 설정",
                                 min_value=0.0, max_value=1.0, value=0.75, step=0.05)

# 파일 업로더 (동영상)
uploaded_video = st.sidebar.file_uploader("분석할 배구 경기 동영상 업로드", type=['mp4'])

video_path = upload_video(uploaded_video)
print(video_path)

# with col:
st.subheader("경기 영상 분석 - 선수 ID 별 터치 횟수 시각화")

if uploaded_video is not None: # 이미지가 업로도되었을 때만 버튼 활성화

    # 원본 비디오 읽기
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # 실시간 프레임을 주입할 Streamlit 빈 공간 생성
    st_frame = st.empty()

    # 실시간 터치 수를 표시할 Streamlit 빈 공간 생성
    st_table = st.empty()

    # 최종 터치 수를 표시할 Streamlit 빈 공간 생성
    st_graph = st.empty()

    # 빈 DataFrame 준비
    data = pd.DataFrame(columns=["touch"])

    if st.button("분석 시작 (Start SPaiKE V Referee)", type="primary"):
        status_text = st.empty()
        frame_count = 0
        with st.spinner(f"SPaiKE V Referee가 경기를 분석 중입니다..."):
            try:
                # botsort.yaml 파일이 존재하지 않으면 생성
                if not os.path.exists(config.BOTSORT_TRACKER_PATH):
                    BotsortYamlMaker.start()
                
                # player tracking
                PlayerTracker(video_path).start()
                
                # ball tracking
                BallDetector(video_path).start()

                # ball touch logic
                ballTouchReferee = BallTouchReferee(video_path, frame_window, speed_thresh, angle_thresh)
                ballTouchReferee.start()

                # OpenCV(BGR) 이미지 형식을 Streamlit(RGB) 형식으로 변환하여 실시간 출력
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret : break

                    frame_count += 1

                    annotated_frame = draw_frame_with_ids(video_path, frame, frame_count)

                    annotated_frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
                    st_frame.image(annotated_frame_rgb, channels="RGB", width="stretch")

                    if frame_count in ballTouchReferee.change_frames:
                        closest_id, min_dist = ballTouchReferee.find_closest_player(frame_count, ballTouchReferee.ball_positions[frame_count])
                        if closest_id in data.index:
                            data.loc[closest_id, "touch"] += 1
                        else:
                            data.loc[closest_id, "touch"] = 1

                        st_table.table(data)

                cap.release()
                st_graph.bar_chart(data)

            except Exception as e:
                st.error(f"분석 중 오류가 발생했습니다: {e}")
else:
    # 동영상이 업로도되지 않았을 때의 가이드
    st.info("사이드바에서 동영상을 업로드한 후 '검출 시작' 버튼을 누르세요.")
    