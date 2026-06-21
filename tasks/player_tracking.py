import sys
import os
from ultralytics import YOLO

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import utils.config as config

# video_path # ui parameter
# custom_conf # slider
# custom_iou # slider

class PlayerTracker:
    def __init__(self, video_path): ## Streamlit에서 video_path 입력받기
        self.video_path = video_path

    def start(self): 
        print("PlayerTracker: start")

        model = YOLO(config.PLAYER_MODEL_PATH)

        results = model.track(
            source = self.video_path,
            tracker = config.BOTSORT_TRACKER_PATH,
            conf=0.3,
            iou=0.5,
            imgsz=640,
            persist=True,           # 이전 프레임에서 추적하던 객체의 고유 ID를 다음 프레임에서도 연속적으로 유지
            save_txt=True,          # 감지된 객체의 클래스, 추적 ID, 바운딩 박스 좌표 정보를 텍스트(.txt) 파일로 저장
            verbose=False,          # 추론 및 추적 과정에서의 상세한 로그(Log) 및 진행 상황 메시지 출력 여부 결정
            project='SPaiKE_V',
            name='tracking'
        )

        print("PlayerTracker: finished")
        # return results