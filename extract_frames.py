import cv2
import os

# Input and output folders
INPUT_DIR = "dataset/ProcessedData_vivit"
OUTPUT_DIR = "dataset/extracted_frames"

# Save every 5th frame
FRAME_SKIP = 5

os.makedirs(OUTPUT_DIR, exist_ok=True)

for word in os.listdir(INPUT_DIR):

    word_path = os.path.join(INPUT_DIR, word)

    if not os.path.isdir(word_path):
        continue

    output_word = os.path.join(OUTPUT_DIR, word)
    os.makedirs(output_word, exist_ok=True)

    print(f"\nProcessing: {word}")

    video_count = 0

    for video in os.listdir(word_path):

        if not video.lower().endswith((".mov", ".mp4", ".avi")):
            continue

        video_path = os.path.join(word_path, video)

        cap = cv2.VideoCapture(video_path)

        frame_num = 0
        saved = 0

        while True:

            ret, frame = cap.read()

            if not ret:
                break

            if frame_num % FRAME_SKIP == 0:

                filename = f"{os.path.splitext(video)[0]}_{saved:04d}.jpg"

                cv2.imwrite(
                    os.path.join(output_word, filename),
                    frame
                )

                saved += 1

            frame_num += 1

        cap.release()
        video_count += 1

    print(f"{video_count} videos processed.")

print("\nDone!")