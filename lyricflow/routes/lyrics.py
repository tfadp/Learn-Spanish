"""
Lyrics routes — endpoints for lyric lines (timestamps, translations, mastery).
Handles bulk creation from Whisper output, inline edits, and the
loop/master actions that drive the core learning loop.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Song, LyricLine

router = APIRouter(prefix="/lyrics", tags=["lyrics"])


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


@router.post("/songs/{song_id}/lines", status_code=201)
def bulk_create_lines(song_id: int, body: dict, db: Session = Depends(get_db)):
    """Create multiple lyric lines at once for a song.
    Bulk create is needed because Whisper transcription produces all lines together."""
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")

    raw_lines = body.get("lines")
    if not raw_lines or not isinstance(raw_lines, list):
        raise HTTPException(status_code=400, detail="'lines' must be a non-empty list")

    created_lines = []
    for entry in raw_lines:
        # line_number starts at 1 per SPECS.md invariant
        line_number = entry.get("line_number")
        original_text = entry.get("original_text")

        if line_number is None or not original_text:
            raise HTTPException(
                status_code=400,
                detail="Each line requires line_number and original_text",
            )

        lyric_line = LyricLine(
            song_id=song_id,
            line_number=line_number,
            original_text=original_text,
            translation=entry.get("translation"),
        )
        db.add(lyric_line)
        created_lines.append(lyric_line)

    db.commit()
    # Refresh all lines so their auto-generated ids are available
    for line in created_lines:
        db.refresh(line)

    return [line_to_dict(l) for l in created_lines]


@router.put("/{line_id}")
def update_line(line_id: int, body: dict, db: Session = Depends(get_db)):
    """Partial update — only change the fields the client sends.
    This powers inline editing on the Checklist and Line Card screens."""
    line = db.query(LyricLine).filter(LyricLine.id == line_id).first()
    if not line:
        raise HTTPException(status_code=404, detail="Lyric line not found")

    # Only allow updating known fields to prevent accidental overwrites
    allowed_fields = {
        "original_text",
        "translation",
        "translation_approved",
        "start_time_ms",
        "end_time_ms",
        "is_mastered",
        "loop_count",
    }

    for field, value in body.items():
        if field in allowed_fields:
            setattr(line, field, value)

    db.commit()
    db.refresh(line)
    return line_to_dict(line)


@router.put("/{line_id}/master")
def toggle_master(line_id: int, db: Session = Depends(get_db)):
    """Toggle the mastered status of a line.
    Mastery is self-assessed (SPECS.md domain rule) — no scoring involved."""
    line = db.query(LyricLine).filter(LyricLine.id == line_id).first()
    if not line:
        raise HTTPException(status_code=404, detail="Lyric line not found")

    line.is_mastered = not line.is_mastered
    db.commit()
    db.refresh(line)
    return line_to_dict(line)


@router.put("/{line_id}/loop")
def increment_loop(line_id: int, db: Session = Depends(get_db)):
    """Increment the loop count by 1.
    Loop count only goes up (SPECS.md invariant) — tracks practice effort."""
    line = db.query(LyricLine).filter(LyricLine.id == line_id).first()
    if not line:
        raise HTTPException(status_code=404, detail="Lyric line not found")

    line.loop_count = (line.loop_count or 0) + 1
    db.commit()
    db.refresh(line)
    return line_to_dict(line)
