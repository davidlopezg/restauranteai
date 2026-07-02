"""
Tests for confirmation patterns for destructive operations.
Verifies that /olvidar requires explicit confirmation, and /export-ideas works.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from agents.memoria.commands import handle_command, _reset_state
from agents.memoria.storage import (
    init_db,
    save_idea,
    load_ideas,
    count_ideas,
    export_ideas,
)


@pytest.fixture(autouse=True)
def reset_state():
    _reset_state()
    yield


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "test_rgpd.db"


@pytest.fixture
def db_conn(db_path: Path) -> sqlite3.Connection:
    conn = init_db(db_path)
    yield conn
    conn.close()


class TestOlvidarTodo:
    def test_olvidar_todo_sin_confirmacion(self, db_conn: sqlite3.Connection):
        """/olvidar todo then any non-confirming message → no deletion."""
        save_idea(db_conn, "idea 1")
        save_idea(db_conn, "idea 2")
        # Step 1: /olvidar todo
        handle_command("/olvidar todo", conn=db_conn)
        assert count_ideas(db_conn) == 2
        # Step 2: non-confirming message (not "olvidar todo")
        result = handle_command("no quiero borrar", conn=db_conn)
        # Non-command returns None
        assert result is None
        # Ideas still intact
        assert count_ideas(db_conn) == 2

    def test_olvidar_todo_con_confirmacion(self, db_conn: sqlite3.Connection):
        """/olvidar todo then olvidar todo → all ideas deleted."""
        save_idea(db_conn, "idea 1")
        save_idea(db_conn, "idea 2")
        save_idea(db_conn, "idea 3")
        # Step 1: /olvidar todo
        handle_command("/olvidar todo", conn=db_conn)
        # Step 2: confirm with "olvidar todo" (without /)
        result = handle_command("olvidar todo", conn=db_conn)
        assert result is not None
        assert "✅" in result["content"]
        assert "3" in result["content"]
        assert "borrado" in result["content"].lower()
        assert count_ideas(db_conn) == 0

    def test_olvidar_todo_sin_estado_pendiente(self, db_conn: sqlite3.Connection):
        """'olvidar todo' (no prior /olvidar todo) → 'No había nada que confirmar'."""
        result = handle_command("olvidar todo", conn=db_conn)
        assert result is not None
        assert "⚠️" in result["content"]
        assert "No había nada que confirmar" in result["content"]

    def test_olvidar_todo_multiple_confirmations_rejected(self, db_conn: sqlite3.Connection):
        """After confirming once, second 'olvidar todo' without pending → error."""
        save_idea(db_conn, "idea 1")
        handle_command("/olvidar todo", conn=db_conn)
        # First confirmation works
        result1 = handle_command("olvidar todo", conn=db_conn)
        assert result1 is not None
        assert "✅" in result1["content"]
        # Second has no pending state → error
        result2 = handle_command("olvidar todo", conn=db_conn)
        assert result2 is not None
        assert "⚠️" in result2["content"]
        assert "No había nada que confirmar" in result2["content"]


class TestOlvidarN:
    def test_olvidar_n_con_confirmacion(self, db_conn: sqlite3.Connection):
        """/olvidar 1 then olvidar 1 → idea #1 deleted."""
        idea_id = save_idea(db_conn, "idea a borrar")
        save_idea(db_conn, "idea a conservar")

        # Step 1: /olvidar 1
        handle_command(f"/olvidar {idea_id}", conn=db_conn)
        assert count_ideas(db_conn) == 2

        # Step 2: confirm
        result = handle_command(f"olvidar {idea_id}", conn=db_conn)
        assert result is not None
        assert "✅" in result["content"]
        assert f"Idea #{idea_id}" in result["content"]
        assert count_ideas(db_conn) == 1

    def test_olvidar_n_mismatched_confirm(self, db_conn: sqlite3.Connection):
        """/olvidar 1 then olvidar 2 → no deletion (wrong ID)."""
        save_idea(db_conn, "idea 1")
        save_idea(db_conn, "idea 2")

        # Step 1: /olvidar 1
        handle_command("/olvidar 1", conn=db_conn)

        # Step 2: wrong ID → not confirmed (passes through as non-command)
        result = handle_command("olvidar 2", conn=db_conn)
        assert result is None  # passed through

        # Ideas intact
        assert count_ideas(db_conn) == 2


class TestExport:
    def test_export_con_ideas(self, db_conn: sqlite3.Connection, tmp_path: Path):
        """/export-ideas with 3 ideas → JSON file with 3 entries."""
        save_idea(db_conn, "idea 1", categoria="concepto")
        save_idea(db_conn, "idea 2", categoria="plato")
        save_idea(db_conn, "idea 3", categoria="técnica")

        # Use a custom export path via the storage function to test content
        export_path = tmp_path / "export_test.json"
        export_ideas(db_conn, export_path)

        with open(export_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert len(data) == 3
        ideas_texts = [item["idea"] for item in data]
        assert "idea 1" in ideas_texts
        assert "idea 2" in ideas_texts
        assert "idea 3" in ideas_texts

    def test_export_sin_ideas(self, db_conn: sqlite3.Connection, tmp_path: Path):
        """/export-ideas on empty DB → JSON file with empty array."""
        export_path = tmp_path / "export_empty.json"
        export_ideas(db_conn, export_path)

        with open(export_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data == []
