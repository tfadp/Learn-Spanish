# Route for AI-powered lyric translation.
# Fetches a song's lines, sends them to Claude for translation,
# saves results back to the database, and returns updated lines.

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import LyricLine, Song
from ..services.translation import translate_song

router = APIRouter(prefix="/songs", tags=["translate"])


# --- Helper (local copy so we don't couple to lyrics.py) ---
def line_to_dict(line):
    return {
        "id": line.id,
        "song_id": line.song_id,
        "line_number": line.line_number,
        "original_text": line.original_text,
        "translation": line.translation,
        "translation_approved": line.translation_approved,
        "start_time_ms": line.start_time_ms,
        "end_time_ms": line.end_time_ms,
        "timestamp_source": line.timestamp_source,
        "is_mastered": line.is_mastered,
        "loop_count": line.loop_count,
    }


@router.post("/{song_id}/translate")
def translate_song_endpoint(song_id: int, db: Session = Depends(get_db)):
    """
    Translate every lyric line for a song via Claude and persist results.

    Steps:
    1. Look up the song (404 if missing).
    2. Grab its lines, sorted by line_number (400 if none exist).
    3. Send original texts to the translation service.
    4. Save each translation back to the database.
    5. Return the full list of updated line dicts.
    """
    # --- 1. Fetch the song ---
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")

    # --- 2. Fetch lines, sorted so translations stay aligned ---
    lines = (
        db.query(LyricLine)
        .filter(LyricLine.song_id == song_id)
        .order_by(LyricLine.line_number)
        .all()
    )
    if not lines:
        raise HTTPException(status_code=400, detail="No lyrics to translate")

    # --- 3. Translate via Claude ---
    original_texts = [line.original_text for line in lines]
    translations = translate_song(original_texts, song.language)

    # --- 4. Persist translations ---
    for line, translated_text in zip(lines, translations):
        line.translation = translated_text

    db.commit()

    # --- 5. Return updated lines ---
    return [line_to_dict(line) for line in lines]


@router.put("/{song_id}/approve-translations")
def bulk_approve_translations(song_id: int, db: Session = Depends(get_db)):
    """Approve all translations for a song in one transaction.
    Replaces N individual PUT calls from the frontend."""
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")

    updated_count = (
        db.query(LyricLine)
        .filter(LyricLine.song_id == song_id)
        .update({"translation_approved": True})
    )
    db.commit()

    return {"approved": updated_count}
