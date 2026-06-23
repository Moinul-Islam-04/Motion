"""Ensures the MediaPipe hand-landmark model is available locally."""

import os
import urllib.request

MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/1/hand_landmarker.task"
)
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
MODEL_PATH = os.path.join(MODEL_DIR, "hand_landmarker.task")


def ensure_model():
    """Return the local model path, downloading it on first run if needed."""
    if os.path.exists(MODEL_PATH):
        return MODEL_PATH
    os.makedirs(MODEL_DIR, exist_ok=True)
    print("Downloading hand-landmark model (~7 MB, one time)...")
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")
    return MODEL_PATH
