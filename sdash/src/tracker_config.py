import uuid
from pathlib import Path

import yaml

import config


def create_tracker_yaml(
    tracker_type: str,
    buffer: int,
    match: float,
    filename: str | None = None,
) -> Path:
    config.TRACKER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    if filename is None:
        filename = f"{tracker_type}_{uuid.uuid4().hex[:8]}.yaml"

    path = config.TRACKER_CONFIG_DIR / filename

    cfg = {
        "tracker_type": tracker_type,
        "track_buffer": int(buffer),
        "match_thresh": float(match),
        "fuse_score": True,
    }

    if tracker_type == "botsort":
        cfg.update(
            {
                "track_high_thresh": 0.75,
                "track_low_thresh": 0.10,
                "new_track_thresh": 0.75,
                "gmc_method": "sparseOptFlow",
                "proximity_thresh": 0.50,
                "appearance_thresh": 0.25,
                "with_reid": True,
                "model": "auto",
            }
        )

    elif tracker_type == "bytetrack":
        cfg.update(
            {
                "track_high_thresh": 0.25,
                "track_low_thresh": 0.05,
                "new_track_thresh": 0.45,
                "gmc_method": "none",
                "proximity_thresh": 0.50,
                "appearance_thresh": 0.25,
                "with_reid": False,
                "model": "auto",
            }
        )

    else:
        raise ValueError(f"지원하지 않는 tracker_type입니다: {tracker_type}")

    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, allow_unicode=True)

    return path


def cleanup_tracker_yamls(*paths):
    for path in paths:
        if path is None:
            continue

        path = Path(path)

        if path.exists():
            path.unlink()