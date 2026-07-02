# Tasks — Módulo de Memoria (Archivo de Ideas)

> **Change**: `archivo-de-ideas`  
> **Phase**: `sdd-tasks`  
> **Status**: 🟢 Escrito — listo para `sdd-apply`  
> **Creado**: 2026-07-02  
> **Dominio**: `memoria`  

---

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~1,400–1,500 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 (Module Core + Tests) → PR 2 (Commands + Tests) → PR 3 (Integration + Regression) |
| Delivery strategy | auto-chain |
| Chain strategy | stacked-to-main |

```text
Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High
```

## Delivery Strategy

The implementation exceeds the 400-line budget by ~4x. Three chained PRs are recommended:

- **PR 1** (~400–500 lines): Core modules + infrastructure tests
- **PR 2** (~400–500 lines): Commands layer + command/duplicate/counter/rgpd tests
- **PR 3** (~400–500 lines): Integration into `app.py` and `agent.py` + regression and concurrency tests

Each PR must be merged to `main` before the next PR starts. Each PR is self-verifying via its own tests.

---

## PR 1 — Core Modules (storage.py + formatters.py + __init__.py)

### Task 1.1: Create `agents/memoria/` package directory

**Status**: ✅ [x] COMPLETED — PR 1

**Action**: Create directory `agents/memoria/` and `agents/memoria/__init__.py`.

**`__init__.py` content**:
```python
from agents.memoria.storage import init_db, save_idea, load_ideas, get_idea
from agents.memoria.storage import edit_idea, delete_idea, delete_all_ideas
from agents.memoria.storage import count_ideas, export_ideas, check_duplicate
from agents.memoria.commands import handle_command, get_contador_state, toggle_contador_state
from agents.memoria import formatters
```

At this point, `commands` import will fail since it doesn't exist yet — that's fine, it will resolve in PR 2. For PR 1, only export `storage` and `formatters` symbols initially.

**Files**: `agents/memoria/__init__.py` (~10 lines)  
**Dependencies**: None  
**Verification**: File exists, Python can import the empty module tree.

---

### Task 1.2: Implement `agents/memoria/storage.py`

**Status**: ✅ [x] COMPLETED — PR 1

**Action**: Write `storage.py` with the following functions:

- `init_db(db_path=None) -> sqlite3.Connection` — creates `.agent_knowledge/` dir, opens WAL-mode connection, creates `ideas` table and indexes
- `save_idea(conn, idea, categoria=None, contexto=None, origen="comando", origen_skill=None) -> int`
- `load_ideas(conn, filtro=None) -> list[dict]` — supports `categoria`, `origen_skill`, `search` (LIKE), and `limit` filters
- `get_idea(conn, idea_id) -> Optional[dict]`
- `edit_idea(conn, idea_id, nuevo_texto, nueva_categoria=None) -> bool`
- `delete_idea(conn, idea_id) -> bool`
- `delete_all_ideas(conn) -> int`
- `count_ideas(conn) -> int`
- `export_ideas(conn, export_path=None) -> Path`
- `check_duplicate(conn, texto, umbral=0.8) -> list[dict]` — exact match (COLLATE NOCASE) first, then fuzzy via `difflib.SequenceMatcher`

**Schema (D2) for `ideas` table**:
```sql
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
);
CREATE INDEX IF NOT EXISTS idx_ideas_created_at ON ideas(created_at);
CREATE INDEX IF NOT EXISTS idx_ideas_categoria ON ideas(categoria);
CREATE INDEX IF NOT EXISTS idx_ideas_origen_skill ON ideas(origen_skill);
```

**PRAGMAs**: `journal_mode=WAL`, `foreign_keys=ON`.

**Edge cases** (all must raise custom `StorageError` or standard exceptions with specific messages as defined in the spec):
- Empty idea → `ValueError("La idea no puede estar vacía")`
- DB locked >5s → `sqlite3.OperationalError` with user-friendly message
- DB corrupt → `sqlite3.DatabaseError` with recovery instructions
- Directory not writable → `PermissionError` with instructions
- DB empty → empty list `[]`
- ID not found → `None` for `get_idea`, `False` for `delete_idea`
- Negative/zero ID → `None`

**Concurrent safety design**:
- `check_same_thread=False` on connection
- `timeout=5.0` for write lock wait
- Each connection is created per call, not cached

**`.agent_knowledge/ideas.md`**: `init_db()` should also generate this companion doc if it doesn't exist, documenting the schema for David's reference.

