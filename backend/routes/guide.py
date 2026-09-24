"""Serve one committed photo per sign from guide-photos/ (not the full dataset)."""

from pathlib import Path
import re

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

ROOT = Path(__file__).resolve().parents[2]
GUIDE = ROOT / "guide-photos"
SAFE = re.compile(r"^[A-Za-z0-9]+$")
SKIP = {"nothing", "del", "space"}

router = APIRouter(prefix="/guide", tags=["guide"])


def _kind_root(kind: str) -> Path:
    if kind == "letters":
        return GUIDE / "letters"
    if kind == "words":
        return GUIDE / "words"
    raise HTTPException(status_code=404, detail="Unknown guide kind.")


def _photo_for(root: Path, label: str) -> Path | None:
    for name in (f"{label}.jpg", f"{label.upper()}.jpg", f"{label.lower()}.jpg"):
        path = root / name
        if path.is_file():
            return path
    return None


def _entries(kind: str) -> list[dict]:
    root = _kind_root(kind)
    if not root.is_dir():
        return []
    items = []
    for photo in sorted(root.glob("*.jpg"), key=lambda p: p.stem.upper()):
        label = photo.stem
        if label.lower() in SKIP or not SAFE.match(label):
            continue
        stamp = int(photo.stat().st_mtime)
        items.append(
            {
                "label": label,
                "count": 1,
                "image": f"/api/guide/image/{kind}/{label}?t={stamp}",
            }
        )
    return items


@router.get("")
def list_guide():
    return {"letters": _entries("letters"), "words": _entries("words")}


@router.get("/image/{kind}/{label}")
def guide_image(kind: str, label: str):
    if kind not in ("letters", "words") or not SAFE.match(label):
        raise HTTPException(status_code=404, detail="Not found.")
    photo = _photo_for(_kind_root(kind), label)
    if photo is None:
        raise HTTPException(status_code=404, detail="No photo for that sign yet.")
    return FileResponse(photo, media_type="image/jpeg")
