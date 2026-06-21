import cv2
import os

img_w, img_h = 1920, 1080  # 모델 입력 크기
labels_path = "./runs/detect/SPaiKE_V/tracking/labels/*.txt"
video_path = "./test/sample2.mp4"
output_path = "./test/output_video.mp4"
video_name = 'sample2'

# 원본 영상 열기
cap = cv2.VideoCapture(video_path)
fps = int(cap.get(cv2.CAP_PROP_FPS))
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# 결과 영상 저장 준비
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

frame_idx = 0
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # 해당 프레임 번호에 맞는 라벨 파일 찾기
    label_file = f"./runs/detect/SPaiKE_V/tracking/labels/{video_name}_{frame_idx}.txt"
    if os.path.exists(label_file):
        with open(label_file, "r") as f:
            lines = f.readlines()

        for line in lines:
            parts = line.strip().split()
            if len(parts) < 6:
                continue
            cls, x_norm, y_norm, w_norm, h_norm, obj_id = parts
            # print(parts)

            # 좌표 변환
            x_center = float(x_norm) * img_w
            y_center = float(y_norm) * img_h
            box_w = float(w_norm) * img_w
            box_h = float(h_norm) * img_h

            x1 = int(x_center - box_w / 2)
            y1 = int(y_center - box_h / 2)
            x2 = int(x_center + box_w / 2)
            y2 = int(y_center + box_h / 2)

            # class별 색상 및 텍스트 설정
            if int(cls) == 0:
                color = (255, 0, 0)  # 파란색
                label_text = f"id:{obj_id}"
            elif int(cls) == 1:
                color = (0, 255, 255)  # 노란색
                label_text = "ball"
            else:
                color = (0, 255, 0)  # 기본 초록색
                label_text = f"class {cls}"

            # bounding box 그리기
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, label_text, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    # 결과 프레임 저장
    out.write(frame)
    frame_idx += 1

cap.release()
out.release()
cv2.destroyAllWindows()


