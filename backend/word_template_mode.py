"""All-word retrieval based on landmark-motion templates from the supplied videos."""

from __future__ import annotations

from collections import deque
from pathlib import Path

import mediapipe as mp
import numpy as np

from backend.training.word_holistic_landmarks import results_to_frame


class WordTemplatePredictor:
    """Match one captured sign against every labelled source-motion template."""

    TEMPLATES_PER_WORD = 8
    # Upper body, both wrists/fingers, and compact facial landmarks.  These
    # hold the motion information relevant to ISL without background pixels.
    FEATURE_NODES = np.array([
        0, 11, 12, 13, 14, 15, 16, 23, 24,
        33, 37, 41, 45, 49, 53,
        54, 58, 62, 66, 70, 74,
        75, 77, 78, 79, 81, 85, 91, 94,
    ])
    MAX_DISTANCE = 1.15

    def __init__(self, dataset_dir: str, sequence_length: int = 24):
        self.sequence_length = sequence_length
        self.templates = self._load_templates(Path(dataset_dir))
        self.classes = sorted(self.templates)
        if not self.classes:
            raise RuntimeError(f"No landmark templates were found in {dataset_dir}")
        self.holistic = mp.solutions.holistic.Holistic(
            static_image_mode=False,
            model_complexity=1,
            refine_face_landmarks=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.reset()

    def _load_templates(self, root: Path) -> dict[str, list[np.ndarray]]:
        templates: dict[str, list[np.ndarray]] = {}
        for directory in sorted(path for path in root.iterdir() if path.is_dir()):
            files = sorted(directory.glob("*.npy"))
            if not files:
                continue
            choices = np.linspace(0, len(files) - 1, min(self.TEMPLATES_PER_WORD, len(files)), dtype=int)
            templates[directory.name] = [self._features(np.load(files[index]).astype(np.float32)) for index in choices]
        print(f"[WORD] Loaded {sum(map(len, templates.values()))} motion templates across {len(templates)} words.")
        return templates

    def reset(self):
        self.frames = deque(maxlen=self.sequence_length)
        self.no_pose_frames = 0
        self.capture_locked = False
        self.locked_label = ""
        self.locked_confidence = 0.0

    def _features(self, sequence: np.ndarray) -> np.ndarray:
        selected = sequence[:, self.FEATURE_NODES, :3].copy()
        visible = sequence[:, self.FEATURE_NODES, 3:4] > 0.05
        # Missing landmarks must not become evidence for a particular word.
        selected *= visible
        return selected

    @staticmethod
    def _dtw_distance(live: np.ndarray, template: np.ndarray) -> float:
        # Frame-to-frame Euclidean distance, with dynamic time warping so a
        # live signer can perform the same motion at a different speed.
        local = np.sqrt(np.mean((live[:, None] - template[None, :]) ** 2, axis=(2, 3)))
        rows, columns = local.shape
        costs = np.full((rows + 1, columns + 1), np.inf, dtype=np.float32)
        costs[0, 0] = 0.0
        for row in range(1, rows + 1):
            for column in range(1, columns + 1):
                costs[row, column] = local[row - 1, column - 1] + min(
                    costs[row - 1, column], costs[row, column - 1], costs[row - 1, column - 1]
                )
        return float(costs[rows, columns] / (rows + columns))

    def _rank(self, live: np.ndarray) -> list[tuple[str, float]]:
        scores = [
            (label, min(self._dtw_distance(live, template) for template in examples))
            for label, examples in self.templates.items()
        ]
        return sorted(scores, key=lambda item: item[1])

    def process(self, rgb_frame: np.ndarray) -> dict:
        if self.capture_locked:
            return {"label": self.locked_label, "confidence": self.locked_confidence, "stable": False, "status": "Word captured — press Capture word to sign again."}

        results = self.holistic.process(rgb_frame)
        frame = results_to_frame(results)
        if not frame[:33, 3].max():
            self.no_pose_frames += 1
            return {"label": "", "confidence": 0.0, "stable": False, "status": "Keep face, upper body, and hands visible."}

        self.no_pose_frames = 0
        self.frames.append(frame)
        if len(self.frames) < self.sequence_length:
            return {"label": "", "confidence": 0.0, "stable": False, "status": f"Capturing motion… {len(self.frames)}/{self.sequence_length}"}

        rankings = self._rank(self._features(np.asarray(self.frames, dtype=np.float32)))
        print("[WORD] closest motion top 3: " + ", ".join(f"{label} d={distance:.3f}" for label, distance in rankings[:3]))
        label, distance = rankings[0]
        confidence = 100.0 / (1.0 + distance)
        if distance > self.MAX_DISTANCE:
            self.capture_locked = True
            return {"label": "", "confidence": confidence, "stable": False, "status": "No close word match — repeat the complete sign."}

        self.capture_locked = True
        self.locked_label = label
        self.locked_confidence = confidence
        return {"label": label, "confidence": confidence, "stable": True, "status": "Closest motion captured — add it or capture the next word."}