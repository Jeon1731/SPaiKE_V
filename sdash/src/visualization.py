'''# 공 궤적 시각화
import cv2
import numpy as np
import config        # 설정값(FIXED_BALL_ID 등)을 불러오기 위함

def draw_ball_info(frame, row, history_pts):
    
    # 1. 좌표가 존재하는지(결측치가 아닌지) 확인
    if not np.isnan(row['cx']) and not np.isnan(row['cy']):
        # 중심 좌표 및 너비/높이를 정수형으로 변환
        cx, cy = int(row['cx']), int(row['cy'])
        w, h = int(row['w']), int(row['h'])
        conf = row['conf']

        # 중심 좌표를 바탕으로 바운딩 박스의 좌상단(x1, y1), 우하단(x2, y2) 복원
        x1 = cx - w // 2
        y1 = cy - h // 2
        x2 = cx + w // 2
        y2 = cy + h // 2

        # 2. 바운딩 박스 시각화 (노란색: 0, 255, 255)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)

        # 3. 라벨 텍스트 표시
        # conf가 0.0이면 수학적으로 보간된 가상의 좌표이므로 '(Interp)' 라벨을 붙여 차별화
        label = f"Ball ID:{config.FIXED_BALL_ID} (Interp)" if conf == 0.0 else f"Ball ID:{config.FIXED_BALL_ID} {conf:.2f}"
        
        cv2.putText(frame, label, (x1, max(30, y1 - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        # 4. 궤적 선(Tail) 그리기 (빨간색: 0, 0, 255)
        # 꼬리를 그릴 수 있는 과거 좌표가 2개 이상 존재할 때만 실행
        if len(history_pts) > 1:
            cv2.polylines(frame, [history_pts], isClosed=False, color=(0, 0, 255), thickness=3)

    return frame


#tracker.py의 선수 박스 그리는 코드'''


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