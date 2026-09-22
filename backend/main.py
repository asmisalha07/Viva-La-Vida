"""
Sign Language Converter API.

Run from this folder:
    uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.guide import router as guide_router
from routes.health import router as health_router
from routes.predict import router as predict_router

app = FastAPI(
    title="AI-Powered Sign Language Converter",
    description="Accepts webcam frames, preprocesses them with OpenCV, and classifies ASL letters with a CNN.",
    version="0.1.0",
)

# Browser app (Vite) calls this API from another origin during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(predict_router)
app.include_router(guide_router)
