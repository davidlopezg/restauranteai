"""
Regression tests for the Archivo de Ideas transversal dispatcher (PR 3).

Verifies that:
1. Skills respond normally to non-command messages (no regression)
2. Commands are intercepted and return confirmation/error responses
3. Edge cases don't crash the dispatcher
"""

from __future__ import annotations

import sys
import pytest
import sqlite3
from pathlib import Path
from unittest.mock import patch, MagicMock

# Mock gradio before importing app.py (not available in test env)
sys.modules["gradio"] = MagicMock()
sys.modules["gradio.themes"] = MagicMock()
sys.modules["gradio.themes"]().Soft = MagicMock()


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def tmp_db_conn(tmp_path: Path):
    """Create a temporary SQLite database for regression testing."""
    db_path = tmp_path / "test_ideas.db"
    conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=5.0)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ideas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            idea TEXT NOT NULL,
            categoria TEXT,
            contexto TEXT,
            confirmada_por_usuario INTEGER NOT NULL DEFAULT 1,
            origen TEXT NOT NULL,
            origen_skill TEXT
        )
    """)
    conn.commit()
    return conn


@pytest.fixture(autouse=True)
def reset_state():
    """Reset memoria module in-memory state before each test."""
    from agents.memoria.commands import _reset_state
    _reset_state()


@pytest.fixture
def mock_call_minimax(tmp_db_conn):
    """Mock call_minimax and init_db for clean regression testing.

    Patches:
    - ``agents.memoria.storage.init_db``: returns the temp SQLite connection.
    - ``agents.creativo.agent.call_minimax``: catches calls from agent.py CLI.
    - ``app.call_minimax``: catches calls from app.py (imported at module-level
      via ``from X import Y``, so source module patching alone doesn't work after
      the first test that caches the app module).
    """
    conn = tmp_db_conn

    def _mock_init_db(*args, **kwargs):
        return conn

    with patch("agents.memoria.storage.init_db", side_effect=_mock_init_db):
        with patch("agents.creativo.agent.call_minimax") as mock:
            mock.return_value = (
                "Esta es una respuesta simulada del chef para pruebas de regresión."
            )
            # Import app WHILE the source module patch is active so the
            # ``from agents.creativo.agent import call_minimax`` at module
            # level captures the mocked version.
            import app as app_module
            # Also patch app.call_minimax for subsequent test runs where
            # sys.modules caches the already-imported app module.
            with patch.object(app_module, "call_minimax", mock):
                yield mock


# ── Tests ───────────────────────────────────────────────────────────────────


class TestRegresionFicha:
    """Skill 'ficha' works normally with the dispatcher active."""

    def test_mensaje_normal_ejecuta_handler(self, mock_call_minimax):
        """Non-command message → ficha handler executes (call_minimax called)."""
        from app import responder

        result = responder("dame una ficha de setas", [], "ficha")
        mock_call_minimax.assert_called_once()
        assert result["role"] == "assistant"
        assert "respuesta simulada" in result["content"]

    def test_mensaje_con_historial_ejecuta_handler(self, mock_call_minimax):
        """Non-command message with history → handler still executes."""
        from app import responder

        historial = [{"role": "assistant", "content": "respuesta anterior del chef"}]
        result = responder("setas con parmesano", historial, "ficha")
        mock_call_minimax.assert_called_once()
        assert result["role"] == "assistant"
        assert "respuesta simulada" in result["content"]

    def test_comando_devuelve_respuesta_sin_handler(self, mock_call_minimax):
        """Command /guardar [texto] → dispatcher returns confirmation, no handler."""
        from app import responder

        result = responder("/guardar probar kumquat", [], "ficha")
        # call_minimax should NOT be called (dispatcher intercepted)
        mock_call_minimax.assert_not_called()
        assert result["role"] == "assistant"
        content = result["content"]
        # Should be a confirmation message, not a skill response
        assert "respuesta simulada" not in content
        # Should mention save or be a success/duplicate message
        assert any(marker in content for marker in ("✅", "⚠️", "guardada"))

    def test_varios_mensajes_sin_comando(self, mock_call_minimax):
        """Multiple canonical non-command inputs → handler always executes."""
        from app import responder

        mensajes = [
            "dame una ficha de setas",
            "maridaje para cordero",
            "quiero un plato vegano",
            "qué tal un postre de chocolate",
        ]
        for msg in mensajes:
            mock_call_minimax.reset_mock()
            result = responder(msg, [], "ficha")
            mock_call_minimax.assert_called_once()
            assert result["role"] == "assistant"

    def test_comando_desconocido_no_ejecuta_handler(self, mock_call_minimax):
        """Unknown command with / → dispatcher returns error, no handler."""
        from app import responder

        result = responder("/xyz", [], "ficha")
        mock_call_minimax.assert_not_called()
        assert result["role"] == "assistant"
        assert "Comando no reconocido" in result["content"]


class TestRegresionIdeasCreativas:
    """Skill 'ideas_creativas' works normally with the dispatcher active."""

    def test_mensaje_normal_ejecuta_handler(self, mock_call_minimax):
        """Non-command message → ideas_creativas handler executes."""
        from app import responder

        result = responder("dame ideas para otoño", [], "ideas_creativas")
        mock_call_minimax.assert_called_once()
        assert result["role"] == "assistant"

    def test_comando_devuelve_respuesta_sin_handler(self, mock_call_minimax):
        """Command in ideas_creativas → dispatcher intercepts."""
        from app import responder

        # Use a command with text to ensure it's handled properly
        result = responder("/guardar probar kumquat", [], "ideas_creativas")
        mock_call_minimax.assert_not_called()
        assert result["role"] == "assistant"
        content = result["content"]
        assert "respuesta simulada" not in content
        assert any(marker in content for marker in ("✅", "⚠️", "guardada"))

    def test_mensaje_normal_sin_comando(self, mock_call_minimax):
        """Multiple canonical non-command inputs → handler executes."""
        from app import responder

        mensajes = [
            "dame ideas para otoño",
            "ideas de postres sin gluten",
        ]
        for msg in mensajes:
            mock_call_minimax.reset_mock()
            result = responder(msg, [], "ideas_creativas")
            mock_call_minimax.assert_called_once()
            assert result["role"] == "assistant"


class TestRegresionDispatcheador:
    """Dispatcher behavior and edge cases."""

    def test_historial_vacio_no_crash_guardar(self, mock_call_minimax):
        """Empty history when /guardar is called → error message, no crash."""
        from app import responder

        result = responder("/guardar", [], "ficha")
        assert result["role"] == "assistant"
        content = result["content"]
        # Should say there's no recent message
        assert "no tengo un mensaje reciente" in content

    def test_exception_safety_net(self):
        """If init_db raises, user gets error, not a crash."""
        from app import responder

        with patch("agents.memoria.storage.init_db") as mock_init:
            mock_init.side_effect = Exception("DB failure simulation")
            result = responder("/guardar test", [], "ficha")
            assert result["role"] == "assistant"
            assert "Error interno" in result["content"]
            assert "funcionando normalmente" in result["content"]

    def test_mensaje_vacio_retorna_vacio(self, mock_call_minimax):
        """Empty message → empty response, no handler."""
        from app import responder

        result = responder("", [], "ficha")
        mock_call_minimax.assert_not_called()
        assert result["role"] == "assistant"
        assert result["content"] == ""

    def test_historial_sin_assistant_no_crash(self, mock_call_minimax):
        """History with no assistant messages → dispatcher handles gracefully."""
        from app import responder

        historial = [{"role": "user", "content": "hola"}]
        # Non-command should still work
        result = responder("dame una ficha", historial, "ficha")
        mock_call_minimax.assert_called_once()
        assert result["role"] == "assistant"

    def test_guardar_con_historial_usuario_solo(self, mock_call_minimax):
        """History with only user messages → /guardar returns correct error."""
        from app import responder

        historial = [{"role": "user", "content": "hola"}]
        result = responder("/guardar", historial, "ficha")
        mock_call_minimax.assert_not_called()
        assert result["role"] == "assistant"
        assert "no tengo un mensaje reciente" in result["content"]

    def test_multiple_comandos_seguidos(self, mock_call_minimax):
        """Multiple commands in sequence all intercepted by dispatcher."""
        from app import responder

        for cmd in ["/ayuda", "/silenciar-contador", "/export-ideas"]:
            mock_call_minimax.reset_mock()
            result = responder(cmd, [], "ficha")
            mock_call_minimax.assert_not_called()
            assert result["role"] == "assistant"
            assert len(result["content"]) > 0

    def test_olvidar_todo_devuelve_confirmacion(self, mock_call_minimax):
        """/olvidar todo → confirmation prompt, not skill response."""
        from app import responder

        result = responder("/olvidar todo", [], "ficha")
        mock_call_minimax.assert_not_called()
        assert result["role"] == "assistant"
        content = result["content"]
        assert "olvidar todo" in content
        assert "confirmar" in content
        assert "respuesta simulada" not in content
