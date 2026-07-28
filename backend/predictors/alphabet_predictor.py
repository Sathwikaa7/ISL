import json
import os

import mediapipe as mp
import numpy as np
import tensorflow as tf
from PIL import Image

# ======================================
# Load MobileNetV3 Model
# ======================================

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

MODEL_PATH = os.path.join(BASE_DIR, "models", "isl_model.keras")
CLASS_PATH = os.path.join(BASE_DIR, "models", "alphabet_classes.json")

MODEL = tf.keras.models.load_model(MODEL_PATH)

with open(CLASS_PATH, "r") as f:
    CLASSES = json.load(f)

# ======================================
# MediaPipe
# FIX 1: static_image_mode=True for single frame capture
# FIX 2: max_num_hands=1 (alphabet needs one hand only)
# FIX 3: increased detection confidence
# ======================================

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=True,
    max_num_hands=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# ======================================
# Predictor
# ======================================

def predict(image):

    frame = np.array(image)

    h, w = frame.shape[:2]

    results = hands.process(frame)

    if not results.multi_hand_landmarks:
        print("[ALPHABET] No hand detected in captured frame")
        return None, 0

    hand = results.multi_hand_landmarks[0]

    xs = [lm.x for lm in hand.landmark]
    ys = [lm.y for lm in hand.landmark]

    # ------------------------------------
    # Bounding box with square crop
    # ------------------------------------

    xmin = int(min(xs) * w)
    xmax = int(max(xs) * w)
    ymin = int(min(ys) * h)
    ymax = int(max(ys) * h)

    # Training images contain the hand with substantial surrounding context;
    # a tight live crop made the hand 2-3x larger than during training.
    # Use proportional padding to keep the live hand scale comparable.
    padding = max(35, int(max(xmax - xmin, ymax - ymin) * 0.75))
    xmin -= padding
    xmax += padding
    ymin -= padding
    ymax += padding

    bw = xmax - xmin
    bh = ymax - ymin
    size = max(bw, bh)

    cx = (xmin + xmax) // 2
    cy = (ymin + ymax) // 2

    xmin = max(0, cx - size // 2)
    ymin = max(0, cy - size // 2)
    xmax = min(w, xmin + size)
    ymax = min(h, ymin + size)

    crop = frame[ymin:ymax, xmin:xmax]

    if crop.size == 0:
        return None, 0

    # ------------------------------------
    # Preprocess
    # ------------------------------------

    crop = Image.fromarray(crop).resize((224, 224))

    # The saved model already contains MobileNetV3 preprocessing.  Passing
    # normalised pixels here normalises them a second time and gives the model
    # inputs unlike the raw RGB 0-255 images used during training.
    crop = np.array(crop, dtype=np.float32)
    crop = np.expand_dims(crop, axis=0)

    # ------------------------------------
    # Predict
    # ------------------------------------

    prediction = MODEL.predict(crop, verbose=0)[0]

    idx = np.argmax(prediction)
    confidence = float(prediction[idx]) * 100

    print(f"[DEBUG] Top 3 predictions:")
    top3 = np.argsort(prediction)[-3:][::-1]
    for i in top3:
        print(f"  {CLASSES[i]}: {prediction[i]*100:.1f}%")

    return CLASSES[idx], confidence
