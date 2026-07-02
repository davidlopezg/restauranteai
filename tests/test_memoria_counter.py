"""
Tests for counter state management via commands.
Verifies that /silenciar-contador toggles state and affects save confirmations.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from agents.memoria.commands import (
    handle_command,
    get_contador_state,
    toggle_contador_state,
    _reset_state,
)
from agents.memoria.storage import init_db, save_idea


@pytest.fixture(autouse=True)
def reset_state():
    _reset_state()
    yield


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "test_counter.db"


@pytest.fixture
def db_conn(db_path: Path) -> sqlite3.Connection:
    conn = init_db(db_path)
    yield conn
    conn.close()


class TestCounter:
    def test_counter_initial_state(self):
        """get_contador_state() returns True by default."""
        assert get_contador_state() is True

    def test_counter_visible_after_save(self, db_conn: sqlite3.Connection):
        """/guardar texto with contador_activo=True → response includes 📁."""
        result = handle_command(
            "/guardar probar kumquat", conn=db_conn, contador_activo=True
        )
        assert result is not None
        assert "📁" in result["content"]

    def test_counter_silenced(self, db_conn: sqlite3.Connection):
        """/silenciar-contador then /guardar → response does NOT include 📁."""
        # Silence
        handle_command("/silenciar-contador", conn=db_conn)
        assert get_contador_state() is False
        # Guardar—counter should NOT appear because global state is False
        result = handle_command(
            "/guardar probar kumquat", conn=db_conn, contador_activo=True
        )
        assert result is not None
        assert "📁" not in result["content"]
        # But idea is still saved
        assert "✅" in result["content"]

    def test_counter_reactivated(self, db_conn: sqlite3.Connection):
        """/silenciar-contador twice then /guardar → 📁 appears again."""
        # First toggle: silence
        handle_command("/silenciar-contador", conn=db_conn)
        assert get_contador_state() is False
        # Second toggle: reactivate
        handle_command("/silenciar-contador", conn=db_conn)
        assert get_contador_state() is True
        # Guardar — counter should appear
        result = handle_command(
            "/guardar probar kumquat", conn=db_conn, contador_activo=True
        )
        assert result is not None
        assert "📁" in result["content"]

    def test_toggle_returns_new_state(self):
        """toggle_contador_state returns the new state."""
        assert toggle_contador_state() is False  # was True, now False
        assert toggle_contador_state() is True   # was False, now True
