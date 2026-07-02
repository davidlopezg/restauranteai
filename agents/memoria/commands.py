"""
commands.py — Command parsing, dispatch, and state for the Archivo de Ideas.

Provides handle_command() which parses slash-commands, dispatches to storage
and formatters, and returns chat-ready response dicts.

In-memory state:
  - _confirmacion_pendiente: pending confirmation for destructive operations
    (olvidar todo, olvidar N, guardar igual after duplicate warning).
  - _contador_activo: whether to show the ideas counter after saves.
  - _lock: threading.Lock for thread-safe access to both.
"""

from __future__ import annotations

import os
import re
import threading
from typing import Any, Optional

from agents.memoria.storage import (
    init_db,
    save_idea,
    load_ideas,
    get_idea,
    edit_idea,
    delete_idea,
    delete_all_ideas,
    count_ideas,
    export_ideas,
    check_duplicate,
)
from agents.memoria.formatters import (
    format_counter,
    format_idea_list,
    format_save_confirmation,
    format_error,
    format_duplicate_warning,
)

# ── Module-level state (thread-safe) ──────────────────────────────────────

_confirmacion_pendiente: dict[str, Any] | None = None
_contador_activo: bool = True
_lock = threading.Lock()


def get_contador_state() -> bool:
    """Return whether the ideas counter is currently active (default: True).

    Thread-safe.
    """
    with _lock:
        return _contador_activo


def toggle_contador_state() -> bool:
    """Toggle the ideas counter state.

    Thread-safe. Returns the *new* state.
    """
    global _contador_activo
    with _lock:
        _contador_activo = not _contador_activo
        return _contador_activo


def _reset_state() -> None:
    """Reset all module-level state (for testing only)."""
    global _confirmacion_pendiente, _contador_activo
    with _lock:
        _confirmacion_pendiente = None
        _contador_activo = True


# ── Pending confirmation helpers ───────────────────────────────────────────


def _set_pending(data: dict[str, Any] | None) -> None:
    """Set the pending confirmation state (thread-safe)."""
    global _confirmacion_pendiente
    with _lock:
        _confirmacion_pendiente = data


def _get_pending() -> dict[str, Any] | None:
    """Return a copy of the pending confirmation state (thread-safe)."""
    with _lock:
        if _confirmacion_pendiente is None:
            return None
        return dict(_confirmacion_pendiente)


def _clear_pending() -> None:
    """Clear the pending confirmation state (thread-safe)."""
    global _confirmacion_pendiente
    with _lock:
        _confirmacion_pendiente = None


# ── Connection helper ──────────────────────────────────────────────────────


def _resolve_conn(conn: Any) -> tuple[Any, bool]:
    """Return (connection, owned) where owned=True if we created it.

    If conn is None, create a temporary connection and mark it owned so
    the caller knows to close it.
    """
    if conn is not None:
        return conn, False
    return init_db(), True


# ── Numbered list extraction ──────────────────────────────────────────────


_NUMBERED_LINE_RE = re.compile(r"^\s*(\d+)[.)]\s+(.+)", re.MULTILINE)


def _extract_numbered_lines(text: str) -> list[tuple[int, str]]:
    """Extract numbered lines from a text block.

    Returns a list of (number, content) tuples in document order.
    """
    matches = _NUMBERED_LINE_RE.findall(text)
    return [(int(num), content.strip()) for num, content in matches]


# ── Command parsing regexes ────────────────────────────────────────────────

_RE_GUARDAR_IGUAL = re.compile(r"^/guardar\s+igual$", re.IGNORECASE)
_RE_GUARDAR_NUM = re.compile(r"^/guardar\s+(\d+)$")
_RE_GUARDAR_SIMPLE = re.compile(r"^/guardar$")
_RE_GUARDAR_TEXTO = re.compile(r"^/guardar\s+(.+)$")
_RE_EDITAR = re.compile(r"^/editar\s+(\d+)\s+(.+)$")
_RE_IDEAS = re.compile(r"^/ideas(\s+.+)?$")
_RE_OLVIDAR_TODO = re.compile(r"^/olvidar\s+todo$")
_RE_OLVIDAR_N = re.compile(r"^/olvidar\s+(\d+)$")
_RE_EXPORT = re.compile(r"^/export-ideas$")
_RE_SILENCIAR = re.compile(r"^/silenciar-contador$")
_RE_AYUDA = re.compile(r"^/ayuda$")

