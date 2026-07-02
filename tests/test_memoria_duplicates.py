"""
Tests for duplicate detection via the commands layer.
Verifies that /guardar triggers duplicate warnings and /guardar igual works.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from agents.memoria.commands import handle_command, _reset_state
from agents.memoria.storage import init_db, save_idea, count_ideas


@pytest.fixture(autouse=True)
def reset_state():
    _reset_state()
    yield


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "test_duplicates.db"


@pytest.fixture
def db_conn(db_path: Path) -> sqlite3.Connection:
    conn = init_db(db_path)
    yield conn
    conn.close()


class TestDuplicates:
    def test_duplicado_exacto(self, db_conn: sqlite3.Connection):
        """Same text as existing idea → warning with ID and /guardar igual prompt."""
        save_idea(db_conn, "probar kumquat en el postre")
        result = handle_command(
            "/guardar probar kumquat en el postre", conn=db_conn
        )
        assert result is not None
        content = result["content"]
        assert "Ya tenés algo parecido" in content
        assert "#1" in content
        assert "/guardar igual" in content
        # No new idea inserted
        assert count_ideas(db_conn) == 1

    def test_duplicado_fuzzy_sobre_umbral(self, db_conn: sqlite3.Connection):
        """85% similar text → warning with ID."""
        save_idea(db_conn, "probar kumquat en el postre de temporada")
        result = handle_command(
            "/guardar probar kumquat en postre temporada", conn=db_conn
        )
        assert result is not None
        assert "Ya tenés algo parecido" in result["content"]
        assert count_ideas(db_conn) == 1

    def test_sin_duplicado_fuzzy_bajo_umbral(self, db_conn: sqlite3.Connection):
        """50% similar text → saves directly without warning."""
        save_idea(db_conn, "probar kumquat en el postre")
        result = handle_command(
            "/guardar cambiar el menú de setas a otoño", conn=db_conn
        )
        assert result is not None
        assert "✅" in result["content"]
        assert "Ya tenés algo parecido" not in result["content"]
        assert count_ideas(db_conn) == 2

    def test_duplicado_db_vacia(self, db_conn: sqlite3.Connection):
        """Any text on empty DB → saves directly."""
        result = handle_command(
            "/guardar primera idea", conn=db_conn
        )
        assert result is not None
        assert "✅" in result["content"]
        assert "Ya tenés algo parecido" not in result["content"]
        assert count_ideas(db_conn) == 1

    def test_duplicado_con_guardar_igual(self, db_conn: sqlite3.Connection):
        """After duplicate detection, /guardar igual force-saves."""
        save_idea(db_conn, "texto duplicado")
        # Trigger duplicate
        handle_command("/guardar texto duplicado", conn=db_conn)
        # Force save
        result = handle_command("/guardar igual", conn=db_conn)
        assert result is not None
        assert "✅" in result["content"]
        assert count_ideas(db_conn) == 2
