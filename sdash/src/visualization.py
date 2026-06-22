import cv2
import numpy as np
import pandas as pd

import config


def draw_player_info(frame, player):
    x1, y1, x2, y2, track_id, conf = player

    cv2.rectangle(
        frame,
        (int(x1), int(y1)),
        (int(x2), int(y2)),
        (255, 0, 0),
        2,
    )

    label = f"ID:{track_id} {conf:.2f}"

    cv2.putText(
        frame,
        label,
        (int(x1), max(30, int(y1) - 10)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 0, 0),
        2,
    )

    return frame


def draw_ball_info(frame, row, history_pts):
    if row is None:
        return frame

    cx = row.get("cx")
    cy = row.get("cy")
    w = row.get("w")
    h = row.get("h")
    conf = row.get("conf")

    if pd.isna(cx) or pd.isna(cy) or pd.isna(w) or pd.isna(h):
        return frame

    cx = int(cx)
    cy = int(cy)
    w = int(w)
    h = int(h)
    conf = float(conf) if not pd.isna(conf) else 0.0

    x1 = cx - w // 2
    y1 = cy - h // 2
    x2 = cx + w // 2
    y2 = cy + h // 2

    cv2.rectangle(
        frame,
        (x1, y1),
        (x2, y2),
        (0, 255, 255),
        2,
    )

    if conf == 0.0:
        label = f"Ball ID:{config.FIXED_BALL_ID} (Interp)"
    else:
        label = f"Ball ID:{config.FIXED_BALL_ID} {conf:.2f}"

    cv2.putText(
        frame,
        label,
        (x1, max(30, y1 - 10)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 255, 255),
        2,
    )

    if history_pts is not None and len(history_pts) > 1:
        history_pts = np.asarray(history_pts, dtype=np.int32)

        cv2.polylines(
            frame,
            [history_pts],
            isClosed=False,
            color=(0, 0, 255),
            thickness=3,
        )

    return frame