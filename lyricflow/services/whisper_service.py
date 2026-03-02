"""
Whisper service — generates word/line timestamps from audio.

Uses OpenAI Whisper locally to transcribe, then fuzzy-matches
the transcription against known lyrics using rapidfuzz.

Why two separate functions?
- transcribe_audio handles the heavy ML work (CPU-bound)
- align_lyrics is pure string matching, easy to test independently
"""

import logging
import re

import whisper
from rapidfuzz import fuzz

logger = logging.getLogger(__name__)


class WhisperTranscriptionError(Exception):
    """Raised when Whisper transcription fails.
    Lets callers distinguish 'transcription broke' from 'audio had no words'."""
    pass

# ── Language map ────────────────────────────────────────────────
# Whisper expects ISO 639-1 codes; our DB stores full names.
LANGUAGE_CODES = {
    "spanish": "es",
    "portuguese": "pt",
    "french": "fr",
    "italian": "it",
    "german": "de",
    "japanese": "ja",
    "korean": "ko",
}

# ── Module-level model cache ───────────────────────────────────
# Loading a Whisper model is slow (~5 s for "base").
# We load once and reuse across all requests.
_model = None


def _get_model():
    """Return the cached Whisper model, loading it on first call."""
    global _model
    if _model is None:
        _model = whisper.load_model("base")
    return _model


# ── Text normalization ─────────────────────────────────────────

def _normalize(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace.

    Keeps letters, numbers, and spaces so fuzzy matching
    compares actual words, not stray commas or quotes.
    """
    text = text.lower()
    # Keep only letters (any script), digits, and spaces
    text = re.sub(r"[^\w\s]", "", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ── Public API ─────────────────────────────────────────────────

def transcribe_audio(audio_path: str, language: str) -> dict:
    """Run Whisper on an audio file and return the raw result dict.

    Parameters
    ----------
    audio_path : str
        Absolute path to the MP3 file on disk.
    language : str
        Human-readable language name (e.g. "spanish").
        Mapped to a Whisper code; unknown languages trigger auto-detect.

    Returns
    -------
    dict
        Whisper result with "segments" list.  Each segment has
        "start", "end", "text", and optionally "words".
        Returns {"segments": []} if transcription fails.
    """
    code = LANGUAGE_CODES.get(language.lower()) if language else None

    try:
        model = _get_model()
        result = model.transcribe(
            audio_path,
            language=code,
            word_timestamps=True,
        )
        return result
    except Exception as exc:
        logger.error("Whisper transcription failed for %s: %s", audio_path, exc)
        raise WhisperTranscriptionError(
            f"Transcription failed: {exc}"
        ) from exc


def align_lyrics(lyric_lines: list[str], whisper_result: dict) -> list[dict]:
    """Match known lyric lines to Whisper segments via fuzzy matching.

    Algorithm overview:
    1. Walk through segments sequentially (pointer advances forward only).
    2. For each lyric line, find the best-scoring segment(s).
    3. If one segment isn't a great match, try merging with the next.
    4. Classify confidence: >=70 high, 40-69 low, <40 unmatched.

    Parameters
    ----------
    lyric_lines : list[str]
        Original lyric texts in order (line 1, line 2, …).
    whisper_result : dict
        The dict returned by transcribe_audio.

    Returns
    -------
    list[dict]
        One entry per lyric line with timing and confidence info.
    """
    segments = whisper_result.get("segments", [])
    total_segments = len(segments)
    total_lines = len(lyric_lines)

    # Pointer into segments — only moves forward so earlier lyrics
    # always match earlier audio (preserves chronological order).
    seg_ptr = 0

    results = []

    for i, lyric_text in enumerate(lyric_lines):
        norm_lyric = _normalize(lyric_text)

        best_score = 0
        best_start = None
        best_end = None
        best_whisper_text = ""

        if seg_ptr < total_segments and norm_lyric:
            # ── Try single-segment match ──────────────────────
            seg = segments[seg_ptr]
            norm_seg = _normalize(seg.get("text", ""))
            single_score = fuzz.partial_ratio(norm_lyric, norm_seg)

            best_score = single_score
            best_start = seg["start"]
            best_end = seg["end"]
            best_whisper_text = seg.get("text", "").strip()

            # ── Try merging with the next segment ─────────────
            # Sometimes one lyric line spans two Whisper segments
            # (e.g. Whisper breaks mid-sentence).
            if seg_ptr + 1 < total_segments:
                next_seg = segments[seg_ptr + 1]
                combined_text = norm_seg + " " + _normalize(
                    next_seg.get("text", "")
                )
                combined_score = fuzz.partial_ratio(
                    norm_lyric, combined_text
                )

                if combined_score > single_score:
                    best_score = combined_score
                    best_start = seg["start"]
                    best_end = next_seg["end"]
                    best_whisper_text = (
                        seg.get("text", "").strip()
                        + " "
                        + next_seg.get("text", "").strip()
                    )

            # ── Advance pointer ───────────────────────────────
            if best_score >= 40:
                # Good enough match — advance past the segment(s) we used
                if (
                    seg_ptr + 1 < total_segments
                    and best_end == segments[seg_ptr + 1]["end"]
                ):
                    # We merged two segments, skip both
                    seg_ptr += 2
                else:
                    seg_ptr += 1
            else:
                # No match — still advance proportionally so we don't
                # get stuck. Estimate where this line *should* be
                # in the audio based on its position in the lyrics.
                expected_pos = int(
                    (i + 1) / total_lines * total_segments
                )
                # Move forward at least 1, but don't overshoot
                seg_ptr = max(seg_ptr + 1, min(expected_pos, total_segments))

        # ── Build result entry ────────────────────────────────
        if best_score >= 40:
            # "high" (>=70) or "low" (40-69) — we have usable timing
            confidence = "high" if best_score >= 70 else "low"
            results.append({
                "line_number": i + 1,
                "start_time_ms": int(best_start * 1000),
                "end_time_ms": int(best_end * 1000),
                "confidence": confidence,
                "whisper_text": best_whisper_text,
            })
        else:
            # Unmatched — no reliable timing data
            results.append({
                "line_number": i + 1,
                "start_time_ms": None,
                "end_time_ms": None,
                "confidence": "unmatched",
                "whisper_text": best_whisper_text,
            })

    return results
