"""
Copy a Kaggle ASL Alphabet download into dataset/letters/ for letter training.

Expected layouts (either works):

    dataset/asl_alphabet/A/*.jpg
    dataset/asl_alphabet/asl_alphabet_train/A/*.jpg

    cd backend
    python model/import_kaggle_asl.py
"""

from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT.parent / "dataset"
SRC_CANDIDATES = [
    DATASET / "asl_alphabet" / "asl_alphabet_train",
    DATASET / "asl_alphabet",
]
DEST = DATASET / "letters"
MAX_PER_CLASS = 250
SKIP = {"del"}


def find_source() -> Path:
    for base in SRC_CANDIDATES:
        if not base.is_dir():
            continue
        sample = base / "A"
        if sample.is_dir() and (list(sample.glob("*.jpg")) or list(sample.glob("*.png"))):
            return base
    raise SystemExit(
        "Could not find Kaggle folders like dataset/asl_alphabet/A/.\n"
        "Unzip the ASL Alphabet dataset into dataset/asl_alphabet/"
    )


def main():
    src = find_source()
    print("Importing from", src)
    copied = 0
    for folder in sorted(src.iterdir()):
        if not folder.is_dir():
            continue
        name = folder.name
        if name in SKIP:
            continue
        label = "nothing" if name.lower() == "nothing" else name.upper()
        if name.lower() == "space":
            label = "nothing"
        dest = DEST / label
        dest.mkdir(parents=True, exist_ok=True)
        files = sorted(list(folder.glob("*.jpg")) + list(folder.glob("*.png")))[:MAX_PER_CLASS]
        for i, path in enumerate(files):
            shutil.copy2(path, dest / f"{label}_kaggle_{i:04d}{path.suffix.lower()}")
        print(f"  {label}: {len(files)}")
        copied += len(files)
    print(f"Copied {copied} images → {DEST}")
    print("Train with: python model/train.py --source letters")


if __name__ == "__main__":
    sys.exit(main() or 0)
