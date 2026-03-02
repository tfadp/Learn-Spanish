"""
Upload routes — handle MP3 file uploads.
Files are saved with a UUID prefix to avoid name collisions when
two songs happen to have the same filename.
"""

import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile

router = APIRouter(prefix="/upload", tags=["upload"])

# Resolve relative to this file so it works regardless of where uvicorn starts
UPLOAD_DIR = Path(__file__).resolve().parent.parent / "static" / "uploads"


@router.post("/mp3")
async def upload_mp3(file: UploadFile):
    """Accept an MP3 upload, stream it to disk in chunks.
    Validates: content-type, filename (no traversal), extension, size."""
    if not file.content_type or not file.content_type.startswith("audio/"):
        raise HTTPException(
            status_code=400,
            detail="Only audio files are accepted (content_type must start with 'audio/')",
        )

    # Strip directory components to block path traversal
    # Path("../../evil.mp3").name → "evil.mp3"
    raw_name = Path(file.filename).name if file.filename else ""
    if not raw_name:
        raise HTTPException(status_code=400, detail="Filename is required")

    if not raw_name.lower().endswith(".mp3"):
        raise HTTPException(
            status_code=400, detail="Only .mp3 files are accepted"
        )

    # UUID prefix guarantees uniqueness even if two files share a name
    unique_prefix = uuid.uuid4().hex[:12]
    safe_filename = f"{unique_prefix}_{raw_name}"

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    file_path = UPLOAD_DIR / safe_filename

    # Final safety: resolved path must stay under UPLOAD_DIR
    if not file_path.resolve().is_relative_to(UPLOAD_DIR.resolve()):
        raise HTTPException(status_code=400, detail="Invalid filename")

    # Stream to disk in chunks — avoids loading entire file into memory
    max_size = 20 * 1024 * 1024  # 20MB
    chunk_size = 8 * 1024         # 8KB per read
    bytes_written = 0

    try:
        with open(file_path, "wb") as dest:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                bytes_written += len(chunk)
                if bytes_written > max_size:
                    raise HTTPException(
                        status_code=400,
                        detail="File too large. Maximum size is 20MB.",
                    )
                dest.write(chunk)
    except HTTPException:
        # Clean up partial file on size rejection
        file_path.unlink(missing_ok=True)
        raise

    relative_path = f"static/uploads/{safe_filename}"

    return {
        "file_path": relative_path,
        "filename": raw_name,
    }
