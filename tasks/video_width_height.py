import cv2

class VideoWidthHeightGetter:
    def __init__(self, video_path):
        self.video_path = video_path

    def start(self):
        cap = cv2.VideoCapture(self.video_path)

        if not cap.isOpened():
            print("VideoWidthHeightGetterERROR: 동영상을 열 수 없습니다.")
        else:
            # width와 height 가져오기
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        cap.release()
        return width, height
