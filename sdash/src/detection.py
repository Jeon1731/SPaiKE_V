import cv2
import numpy as np
import torch

import config
from src.video_io import is_stop_requested


def get_ball_class_id(model_choice: str) -> int:
    if "Fine-Tuned" in model_choice:
        return config.FINETUNED_BALL_CLASS_ID

    return config.BASE_YOLO_BALL_CLASS_ID


def extract_tracks(
    video_path,
    ball_model,
    player_model,
    model_choice: str,
    ball_track_method: str,
    player_tracker_yaml,
    ball_tracker_yaml,
    p_conf: float,
    b_conf: float,
    progress_callback=None,
    status_callback=None,
):
    if status_callback:
        status_callback("⏳ [1/2 단계] 선수 및 공 위치 데이터를 추출하고 있습니다...")

    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        raise RuntimeError(f"영상을 열 수 없습니다: {video_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0

    ball_class_id = get_ball_class_id(model_choice)

    ball_trajectory = []
    player_tracks_history = []

    last_cx = None
    last_cy = None
    missing_count = 0
    frame_idx = 0

    while cap.isOpened():
        if is_stop_requested():
            cap.release()
            raise RuntimeError("사용자 요청으로 분석이 중단되었습니다.")

        success, frame = cap.read()

        if not success:
            break

        # ==========================================
        # 1. 선수 추적
        # ==========================================
        player_results = player_model.track(
            frame,
            tracker=str(player_tracker_yaml),
            conf=float(p_conf),
            persist=True,
            verbose=False,
            classes=[config.PLAYER_CLASS_ID],
            max_det=100,
        )

        frame_players = []

        if (
            player_results
            and player_results[0].boxes is not None
            and player_results[0].boxes.id is not None
        ):
            boxes = player_results[0].boxes

            for i in range(len(boxes.id)):
                x1, y1, x2, y2 = map(
                    int,
                    boxes.xyxy[i].detach().cpu().numpy(),
                )

                track_id = int(boxes.id[i].item())
                conf = float(boxes.conf[i].item())

                frame_players.append(
                    (x1, y1, x2, y2, track_id, conf)
                )

        player_tracks_history.append(frame_players)

        # ==========================================
        # 2. 공 탐지 또는 추적
        # ==========================================
        if ball_track_method == config.BALL_METHOD_BYTETRACK:
            ball_results = ball_model.track(
                frame,
                tracker=str(ball_tracker_yaml),
                conf=float(b_conf),
                persist=True,
                verbose=False,
            )[0]

        else:
            ball_results = ball_model.predict(
                frame,
                conf=float(b_conf),
                iou=0.5,
                verbose=False,
            )[0]

        ball_found = False

        if ball_results.boxes is not None and len(ball_results.boxes) > 0:
            boxes = ball_results.boxes

            ball_indices = (boxes.cls == ball_class_id).nonzero(as_tuple=True)[0]

            if len(ball_indices) > 0:
                best_idx = None

                # 이전 공 위치가 있으면, 너무 멀리 튄 후보는 제외
                if last_cx is not None and missing_count < 5:
                    valid_candidates = []

                    for idx_tensor in ball_indices:
                        idx = int(idx_tensor.item())

                        x1, y1, x2, y2 = map(
                            int,
                            boxes.xyxy[idx].detach().cpu().numpy(),
                        )

                        cx = (x1 + x2) // 2
                        cy = (y1 + y2) // 2

                        dist = np.sqrt((cx - last_cx) ** 2 + (cy - last_cy) ** 2)

                        allowed_distance = config.MAX_ALLOWED_BALL_DISTANCE * (
                            missing_count + 1
                        )

                        if dist < allowed_distance:
                            candidate_conf = float(boxes.conf[idx].item())
                            valid_candidates.append((idx, candidate_conf))

                    if valid_candidates:
                        valid_candidates.sort(key=lambda x: x[1], reverse=True)
                        best_idx = valid_candidates[0][0]

                # 이전 위치 정보가 없으면 confidence가 가장 높은 공 후보 선택
                else:
                    conf_values = boxes.conf[ball_indices]
                    max_conf_pos = torch.argmax(conf_values)
                    best_idx = int(ball_indices[max_conf_pos].item())

                if best_idx is not None:
                    box = boxes[best_idx]

                    x1, y1, x2, y2 = map(
                        int,
                        box.xyxy[0].detach().cpu().numpy(),
                    )

                    cx = (x1 + x2) // 2
                    cy = (y1 + y2) // 2
                    w = x2 - x1
                    h = y2 - y1
                    conf = float(box.conf[0].item())

                    ball_trajectory.append(
                        [frame_idx, cx, cy, w, h, conf]
                    )

                    last_cx = cx
                    last_cy = cy
                    missing_count = 0
                    ball_found = True

        if not ball_found:
            ball_trajectory.append(
                [frame_idx, None, None, None, None, None]
            )

            missing_count += 1

        frame_idx += 1

        if progress_callback and total_frames > 0:
            progress = min((frame_idx / total_frames) * 0.5, 0.5)
            progress_callback(progress)

    cap.release()

    return ball_trajectory, player_tracks_history