# Especificación del Módulo de Memoria — Archivo de Ideas

> **Change**: `archivo-de-ideas`
> **Phase**: `sdd-spec`
> **Status**: 🟢 Escrito — listo para `sdd-design`
> **Creado**: 2026-07-02
> **Dominio**: `memoria`

---

## 1. Propósito

El módulo `agents/memoria/` proporciona persistencia local para ideas del usuario David (Sol de Nit). Complementa la skill efímera `ideas_creativas` (que genera 10 ideas por LLM pero las olvida al cerrar sesión) con almacenamiento durable en SQLite. El invariante central es: **solo se guarda lo que el usuario ordena explícitamente mediante comandos**. No hay propuesta automática, no hay heurística, no hay guardado sin consentimiento.

---

## 2. Contrato de API

### 2.1 `agents/memoria/storage.py`

Todas las funciones aceptan un parámetro opcional `db_path` para testabilidad. Por defecto usan `Path(".agent_knowledge/ideas.db")`.

#### `init_db(db_path: Optional[Path] = None) -> sqlite3.Connection`

| Aspecto | Especificación |
|---|---|
| **Firma** | `def init_db(db_path: Optional[Path] = None) -> sqlite3.Connection` |
| **Comportamiento normal** | Crea `.agent_knowledge/` si no existe (con `Path.mkdir(parents=True, exist_ok=True)`). Abre conexión SQLite con `check_same_thread=False` y `timeout=5.0`. Ejecuta PRAGMAs: `journal_mode=WAL`, `foreign_keys=ON`. Crea la tabla `ideas` con el schema D2 si no existe. Crea índices `idx_ideas_created_at`, `idx_ideas_categoria`, `idx_ideas_origen_skill`. Retorna la conexión. |
| **Edge case: directorio no escribible** | Lanza `PermissionError` con mensaje "No tengo permisos para crear .agent_knowledge/ en {path.parent}. Verificá los permisos del directorio." |
| **Edge case: DB corrupta** | Lanza `sqlite3.DatabaseError` con mensaje "El archivo ideas.db está corrupto. Exportá el backup manual si existe y borrá el archivo para regenerarlo." |
| **Idempotencia** | Si la tabla ya existe, `CREATE TABLE IF NOT EXISTS` es no-op. Safe llamar múltiples veces. |
| **Concurrencia** | Cada llamada crea una conexión nueva. WAL mode permite lectores concurrentes. Escritores concurrentes usan timeout=5.0. |

#### `save_idea(conn: sqlite3.Connection, idea: str, categoria: Optional[str], contexto: Optional[str], origen: str, origen_skill: Optional[str]) -> int`

| Aspecto | Especificación |
|---|---|
| **Firma** | `def save_idea(conn, idea, categoria=None, contexto=None, origen='comando', origen_skill=None) -> int` |
| **Comportamiento normal** | Inserta fila con `created_at=datetime.now(timezone.utc).isoformat()`, `confirmada_por_usuario=1`, `idea`, `categoria`, `contexto`, `origen`, `origen_skill`. Retorna `last_insert_rowid`. |
| **Edge case: idea vacía** | Lanza `ValueError("La idea no puede estar vacía")`. |
| **Edge case: SQLite locked >5s** | Lanza `sqlite3.OperationalError` con mensaje "La base de datos está ocupada. Intentá de nuevo en unos segundos." |
| **Postcondición** | La fila existe y es recuperable con `get_idea(conn, id)`. |

#### `load_ideas(conn: sqlite3.Connection, filtro: Optional[dict] = None) -> list[dict]`

| Aspecto | Especificación |
|---|---|
| **Firma** | `def load_ideas(conn, filtro=None) -> list[dict]` |
| **Comportamiento normal** | Retorna todas las filas ordenadas por `created_at DESC`. Cada fila es un dict con claves: `id`, `created_at`, `updated_at`, `idea`, `categoria`, `contexto`, `confirmada_por_usuario`, `origen`, `origen_skill`. |
| **Filtros opcionales** | `filtro` acepta: `{"categoria": str}`, `{"origen_skill": str}`, `{"search": str}` (LIKE %search% sobre `idea`), `{"limit": int}`. Combinables. |
| **Edge case: DB vacía** | Retorna lista vacía `[]`. |
| **Edge case: filtro sin matches** | Retorna lista vacía `[]`. |

#### `get_idea(conn: sqlite3.Connection, idea_id: int) -> Optional[dict]`

| Aspecto | Especificación |
|---|---|
| **Firma** | `def get_idea(conn, idea_id) -> Optional[dict]` |
| **Comportamiento normal** | Retorna la fila con ese ID como dict, o `None` si no existe. |
| **Edge case: ID negativo o cero** | Retorna `None`. |

#### `edit_idea(conn: sqlite3.Connection, idea_id: int, nuevo_texto: str, nueva_categoria: Optional[str] = None) -> bool`

| Aspecto | Especificación |
|---|---|
| **Firma** | `def edit_idea(conn, idea_id, nuevo_texto, nueva_categoria=None) -> bool` |
| **Comportamiento normal** | Actualiza `idea = nuevo_texto`, `updated_at = datetime.now(timezone.utc).isoformat()`, y opcionalmente `categoria = nueva_categoria`. Retorna `True` si se actualizó alguna fila. |
| **Edge case: ID no existe** | Retorna `False`. |
| **Edge case: nuevo_texto vacío** | Lanza `ValueError("La idea no puede estar vacía")`. |
| **Postcondición** | `updated_at` tiene timestamp de la modificación. No se pierde `created_at` original. |