# Confirmation responses (without /)
_RE_CONFIRMAR_TODO = re.compile(r"^olvidar\s+todo$", re.IGNORECASE)
_RE_CONFIRMAR_N = re.compile(r"^olvidar\s+(\d+)$", re.IGNORECASE)

# ── Help text ──────────────────────────────────────────────────────────────

_AYUDA_TEXTO = """**Comandos disponibles:**

`/guardar [texto]` — Guardá una idea nueva.
`/guardar` — Guardá el último mensaje del asistente.
`/guardar N` — Guardá la idea número N de una lista numerada.
`/guardar igual` — Guardá igual si hay advertencia de duplicado.
`/editar N [nuevo texto]` — Editá una idea guardada.
`/ideas [filtro]` — Listá tus ideas guardadas.
`/olvidar todo` — Borrar TODAS las ideas (requiere confirmación).
`/olvidar N` — Borrar una idea específica (requiere confirmación).
`/export-ideas` — Exportá tus ideas a un archivo JSON.
`/silenciar-contador` — Activá o desactivá el contador al guardar.
`/ayuda` — Mostrá esta lista de comandos."""


# ── Main dispatch ─────────────────────────────────────────────────────────


def handle_command(
    mensaje: str,
    ultimo_assistant_mensaje: Optional[str] = None,
    skill_activa: str = "ficha",
    conn: Any = None,
    contador_activo: bool = True,
) -> Optional[dict[str, str]]:
    """Parse and execute a command, returning a chat response or None.

    Args:
        mensaje: The user's raw message.
        ultimo_assistant_mensaje: The last assistant response text, used by
            ``/guardar`` (no args) and ``/guardar N``.
        skill_activa: The currently active skill name. Default ``"ficha"``.
        conn: An open SQLite connection. If None, a temporary connection
            is created and closed after the command.
        contador_activo: Whether the counter feature is enabled for this call.
            When True (default), the global counter state is also checked.

    Returns:
        A dict ``{"role": "assistant", "content": str}`` if the message was
        a recognized command (or confirmation), or ``None`` if the message
        should pass through to the skill handler.
    """
    # ── Guard: module disabled via env var ──
    if os.environ.get("ARCHIVO_IDEAS_ENABLED", "1") == "0":
        return None

    mensaje_stripped = mensaje.strip()

    # ── Check pending confirmations ──
    pending = _get_pending()

    if pending is not None:
        # --- Pending "olvidar todo" ---
        if pending["type"] == "olvidar_todo":
            if _RE_CONFIRMAR_TODO.match(mensaje_stripped):
                _clear_pending()
                resolved_conn, owned = _resolve_conn(conn)
                try:
                    count = delete_all_ideas(resolved_conn)
                finally:
                    if owned:
                        resolved_conn.close()
                return {
                    "role": "assistant",
                    "content": f"✅ Archivo de ideas borrado. Se eliminaron {count} ideas.",
                }
            # else: ignore, fall through — user must re-issue /olvidar

        # --- Pending "olvidar N" ---
        if pending["type"] == "olvidar_n":
            confirm_match = _RE_CONFIRMAR_N.match(mensaje_stripped)
            if confirm_match and int(confirm_match.group(1)) == pending["id"]:
                _clear_pending()
                resolved_conn, owned = _resolve_conn(conn)
                try:
                    deleted = delete_idea(resolved_conn, pending["id"])
                finally:
                    if owned:
                        resolved_conn.close()
                if deleted:
                    return {
                        "role": "assistant",
                        "content": f"✅ Idea #{pending['id']} borrada.",
                    }
                # Shouldn't happen if we verified existence, but handle gracefully
                return {
                    "role": "assistant",
                    "content": format_error(
                        f"ocurrió un error al borrar la idea #{pending['id']}."
                    ),
                }
            # else: ignore, fall through

        # --- Pending "guardar igual" ---
        if pending["type"] == "guardar_duplicate":
            if _RE_GUARDAR_IGUAL.match(mensaje_stripped):
                _clear_pending()
                resolved_conn, owned = _resolve_conn(conn)
                try:
                    idea_id = save_idea(
                        resolved_conn,
                        pending["texto"],
                        categoria=pending.get("categoria"),
                        contexto=pending.get("contexto"),
                        origen_skill=pending.get("origen_skill", skill_activa),
                    )
                    saved_idea_dict = get_idea(resolved_conn, idea_id)
                    total = count_ideas(resolved_conn)
                finally:
                    if owned:
                        resolved_conn.close()

                if saved_idea_dict is None:
                    return {
                        "role": "assistant",
                        "content": format_error("error al guardar la idea."),
                    }

                show_counter = contador_activo and get_contador_state()
                return {
                    "role": "assistant",
                    "content": format_save_confirmation(
                        saved_idea_dict, total, contador_activo=show_counter
                    ),
                }
            # else: ignore, fall through

    # ── Special: "olvidar todo" / "olvidar N" without pending → error ──
    if _RE_CONFIRMAR_TODO.match(mensaje_stripped) and pending is None:
        return {
            "role": "assistant",
            "content": format_error("No había nada que confirmar."),
        }
    confirm_n = _RE_CONFIRMAR_N.match(mensaje_stripped)
    if confirm_n and pending is None:
        return {
            "role": "assistant",
            "content": format_error("No había nada que confirmar."),
        }

    # ── Not a slash-command → pass through ──
    if not mensaje_stripped.startswith("/"):
        return None

    # ── Parse command using raw message (not stripped) to correctly
    #    distinguish "/guardar" from "/guardar   " ──
    resolved_conn, owned = _resolve_conn(conn)

    try:
        # --- /guardar igual (also handled in pending, but standalone) ---
        if _RE_GUARDAR_IGUAL.match(mensaje):
            return {
                "role": "assistant",
                "content": format_error(
                    "No hay un guardado pendiente para confirmar."
                ),
            }

        # --- /guardar N (numbered) ---
        num_match = _RE_GUARDAR_NUM.match(mensaje)
        if num_match:
            return _handle_guardar_num(
                resolved_conn,
                int(num_match.group(1)),
                ultimo_assistant_mensaje,
                skill_activa,
                contador_activo,
            )

        # --- /guardar (no args, exact match only) ---
        if _RE_GUARDAR_SIMPLE.match(mensaje):
            return _handle_guardar_sin_args(
                resolved_conn,
                ultimo_assistant_mensaje,
                skill_activa,
                contador_activo,
            )

        # --- /guardar [texto] ---
        texto_match = _RE_GUARDAR_TEXTO.match(mensaje)
        if texto_match:
            return _handle_guardar_texto(
                resolved_conn,
                texto_match.group(1).strip(),
                skill_activa,
                contador_activo,
            )

        # --- /editar N [texto] ---
        editar_match = _RE_EDITAR.match(mensaje)
        if editar_match:
            return _handle_editar(
                resolved_conn,
                int(editar_match.group(1)),
                editar_match.group(2).strip(),
            )

        # --- /ideas [filtro] ---
        ideas_match = _RE_IDEAS.match(mensaje)
        if ideas_match:
            filtro_raw = ideas_match.group(1)
            return _handle_ideas(resolved_conn, filtro_raw)

        # --- /olvidar todo ---
        if _RE_OLVIDAR_TODO.match(mensaje):
            _set_pending({"type": "olvidar_todo"})
            return {
                "role": "assistant",
                "content": (
                    "⚠️ Escribí `olvidar todo` (sin la /) "
                    "para confirmar que querés borrar TODAS tus ideas guardadas."
                ),
            }

        # --- /olvidar N ---
        olvidar_n_match = _RE_OLVIDAR_N.match(mensaje)
        if olvidar_n_match:
            idea_id = int(olvidar_n_match.group(1))
            existing = get_idea(resolved_conn, idea_id)
            if existing is None:
                return {
                    "role": "assistant",
                    "content": format_error(
                        f"no existe ninguna idea con ID {idea_id}"
                    ),
                }
            _set_pending({"type": "olvidar_n", "id": idea_id})
            return {
                "role": "assistant",
                "content": (
                    f"⚠️ ¿Estás seguro? Escribí `olvidar {idea_id}` "
                    "(sin la /) para confirmar."
                ),
            }

        # --- /export-ideas ---
        if _RE_EXPORT.match(mensaje):
            return _handle_export(resolved_conn)

        # --- /silenciar-contador ---
        if _RE_SILENCIAR.match(mensaje):
            new_state = toggle_contador_state()
            if new_state:
                return {
                    "role": "assistant",
                    "content": "🔊 Contador reactivado. Se mostrará al guardar ideas.",
                }
            return {
                "role": "assistant",
                "content": "🔇 Contador silenciado. Usá `/silenciar-contador` de nuevo para reactivarlo.",
            }

        # --- /ayuda ---
        if _RE_AYUDA.match(mensaje):
            return {"role": "assistant", "content": _AYUDA_TEXTO}

        # ── Unknown /command ──
        return {
            "role": "assistant",
            "content": format_error(
                "Comando no reconocido. Escribí `/ayuda` para ver los comandos disponibles."
            ),
        }

    finally:
        if owned:
            resolved_conn.close()


