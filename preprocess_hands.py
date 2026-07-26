import os
import cv2
import mediapipe as mp

# ==========================
# Paths
# ==========================
INPUT_DIR = "dataset/ProcessedData_vivit"
OUTPUT_DIR = "dataset/processed_hands"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==========================
# MediaPipe Hands
# ==========================
mp_hands = mp.solutions.hands

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.4,
    min_tracking_confidence=0.4
)

FRAME_SKIP = 2

total_saved = 0

# ==========================
# Process each class
# ==========================
for class_name in sorted(os.listdir(INPUT_DIR)):

    class_path = os.path.join(INPUT_DIR, class_name)

    if not os.path.isdir(class_path):
        continue

    save_class = os.path.join(OUTPUT_DIR, class_name)
    os.makedirs(save_class, exist_ok=True)

    image_count = 0
    total_frames = 0
    detected_frames = 0
    total_videos = 0

    print("=" * 60)
    print(f"Processing: {class_name}")

    for video_name in os.listdir(class_path):

        if not video_name.lower().endswith((".mov", ".mp4", ".avi")):
            continue

        total_videos += 1

        video_path = os.path.join(class_path, video_name)

        cap = cv2.VideoCapture(video_path)

        frame_num = 0

        while True:

            success, frame = cap.read()

            if not success:
                break

            frame_num += 1
            total_frames += 1

            if frame_num % FRAME_SKIP != 0:
                continue

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            results = hands.process(rgb)

            if results.multi_hand_landmarks:

                detected_frames += 1

                h, w, _ = frame.shape

                for hand_landmarks in results.multi_hand_landmarks:

                    xs = [lm.x for lm in hand_landmarks.landmark]
                    ys = [lm.y for lm in hand_landmarks.landmark]

                    xmin = max(int(min(xs) * w) - 30, 0)
                    xmax = min(int(max(xs) * w) + 30, w)

                    ymin = max(int(min(ys) * h) - 30, 0)
                    ymax = min(int(max(ys) * h) + 30, h)

                    crop = frame[ymin:ymax, xmin:xmax]

                    if crop.size == 0:
                        continue

                    crop = cv2.resize(crop, (224, 224))

                    filename = f"{class_name}_{image_count}.jpg"

                    cv2.imwrite(
                        os.path.join(save_class, filename),
                        crop
                    )

                    image_count += 1
                    total_saved += 1

        cap.release()

    print(f"Videos           : {total_videos}")
    print(f"Frames Checked   : {total_frames}")
    print(f"Frames Detected  : {detected_frames}")
    print(f"Images Saved     : {image_count}")
    print()

hands.close()

print("=" * 60)
print("Preprocessing Finished!")
print(f"Total Images Saved: {total_saved}")