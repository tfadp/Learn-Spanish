# Translation service — uses Anthropic Claude API to translate song lyrics.
# Sends all lines in one request so Claude can use full-song context
# for idiomatic (natural-sounding) translations instead of word-for-word.

import json
import os
from pathlib import Path

from anthropic import Anthropic

# JSON cache lives at project root → translations/<song_id>.json
# Easy to find, hand-edit, and version-control if desired.
TRANSLATIONS_DIR = Path(__file__).resolve().parent.parent.parent / "translations"


def get_cache_path(song_id: int) -> Path:
    """Return the path to a song's translation cache file."""
    return TRANSLATIONS_DIR / f"{song_id}.json"


def load_cached_translations(song_id: int) -> list[dict] | None:
    """
    Load translations from the JSON cache file.

    Returns a list of dicts like:
        [{"line_number": 1, "original": "...", "translation": "..."}, ...]
    Returns None if no cache file exists.
    """
    cache_path = get_cache_path(song_id)
    if not cache_path.exists():
        return None
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        # Corrupt or unreadable cache — treat as missing so API gets called
        return None


def save_cached_translations(
    song_id: int,
    lines_data: list[dict],
) -> None:
    """
    Save translations to a JSON cache file for instant future loads.

    lines_data: list of {"line_number": int, "original": str, "translation": str}
    """
    TRANSLATIONS_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = get_cache_path(song_id)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(lines_data, f, ensure_ascii=False, indent=2)


def translate_song(lines: list[str], language: str) -> list[str]:
    """
    Translate a list of lyric strings from `language` into English.

    Makes a SINGLE API call with every line so Claude sees full context.
    Returns translations in the same order as the input list.

    On ANY failure (missing key, API error, bad JSON), returns a list of
    empty strings so the caller always gets a predictable shape back.
    """
    # Edge case: nothing to translate
    if not lines:
        return []

    # --- Build the numbered dict that becomes our user message ---
    # Why numbered? So the response maps 1-to-1 with input order.
    numbered_input = {str(i + 1): text for i, text in enumerate(lines)}

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        # No key = can't call the API; fail gracefully
        return [""] * len(lines)

    try:
        client = Anthropic(api_key=api_key)

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=(
                "You translate song lyrics. For each numbered line, provide "
                "a natural English translation that captures meaning and "
                "intent, not word-for-word. Return ONLY valid JSON: "
                '{"1": "translation", "2": "translation", ...}'
            ),
            messages=[
                {
                    "role": "user",
                    "content": json.dumps(numbered_input),
                }
            ],
        )

        # The SDK returns content as a list of blocks; grab the text.
        raw_text = message.content[0].text
        parsed = json.loads(raw_text)

        # Rebuild as an ordered list using the same numbering we sent.
        translations = [
            parsed.get(str(i + 1), "") for i in range(len(lines))
        ]
        return translations

    except Exception:
        # Catch-all: API errors, network issues, JSON parse failures, etc.
        return [""] * len(lines)