**Files**: `agents/memoria/storage.py` (~200 lines)  
**Dependencies**: None (stdlib only: `sqlite3`, `pathlib`, `datetime`, `difflib`, `typing`, `json`)  
**Verification**: `python -c "from agents.memoria.storage import init_db"` succeeds.

---

### Task 1.3: Implement `agents/memoria/formatters.py`

**Status**: ✅ [x] COMPLETED — PR 1

**Action**: Write five pure formatting functions:

| Function | Signature | Behavior |
|---|---|---|
| `format_counter(count)` | `(int) -> str` | `0 → ""`, `1 → "📁 1 guardada"`, `≥2 → "📁 N guardadas"` |
| `format_idea_list(ideas)` | `(list[dict]) -> str` | Each idea: `#{id} \| {created_at} \| {categoria or "sin categoría"}\n> {idea[:200]}{…}` |
| `format_save_confirmation(idea, count, contador_activo)` | `(dict, int, bool) -> str` | `"✅ Idea #{id} guardada: {preview}"` + optional counter |
| `format_error(msg)` | `(str) -> str` | `"⚠️ {msg}"` |
| `format_duplicate_warning(dup)` | `(dict) -> str` | `"⚠️ Ya tenés algo parecido (#{id}): {preview}…\n¿Usar /guardar igual para guardar de todas formas?"` |

**Files**: `agents/memoria/formatters.py` (~80 lines)  
**Dependencies**: None (pure functions, zero IO)  
**Verification**: `python -c "from agents.memoria.formatters import format_counter; print(format_counter(1))"` outputs `"📁 1 guardada"`.

---

### Task 1.4: Create `agents/ideas_categorias.json`

**Status**: ✅ [x] COMPLETED — PR 1

**Action**: Write the categories file.

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

**Files**: `agents/ideas_categorias.json` (~15 lines)  
**Dependencies**: None  
**Verification**: `python -c "import json; json.load(open('agents/ideas_categorias.json'))"` succeeds.

---

### Task 1.5: Write `tests/test_memoria_storage.py` and `tests/test_memoria_formatters.py`

**Status**: ✅ [x] COMPLETED — PR 1

**Action**: Test CRUD operations against a `tmp_path`-backed SQLite, and pure formatter functions.

**Fixture** (in `conftest.py` or inline):
```python
@pytest.fixture
def db_conn(tmp_path):
    from agents.memoria.storage import init_db
    conn = init_db(tmp_path / "test.db")
    yield conn
    conn.close()
```

**Tests** (each function + edge cases):

| Test | What it verifies |
|---|---|
| `test_init_db_creates_dir_and_table` | Directory + table created, pragmas set |
| `test_init_db_idempotent` | Calling twice is safe |
| `test_save_idea_basic` | Returns int ID, row exists |
| `test_save_idea_empty_raises` | `ValueError` for empty string |
| `test_save_idea_with_all_fields` | categoria, contexto, origen_skill stored |
| `test_load_ideas_empty` | Returns `[]` |
| `test_load_ideas_all` | Returns all rows DESC by created_at |
| `test_load_ideas_with_filtro_categoria` | Filter by categoria |
| `test_load_ideas_with_filtro_search` | LIKE %search% on idea |
| `test_load_ideas_with_filtro_limit` | Limit results |
| `test_get_idea_found` | Returns correct dict |
| `test_get_idea_not_found` | Returns `None` |
| `test_get_idea_negative_id` | Returns `None` |
| `test_edit_idea_text` | Updates idea + updated_at, preserves created_at |
| `test_edit_idea_not_found` | Returns `False` |
| `test_edit_idea_empty_text` | Raises `ValueError` |
| `test_delete_idea_found` | Returns `True`, row gone |
| `test_delete_idea_not_found` | Returns `False` |
| `test_delete_all_ideas` | Returns count, all rows gone |
| `test_delete_all_empty` | Returns 0 |
| `test_count_ideas` | Returns correct count |
| `test_count_ideas_empty` | Returns 0 |
| `test_export_ideas_default_path` | Creates file in `.agent_knowledge/` with timestamp |
| `test_export_ideas_custom_path` | Writes to specified path |
| `test_export_ideas_empty_db` | Writes `[]` |
| `test_check_duplicate_exact` | Returns matching row for identical text (case-insensitive) |
| `test_check_duplicate_fuzzy_above_threshold` | Returns matching row for ≥80% similar |
| `test_check_duplicate_fuzzy_below_threshold` | Returns `[]` for <80% |
| `test_check_duplicate_empty_text` | Returns `[]` |
| `test_check_duplicate_empty_db` | Returns `[]` |

