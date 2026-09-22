"""Classify a webcam frame from MediaPipe landmarks (Random Forest or leftover Keras)."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from model.labels import generic_saved_kind, get_labels
from services.landmarks import FEATURE_SIZE, RAW_SIZE, enrich_landmarks, extract_landmarks
from services.preprocess import crop_center_roi

MODEL_DIR = Path(__file__).resolve().parent
GENERIC_MODEL = MODEL_DIR / "sign_model.keras"
LETTER_RF = MODEL_DIR / "sign_model_letters.joblib"
WORD_RF = MODEL_DIR / "sign_model_words.joblib"
LETTER_MODEL = MODEL_DIR / "sign_model_letters.keras"
WORD_MODEL = MODEL_DIR / "sign_model_words.keras"

_cache: dict = {}


def _path_for(kind: str) -> Path | None:
    if kind == "letters":
        if LETTER_RF.exists():
            return LETTER_RF
        if LETTER_MODEL.exists():
            return LETTER_MODEL
        if GENERIC_MODEL.exists() and generic_saved_kind() == "letters":
            return GENERIC_MODEL
        return None
    if WORD_RF.exists():
        return WORD_RF
    if WORD_MODEL.exists():
        return WORD_MODEL
    if GENERIC_MODEL.exists() and generic_saved_kind() == "words":
        return GENERIC_MODEL
    return None


def model_is_ready(kind: str | None = None) -> bool:
    if kind in ("letters", "words"):
        return _path_for(kind) is not None
    return any(p.exists() for p in (LETTER_RF, WORD_RF, LETTER_MODEL, WORD_MODEL, GENERIC_MODEL))


def get_model(kind: str = "letters"):
    path = _path_for(kind)
    if path is None:
        return None
    key = str(path)
    mtime = path.stat().st_mtime
    entry = _cache.get(key)
    if entry is None or entry["mtime"] != mtime:
        if str(path).endswith(".joblib"):
            import joblib

            _cache[key] = {"mtime": mtime, "model": joblib.load(path)}
        else:
            from tensorflow.keras.models import load_model

            _cache[key] = {"mtime": mtime, "model": load_model(path)}
    return _cache[key]["model"]


def _vector(features: np.ndarray, feat_dim: int) -> np.ndarray:
    feat = np.asarray(features, dtype=np.float32).flatten()
    if feat.size == RAW_SIZE:
        feat = enrich_landmarks(feat)
    if feat.size >= feat_dim:
        return feat[:feat_dim]
    return feat


def _empty(kind: str, labels: list[str]) -> dict:
    return {
        "letter": "nothing",
        "raw_letter": "nothing",
        "confidence": 0.0,
        "confidence_percent": 0.0,
        "margin": 0.0,
        "probabilities": {label: 0.0 for label in labels},
        "top3": [],
        "hand_detected": False,
        "mode": kind,
    }


def _pack(kind: str, labels: list[str], probabilities: np.ndarray) -> dict:
    ranked = np.argsort(probabilities)[::-1]
    index = int(ranked[0])
    second = int(ranked[1]) if len(ranked) > 1 else index
    if index >= len(labels):
        raise RuntimeError(f"{kind} model class count does not match labels. Retrain.")
    guess = labels[index]
    confidence = float(probabilities[index])
    margin = float(probabilities[index] - probabilities[second])
    min_conf = 0.4 if kind == "letters" else 0.5
    min_margin = 0.08 if kind == "letters" else 0.08
    letter = guess if confidence >= min_conf and margin >= min_margin else "nothing"
    if kind == "letters" and str(guess).lower() == "nothing" and confidence >= min_conf:
        letter = "space"
    breakdown = {
        label: round(float(prob), 4) for label, prob in zip(labels, probabilities[: len(labels)])
    }
    top3 = []
    for idx in ranked[:3]:
        if int(idx) >= len(labels):
            break
        top3.append(
            {"label": labels[int(idx)], "percent": round(float(probabilities[int(idx)]) * 100, 1)}
        )
    return {
        "letter": letter,
        "raw_letter": letter if letter != "nothing" else guess,
        "confidence": round(confidence, 4),
        "confidence_percent": round(confidence * 100, 1),
        "margin": round(margin, 4),
        "probabilities": breakdown,
        "top3": top3,
        "hand_detected": True,
        "mode": kind,
    }


def _rf_probs(bundle: dict, feat: np.ndarray, labels: list[str]) -> np.ndarray:
    clf = bundle["model"]
    feat = _vector(feat, int(bundle.get("feat_dim") or FEATURE_SIZE))
    raw = clf.predict_proba(feat.reshape(1, -1))[0]
    # Map sklearn class ids onto our label order.
    out = np.zeros(len(labels), dtype=np.float32)
    for cls_i, prob in zip(clf.classes_, raw):
        idx = int(cls_i)
        if 0 <= idx < len(labels):
            out[idx] = float(prob)
    return out


def predict_letter(frame_bgr: np.ndarray, kind: str = "letters") -> dict:
    kind = "words" if kind == "words" else "letters"
    model = get_model(kind)
    if model is None:
        raise FileNotFoundError(
            f"No {kind} model. Train with: python model/train.py --source {kind}"
        )

    labels = get_labels(kind)
    if isinstance(model, dict) and model.get("labels"):
        labels = list(model["labels"])
    empty = _empty(kind, labels)
    try:
        roi = crop_center_roi(frame_bgr)
        features = extract_landmarks(roi, static=True)
        if features is None:
            features = extract_landmarks(frame_bgr, static=True)
    except Exception:
        return empty
    if features is None:
        return empty

    try:
        if isinstance(model, dict) and model.get("type") == "rf":
            probabilities = _rf_probs(model, features, labels)
        else:
            feat = _vector(features, FEATURE_SIZE)
            shape = model.input_shape
            if len(shape) == 3:
                seq_len = int(shape[1] or 12)
                batch = np.repeat(feat[np.newaxis, : int(shape[2])], seq_len, axis=0)
                probabilities = model.predict(batch[np.newaxis, ...], verbose=0)[0]
            else:
                probabilities = model.predict(np.expand_dims(feat[: int(shape[1])], 0), verbose=0)[0]
    except Exception as exc:
        raise RuntimeError(
            f"The {kind} model does not match landmarks. Retrain: python model/train.py --source {kind}"
        ) from exc

    return _pack(kind, labels, probabilities)
