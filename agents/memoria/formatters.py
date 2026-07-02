"""
formatters.py — Pure formatting functions for the Archivo de Ideas module.

All functions are pure (no IO, no DB). They take primitives/dicts and return
formatted strings ready for display in CLI or Gradio chat.
"""

from __future__ import annotations

from typing import Any


def format_counter(count: int) -> str:
    """Format the ideas counter.

    Args:
        count: Number of saved ideas.

    Returns:
        Empty string if count == 0,
        "📁 1 guardada" if count == 1,
        "📁 N guardadas" if count >= 2.
    """
    if count == 0:
        return ""
    if count == 1:
        return "📁 1 guardada"
    return f"📁 {count} guardadas"


def format_idea_list(ideas: list[dict[str, Any]]) -> str:
    """Format a list of idea dicts as a human-readable string.

    Each idea occupies 2–4 lines: ID | created_at | categoria, then the text.

    Args:
        ideas: List of idea dicts with keys: id, created_at, updated_at,
               idea, categoria, contexto, confirmada_por_usuario, origen,
               origen_skill.

    Returns:
        Formatted multi-line string, or a "no ideas" message for empty list.
    """
    if not ideas:
        return (
            "No tenés ideas guardadas todavía. "
            "Usá /guardar para guardar tu primera idea."
        )

    lines: list[str] = []
    for idea in ideas:
        idea_id = idea.get("id", "?")
        created = idea.get("created_at", "?")
        categoria = idea.get("categoria") or "sin categoría"
        texto = idea.get("idea", "")
        if len(texto) > 200:
            texto = texto[:200] + "…"
        lines.append(f"#{idea_id} | {created} | {categoria}")
        lines.append(f"> {texto}")
        lines.append("")

    return "\n".join(lines).rstrip("\n")


def format_save_confirmation(
    idea: dict[str, Any],
    count: int,
    contador_activo: bool = True,
) -> str:
    """Format a save confirmation message.

    Args:
        idea: The saved idea dict (must contain 'id' and 'idea' keys).
        count: Total number of ideas after this save.
        contador_activo: Whether to append the counter line.

    Returns:
        Confirmation string, e.g.
        "✅ Idea #1 guardada: probar kumquat…\n📁 1 guardada"
    """
    idea_id = idea.get("id", "?")
    texto = idea.get("idea", "")
    preview = (texto[:80] + "…") if len(texto) > 80 else texto
    msg = f"✅ Idea #{idea_id} guardada: {preview}"
    if contador_activo:
        counter_str = format_counter(count)
        if counter_str:
            msg += f"\n{counter_str}"
    return msg


def format_error(msg: str) -> str:
    """Format an error message with the standard warning prefix.

    Args:
        msg: The error description.

    Returns:
        "⚠️ {msg}"
    """
    return f"⚠️ {msg}"


def format_duplicate_warning(dup: dict[str, Any]) -> str:
    """Format a duplicate warning message.

    Args:
        dup: The existing duplicate idea dict (must contain 'id' and 'idea').

    Returns:
        Warning with preview of the existing idea and prompt to /guardar igual.
    """
    dup_id = dup.get("id", "?")
    texto = dup.get("idea", "")
    preview = (texto[:80] + "…") if len(texto) > 80 else texto
    return (
        f"⚠️ Ya tenés algo parecido (#{dup_id}): {preview}\n"
        "¿Usar /guardar igual para guardar de todas formas?"
    )