**Files**: `tests/test_memoria_storage.py` (~150 lines)  
**Dependencies**: `pytest`  
**Verification**: `python -m pytest tests/test_memoria_storage.py -v` passes all tests.

---

### Task 1.6: Write `tests/test_memoria_concurrency.py`

**Status**: ✅ [x] COMPLETED — PR 2

**Action**: Test concurrent writes with `ThreadPoolExecutor`.

**Tests**:
- `test_concurrent_writes`: 4 threads write simultaneously, all 4 distinct IDs returned, `count = 4`
- `test_concurrent_read_and_write`: One thread writes while another reads, no exception, results consistent

**Files**: `tests/test_memoria_concurrency.py` (~50 lines)  
**Dependencies**: `pytest`, `concurrent.futures`  
**Verification**: `python -m pytest tests/test_memoria_concurrency.py -v` passes.

---

## PR 2 — Commands Layer (commands.py + command tests)

### Task 2.1: Implement `agents/memoria/commands.py`

**Status**: ✅ [x] COMPLETED — PR 2

**Action**: Write the command parsing and dispatching module.

**Key components**:

**`handle_command(mensaje, ultimo_assistant_mensaje=None, skill_activa='ficha', conn=None, contador_activo=True) -> Optional[dict]`**:

1. Check `_confirmacion_pendiente` (in-memory dict) first:
   - If pending `"olvidar todo"` and `mensaje.strip() == "olvidar todo"` → execute `delete_all_ideas()`, return confirmation, clear pending state.
   - If pending `"olvidar N"` and `mensaje.strip() == f"olvidar {N}"` → execute `delete_idea(conn, N)`, return confirmation, clear pending state.
   - If pending but user typed something else → ignore (don't confirm, don't clear — user must re-issue `/olvidar` to start over).
2. If `mensaje` does not start with `/`, return `None`.
3. Parse command regex (see table below).
4. Execute command via `storage.py`, format via `formatters.py`.
5. Return `{"role": "assistant", "content": str}`.

**`get_contador_state() -> bool`** and **`toggle_contador_state() -> bool`**:
- Thread-safe via `threading.Lock`
- Default state: `True` (counter active)

**Command parsing table** (use `re` module):

| Command | Regex | Handler | Errors |
|---|---|---|---|
| `/guardar [texto]` | `r"^/guardar\s+(.+)"` | `check_duplicate` → `save_idea` | Empty → `format_error` |
| `/guardar` (no args) | `r"^/guardar$"` | Use `ultimo_assistant_mensaje` as idea | No historial → `format_error` |
| `/guardar N` (numbered) | `r"^/guardar\s+(\d+)$"` | Parse numbered list from `ultimo_assistant_mensaje`, extract line N | No list / out of range → `format_error` |
| `/guardar igual` | `r"^/guardar\s+igual$"` | Force save (skip duplicate check) | — |
| `/editar N [texto]` | `r"^/editar\s+(\d+)\s+(.+)"` | `edit_idea()` | ID not found / empty text → `format_error` |
| `/ideas [filtro]` | `r"^/ideas(\s+.+)?"` | `load_ideas()` with optional filter | Empty → "No tenés ideas" |
| `/olvidar todo` | `r"^/olvidar\s+todo$"` | Set pending confirmation, return prompt | — |
| `/olvidar N` | `r"^/olvidar\s+(\d+)$"` | Verify ID exists, set pending confirmation | ID not found → `format_error` |
| `/export-ideas` | `r"^/export-ideas$"` | `export_ideas()` | Error → `format_error` |
| `/silenciar-contador` | `r"^/silenciar-contador$"` | `toggle_contador_state()` | — |
| `/ayuda` | `r"^/ayuda$"` | Return formatted help text | — |

**Numbered list extraction** (for `/guardar N`):
```python
pattern = r"^\s*(\d+)[.)]\s+(.+)"
matches = re.findall(pattern, ultimo_assistant_mensaje, re.MULTILINE)
```

**Environment variable**: Check `ARCHIVO_IDEAS_ENABLED` at the start of `handle_command()`. If `"0"`, return `None`.

**In-memory state** (`_confirmacion_pendiente`, `_contador_activo`) — thread-safe via `threading.Lock`.