#### `delete_idea(conn: sqlite3.Connection, idea_id: int) -> bool`

| Aspecto | Especificación |
|---|---|
| **Firma** | `def delete_idea(conn, idea_id) -> bool` |
| **Comportamiento normal** | Borra la fila con `id = idea_id`. Retorna `True` si se borró algo. |
| **Edge case: ID no existe** | Retorna `False`. |

#### `delete_all_ideas(conn: sqlite3.Connection) -> int`

| Aspecto | Especificación |
|---|---|
| **Firma** | `def delete_all_ideas(conn) -> int` |
| **Comportamiento normal** | Ejecuta `DELETE FROM ideas`. Retorna número de filas borradas. |
| **Edge case: DB vacía** | Retorna 0. |

#### `export_ideas(conn: sqlite3.Connection, export_path: Optional[Path] = None) -> Path`

| Aspecto | Especificación |
|---|---|
| **Firma** | `def export_ideas(conn, export_path=None) -> Path` |
| **Comportamiento normal** | Exporta todas las filas (con todas las columnas) a un archivo JSON en `export_path` o por defecto `.agent_knowledge/ideas_export_<YYYYMMDD-HHMMSS>.json`. JSON usa codificación UTF-8, `ensure_ascii=False`, `indent=2`. Retorna el Path del archivo creado. |
| **Edge case: directorio no escribible** | Lanza `PermissionError` con mensaje "No tengo permisos para escribir en {export_path.parent}. Intentá con otra ubicación o usá stdout." |
| **Edge case: DB vacía** | Escribe un JSON con array vacío `[]`. No es error. |
| **Formato JSON** | `[{"id": 1, "created_at": "...", "updated_at": null, "idea": "...", "categoria": "...", "contexto": "...", "confirmada_por_usuario": 1, "origen": "comando", "origen_skill": "ficha"}, ...]` |

#### `count_ideas(conn: sqlite3.Connection) -> int`

| Aspecto | Especificación |
|---|---|
| **Firma** | `def count_ideas(conn) -> int` |
| **Comportamiento normal** | Retorna `SELECT COUNT(*) FROM ideas`. |
| **Edge case: DB vacía** | Retorna 0. |

#### `check_duplicate(conn: sqlite3.Connection, texto: str, umbral: float = 0.8) -> list[dict]`

| Aspecto | Especificación |
|---|---|
| **Firma** | `def check_duplicate(conn, texto, umbral=0.8) -> list[dict]` |
| **Comportamiento normal** | 1. Busca match exacto (comparación case-insensitive del texto completo). 2. Si no hay exacto, busca fuzzy: carga todas las ideas, calcula `difflib.SequenceMatcher.ratio()` con cada una, retorna aquellas con ratio >= umbral. Retorna lista de dicts de ideas duplicadas (vacía si no hay). |
| **Edge case: texto vacío** | Retorna lista vacía. |
| **Edge case: DB vacía** | Retorna lista vacía. |
| **Rendimiento** | Para <1000 ideas, carga completa y compara en memoria es aceptable. Si en el futuro hay más, migrar a FTS5. |

---

### 2.2 `agents/memoria/commands.py`

#### `handle_command(mensaje: str, ultimo_assistant_mensaje: Optional[str], skill_activa: str, conn: sqlite3.Connection, contador_activo: bool = True) -> Optional[dict]`

