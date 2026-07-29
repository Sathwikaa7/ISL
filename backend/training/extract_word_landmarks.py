"""Extract fixed-length MediaPipe landmark sequences for ISL word videos.

This script is intentionally independent of the alphabet pipeline.  It reads
``dataset/words/<class>/*.mp4`` and writes only new ``.npy`` files under
``dataset/word_landmarks``.  Every output has shape ``(48, 42, 4)``:

* 24 uniformly sampled frames
* 42 nodes (21 left-hand landmarks followed by 21 right-hand landmarks)
* 4 features per node: normalized x, y, z and a hand-present flag

Run from D:\\SLD:
    venv_preprocess\\Scripts\\python.exe backend\\training\\extract_word_landmarks.py
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np


DEFAULT_INPUT = Path(r"D:\SLD\dataset\words")
DEFAULT_OUTPUT = Path(r"D:\SLD\dataset\word_landmarks")
LANDMARKS_PER_HAND = 21
NUM_HANDS = 2
FEATURES_PER_NODE = 4


def safe_label(label: str) -> str:
    """Convert a display folder name into a stable model label."""
    return re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")


def selected_frame_indices(frame_count: int, sequence_length: int) -> np.ndarray:
    """Uniformly sample a clip while retaining its start and end."""
    if frame_count < 1:
        return np.array([], dtype=np.int32)
    return np.linspace(0, frame_count - 1, sequence_length).round().astype(np.int32)


def empty_frame() -> np.ndarray:
    return np.zeros((NUM_HANDS * LANDMARKS_PER_HAND, FEATURES_PER_NODE), dtype=np.float32)


def landmarks_to_frame(results) -> np.ndarray:
    """Return left/right ordered, wrist-centred landmarks for one video frame."""
    frame = empty_frame()
    if not results.multi_hand_landmarks or not results.multi_handedness:
        return frame

    hands: dict[str, np.ndarray] = {}
    for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
        label = handedness.classification[0].label.lower()
        if label not in {"left", "right"} or label in hands:
            continue
        hands[label] = np.array(
            [[point.x, point.y, point.z] for point in hand_landmarks.landmark],
            dtype=np.float32,
        )

    if not hands:
        return frame

    # Centre both hands together.  This retains their relative positions,
    # unlike normalising each hand independently.
    wrists = np.array([points[0] for points in hands.values()], dtype=np.float32)
    centre = wrists.mean(axis=0)
    palm_sizes = [np.linalg.norm(points[9] - points[0]) for points in hands.values()]
    scale = max(float(np.mean(palm_sizes)), 1e-4)

    for offset, side in ((0, "left"), (LANDMARKS_PER_HAND, "right")):
        points = hands.get(side)
        if points is None:
            continue
        normalized = (points - centre) / scale
        frame[offset : offset + LANDMARKS_PER_HAND, :3] = normalized
        frame[offset : offset + LANDMARKS_PER_HAND, 3] = 1.0

    return frame


def extract_video(video_path: Path, hands, sequence_length: int) -> np.ndarray | None:
    capture = cv2.VideoCapture(str(video_path))
    try:
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        targets = selected_frame_indices(frame_count, sequence_length)
        if len(targets) == 0:
            return None

        sequence = []
        target_position = 0
        frame_index = 0
        while target_position < len(targets):
            ok, bgr = capture.read()
            if not ok:
                break
            while target_position < len(targets) and frame_index == targets[target_position]:
                rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
                rgb.flags.writeable = False
                sequence.append(landmarks_to_frame(hands.process(rgb)))
                target_position += 1
            frame_index += 1

        if not sequence:
            return None
        # A damaged video may end early; preserve a fixed input shape.
        while len(sequence) < sequence_length:
            sequence.append(sequence[-1].copy())
        return np.stack(sequence[:sequence_length]).astype(np.float32)
    finally:
        capture.release()


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract MediaPipe hand landmarks from ISL word videos.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--frames", type=int, default=24)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    if args.frames < 2:
        raise ValueError("--frames must be at least 2")
    if not args.input.is_dir():
        raise FileNotFoundError(f"Input folder does not exist: {args.input}")

    class_dirs = sorted(path for path in args.input.iterdir() if path.is_dir())
    if not class_dirs:
        raise RuntimeError(f"No class folders found in {args.input}")

    labels = {safe_label(path.name): path.name for path in class_dirs}
    if len(labels) != len(class_dirs):
        raise RuntimeError("Two class folder names become the same normalized label.")

    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "classes.json").open("w", encoding="utf-8") as file:
        json.dump(labels, file, indent=2)

    manifest_rows = []
    extracted = skipped = 0
    mp_hands = mp.solutions.hands
    with mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=2,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ) as hands:
        for class_dir in class_dirs:
            label = safe_label(class_dir.name)
            output_dir = args.output / label
            output_dir.mkdir(parents=True, exist_ok=True)
            videos = sorted(path for path in class_dir.iterdir() if path.suffix.lower() in {".mp4", ".avi", ".mov", ".mkv"})
            print(f"{class_dir.name}: {len(videos)} videos")
            for video_path in videos:
                output_path = output_dir / f"{video_path.stem}.npy"
                if output_path.exists() and not args.overwrite:
                    extracted += 1
                    manifest_rows.append([str(output_path), label, video_path.name, "existing"])
                    continue
                sequence = extract_video(video_path, hands, args.frames)
                if sequence is None:
                    skipped += 1
                    print(f"  skipped unreadable video: {video_path.name}")
                    manifest_rows.append(["", label, video_path.name, "skipped"])
                    continue
                np.save(output_path, sequence)
                extracted += 1
                manifest_rows.append([str(output_path), label, video_path.name, "extracted"])

    with (args.output / "manifest.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["landmark_path", "label", "source_video", "status"])
        writer.writerows(manifest_rows)
    print(f"Done. {extracted} sequences available; {skipped} videos skipped.")
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
