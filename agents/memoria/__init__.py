"""
agents/memoria — Módulo de Memoria (Archivo de Ideas)

Proporciona persistencia local para ideas del usuario con almacenamiento
durable en SQLite. Los comandos se añaden en PR 2 (commands.py).

PR 1 exports:
  - storage functions (init_db, save_idea, load_ideas, etc.)
  - formatters (format_counter, format_idea_list, etc.)
"""

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
from agents.memoria.commands import handle_command, get_contador_state, toggle_contador_state
from agents.memoria import formatters

__all__ = [
    # storage
    "init_db",
    "save_idea",
    "load_ideas",
    "get_idea",
    "edit_idea",
    "delete_idea",
    "delete_all_ideas",
    "count_ideas",
    "export_ideas",
    "check_duplicate",
    # commands
    "handle_command",
    "get_contador_state",
    "toggle_contador_state",
    # formatters module
    "formatters",
]
