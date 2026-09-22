"""
Capture MediaPipe hand landmarks for word (or letter) classes.

    cd backend
    python model/collect_samples.py --word HELLO
    python model/collect_samples.py --word YES
    python model/collect_samples.py --letters

Press S to save the current pose (needs a visible hand). Q quits.

Collect 60+ samples per class, in more than one room / lighting if you can.
The model stores joint positions only — not the background.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import sys
import time

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from model.labels import LETTER_LABELS, SENTENCE_WORDS, WORD_LABELS  # noqa: E402
from services.landmarks import extract_landmarks  # noqa: E402
from services.preprocess import crop_center_roi  # noqa: E402

DATASET_ROOT = ROOT.parent / "dataset"


def draw_guide(frame, hint: str, found: bool):
    height, width = frame.shape[:2]
    side = int(min(height, width) * 0.55)
    x0 = (width - side) // 2
    y0 = (height - side) // 2
    color = (40, 200, 120) if found else (40, 40, 200)
    cv2.rectangle(frame, (x0, y0), (x0 + side, y0 + side), color, 2)
    cv2.putText(
        frame,
        hint,
        (16, 32),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.62,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    status = "hand found — S to save" if found else "no hand — move into the box"
    cv2.putText(
        frame,
        status,
        (16, height - 24),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        color,
        2,
        cv2.LINE_AA,
    )
    return frame


def save_sample(folder: Path, label: str, features: np.ndarray, frame):
    folder.mkdir(parents=True, exist_ok=True)
    stamp = int(time.time() * 1000)
    np.save(folder / f"{label}_{stamp}.npy", features.astype(np.float32))
    roi = crop_center_roi(frame)
    cv2.imwrite(str(folder / f"{label}_{stamp}.jpg"), roi)
    print("saved", f"{label}_{stamp}.npy")


def run_camera(on_save, hint: str):
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        raise SystemExit("Could not open webcam. Check that no other app is using it.")

    while True:
        ok, frame = camera.read()
        if not ok:
            break
        frame = cv2.flip(frame, 1)
        features = extract_landmarks(frame, static=False)
        display = draw_guide(frame.copy(), hint, features is not None)
        cv2.imshow("Sign collector (landmarks)", display)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        if key in (ord("s"), ord("S")):
            if features is None:
                print("No hand detected — hold the sign in the box.")
            else:
                on_save(features, frame)

    camera.release()
    cv2.destroyAllWindows()


def collect_word(word: str):
    label = word.strip().upper().replace(" ", "")
    if label == "NOTHING":
        label = "nothing"
    folder = DATASET_ROOT / "signs" / label
    print("Collecting", label, "→", folder)
    print("Press S when the pose is right. Aim for 60+ saves, mixed lighting.")

    def on_save(features, frame):
        save_sample(folder, label, features, frame)

    run_camera(on_save, f"{label}  |  S save  |  Q quit")


def collect_sentence_words(burst: int = 40):
    """Walk the sentence dictionary; Space auto-saves, N next word, Esc quit."""
    print("Sentence words:", ", ".join(SENTENCE_WORDS))
    print("Examples:  WHAT IS YOUR NAME   ·   HOW ARE YOU   ·   MY NAME IS")
    print("Hold each sign, press SPACE for", burst, "saves. N = next word. Esc = quit.")
    print("Then: python model/train.py --source words")

    idx = {"i": 0, "left": 0, "skip": 0}
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        raise SystemExit("Could not open webcam.")
    while True:
        label = SENTENCE_WORDS[idx["i"]]
        folder = DATASET_ROOT / "signs" / label
        have = len(list(folder.glob("*.npy"))) if folder.is_dir() else 0
        ok, frame = camera.read()
        if not ok:
            break
        frame = cv2.flip(frame, 1)
        features = extract_landmarks(frame, static=False)
        display = draw_guide(
            frame.copy(),
            f"{idx['i'] + 1}/{len(SENTENCE_WORDS)}  SPACE save  |  N next  |  Esc quit",
            features is not None,
        )
        cv2.putText(
            display,
            label,
            (24, 92),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.8,
            (40, 220, 180),
            4,
            cv2.LINE_AA,
        )
        cv2.putText(
            display,
            f"samples saved: {have}",
            (24, 128),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        cv2.imshow("Sign collector (landmarks)", display)
        key = cv2.waitKey(1) & 0xFF
        if key == 27:
            break
        if key in (ord("n"), ord("N")):
            idx["i"] = (idx["i"] + 1) % len(SENTENCE_WORDS)
            idx["left"] = 0
            print("next →", SENTENCE_WORDS[idx["i"]])
        if key == 32:
            idx["left"] = burst
            idx["skip"] = 0
            print("burst", burst, "for", label)
        if idx["left"] > 0:
            idx["skip"] += 1
            if idx["skip"] % 3 == 0:
                if features is None:
                    print("No hand — keep it in the box.")
                else:
                    save_sample(folder, label, features, frame)
                    idx["left"] -= 1
                    if idx["left"] == 0:
                        nxt = SENTENCE_WORDS[(idx["i"] + 1) % len(SENTENCE_WORDS)]
                        print("done", label, "— press N for", nxt)
    camera.release()
    cv2.destroyAllWindows()


def collect_letters(burst: int = 0):
    dataset = DATASET_ROOT / "letters"
    dataset.mkdir(parents=True, exist_ok=True)
    for name in LETTER_LABELS:
        (dataset / name).mkdir(exist_ok=True)

    key_map = {ord(ch.lower()): ch for ch in LETTER_LABELS if len(ch) == 1}
    key_map[ord("0")] = "nothing"
    pending = {"label": None, "left": 0, "skip": 0}
    print("Letters →", dataset)
    print("1) Press A–Z to pick the letter, or 0 (zero) for nothing / rest pose")
    print("2) Hold the pose, press SPACE to auto-save", burst or 40, "webcam samples")
    print("3) Repeat for all 26. Then: python model/train.py --source letters --webcam-only")
    print("Esc quits (Q is the letter Q). 0 is nothing.")

    target = burst if burst > 0 else 40
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        raise SystemExit("Could not open webcam.")
    while True:
        ok, frame = camera.read()
        if not ok:
            break
        frame = cv2.flip(frame, 1)
        features = extract_landmarks(frame, static=False)
        label = pending["label"] or "?"
        extra = f"  saving {pending['left']}" if pending["left"] else "  SPACE burst"
        display = draw_guide(
            frame.copy(),
            f"class {label}{extra}  |  a-z or 0=nothing  |  Esc quit",
            features is not None,
        )
        cv2.imshow("Sign collector (landmarks)", display)
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # Esc — Q is a letter class
            break
        if key in key_map:
            pending["label"] = key_map[key]
            pending["left"] = 0
            print("class →", pending["label"], " — hold pose, press SPACE")
        if key == 32:  # space starts a burst
            if not pending["label"]:
                print("Press a letter key first.")
            else:
                pending["left"] = target
                pending["skip"] = 0
                print("burst", target, "for", pending["label"])
        if pending["left"] > 0:
            pending["skip"] += 1
            if pending["skip"] % 3 == 0:
                if features is None:
                    print("No hand — keep it in the box.")
                else:
                    save_sample(dataset / pending["label"], pending["label"], features, frame)
                    pending["left"] -= 1
                    if pending["left"] == 0:
                        print("done", pending["label"], "— next letter")
    camera.release()
    cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(description="Collect landmark samples.")
    parser.add_argument("--word", help="Word class (HELLO, YES, WHAT, ...)")
    parser.add_argument("--letters", action="store_true")
    parser.add_argument(
        "--sentences",
        action="store_true",
        help="Collect the sentence dictionary (WHAT IS YOUR NAME, HOW ARE YOU, …)",
    )
    parser.add_argument("--burst", type=int, default=40, help="Auto-saves per letter/word after SPACE")
    args = parser.parse_args()

    if args.letters:
        collect_letters(burst=args.burst)
        return
    if args.sentences:
        collect_sentence_words(burst=args.burst)
        return
    if args.word:
        collect_word(args.word)
        return

    print("Word / sentence classes:", ", ".join(SENTENCE_WORDS))
    print("  python model/collect_samples.py --sentences")
    print("  python model/collect_samples.py --word HELLO")
    print("  python model/collect_samples.py --letters")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
