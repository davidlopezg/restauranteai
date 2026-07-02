"""
Concurrency tests for agents.memoria.storage — verifies WAL mode handles
concurrent readers and writers safely using ThreadPoolExecutor.
"""

from __future__ import annotations

import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pytest

from agents.memoria.storage import init_db, save_idea, load_ideas, count_ideas


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    """Return a temporary path for the test database."""
    return tmp_path / "concurrent_ideas.db"


@pytest.fixture
def db_conn(db_path: Path) -> sqlite3.Connection:
    """Create a clean WAL-mode SQLite connection for testing."""
    conn = init_db(db_path)
    yield conn
    conn.close()


class TestConcurrentWrites:
    """Test that multiple threads can write simultaneously without corruption."""

    def test_concurrent_writes(self, db_path: Path):
        """4 threads write simultaneously, all 4 distinct IDs returned, count=4."""
        # Each thread opens its own connection (WAL mode allows this safely)
        def write_idea(n: int) -> int:
            conn = init_db(db_path)
            try:
                return save_idea(
                    conn,
                    f"idea concurrente {n}",
                    categoria="test",
                    origen_skill="concurrency",
                )
            finally:
                conn.close()

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(write_idea, i) for i in range(4)]
            ids = [f.result() for f in as_completed(futures)]

        # All IDs should be distinct
        assert len(set(ids)) == 4, f"Expected 4 distinct IDs, got {ids}"

        # Verify by reopening the DB
        conn2 = init_db(db_path)
        try:
            assert count_ideas(conn2) == 4
        finally:
            conn2.close()

    def test_concurrent_read_and_write(self, db_path: Path):
        """One thread writes while another reads, no exception, results consistent."""
        # Seed with the main connection first
        seed_conn = init_db(db_path)
        for i in range(3):
            save_idea(seed_conn, f"seed idea {i}", origen="seed")
        seed_conn.close()

        def writer() -> int:
            conn = init_db(db_path)
            try:
                return save_idea(conn, "written during read", origen="concurrent")
            finally:
                conn.close()

        def reader() -> int:
            conn = init_db(db_path)
            try:
                ideas = load_ideas(conn)
                return len(ideas)
            finally:
                conn.close()

        with ThreadPoolExecutor(max_workers=2) as executor:
            w_future = executor.submit(writer)
            r_future = executor.submit(reader)
            w_id = w_future.result()
            r_count = r_future.result()

        # Writer should have a valid ID
        assert isinstance(w_id, int)
        assert w_id > 0

        # Reader should have gotten at least the seed ideas (might or might not
        # see the concurrent write due to WAL read consistency)
        assert r_count >= 3

        # Final count should be 4 (3 seeds + 1 concurrent)
        final_conn = init_db(db_path)
        try:
            assert count_ideas(final_conn) == 4
        finally:
            final_conn.close()
