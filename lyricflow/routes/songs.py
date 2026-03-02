"""
Song routes — CRUD endpoints for the song library.
Each song carries a computed mastery_progress so the UI can show
how much of a song the user has self-marked as learned.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..models import Song, LyricLine

router = APIRouter(prefix="/songs", tags=["songs"])


def calculate_mastery_progress(lines):
    """Mastery = fraction of lines the user self-marked as mastered.
    Returns 0.0 when a song has no lines yet (avoids divide-by-zero)."""
    total = len(lines)
    if total == 0:
        return 0.0
    mastered = sum(1 for line in lines if line.is_mastered)
    return round(mastered / total, 2)


def song_to_dict(song):
    """Convert a Song ORM object to a plain dict with mastery_progress.
    We use a dict instead of a Pydantic model to keep things simple early on."""
    lines = song.lines or []
    mastered = sum(1 for l in lines if l.is_mastered)
    return {
        "id": song.id,
        "title": song.title,
        "artist": song.artist,
        "language": song.language,
        "source_type": song.source_type,
        "source_url": song.source_url,
        "audio_file_path": song.audio_file_path,
        "whisper_status": song.whisper_status,
        "created_at": song.created_at.isoformat() if song.created_at else None,
        "mastery_progress": calculate_mastery_progress(lines),
        "line_count": len(lines),
        "mastered_count": mastered,
    }


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


@router.get("/")
def list_songs(db: Session = Depends(get_db)):
    """Return all songs, newest first, each with a mastery_progress score."""
    songs = (
        db.query(Song)
        .options(selectinload(Song.lines))
        .order_by(Song.created_at.desc())
        .all()
    )
    return [song_to_dict(s) for s in songs]


@router.post("/", status_code=201)
def create_song(body: dict, db: Session = Depends(get_db)):
    """Add a new song to the library.
    source_type defaults to 'mp3' because most users start with local files."""
    title = body.get("title")
    artist = body.get("artist")
    language = body.get("language")
    source_type = body.get("source_type", "mp3")

    if not title or not artist or not language:
        raise HTTPException(status_code=400, detail="title, artist, and language are required")

    # Validate source_type against the allowed values from SPECS.md
    allowed_source_types = ("mp3", "spotify", "youtube")
    if source_type not in allowed_source_types:
        raise HTTPException(
            status_code=400,
            detail=f"source_type must be one of: {', '.join(allowed_source_types)}",
        )

    song = Song(
        title=title,
        artist=artist,
        language=language,
        source_type=source_type,
        audio_file_path=body.get("audio_file_path"),
    )
    db.add(song)
    db.commit()
    db.refresh(song)
    return song_to_dict(song)


@router.get("/{song_id}")
def get_song(song_id: int, db: Session = Depends(get_db)):
    """Return one song with all its lyric lines, ordered by line_number.
    Lines are included so the Checklist screen can render immediately."""
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")

    result = song_to_dict(song)
    # Sort lines by line_number so the UI gets them in lyric order
    sorted_lines = sorted(song.lines, key=lambda l: l.line_number)
    result["lines"] = [line_to_dict(l) for l in sorted_lines]
    return result


@router.delete("/{song_id}")
def delete_song(song_id: int, db: Session = Depends(get_db)):
    """Delete a song and all its lines.
    Cascade is handled by the ORM relationship, but we delete lines
    explicitly as a safety net in case cascade isn't configured."""
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")

    # Delete lines first in case ORM cascade isn't set up yet
    db.query(LyricLine).filter(LyricLine.song_id == song_id).delete()
    db.delete(song)
    db.commit()
    return {"ok": True}
