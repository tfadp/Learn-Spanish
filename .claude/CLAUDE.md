# LyricFlow
Learn languages through music — loop lines, master them, stack them into verses.

## Tech Stack
- Backend: Python 3.12 + FastAPI
- Frontend: HTML/CSS + Alpine.js (no build step)
- Database: SQLite via SQLAlchemy
- AI Translation: Anthropic Claude API
- Audio Transcription: OpenAI Whisper (local)
- Audio Playback: HTML5 Audio API
- Hosting: DigitalOcean (nginx + uvicorn)

## Commands
uvicorn lyricflow.main:app --reload   # Run dev server (from project root)
pytest                                # Run tests

## Key Files
Spec.md                          — Product spec v2.0 (source of truth for features)
lyricflow-ux-v2.0.html           — UX visual reference / mockups
lyricflow/main.py                — FastAPI app entry point
lyricflow/database.py            — SQLAlchemy engine + session
lyricflow/models.py              — Song, LyricLine, UserSettings models
lyricflow/routes/songs.py        — Song CRUD endpoints
lyricflow/routes/lyrics.py       — Lyric lines + mastery endpoints
lyricflow/routes/upload.py       — MP3 upload endpoint
lyricflow/static/css/style.css   — Dark theme, mobile-first CSS
lyricflow/static/js/app.js       — Alpine.js components + audio engine
lyricflow/templates/library.html — Song Library screen
lyricflow/templates/song.html    — Checklist + slide-up card screen

## Project Rules
- Check .claude/SPECS.md only when modifying naming, schemas, or contracts.
  Do NOT load SPECS.md at session start.
- Spec.md is the product source of truth. SPECS.md is the code contract source of truth.
- Learning model: Atomize → Loop → Master → Stack → Expand. Do not add modes, quizzes, or scoring.
- The app has exactly 4 screens: Song Library, Checklist, Line Card, Stack Card.

## Change Control
To change anything in SPECS.md sections marked LOCKED:
1. State what you want to change and why.
2. Show before/after.
3. Assess impact on existing code.
4. Get explicit approval.
5. Log the change in SPECS.md Decisions Log.
