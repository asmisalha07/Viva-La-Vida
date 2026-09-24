"""
Copy one webcam jpg per class into guide-photos/ for Git.

    cd backend
    python model/export_guide_photos.py
"""

from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "dataset"
OUT = ROOT / "guide-photos"
SKIP = {"nothing", "del", "space"}


def newest_jpg(folder: Path) -> Path | None:
    photos = sorted(folder.glob("*.jpg"), key=lambda p: p.stat().st_mtime, reverse=True)
    return photos[0] if photos else None


def export_kind(src: Path, dest: Path) -> int:
    dest.mkdir(parents=True, exist_ok=True)
    copied = 0
    if not src.is_dir():
        return 0
    for folder in sorted(src.iterdir()):
        if not folder.is_dir() or folder.name.lower() in SKIP:
            continue
        photo = newest_jpg(folder)
        if photo is None:
            continue
        target = dest / f"{folder.name}.jpg"
        shutil.copy2(photo, target)
        copied += 1
        print("guide", target.relative_to(ROOT))
    return copied


def main():
    n_letters = export_kind(DATASET / "letters", OUT / "letters")
    n_words = export_kind(DATASET / "signs", OUT / "words")
    print(f"Copied {n_letters} letters and {n_words} words -> {OUT}")
    if n_letters + n_words == 0:
        raise SystemExit("No jpgs found under dataset/letters or dataset/signs.")


if __name__ == "__main__":
    main()