# ── Command handlers ───────────────────────────────────────────────────────


def _handle_guardar_texto(
    conn: Any,
    texto: str,
    skill_activa: str,
    contador_activo: bool,
) -> dict[str, str]:
    """Handle ``/guardar [texto]`` — save text with duplicate check."""
    if not texto:
        return {
            "role": "assistant",
            "content": format_error("especificá qué querés guardar"),
        }

    # Check duplicates
    dups = check_duplicate(conn, texto)
    if dups:
        # Store in pending for /guardar igual
        _set_pending({
            "type": "guardar_duplicate",
            "texto": texto,
            "categoria": None,
            "contexto": None,
            "origen_skill": skill_activa,
        })
        return {
            "role": "assistant",
            "content": format_duplicate_warning(dups[0]),
        }

    # No duplicate — save directly
    idea_id = save_idea(
        conn,
        texto,
        categoria=None,
        contexto=None,
        origen_skill=skill_activa,
    )
    saved_idea = get_idea(conn, idea_id)
    if saved_idea is None:
        return {
            "role": "assistant",
            "content": format_error("error al guardar la idea."),
        }

    total = count_ideas(conn)
    show_counter = contador_activo and get_contador_state()
    return {
        "role": "assistant",
        "content": format_save_confirmation(
            saved_idea, total, contador_activo=show_counter
        ),
    }


