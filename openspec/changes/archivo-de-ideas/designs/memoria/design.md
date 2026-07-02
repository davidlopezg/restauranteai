# Design — Módulo de Memoria (Archivo de Ideas)

> **Change**: `archivo-de-ideas`
> **Phase**: `sdd-design`
> **Status**: 🟢 Escrito — listo para `sdd-tasks`
> **Creado**: 2026-07-02
> **Dominio**: `memoria`
> **Base**: `proposal.md` → `spec.md` (decisiones lockeadas D1–D6, Q1–Q5, N1–N5 resueltas en spec)

---

## 1. Module Architecture

### 1.1 Dependency graph

```
                    ┌─────────────────────────┐
                    │     formatters.py        │
                    │  (pure functions, no IO) │
                    └──────────┬──────────────┘
                               │ imported by
                               ▼
                    ┌─────────────────────────┐
                    │     commands.py          │
                    │  (message parsing,       │
                    │   dispatching,           │
                    │   contador state)        │
                    └──────────┬──────────────┘
                               │ imported by
                    ┌──────────▼──────────────┐
                    │     storage.py           │
                    │  (SQLite CRUD,           │
                    │   duplicate detection,   │
                    │   WAL mode)              │
                    └──────────┬──────────────┘
                               │ called by
                    ┌──────────▼──────────────┐
                    │ app.py :: responder()   │
                    │ agents/creativo/        │
                    │  agent.py :: _loop_*()  │
                    └─────────────────────────┘
```

### 1.2 Module responsibilities

| Module | Responsibility | Side effects | Testability |
|---|---|---|---|
| `storage.py` | SQLite CRUD, init_db, duplicate detection (exact + fuzzy), export, count | ✅ Writes to `.agent_knowledge/ideas.db` | Parameterized `conn: sqlite3.Connection` — test with `tmp_path` |
| `commands.py` | Parse command prefix `/`, dispatch to storage, manage contador state | ✅ Read/write DB via conn; ✅ mutable contador state (in-memory dict) | Accepts `conn`, `ultimo_assistant_mensaje`, `skill_activa` explicitly |
| `formatters.py` | Format confirmation, error, list, counter, duplicate warning strings | ❌ Zero side effects. Pure string functions. | Direct assert on output strings |

### 1.3 Storage layer design (`storage.py`)

```python
# storage.py — Design sketch
import sqlite3
import difflib
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

_DEFAULT_DB_PATH = Path(".agent_knowledge/ideas.db")

class StorageError(Exception):
    """Custom exception for storage-layer failures."""
    pass

def init_db(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """
    Create .agent_knowledge/ dir if needed.
    Open connection with check_same_thread=False, timeout=5.0.
    PRAGMA journal_mode=WAL, foreign_keys=ON.
    CREATE TABLE IF NOT EXISTS ideas (schema D2).
    CREATE INDEX IF NOT EXISTS idx_ideas_created_at, _categoria, _origen_skill.
    """

def save_idea(conn, idea, categoria=None, contexto=None,
              origen="comando", origen_skill=None) -> int:
    """INSERT with created_at=utcnow.isoformat(), confirmada_por_usuario=1."""

def load_ideas(conn, filtro=None) -> list[dict]:
    """SELECT * ORDER BY created_at DESC. Optional filter dict."""

def get_idea(conn, idea_id) -> Optional[dict]:
    """SELECT by id. Returns None if not found."""

def edit_idea(conn, idea_id, nuevo_texto, nueva_categoria=None) -> bool:
    """UPDATE idea, updated_at. Returns True if rowcount > 0."""

def delete_idea(conn, idea_id) -> bool:
    """DELETE by id. Returns True if rowcount > 0."""

def delete_all_ideas(conn) -> int:
    """DELETE FROM ideas. Returns rowcount."""

def count_ideas(conn) -> int:
    """SELECT COUNT(*)."""

def export_ideas(conn, export_path=None) -> Path:
    """SELECT * → JSON → .agent_knowledge/ideas_export_<timestamp>.json."""

def check_duplicate(conn, texto, umbral=0.8) -> list[dict]:
    """
    1. Exact match (COLLATE NOCASE).
    2. Fuzzy: load all, difflib.SequenceMatcher.ratio() >= umbral.
    Returns list of duplicate ideas (empty if none).
    """
```

### 1.4 Commands layer design (`commands.py`)