**Files**: `agents/memoria/commands.py` (~250 lines)  
**Dependencies**: Task 1.2 (`storage.py`), Task 1.3 (`formatters.py`)  
**Verification**: `python -c "from agents.memoria.commands import handle_command; print(handle_command('/ayuda'))"` returns help text.

---

### Task 2.2: Write `tests/test_memoria_commands.py`

**Status**: ✅ [x] COMPLETED — PR 2

**Action**: Test each command variant.

**Tests**:

| Test | Input | Expected |
|---|---|---|
| `test_guardar_texto_libre` | `/guardar probar kumquat` | Confirmation with ID + counter |
| `test_guardar_texto_vacio` | `/guardar ` (empty) | Error: "especificá qué querés guardar" |
| `test_guardar_sin_args_con_historial` | `/guardar` with `ultimo_assistant="una idea genial"` | Saves the historial text |
| `test_guardar_sin_args_sin_historial` | `/guardar` with `ultimo_assistant=None` | Error: "no tengo un mensaje reciente" |
| `test_guardar_numero_valido` | `/guardar 3` with numbered list | Saves line 3 |
| `test_guardar_numero_fuera_rango` | `/guardar 7` with 4-item list | Error: "no encontré la idea número 7" |
| `test_guardar_numero_sin_lista` | `/guardar 1` with prose message | Error: "no es una lista numerada" |
| `test_guardar_numero_formato_mixto` | List with `3)` and `4.` | Both parsed correctly |
| `test_guardar_igual` | `/guardar igual` after duplicate warning | Force save |
| `test_editar_existente` | `/editar 1 nuevo texto` | Confirmation + ideas[1]["idea"] updated |
| `test_editar_inexistente` | `/editar 99 nuevo texto` | Error: "no existe ninguna idea con ID 99" |
| `test_editar_sin_texto` | `/editar 1` | Error: "especificá el nuevo texto" |
| `test_ideas_sin_filtro` | `/ideas` | Formatted list |
| `test_ideas_con_filtro` | `/ideas concepto` (depends on filter parsing) | Filtered list |
| `test_ideas_vacio` | `/ideas` on empty DB | "No tenés ideas guardadas todavía" |
| `test_olvidar_todo_pedido` | `/olvidar todo` | Confirmation prompt, no deletion |
| `test_olvidar_n_pedido` | `/olvidar 1` | Confirmation prompt, no deletion |
| `test_olvidar_n_inexistente` | `/olvidar 99` | Error: "no existe ninguna idea con ID 99" |
| `test_export_ideas` | `/export-ideas` | Confirmation with path |
| `test_ayuda` | `/ayuda` | Lists all commands |
| `test_silenciar_contador` | `/silenciar-contador` | Confirmation + state toggled |
| `test_comando_desconocido` | `/xyz` | Error: "Comando no reconocido" |
| `test_no_comando_retorna_none` | `hola mundo` | `None` (pass through to skill) |

**Files**: `tests/test_memoria_commands.py` (~200 lines)  
**Dependencies**: `pytest`, Task 2.1  
**Verification**: `python -m pytest tests/test_memoria_commands.py -v` passes.

---

### Task 2.3: Write `tests/test_memoria_duplicates.py`

**Status**: ✅ [x] COMPLETED — PR 2

**Action**: Test duplicate detection logic via the command layer.

| Test | Input | Expected |
|---|---|---|
| `test_duplicado_exacto` | Same text as existing idea | Warning with ID + prompt to `/guardar igual` |
| `test_duplicado_fuzzy_sobre_umbral` | 85% similar text | Warning with ID |
| `test_sin_duplicado_fuzzy_bajo_umbral` | 50% similar text | Saves directly without warning |
| `test_duplicado_db_vacia` | Any text on empty DB | Saves directly |

**Files**: `tests/test_memoria_duplicates.py` (~80 lines)  
**Dependencies**: `pytest`, Task 2.1  
**Verification**: `python -m pytest tests/test_memoria_duplicates.py -v` passes.

---

### Task 2.4: Write `tests/test_memoria_counter.py`

**Status**: ✅ [x] COMPLETED — PR 2

**Action**: Test counter state management via commands.

| Test | Input | Expected |
|---|---|---|
| `test_counter_visible_after_save` | `/guardar texto` with `contador_activo=True` | Response includes "📁" counter |
| `test_counter_silenced` | `/silenciar-contador` → `/guardar texto` | Response does NOT include "📁" |
| `test_counter_reactivated` | `/silenciar-contador` (twice) → `/guardar texto` | Response includes "📁" again |
| `test_counter_initial_state` | `get_contador_state()` | `True` |

