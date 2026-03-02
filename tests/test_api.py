"""
Regression tests for LyricFlow fixes.
Run with: python -m pytest tests/test_api.py -v
"""

import io
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from lyricflow.database import Base, get_db
from lyricflow.models import Song, LyricLine
from lyricflow.main import app

# ── Test database (in-memory SQLite) ─────────────────────────

TEST_DB_URL = "sqlite://"
test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(bind=test_engine)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    """Create tables before each test, drop after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


def _seed_song_with_lines(n_lines=1):
    """Helper: create a song + N lines in the test DB. Returns (song_id, [line_ids])."""
    db = TestSession()
    song = Song(
        title="Test Song", artist="Artist", language="spanish",
        audio_file_path="static/uploads/fake.mp3",
    )
    db.add(song)
    db.commit()
    db.refresh(song)
    song_id = song.id  # capture before session closes

    line_ids = []
    for i in range(n_lines):
        line = LyricLine(
            song_id=song_id, line_number=i + 1,
            original_text=f"Hola mundo {i}",
            translation=f"Hello world {i}",
        )
        db.add(line)
        db.commit()
        db.refresh(line)
        line_ids.append(line.id)

    db.close()
    return song_id, line_ids


# ── Fix 1: Path traversal ───────────────────────────────────

class TestUploadTraversal:
    def test_traversal_filename_is_sanitized(self):
        """Filename with ../ should be stripped to just the base name."""
        fake_mp3 = io.BytesIO(b"\x00" * 100)
        resp = client.post(
            "/api/upload/mp3",
            files={"file": ("../../etc/passwd.mp3", fake_mp3, "audio/mpeg")},
        )
        # Should succeed with sanitized name (no ../ in path)
        if resp.status_code == 200:
            assert "../" not in resp.json()["file_path"]

    def test_rejects_empty_filename(self):
        fake_mp3 = io.BytesIO(b"\x00" * 100)
        resp = client.post(
            "/api/upload/mp3",
            files={"file": ("", fake_mp3, "audio/mpeg")},
        )
        # FastAPI may reject with 422 before our 400 handler runs
        assert resp.status_code in (400, 422)

    def test_rejects_non_mp3_extension(self):
        fake_wav = io.BytesIO(b"\x00" * 100)
        resp = client.post(
            "/api/upload/mp3",
            files={"file": ("song.wav", fake_wav, "audio/mpeg")},
        )
        assert resp.status_code == 400
        assert "mp3" in resp.json()["detail"].lower()


# ── Fix 2: Upload size limit ────────────────────────────────

class TestUploadSize:
    def test_rejects_oversized_file(self):
        """File over 20MB should be rejected."""
        big_file = io.BytesIO(b"\x00" * (21 * 1024 * 1024))
        resp = client.post(
            "/api/upload/mp3",
            files={"file": ("big.mp3", big_file, "audio/mpeg")},
        )
        assert resp.status_code == 400
        assert "20MB" in resp.json()["detail"]

    def test_accepts_small_file(self):
        """Normal-sized MP3 should succeed."""
        small_file = io.BytesIO(b"\x00" * 1024)
        resp = client.post(
            "/api/upload/mp3",
            files={"file": ("small.mp3", small_file, "audio/mpeg")},
        )
        assert resp.status_code == 200
        assert resp.json()["file_path"].startswith("static/uploads/")


# ── Fix 3: Whisper error propagation ────────────────────────

class TestWhisperErrors:
    @patch("lyricflow.routes.timestamps.transcribe_audio")
    def test_whisper_failure_sets_failed_status(self, mock_transcribe):
        """When Whisper raises, status should be 'failed', not 'done'."""
        from lyricflow.services.whisper_service import WhisperTranscriptionError
        mock_transcribe.side_effect = WhisperTranscriptionError("test error")

        song_id, _ = _seed_song_with_lines(1)
        resp = client.post(f"/api/songs/{song_id}/auto-timestamp")
        assert resp.status_code == 500

        # Verify DB state shows "failed"
        db = TestSession()
        song = db.query(Song).filter(Song.id == song_id).first()
        assert song.whisper_status == "failed"
        db.close()


# ── Fix 4: Timestamp validation ─────────────────────────────

class TestTimestampValidation:
    def test_missing_fields_returns_422(self):
        song_id, _ = _seed_song_with_lines(1)
        resp = client.put(
            f"/api/songs/{song_id}/timestamps",
            json={"timestamps": [{"line_id": 1}]},
        )
        assert resp.status_code == 422

    def test_negative_time_returns_422(self):
        song_id, line_ids = _seed_song_with_lines(1)
        resp = client.put(
            f"/api/songs/{song_id}/timestamps",
            json={"timestamps": [
                {"line_id": line_ids[0], "start_time_ms": -100, "end_time_ms": 5000}
            ]},
        )
        assert resp.status_code == 422

    def test_end_before_start_returns_422(self):
        song_id, line_ids = _seed_song_with_lines(1)
        resp = client.put(
            f"/api/songs/{song_id}/timestamps",
            json={"timestamps": [
                {"line_id": line_ids[0], "start_time_ms": 5000, "end_time_ms": 3000}
            ]},
        )
        assert resp.status_code == 422

    def test_valid_timestamps_succeed(self):
        song_id, line_ids = _seed_song_with_lines(1)
        resp = client.put(
            f"/api/songs/{song_id}/timestamps",
            json={"timestamps": [
                {"line_id": line_ids[0], "start_time_ms": 1000, "end_time_ms": 3000}
            ]},
        )
        assert resp.status_code == 200


# ── Fix 5: N+1 query count ──────────────────────────────────

class TestSongListQuery:
    def test_constant_query_count(self):
        """List songs should use selectinload, not lazy-load per song."""
        db = TestSession()
        for i in range(5):
            song = Song(title=f"Song {i}", artist="A", language="spanish")
            db.add(song)
        db.commit()
        db.close()

        query_count = 0

        def count_queries(conn, cursor, statement, parameters, context, executemany):
            nonlocal query_count
            query_count += 1

        event.listen(test_engine, "before_cursor_execute", count_queries)

        resp = client.get("/api/songs")
        assert resp.status_code == 200
        assert len(resp.json()) == 5

        event.remove(test_engine, "before_cursor_execute", count_queries)

        # selectinload = 2 queries (songs + lines). Allow up to 3 for overhead.
        # Without fix: would be 1 + 5 = 6
        assert query_count <= 3, f"Expected <=3 queries, got {query_count}"


# ── Fix 6: Bulk approval ────────────────────────────────────

class TestBulkApproval:
    def test_bulk_approve_all_lines(self):
        song_id, _ = _seed_song_with_lines(3)

        resp = client.put(f"/api/songs/{song_id}/approve-translations")
        assert resp.status_code == 200
        assert resp.json()["approved"] == 3

        # Verify all lines are approved in DB
        db = TestSession()
        lines = db.query(LyricLine).filter(
            LyricLine.song_id == song_id
        ).all()
        assert all(line.translation_approved for line in lines)
        db.close()

    def test_approve_nonexistent_song_returns_404(self):
        resp = client.put("/api/songs/9999/approve-translations")
        assert resp.status_code == 404
