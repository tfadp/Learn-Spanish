# LyricFlow — Exceptions Log

## Session 7 (2026-03-03)

### Exception 1: Potential null crash in timing save callback
- **File**: lyricflow/templates/song.html (adjust_time method)
- **What**: setTimeout callback referenced `this.current_line` which could be null if card closed during the 500ms debounce window
- **Resolution**: Captured `const line_to_save = this.current_line` before setTimeout; added null guard inside callback; added flush-on-close in close_card()

### Exception 2: Corrupt JSON cache crashes translate endpoint
- **File**: lyricflow/services/translation.py (load_cached_translations)
- **What**: `json.load()` on a corrupt/truncated cache file would raise JSONDecodeError, crashing the translation endpoint with a 500 error
- **Resolution**: Wrapped in try/except (json.JSONDecodeError, OSError), returns None on failure so the API call path is used instead

### Exception 3: Stale cache serves wrong translations after lyric edits
- **File**: lyricflow/routes/translate.py (translate_song_endpoint)
- **What**: Cache only checked line count, not content. Editing a lyric line without changing the total count would serve stale translations
- **Resolution**: Added per-line validation: cache is valid only when every cached row's line_number AND original text match current DB lyrics

No unresolved exceptions remaining.
