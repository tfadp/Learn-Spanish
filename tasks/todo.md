# LyricFlow — Task Tracker

## Session State
- **Branch**: main
- **Last test result**: 13/13 passed
- **Last commit**: e5702fa — Fix review issues, add PWA icons, and polish mastery animation
- **Blockers**: None
- **Pending decisions**: None

## Completed Tasks

### Session 7 (2026-03-03)
- [x] Fix all 24 /review issues (grouped into 7 fix tasks)
  - #1 (HIGH): Null guard in debounced timing save (captured line ref before setTimeout)
  - #2: Cancel timing timeout on close_card
  - #3: Upper bound guard on end_time_ms (audio duration)
  - #8+#9: 44px touch targets for eye toggle + timing button
  - #13 (HIGH): Try/except for corrupt JSON in translation cache
  - #17: Cache freshness validation (line count + original text match)
  - #18: Skip empty translations to protect existing DB values
  - #20: Sync sw.js precache versions to v11
- [x] Refactor timing save into save_line_timing helper with _pending_timing_line tracking
- [x] Flush pending timing save on close_card instead of dropping it
- [x] Generate PNG icons (192px + 512px) for iPhone PWA installability
- [x] Update manifest.json with PNG icon entries
- [x] Update apple-touch-icon in base.html to PNG
- [x] Add checkmark pop animation on mastery (scale 0→1.2→1.0, 300ms)
- [x] Push to GitHub + provide deploy instructions

## Backlog
- [ ] Test PWA installability on iPhone Safari (Add to Home Screen)
- [ ] Test PWA installability on Chrome Android
- [ ] Consider adding a second song to test multi-song flows
