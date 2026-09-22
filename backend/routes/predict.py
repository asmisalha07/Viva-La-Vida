from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from model.predict import predict_letter
from services.preprocess import decode_base64_image, preview_roi_base64

router = APIRouter(prefix="/predict", tags=["predict"])


class PredictRequest(BaseModel):
    image: str = Field(..., description="Base64-encoded JPEG/PNG from the webcam canvas.")
    mode: str = Field("letters", description="letters (A–Z) or words (HELLO, YES, …)")


@router.post("")
def predict_sign(body: PredictRequest):
    """Detect the hand with MediaPipe and classify using the letters or words model."""
    try:
        frame = decode_base64_image(body.image)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    kind = "words" if (body.mode or "").lower() == "words" else "letters"
    try:
        result = predict_letter(frame, kind=kind)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    result["roi_preview"] = preview_roi_base64(frame)
    return result
