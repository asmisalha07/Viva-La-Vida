"""MediaPipe hand landmarks — pose only, so lighting and background do not matter."""

from __future__ import annotations

import threading

import numpy as np

NUM_LANDMARKS = 21
RAW_SIZE = NUM_LANDMARKS * 3  # x, y, z per joint
# 63 pose + 15 finger-bend angles/lengths + 10 fingertip distances
FEATURE_SIZE = RAW_SIZE + 15 + 10
_FINGERS = ((1, 2, 3, 4), (5, 6, 7, 8), (9, 10, 11, 12), (13, 14, 15, 16), (17, 18, 19, 20))
_TIPS = (4, 8, 12, 16, 20)

_lock = threading.Lock()
_hands_video = None


def _video_hands():
    import mediapipe as mp

    global _hands_video
    if _hands_video is None:
        _hands_video = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=1,
        )
    return _hands_video


def extract_landmarks(frame_bgr: np.ndarray, static: bool = True) -> np.ndarray | None:
    """
    BGR OpenCV frame → normalized 63-vector, or None if no hand.

    Still frames (browser /predict) get a fresh Hands graph each call.
    Reusing one graph across HTTP photos hits MediaPipe timestamp errors.
    """
    import cv2
    import mediapipe as mp

    if frame_bgr is None or frame_bgr.size == 0:
        return None
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

    with _lock:
        if static:
            hands = mp.solutions.hands.Hands(
                static_image_mode=True,
                max_num_hands=1,
                min_detection_confidence=0.4,
                model_complexity=0,
            )
            try:
                result = hands.process(rgb)
            except ValueError:
                return None
            finally:
                hands.close()
        else:
            try:
                result = _video_hands().process(rgb)
            except ValueError:
                global _hands_video
                if _hands_video is not None:
                    _hands_video.close()
                    _hands_video = None
                try:
                    result = _video_hands().process(rgb)
                except ValueError:
                    return None

    if not result.multi_hand_landmarks:
        return None
    return enrich_landmarks(normalize_hand(result.multi_hand_landmarks[0]))


def normalize_hand(hand_landmarks) -> np.ndarray:
    pts = np.array([[lm.x, lm.y, lm.z] for lm in hand_landmarks.landmark], dtype=np.float32)
    pts -= pts[0]
    span = np.max(np.linalg.norm(pts[:, :2], axis=1))
    if span > 1e-6:
        pts /= span
    return pts.flatten()


def _angle(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    ba = a - b
    bc = c - b
    denom = float(np.linalg.norm(ba) * np.linalg.norm(bc)) + 1e-6
    cos = float(np.clip(np.dot(ba, bc) / denom, -1.0, 1.0))
    return float(np.arccos(cos) / np.pi)


def enrich_landmarks(flat) -> np.ndarray:
    """Wrist-normalized 21×3 plus finger curls and tip spacing (helps M/N/S/T/E)."""
    raw = np.asarray(flat, dtype=np.float32).flatten()
    if raw.size < RAW_SIZE:
        raise ValueError("expected 63 landmark values")
    pts = raw[:RAW_SIZE].reshape(NUM_LANDMARKS, 3)
    extras = []
    for mcp, pip, dip, tip in _FINGERS:
        extras.append(_angle(pts[mcp], pts[pip], pts[dip]))
        extras.append(_angle(pts[pip], pts[dip], pts[tip]))
        extras.append(float(np.linalg.norm(pts[tip, :2])))
    for i, a in enumerate(_TIPS):
        for b in _TIPS[i + 1 :]:
            extras.append(float(np.linalg.norm(pts[a, :2] - pts[b, :2])))
    return np.concatenate([pts.flatten(), np.asarray(extras, dtype=np.float32)])


def flip_landmarks_x(flat) -> np.ndarray:
    """Mirror the hand (selfie vs photographer view / left vs right)."""
    raw = np.asarray(flat, dtype=np.float32).flatten()
    pts = raw[:RAW_SIZE].reshape(NUM_LANDMARKS, 3).copy()
    pts[:, 0] *= -1.0
    return enrich_landmarks(pts.flatten())


def jitter(features: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    raw = np.asarray(features, dtype=np.float32).flatten()
    pts = raw[:RAW_SIZE].reshape(NUM_LANDMARKS, 3).copy()
    pts += rng.normal(0.0, 0.018, size=pts.shape).astype(np.float32)
    degrees = float(rng.uniform(-18.0, 18.0))
    rad = np.deg2rad(degrees)
    cos_a, sin_a = np.cos(rad), np.sin(rad)
    xy = pts[:, :2]
    pts[:, :2] = xy @ np.array([[cos_a, -sin_a], [sin_a, cos_a]], dtype=np.float32).T
    return enrich_landmarks(pts.flatten())
