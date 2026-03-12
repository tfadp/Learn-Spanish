# LyricFlow — Exceptions Log

## Session 8 (2026-03-11)

### Exception 1: Seek-then-play race causes wrong playback position
- **File**: lyricflow/templates/song.html (start_line_loop, start_stack_loop, toggle_pause, toggle_stack_pause)
- **What**: `audio.currentTime = X; audio.play()` could start playback before the seek completed, causing audio to play from the wrong position (especially on iOS Safari)
- **Resolution**: Wait for `seeked` event before calling `play()`. Fast-path when seek lands instantly (buffered audio, readyState >= 1).

### Exception 2: Orphaned seeked listener causes zombie playback
- **File**: lyricflow/templates/song.html (all seeked listeners)
- **What**: If `stop_audio()` was called while a `seeked` listener was pending, the callback would fire later and call `audio.play()` on a closed card
- **Resolution**: Added `_loop_gen` generation counter. Incremented on `stop_audio()`, checked in every `on_seeked` callback. Stale callbacks bail out immediately.

### Exception 3: Premature _loop_state in stack pause resume
- **File**: lyricflow/templates/song.html (toggle_stack_pause)
- **What**: `_loop_state` was set to `'playing'` before the seek completed. The 20ms interval would fire and check `audio.currentTime` at the wrong position, potentially triggering drift guard or end-detection incorrectly.
- **Resolution**: Removed premature `_loop_state = 'playing'`. Now only set inside `on_seeked` after seek confirms position.

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
