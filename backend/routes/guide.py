"""Serve one webcam crop per collected letter or word for the in-app sign guide."""

from pathlib import Path
import re

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

DATASET = Path(__file__).resolve().parents[2] / "dataset"
SAFE = re.compile(r"^[A-Za-z0-9]+$")

router = APIRouter(prefix="/guide", tags=["guide"])


def _kind_root(kind: str) -> Path:
    if kind == "letters":
        return DATASET / "letters"
    if kind == "words":
        return DATASET / "signs"
    raise HTTPException(status_code=404, detail="Unknown guide kind.")


def _pick_jpg(folder: Path) -> Path | None:
    photos = sorted(folder.glob("*.jpg"), key=lambda p: p.stat().st_mtime, reverse=True)
    return photos[0] if photos else None


def _entries(kind: str) -> list[dict]:
    root = _kind_root(kind)
    if not root.is_dir():
        return []
    items = []
    for folder in sorted(root.iterdir(), key=lambda p: p.name.upper()):
        if not folder.is_dir() or folder.name.startswith("."):
            continue
        if folder.name.lower() in ("nothing", "del", "space"):
            continue
        if not SAFE.match(folder.name):
            continue
        if not list(folder.glob("*.npy")):
            continue
        photo = _pick_jpg(folder)
        if photo is None:
            continue
        stamp = int(photo.stat().st_mtime)
        items.append(
            {
                "label": folder.name,
                "count": len(list(folder.glob("*.npy"))),
                "image": f"/api/guide/image/{kind}/{folder.name}?t={stamp}",
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
    folder = _kind_root(kind) / label
    if not folder.is_dir():
        # Words are stored in uppercase folders.
        alt = _kind_root(kind) / label.upper()
        folder = alt if alt.is_dir() else folder
    photo = _pick_jpg(folder) if folder.is_dir() else None
    if photo is None:
        raise HTTPException(status_code=404, detail="No photo for that sign yet.")
    return FileResponse(photo, media_type="image/jpeg")
