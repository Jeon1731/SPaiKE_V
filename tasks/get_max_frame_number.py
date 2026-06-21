import os
import glob

def get_max_frame_number(video_name, labels_path):
    # 해당 video_name으로 시작하는 모든 txt 파일 찾기
    files = glob.glob(os.path.join(labels_path, f"{video_name}_*.txt"))
    
    frame_numbers = []
    for file in files:
        # 파일명만 추출
        basename = os.path.basename(file)
        # 확장자 제거
        name, _ = os.path.splitext(basename)
        # video_name 뒤의 숫자 부분 추출
        try:
            frame_num = int(name.split("_")[-1])
            frame_numbers.append(frame_num)
        except ValueError:
            continue
    
    return max(frame_numbers) if frame_numbers else None