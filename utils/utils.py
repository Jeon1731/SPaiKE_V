import os
import utils.config as config

def upload_video(uploaded_file):
    if not os.path.exists(config.VIDEOS_PATH):
        os.makedirs(config.VIDEOS_PATH)

    if uploaded_file is not None:
        video_path = os.path.join(config.VIDEOS_PATH, uploaded_file.name)
        with open(video_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return video_path