```python
# commands.py — Design sketch
from typing import Optional
import re

# In-memory contador state (thread-safe via Lock)
_contador_activo = True
_contador_lock = __import__("threading").Lock()

def handle_command(mensaje, ultimo_assistant_mensaje=None,
                   skill_activa="ficha", conn=None,
                   contador_activo=True) -> Optional[dict]:
    """
    If mensaje starts with '/', parse and delegate.
    Returns dict {role, content} for matched commands, None otherwise.
    If conn is None, opens/closes a temporary connection.
    """

def get_contador_state() -> bool: ...
def toggle_contador_state() -> bool: ...
```

**Command parsing table** (regex patterns):

| Command | Pattern | Handler |
|---|---|---|
| `/guardar [texto]` | `r"^/guardar\s+(.+)"` | `save_idea(conn, texto, ...)` |
| `/guardar` | `r"^/guardar$"` | Use `ultimo_assistant_mensaje` as idea |
| `/guardar N` | `r"^/guardar\s+(\d+)$"` | Parse N from numbered list in `ultimo_assistant_mensaje` |
| `/editar N [texto]` | `r"^/editar\s+(\d+)\s+(.+)"` | `edit_idea(conn, N, texto)` |
| `/ideas [filtro]` | `r"^/ideas(\s+.+)?"` | `load_ideas(conn, filtro)` |
| `/olvidar todo` | `r"^/olvidar\s+todo$"` | Request confirmation |
| `/olvidar N` | `r"^/olvidar\s+(\d+)$"` | Request confirmation for single |
| `/export-ideas` | `r"^/export-ideas$"` | `export_ideas(conn)` |
| `/silenciar-contador` | `r"^/silenciar-contador$"` | `toggle_contador_state()` |
| `/ayuda` | `r"^/ayuda$"` | Show help text |

### 1.5 Formatters layer design (`formatters.py`)

```python
# formatters.py — Design sketch (pure functions)

def format_save_confirmation(idea, count, contador_activo=True) -> str: ...
def format_idea_list(ideas) -> str: ...
def format_error(msg) -> str: ...
def format_duplicate_warning(dup) -> str: ...
def format_counter(count) -> str: ...
```

All functions take primitives/dicts and return strings. Zero IO. Zero side effects.

---

## 2. Key Algorithms

### 2a. Duplicate detection (fuzzy ≥80%)

**Algorithm**:

1. **Exact match**: `SELECT id, idea, ... FROM ideas WHERE idea = ? COLLATE NOCASE`. If found, return immediately with the matching row(s).
2. **Fuzzy match (≥80%)**: If no exact match, load ALL ideas into memory. For each, compute:
   ```python
   ratio = difflib.SequenceMatcher(None, texto_normalized, idea_normalized).ratio()
   ```
   Collect all with `ratio >= 0.80` (where `umbral = 0.8`).
3. Return list of duplicates (or empty list).

**Threshold semantics**: `≥80%` (greater-or-equal). If ratio is exactly 0.80, it triggers. The parameter `umbral=0.8` is the default; tests can override to lower/higher.

**Performance note**: For v1 (<1000 ideas), loading all into memory is acceptable. If the DB grows, future migration to SQLite FTS5 is the recommended path.

### 2b. `/guardar N` parsing — numbered list extraction

**Regex for numbered lines** (multiline mode):

```python
import re
pattern = r"^\s*(\d+)[.)]\s+(.+)"  # matches "1. ", "1) ", "**1.** ", "3. ", "3) "
matches = re.findall(pattern, ultimo_assistant_mensaje, re.MULTILINE)
```

**What counts as a "numbered list"**:
- `1. Texto` (plain number + dot)
- `1) Texto` (plain number + parenthesis)
- `**1.** Texto` (markdown bold number + dot)
- `**1)** Texto` (markdown bold number + parenthesis)
- `1.  Texto` (extra whitespace)
- Lines MUST start with the number (after optional whitespace). Mid-line numbers don't count.

**What does NOT count**:
- Inline text like "en la idea 3 vimos que..."
- Unordered lists (`- item`, `* item`)
- No list at all (just a prose paragraph)

**Error messages** (exact spec from proposal):

| Condition | Message |
|---|---|
| No numbered list found | `"⚠️ el último mensaje no es una lista numerada. Usá /guardar o /guardar [texto]"` |
| N out of range (e.g., `/guardar 7` when max is 4) | `"⚠️ no encontré la idea número 7. El rango válido es 1–4"` |
| No `ultimo_assistant_mensaje` available | `"⚠️ no tengo un mensaje reciente para guardar"` |