def _handle_guardar_sin_args(
    conn: Any,
    ultimo_assistant_mensaje: Optional[str],
    skill_activa: str,
    contador_activo: bool,
) -> dict[str, str]:
    """Handle ``/guardar`` (no args) — save last assistant message."""
    if not ultimo_assistant_mensaje or not ultimo_assistant_mensaje.strip():
        return {
            "role": "assistant",
            "content": format_error(
                "no tengo un mensaje reciente para guardar"
            ),
        }

    texto = ultimo_assistant_mensaje.strip()

    # Check duplicates
    dups = check_duplicate(conn, texto)
    if dups:
        _set_pending({
            "type": "guardar_duplicate",
            "texto": texto,
            "categoria": None,
            "contexto": None,
            "origen_skill": skill_activa,
        })
        return {
            "role": "assistant",
            "content": format_duplicate_warning(dups[0]),
        }

    idea_id = save_idea(
        conn,
        texto,
        categoria=None,
        contexto=None,
        origen_skill=skill_activa,
    )
    saved_idea = get_idea(conn, idea_id)
    if saved_idea is None:
        return {
            "role": "assistant",
            "content": format_error("error al guardar la idea."),
        }

    total = count_ideas(conn)
    show_counter = contador_activo and get_contador_state()
    return {
        "role": "assistant",
        "content": format_save_confirmation(
            saved_idea, total, contador_activo=show_counter
        ),
    }


