from pathlib import Path

# ==========================================
# 기본 경로
# ==========================================
ROOT_DIR = Path(__file__).resolve().parent

MODEL_DIR = ROOT_DIR / "models"
CONFIG_DIR = ROOT_DIR / "configs"
TEMP_DIR = ROOT_DIR / "temp"

UPLOAD_DIR = TEMP_DIR / "uploads"
OUTPUT_DIR = TEMP_DIR / "outputs"
TRACKER_CONFIG_DIR = TEMP_DIR / "tracker_configs"

STOP_FLAG_PATH = TEMP_DIR / "stop_requested.flag"

# ==========================================
# 모델 경로
# ==========================================
FINETUNED_BALL_MODEL = MODEL_DIR / "ball_best.onnx"
FINETUNED_PLAYER_MODEL = MODEL_DIR / "player_best.onnx"
BASE_YOLO_MODEL = MODEL_DIR / "yolov8s.onnx"

# ==========================================
# 클래스 ID
# ==========================================
# 직접 학습한 공 모델 기준
FINETUNED_BALL_CLASS_ID = 0

# 기본 YOLOv8 COCO 기준 sports ball class id
BASE_YOLO_BALL_CLASS_ID = 32

# 기본 YOLOv8 COCO 기준 person class id
PLAYER_CLASS_ID = 0

FIXED_BALL_ID = 13

# 공 후보 선택 시 이전 위치와의 최대 허용 거리
MAX_ALLOWED_BALL_DISTANCE = 150

# ==========================================
# 선수 트래커 기본값: BoT-SORT
# ==========================================
DEFAULT_P_CONF = 0.75
DEFAULT_P_BUF = 100
DEFAULT_P_MATCH = 0.80

# ==========================================
# 공 트래커 기본값: ByteTrack
# ==========================================
DEFAULT_B_CONF = 0.03
DEFAULT_B_BUF = 60
DEFAULT_B_MATCH = 0.95

# ==========================================
# 공 Frame-by-frame detection 기본값
# ==========================================
DEFAULT_B_DETECT_CONF = 0.15

# ==========================================
# 공 터치 판정 기본값
# ==========================================
TOUCH_FRAME_WINDOW = 5
TOUCH_SPEED_THRESH = 2.0
TOUCH_ANGLE_THRESH = 0.5

# 같은 터치가 여러 번 카운트되는 것 방지
TOUCH_COOLDOWN_FRAMES = 5

# 공과 선수 중심점 사이 거리가 이 값보다 크면 터치로 보지 않음
# 영상 해상도에 따라 조절 가능
TOUCH_MAX_PLAYER_DISTANCE = 300

# ==========================================
# UI 기본값
# ==========================================
MODEL_FINE_TUNED = "직접 학습시킨 모델 (Fine-Tuned)"
MODEL_BASE = "기본 모델 (YOLOv8s)"

BALL_METHOD_FRAME = "Frame-by-frame detection"
BALL_METHOD_BYTETRACK = "ByteTrack"