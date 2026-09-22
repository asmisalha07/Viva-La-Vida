"""Live-hand ASL letter cues from MediaPipe joints (webcam, not Kaggle photos)."""

from __future__ import annotations

import numpy as np

# MediaPipe: 0 wrist, 4 thumb tip, 8 index, 12 middle, 16 ring, 20 pinky
_THUMB = (2, 3, 4)
_INDEX = (5, 6, 8)
_MIDDLE = (9, 10, 12)
_RING = (13, 14, 16)
_PINKY = (17, 18, 20)


def _pts(feat: np.ndarray) -> np.ndarray:
    raw = np.asarray(feat, dtype=np.float32).flatten()
    return raw[:63].reshape(21, 3)


def _dist(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(a[:2] - b[:2]))


def _extended(pts: np.ndarray, mcp: int, pip: int, tip: int) -> bool:
    wrist = pts[0, :2]
    d_tip = float(np.linalg.norm(pts[tip, :2] - wrist))
    d_pip = float(np.linalg.norm(pts[pip, :2] - wrist))
    d_mcp = float(np.linalg.norm(pts[mcp, :2] - wrist))
    return d_tip > d_pip * 1.12 and d_tip > d_mcp * 1.05


def _angle(u: np.ndarray, v: np.ndarray) -> float:
    nu = float(np.linalg.norm(u)) + 1e-6
    nv = float(np.linalg.norm(v)) + 1e-6
    cos = float(np.clip(np.dot(u, v) / (nu * nv), -1.0, 1.0))
    return float(np.degrees(np.arccos(cos)))


def _finger_flags(pts: np.ndarray) -> dict[str, bool]:
    return {
        "thumb": _extended(pts, *_THUMB),
        "index": _extended(pts, *_INDEX),
        "middle": _extended(pts, *_MIDDLE),
        "ring": _extended(pts, *_RING),
        "pinky": _extended(pts, *_PINKY),
    }


def classify_asl_letter(feat: np.ndarray) -> tuple[str, float]:
    """
    Return (letter, confidence 0–1) from finger geometry.
    Unsure poses return ("nothing", low).
    """
    pts = _pts(feat)
    f = _finger_flags(pts)
    index, middle, ring, pinky, thumb = f["index"], f["middle"], f["ring"], f["pinky"], f["thumb"]
    up = sum([index, middle, ring, pinky])

    tip_i, tip_m, tip_r, tip_p, tip_t = pts[8], pts[12], pts[16], pts[20], pts[4]
    im = _dist(tip_i, tip_m)
    ir = _dist(tip_i, tip_r)
    mp = _dist(tip_m, tip_p)
    touch_ti = _dist(tip_t, tip_i)
    cluster = np.mean([_dist(tip_t, tip_i), _dist(tip_t, tip_m), _dist(tip_t, tip_r), _dist(tip_t, tip_p)])

    idx_vec = pts[8, :2] - pts[5, :2]
    mid_vec = pts[12, :2] - pts[9, :2]
    spread = _angle(idx_vec, mid_vec)

    # Distinctive open shapes first — these are the review-safe letters.
    if thumb and index and not middle and not ring and not pinky:
        return "L", 0.92
    if pinky and not index and not middle and not ring:
        return "I", 0.9
    if thumb and pinky and not index and not middle and not ring:
        return "Y", 0.92
    if index and middle and ring and not pinky:
        return "W", 0.9
    if index and middle and not ring and not pinky:
        if spread >= 22:
            return "V", 0.9
        if _dist(tip_i, pts[10]) < 0.22:  # index crosses toward middle PIP
            return "R", 0.72
        return "U", 0.82
    if index and middle and ring and pinky:
        if touch_ti < 0.18 and not thumb:
            return "F", 0.8
        return "B", 0.88
    if index and not middle and not ring and not pinky:
        if thumb and touch_ti < 0.22:
            return "D", 0.7
        return "D", 0.78

    # Closed / curved family
    if up == 0:
        if cluster < 0.22:
            return "O", 0.8
        span = float(np.max(np.linalg.norm(pts[:, :2], axis=1)))
        if 0.35 < cluster < 0.7 and span > 0.55:
            return "C", 0.75
        # Fist: A thumb beside, S thumb in front, E tighter curl
        thumb_side = abs(float(tip_t[0] - pts[5, 0]))
        if thumb_side > 0.22:
            return "A", 0.78
        if _dist(tip_t, pts[6]) < _dist(tip_t, pts[5]):
            return "S", 0.7
        return "A", 0.65

    if up == 1 and index and thumb:
        return "L", 0.7

    return "nothing", 0.2


def apply_geometry(feat: np.ndarray, labels: list[str], probabilities: np.ndarray) -> np.ndarray:
    """Boost the geometry letter so live webcam wins over the Kaggle photo model."""
    letter, conf = classify_asl_letter(feat)
    if letter == "nothing" or letter not in labels or conf < 0.62:
        return probabilities
    out = probabilities.astype(np.float64).copy()
    idx = labels.index(letter)
    # Mix: geometry dominates when it is sure.
    one = np.zeros_like(out)
    one[idx] = 1.0
    mixed = (1.0 - conf) * out + conf * one
    mixed_sum = float(mixed.sum()) + 1e-8
    return (mixed / mixed_sum).astype(np.float32)
