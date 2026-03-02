"""
SQLAlchemy models — the Python classes that map to database tables.

Each class = one table. Each attribute = one column.
Relationships let us jump between related records
(e.g., song.lines gives all lyrics for that song).

Schemas match SPECS.md Section B (Data Shapes).
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from .database import Base


class Song(Base):
    __tablename__ = "songs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    artist = Column(String, nullable=False)
    language = Column(String, nullable=False, default="spanish")

    # source_type constrains how we locate the audio
    # (mp3 = local file, spotify/youtube = external link)
    source_type = Column(String, nullable=False, default="mp3")
    source_url = Column(String, nullable=True)
    audio_file_path = Column(String, nullable=True)

    # Tracks Whisper transcription progress so the UI can show a spinner
    whisper_status = Column(String, default="pending")

    # UTC so we never fight timezone bugs
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # cascade="all, delete-orphan" means: if a song is deleted,
    # its lyric lines are automatically deleted too (no orphan rows).
    lines = relationship(
        "LyricLine", back_populates="song", cascade="all, delete-orphan"
    )


class LyricLine(Base):
    __tablename__ = "lyric_lines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    song_id = Column(Integer, ForeignKey("songs.id"), nullable=False)

    # line_number starts at 1 per SPECS.md invariants
    line_number = Column(Integer, nullable=False)
    original_text = Column(String, nullable=False)

    # Translation filled by Claude API; user can approve/edit
    translation = Column(String, nullable=True)
    translation_approved = Column(Boolean, default=False)

    # Timestamps in milliseconds for audio sync
    start_time_ms = Column(Integer, nullable=True)
    end_time_ms = Column(Integer, nullable=True)

    # "whisper" = auto-detected, "manual" = user-adjusted
    timestamp_source = Column(String, nullable=True)

    # Mastery is self-assessed (SPECS.md domain rule: no scoring)
    is_mastered = Column(Boolean, default=False)

    # loop_count only increments, never decrements (SPECS.md invariant)
    loop_count = Column(Integer, default=0)

    song = relationship("Song", back_populates="lines")


class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Default "dark" per SPECS.md Section B
    theme = Column(String, default="dark")
