from ultralytics.trackers.basetrack import BaseTrack

import config
from src.ball_touch import BallTouchReferee
from src.detection import extract_tracks
from src.model_loader import load_models, reset_model_predictors
from src.renderer import render_analysis_video
from src.tracker_config import cleanup_tracker_yamls, create_tracker_yaml
from src.trajectory import interpolate_trajectory
from src.video_io import build_output_video_path, ensure_directories


def process_video(
    video_path,
    model_choice,
    ball_track_method,
    p_conf,
    p_buf,
    p_match,
    b_conf,
    b_buf,
    b_match,
    st_frame=None,
    progress_bar=None,
    status_msg=None,
):
    ensure_directories()

    def set_progress(value):
        if progress_bar is not None:
            value = max(0.0, min(1.0, float(value)))
            progress_bar.progress(value)

    def set_status(message):
        if status_msg is not None:
            status_msg.info(message)

    set_progress(0.0)

    player_yaml = None
    ball_yaml = None

    try:
        # ==========================================
        # 모델 로드
        # ==========================================
        set_status("⏳ 모델을 불러오는 중입니다...")

        ball_model, player_model = load_models(model_choice)

        reset_model_predictors(ball_model, player_model)

        # 추적 ID 초기화
        BaseTrack._count = 0

        # ==========================================
        # 트래커 설정 파일 생성
        # ==========================================
        player_yaml = create_tracker_yaml(
            tracker_type="botsort",
            buffer=p_buf,
            match=p_match,
            filename="temp_player_botsort.yaml",
        )

        ball_yaml = create_tracker_yaml(
            tracker_type="bytetrack",
            buffer=b_buf,
            match=b_match,
            filename="temp_ball_bytetrack.yaml",
        )

        # ==========================================
        # 1단계: 탐지 및 추적
        # ==========================================
        ball_trajectory, player_tracks_history = extract_tracks(
            video_path=video_path,
            ball_model=ball_model,
            player_model=player_model,
            model_choice=model_choice,
            ball_track_method=ball_track_method,
            player_tracker_yaml=player_yaml,
            ball_tracker_yaml=ball_yaml,
            p_conf=p_conf,
            b_conf=b_conf,
            progress_callback=set_progress,
            status_callback=set_status,
        )

        # ==========================================
        # 공 궤적 보간
        # ==========================================
        ball_df = interpolate_trajectory(ball_trajectory)

        # ==========================================
        # 공 터치 판정
        # ==========================================
        referee = BallTouchReferee(
            ball_df=ball_df,
            player_tracks_history=player_tracks_history,
            frame_window=config.TOUCH_FRAME_WINDOW,
            speed_thresh=config.TOUCH_SPEED_THRESH,
            angle_thresh=config.TOUCH_ANGLE_THRESH,
            cooldown_frames=0,
            max_player_distance=None,
        )

        touch_counts = referee.start()

        # ==========================================
        # 2단계: 영상 렌더링
        # ==========================================
        output_video_path = build_output_video_path(video_path)

        render_analysis_video(
            video_path=video_path,
            output_path=output_video_path,
            ball_df=ball_df,
            player_tracks_history=player_tracks_history,
            st_frame=st_frame,
            progress_callback=set_progress,
            status_callback=set_status,
        )

        set_progress(1.0)

        return {
            "output_video_path": output_video_path,
            "ball_df": ball_df,
            "ball_trajectory": ball_trajectory,
            "player_tracks_history": player_tracks_history,
            "touch_counts": touch_counts,
            "touch_events": referee.touch_events,
            "change_frames": referee.change_frames,
        }

    finally:
        cleanup_tracker_yamls(player_yaml, ball_yaml)