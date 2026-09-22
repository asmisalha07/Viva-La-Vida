# Dataset

Word recognition uses **MediaPipe landmarks** (finger joints), not photos of the room.
Train once; the same model should work in another room as long as the hand is visible.

## Collect word signs

```bash
cd backend
python model/collect_samples.py --word HELLO
python model/collect_samples.py --word YES
python model/collect_samples.py --word NO
python model/collect_samples.py --word THANKS
python model/collect_samples.py --word PLEASE
python model/collect_samples.py --word LOVE
python model/collect_samples.py --word BYE
python model/collect_samples.py --word nothing
```

Wait until the window says **hand found**, then press **S**. **Q** quits.

Aim for **60+ samples per word**. Mix:

- slightly different angles and distances
- two lighting conditions if you can (desk lamp vs window)

Then:

```bash
python model/train.py --source words
```

Restart uvicorn. App → **Words** → Start camera → Start prediction.

## Letters (optional)

```bash
python model/collect_samples.py --letters
python model/train.py --source letters
```

Press a–z (or n for nothing) to choose the class, then **S** to save.