### 2c. Transversal dispatcher in `app.py:responder()`

**Exact insertion point** — between input validation and skill dispatch:

```python
def responder(mensaje, historial, skill="ficha"):
    mensaje = (mensaje or "").strip()
    if not mensaje:
        return {"role": "assistant", "content": ""}

    # ── ARCHIVO DE IDEAS: transversal command dispatch ──
    ultimo_assistant = historial[-1]["content"] if historial and historial[-1]["role"] == "assistant" else ""
    try:
        from agents.memoria.commands import handle_command
        from agents.memoria.storage import init_db
        conn = init_db()
        cmd_result = handle_command(mensaje, ultimo_assistant, skill, conn)
        conn.close()
        if cmd_result is not None:
            return cmd_result
    except Exception as e:
        logging.getLogger("chef_creativo").error(f"[memoria] error: {e}")
        return {"role": "assistant",
                "content": f"⚠️ Error interno del archivo de ideas: {str(e)[:200]}"}
    # ── end transversal dispatch ──

    # ── Existing skill dispatch (untouched) ──
    if skill == "proceso_creativo":
        return _responder_proceso_creativo(mensaje)
    if skill == "ideas_creativas":
        return _responder_ideas_creativas(mensaje)
    # default: ficha
    return _responder_ficha(mensaje, historial)
```

**Key design rules**:
- The dispatcher runs BEFORE any skill handler.
- If `handle_command()` returns a dict, we return it (early-return guard).
- If it returns `None`, we fall through to the existing skill switch — handlers are untouched.
- Import is local (inside function) to avoid circular imports at module level.
- `conn.close()` after each dispatch: connections are created per request, not cached.
- Exception safety net catches anything from the memoria module without breaking the main flow.

### 2d. Transversal dispatcher in CLI `_loop_*`

**Pattern** (identical logic adapted for CLI):

```python
def _loop_ficha(self, skills):
    # ... existing setup ...
    ultimo_assistant = None  # CLI state variable for last assistant response
    while True:
        mensaje = input("➤ ").strip()
        if not mensaje:
            continue
        if mensaje.lower() in ("salir", "exit", "quit"):
            return None

        # ── ARCHIVO DE IDEAS: transversal command dispatch ──
        try:
            from agents.memoria.commands import handle_command
            from agents.memoria.storage import init_db
            conn = init_db()
            cmd_result = handle_command(mensaje, ultimo_assistant, skill_key, conn)
            conn.close()
            if cmd_result is not None:
                print("\n" + cmd_result["content"] + "\n")
                continue  # back to the loop, same skill
        except Exception as e:
            print(f"\n⚠️ Error interno del archivo de ideas: {e}\n")
            continue
        # ── end transversal dispatch ──

        # ... existing handler ...
```

**Integration with `PROCESO_COMANDOS`**: The comandos from memoria (`/guardar`, `/ideas`, `/olvidar`, etc.) must be added to the `PROCESO_COMANDOS` set in `agent.py` so the CLI dispatcher doesn't attempt to interpret them as skill-specific commands:

```python
PROCESO_COMANDOS: set[str] = {
    "/estado", "/volver", "/ficha", "/reiniciar", "/salir",
    # ── Archivo de Ideas ──
    "/guardar", "/guardar ", "/ideas", "/editar",
    "/olvidar", "/olvidar ",
    "/export-ideas", "/silenciar-contador", "/ayuda",
}
```

Note: both `/guardar` (exact, no args) and `/guardar ` (with args) are added to prevent false matching in the process_creativo dispatcher.

**Applied to**: `_loop_ficha()`, `_loop_ideas_creativas()`, `_loop_proceso_creativo()`, and the `main()` CLI entry points for `ideas` and `pc` modes.

---

## 3. Data Flow

### 3.1 `/guardar probar kumquat` (texto libre)

