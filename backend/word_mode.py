"""Live, word-only ST-GCN inference.  This module never serves alphabet mode."""

from __future__ import annotations

from collections import Counter, deque
import json
import os
import time

import mediapipe as mp
import numpy as np
import tensorflow as tf

from backend.training.extract_word_landmarks import landmarks_to_frame
from backend.training.train_word_stgcn import GraphConvolution, STGCNBlock


class WordPredictor:
    CONFIDENCE_THRESHOLD = 0.85
    REQUIRED_VOTES = 4
    VOTE_WINDOW = 5
    PREDICT_EVERY = 4
    COOLDOWN_SECONDS = 1.5

    def __init__(self, models_dir: str):
        model_path = os.path.join(models_dir, "isl_word_stgcn.keras")
        classes_path = os.path.join(models_dir, "word_classes.json")
        with open(classes_path, encoding="utf-8") as file:
            self.classes = json.load(file)
        self.model = tf.keras.models.load_model(
            model_path,
            custom_objects={"GraphConvolution": GraphConvolution, "STGCNBlock": STGCNBlock},
        )
        # Keep live inference tied to the model's training shape.  After a
        # 24-frame retrain, this becomes 24 automatically.
        self.sequence_length = int(self.model.input_shape[1])
        self.hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.reset()

    def reset(self):
        self.frames = deque(maxlen=self.sequence_length)
        self.votes = deque(maxlen=self.VOTE_WINDOW)
        self.frame_count = 0
        self.no_hand_frames = 0
        self.last_accepted_label = None
        self.last_accepted_at = 0.0

    def process(self, rgb_frame: np.ndarray) -> dict:
        results = self.hands.process(rgb_frame)
        frame = landmarks_to_frame(results)
        hand_detected = bool(frame[:, 3].max())

        if not hand_detected:
            self.no_hand_frames += 1
            if self.no_hand_frames >= 12:
                self.reset()
            return {"label": "", "confidence": 0.0, "stable": False, "status": "Show your signing hand(s) in the guide."}

        self.no_hand_frames = 0
        self.frames.append(frame)
        self.frame_count += 1
        if len(self.frames) < self.sequence_length:
            return {
                "label": "",
                "confidence": 0.0,
                "stable": False,
                "status": f"Capturing sign… {len(self.frames)}/{self.sequence_length}",
            }
        if self.frame_count % self.PREDICT_EVERY:
            return {"label": "", "confidence": 0.0, "stable": False, "status": "Reading sign…"}

        sequence = np.expand_dims(np.asarray(self.frames, dtype=np.float32), axis=0)
        probabilities = self.model.predict(sequence, verbose=0)[0]
        index = int(np.argmax(probabilities))
        confidence = float(probabilities[index]) * 100
        label = self.classes[index]
        if confidence < self.CONFIDENCE_THRESHOLD * 100:
            self.votes.clear()
            return {"label": label, "confidence": confidence, "stable": False, "status": "Hold the complete sign clearly."}

        self.votes.append(index)
        stable = self.votes.count(index) >= self.REQUIRED_VOTES
        now = time.monotonic()
        if stable and (label != self.last_accepted_label or now - self.last_accepted_at >= self.COOLDOWN_SECONDS):
            self.last_accepted_label = label
            self.last_accepted_at = now
            return {"label": label, "confidence": confidence, "stable": True, "status": "Word ready — confirm to add."}
        return {"label": label, "confidence": confidence, "stable": False, "status": "Stabilizing prediction…"}
