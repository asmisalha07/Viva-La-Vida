from fastapi import APIRouter

from model.labels import get_labels
from model.predict import model_is_ready

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    letter_labels = get_labels("letters")
    word_labels = get_labels("words")
    letters_ready = model_is_ready("letters")
    word_ready = model_is_ready("words")
    ready = letters_ready or word_ready
    return {
        "status": "ok",
        "model_loaded": ready,
        "letters_ready": bool(letters_ready),
        "words_ready": bool(word_ready),
        "labels": letter_labels if letters_ready else word_labels,
        "letter_labels": letter_labels,
        "word_labels": word_labels,
        "word_classes": [x for x in word_labels if len(x) > 1 and x.lower() != "nothing"],
        "message": (
            f"Letters {'ready' if letters_ready else 'not trained'} · "
            f"Words {'ready' if word_ready else 'not trained'}."
        ),
    }