```
User: "/guardar probar kumquat"
  │
  ▼
app.py:responder("/guardar probar kumquat", historial, "ficha")
  │ validate: mensaje non-empty
  │ extract: ultimo_assistant = historial[-1]["content"]
  ▼
commands.handle_command("/guardar probar kumquat", ultimo_assistant=..., skill_activa="ficha", conn=...)
  │ regex match r"^/guardar\s+(.+)" → texto = "probar kumquat"
  │
  ├─→ check_duplicate(conn, "probar kumquat") → []
  │    (no exact match, no fuzzy match ≥80%)
  │
  └─→ save_idea(conn, "probar kumquat", origen="comando", origen_skill="ficha")
       │ INSERT with created_at=utcnow, confirmada_por_usuario=1
       │ return last_insert_rowid → 1
  │
  ▼
formatters.format_save_confirmation({"id": 1, "idea": "probar kumquat", ...}, count=1, contador_activo=True)
  │ → "✅ Idea #1 guardada: probar kumquat\n📁 1 guardada"
  │
  ▼
commands returns {"role": "assistant", "content": "✅ Idea #1 guardada: probar kumquat\n📁 1 guardada"}
  │
  ▼
app.py:responder() returns (early exit, skill handler NOT executed)
```

### 3.2 `/guardar` (sin args) — extract from last assistant message

```
User: "/guardar"
  │
  ▼
app.py:responder("/guardar", historial, "ideas_creativas")
  │ ultimo_assistant = "1. Plato con setas\n2. Fermento de kumquat\n3. Restricción sin gluten"
  │
  ▼
commands.handle_command("/guardar", ultimo_assistant="1. Plato...", skill_activa="ideas_creativas", conn=...)
  │ regex: r"^/guardar$" matches → no args
  │ ultimo_assistant is non-empty → use it as the idea
  │ idea = "1. Plato con setas\n2. Fermento de kumquat\n3. Restricción sin gluten"
  │
  └─→ check_duplicate → save_idea → format_save_confirmation
  │
  ▼
Returns {"role": "assistant", "content": "✅ Idea #5 guardada: 1. Plato con setas\n2. Fermento de kumquat\n3. Restricción sin gluten\n📁 5 guardadas"}
```

### 3.3 `/guardar 3` (numerada)

```
User: "/guardar 3"
  │
  ▼
app.py:responder("/guardar 3", historial, "ficha")
  │ ultimo_assistant = "1. Plato con setas\n2. Fermento de kumquat\n3. Restricción sin gluten\n4. Menú completo 4 pasos"
  │
  ▼
commands.handle_command("/guardar 3", ultimo_assistant=..., skill_activa="ficha", conn=...)
  │ regex: r"^/guardar\s+(\d+)$" → N=3
  │ parse numbered lines from ultimo_assistant:
  │   re.findall(r"^\s*(\d+)[.)]\s+(.+)", ultimo_assistant, re.MULTILINE)
  │   → [(1, "Plato con setas"), (2, "Fermento de kumquat"), (3, "Restricción sin gluten"), (4, "Menú completo 4 pasos")]
  │ N=3 → idea = "Restricción sin gluten"
  │
  └─→ check_duplicate → save_idea → format_save_confirmation
  │
  ▼
Returns {"role": "assistant", "content": "✅ Idea #6 guardada: Restricción sin gluten\n📁 6 guardadas"}
```

### 3.4 `/ideas` (listar)

```
User: "/ideas"
  │
  ▼
commands.handle_command("/ideas", ..., conn=...)
  │ regex r"^/ideas(\s+.+)?" matches
  │ load_ideas(conn) → [dict, dict, ...]
  │
  ▼
formatters.format_idea_list(ideas)
  │ → "#1 | 2026-07-02T10:30:00+00:00 | concepto\n> probar kumquat en el postre\n\n#2 ..."
  │
  ▼
Returns {"role": "assistant", "content": "#1 ..."}
```

### 3.5 `/olvidar todo` with confirmation

```
User: "/olvidar todo"
  │
  ▼
commands.handle_command: matches /olvidar todo
  │ Set pending confirm state (in-memory dict)
  │ Return {"role": "assistant", "content": "⚠️ Escribí `olvidar todo` (sin la /) para confirmar..."}
  │
  ▼ (next turn)
User: "olvidar todo"
  │
  ▼
commands.handle_command: mensaje doesn't start with "/" → return None
  │
  ▼
Skill handler processes "olvidar todo" as normal message (not a command)
  │ → BUT we need to intercept this
```

**Design decision for confirmation flow** (spec N5 resolved):

The confirmation `"olvidar todo"` does NOT start with `/`, so it wouldn't match the command dispatcher. Two approaches:

**Approach A (recommended)**: The confirmation message DOES start with `/`:

```python
User: "/olvidar todo"             → asks confirmation
User: "sí" / "si" / "confirmar"   → confirm (processed by commands.py)
User: anything else                → cancel
```

