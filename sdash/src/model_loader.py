'''import streamlit as st
from ultralytics import YOLO
import config

# @st.cache_resource
def load_models(model_choice):
    if "Fine-Tuned" in model_choice:
        # device='gpu' 파라미터 추가 또는 ONNX Provider 명시
        ball_model = YOLO(config.FINETUNED_BALL_MODEL, task='detect')
        player_model = YOLO(config.FINETUNED_PLAYER_MODEL, task='detect')
    else:
        ball_model = YOLO(config.BASE_YOLO_MODEL, task='detect')
        player_model = YOLO(config.BASE_YOLO_MODEL, task='detect')
        
    return ball_model, player_model
'''

from ultralytics import YOLO

import config


def load_models(model_choice: str):
    if "Fine-Tuned" in model_choice:
        ball_model_path = config.FINETUNED_BALL_MODEL
        player_model_path = config.FINETUNED_PLAYER_MODEL
    else:
        ball_model_path = config.BASE_YOLO_MODEL
        player_model_path = config.BASE_YOLO_MODEL

    ball_model = YOLO(str(ball_model_path), task="detect")
    player_model = YOLO(str(player_model_path), task="detect")

    return ball_model, player_model


def reset_model_predictors(*models):
    for model in models:
        if hasattr(model, "predictor"):
            model.predictor = None