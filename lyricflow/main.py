"""
LyricFlow — FastAPI application entry point.

This wires together: database, routes, templates, and static files.
Run with: uvicorn lyricflow.main:app --reload
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .database import Base, engine
from .routes import songs, lyrics, upload, translate, timestamps

# Resolve paths relative to this file so it works regardless
# of which directory you run uvicorn from.
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create all database tables on startup (if they don't exist yet)."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="LyricFlow",
    description="Learn languages through music",
    lifespan=lifespan,
)

# Read allowed origins from env. Comma-separated in production,
# defaults to "*" for local dev convenience.
_cors_raw = os.environ.get("CORS_ORIGINS", "*")
_cors_origins = [origin.strip() for origin in _cors_raw.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve CSS, JS, and uploaded MP3s
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# --- API routes (all prefixed with /api) ---
app.include_router(songs.router, prefix="/api")
app.include_router(lyrics.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(translate.router, prefix="/api")
app.include_router(timestamps.router, prefix="/api")


# --- Page routes (serve HTML templates) ---

@app.get("/")
async def library_page(request: Request):
    """Song library — the home screen."""
    return templates.TemplateResponse("library.html", {"request": request})


@app.get("/songs/new")
async def add_song_page(request: Request):
    """Multi-step form to add a new song."""
    return templates.TemplateResponse("add_song.html", {"request": request})


@app.get("/song/{song_id}")
async def song_page(request: Request, song_id: int):
    """Individual song view — lyric lines, looping, mastery."""
    return templates.TemplateResponse(
        "song.html", {"request": request, "song_id": song_id}
    )
