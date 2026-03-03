"""
Offline translation CLI — translate a song once, save to JSON.

Usage:
    python translate_cli.py <song_id>

What it does:
    1. Reads the song's lyrics from the database
    2. Calls the Anthropic API to translate them
    3. Saves the result to translations/<song_id>.json

After this, the web app loads translations instantly from the JSON
file and never calls the API for that song again.

Requires ANTHROPIC_API_KEY in your environment.
"""

import sys

from sqlalchemy.orm import Session

from lyricflow.database import SessionLocal
from lyricflow.models import LyricLine, Song
from lyricflow.services.translation import (
    save_cached_translations,
    translate_song,
)


def main():
    if len(sys.argv) != 2:
        print("Usage: python translate_cli.py <song_id>")
        sys.exit(1)

    song_id = int(sys.argv[1])
    db: Session = SessionLocal()

    try:
        song = db.query(Song).filter(Song.id == song_id).first()
        if not song:
            print(f"Song {song_id} not found in database.")
            sys.exit(1)

        lines = (
            db.query(LyricLine)
            .filter(LyricLine.song_id == song_id)
            .order_by(LyricLine.line_number)
            .all()
        )
        if not lines:
            print(f"Song '{song.title}' has no lyrics yet.")
            sys.exit(1)

        print(f"Translating '{song.title}' ({len(lines)} lines)...")

        original_texts = [line.original_text for line in lines]
        translations = translate_song(original_texts, song.language)

        # Check if the API returned anything useful
        if all(t == "" for t in translations):
            print("Translation failed — check your ANTHROPIC_API_KEY.")
            sys.exit(1)

        # Save to JSON cache
        lines_data = [
            {
                "line_number": line.line_number,
                "original": line.original_text,
                "translation": t,
            }
            for line, t in zip(lines, translations)
        ]
        save_cached_translations(song_id, lines_data)

        # Also persist to database
        for line, t in zip(lines, translations):
            line.translation = t
        db.commit()

        print(f"Saved to translations/{song_id}.json")
        print("\nPreview:")
        for entry in lines_data:
            print(f"  {entry['line_number']}. {entry['original']}")
            print(f"     → {entry['translation']}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
