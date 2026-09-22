# AI-Powered Sign Language Converter

Web app that reads **ASL hand signs** from a webcam, turns them into text, and speaks the result.

Final review: train on **word signs** (one gesture → spoken word) and optionally **A–Z**. The live app predicts the class and speaks it.

## Quick start

**Python:** TensorFlow needs **3.10–3.12** (not 3.14). If `python --version` shows 3.14, install [Python 3.12](https://www.python.org/downloads/) and create the venv with `py -3.12 -m venv .venv`.

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Collect + train (word signs — final review)

```bash
cd backend
python model/collect_samples.py --word HELLO
python model/collect_samples.py --word YES
# …repeat for NO THANKS PLEASE LOVE BYE nothing
python model/train.py --source words
```

Collect **60+ landmark samples per class** (S to save when “hand found”). Mix lighting if possible. Then restart uvicorn and use **Words** mode.

Letters / Kaggle ASL alphabet: see [dataset/README.md](dataset/README.md).

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL, allow the camera, keep the hand inside the guide box.

## Layout

```
frontend/     React (Vite) + Tailwind + Axios + SpeechSynthesis
backend/      FastAPI + OpenCV + Keras CNN
dataset/      HELLO-subset images you capture
docs/         Architecture, Monday demo script, talking points
```

## API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | API + whether `sign_model.keras` exists |
| POST | `/predict` | `{ "image": "<base64>" }` → letter, confidence, ROI preview |

## Docs

| File | Use |
| --- | --- |
| [docs/MONDAY_DEMO.md](docs/MONDAY_DEMO.md) | Install from scratch (venv, train, run) + demo checklist |
| [docs/PRESENTATION_TALKING_POINTS.md](docs/PRESENTATION_TALKING_POINTS.md) | PPT slide titles + bullets |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Pipeline diagram / why CNN |

UI default: **Words** (one sign → that word + speech). **Letters** mode is for A–Z spelling.
