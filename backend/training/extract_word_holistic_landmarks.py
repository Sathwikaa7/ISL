"""Extract pose, face, and hand sequences from the downloaded word videos."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np

# Allows both `python -m backend.training...` and direct script execution
# from D:\SLD, which is how the existing training commands are documented.
PROJECT_DIR = Path(__file__).resolve().parents[2]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from backend.training.extract_word_landmarks import iter_labeled_videos, selected_frame_indices
from backend.training.word_holistic_landmarks import results_to_frame



def extract_video(path: Path, holistic, frames: int):
    capture = cv2.VideoCapture(str(path))
    try:
        targets = selected_frame_indices(int(capture.get(cv2.CAP_PROP_FRAME_COUNT)), frames)
        sequence, target, index = [], 0, 0
        while target < len(targets):
            ok, bgr = capture.read()
            if not ok:
                break
            while target < len(targets) and index == targets[target]:
                rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
                rgb.flags.writeable = False
                sequence.append(results_to_frame(holistic.process(rgb)))
                target += 1
            index += 1
        if not sequence:
            return None
        while len(sequence) < frames:
            sequence.append(sequence[-1].copy())
        return np.asarray(sequence[:frames], dtype=np.float32)
    finally:
        capture.release()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, default=PROJECT_DIR / 'dataset' / 'words')
    parser.add_argument('--output', type=Path, default=PROJECT_DIR / 'dataset' / 'word_holistic_landmarks')
    parser.add_argument('--frames', type=int, default=24)
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args()
    videos = list(iter_labeled_videos(args.input))
    if not videos:
        raise RuntimeError(f'No videos found in {args.input}')
    rows, saved, skipped = [], 0, 0
    with mp.solutions.holistic.Holistic(static_image_mode=False, model_complexity=1, refine_face_landmarks=False, min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
        for label in sorted({label for label, _, _ in videos}):
            output_dir = args.output / label
            output_dir.mkdir(parents=True, exist_ok=True)
            for video_label, path, group in (item for item in videos if item[0] == label):
                target = output_dir / f'{"sample" if group.startswith("sample:") else "video"}__{path.stem}.npy'
                if target.exists() and not args.overwrite:
                    rows.append([str(target.resolve()), label, group, path.name, 'existing']); continue
                data = extract_video(path, holistic, args.frames)
                if data is None:
                    skipped += 1; rows.append(['', label, group, path.name, 'skipped']); continue
                np.save(target, data); saved += 1
                rows.append([str(target.resolve()), label, group, path.name, 'extracted'])
            print(f'{label}: done')
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / 'manifest.csv').open('w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file); writer.writerow(['landmark_path','label','group_id','source_video','status']); writer.writerows(rows)
    print(f'Saved={saved}, skipped={skipped}, output={args.output}')


if __name__ == '__main__':
    main()
