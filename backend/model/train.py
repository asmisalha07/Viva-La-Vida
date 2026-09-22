"""
Train a MediaPipe-landmark Random Forest (location-invariant pose, not LSTM).

    cd backend
    python model/train.py --source letters --webcam-only
    python model/train.py --source words
"""

from pathlib import Path
import argparse
import json
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from model.labels import save_labels  # noqa: E402
from services.landmarks import FEATURE_SIZE, RAW_SIZE, enrich_landmarks, jitter  # noqa: E402

DATASET_ROOT = ROOT.parent / "dataset"
MODEL_DIR = Path(__file__).resolve().parent
LETTER_MODEL = MODEL_DIR / "sign_model_letters.joblib"
WORD_MODEL = MODEL_DIR / "sign_model_words.joblib"
HISTORY_PATH = MODEL_DIR / "training_history.json"
SEED = 42
MIN_PER_CLASS = 20
AUGMENT = 8


def list_class_folders(dataset: Path) -> list[str]:
    if not dataset.is_dir():
        return []
    labels = []
    for folder in sorted(dataset.iterdir()):
        if not folder.is_dir() or folder.name.startswith("."):
            continue
        n = len(list(folder.glob("*.npy")))
        if n > 0:
            labels.append(folder.name)
    return labels


def pick_dataset(source: str | None) -> Path:
    words = DATASET_ROOT / "signs"
    letters = DATASET_ROOT / "letters"
    if source == "letters":
        return letters
    if source == "words":
        return words
    if len(list_class_folders(words)) >= 2:
        return words
    return letters


def load_dataset(dataset: Path, labels: list[str], webcam_only: bool = False):
    xs, ys = [], []
    for index, label in enumerate(labels):
        for path in sorted((dataset / label).glob("*.npy")):
            if webcam_only and "_asl_" in path.name:
                continue
            vec = np.load(path).astype(np.float32).flatten()
            if vec.size == RAW_SIZE:
                vec = enrich_landmarks(vec)
            elif vec.size != FEATURE_SIZE:
                continue
            xs.append(vec)
            ys.append(index)
    return np.asarray(xs, dtype=np.float32), np.asarray(ys, dtype=np.int32)


def augment(x, y, rng):
    extra_x, extra_y = [], []
    for vec, lab in zip(x, y):
        for _ in range(AUGMENT):
            extra_x.append(jitter(vec, rng))
            extra_y.append(lab)
    if not extra_x:
        return x, y
    return np.concatenate([x, np.asarray(extra_x, dtype=np.float32)]), np.concatenate(
        [y, np.asarray(extra_y, dtype=np.int32)]
    )


def stratified_split(x, y, test_size=0.2, seed=SEED):
    rng = np.random.default_rng(seed)
    train_idx, val_idx = [], []
    for class_id in np.unique(y):
        idx = np.where(y == class_id)[0]
        rng.shuffle(idx)
        n_val = max(1, int(round(len(idx) * test_size)))
        val_idx.extend(idx[:n_val].tolist())
        train_idx.extend(idx[n_val:].tolist())
    rng.shuffle(train_idx)
    rng.shuffle(val_idx)
    return x[train_idx], x[val_idx], y[train_idx], y[val_idx]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=["words", "letters", "auto"], default="auto")
    parser.add_argument(
        "--webcam-only",
        action="store_true",
        help="Letters: skip leftover *_asl_*.npy files.",
    )
    args = parser.parse_args()
    source = None if args.source == "auto" else args.source

    dataset = pick_dataset(source)
    kind = "letters" if dataset == DATASET_ROOT / "letters" else "words"
    model_path = LETTER_MODEL if kind == "letters" else WORD_MODEL
    webcam_only = args.webcam_only or kind == "letters"
    all_labels = list_class_folders(dataset)

    def npy_count(label: str) -> int:
        paths = list((dataset / label).glob("*.npy"))
        if webcam_only:
            paths = [p for p in paths if "_asl_" not in p.name]
        return len(paths)

    counts = {label: npy_count(label) for label in all_labels}
    print("Dataset:", dataset)
    print("Landmark samples:", counts)
    skipped = [label for label, n in counts.items() if n < MIN_PER_CLASS]
    if skipped:
        print("Skipping low-count classes:", skipped)
    labels = [label for label in all_labels if counts.get(label, 0) >= MIN_PER_CLASS]
    if len(labels) < 2:
        raise SystemExit(
            "Need webcam .npy files in at least 2 class folders.\n"
            "Letters: python model/collect_samples.py --letters\n"
            "Words:   python model/collect_samples.py --word HELLO"
        )

    x, y = load_dataset(dataset, labels, webcam_only=webcam_only)
    print(f"Loaded {len(x)} MediaPipe poses  dim={FEATURE_SIZE}  classes={labels}")

    x_train, x_val, y_train, y_val = stratified_split(x, y)
    rng = np.random.default_rng(SEED)
    x_train, y_train = augment(x_train, y_train, rng)

    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score

    clf = RandomForestClassifier(
        n_estimators=280,
        max_depth=18,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=SEED,
        n_jobs=-1,
    )
    clf.fit(x_train, y_train)
    val_acc = float(accuracy_score(y_val, clf.predict(x_val)))
    train_acc = float(accuracy_score(y_train, clf.predict(x_train)))
    print(f"Random Forest  train_acc={train_acc:.3f}  val_acc={val_acc:.3f}")

    import joblib

    joblib.dump({"type": "rf", "model": clf, "labels": labels, "feat_dim": FEATURE_SIZE}, model_path)
    save_labels(labels, kind=kind)
    HISTORY_PATH.write_text(json.dumps({"val_accuracy": [val_acc], "train_accuracy": [train_acc]}, indent=2))
    print("Saved", kind, "model to", model_path)


if __name__ == "__main__":
    main()
