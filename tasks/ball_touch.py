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