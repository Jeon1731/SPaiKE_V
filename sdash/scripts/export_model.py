from ultralytics import YOLO

model_paths = [
    './models/player_best.pt', 
    './models/ball_best.pt',
    './models/yolov8s.pt'
]

print("두 모델의 ONNX 변환을 시작합니다...\n")

for path in model_paths:
    print(f"[{path}] 로딩 중...")
    model = YOLO(path)
    
    # ONNX 변환
    model.export(format='onnx', opset=12)
    print(f"[{path}] 변환 완료!\n")

print("모든 변환 작업이 끝났습니다! models 폴더를 확인해 보세요.")