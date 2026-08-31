"""Create alphabet training images using the same MediaPipe hand crop as live inference.

Run from D:\SLD:
    venv_preprocess\Scripts\python.exe backend\training\preprocess_alphabet_hands.py

The original images are never changed. Cropped images are written to
dataset/alphabet_cropped/<label>/ and can be used for retraining.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import mediapipe as mp
import numpy as np
from PIL import Image


PROJECT_DIR = Path(__file__).resolve().parents[2]
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}


def crop_hands(image: Image.Image, hands) -> Image.Image | None:
    frame = np.asarray(image.convert("RGB"))
    height, width = frame.shape[:2]
    results = hands.process(frame)
    if not results.multi_hand_landmarks:
        return None

    landmarks = [point for hand in results.multi_hand_landmarks for point in hand.landmark]
    xs = [point.x for point in landmarks]
    ys = [point.y for point in landmarks]
    xmin, xmax = int(min(xs) * width), int(max(xs) * width)
    ymin, ymax = int(min(ys) * height), int(max(ys) * height)

    padding = max(12, int(max(xmax - xmin, ymax - ymin) * 0.20))
    xmin, xmax = xmin - padding, xmax + padding
    ymin, ymax = ymin - padding, ymax + padding
    size = max(xmax - xmin, ymax - ymin)
    centre_x, centre_y = (xmin + xmax) // 2, (ymin + ymax) // 2
    xmin, ymin = max(0, centre_x - size // 2), max(0, centre_y - size // 2)
    xmax, ymax = min(width, xmin + size), min(height, ymin + size)
    if xmax <= xmin or ymax <= ymin:
        return None
    return Image.fromarray(frame[ymin:ymax, xmin:xmax]).resize((224, 224), Image.Resampling.LANCZOS)


def main() -> None:
    parser = argparse.ArgumentParser(description="Crop alphabet images around detected hands.")
    parser.add_argument("--input", type=Path, default=PROJECT_DIR / "dataset" / "alphabet")
    parser.add_argument("--output", type=Path, default=PROJECT_DIR / "dataset" / "alphabet_cropped")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if not args.input.is_dir():
        raise FileNotFoundError(args.input)

    saved = skipped = existing = 0
    with mp.solutions.hands.Hands(static_image_mode=True, max_num_hands=2, min_detection_confidence=0.5) as hands:
        for class_dir in sorted(path for path in args.input.iterdir() if path.is_dir()):
            output_dir = args.output / class_dir.name
            output_dir.mkdir(parents=True, exist_ok=True)
            for source in sorted(path for path in class_dir.iterdir() if path.suffix.lower() in IMAGE_SUFFIXES):
                target = output_dir / f"{source.stem}.jpg"
                if target.exists() and not args.overwrite:
                    existing += 1
                    continue
                try:
                    with Image.open(source) as image:
                        crop = crop_hands(image, hands)
                    if crop is None:
                        skipped += 1
                        continue
                    crop.save(target, quality=95)
                    saved += 1
                except OSError:
                    skipped += 1
            print(f"{class_dir.name}: done")
    print(f"Saved={saved}, existing={existing}, skipped(no hand/unreadable)={skipped}")
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
