"""
Tests for agents.memoria.formatters — pure formatting functions.

All functions are pure (no IO, no DB), so tests are direct string assertions.
"""

from __future__ import annotations

from agents.memoria.formatters import (
    format_counter,
    format_idea_list,
    format_save_confirmation,
    format_error,
    format_duplicate_warning,
)


# ── format_counter tests ───────────────────────────────────────────────────


class TestFormatCounter:
    def test_zero(self):
        assert format_counter(0) == ""

    def test_one(self):
        assert format_counter(1) == "📁 1 guardada"

    def test_many(self):
        assert format_counter(5) == "📁 5 guardadas"
        assert format_counter(100) == "📁 100 guardadas"


# ── format_idea_list tests ─────────────────────────────────────────────────


class TestFormatIdeaList:
    def test_empty(self):
        result = format_idea_list([])
        assert "Usá /guardar" in result
        assert "No tenés ideas" in result

    def test_single_idea(self):
        ideas = [
            {
                "id": 1,
                "created_at": "2026-07-02T10:00:00+00:00",
                "idea": "probar kumquat",
                "categoria": "concepto",
            }
        ]
        result = format_idea_list(ideas)
        assert "#1" in result
        assert "2026-07-02" in result
        assert "concepto" in result
        assert "probar kumquat" in result

    def test_multiple_ideas(self):
        ideas = [
            {"id": 2, "created_at": "2026-07-02T11:00:00+00:00",
             "idea": "segunda idea", "categoria": "plato"},
            {"id": 1, "created_at": "2026-07-02T10:00:00+00:00",
             "idea": "primera idea", "categoria": None},
        ]
        result = format_idea_list(ideas)
        assert "#2" in result
        assert "#1" in result
        assert "sin categoría" in result
        assert "segunda idea" in result
        assert "primera idea" in result

    def test_long_text_truncation(self):
        """Idea text >200 chars is truncated with …."""
        ideas = [
            {"id": 1, "created_at": "2026-07-02T10:00:00+00:00",
             "idea": "x" * 250, "categoria": "concepto"}
        ]
        result = format_idea_list(ideas)
        assert "x" * 200 in result
        assert "…" in result

    def test_no_categoria(self):
        ideas = [
            {"id": 1, "created_at": "2026-07-02T10:00:00+00:00",
             "idea": "texto", "categoria": None}
        ]
        result = format_idea_list(ideas)
        assert "sin categoría" in result

    def test_empty_categoria_string(self):
        ideas = [
            {"id": 1, "created_at": "2026-07-02T10:00:00+00:00",
             "idea": "texto", "categoria": ""}
        ]
        result = format_idea_list(ideas)
        assert "sin categoría" in result


# ── format_save_confirmation tests ─────────────────────────────────────────


class TestFormatSaveConfirmation:
    def test_basic(self):
        idea = {"id": 5, "idea": "probar kumquat"}
        result = format_save_confirmation(idea, count=3)
        assert "✅" in result
        assert "Idea #5" in result
        assert "probar kumquat" in result
        assert "📁 3 guardadas" in result

    def test_long_preview_truncated(self):
        """Text >80 chars is truncated."""
        idea = {"id": 1, "idea": "a" * 100}
        result = format_save_confirmation(idea, count=1)
        assert "a" * 80 in result
        assert "…" in result

    def test_contador_inactive(self):
        """No counter line when contador_activo=False."""
        idea = {"id": 1, "idea": "texto corto"}
        result = format_save_confirmation(idea, count=5, contador_activo=False)
        assert "✅" in result
        assert "📁" not in result

    def test_counter_zero_not_shown(self):
        """Counter doesn't show '📁 0 guardadas'."""
        idea = {"id": 1, "idea": "texto"}
        result = format_save_confirmation(idea, count=0, contador_activo=True)
        assert "📁" not in result


# ── format_error tests ─────────────────────────────────────────────────────


class TestFormatError:
    def test_basic(self):
        result = format_error("especificá qué querés guardar")
        assert result == "⚠️ especificá qué querés guardar"

    def test_empty_msg(self):
        result = format_error("")
        assert result == "⚠️ "


# ── format_duplicate_warning tests ─────────────────────────────────────────


class TestFormatDuplicateWarning:
    def test_basic(self):
        dup = {"id": 1, "idea": "probar kumquat en el postre"}
        result = format_duplicate_warning(dup)
        assert "#1" in result
        assert "probar kumquat" in result
        assert "/guardar igual" in result

    def test_long_preview(self):
        """Text >80 chars is truncated."""
        dup = {"id": 2, "idea": "a" * 100}
        result = format_duplicate_warning(dup)
        assert "a" * 80 in result
        assert "…" in result