This requires `commands.py` to maintain a pending-confirmation state. When the user types `/olvidar todo`:
1. Set `_confirmacion_pendiente["accion"] = "olvidar_todo"`
2. Return confirmation prompt
3. On next `handle_command()` call, check if there's a pending confirmation before checking for `/` prefix
4. If pending, check if `mensaje` matches expected confirmation (`"sí"`, `"si"`, `"confirmar"`)

**Approach B (spec as written)**: The confirmation is the literal string `olvidar todo` (without `/`). This means we need to intercept strings that don't start with `/` in `handle_command()` when a confirmation is pending.

**Decision**: Use **Approach B** (as locked in spec section 3.9). The confirmation "olvidar todo" (without `/`) is intercepted by `handle_command()` by checking `_confirmacion_pendiente` BEFORE returning `None`. If there's a pending confirmation and the user types the matching text, process it in `commands.py` without needing a `/` prefix.

```python
def handle_command(mensaje, ...):
    # Check pending confirmations first (even without / prefix)
    if _confirmacion_pendiente and mensaje.strip() == _confirmacion_pendiente["esperando"]:
        # Execute the pending action
        ...
        return {"role": "assistant", "content": ...}
    
    # Normal command detection
    if not mensaje.startswith("/"):
        return None
    ...
```

Same pattern for `/olvidar N` → expect `olvidar N` (without `/`) as confirmation.

---

## 4. State Management

### 4.1 In-memory state (reset on session restart)

| Variable | Type | Default | Purpose | Thread-safe |
|---|---|---|---|---|
| `_contador_activo` | `bool` | `True` | Whether to show counter after save | ✅ `threading.Lock` |
| `_confirmacion_pendiente` | `dict \| None` | `None` | Pending confirmation state: `{"accion": str, "esperando": str}` | ✅ `threading.Lock` |

### 4.2 Persisted state (SQLite — source of truth)

| Table | Purpose |
|---|---|
| `ideas` | All saved ideas, 8 fields + `updated_at` |

### 4.3 What is NOT state

- Categorías precargadas: loaded from `agents/ideas_categorias.json` (file, not state)
- Skill activa: passed as parameter to `handle_command()`, not stored in memoria
- Historial de chat: managed by Gradio/CLI, not by memoria

---

## 5. Concurrency

### 5.1 SQLite configuration

```python
conn = sqlite3.connect(
    str(db_path),
    check_same_thread=False,  # Allow cross-thread access (HF Space)
    timeout=5.0,              # Fail-fast instead of indefinite lock
)
conn.execute("PRAGMA journal_mode=WAL")       # Readers don't block writers
conn.execute("PRAGMA foreign_keys=ON")        # Enforce referential integrity
```

### 5.2 Rationale per setting

| Setting | Why |
|---|---|
| `check_same_thread=False` | Gradio on HF Space can dispatch requests from multiple threads/workers to the same process. Without this, SQLite raises `ProgrammingError`. |
| `timeout=5.0` | If two writes happen simultaneously, the second writer waits up to 5s for the first to finish. If timeout expires, `sqlite3.OperationalError` is raised. |
| `WAL mode` | Writers don't block readers. Critical for HF Space where one user reads while another writes. WAL also provides better crash recovery. |

### 5.3 Connection management

- **`app.py`**: Open connection per request in `responder()`, close after dispatch.
- **CLI `_loop_*`**: Open connection per command iteration, close after command processing.
- **Tests**: Fixture creates `tmp_path` connection, test functions receive `conn` parameter.

### 5.4 Concurrency test

```python
def test_concurrent_writes(db_conn):
    from concurrent.futures import ThreadPoolExecutor
    def writer(n):
        from agents.memoria.storage import save_idea
        return save_idea(db_conn, f"concurrent idea {n}", origen="test")
    
    with ThreadPoolExecutor(max_workers=4) as pool:
        ids = list(pool.map(writer, range(4)))
    
    assert len(set(ids)) == 4  # All distinct
    assert count_ideas(db_conn) == 4  # All persisted
```

---

## 6. Error Propagation

### 6.1 Exception flow

