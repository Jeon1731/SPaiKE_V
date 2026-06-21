import cv2

from src.video_io import get_video_metadata
from src.visualization import draw_ball_info, draw_player_info
from src.video_io import is_stop_requested


def create_video_writer(output_path, fps, width, height):
    codecs = ["avc1", "mp4v"]

    for codec in codecs:
        fourcc = cv2.VideoWriter_fourcc(*codec)

        writer = cv2.VideoWriter(
            str(output_path),
            fourcc,
            fps,
            (width, height),
        )

        if writer.isOpened():
            return writer

        writer.release()

    raise RuntimeError("VideoWriter를 열 수 없습니다. avc1/mp4v 코덱을 확인하세요.")


def render_analysis_video(
    video_path,
    output_path,
    ball_df,
    player_tracks_history,
    st_frame=None,
    progress_callback=None,
    status_callback=None,
):
    if status_callback:
        status_callback("⏳ [2/2 단계] 공 궤적 보간 및 최종 영상을 렌더링하고 있습니다...")

    metadata = get_video_metadata(video_path)

    total_frames = metadata["total_frames"]
    fps = metadata["fps"]
    width = metadata["width"]
    height = metadata["height"]

    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        raise RuntimeError(f"영상을 열 수 없습니다: {video_path}")

    out = create_video_writer(output_path, fps, width, height)

    frame_idx = 0

    while cap.isOpened():
        if is_stop_requested():
            cap.release()
            out.release()
            raise RuntimeError("사용자 요청으로 분석이 중단되었습니다.")

        success, frame = cap.read()

        if not success:
            break

        annotated_frame = frame.copy()

        # ==========================================
        # 선수 박스 그리기
        # ==========================================
        if frame_idx < len(player_tracks_history):
            for player in player_tracks_history[frame_idx]:
                annotated_frame = draw_player_info(annotated_frame, player)

        # ==========================================
        # 공 박스 및 궤적 그리기
        # ==========================================
        if ball_df is not None and frame_idx < len(ball_df):
            row = ball_df.iloc[frame_idx]

            start_history = max(0, frame_idx - 15)

            history_pts = (
                ball_df.iloc[start_history: frame_idx + 1][["cx", "cy"]]
                .dropna()
                .values
            )

            annotated_frame = draw_ball_info(
                annotated_frame,
                row,
                history_pts,
            )

        out.write(annotated_frame)

        # Streamlit 화면에는 3프레임에 1번만 출력해서 속도 확보
        if st_frame is not None and frame_idx % 3 == 0:
            annotated_frame_rgb = cv2.cvtColor(
                annotated_frame,
                cv2.COLOR_BGR2RGB,
            )

            st_frame.image(
                annotated_frame_rgb,
                channels="RGB",
                use_container_width=True,
            )

        frame_idx += 1

        if progress_callback and total_frames > 0:
            progress = min(0.5 + (frame_idx / total_frames) * 0.5, 1.0)
            progress_callback(progress)

    cap.release()
    out.release()

    return output_path