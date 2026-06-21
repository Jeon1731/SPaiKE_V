from ultralytics import YOLO
import os
import torch
import numpy as np
import pandas as pd
import cv2
import utils.config as config
from video_width_height import VideoWidthHeightGetter

class BallDetector:
    def __init__(self, video_path): ## Streamlit에서 video_path 입력받기
        self.video_path = video_path
        self.video_name = os.path.splitext(os.path.basename(self.video_path))[0]
        self.model = YOLO(config.BALL_MODEL_PATH)
        
        # distance_gating 
        self.raw_trajectory = []

        # curve_fitting
        self.df = None # DaraFrame

    def start(self):
        self.distance_gating()
        self.curve_fitting()
        self.add_labels()
    
    def distance_gating(self): # 거리 가드 보강 
        # video_path = './test/sample2.mp4'
        # video_name = os.path.splitext(os.path.basename(video_path))[0]

        cap = cv2.VideoCapture(self.video_path)

        frame_idx = 0
        last_cx, last_cy = None, None
        missing_count = 0

        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break
            
            # frame별 detection
            results = self.model(
                frame,
                conf=0.15, 
                iou=0.5,
                verbose=False
                )
            result = results[0]

            ball_found = False
            if result.boxes is not None and len(result.boxes) > 0:
                boxes = result.boxes
                ball_indices = (boxes.cls == 0).nonzero(as_tuple=True)[0]

                if len(ball_indices) > 0:
                    best_idx = None

                    if last_cx is not None and missing_count < 5:
                        valid_candidates = []
                        for idx in ball_indices:
                            x1, y1, x2, y2 = map(int, boxes[idx].xyxy[0].cpu().numpy())
                            bcx = (x1 + x2) // 2
                            bcy = (y1 + y2) // 2
                            conf = float(boxes[idx].conf[0].item())

                            dist = np.sqrt((bcx - last_cx)**2 + (bcy - last_cy)**2)
                            dynamic_max_dist = config.MAX_ALLOWED_DISTANCE * (missing_count + 1)

                            if dist < dynamic_max_dist:
                                valid_candidates.append((idx, conf))

                        if valid_candidates:
                            valid_candidates.sort(key=lambda x: x[1], reverse=True)
                            best_idx = valid_candidates[0][0]
                    else:
                        best_idx = ball_indices[torch.argmax(boxes.conf[ball_indices])]

                    if best_idx is not None:
                        box = boxes[best_idx]
                        x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                        conf = float(box.conf[0].item())

                        cx = (x1 + x2) // 2
                        cy = (y1 + y2) // 2
                        w = x2 - x1
                        h = y2 - y1

                        self.raw_trajectory.append([frame_idx, cx, cy, w, h, conf])

                        last_cx, last_cy = cx, cy
                        missing_count = 0
                        ball_found = True

            if not ball_found:
                self.raw_trajectory.append([frame_idx, None, None, None, None, None])
                missing_count += 1

            frame_idx += 1

        cap.release()

    def curve_fitting(self): # 선형 보간 과정
        self.df = pd.DataFrame(self.raw_trajectory, columns=['frame', 'cx', 'cy', 'w', 'h', 'conf'])

        self.df['cx'] = self.df['cx'].interpolate(method='linear')
        self.df['cy'] = self.df['cy'].interpolate(method='linear')
        self.df['w'] = self.df['w'].interpolate(method='linear').bfill().ffill()
        self.df['h'] = self.df['h'].interpolate(method='linear').bfill().ffill()
        self.df['conf'] = self.df['conf'].fillna(0.0)

    def add_labels(self): # tracking labels와 같은 형식으로 변환
        # img_w, img_h = 1920, 1080  # 모델 입력 크기
        img_w, img_h = VideoWidthHeightGetter(self.video_path).start()

        for _, row in self.df.iterrows():
            frame = int(row['frame']) + 1
            cx, cy, w, h, conf = row['cx'], row['cy'], row['w'], row['h'], row['conf']

            # 정규화 (0~1 범위)
            x_norm = cx / img_w
            y_norm = cy / img_h
            w_norm = w / img_w
            h_norm = h / img_h

            # YOLO 학습용 라벨 형식: class x_center y_center width height
            line = f"1 {x_norm:.6f} {y_norm:.6f} {w_norm:.6f} {h_norm:.6f} 0\n"

            dir_path = os.path.dirname('./runs/detect/SPaiKE_V/tracking/labels/')
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)

            txt_filename = f"./runs/detect/SPaiKE_V/tracking/labels/{self.video_name}_{frame}.txt"
            with open(txt_filename, "a") as f:
                f.write(line)