**Files**: `tests/test_memoria_counter.py` (~60 lines)  
**Dependencies**: `pytest`, Task 2.1  
**Verification**: `python -m pytest tests/test_memoria_counter.py -v` passes.

---

### Task 2.5: Write `tests/test_memoria_rgpd.py`

**Status**: ✅ [x] COMPLETED — PR 2

**Action**: Test confirmation patterns for destructive operations.

| Test | Input | Expected |
|---|---|---|
| `test_olvidar_todo_sin_confirmacion` | `/olvidar todo` then any non-confirming message | No deletion, pending state may be cleared or preserved per spec |
| `test_olvidar_todo_con_confirmacion` | `/olvidar todo` then `olvidar todo` | All ideas deleted, confirmation message |
| `test_olvidar_todo_sin_estado_pendiente` | `olvidar todo` (no prior `/olvidar todo`) | "No había nada que confirmar" |
| `test_olvidar_n_con_confirmacion` | `/olvidar 1` then `olvidar 1` | Idea #1 deleted |
| `test_export_con_ideas` | `/export-ideas` with 3 ideas | JSON file with 3 entries |
| `test_export_sin_ideas` | `/export-ideas` with empty DB | JSON file with `[]` |

**Files**: `tests/test_memoria_rgpd.py` (~80 lines)  
**Dependencies**: `pytest`, Task 2.1  
**Verification**: `python -m pytest tests/test_memoria_rgpd.py -v` passes.

---

## PR 3 — Integration (app.py + agent.py + regression tests)

### Task 3.1: Integrate transversal dispatcher in `app.py:responder()`

**Status**: ✅ [x] COMPLETED — PR 3

**Action**: Add the Archivo de Ideas dispatcher block BEFORE the existing skill switch in `responder()`.

**Insertion point**: After input validation (`mensaje.strip()`) and before `if skill == "proceso_creativo":`.

**Code to add** (~20 lines):
```python
# ── ARCHIVO DE IDEAS: transversal command dispatch ──
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
        "content": f"⚠️ Error interno del archivo de ideas ({tipo}). El chat sigue funcionando normalmente."
    }
# ── end ARCHIVO DE IDEAS ──
```

**Rules**:
- Local imports to avoid circular deps
- `conn.close()` in `try/finally`
- Exception safety net: log error, return user-friendly message, DON'T crash the app
- `cmd_result is not None` → early return (skill handlers NOT executed)
- `cmd_result is None` → fall through to existing skill switch

**Files**: `app.py` (~20 lines added)  
**Dependencies**: Task 2.1 (`commands.py`)  
**Verification**: `/guardar test` in any skill returns confirmation; normal messages still reach skills.

---

### Task 3.2: Integrate transversal dispatcher in CLI `_loop_*` methods

**Status**: ✅ [x] COMPLETED — PR 3

**Action**: Add the same dispatcher pattern to all three CLI loops in `agents/creativo/agent.py`.

**`_loop_ficha(skills)`** changes:
- Add `ultimo_assistant = None` state variable
- Before the skill handler call, insert the same dispatcher block (adapted for CLI)
- If `cmd_result is not None`, `print(cmd_result["content"])` and `continue`
- After successful skill response, set `ultimo_assistant = respuesta`

**`_loop_ideas_creativas(skills)`** changes:
- Same dispatcher block
- After skill response, set `ultimo_assistant = respuesta`

**`_loop_proceso_creativo(skills, sesion_inicial=None)`** changes:
- Same dispatcher block
- After skill response, set `ultimo_assistant = respuesta`

**`PROCESO_COMANDOS` update** (in `agent.py`):
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

**`main()` function** — also add the dispatcher to the direct `ideas` and `pc` CLI entry points.

**Files**: `agents/creativo/agent.py` (~60 lines added across all loops)  
**Dependencies**: Task 2.1 (`commands.py`)  
**Verification**: CLI loops accept `/guardar` commands without crashing; normal skill interaction still works.

---

### Task 3.3: Write `tests/test_regresion_skills.py`

**Status**: ✅ [x] COMPLETED — PR 3

**Action**: Verify the dispatcher does not alter existing skill behavior.

**Tests**:

