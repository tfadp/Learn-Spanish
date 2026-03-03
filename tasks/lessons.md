# LyricFlow — Lessons Learned

## Session 7 (2026-03-03)

### Lesson 1: Check what already exists before planning new work
The user proposed 8 PWA polish items. On inspection, 5 were already done
(manifest, SW, SW registration, card swipe, touch targets). Only 3 items
were actually new. Always audit the codebase before proposing changes.

### Lesson 2: Debounced saves need flush-on-close, not just cancel
When you have a debounced save (setTimeout), cancelling the timeout on
close means the user's last few changes are silently lost. Better pattern:
flush the pending save immediately on close, then cancel the timeout.

### Lesson 3: Translation cache needs content validation, not just line count
Checking `len(cached) == len(lines)` catches added/removed lines, but
misses edited lyrics (same count, different text). The fix: validate both
line_number and original_text match between cache and DB rows.

### Lesson 4: iOS Safari ignores SVG icons in manifest.json
For PWA "Add to Home Screen" to show an icon on iPhone, you need PNG
icons. SVG icons are only used by browsers that support them (Chrome).
Always include both PNG (192px, 512px) and SVG in the manifest.

### Lesson 5: Capture closure variables before setTimeout
`this.current_line` inside a setTimeout callback can be null if the card
closes before the timeout fires. Always capture `const line_to_save = this.current_line`
before the setTimeout so the callback references a stable snapshot.