```
storage.py                          commands.py                         formatters.py
──────────                          ───────────                         ─────────────
StorageError (custom) ──────────►   handle_command() catches            format_error(msg)
sqlite3.OperationalError              │                                    │
  (timeout, locked)                   ├─ StorageError → format_error()   "⚠️ {msg}"
sqlite3.DatabaseError                 ├─ ValueError   → format_error()
  (corrupt DB)                        ├─ PermissionError → format_error()
PermissionError                       └─ sqlite3.*    → format_error()
  (can't write .agent_knowledge/)
ValueError
  (empty idea text)

app.py / agent.py (CLI)               Safety net:
  │                                    Any unhandled Exception from
  ├─ handle_command() returns dict ──► commands.py is caught in the
  │                                    responder() / _loop_* catch block.
  └─ Exception ─────────────────────► Logged. Returns generic error message.
```

### 6.2 Error message catalog

| Condition | Source | Handler | User message |
|---|---|---|---|
| DB locked >5s | `storage.py` | `commands.py` | `"⚠️ La base de datos está ocupada. Intentá de nuevo en unos segundos."` |
| DB corrupt | `storage.py` | `commands.py` | `"⚠️ El archivo ideas.db está corrupto. Exportá el backup manual si existe y borrá el archivo para regenerarlo."` |
| Can't create `.agent_knowledge/` | `storage.py` | `commands.py` | `"⚠️ No tengo permisos para crear el archivo de ideas. Verificá los permisos del directorio."` |
| Empty idea text | `storage.py` | `commands.py` | `"⚠️ especificá qué querés guardar"` |
| `/editar N` with N not found | `commands.py` | — | `"⚠️ no existe ninguna idea con ID {N}"` |
| `/olvidar N` with N not found | `commands.py` | — | `"⚠️ no existe ninguna idea con ID {N}"` |
| `/guardar N` no numbered list | `commands.py` | — | `"⚠️ el último mensaje no es una lista numerada. Usá /guardar o /guardar [texto]"` |
| `/guardar N` out of range | `commands.py` | — | `"⚠️ no encontré la idea número {N}. El rango válido es 1–{total}"` |
| `/guardar` no historial | `commands.py` | — | `"⚠️ no tengo un mensaje reciente para guardar"` |
| Comando desconocido | `commands.py` | — | `"⚠️ Comando no reconocido. Escribí /ayuda para ver los comandos disponibles."` |
| Export path unwritable | `storage.py` | `commands.py` | `"⚠️ No pude exportar: {error}. Intentá de nuevo."` |
| Unhandled exception | `app.py` / CLI | safety net | `"⚠️ Error interno del archivo de ideas: {error}"` |

---

## 7. Integration Code Sketch

### 7.1 `app.py:responder()` — full modified function

```python
def responder(mensaje: str, historial: list, skill: str = "ficha") -> dict:
    mensaje = (mensaje or "").strip()
    if not mensaje:
        return {"role": "assistant", "content": ""}

    timestamp = datetime.now().strftime("%H:%M:%S")
    logger.info(f"[{timestamp}] Nueva petición (skill={skill}, len={len(mensaje)})")

    # ────────────────────────────────────────────────────────────────────
    # ARCHIVO DE IDEAS: transversal command dispatch (added in v1)
    # ────────────────────────────────────────────────────────────────────
    ultimo_assistant = (
        historial[-1]["content"]
        if historial and historial[-1]["role"] == "assistant"
        else ""
    )
    try:
        from agents.memoria.commands import handle_command
        from agents.memoria.storage import init_db

        conn = init_db()
        try:
            cmd_result = handle_command(mensaje, ultimo_assistant, skill, conn)
        finally:
            conn.close()

        if cmd_result is not None:
            return cmd_result
    except Exception as e:
        tipo = type(e).__name__
        logger.error(f"[{timestamp}] Error en archivo de ideas: {tipo}: {e}")
        return {
            "role": "assistant",
            "content": f"⚠️ Error interno del archivo de ideas ({tipo}). "
                       f"El chat sigue funcionando normalmente."
        }
    # ── end ARCHIVO DE IDEAS ──

    # ── Existing skill dispatch (UNTOUCHED) ──
    if skill == "proceso_creativo":
        return _responder_proceso_creativo(mensaje)
    if skill == "ideas_creativas":
        return _responder_ideas_creativas(mensaje)
    # default: ficha
    return _responder_ficha(mensaje, historial)
```

### 7.2 `agents/creativo/agent.py` — CLI `_loop_ficha` transversal

