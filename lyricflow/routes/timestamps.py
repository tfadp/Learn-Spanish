"""
Timestamp routes — auto-generate timestamps via Whisper or accept manual edits.

Two endpoints:
- POST /{song_id}/auto-timestamp  → run Whisper + fuzzy alignment
- PUT  /{song_id}/timestamps      → save user-corrected timestamps
"""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Song, LyricLine
from ..services.whisper_service import (
    transcribe_audio,
    align_lyrics,
    WhisperTranscriptionError,
)

router = APIRouter(prefix="/songs", tags=["timestamps"])


# ── Pydantic models for request validation ─────────────────

class TimestampEntry(BaseModel):
    """One line's timestamp correction from the user."""
    line_id: int
    start_time_ms: int
    end_time_ms: int

    @field_validator("start_time_ms", "end_time_ms")
    @classmethod
    def must_be_non_negative(cls, v):
        if v < 0:
            raise ValueError("Timestamps must be non-negative")
        return v

    @field_validator("end_time_ms")
    @classmethod
    def end_after_start(cls, v, info):
        start = info.data.get("start_time_ms")
        if start is not None and v <= start:
            raise ValueError("end_time_ms must be greater than start_time_ms")
        return v


class TimestampUpdateRequest(BaseModel):
    """Request body for PUT /songs/{song_id}/timestamps."""
    timestamps: list[TimestampEntry]


def line_to_dict(line):
    """Convert a LyricLine ORM object to a plain dict."""
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


# ── POST /{song_id}/auto-timestamp ────────────────────────────

@router.post("/{song_id}/auto-timestamp")
def auto_timestamp(song_id: int, db: Session = Depends(get_db)):
    """Run Whisper on the song's audio file, then fuzzy-match
    the transcription to the stored lyric lines.

    Updates each LyricLine's start/end times in the database
    when the match confidence is high or low (not unmatched).
    """
    # ── Validate song exists ──────────────────────────────
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")

    # ── Validate lyrics exist ─────────────────────────────
    lines = (
        db.query(LyricLine)
        .filter(LyricLine.song_id == song_id)
        .order_by(LyricLine.line_number)
        .all()
    )
    if not lines:
        raise HTTPException(
            status_code=400, detail="No lyrics to timestamp"
        )

    # ── Mark as processing so the UI can show a spinner ───
    song.whisper_status = "processing"
    db.commit()

    try:
        # ── Resolve audio path ────────────────────────────
        # audio_file_path in DB: "static/uploads/abc123_song.mp3"
        # Actual file lives at:  lyricflow/static/uploads/abc123_song.mp3
        # __file__ is lyricflow/routes/timestamps.py
        # .parent.parent gets us to lyricflow/
        base_dir = Path(__file__).resolve().parent.parent
        audio_path = base_dir / song.audio_file_path

        # ── Transcribe ────────────────────────────────────
        whisper_result = transcribe_audio(str(audio_path), song.language)

        # ── Align lyrics to transcription ─────────────────
        line_texts = [line.original_text for line in lines]
        alignment = align_lyrics(line_texts, whisper_result)

        # ── Update DB with aligned timestamps ─────────────
        # Build a lookup so we can match alignment entries to ORM objects
        line_by_number = {line.line_number: line for line in lines}
        matched_count = 0

        for entry in alignment:
            line_obj = line_by_number.get(entry["line_number"])
            if not line_obj:
                continue

            if entry["confidence"] != "unmatched":
                line_obj.start_time_ms = entry["start_time_ms"]
                line_obj.end_time_ms = entry["end_time_ms"]
                line_obj.timestamp_source = "whisper"
                matched_count += 1

        song.whisper_status = "done"
        db.commit()

        return {
            "status": "done",
            "alignment": alignment,
            "matched": matched_count,
            "total": len(lines),
        }

    except WhisperTranscriptionError as exc:
        song.whisper_status = "failed"
        db.commit()
        raise HTTPException(
            status_code=500,
            detail=f"Whisper transcription error: {str(exc)}",
        )
    except Exception as exc:
        song.whisper_status = "failed"
        db.commit()
        raise HTTPException(
            status_code=500,
            detail=f"Whisper processing failed: {str(exc)}",
        )


# ── PUT /{song_id}/timestamps ─────────────────────────────────

@router.put("/{song_id}/timestamps")
def update_timestamps(
    song_id: int,
    body: TimestampUpdateRequest,
    db: Session = Depends(get_db),
):
    """Accept manually-corrected timestamps from the user.
    Pydantic validates types, non-negative values, and end > start."""
    # ── Validate song exists ──────────────────────────────
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")

    # Build a lookup of this song's lines by ID for fast access
    lines = (
        db.query(LyricLine)
        .filter(LyricLine.song_id == song_id)
        .all()
    )
    line_by_id = {line.id: line for line in lines}

    updated_lines = []
    for entry in body.timestamps:
        line_obj = line_by_id.get(entry.line_id)
        if not line_obj:
            continue

        line_obj.start_time_ms = entry.start_time_ms
        line_obj.end_time_ms = entry.end_time_ms
        line_obj.timestamp_source = "manual"
        updated_lines.append(line_obj)

    db.commit()

    return [line_to_dict(line) for line in updated_lines]
