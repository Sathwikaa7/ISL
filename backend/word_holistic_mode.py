"""Live word-sign inference using MediaPipe pose, face, and both hands."""

from __future__ import annotations

from collections import deque
import json
import os
import time

import mediapipe as mp
import numpy as np
import tensorflow as tf

from backend.training.word_holistic_landmarks import results_to_frame


class WordHolisticPredictor:
    CONFIDENCE_THRESHOLD = 0.80
    # The browser records a complete 24-frame gesture first, then sends it in
    # order.  Predicting only once at the end prevents a resting pose from
    # being repeatedly reinterpreted as new words.

    def __init__(self, models_dir: str, model_name: str = "isl_word_holistic.keras"):
        model_stem = os.path.splitext(model_name)[0]
        with open(os.path.join(models_dir, f"{model_stem}_classes.json"), encoding="utf-8") as file:
            self.classes = json.load(file)
        self.model = tf.keras.models.load_model(os.path.join(models_dir, model_name))
        self.sequence_length = int(self.model.input_shape[1])
        self.holistic = mp.solutions.holistic.Holistic(
            static_image_mode=False,
            model_complexity=1,
            refine_face_landmarks=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.reset()

    def reset(self):
        self.frames = deque(maxlen=self.sequence_length)
        self.frame_count = self.no_pose_frames = 0
        # A word sign is one capture, not a continuous stream.  Once a
        # prediction has passed the stability check, hold it until the client
        # explicitly starts the next capture.
        self.capture_locked = False
        self.locked_label = ""
        self.locked_confidence = 0.0

    def process(self, rgb_frame: np.ndarray) -> dict:
        if self.capture_locked:
            return {
                "label": self.locked_label,
                "confidence": self.locked_confidence,
                "stable": False,
                "status": "Word captured — press Capture next word to sign again.",
            }

        results = self.holistic.process(rgb_frame)
        frame = results_to_frame(results)
        if not frame[:33, 3].max():
            self.no_pose_frames += 1
            if self.no_pose_frames >= 8:
                self.reset()
            return {"label": "", "confidence": 0.0, "stable": False, "status": "Keep your face, upper body, and hands visible."}

        self.no_pose_frames = 0
        self.frames.append(frame)
        self.frame_count += 1
        if len(self.frames) < self.sequence_length:
            return {"label": "", "confidence": 0.0, "stable": False, "status": f"Capturing motion… {len(self.frames)}/{self.sequence_length}"}

        probabilities = self.model.predict(np.expand_dims(np.asarray(self.frames, dtype=np.float32), 0), verbose=0)[0]
        top_indices = np.argsort(probabilities)[-3:][::-1]
        top3 = [(self.classes[item], float(probabilities[item]) * 100) for item in top_indices]
        print("[WORD] top 3 predictions: " + ", ".join(f"{name} {score:.1f}%" for name, score in top3))
        index = int(top_indices[0])
        confidence = float(probabilities[index]) * 100
        label = self.classes[index]
        if confidence < self.CONFIDENCE_THRESHOLD * 100:
            return {"label": "", "confidence": confidence, "stable": False, "status": "Not confident enough — repeat the complete sign clearly."}

        self.capture_locked = True
        self.locked_label = label
        self.locked_confidence = confidence
        return {"label": label, "confidence": confidence, "stable": True, "status": "Word captured — add it or capture the next word."}