```python
def _loop_ficha(skills):
    # ... existing setup ...
    ultimo_assistant = None  # NEW: track last assistant response
    
    while True:
        peticion = input("➤ ").strip()
        if not peticion:
            continue
        if peticion.lower() in ("salir", "exit", "quit"):
            return None

        # ── ARCHIVO DE IDEAS: transversal command dispatch ──
        try:
            from agents.memoria.commands import handle_command
            from agents.memoria.storage import init_db
            conn = init_db()
            try:
                cmd_result = handle_command(peticion, ultimo_assistant, "ficha", conn)
            finally:
                conn.close()
            if cmd_result is not None:
                print("\n" + cmd_result["content"] + "\n")
                print("-" * 60 + "\n")
                continue  # back to loop
        except Exception as e:
            print(f"\n⚠️ Error en archivo de ideas: {e}\n")
            continue
        # ── end ARCHIVO DE IDEAS ──

        # ... existing skill handler ...
        try:
            ficha = generar_ficha(peticion, skill_key="ficha")
            print("\n" + ficha + "\n")
            ultimo_assistant = ficha  # NEW: track for next /guardar
            print("-" * 60 + "\n")
        except Exception as e:
            print(f"\n❌ Error: {e}\n", file=sys.stderr)
```

### 7.3 `PROCESO_COMANDOS` update

```python
PROCESO_COMANDOS: set[str] = {
    "/estado", "/volver", "/ficha", "/reiniciar", "/salir",
    # Archivo de Ideas
    "/guardar", "/guardar ",
    "/ideas", "/ideas ",
    "/editar",
    "/olvidar", "/olvidar ",
    "/export-ideas",
    "/silenciar-contador",
    "/ayuda",
}
```

### 7.4 `agents/ideas_categorias.json`

```json
[
    "concepto",
    "plato",
    "técnica",
    "producto",
    "proveedor",
    "menú completo",
    "ocasión/evento",
    "restricción",
    "otro (escribir)"
]
```

### 7.5 `.agent_knowledge/ideas.md` companion (auto-generated)

Schema documentation companion file, created by `init_db()` if it doesn't exist. Content documents the `ideas` table schema with field descriptions, similar to `restaurante.md`.

---

## 8. Implementation Order (for tasks.md)

| Step | File(s) | Dependencies | Risk | Mitigation |
|---|---|---|---|---|
| **1** | `agents/memoria/__init__.py`, `agents/memoria/storage.py` | None | SQLite schema may need future migration | Keep to 8+updated_at fields, no FK constraints on categoria |
| **2** | `agents/memoria/formatters.py` | None (pure functions) | Minimal risk | Test with direct assert |
| **3** | `agents/memoria/commands.py` | Step 1, 2 | Numbered list parsing may be fragile | Use regex `r"^\s*(\d+)[.)]\s+(.+)"` with MULTILINE; test edge cases |
| **4** | `agents/ideas_categorias.json` | None | Tiny file | — |
| **5** | `app.py` (transversal dispatcher) | Step 3 | Accidental breakage of existing handlers | Early-return guard pattern; tests C11-C12 verify no regression |
| **6** | `agents/creativo/agent.py` (CLI loops + PROCESO_COMANDOS) | Step 3 | Missed a loop variant | Apply to all 3 loops + main() ideas/pc modes |
| **7** | Tests (storage → commands → formatters → regression → rgpd → counter → concurrency) | Steps 1-6 | TDD order: test each module as implemented | Write tests in same order as steps 1-6 |

---

## 9. Risks Per Implementation Step

| Step | Risk | Severity | Mitigation |
|---|---|---|---|
| **1** (storage.py) | SQLite schema rigid — adding columns later requires ALTER TABLE | 🟡 MEDIO | Schema designed with 8+updated_at fields, nullable categoria, no FK constraints. ALTER TABLE ADD COLUMN is safe in SQLite. |
| **3** (commands.py) | Numbered list parsing with regex may miss edge cases (e.g., `N.` with unicode spaces, inline code blocks) | 🟡 MEDIO | Regex `r"^\s*(\d+)[.)]\s+(.+)"` with `re.MULTILINE`. Test mix of formats. If regex fails, fallback: return clear error message suggesting `/guardar` or `/guardar [texto]`. |
| **3** (commands.py) | Confirmation state for `/olvidar` — pending state lost on app restart | 🟢 BAJO | Acceptable: user just re-issues `/olvidar todo`. |
| **5** (app.py) | Import of `agents.memoria` at top level creates circular import | 🟡 MEDIO | **Local import inside `responder()`** avoids module-level circular deps. |
| **5** (app.py) | `conn.close()` in try/finally may still be called if `handle_command` raises | 🟢 BAJO | Already handled by try/finally pattern in code sketch. |
| **6** (agent.py CLI) | Forgetting to update `_loop_ideas_creativas` or `_loop_proceso_creativo` | 🟡 MEDIO | Apply same pattern to all 3 loops + main() entry points. Code review gate. |
| **7** (tests) | Concurrent write test (C15) may be flaky in CI due to timing | 🟡 MEDIO | Use `ThreadPoolExecutor` with small work set (4 writers). Assert on `count_ideas()` and distinct IDs, not on timing. |

