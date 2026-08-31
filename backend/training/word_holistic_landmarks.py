"""Shared full-body landmarks for word-sign recognition."""

import numpy as np

POSE_POINTS = 33
HAND_POINTS = 21
# Eyes, brows, nose, mouth, jaw/chin: compact facial-expression representation.
FACE_INDICES = (1, 10, 13, 14, 33, 61, 70, 78, 91, 133, 152, 159, 168, 199, 263, 291, 308, 324, 356, 386)
NUM_NODES = POSE_POINTS + 2 * HAND_POINTS + len(FACE_INDICES)
FEATURES = 4


def _put(frame, offset, points, origin, scale, visibility=1.0):
    if not points:
        return
    for index, point in enumerate(points):
        frame[offset + index, :3] = ((point.x - origin[0]) / scale, (point.y - origin[1]) / scale, (point.z - origin[2]) / scale)
        frame[offset + index, 3] = getattr(point, "visibility", visibility)


def results_to_frame(results) -> np.ndarray:
    """Pose + both hands + selected face landmarks, body-centred and scale-normalised."""
    frame = np.zeros((NUM_NODES, FEATURES), dtype=np.float32)
    pose = results.pose_landmarks.landmark if results.pose_landmarks else None
    if not pose:
        return frame
    left_shoulder, right_shoulder = pose[11], pose[12]
    origin = ((left_shoulder.x + right_shoulder.x) / 2, (left_shoulder.y + right_shoulder.y) / 2, (left_shoulder.z + right_shoulder.z) / 2)
    scale = max(float(np.hypot(left_shoulder.x - right_shoulder.x, left_shoulder.y - right_shoulder.y)), 1e-4)
    _put(frame, 0, pose, origin, scale)
    _put(frame, POSE_POINTS, results.left_hand_landmarks.landmark if results.left_hand_landmarks else None, origin, scale)
    _put(frame, POSE_POINTS + HAND_POINTS, results.right_hand_landmarks.landmark if results.right_hand_landmarks else None, origin, scale)
    if results.face_landmarks:
        selected = [results.face_landmarks.landmark[index] for index in FACE_INDICES]
        _put(frame, POSE_POINTS + 2 * HAND_POINTS, selected, origin, scale)
    return frame
