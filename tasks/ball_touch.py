import sys
import os
import numpy as np
import matplotlib.pyplot as plt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import utils.config as config
from tasks.get_max_frame_number import get_max_frame_number

class BallTouchReferee:
    def __init__(self, video_path, frame_window, speed_thresh, angle_thresh):
        self.video_path = video_path
        self.video_name = os.path.splitext(os.path.basename(self.video_path))[0]
        self.max_frame = get_max_frame_number(self.video_name, config.LABELS_PATH)

        # read_ball_position
        self.ball_positions = {}

        # compute_speed_angle
        self.frame_window = frame_window # 사용자 지정 parameter
        self.speeds, self.angles = {}, {}

        # detect_changes
        self.speed_thresh = speed_thresh # 사용자 지정 parameter
        self.angle_thresh = angle_thresh # 사용자 지정 parameter
        self.change_frames = []

    def start(self):
        print("BallTouchReferee: start")

        self.read_ball_positions()
        self.compute_speed_angle()
        self.detect_changes()

        print("급격 변화 프레임:", self.change_frames)

        for f in self.change_frames:
            closest_id, dist = self.find_closest_player(f, self.ball_positions[f])
            print(f"Frame {f}: Closest Player ID={closest_id}, Distance={dist:.4f}")
        
        print("BallTouchReferee: finished")


    def read_ball_positions(self):
        # ball_positions = {}
        for frame in range(1, self.max_frame+1):
            file_path = os.path.join(config.LABELS_PATH, f"{self.video_name}_{frame}.txt")
            if not os.path.exists(file_path):
                continue
            with open(file_path, "r") as f:
                lines = f.readlines()
            for line in lines:
                parts = line.strip().split()
                cls = int(parts[0])
                if cls == 1:  # ball
                    cx, cy = float(parts[1]), float(parts[2])
                    self.ball_positions[frame] = (cx, cy)
        # return ball_positions

    def compute_speed_angle(self):
        # speeds, angles = {}, {}
        frames = sorted(self.ball_positions.keys())
        for i in range(self.frame_window, len(frames)):
            t = frames[i]
            t_prev = frames[i-self.frame_window]
            x1, y1 = self.ball_positions[t_prev]
            x2, y2 = self.ball_positions[t]
            dx, dy = x2 - x1, y2 - y1
            speed = np.sqrt(dx**2 + dy**2) / self.frame_window
            angle = np.arctan2(dy, dx)
            self.speeds[t] = speed
            self.angles[t] = angle
        # return speeds, angles

    def detect_changes(self):
        # change_frames = []
        frames = sorted(self.speeds.keys())
        for i in range(1, len(frames)):
            t = frames[i]
            t_prev = frames[i-1]
            if abs(self.speeds[t] - self.speeds[t_prev]) > self.speed_thresh or \
            abs(self.angles[t] - self.angles[t_prev]) > self.angle_thresh:
                self.change_frames.append(t)
        # return change_frames

    def find_closest_player(self, frame, ball_pos):
        file_path = os.path.join(config.LABELS_PATH, f"{self.video_name}_{frame}.txt")
        if not os.path.exists(file_path):
            return None
        with open(file_path, "r") as f:
            lines = f.readlines()
        min_dist, closest_id = float("inf"), None
        for line in lines:
            parts = line.strip().split()
            cls = int(parts[0])
            if cls == 0:  # player
                cx, cy = float(parts[1]), float(parts[2])
                pid = parts[5] if len(parts) > 5 else "unknown"
                dist = np.sqrt((cx - ball_pos[0])**2 + (cy - ball_pos[1])**2)
                if dist < min_dist:
                    min_dist, closest_id = dist, pid
        return closest_id, min_dist
    
# --------------- 공 궤적 그래프 시각화 ---------------
# def visualize_trajectory(ball_positions, change_frames, video_name, flip=True):
#     frames = sorted(ball_positions.keys())
#     xs = [ball_positions[f][0] for f in frames]
#     ys = [ball_positions[f][1] for f in frames]

#     plt.figure(figsize=(10,6))
#     plt.plot(xs, ys, "-o", label="Ball Trajectory", alpha=0.6)

#     # 변화 순간 강조
#     for f in change_frames:
#         if f in ball_positions:
#             x, y = ball_positions[f]
#             plt.scatter(x, y, c="red", s=80, label="Change Point" if f==change_frames[0] else "")
#             closest_id, dist = find_closest_player(f, ball_positions[f])
#             if closest_id:
#                 plt.text(x, y, f"ID:{closest_id}", fontsize=9, color="blue")

#     plt.title("Ball Trajectory with Change Points (Flipped)")
#     plt.xlabel("Center X")
#     plt.ylabel("Center Y")
#     plt.legend()

#     # 상하 반전
#     if flip:
#         ax = plt.gca()
#         ax.invert_yaxis()

#     plt.show()


# ---------------- 실행 예시 ----------------
# video_name = "sample2"
# max_frame = 490
# frame_window = 15
# speed_thresh = 0.05
# angle_thresh = 0.75

# ball_positions = read_ball_positions(video_name, max_frame)
# speeds, angles = compute_speed_angle(ball_positions, frame_window)
# change_frames = detect_changes(speeds, angles, speed_thresh, angle_thresh)

# print("급격 변화 프레임:", change_frames)

# for f in change_frames:
#     closest_id, dist = find_closest_player(f, ball_positions[f])
#     print(f"Frame {f}: Closest Player ID={closest_id}, Distance={dist:.4f}")

# visualize_trajectory(ball_positions, change_frames, video_name)

# --------------- 영상 시각화 ---------------
# import cv2
# import os

# LABEL_DIR = "./runs/detect/SPaiKE_V/tracking/labels/"
# VIDEO_PATH = "./test/sample2.mp4"

# def draw_frame_with_ids(video_name, frame_number):
#     # 비디오 열기
#     cap = cv2.VideoCapture(VIDEO_PATH)
#     cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number-1)  # 특정 프레임으로 이동
#     ret, frame = cap.read()
#     if not ret:
#         print("프레임을 읽을 수 없습니다.")
#         return
    
#     # 라벨 파일 읽기
#     label_file = os.path.join(LABEL_DIR, f"{video_name}_{frame_number}.txt")
#     if not os.path.exists(label_file):
#         print("라벨 파일 없음:", label_file)
#         return
    
#     with open(label_file, "r") as f:
#         lines = f.readlines()
    
#     h, w, _ = frame.shape
    
#     for line in lines:
#         parts = line.strip().split()
#         cls = int(parts[0])
#         cx, cy, bw, bh = map(float, parts[1:5])
#         pid = parts[5] if len(parts) > 5 else "unknown"
        
#         # 좌표 변환 (YOLO 형식 → 픽셀 좌표)
#         x = int(cx * w)
#         y = int(cy * h)
#         box_w = int(bw * w)
#         box_h = int(bh * h)
#         x1, y1 = x - box_w//2, y - box_h//2
#         x2, y2 = x + box_w//2, y + box_h//2
        
#         # 색상 지정
#         color = (0,255,0) if cls == 0 else (0,0,255)  # player=green, ball=red
        
#         # 박스와 ID 표시
#         cv2.rectangle(frame, (x1,y1), (x2,y2), color, 2)
#         cv2.putText(frame, f"ID:{pid}", (x1,y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    
#     cv2.imshow("Frame with IDs", frame)
#     cv2.waitKey(0)
#     cv2.destroyAllWindows()
#     cap.release()

# # # 실행 예시
# draw_frame_with_ids("sample2", 439)