---

## 10. Variables de entorno

| Variable | Effect | Default | Introduced in |
|---|---|---|---|
| `ARCHIVO_IDEAS_ENABLED=0` | Dispatcheador de comandos no responde. El módulo sigue instalado pero inerte. | `1` (activado) | Step 5 (app.py) |

Implementation: check at the start of `handle_command()`:

```python
import os
if os.environ.get("ARCHIVO_IDEAS_ENABLED", "1") != "1":
    return None  # Disabled: pretend it's not a command
```

---

## 11. Decisiones de diseño (N-resolved)

| ID | Item | Decisión | Rational |
|---|---|---|---|
| N1 | Comando de edición | **`/editar N [nuevo texto]`** | Consistent with `/olvidar N`. Familiar CLI convention. |
| N2 | Multi-tenant HF Space | **v1 asume single-user local**. Documentado en `ideas.md`. | David es el único usuario del Space hoy. Si se expone a público, migrar a `ideas_<user_hash>.db`. |
| N3 | Categorías precargadas | `["concepto", "plato", "técnica", "producto", "proveedor", "menú completo", "ocasión/evento", "restricción", "otro (escribir)"]` | Validado en sesión de spec. |
| N4 | Formato del contador | `"📁 X guardadas"` (con singular/plural: `1 guardada`, `5 guardadas`) | Propuesto y validado. |
| N5 | Confirmación de `/olvidar todo` | El usuario escribe exactamente `olvidar todo` (sin `/`) para confirmar. | Spec 3.8-3.9. Se intercepta en `commands.py` mediante estado pendiente. |
| — | Conexión DB por request | Se abre y cierra conexión SQLite en cada `responder()` / `_loop_*` iteración. | Simple, thread-safe, sin cache de conexión que pueda quedar stale. |

---

## 12. Archivos a crear/modificar (resumen)

### Crear

| Archivo | Líneas est. |
|---|---|
| `agents/memoria/__init__.py` | ~10 |
| `agents/memoria/storage.py` | ~200 |
| `agents/memoria/commands.py` | ~250 |
| `agents/memoria/formatters.py` | ~80 |
| `agents/ideas_categorias.json` | ~15 |
| `tests/test_memoria_storage.py` | ~150 |
| `tests/test_memoria_commands.py` | ~200 |
| `tests/test_memoria_duplicates.py` | ~80 |
| `tests/test_memoria_counter.py` | ~60 |
| `tests/test_memoria_rgpd.py` | ~80 |
| `tests/test_memoria_concurrency.py` | ~50 |
| `tests/test_regresion_skills.py` | ~120 |

### Modificar

| Archivo | Cambio | Líneas |
|---|---|---|
| `app.py` | Dispatcher transversal en `responder()` | ~20 |
| `agents/creativo/agent.py` | Dispatcher en 3 `_loop_*` + `PROCESO_COMANDOS` | ~60 |

---

## 13. Resultado de fase

```yaml
status: design-complete
artifacts:
  - openspec/changes/archivo-de-ideas/designs/memoria/design.md  (este archivo)
next_recommended: sdd-tasks
locked_decisions:
  - D1–D6, Q1–Q5 (from proposal)
  - N1: /editar N [texto]
  - N2: v1 single-user, documentado
  - N3: categorías en JSON
  - N4: "📁 X guardadas"
  - N5: "olvidar todo" sin / como confirmación
risks:
  - R3: concurrencia SQLite (MEDIO, WAL + timeout + test)
  - R4: rigidez schema (MEDIO, JSON editable + campo libre)
  - R5: comandos olvidados (MEDIO, /ayuda)
  - R6: regresión MVP-0.5 (BAJO, cambios aditivos + tests)
  - RegEx numbered list parsing (MEDIO, fallback a error claro)
skill_resolution: none
```
