"""
Download the ASL Alphabet dataset (A–Z) and convert images to MediaPipe landmarks.

    cd backend
    python model/import_asl_letters.py
    python model/train.py --source letters

Uses https://www.kaggle.com/datasets/grassknoted/asl-alphabet via kagglehub.
"""

from __future__ import annotations

from pathlib import Path
import sys

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.landmarks import extract_landmarks  # noqa: E402

DATASET = ROOT.parent / "dataset"
DEST = DATASET / "letters"
MAX_PER_CLASS = 250
SKIP = {"del", "space"}


def find_existing_source() -> Path | None:
    candidates = [
        DATASET / "asl_alphabet" / "asl_alphabet_train",
        DATASET / "asl_alphabet",
    ]
    for base in candidates:
        if (base / "A").is_dir():
            return base
    return None


def download_kaggle() -> Path:
    try:
        import kagglehub
    except ImportError:
        raise SystemExit("Install kagglehub first: pip install kagglehub")

    print("Downloading grassknoted/asl-alphabet (this can take several minutes)...")
    path = Path(kagglehub.dataset_download("grassknoted/asl-alphabet"))
    print("Downloaded to", path)
    for base in (path, path / "asl_alphabet_train", path / "asl_alphabet"):
        if (base / "A").is_dir():
            return base
        nested = list(base.glob("**/asl_alphabet_train/A"))
        if nested:
            return nested[0].parent
        if (base / "A").is_dir():
            return base
    # Common layout: <cache>/asl_alphabet_train/A
    hits = list(path.rglob("A"))
    for hit in hits:
        if hit.is_dir() and (list(hit.glob("*.jpg")) or list(hit.glob("*.png"))):
            return hit.parent
    raise SystemExit(f"Downloaded, but could not find A/ folders under {path}")


def class_label(folder_name: str) -> str | None:
    name = folder_name.strip()
    if name.lower() in SKIP:
        return None
    if name.lower() == "nothing":
        return "nothing"
    if len(name) == 1 and name.isalpha():
        return name.upper()
    return None


def convert_class(src_folder: Path, label: str) -> int:
    dest = DEST / label
    dest.mkdir(parents=True, exist_ok=True)
    existing = len(list(dest.glob("*.npy")))
    if existing >= MAX_PER_CLASS:
        print(f"  {label}: already have {existing} landmarks, skip")
        return existing

    files = sorted(list(src_folder.glob("*.jpg")) + list(src_folder.glob("*.png")))
    saved = existing
    for path in files:
        if saved >= MAX_PER_CLASS:
            break
        image = cv2.imread(str(path))
        if image is None:
            continue
        feats = extract_landmarks(image, static=True)
        if feats is None:
            continue
        np.save(dest / f"{label}_asl_{saved:04d}.npy", feats.astype(np.float32))
        saved += 1
        if saved % 50 == 0:
            print(f"  {label}: {saved}")
    print(f"  {label}: {saved} landmark samples")
    return saved


def main():
    src = find_existing_source()
    if src is None:
        src = download_kaggle()
    print("Source images:", src)
    DEST.mkdir(parents=True, exist_ok=True)

    counts = {}
    for folder in sorted(src.iterdir()):
        if not folder.is_dir():
            continue
        label = class_label(folder.name)
        if not label:
            continue
        counts[label] = convert_class(folder, label)

    missing = [ch for ch in list("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + ["nothing"] if counts.get(ch, 0) < 25]
    print("Done.", counts)
    if missing:
        print("Warning — few/no landmarks for:", ", ".join(missing))
        print("Those Kaggle photos may not show a full hand MediaPipe can detect.")
    print("Next: python model/train.py --source letters")


if __name__ == "__main__":
    main()
