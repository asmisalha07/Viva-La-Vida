"""OpenCV preprocessing shared by training, capture, and the prediction API."""

from __future__ import annotations

import base64
import cv2
import numpy as np

# CNN input size. Slightly larger than 64 so finger gaps stay visible.
IMAGE_SIZE = 96


def crop_center_roi(frame: np.ndarray, roi_ratio: float = 0.55) -> np.ndarray:
    """
    Take a square region from the center of the frame.

    The React UI draws the same guide box so the user places their hand here.
    """
    height, width = frame.shape[:2]
    side = int(min(height, width) * roi_ratio)
    x0 = (width - side) // 2
    y0 = (height - side) // 2
    return frame[y0 : y0 + side, x0 : x0 + side]


def enhance_hand_roi(roi_bgr: np.ndarray) -> np.ndarray:
    """
    Lighting-normalize a hand crop so live webcam and training look alike.

    CLAHE on L channel reduces washout / shadow; light blur reduces webcam noise.
    """
    lab = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2LAB)
    lightness, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    lightness = clahe.apply(lightness)
    enhanced = cv2.cvtColor(cv2.merge([lightness, a, b]), cv2.COLOR_LAB2BGR)
    return cv2.GaussianBlur(enhanced, (3, 3), 0)


def roi_to_tensor(roi_bgr: np.ndarray) -> np.ndarray:
    """Already-cropped BGR ROI → float32 (IMAGE_SIZE, IMAGE_SIZE, 3) RGB in [0, 1]."""
    enhanced = enhance_hand_roi(roi_bgr)
    resized = cv2.resize(enhanced, (IMAGE_SIZE, IMAGE_SIZE), interpolation=cv2.INTER_AREA)
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    return rgb.astype("float32") / 255.0


def prepare_cnn_input(frame_bgr: np.ndarray) -> np.ndarray:
    """Full BGR webcam/OpenCV frame → float32 tensor for the CNN."""
    roi = crop_center_roi(frame_bgr)
    return roi_to_tensor(roi)


def encode_jpeg_base64(image_bgr: np.ndarray, quality: int = 80) -> str:
    ok, buffer = cv2.imencode(".jpg", image_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not ok:
        raise ValueError("Could not encode image as JPEG.")
    return base64.b64encode(buffer).decode("ascii")


def decode_base64_image(data: str) -> np.ndarray:
    """Accept a raw base64 string or a data URL (data:image/jpeg;base64,...)."""
    if "," in data:
        data = data.split(",", 1)[1]
    raw = base64.b64decode(data)
    array = np.frombuffer(raw, dtype=np.uint8)
    frame = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("Could not decode image bytes.")
    return frame


def preview_roi_base64(frame_bgr: np.ndarray) -> str:
    """Show the enhanced crop the CNN actually sees."""
    roi = crop_center_roi(frame_bgr)
    preview = enhance_hand_roi(roi)
    preview = cv2.resize(preview, (160, 160), interpolation=cv2.INTER_AREA)
    return encode_jpeg_base64(preview)
