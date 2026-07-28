import cv2
import mediapipe as mp

mp_hands = mp.solutions.hands

# FIX: static_image_mode=True for single frame capture
hands = mp_hands.Hands(
    static_image_mode=True,
    max_num_hands=2,
    min_detection_confidence=0.3,
    min_tracking_confidence=0.3
)


def extract_hand(frame):

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = hands.process(rgb)

    if not results.multi_hand_landmarks:
        return None

    h, w, _ = frame.shape

    hand = results.multi_hand_landmarks[0]

    xs = [lm.x for lm in hand.landmark]
    ys = [lm.y for lm in hand.landmark]

    xmin = max(int(min(xs) * w) - 20, 0)
    xmax = min(int(max(xs) * w) + 20, w)
    ymin = max(int(min(ys) * h) - 20, 0)
    ymax = min(int(max(ys) * h) + 20, h)

    crop = frame[ymin:ymax, xmin:xmax]

    if crop.size == 0:
        return None

    crop = cv2.resize(crop, (224, 224))

    return crop