'''import sys
import os
import numpy as np
import matplotlib.pyplot as plt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


import config
from src.get_max_frame_number import get_max_frame_number

class BallTouchReferee:
    def __init__(
        self,
        ball_trajectory,
        player_tracks_history,
        frame_window=5,
        speed_thresh=2.0,
        angle_thresh=0.5
    ):
        self.ball_trajectory = ball_trajectory
        self.player_tracks_history = player_tracks_history
        self.frame_window = frame_window
        self.speed_thresh = speed_thresh
        self.angle_thresh = angle_thresh

        self.ball_positions = {}
        self.speeds = {}
        self.angles = {}
        self.change_frames = []

    def start(self):
        self.read_ball_positions()
        self.compute_speed_angle()
        self.detect_changes()

    def read_ball_positions(self):
        for row in self.ball_trajectory:
            frame, cx, cy, w, h, conf = row

            if cx is None or cy is None:
                continue

            self.ball_positions[int(frame)] = (float(cx), float(cy))

    def compute_speed_angle(self):
        frames = sorted(self.ball_positions.keys())

        for i in range(self.frame_window, len(frames)):
            t = frames[i]
            t_prev = frames[i - self.frame_window]

            x1, y1 = self.ball_positions[t_prev]
            x2, y2 = self.ball_positions[t]

            dx = x2 - x1
            dy = y2 - y1

            speed = (dx ** 2 + dy ** 2) ** 0.5 / self.frame_window
            angle = np.arctan2(dy, dx)

            self.speeds[t] = speed
            self.angles[t] = angle

    def detect_changes(self):
        frames = sorted(self.speeds.keys())

        for i in range(1, len(frames)):
            t = frames[i]
            t_prev = frames[i - 1]

            speed_change = abs(self.speeds[t] - self.speeds[t_prev])
            angle_change = abs(self.angles[t] - self.angles[t_prev])

            if speed_change > self.speed_thresh or angle_change > self.angle_thresh:
                self.change_frames.append(t)

    def find_closest_player(self, frame, ball_pos):
        if frame >= len(self.player_tracks_history):
            return None, float("inf")

        players = self.player_tracks_history[frame]

        min_dist = float("inf")
        closest_id = None

        for x1, y1, x2, y2, track_id, conf in players:
            px = (x1 + x2) / 2
            py = (y1 + y2) / 2

            dist = ((px - ball_pos[0]) ** 2 + (py - ball_pos[1]) ** 2) ** 0.5

            if dist < min_dist:
                min_dist = dist
                closest_id = track_id

        return closest_id, min_dist'''


import math

import numpy as np
import pandas as pd


class BallTouchReferee:
    def __init__(
        self,
        ball_df: pd.DataFrame,
        player_tracks_history,
        frame_window: int = 5,
        speed_thresh: float = 2.0,
        angle_thresh: float = 0.5,
        cooldown_frames: int = 5,
        max_player_distance: float | None = 120,
    ):
        self.ball_df = ball_df
        self.player_tracks_history = player_tracks_history

        self.frame_window = int(frame_window)
        self.speed_thresh = float(speed_thresh)
        self.angle_thresh = float(angle_thresh)
        self.cooldown_frames = int(cooldown_frames)
        self.max_player_distance = max_player_distance

        self.ball_positions = {}
        self.speeds = {}
        self.angles = {}
        self.change_frames = []

        self.touch_events = []
        self.touch_counts = {}

    def start(self):
        self.read_ball_positions()
        self.compute_speed_angle()
        self.detect_changes()
        self.count_touches()

        return self.touch_counts

    def read_ball_positions(self):
        self.ball_positions = {}

        if self.ball_df is None or self.ball_df.empty:
            return

        for _, row in self.ball_df.iterrows():
            frame = row.get("frame")
            cx = row.get("cx")
            cy = row.get("cy")

            if pd.isna(frame) or pd.isna(cx) or pd.isna(cy):
                continue

            self.ball_positions[int(frame)] = (float(cx), float(cy))

    def compute_speed_angle(self):
        self.speeds = {}
        self.angles = {}

        frames = sorted(self.ball_positions.keys())

        if len(frames) <= self.frame_window:
            return

        for i in range(self.frame_window, len(frames)):
            t = frames[i]
            t_prev = frames[i - self.frame_window]

            x1, y1 = self.ball_positions[t_prev]
            x2, y2 = self.ball_positions[t]

            dx = x2 - x1
            dy = y2 - y1

            speed = math.sqrt(dx**2 + dy**2) / self.frame_window
            angle = math.atan2(dy, dx)

            self.speeds[t] = speed
            self.angles[t] = angle

    def detect_changes(self):
        self.change_frames = []

        frames = sorted(self.speeds.keys())

        if len(frames) <= 1:
            return

        for i in range(1, len(frames)):
            t = frames[i]
            t_prev = frames[i - 1]

            speed_change = abs(self.speeds[t] - self.speeds[t_prev])
            angle_change = self.angle_diff(self.angles[t], self.angles[t_prev])

            if (
                speed_change > self.speed_thresh
                or angle_change > self.angle_thresh
            ):
                self.change_frames.append(t)

    @staticmethod
    def angle_diff(a, b):
        diff = abs(a - b)

        # 각도가 pi 경계를 넘어갈 때 차이가 과도하게 커지는 문제 보정
        if diff > math.pi:
            diff = 2 * math.pi - diff

        return diff

    def count_touches(self):
        self.touch_events = []
        self.touch_counts = {}

        last_touch_frame_by_player = {}

        for frame in self.change_frames:
            if frame not in self.ball_positions:
                continue

            ball_pos = self.ball_positions[frame]

            closest_id, dist = self.find_closest_player(frame, ball_pos)

            if closest_id is None:
                continue

            if (
                self.max_player_distance is not None
                and dist > self.max_player_distance
            ):
                continue

            last_frame = last_touch_frame_by_player.get(closest_id)

            if (
                last_frame is not None
                and frame - last_frame <= self.cooldown_frames
            ):
                continue

            last_touch_frame_by_player[closest_id] = frame

            self.touch_counts[closest_id] = self.touch_counts.get(closest_id, 0) + 1

            self.touch_events.append(
                {
                    "frame": frame,
                    "player_id": closest_id,
                    "distance": round(float(dist), 2),
                    "speed": round(float(self.speeds.get(frame, 0.0)), 3),
                    "angle": round(float(self.angles.get(frame, 0.0)), 3),
                }
            )

    def find_closest_player(self, frame: int, ball_pos):
        if frame < 0 or frame >= len(self.player_tracks_history):
            return None, float("inf")

        players = self.player_tracks_history[frame]

        if not players:
            return None, float("inf")

        min_dist = float("inf")
        closest_id = None

        bx, by = ball_pos

        for player in players:
            x1, y1, x2, y2, track_id, conf = player

            px = (x1 + x2) / 2
            py = (y1 + y2) / 2

            dist = np.sqrt((px - bx) ** 2 + (py - by) ** 2)

            if dist < min_dist:
                min_dist = dist
                closest_id = str(track_id)

        return closest_id, min_dist