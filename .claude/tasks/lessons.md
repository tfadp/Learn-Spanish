# lessons.md — What We Learned
- Shell escaping with Spanish lyrics (apostrophes) breaks curl JSON. Fix: write JSON to a temp file with Python, then `curl -d @file`.
- In-memory SQLite test databases need `poolclass=StaticPool` — without it, each connection gets a separate empty DB and test seeds are invisible to app routes.
- Capture SQLAlchemy IDs (`song_id = song.id`) before closing the session, otherwise `DetachedInstanceError`.
- FastAPI may return 422 before custom handlers run (e.g., empty filename validation) — test for both expected status codes.
- Whisper auto-timestamp only matched 65% of lines (26/40) for NUEVAYoL. Manual tap-to-sync is faster and more reliable for music with repeated phrases.
- `load_dotenv()` must run in `database.py` (not just main.py) because database.py is imported first and reads env vars at import time.
