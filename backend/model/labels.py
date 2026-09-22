# Class names saved next to each trained model (letters vs words).

from __future__ import annotations

import json
from pathlib import Path

MODEL_DIR = Path(__file__).resolve().parent
LABELS_PATH = MODEL_DIR / "labels.json"
LETTER_LABELS_PATH = MODEL_DIR / "labels_letters.json"
WORD_LABELS_PATH = MODEL_DIR / "labels_words.json"

MONDAY_LABELS = ["E", "H", "L", "O", "nothing"]
# Isolated signs that glue into short English sentences after TTS.
SENTENCE_WORDS = [
    "HELLO",
    "I",
    "MY",
    "NAME",
    "IS",
    "WHAT",
    "YOUR",
    "HOW",
    "ARE",
    "YOU",
    "GOOD",
    "YES",
    "NO",
    "THANKS",
    "PLEASE",
    "BYE",
    "HELP",
    "WHERE",
    "WANT",
    "SORRY",
]
WORD_LABELS = SENTENCE_WORDS + ["nothing"]
LETTER_LABELS = [chr(c) for c in range(ord("A"), ord("Z") + 1)] + ["nothing"]


def _read(path: Path) -> list[str]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    labels = data.get("labels") if isinstance(data, dict) else data
    if isinstance(labels, list) and labels:
        return [str(x) for x in labels]
    return []


def labels_kind(labels: list[str]) -> str | None:
    """Classify a label list as letters (A–Z) or dictionary words."""
    real = [x for x in labels if str(x).lower() not in ("nothing", "space")]
    if not real:
        return None
    if any(len(str(x)) > 1 for x in real):
        return "words"
    if sum(1 for x in real if len(str(x)) == 1) >= 2:
        return "letters"
    return None


def generic_saved_kind() -> str | None:
    return labels_kind(_read(LABELS_PATH))


def get_labels(kind: str = "auto") -> list[str]:
    if kind == "letters":
        return _read(LETTER_LABELS_PATH) or (
            _read(LABELS_PATH) if generic_saved_kind() == "letters" else []
        ) or list(LETTER_LABELS)
    if kind == "words":
        return _read(WORD_LABELS_PATH) or (
            _read(LABELS_PATH) if generic_saved_kind() == "words" else []
        ) or list(WORD_LABELS)
    return _read(LABELS_PATH) or list(MONDAY_LABELS)


def save_labels(labels: list[str], kind: str = "auto") -> None:
    payload = json.dumps({"labels": labels}, indent=2)
    if kind == "letters":
        LETTER_LABELS_PATH.write_text(payload, encoding="utf-8")
        return
    if kind == "words":
        WORD_LABELS_PATH.write_text(payload, encoding="utf-8")
        return
    LABELS_PATH.write_text(payload, encoding="utf-8")


LABELS = get_labels()
