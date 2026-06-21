import cv2
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import utils.config as config

from tasks.get_max_frame_number import get_max_frame_number

def draw_frame_with_ids(video_path, frame, frame_number):
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    
    # 라벨 파일 읽기
    label_file = os.path.join(config.LABELS_PATH, f"{video_name}_{frame_number}.txt")
    if not os.path.exists(label_file):
        print("라벨 파일 없음:", label_file)
        return
    
    with open(label_file, "r") as f:
        lines = f.readlines()
    
    h, w, _ = frame.shape
    
    for line in lines:
        parts = line.strip().split()
        cls = int(parts[0])
        cx, cy, bw, bh = map(float, parts[1:5])
        pid = parts[5] if len(parts) > 5 else "unknown"
        
        # 좌표 변환 (YOLO 형식 → 픽셀 좌표)
        x = int(cx * w)
        y = int(cy * h)
        box_w = int(bw * w)
        box_h = int(bh * h)
        x1, y1 = x - box_w//2, y - box_h//2
        x2, y2 = x + box_w//2, y + box_h//2
        
        # 색상 지정
        color = (0,255,0) if cls == 0 else (0,0,255)  # player=green, ball=red
        
        # 박스와 ID 표시
        cv2.rectangle(frame, (x1,y1), (x2,y2), color, 2)
        cv2.putText(frame, f"ID:{pid}", (x1,y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)


    # cv2.imshow("Frame with IDs", frame)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    # cap.release()
    return frame