| Test | What it verifies |
|---|---|
| `test_ficha_recibe_mensaje_normal` | `responder("dame una ficha de setas", [], "ficha")` still triggers ficha handler |
| `test_ideas_creativas_recibe_mensaje_normal` | `responder("dame ideas para otoño", [], "ideas_creativas")` triggers ideas handler |
| `test_comando_devuelve_respuesta_sin_skill` | `responder("/guardar test", [], "ficha")` returns confirmation, NOT a ficha |
| `test_no_comando_devuelve_ficha_normal` | `responder("setas con parmesano", [{"role":"assistant","content":"anterior"}], "ficha")` returns a ficha |
| `test_comando_skills_creativas_sin_afectar` | 5 canonical inputs per skill produce identical response structure with/without memoria module active |

**Snapshot approach**: For each skill, run 3-5 canonical inputs through `responder()` and verify:
1. Non-command inputs produce responses with the expected structure (contains ficha sections, contains ideas, etc.)
2. Command inputs produce short confirmation/error responses, not full skill responses
3. The dispatcher does NOT crash on any input

**Files**: `tests/test_regresion_skills.py` (~120 lines)  
**Dependencies**: Task 3.1, Task 3.2  
**Verification**: `python -m pytest tests/test_regresion_skills.py -v` passes.

---

## Implementation Order Summary

| Step | Task | PR | Est. Lines | Blocked By |
|---|---|---|---|---|
| 1.1 | Create `agents/memoria/__init__.py` | PR 1 | ~10 | — |
| 1.2 | `storage.py` with full CRUD | PR 1 | ~200 | — |
| 1.3 | `formatters.py` pure functions | PR 1 | ~80 | — |
| 1.4 | `ideas_categorias.json` | PR 1 | ~15 | — |
| 1.5 | `tests/test_memoria_storage.py` | PR 1 | ~150 | 1.2, 1.3 |
| 1.6 | `tests/test_memoria_concurrency.py` | PR 1 | ~50 | 1.2 |
| 2.1 | `commands.py` with all command handlers | PR 2 | ~250 | 1.2, 1.3 |
| 2.2 | `tests/test_memoria_commands.py` | PR 2 | ~200 | 2.1 |
| 2.3 | `tests/test_memoria_duplicates.py` | PR 2 | ~80 | 2.1 |
| 2.4 | `tests/test_memoria_counter.py` | PR 2 | ~60 | 2.1 |
| 2.5 | `tests/test_memoria_rgpd.py` | PR 2 | ~80 | 2.1 |
| 3.1 | Integrate dispatcher in `app.py:responder()` | PR 3 | ~20 | 2.1 |
| 3.2 | Integrate dispatcher in CLI `_loop_*` methods | PR 3 | ~60 | 2.1 |
| 3.3 | `tests/test_regresion_skills.py` | PR 3 | ~120 | 3.1, 3.2 |

**Total estimated lines**: ~1,375

---

## Rollout: .gitignore

The `.gitignore` already contains `.agent_knowledge/` — this covers both `ideas.db` and export JSONs. No action needed.

---

## Persistent State Design

| State | Location | Lifetime | Thread-safe |
|---|---|---|---|
| Ideas data | `.agent_knowledge/ideas.db` (SQLite, WAL) | Permanent | ✅ WAL + timeout 5s |
| Counter active/inactive | In-memory `_contador_activo` | Session only (resets on restart) | ✅ `threading.Lock` |
| Pending confirmations | In-memory `_confirmacion_pendiente` | Session only (resets on restart) | ✅ `threading.Lock` |

---

## Environment Variables

| Variable | Effect | Default | Introduced in |
|---|---|---|---|
| `ARCHIVO_IDEAS_ENABLED=0` | Dispatcheador no responde comandos. Módulo instalado pero inerte. | `1` (activado) | Task 2.1 |

---

## Residual Risks After This Phase

| Risk | Severity | Mitigation |
|---|---|---|
| Numbered list regex may miss edge cases (unicode spaces, markdown inside code blocks) | 🟡 MEDIO | Clear error message fallback: "no es una lista numerada. Usá /guardar o /guardar [texto]" |
| Confirmation state lost on app restart | 🟢 BAJO | Acceptable; user re-issues `/olvidar todo` |
| Concurrent writes in HF Space multi-user scenarios | 🟡 MEDIO | WAL mode + timeout 5s + concurrency tests |
| Schema migration when adding columns later | 🟡 MEDIO | SQLite `ALTER TABLE ADD COLUMN` is safe; reversible via new column default |
