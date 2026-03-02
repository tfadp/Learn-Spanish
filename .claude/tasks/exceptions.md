# exceptions.md — Proactive Catches

## Format
- [DATE] | [FILE] | [WHAT WAS CAUGHT] | [RESOLUTION]

## Log
- 2026-03-02 | routes/songs.py, routes/lyrics.py | Absolute imports (`from database`) would fail in package context | Fixed to relative imports (`from ..database`)
- 2026-03-02 | templates/base.html | `x-data="app()"` on container conflicted with page-specific components | Removed — each page defines its own x-data
- 2026-03-02 | routes/songs.py | Library template expected `line_count` and `mastered_count` but API only returned `mastery_progress` | Added both fields to `song_to_dict()`
- 2026-03-02 | static/js/app.js | Audio src double-pathed: upload returns `static/uploads/...` but JS prepended `/static/uploads/` again | Fixed JS to use `/${audio_file_path}`
- 2026-03-02 | models.py | User prompt said UserSettings.theme default="burgundy" but SPECS.md says "dark" | Kept "dark" per SPECS.md (source of truth)
