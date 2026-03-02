# LyricFlow — Product Specification v2.0

**Learn Languages Through Music**
**February 2026 · CONFIDENTIAL**

---

## What Changed from v1.x

Everything about the learning experience was rebuilt around one insight: **you don't learn a song. You stack Lego bricks.**

The old spec had Study Mode, Flow Mode, configurable pauses, countdown timers, three-button card layouts, segment views as separate screens. All gone.

Replaced by: **Atomize → Loop → Master → Stack → Expand.**

The backend (FastAPI, SQLite, Whisper, Claude API) barely changes. The frontend is dramatically simpler.

---

## 1. Learning Model

### The Core Loop

1. **Atomize:** A song is broken into individual lines. Each line is one brick.
2. **Loop:** Tap a line. The card slides up. Audio plays that line, pauses ~1 second, plays again. Loops forever until you act.
3. **Master:** When you can say it without looking, tap "✓ Mastered." Card slides down. Checkmark appears.
4. **Stack:** As you master lines, stack buttons appear: "Play 1–2", "Play 1–3", etc. Tap one and the continuous song audio loops through those lines.
5. **Expand:** Keep mastering lines. Stack grows. Eventually you own the whole song.

### Why This Works

Memory hates big jumps. It loves incremental expansion. If you can sing one line comfortably, adding one more feels 30% harder, not 100% harder. This is how musicians learn. How actors learn scripts. How athletes learn plays.

### Design Rules

- No recording. No scoring. No grammar quizzes.
- Mastery is self-assessed. You tap "Mastered" when you're ready.
- Stacking is optional. You can start any line anytime. No hard gates.
- Translation is visible by default. Tap to hide when you're going from memory.
- The loop gap is ~1 second — tight and rhythmic, not a drill.
- Stacks play continuous song audio (lines flow as recorded, not segmented).
- Stacks auto-loop until you stop them.

---

## 2. Screens

The entire app is four screens.

### Screen 1: Song Library (Home)

Shows all songs with progress bars. Tap a song to enter its checklist. Tap "+" to add a new song.

- Song cards: title, artist, language, line count, progress bar (% mastered)
- Language filter tabs: All, Spanish, Portuguese, etc.
- Empty state: "No songs yet. Tap + to start learning."

### Screen 2: Checklist (Main Learning Screen)

This is where you spend 90% of your time. It shows every line of the song as a checklist.

- **Header:** Song title, back arrow to library, "X/Y ✓" mastery count
- **Line list:** Each line shows a number (or checkmark if mastered) and the original text
  - Mastered lines: green checkmark, slightly dimmed text
  - Current/active line: burgundy number, highlighted background
  - Unstarted lines: gray number, dimmed text