| Aspecto | Especificación |
|---|---|
| **Firma completa** | `def handle_command(mensaje, ultimo_assistant_mensaje=None, skill_activa='ficha', conn=None, contador_activo=True) -> Optional[dict]` |
| **Comportamiento normal** | Analiza `mensaje` para detectar si comienza con `/`. Si es un comando conocido, lo ejecuta y retorna `{"role": "assistant", "content": str}` con la respuesta formateada. Si NO es un comando conocido o no comienza con `/`, retorna `None` para que el dispatcher continúe al handler de skill. |
| **Comandos soportados** | Ver tabla abajo. |
| **Edge case: conn=None** | Abre conexión temporal con `init_db()` si no se provee `conn`. Cierra al terminar. |
| **Edge case: comando desconocido que empieza con /** | Retorna dict con error formateado: "Comando no reconocido. Escribí `/ayuda` para ver los comandos disponibles." |

##### Tabla de comandos

| Comando | Parseo | Comportamiento | Errores |
|---|---|---|---|
| `/guardar [texto]` | `mensaje[8:].strip()` | Valida texto no vacío. Llama `check_duplicate()`. Si hay duplicados, retorna mensaje con IDs y "¿Guardar igual?" Si no, guarda con `save_idea()`. Retorna confirmación con ID y contador (si activo). | "especificá qué querés guardar" si texto vacío |
| `/guardar` (sin args) | `mensaje == "/guardar"` | Usa `ultimo_assistant_mensaje` como idea. Si es None o vacío, error. Guarda igual que arriba. | "no tengo un mensaje reciente para guardar" |
| `/guardar N` | Regex `r"^/guardar\s+(\d+)$"` | Parsea el número. Busca en `ultimo_assistant_mensaje` líneas que matcheen `r"^\s*\d+[.)]\s+(.+)"`. Extrae la línea N. Guarda. | "el último mensaje no es una lista numerada" / "no encontré la idea número {N}. El rango válido es 1–{total}" |
| `/editar N [nuevo texto]` | Regex `r"^/editar\s+(\d+)\s+(.+)"` | Verifica que el ID exista con `get_idea()`. Actualiza con `edit_idea()`. Retorna confirmación. | "no existe ninguna idea con ID {N}" / "especificá el nuevo texto para la idea" |
| `/ideas [filtro]` | `mensaje[7:].strip()` | Llama `load_ideas()` con filtro opcional. Retorna lista formateada o "No tenés ideas guardadas todavía." | — |
| `/olvidar todo` | `mensaje.strip() == "/olvidar todo"` | Retorna "Escribí `olvidar todo` para confirmar (sin la /)." No borra nada hasta la confirmación. | — |
| `olvidar todo` (confirmación) | `mensaje.strip() == "olvidar todo"` | Solo si el estado del diálogo indica que se pidió confirmación previamente. Llama `delete_all_ideas()`. Retorna "Archivo de ideas borrado. Se eliminaron {N} ideas." | "No había nada que confirmar." si no hay estado pendiente |
| `/olvidar N` | Regex `r"^/olvidar\s+(\d+)$"` | Verifica que el ID exista. Pide confirmación en el mensaje de respuesta. Espera siguiente turno para confirmar. | "no existe ninguna idea con ID {N}" |
| `/export-ideas` | `mensaje == "/export-ideas"` | Llama `export_ideas()`. Retorna "✅ Exportado a {path}. Es un archivo local, no se subió a ningún servidor." | "No pude exportar: {error}. Intentá de nuevo." |
| `/silenciar-contador` | `mensaje == "/silenciar-contador"` | Alterna estado booleano en memoria (no persistente). Retorna "Contador silenciado. Usá `/silenciar-contador` de nuevo para reactivarlo." | — |
| `/ayuda` | `mensaje == "/ayuda"` | Retorna lista de todos los comandos disponibles con descripción breve. | — |

#### `get_contador_state() -> bool` / `toggle_contador_state() -> bool`

| Aspecto | Especificación |
|---|---|
| **Propósito** | Estado del contador en memoria para la sesión actual. No persiste entre sesiones. |
| **`get_contador_state()`** | Retorna `True` si el contador está activo (default), `False` si silenciado. |
| **`toggle_contador_state()`** | Alterna el estado. Retorna el nuevo estado. |
| **Thread safety** | Las funciones usan un `threading.Lock` interno. |

---

### 2.3 `agents/memoria/formatters.py`

Todas las funciones son puras (sin IO, sin DB).

#### `format_counter(count: int) -> str`

| Input | Output |
|---|---|
| `0` | `""` (vacío) |
| `1` | `"📁 1 guardada"` |
| `5` | `"📁 5 guardadas"` |

#### `format_idea_list(ideas: list[dict]) -> str`

| Aspecto | Especificación |
|---|---|
| **Comportamiento** | Formatea una lista de dicts de ideas como texto legible. Cada idea ocupa 2-4 líneas. |
| **Formato** | Para cada idea: `#{id} | {created_at} | {categoria or "sin categoría"}\n> {idea[:200]}{"…" if len(idea)>200 else ""}` |
| **Lista vacía** | `"No tenés ideas guardadas todavía. Usá /guardar para guardar tu primera idea."` |

#### `format_save_confirmation(idea: dict, count: int, contador_activo: bool = True) -> str`

| Aspecto | Especificación |
|---|---|
| **Comportamiento** | Retorna string de confirmación con ID, preview del texto, y contador si activo. |
| **Formato** | `"✅ Idea #{id} guardada: {idea_texto[:80]}{"…" if len>80 else ""}"` + `\n📁 {count} guardadas` (si contador_activo) |

#### `format_error(msg: str) -> str`

| Aspecto | Especificación |
|---|---|
| **Comportamiento** | Retorna string con formato de error estándar. |
| **Formato** | `"⚠️ {msg}"` |
| **Uso** | Todos los errores de comando y storage pasan por esta función. |

#### `format_duplicate_warning(dup: dict) -> str`

| Aspecto | Especificación |
|---|---|
| **Comportamiento** | Retorna string advirtiendo sobre duplicado. Incluye ID, preview y pregunta. |
| **Formato** | `"⚠️ Ya tenés algo parecido (#{dup['id']}): {dup['idea'][:80]}…\n¿Usar /guardar igual para guardar de todas formas?"` |

---

## 3. Escenarios Given/When/Then

### 3.1 C1 — `/guardar "mi idea"` guarda fila y devuelve confirmación

**Feature: Guardar texto libre**

```gherkin
Scenario: guardar texto libre básico
  Given una DB vacía en .agent_knowledge/ideas.db
    And la skill activa es "ficha"
  When el usuario escribe "/guardar probar kumquat en el postre"
  Then save_idea() se llama con idea="probar kumquat en el postre"
    And confirmada_por_usuario=1
    And origen="comando"
    And origen_skill="ficha"
    And el mensaje de respuesta incluye "✅ Idea #1 guardada: probar kumquat en el postre"
    And el mensaje de respuesta incluye "📁 1 guardada"

Scenario: guardar texto con caracteres especiales
  Given una DB con 5 ideas existentes
  When el usuario escribe '/guardar "fermentación láctica de hongos de temporada — setas 2026"'
  Then la idea se guarda con el texto exacto incluyendo las comillas
    And el contador muestra "📁 6 guardadas"

Scenario: guardar texto vacío
  Given cualquier skill
  When el usuario escribe "/guardar " (solo espacios)
  Then el mensaje de respuesta es "⚠️ especificá qué querés guardar"
    And NO se inserta ninguna fila en la DB
```

### 3.2 C2 — `/guardar` (sin args) guarda el último mensaje del assistant

**Feature: Guardar último mensaje del asistente**

```gherkin
Scenario: guardar último mensaje exitoso
  Given el assistant acaba de responder "Podés probar con fermentos de hongos, le dan un umami muy interesante al plato de temporada"
  When el usuario escribe "/guardar"
  Then la idea guardada es "Podés probar con fermentos de hongos, le dan un umami muy interesante al plato de temporada"
    And el mensaje de respuesta incluye confirmación con el texto truncado

Scenario: guardar sin historial previo
  Given no hay mensaje del assistant en el contexto (None)
  When el usuario escribe "/guardar"
  Then el mensaje de respuesta es "⚠️ no tengo un mensaje reciente para guardar"
    And NO se inserta ninguna fila

Scenario: guardar con último mensaje vacío
  Given ultimo_assistant_mensaje = ""
  When el usuario escribe "/guardar"
  Then el mensaje de respuesta es "⚠️ no tengo un mensaje reciente para guardar"
```

### 3.3 C3 — `/guardar N` guarda idea numerada del último mensaje

**Feature: Guardar idea por número de lista**

```gherkin
Scenario: guardar idea 3 de una lista numerada
  Given el último mensaje del assistant es:
    """
    1. Plato de otoño con setas
    2. Fermento de kumquat para acompañar
    3. Restricción: sin gluten para mesa 7
    4. Menú de hongos completo con 4 pasos
    """
  When el usuario escribe "/guardar 3"
  Then la idea guardada es "Restricción: sin gluten para mesa 7"
    And origen_skill es la skill activa actual

Scenario: guardar con N que excede el rango de la lista
  Given el último mensaje del assistant tiene 4 ideas numeradas
  When el usuario escribe "/guardar 7"
  Then el mensaje de respuesta es "⚠️ no encontré la idea número 7. El rango válido es 1–4"
    And NO se inserta ninguna fila

Scenario: guardar por número sin lista numerada
  Given el último mensaje del assistant es "Podés probar con fermentos de hongos"
  When el usuario escribe "/guardar 1"
  Then el mensaje de respuesta es "⚠️ el último mensaje no es una lista numerada. Usá `/guardar` o `/guardar [texto]`"
    And NO se inserta ninguna fila

Scenario: guardar por número con formato mixto "3)" y "3."
  Given el último mensaje del assistant tiene ideas con "3)" y "4."
  When el usuario escribe "/guardar 3"
  Then la línea que comienza con "3)" se captura correctamente
```

### 3.4 C4 — Duplicados exactos detectados

**Feature: Detección de duplicados exactos**

```gherkin
Scenario: guardar idea idéntica a una existente
  Given la DB contiene una idea con texto "probar kumquat en el postre" (ID #1)
  When el usuario escribe '/guardar "probar kumquat en el postre"'
  Then check_duplicate() retorna la idea #1
    And el mensaje de respuesta es "⚠️ Ya tenés algo parecido (#1): probar kumquat en el postre… ¿Usar /guardar igual para guardar de todas formas?"
    And NO se inserta una nueva fila automáticamente

Scenario: guardar igual a pesar de duplicado exacto
  Given la DB contiene "probar kumquat en el postre" (ID #1)
    And el usuario recibió la advertencia de duplicado
  When el usuario escribe "/guardar igual"
  Then se inserta una nueva fila con el mismo texto
    And el contador refleja el nuevo total
```

### 3.5 C5 — Duplicados fuzzy ≥80% detectados

**Feature: Detección de duplicados fuzzy**

```gherkin
Scenario: guardar idea muy similar a una existente
  Given la DB contiene "probar kumquat en el postre de temporada" (ID #1)
  When el usuario escribe '/guardar "probar kumquat en postre temporada"'
  Then check_duplicate() retorna la idea #1 (ratio >= 0.8)
    And se muestra advertencia con el ID existente

Scenario: guardar idea similar pero diferente (ratio <80%)
  Given la DB contiene "probar kumquat en el postre"
  When el usuario escribe '/guardar "cambiar el menú de setas a otoño"'
  Then check_duplicate() retorna lista vacía
    And la idea se guarda sin advertencia
```

### 3.6 C6 — `/editar N "texto nuevo"` actualiza fila

**Feature: Editar idea guardada**

```gherkin
Scenario: editar texto de una idea existente
  Given la DB contiene una idea con ID #3 y texto "idea original"
  When el usuario escribe '/editar 3 "texto nuevo y mejorado"'
  Then edit_idea(conn, 3, "texto nuevo y mejorado") retorna True
    AND get_idea(conn, 3)["idea"] == "texto nuevo y mejorado"
    AND get_idea(conn, 3)["updated_at"] NO es NULL
    AND get_idea(conn, 3)["created_at"] es el timestamp original
    AND el mensaje de respuesta incluye "✅ Idea #3 actualizada"

Scenario: editar idea inexistente
  Given la DB tiene ideas con IDs 1-5
  When el usuario escribe '/editar 99 "texto nuevo"'
  Then el mensaje de respuesta es "⚠️ no existe ninguna idea con ID 99"

Scenario: editar sin nuevo texto
  When el usuario escribe '/editar 3' (sin texto nuevo)
  Then el mensaje de respuesta es "⚠️ especificá el nuevo texto para la idea"
```

### 3.7 C7 — Contador visible con opt-out

**Feature: Contador de ideas guardadas**

```gherkin
Scenario: contador se muestra después de guardar
  Given la DB tiene 3 ideas guardadas
  When el usuario guarda una nueva idea
  Then el mensaje de respuesta incluye "📁 4 guardadas"

Scenario: silenciar contador
  Given el contador está activo (por defecto)
  When el usuario escribe "/silenciar-contador"
  Then el mensaje de respuesta confirma que el contador está silenciado
    And get_contador_state() retorna False

Scenario: contador no se muestra después de silenciar
  Given el contador está silenciado
  When el usuario guarda una nueva idea
  Then el mensaje de respuesta NO incluye "📁"
    And la idea se guarda correctamente

Scenario: reactivar contador
  Given el contador está silenciado
  When el usuario escribe "/silenciar-contador"
  Then get_contador_state() retorna True
    And el mensaje de respuesta confirma la reactivación
```

### 3.8 C8 — `/olvidar todo` con confirmación explícita

**Feature: Borrar todas las ideas**

```gherkin
Scenario: pedir borrar todo sin confirmación
  Given la DB tiene 10 ideas guardadas
  When el usuario escribe "/olvidar todo"
  Then NO se borra ninguna fila
    And el mensaje de respuesta es "⚠️ Escribí `olvidar todo` (sin la /) para confirmar que querés borrar TODAS tus ideas guardadas."

Scenario: confirmar borrado de todo
  Given el usuario recibió el mensaje de confirmación
  When el usuario escribe "olvidar todo" (sin /)
  Then delete_all_ideas() se ejecuta
    And el mensaje de respuesta es "✅ Archivo de ideas borrado. Se eliminaron 10 ideas."

Scenario: confirmar sin estado pendiente
  Given no hay una operación de borrado pendiente
  When el usuario escribe "olvidar todo" (sin /)
  Then NO se borra ninguna fila
    And el mensaje de respuesta es "⚠️ No había nada que confirmar."
```

### 3.9 C9 — `/olvidar N` con confirmación

**Feature: Borrar una idea específica**

```gherkin
Scenario: pedir borrar una idea
  Given la DB contiene una idea con ID #5
  When el usuario escribe "/olvidar 5"
  Then NO se borra la fila todavía
    And el mensaje de respuesta es "⚠️ ¿Estás seguro? Escribí `olvidar 5` (sin la /) para confirmar."

Scenario: confirmar borrado de una idea
  Given hay una operación de borrado pendiente para ID #5
  When el usuario escribe "olvidar 5"
  Then delete_idea(conn, 5) retorna True
    And el mensaje de respuesta es "✅ Idea #5 borrada."

Scenario: olvidar idea inexistente
  When el usuario escribe "/olvidar 99"
  Then el mensaje de respuesta es "⚠️ no existe ninguna idea con ID 99"
```

### 3.10 C10 — `/export-ideas` crea archivo JSON

**Feature: Exportar ideas a JSON**

```gherkin
Scenario: exportar con ideas existentes
  Given la DB tiene 5 ideas guardadas
  When el usuario escribe "/export-ideas"
  Then se crea un archivo .agent_knowledge/ideas_export_<timestamp>.json
    And el JSON contiene un array con 5 objetos
    And cada objeto tiene los campos: id, created_at, updated_at, idea, categoria, contexto, origen, origen_skill
    And el mensaje de respuesta incluye "✅ Exportado a .agent_knowledge/ideas_export_"
    And el mensaje de respuesta incluye "Es un archivo local, no se subió a ningún servidor"

Scenario: exportar con DB vacía
  Given la DB está vacía
  When el usuario escribe "/export-ideas"
  Then se crea un archivo JSON con array vacío []
    And el mensaje de respuesta indica que se exportaron 0 ideas

Scenario: exportar a directorio no escribible
  Given .agent_knowledge/ no tiene permisos de escritura
  When el usuario escribe "/export-ideas"
  Then el mensaje de respuesta es "⚠️ No pude exportar: [error]. Intentá de nuevo."
```

### 3.11 C11 — No-regresión: skills responden igual a inputs no-comando

**Feature: Skills no se ven afectadas por el dispatcher**

```gherkin
Scenario: ficha responde a mensaje normal
  Given el dispatcher de comandos está activo
  When el usuario escribe "dame una ficha de salteado de setas" en skill ficha
  Then el handler de ficha recibe el mensaje sin modificar
    And la respuesta es idéntica a la que daría sin el módulo memoria

Scenario: ideas_creativas responde a mensaje normal
  Given el dispatcher de comandos está activo
  When el usuario escribe "dame ideas para menú de otoño" en skill ideas_creativas
  Then el handler de ideas_creativas recibe el mensaje sin modificar
    And la respuesta es la lista de 10 ideas

Scenario: snapshot de regresión
  Given una lista de 10 inputs canónicos por skill
  When se ejecuta cada input contra responder() con y sin el módulo memoria
  Then las respuestas son idénticas (comparación exacta de strings)
```

### 3.12 C12 — Handlers existentes no se modifican

**Feature: Handlers existentes intactos**

```gherkin
Scenario: el dispatcher actúa antes y retorna dict si matchea comando
  Given responder() recibe "/guardar probar kumquat"
  When se ejecuta responder()
  Then commands.handle_command() retorna un dict no-None
    And el handler de skill NO se ejecuta para este mensaje
    And la respuesta es el dict del comando

Scenario: el dispatcher retorna None para no-comandos
  Given responder() recibe "dame ideas para otoño"
  When se ejecuta responder()
  Then commands.handle_command() retorna None
    And el handler de skill correspondiente se ejecuta normalmente
```

### 3.13 C13 — `.agent_knowledge/ideas.db` ignorado por git

**Feature: Gitignore cubre la DB**

```gherkin
Scenario: verificar gitignore
  Given el archivo .gitignore contiene la línea ".agent_knowledge/"
  When se ejecuta "git check-ignore .agent_knowledge/ideas.db"
  Then el comando retorna código 0 (el archivo está ignorado)

Scenario: export JSON también ignorado
  When se ejecuta "git check-ignore .agent_knowledge/ideas_export_20260702.json"
  Then el comando retorna código 0
```

### 3.14 C14 — Tests contra DB temporal (path injectable)

**Feature: Testabilidad con path injectable**

```gherkin
Scenario: storage.py acepta db_path en todas las funciones
  Given un fixture de pytest que crea un temp SQLite en tmp_path
  When se llama a init_db(tmp_path / "test.db")
  Then la conexión apunta al archivo temporal
    And ninguna fila se escribe en .agent_knowledge/ideas.db

Scenario: todas las funciones de storage aceptan conn
  Given una conexión a temp SQLite
  When se ejecutan save_idea(), load_ideas(), get_idea(), edit_idea(), delete_idea(), check_duplicate()
  Then todas las operaciones operan sobre la DB temporal
    And .agent_knowledge/ queda intacto
```

### 3.15 C15 — Concurrencia no corrompe DB

**Feature: Escrituras concurrentes seguras**

```gherkin
Scenario: dos hilos guardan simultáneamente
  Given una DB SQLite con WAL mode
  When 2 hilos ejecutan save_idea() concurrentemente con ThreadPoolExecutor
  Then ambas ideas se guardan (COUNT(*) == 2)
    And last_insert_rowid es distinto para cada hilo
    And no hay excepción sqlite3.DatabaseError

Scenario: lector concurrente durante escritura
  Given un hilo escribe mientras otro lee
  When el lector ejecuta load_ideas() durante una escritura
  Then el lector no se bloquea (WAL mode permite lectura concurrente)
    And no hay excepción
```

### 3.16 C16 — Tests verdes antes de merge

**Feature: Suite de tests pasa**

```gherkin
Scenario: todos los tests memoria pasan
  Given la suite test_memoria_*.py completa
  When se ejecuta "pytest tests/test_memoria_*.py -v"
  Then todos los tests pasan (exit code 0)

Scenario: tests de regresión pasan
  When se ejecuta "pytest tests/test_regresion_skills.py -v"
  Then todos los tests pasan
    And las respuestas snapshot coinciden con las baseline
```

---

## 4. Manejo de errores y modos de fallo

### 4.1 SQLite archivo bloqueado / no escribible

| Condición | Comportamiento | Test |
|---|---|---|
| Archivo `.agent_knowledge/ideas.db` bloqueado por otro proceso | `timeout=5.0` espera hasta 5s. Si expira, `sqlite3.OperationalError` se captura en `commands.py` y se devuelve `"⚠️ La base de datos está ocupada. Intentá de nuevo en unos segundos."` | `test_storage_locked.py` simula bloqueo con `exclusive_lock` desde otro proceso |
| Directorio `.agent_knowledge/` no existe | `init_db()` lo crea (mkdir parents). Si falla, `PermissionError` se captura. | Test con mock de `Path.mkdir` que lanza PermissionError |
| Archivo DB corrupto | `sqlite3.DatabaseError` se captura. Mensaje: "El archivo ideas.db está corrupto." | Test con archivo binario corrupto como DB |
| Disco lleno | `sqlite3.OperationalError` ("database or disk is full"). Capturado, mensaje claro. | Mock de escritura que llena el disco simulado |

### 4.2 Detección de duplicados

| Condición | Comportamiento |
|---|---|
| Match exacto (case-insensitive) | Advertencia: "Ya tenés algo parecido (#ID). ¿Guardar igual?" |
| Match fuzzy ≥80% | Misma advertencia que exacto. El usuario no distingue entre exacto y fuzzy en la UX. |
| Sin duplicados | Guardado directo sin advertencia. |
| DB vacía | No hay duplicados. Guardado directo. |

### 4.3 Último mensaje del assistant no definido

| Comando | Error |
|---|---|
| `/guardar` (sin args) sin historial | `"⚠️ no tengo un mensaje reciente para guardar"` |
| `/guardar N` sin último mensaje | `"⚠️ el último mensaje no es una lista numerada. Usá /guardar o /guardar [texto]"` |
| `/guardar N` con último mensaje no numerado | `"⚠️ el último mensaje no es una lista numerada. Usá /guardar o /guardar [texto]"` |

### 4.4 `/editar N` con N fuera de rango

| Condición | Comportamiento |
|---|---|
| N no existe en DB | `"⚠️ no existe ninguna idea con ID {N}"` |
| N no es entero válido | `"⚠️ formato: /editar ID nuevo texto"` |

### 4.5 `/olvidar` — confirmación explícita

| Condición | Comportamiento |
|---|---|
| `/olvidar todo` (primera vez) | No borra. Responde: "⚠️ Escribí `olvidar todo` (sin la /) para confirmar." |
| `olvidar todo` (confirmación) | Borra todo. Responde: "✅ Archivo de ideas borrado. Se eliminaron {N} ideas." |
| `olvidar todo` sin estado pendiente | No borra. Responde: "⚠️ No había nada que confirmar." |
| Cualquier otro input después de pedir confirmación | Se ignora como confirmación. El usuario debe repetir el proceso. |
| `/olvidar N` (primera vez) | No borra. Responde: "⚠️ ¿Estás seguro? Escribí `olvidar N` (sin la /) para confirmar." |
| `olvidar N` (confirmación) | Borra esa idea. |

### 4.6 Export a directorio no escribible

| Condición | Comportamiento |
|---|---|
| Sin permisos en `.agent_knowledge/` | Captura `PermissionError`. Mensaje: `"⚠️ No pude exportar: [error específico]. Intentá de nuevo."` |
| Export exitoso | Mensaje: `"✅ Exportado a {path}. Es un archivo local, no se subió a ningún servidor."` |
| Export con DB vacía | Mensaje: `"✅ Exportado a {path} (0 ideas). Es un archivo local, no se subió a ningún servidor."` |

### 4.7 Concurrent writes (HF Space multi-usuario)

| Condición | Comportamiento |
|---|---|
| Dos escrituras simultáneas | WAL mode + `timeout=5.0` previene corrupción. Una escritura puede fallar con timeout si la otra tarda >5s. Error: `"⚠️ La base de datos está ocupada. Intentá de nuevo en unos segundos."` |
| Lectura durante escritura | WAL mode permite lectores concurrentes sin bloqueo. |
| Más de 2 usuarios concurrentes | WAL mode maneja, pero performance degrada. Mensaje de error tras timeout. |

---

## 5. Estrategia de testing

### 5.1 Testabilidad por diseño

| Módulo | Mecanismo de testabilidad |
|---|---|
| `storage.py` | Todas las funciones aceptan `conn: sqlite3.Connection` como primer parámetro. El fixture de pytest crea un `tmp_path` con `sqlite3.connect()`. |
| `commands.py` | `handle_command()` acepta `conn` y `ultimo_assistant_mensaje` como parámetros explícitos. No hay variables globales ni estado mutable compartido (excepto el contador que tiene su propio lock). |
| `formatters.py` | Funciones puras. Sin dependencias de DB ni IO. Se testean con asserts directos sobre strings. |

### 5.2 Archivos de test

| Archivo | Cobertura |
|---|---|
| `tests/test_memoria_storage.py` | `init_db`, `save_idea`, `load_ideas`, `get_idea`, `edit_idea`, `delete_idea`, `delete_all_ideas`, `count_ideas`, `export_ideas`. Cada función con happy path + edge cases. También: `init_db` con directorio no existente (lo crea), con DB corrupta, con permisos insuficientes. |
| `tests/test_memoria_commands.py` | Cada variante de `/guardar` (3), `/editar`, `/ideas`, `/olvidar` (2), `/export-ideas`, `/ayuda`, `/silenciar-contador`. También: comando desconocido que empieza con `/`, mensaje sin `/` retorna None. |
| `tests/test_memoria_duplicates.py` | `check_duplicate` con match exacto (case-insensitive), fuzzy ≥80%, fuzzy <80%, DB vacía, texto vacío. |
| `tests/test_memoria_counter.py` | Contador después de guardar, `/silenciar-contador`, guardar sin contador, reactivar. |
| `tests/test_memoria_rgpd.py` | `/olvidar todo` sin confirmación, con confirmación, sin estado pendiente. `/olvidar N` con confirmación. `/export-ideas` con y sin ideas. |
| `tests/test_regresion_skills.py` | Snapshot de 10 inputs por skill. Verifica que el dispatcher retorna None para no-comandos y que handlers existentes reciben el mensaje sin modificar. |
| `tests/test_memoria_concurrency.py` | `ThreadPoolExecutor` con 2-4 hilos escribiendo concurrentemente. Assert: `count(*)` post-ejecución, todos los `last_insert_rowid` distintos, sin excepciones. |

### 5.3 Fixture de pytest

```python
import pytest
import sqlite3
from pathlib import Path

@pytest.fixture
def db_conn(tmp_path):
    """Crea una DB SQLite temporal para tests."""
    db_path = tmp_path / "test_ideas.db"
    conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=5.0)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    # Schema inline para no depender de init_db() en tests unitarios
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
    yield conn
    conn.close()
```

### 5.4 Test de concurrencia (C15)

```python
def test_concurrent_writes(db_conn):
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    def write_idea(n):
        # Cada hilo usa su propio cursor
        import storage
        return storage.save_idea(db_conn, f"idea concurrente {n}", origen="test")
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(write_idea, i) for i in range(4)]
        ids = [f.result() for f in as_completed(futures)]
    
    assert len(set(ids)) == 4  # todos distintos
    assert storage.count_ideas(db_conn) == 4
```

---

## 6. Puntos de integración en código existente

### 6.1 `app.py:responder()` — Dispatcher transversal (HF Gradio)

```
ANTES:
    def responder(mensaje, historial, skill):
        if skill == "proceso_creativo":
            return _responder_proceso_creativo(mensaje, historial)
        if skill == "ideas_creativas":
            return _responder_ideas_creativas(mensaje, historial)
        # default: ficha
        return _responder_ficha(mensaje, historial)
    
DESPUÉS:
    def responder(mensaje, historial, skill):
        # Dispatcher transversal de comandos del archivo de ideas
        conn = init_db()
        ultimo_assistant = historial[-1]["content"] if historial else None
        cmd_result = handle_command(mensaje, ultimo_assistant, skill, conn)
        if cmd_result is not None:
            return cmd_result["content"]
        
        # Skills existentes intactas
        if skill == "proceso_creativo":
            return _responder_proceso_creativo(mensaje, historial)
        if skill == "ideas_creativas":
            return _responder_ideas_creativas(mensaje, historial)
        return _responder_ficha(mensaje, historial)
```

**Regla**: El dispatcher debe ejecutarse ANTES del switch de skill. Si `handle_command()` retorna un dict no-None, se retorna inmediatamente. Si retorna None, se continúa al handler de skill. No se modifica ningún handler existente.

### 6.2 `agents/creativo/agent.py` — CLI `_loop_*`

Mismo patrón en `_loop_ficha()`, `_loop_ideas_creativas()`, `_loop_proceso_creativo()`.

```
DESPUÉS (en cada loop):
    def _loop_ficha(self):
        # ... setup existente ...
        while True:
            mensaje = input("> ")
            # Dispatcher transversal
            conn = init_db()
            cmd_result = handle_command(mensaje, ultimo_assistant, "ficha", conn)
            if cmd_result is not None:
                print(cmd_result["content"])
                continue
            # ... handler existente sigue igual ...
```

Agregar los comandos del archivo de ideas a `PROCESO_COMANDOS` set (para que el CLI no los interprete como parte del flujo de la skill).

### 6.3 Módulo `agents/memoria/`

```
agents/memoria/
├── __init__.py       # Exporta init_db, handle_command y formateadores
├── storage.py        # init_db, save_idea, load_ideas, get_idea, edit_idea, delete_idea, delete_all_ideas, export_ideas, count_ideas, check_duplicate
├── commands.py       # handle_command, get_contador_state, toggle_contador_state
└── formatters.py     # format_counter, format_idea_list, format_save_confirmation, format_error, format_duplicate_warning
```

### 6.4 Variables de entorno (opcional)

| Variable | Efecto | Default |
|---|---|---|
| `ARCHIVO_IDEAS_ENABLED=0` | Desactiva el dispatcher de comandos. El módulo sigue instalado pero no responde a comandos. | `1` (activado) |

---

## 7. Mapa de archivos

### 7.1 Archivos a crear

| Archivo | Líneas estimadas | Contenido |
|---|---|---|
| `agents/memoria/__init__.py` | ~10 | Exporta símbolos públicos |
| `agents/memoria/storage.py` | ~200 | Schema, CRUD, duplicados, export |
| `agents/memoria/commands.py` | ~250 | Parser de comandos, dispatch, contador state |
| `agents/memoria/formatters.py` | ~80 | Funciones de formateo puras |
| `agents/ideas_categorias.json` | ~15 | Categorías precargadas |
| `.agent_knowledge/ideas.md` | ~20 | Documentación del schema (creado por init_db) |
| `tests/test_memoria_storage.py` | ~150 | Tests de CRUD + edge cases |
| `tests/test_memoria_commands.py` | ~200 | Tests de cada comando |
| `tests/test_memoria_duplicates.py` | ~80 | Tests de detección exacta + fuzzy |
| `tests/test_memoria_counter.py` | ~60 | Tests de contador y opt-out |
| `tests/test_memoria_rgpd.py` | ~80 | Tests de olvidar y export |
| `tests/test_memoria_concurrency.py` | ~50 | Tests de concurrencia WAL |
| `tests/test_regresion_skills.py` | ~120 | Tests de no regresión por skill |

### 7.2 Archivos a modificar

| Archivo | Cambio | Líneas |
|---|---|---|
| `app.py` | Agregar dispatcher transversal en `responder()` antes del switch de skill | ~15 |
| `agents/creativo/agent.py` | Agregar dispatcher en `_loop_ficha`, `_loop_ideas_creativas`, `_loop_proceso_creativo`. Agregar comandos a `PROCESO_COMANDOS`. | ~30 |

### 7.3 Archivos que NO se crean (confirmado out-of-scope)

| Archivo | Razón |
|---|---|
| `agents/memoria/triggers.py` | Q1: no hay auto-propuesta |
| `agents/memoria/consent.py` | Q1: el comando ES el consentimiento |
| `agents/ideas_triggers.json` | Q1: no hay heurística de palabras gatillo |
| `tests/test_memoria_triggers.py` | Q1: eliminado |
| `tests/test_memoria_consent*.py` | Q1: no hay consentimiento en 2 turnos |

---

## 8. Riesgos residuales

| ID | Riesgo | Severidad | Estado |
|---|---|---|---|
| R3 | Concurrencia SQLite en HF Space | 🟡 MEDIO | Mitigado: WAL + timeout 5.0 + test C15 con ThreadPoolExecutor |
| R4 | Schema se vuelve rígido (nuevas categorías) | 🟡 MEDIO | Mitigado: categorías en JSON editable + campo libre `categoria` sin FK |
| R5 | David olvida los comandos | 🟡 MEDIO | Mitigado: `/ayuda` lista todos los comandos |
| R6 | Regresión MVP-0.5 | 🟢 BAJO | Mitigado: cambios aditivos + tests C11-C12 de no regresión |
| N2 | Multi-tenant HF Space (futuro) | 🟡 MEDIO | Documentado: v1 asume single-user; si cambia, migrar a `ideas_<user_hash>.db` |
| — | Confirmación de `/olvidar todo` acepta "olvidar todo" literal | 🟢 BAJO | UX validada con David; si prefiere otra forma (ID random), se cambia en design |

---

## 9. Resultado de fase

```yaml
status: spec-complete
artifacts:
  - openspec/changes/archivo-de-ideas/specs/memoria/spec.md  (este archivo)
next_recommended: sdd-design
risks:
  - R3: concurrencia SQLite (MEDIO, mitigado con WAL + timeout + test)
  - R4: rigidez schema (MEDIO, mitigado con JSON editable + campo libre)
  - R5: comandos olvidados (MEDIO, mitigado con /ayuda)
  - R6: regresión MVP-0.5 (BAJO, mitigado con cambios aditivos + tests)
  - N2: multi-tenant HF Space futuro (MEDIO, documentado)
skill_resolution: none
```
