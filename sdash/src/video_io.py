import re
import uuid
from pathlib import Path

import cv2

import config


def ensure_directories():
    config.TEMP_DIR.mkdir(parents=True, exist_ok=True)
    config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    config.TRACKER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def sanitize_filename(filename: str) -> str:
    path = Path(filename)

    stem = path.stem
    suffix = path.suffix.lower()

    stem = re.sub(r"[^a-zA-Z0-9가-힣_-]+", "_", stem)
    stem = stem.strip("_")

    if not stem:
        stem = "uploaded_video"

    if suffix not in [".mp4", ".avi"]:
        suffix = ".mp4"

    return f"{stem}{suffix}"


def save_uploaded_video(uploaded_file) -> Path:
    ensure_directories()

    safe_name = sanitize_filename(uploaded_file.name)
    unique_id = uuid.uuid4().hex[:8]

    path = Path(safe_name)
    output_path = config.UPLOAD_DIR / f"{path.stem}_{unique_id}{path.suffix}"

    with open(output_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return output_path


def get_video_metadata(video_path):
    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        raise RuntimeError(f"영상을 열 수 없습니다: {video_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    cap.release()

    return {
        "total_frames": total_frames,
        "fps": fps,
        "width": width,
        "height": height,
    }


def build_output_video_path(video_path) -> Path:
    ensure_directories()

    video_path = Path(video_path)
    output_name = f"{video_path.stem}_analyzed.mp4"

    return config.OUTPUT_DIR / output_name


def request_stop():
    """분석 중단 요청 플래그 생성"""
    config.TEMP_DIR.mkdir(parents=True, exist_ok=True)

    with open(config.STOP_FLAG_PATH, "w", encoding="utf-8") as f:
        f.write("stop")


def clear_stop_request():
    """분석 중단 요청 플래그 삭제"""
    if config.STOP_FLAG_PATH.exists():
        config.STOP_FLAG_PATH.unlink()


def is_stop_requested():
    """분석 중단 요청 여부 확인"""
    return config.STOP_FLAG_PATH.exists()