- **Tap a line:** Card slides up from the bottom. Audio starts looping.
- **Stack section** (below the line list):
  - Label: "Stack & Play"
  - Progressive buttons appear as you master lines:
    - After mastering lines 1 and 2: "▶ Play 1–2" appears
    - After mastering line 3: "▶ Play 1–3" appears
    - And so on
  - Stack buttons that include unmastered lines show as locked/dimmed (e.g., "Play 1–5" is locked if line 5 isn't mastered)
  - Tapping an available stack button opens the card in Stack Mode

### Screen 3: Slide-Up Card — Line Mode

The practice card. Slides up from the bottom like Spotify's "now playing." Checklist is still visible behind it (dimmed). Swipe down to dismiss.

- **Handle bar** at top (swipe down affordance)
- **Header:** Song title (small, dimmed), loop counter ("🔁 Loop 6")
- **Card body (centered):**
  - Line number label: "LINE 5" in tiny uppercase
  - Target language text: 28px, bold, white, centered
  - English translation: 14px, 50% opacity. **Tap to toggle visibility.** When hidden, shows as a blurred/blanked bar.
- **Loop indicator:** Small dots showing loop count (visual progress)
- **Buttons:**
  - "✓ Mastered" — primary button, white background, burgundy text. Tapping it: brief green flash, card slides down, checkmark appears on checklist.
  - "⏸ Pause" — secondary button, subtle. Pauses the loop. Becomes "▶ Resume" when paused.
- **Audio behavior:** HTML5 Audio plays the line's segment (start_time_ms to end_time_ms), waits ~1 second, seeks back to start_time_ms, plays again. Loops indefinitely.

### Screen 4: Slide-Up Card — Stack Mode

Same slide-up pattern but for playing multiple lines in sequence.

- **Header:** "Stack: Lines 1–4", loop counter
- **Card body:** Shows all lines in the stack as a scrolling text view:
  - Past lines: small, dimmed
  - Current line: large (22px), bold, white
  - Upcoming lines: small, dimmed, below
  - Translation for current line shown below (tap to toggle)
- **Audio behavior:** Plays continuous song audio from line 1's start_time_ms through line N's end_time_ms. When it reaches the end, loops back to line 1's start. Auto-loops until stopped.
- **Buttons:** Just "⏸ Pause Stack" (no Mastered button — stacking is practice, not assessment)
- Swipe down to dismiss and return to checklist.

---

## 3. Add Song Flow

Unchanged from v1.2. Four steps:

1. **Audio Source:** Upload MP3, paste Spotify URL, or YouTube URL (Phase 2). Select language.
2. **Paste Lyrics:** Paste full lyrics. Auto-split by line. Edit/reorder/delete.
3. **AI Translation:** Claude API translates the full song as a JSON mapping. User reviews and edits side-by-side. Tap any translation to edit. "Approve All" to confirm.
4. **Auto-Timestamp:** Whisper transcribes the MP3 with word timestamps. Fuzzy matching aligns transcript to lyrics. User reviews suggested timestamps, adjusts if needed. Manual tap-to-mark as fallback.

---

## 4. Data Model

| Entity | Key Fields | Notes |
|--------|-----------|-------|
| Song | id, title, artist, language, source_type, source_url, audio_file_path, whisper_status, created_at | source_type: mp3, spotify, youtube |
| LyricLine | id, song_id, line_number, original_text, translation, translation_approved, start_time_ms, end_time_ms, timestamp_source, is_mastered, loop_count | is_mastered replaces is_learned. loop_count tracks total loops. |
| UserSettings | id, theme | Simplified — no mode or pause settings needed |

---

## 5. Technical Architecture

### Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Frontend | HTML/CSS + Alpine.js | Reactive state, CSS transitions for slide-up card, no build step |
| Backend | Python + FastAPI | REST API, async endpoints |
| Database | SQLite via SQLAlchemy | Single file, zero config |
| AI Translation | Anthropic Claude API | Full-song JSON translation |
| Audio Transcription | OpenAI Whisper (local) | Auto-timestamp generation |
| Audio (MP3) | HTML5 Audio API | currentTime seeking, looping logic |
| Audio (Spotify) | Spotify Web Playback SDK | OAuth, seek, Premium required |
| Hosting | DigitalOcean Droplet | nginx + uvicorn, GitHub deploys |

### API Endpoints

| Method | Endpoint | Description |
|--------|---------|-------------|
| GET | /api/songs | List all songs with mastery progress |
| POST | /api/songs | Create a new song |
| GET | /api/songs/{id} | Song with all lyric lines |
| DELETE | /api/songs/{id} | Delete song and lines |
| POST | /api/songs/{id}/lyrics | Bulk create lyric lines |
| POST | /api/songs/{id}/translate | AI translation (full song, JSON response) |
| POST | /api/songs/{id}/auto-timestamp | Whisper + fuzzy alignment |
| PUT | /api/lyrics/{line_id} | Edit line or translation |
| PUT | /api/songs/{id}/timestamps | Save/adjust timestamps |
| PUT | /api/lyrics/{line_id}/master | Toggle mastered status |
| PUT | /api/lyrics/{line_id}/loop | Increment loop count |
| POST | /api/upload/mp3 | Upload MP3 file |

### Audio Looping Logic (Line Mode)

```
function loopLine(audio, line) {
  audio.currentTime = line.start_time_ms / 1000
  audio.play()

  // Poll every 50ms
  const interval = setInterval(() => {
    if (audio.currentTime >= line.end_time_ms / 1000) {
      audio.pause()
      // ~1 second gap
      setTimeout(() => {
        audio.currentTime = line.start_time_ms / 1000
        audio.play()
        loopCount++
      }, 1000)
    }
  }, 50)
}
```

### Audio Stacking Logic (Stack Mode)

```
function playStack(audio, lines) {
  const stackStart = lines[0].start_time_ms / 1000
  const stackEnd = lines[lines.length - 1].end_time_ms / 1000

  audio.currentTime = stackStart
  audio.play()

  // Poll to detect end of stack
  const interval = setInterval(() => {
    // Update current line highlight based on audio position
    updateCurrentLine(audio.currentTime * 1000, lines)

    if (audio.currentTime >= stackEnd) {
      // Loop: seek back to start of stack
      audio.currentTime = stackStart
      stackLoopCount++
    }
  }, 50)
}
```

---

## 6. Risks

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Whisper accuracy on music with instrumentation | High | Fallback to manual timestamps |
| Loop gap timing feels unnatural | Medium | Make gap configurable (0.5s, 1s, 1.5s) via a hidden setting |
| Users master lines too quickly (not actually learning) | Low | Self-assessed is fine for personal app; add min-loops gate later if needed |
| Spotify seek precision for stacking | Medium | Use MP3 as primary source; Spotify for playback only |
| Translation idiom accuracy | Medium | Full-song context in Claude prompt; user edits |

---

## 7. Development Phases

### Phase 1: Core Loop (~28 hours)
Working app: add song, translate, auto-timestamp, loop lines, master them, stack them.

### Phase 2: Polish + Spotify (~16 hours)
Spotify integration, PWA installability, translation toggle animation, stack loop counter.

### Phase 3: Enhance (~18 hours)
YouTube, audio speed control, tap-word-for-definition, magic link auth, offline caching.

**Total: ~62 hours** (down from 77 in v1.2 — simpler product, less code)

---

## 8. Open Questions

- Should there be a "karaoke highlight" mode where words light up in real-time during stacking? (Whisper provides word-level timestamps, making this feasible.)
- When you come back the next day, should mastered lines reset to "needs review" after N days? (Spaced repetition.)
- Should the loop count be visible on the checklist? (e.g., "Line 5 — looped 14 times, not yet mastered")
- Domain name?

---

## 9. Changelog

### v2.0 (Current)
- Complete redesign of learning model: Atomize → Loop → Master → Stack → Expand
- Replaced Study/Flow modes with single looping mechanic
- Replaced three-button card (Stop/Replay/Next) with two-button card (Mastered/Pause)
- Replaced segment view with checklist + progressive stack buttons
- Added slide-up card pattern (Spotify "now playing" style)
- Tap-to-toggle translation visibility
- Continuous audio stacking with auto-loop
- Reduced total scope from ~77 to ~62 hours

### v1.2
- Whisper auto-timestamps moved to Phase 1
- Alpine.js replaced vanilla JS
- Full-song JSON translation

### v1.1
- Three card buttons (Stop, Replay, Next)
- Dual playback modes (Study + Flow)
- Complete task breakdown

### v1.0
- Initial spec