def _handle_guardar_num(
    conn: Any,
    num: int,
    ultimo_assistant_mensaje: Optional[str],
    skill_activa: str,
    contador_activo: bool,
) -> dict[str, str]:
    """Handle ``/guardar N`` — save a numbered line from the last message."""
    if not ultimo_assistant_mensaje or not ultimo_assistant_mensaje.strip():
        return {
            "role": "assistant",
            "content": format_error(
                "el último mensaje no es una lista numerada. "
                "Usá `/guardar` o `/guardar [texto]`"
            ),
        }

    numbered_lines = _extract_numbered_lines(ultimo_assistant_mensaje)
    if not numbered_lines:
        return {
            "role": "assistant",
            "content": format_error(
                "el último mensaje no es una lista numerada. "
                "Usá `/guardar` o `/guardar [texto]`"
            ),
        }

    # Find the entry with matching number (1-indexed)
    found = None
    for line_num, line_text in numbered_lines:
        if line_num == num:
            found = line_text
            break

    if found is None:
        total_items = len(numbered_lines)
        return {
            "role": "assistant",
            "content": format_error(
                f"no encontré la idea número {num}. "
                f"El rango válido es 1–{total_items}"
            ),
        }

    # Check duplicates
    dups = check_duplicate(conn, found)
    if dups:
        _set_pending({
            "type": "guardar_duplicate",
            "texto": found,
            "categoria": None,
            "contexto": None,
            "origen_skill": skill_activa,
        })
        return {
            "role": "assistant",
            "content": format_duplicate_warning(dups[0]),
        }

    idea_id = save_idea(
        conn,
        found,
        categoria=None,
        contexto=None,
        origen_skill=skill_activa,
    )
    saved_idea = get_idea(conn, idea_id)
    if saved_idea is None:
        return {
            "role": "assistant",
            "content": format_error("error al guardar la idea."),
        }

    total = count_ideas(conn)
    show_counter = contador_activo and get_contador_state()
    return {
        "role": "assistant",
        "content": format_save_confirmation(
            saved_idea, total, contador_activo=show_counter
        ),
    }


def _handle_editar(
    conn: Any,
    idea_id: int,
    nuevo_texto: str,
) -> dict[str, str]:
    """Handle ``/editar N [nuevo texto]``."""
    if not nuevo_texto:
        return {
            "role": "assistant",
            "content": format_error(
                "especificá el nuevo texto para la idea"
            ),
        }

    try:
        result = edit_idea(conn, idea_id, nuevo_texto)
    except ValueError as e:
        return {
            "role": "assistant",
            "content": format_error(str(e)),
        }

    if not result:
        return {
            "role": "assistant",
            "content": format_error(
                f"no existe ninguna idea con ID {idea_id}"
            ),
        }

    return {
        "role": "assistant",
        "content": f"✅ Idea #{idea_id} actualizada.",
    }


def _handle_ideas(
    conn: Any,
    filtro_raw: Optional[str],
) -> dict[str, str]:
    """Handle ``/ideas [filtro]``."""
    filtro: dict[str, Any] | None = None
    if filtro_raw:
        filtro_texto = filtro_raw.strip()
        if filtro_texto:
            filtro = {"search": filtro_texto}

    ideas = load_ideas(conn, filtro)
    return {
        "role": "assistant",
        "content": format_idea_list(ideas),
    }


def _handle_export(conn: Any) -> dict[str, str]:
    """Handle ``/export-ideas``."""
    from pathlib import Path
    try:
        export_path = export_ideas(conn)
        total = count_ideas(conn)
        return {
            "role": "assistant",
            "content": (
                f"✅ Exportado a {export_path} ({total} ideas). "
                "Es un archivo local, no se subió a ningún servidor."
            ),
        }
    except (PermissionError, OSError) as e:
        return {
            "role": "assistant",
            "content": format_error(
                f"No pude exportar: {e}. Intentá de nuevo."
            ),
        }
