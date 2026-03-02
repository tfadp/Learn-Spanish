# todo.md — Roadmap

## Session State
- branch: (no git repo yet)
- last_test: 13/13 pytest tests passing (2026-03-02)
- blocked: none
- pending_decisions: none
- server: running on 0.0.0.0:8000 (phone access at 172.17.7.14:8000)

## Completed (Session 1)
- [x] Project structure created (Path B — proper folders)
- [x] Backend: database.py, models.py, main.py
- [x] API routes: songs CRUD, lyrics CRUD, MP3 upload (20MB limit)
- [x] Frontend: base.html, library.html, song.html
- [x] CSS: dark theme, mobile-first, all card states
- [x] JS: Alpine.js components, audio looping engine
- [x] Smoke test: server starts, API returns data
- [x] Song Library page (+ button links to /songs/new)
- [x] Add Song page: Step 1 (info + drag-drop MP3 upload)
- [x] Add Song page: Step 2 (paste lyrics + preview/edit/delete lines)
- [x] CSS for Add Song flow (form inputs, upload zone, preview list)
- [x] Full integration test: upload → create → lyrics → library
- [x] Dynamic language filter tabs (auto-generate from user's songs)

## Completed (Session 2)
- [x] AI Translation service (services/translation.py — Claude API, single-call)
- [x] Translation route (routes/translate.py — POST /songs/{id}/translate)
- [x] Whisper service (services/whisper_service.py — transcribe + fuzzy align)
- [x] Timestamp routes (routes/timestamps.py — auto-timestamp + manual save)
- [x] Add Song Step 3: Translation UI (side-by-side, inline edit, approve all)
- [x] Add Song Step 4: Timestamp UI (confidence badges, segment playback, +/-100ms adjust)
- [x] CSS for Steps 3 & 4 (translation view, timestamp view, confidence badges)
- [x] Installed ffmpeg + rapidfuzz dependencies
- [x] Integration test: translate (12 lines translated) + auto-timestamp (11/12 matched)
- [x] Fixed dual songPage conflict (app.js overriding inline component)
- [x] Checklist + Slide-up Card: Line Mode (single-line audio looping)
- [x] Checklist + Slide-up Card: Stack Mode (continuous multi-line playback)
- [x] Audio engine: 50ms polling, 1s loop gap, fire-and-forget loop count
- [x] Touch swipe-down gesture to dismiss cards (>100px threshold)
- [x] Body scroll lock when card is open
- [x] Loop dots enhancement (10 dots max, then shows number)
- [x] Stack card translation for current line
- [x] CSS: spring-like card transition, touch-action on handle

## Completed (Session 3)
- [x] 9 security & quality fixes:
  - Path traversal sanitization (upload.py)
  - Streaming upload with 20MB limit (upload.py)
  - Whisper error propagation (whisper_service.py + timestamps.py)
  - Pydantic timestamp validation (timestamps.py)
  - N+1 query fix with selectinload (songs.py)
  - Bulk approve-translations endpoint (translate.py + add_song.html)
  - CORS from environment variable (main.py)
  - Database URL from environment variable (database.py)
  - 13 regression tests (tests/test_api.py)
- [x] Tap-to-Sync timestamps (replaced Whisper auto-timestamp in Step 4)
  - Phase 1: Tap along with audio (one tap per line)
  - Phase 2: Review + re-tap individual lines + ±100ms adjust
  - Phase 3: Save (reuses existing PUT endpoint)
- [x] Real NUEVAYoL lyrics: 40 lines inserted, translated, 26 auto-timestamped

## Next 3 Steps
1) Initialize git repo + first commit
2) PWA manifest + service worker
3) Deploy to DigitalOcean

## Backlog
- Improve Whisper accuracy (try "small" model, better fuzzy matching)
