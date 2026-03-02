# SPECS.md — Source of Truth (Contracts + Decisions)

## A) Naming Conventions (LOCKED)
- Variables: snake_case
- Functions: snake_case
- Classes: PascalCase
- Files: snake_case (enforced)
- Folders: lowercase
- API endpoints: lowercase-with-dashes (e.g., /api/songs/{id}/auto-timestamp)
- Database columns: snake_case
RULE: Do not change unless you follow Change Control in CLAUDE.md.

## B) Data Shapes / Schemas (LOCKED)
| Entity       | Key Fields |
|--------------|-----------|
| Song         | id (int PK), title (str), artist (str), language (str), source_type (str: mp3/spotify/youtube), source_url (str nullable), audio_file_path (str), whisper_status (str), created_at (datetime) |
| LyricLine    | id (int PK), song_id (int FK), line_number (int), original_text (str), translation (str nullable), translation_approved (bool default false), start_time_ms (int nullable), end_time_ms (int nullable), timestamp_source (str nullable), is_mastered (bool default false), loop_count (int default 0) |
| UserSettings | id (int PK), theme (str default "dark") |

RULE: Any schema change requires before/after + impact + tests.

## C) Invariants (LOCKED)
- IDs are integers, auto-incremented.
- Timestamps (start_time_ms, end_time_ms) are integers in milliseconds.
- created_at is ISO 8601 UTC.
- source_type must be one of: "mp3", "spotify", "youtube".
- line_number starts at 1, not 0.
- loop_count only increments, never decrements.
- is_mastered is self-assessed (no automated scoring).
RULE: Add invariants early and treat them like law.

## D) Domain Rules (LOCKED)
- Mastery is self-assessed. No recording, scoring, or grammar quizzes.
- Stacking is optional. No hard gates on line order.
- Translation visible by default. Tap to hide.
- Loop gap is ~1 second between replays.
- Stack buttons unlock progressively as consecutive lines from line 1 are mastered.
- Stacks play continuous song audio (not segmented clips).
- Stacks auto-loop until user stops them.
RULE: Treat like invariants. Do not change without Change Control.

## E) Decisions Log (editable)
- 2026-03-02: Project initialized; Claude OS installed.
- 2026-03-02: Tech stack confirmed from Spec.md v2.0 — FastAPI + Alpine.js + SQLite.
- 2026-03-02: File naming convention set to snake_case.
- 2026-03-02: 9 security/quality fixes applied (path traversal, streaming upload, Whisper errors, Pydantic validation, N+1, bulk approval, CORS env, DB env, tests).
- 2026-03-02: Replaced Whisper auto-timestamp UI with tap-to-sync (manual tap-along + review + re-tap + fine-tune).
