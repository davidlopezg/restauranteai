# Explore — Archivo de Ideas

> **Change**: `archivo-de-ideas`
> **Phase**: `sdd-explore`
> **Created**: 2026-07-02
> **Orquestador**: el Gentleman (Pi)
> **Status**: ✅ Completo — listo para `sdd-proposal`

---

## Resumen ejecutivo

El feature es **complementario a la skill `ideas_creativas` ya existente**, no duplicado. La skill actual genera 10 ideas por LLM cada vez (ephemeral); el Archivo de Ideas las **persiste** (con consentimiento humano). Ambos coexisten.

- ✅ Patrones reutilizables identificados en `agents/creativo/sessions.py`, `agents/knowledge_context.py`, `agents/init_phase.py`.
- ✅ Las 5 preguntas abiertas del proposal tienen respuesta viable.
- ✅ Invariante crítica: **consentimiento humano antes de cada escritura** — se testea desde día uno.
- ⚠️ Riesgo principal: HF Space sirve múltiples usuarios concurrentes → SQLite necesita configuración específica (WAL + timeout).
- 🔀 Decisión abierta más sensible: **integración con `ideas_creativas`** (módulo transversal con comandos `/guardar`, vs. skill separada). Recomendación: **módulo transversal**.

---

## Hallazgo clave: skill `ideas_creativas` ya existe

`agents/creativo/skills.py:54-66` define la skill `ideas_creativas`, registrada y operativa en producción (`app.py:129` con su handler `_responder_ideas_creativas`).

**Qué hace hoy:**
- Genera 10 ideas nuevas por LLM en cada mensaje del usuario.
- Soporta iteraciones: `"aplicá [método] a la idea N"`, `"más ideas"`, `"ficha de la idea N"`, `"ver métodos"`.
- Tiene su propio prompt (`agents/creativo/prompts/system_ideas_creativas.md`, 6.5KB) bien curado.

**Qué NO hace:**
- No persiste nada entre sesiones.
- Si David cierra el chat y vuelve, las 10 ideas que le gustaron se perdieron.
- No hay forma de "guardar la idea 3 para siempre".

**Conclusión:** el Archivo de Ideas es exactamente el **complemento persistente** que falta. La frontera es clara:

| Skill `ideas_creativas` (existe) | Archivo de Ideas (este change) |
|---|---|
| Genera ideas (LLM, ephemeral) | Persiste ideas (SQLite, durable) |
| Se invoca con: "dame ideas para otoño" | Se invoca con: "guardá esta idea", `/ideas`, `/olvidar` |
| Output por mensaje | Output por sesión |

---

## Mapa de codebase — patrones reutilizables

### Patrón A: Persistencia local en `.agent_knowledge/` (de `knowledge_context.py`)

- **Path raíz**: `.agent_knowledge/` (en raíz del repo), **ya cubierto por `.gitignore`** (línea: `.agent_knowledge/`).
- **Helper `ensure_dir()`**: idempotente, mkdir parents exist_ok. Reutilizable.
- **Patrón JSON + companion .md**: cada archivo de datos tiene un `.md` companion con documentación legible (ej: `restaurante.md`). Recomendación: replicar para `ideas.db` → `ideas.md` con schema documentado.
- **Errores explícitos**: `FileNotFoundError` con mensaje accionable ("corre la fase init primero"). Recomendación: misma UX para `ideas.db`.

### Patrón B: Sesiones persistentes con JSON (de `agents/creativo/sessions.py`)

- **Path de sesiones**: `.agent_knowledge/sessions/<sesion_id>.json` con ID formato `YYYYMMDD-HHMMSS-<8 chars random>`.
- **Funciones clave**: `new_sesion_id()`, `guardar_sesion()`, `cargar_sesion()`, `eliminar_sesion()`, `listar_sesiones()`.
- **ISO 8601 timestamps** con segundos y zona local: `_now_iso()`.
- **No-SQL (JSON files)** porque cada sesión es independiente y se accede por ID.
- **Para Archivo de Ideas**: SQLite es preferible porque hay queries (filtrar por categoría, por fecha, por origen). NO reutilizar este patrón literalmente, pero sí los helpers de timestamp y naming.

### Patrón C: Externalización de opciones (de `init_options.json`)

- **Path**: `agents/init_options.json` (3.8KB).
- **Loader**: `init_phase.py:35` carga desde Path relativo.
- **Fallback**: si el JSON no existe, fallback a las opciones hardcoded en código.
- **Variable `OTRO_LITERAL = "__otra__"`** + `SUFIJO_OTRA = "otra (escribir)"` → patrón para permitir entrada libre.
- **Para Archivo de Ideas**: **excelente patrón para**:
  - `agents/ideas_triggers.json` → palabras gatillo editables (David puede agregar/quitar sin tocar código).
  - `agents/ideas_categorias.json` → categorías precargadas (mismo patrón que `productos_dominantes`).

### Patrón D: Dispatcher de skills + handler por skill (de `app.py`)

- **`responder()`** (`app.py:97`) recibe `(mensaje, historial, skill)` y delega al handler correspondiente.
- **`if skill == "proceso_creativo":`** → handler dedicado.
- **`if skill == "ideas_creativas":`** → handler dedicado.
- **Default**: skill `"ficha"`.
- **Para Archivo de Ideas**: dos opciones:
  - **(Recomendada)** Comandos transversales (`/guardar`, `/ideas`, `/olvidar`, `/export-ideas`) detectables en CUALQUIER skill antes del dispatcher. No hace falta nueva skill.
  - **(Alternativa)** Skill nueva `"archivo_ideas"` con su handler dedicado. Más invasivo, requiere cambios en `app.py` y UI de Gradio.

**Recomendación final: comandos transversales.** Más limpio, menos invasivo, mejor UX (no tenés que cambiar de skill para guardar algo que te gustó en otra skill).

### Patrón E: Knowledge loader con context injection (de `app.py` y `knowledge_context.py`)

- `load_restaurante()`, `load_catalogo()` se inyectan al `system_prompt` antes de cada llamada al LLM.
- **Para Archivo de Ideas**: el chef podría cargar las ideas previas y mencionarlas como contexto al usuario (ej: "ya tenés 3 ideas guardadas sobre fermentos"). Esto es **out of scope** para v1 (decidido en proposal), pero el patrón está disponible para v2.

### Patrón F: CLI main loop (de `agents/creativo/agent.py`)

- `modo_interactivo()` con selector de skill + dispatcher.
- `_loop_ideas_creativas()` loop dedicado por skill.
- **`PROCESO_COMANDOS`**: set de strings que se detectan al inicio del mensaje.
- **Para Archivo de Ideas**: agregar el dispatcher al `responder()` (HF) Y al `_loop_*` (CLI). Mismo set de comandos en ambos.

---

## Validación de las 5 open questions del proposal

### Q1: Palabras gatillo para la heurística de propuesta

**Recomendación**: JSON externo `agents/ideas_triggers.json` con lista editable.

```json
{
  "gatillos_propuesta": [
    "se me ocurre",
    "se me ocurrió",
    "algún día",
    "alguna vez",
    "podríamos probar",
    "podríamos hacer",
    "estaría bueno",
    "sería interesante",
    "qué te parece si",
    "qué tal si",
    "tengo una idea",
    "me dio por pensar",
    "estoy pensando en",
    "estuve pensando en"
  ],
  "umbral_minimo_palabras": 3,
  "cooldown_turnos": 2
}
```

**Reglas**:
- Match case-insensitive, substring (no regex compleja).
- Solo propone si el mensaje tiene ≥ `umbral_minimo_palabras` palabras (evita dispararse con "se me ocurre").
- Cooldown: no proponer más de 1 vez cada N turnos (evitar spam).
- **El agente NUNCA guarda automáticamente. Solo PROPONE.**

### Q2: Categorías precargadas vs libres

**Recomendación**: precargadas en JSON + free-form con `SUFIJO_OTRA`.

```json
// agents/ideas_categorias.json
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

- Mismo patrón que `init_options.json` (categorías con fallback en código si el JSON no existe).
- Sugerencia automática de categoría por heurística simple (no LLM): match de keywords en la idea contra cada categoría.
- Si el usuario dice "otro (escribir)" → input libre → se guarda con la categoría custom.

### Q3: Sugerencia de categoría al guardar

**Recomendación**: el agente sugiere una categoría en el mensaje de propuesta ("creo que esto encaja en `técnica`, pero vos decidís"). El usuario puede:
- Aceptar la sugerencia
- Elegir otra de la lista
- Escribir una custom

**No usar LLM para sugerir categoría** (caro, lento, inconsistente). La heurística de keywords es suficiente.

### Q4: Comportamiento cuando SQLite está bloqueado / unwritable

**Recomendación**: fail-safe con mensaje claro.

- Si el archivo `.agent_knowledge/ideas.db` no se puede abrir (permisos, corrupto, etc.) → **NO crashear el chat**. Loggear el error y devolver un mensaje al usuario tipo: "⚠️ No pude acceder al archivo de ideas (permisos o DB corrupta). Tu idea no se guardó, pero podés copiarla manualmente. Detalle técnico: [error]".
- Tests: `test_storage_locked.py` simula DB bloqueada y verifica que el chat sigue funcionando.
- Recovery: si el archivo está corrupto, ofrecer regenerar (con confirmación explícita y export del actual antes de borrar).

### Q5: Consentimiento en HF Space (Gradio) vs CLI

**Recomendación**: misma semántica, distinto render.

| Contexto | CLI (local) | HF Space (Gradio chat) |
|---|---|---|
| Comando explícito | `/guardar "mi idea"` → guarda inmediato (ya es consentimiento) | `/guardar "mi idea"` → guarda inmediato (ya es consentimiento) |
| Propuesta del agente | Imprime: "¿Querés que guarde esto como idea? (s/n)" + lee siguiente input | Imprime: "¿Querés que guarde esto como idea?" + un **botón de Gradio** debajo con [Sí, guardar] [No, descartar] |
| Estado pendiente | Variable global `propuesta_pendiente` con la idea a confirmar | `gr.State` con la idea pendiente; el botón lee el state y confirma |

**Diferencia clave**: en CLI se usa el siguiente input del usuario. En HF Space se usa un botón explícito (más seguro: el usuario clickea, no hay ambigüedad de "¿contestó que sí o que no?").

**Tests**: `test_consent_hf.py` simula el flujo de state + botón. `test_consent_cli.py` simula el input.

---

## Decisiones arquitectónicas para `sdd-spec`

### D1: Storage — SQLite en `.agent_knowledge/ideas.db`

| Aspecto | Decisión | Razón |
|---|---|---|
| Engine | SQLite 3 (stdlib, no dependencias) | Sin nuevas deps, robusto, suficiente para <100k ideas/año |
| Path | `.agent_knowledge/ideas.db` | Consistente con `knowledge_context.py`, ya cubierto por `.gitignore` |
| Schema companion | `.agent_knowledge/ideas.md` con documentación | Mismo patrón que `restaurante.md` |
| WAL mode | Habilitado (`PRAGMA journal_mode=WAL`) | Concurrencia en HF Space |
| `check_same_thread` | `False` | HF Space puede servir múltiples users |
| `timeout` | `5.0` segundos | Fail-fast en lugar de lock indefinido |

### D2: Schema SQLite (validar el del proposal)

```sql
CREATE TABLE ideas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,              -- ISO 8601 con timezone
    idea TEXT NOT NULL,                    -- texto literal (sin límite, SQLite lo maneja)
    categoria TEXT,                        -- de ideas_categorias.json o custom
    contexto TEXT,                         -- qué se estaba hablando (skill, mensaje previo, etc.)
    confirmada_por_usuario INTEGER NOT NULL DEFAULT 0,  -- 1 = sí, 0 = no
    origen TEXT NOT NULL,                  -- 'comando' | 'propuesta_agente' | 'ideas_creativas_N'
    origen_skill TEXT                      -- 'ficha' | 'ideas_creativas' | 'proceso_creativo' | 'manual'
);

CREATE INDEX idx_ideas_created_at ON ideas(created_at DESC);
CREATE INDEX idx_ideas_categoria ON ideas(categoria);
CREATE INDEX idx_ideas_origen_skill ON ideas(origen_skill);
```

**Cambios sobre el proposal original**:
- ➕ `origen_skill`: saber de qué skill vino la idea (útil para futuro retrieval contextual).
- ➕ `origen`: explícito para distinguir comando / propuesta / extracción de otra skill.
- ➕ Índices en `created_at`, `categoria`, `origen_skill` (queries esperadas).

### D3: Trigger — mixto comando + propuesta del agente

- **Comando explícito**: `/guardar [texto]` o `/guardar [N]` (donde N es índice de la última respuesta de `ideas_creativas`).
- **Propuesta del agente**: heurística de keywords (Q1) → mensaje "¿Querés guardar esto? [Sí/No]" → solo guarda si el usuario confirma.
- **El agente NUNCA guarda sin confirmación**. Sin excepciones. Esto es invariante dura.

### D4: UX de consentimiento — comandos transversales

- Comandos disponibles en TODAS las skills (`ficha`, `ideas_creativas`, `proceso_creativo`).
- Detección de comandos: ANTES del dispatcher de skill (en `responder()` y en `_loop_*`).
- Estado de consentimiento: en memoria (dict thread-safe), NO persistente (la propuesta muere si el usuario no contesta en la misma sesión).

### D5: RGPD — sin cifrado + botones olvidar/export

- **Sin cifrado en reposo**: la DB vive en la máquina local de David, él es el único con acceso físico. SQLite no cifra por default y agregarlo mete complejidad innecesaria.
- **`/olvidar`**: borra todas las ideas. Pide confirmación explícita ("¿Seguro? Esto borra TODO. Escribí `olvidar todo` para confirmar").
- **`/olvidar N`**: borra la idea N (la última guardada, o la N según el listado).
- **`/export-ideas`**: exporta a `.agent_knowledge/ideas_export_<timestamp>.json` (en formato portable, no SQLite).
- **Tests de RGPD**: `test_rgpd_export.py`, `test_rgpd_olvidar.py`.

### D6: Integración con skill `ideas_creativas` existente

- **Comando nuevo**: `/guardar N` dentro de la skill `ideas_creativas` → extrae la idea N de la última respuesta y la guarda con `origen_skill='ideas_creativas'`, `origen='ideas_creativas_N'`.
- **No modificar** el prompt de `ideas_creativas` (excepto agregar al final: "También podés usar `/guardar N` para guardar la idea N en tu archivo de ideas").
- **No modificar** el handler `_responder_ideas_creativas` — el dispatcher de comandos transversales actúa ANTES.

### D7: Out of scope (reconfirmar)

- ❌ El chef NO consulta automáticamente la DB al generar fichas.
- ❌ NO hay cifrado en reposo.
- ❌ NO hay sync entre dispositivos.
- ❌ NO hay categorización automática con LLM.
- ❌ NO hay "sugerencias cruzadas" automáticas.
- ❌ NO se commitea la DB ni el export a git.

---

## Riesgos

| ID | Riesgo | Severidad | Mitigación |
|---|---|---|---|
| **R1** | Consentimiento débil (UX confusa → guarda sin permiso real) | 🔴 CRÍTICO | Tests desde día uno (`test_consent_cli.py`, `test_consent_hf.py`); invariante dura en código (primera assertion de `consent.py`); code review obligatorio pre-merge |
| **R2** | El agente propone guardar cosas que David no quería (falsos positivos) | 🟠 ALTO | Comando `/deshacer` que borra la última guardada; cooldown de propuestas; propuesta es SIEMPRE explícita ("¿Querés guardar esto?") |
| **R3** | Concurrencia SQLite en HF Space (múltiples usuarios) | 🟡 MEDIO | WAL mode + `check_same_thread=False` + `timeout=5.0`; tests con threads concurrentes |
| **R4** | Schema se vuelve rígido (David quiere nuevas categorías) | 🟡 MEDIO | Categorías en JSON editable (`agents/ideas_categorias.json`); campo `categoria` libre (sin FK constraint) |
| **R5** | Comandos que David no recuerda | 🟡 MEDIO | Comando `/ayuda` que lista todos los comandos del archivo de ideas; sección "Archivo de ideas" en la landing con los comandos visibles |
| **R6** | Ruptura de compatibilidad con MVP-0.5 (Chef Creativo en HF Space) | 🟢 BAJO | Cambios estrictamente aditivos en `app.py` (nuevo dispatcher de comandos transversales, sin tocar handlers existentes); tests de regresión con la skill `ficha` y `ideas_creativas` |
| **R7** | HF cachea deps y rompe SQLite (improbable, SQLite es stdlib) | 🟢 BAJO | SQLite es stdlib en Python 3.4+, no hay riesgo de version mismatch |
| **R8** | Export contiene datos sensibles que David no quiere compartir | 🟢 BAJO | `/export-ideas` es local, NO sube a ningún lado; mensaje claro en la confirmación |

---

## Estructura de archivos propuesta (para `sdd-tasks`)

```
agents/
├── memoria/                              [NUEVO MÓDULO]
│   ├── __init__.py
│   ├── storage.py                        [NUEVO] SQLite + schema + queries
│   ├── consent.py                        [NUEVO] invariante de consentimiento
│   ├── triggers.py                       [NUEVO] heurística de propuesta
│   ├── commands.py                       [NUEVO] /guardar, /ideas, /olvidar, /export-ideas, /ayuda, /deshacer
│   └── formatters.py                     [NUEVO] formato de salida para chat
├── ideas_categorias.json                 [NUEVO] categorías precargadas
├── ideas_triggers.json                   [NUEVO] palabras gatillo
├── creativo/
│   ├── agent.py                          [MODIFICADO] dispatcher de comandos transversales en _loop_*
│   └── prompts/system_ideas_creativas.md [MODIFICADO] agregar al final: "/guardar N guarda la idea N en tu archivo de ideas"
app.py                                    [MODIFICADO] dispatcher de comandos transversales en responder()
.agent_knowledge/
├── ideas.db                              [NUEVO, autogenerado, ignorado por git]
└── ideas.md                              [NUEVO] documentación del schema
tests/
├── test_memoria_storage.py               [NUEVO] CRUD básico + concurrencia
├── test_memoria_consent_cli.py           [NUEVO] consentimiento en CLI (input)
├── test_memoria_consent_hf.py            [NUEVO] consentimiento en HF (state + botón)
├── test_memoria_triggers.py              [NUEVO] heurística de gatillos
├── test_memoria_commands.py              [NUEVO] /guardar, /ideas, /olvidar, /export-ideas, /ayuda
├── test_memoria_rgpd.py                  [NUEVO] /olvidar + /export-ideas
└── test_regresion_skills.py              [NUEVO] verificar que /guardar no rompe ficha/ideas_creativas/proceso_creativo
docs/
└── index.html                            [MODIFICADO, en sesión de archive] sección "Archivo de ideas"
```

**Líneas estimadas**: ~600-800 de código nuevo + ~300-400 de tests + ~50 de cambios en `app.py` y prompts. Total: ~1000-1250 líneas → **cabe en un solo PR** (<400 líneas por archivo individual, ninguno excede el review budget de 400).

---

## Open items para `sdd-proposal`

1. **Validación con David** (interactiva, `executionMode: interactive`):
   - ¿Le cierran las 6 decisiones tentativas (D1-D6)?
   - ¿Nombres de comandos OK? (`/guardar`, `/ideas`, `/olvidar`, `/export-ideas`, `/ayuda`, `/deshacer`)
   - ¿Palabras gatillo OK o agregar/quitar alguna?
   - ¿Categorías precargadas OK o agregar/quitar alguna?
   - ¿Schema SQLite OK o agregar/quitar algún campo?

2. **Decisión de UX integration**:
   - Recomendación tomada: **comandos transversales** (disponibles en todas las skills).
   - Si David prefiere un tab/botón separado en la UI de Gradio → requiere rediseño y más cambios.

3. **Out of scope** — confirmar que v2 NO incluye:
   - Retrieval automático del chef desde la DB.
   - Sugerencias cruzadas.
   - Sync entre dispositivos.
   - Cifrado en reposo.

---

## Resultado de fase

```yaml
status: explore-complete
artifacts:
  - openspec/changes/archivo-de-ideas/explore.md  (este archivo)
next_recommended: sdd-proposal
needs:
  - Validación con David de las decisiones tentativas (sesión interactiva)
  - Confirmación de nombres de comandos y categorías
  - Confirmación de out-of-scope
risks:
  - R1: consentimiento débil (CRÍTICO, mitigado con tests desde día 1)
  - R3: concurrencia SQLite en HF Space (MEDIO, mitigado con WAL + timeout)
  - R6: ruptura de compatibilidad con MVP-0.5 (BAJO, mitigado con cambios aditivos)
skill_resolution: none
```

---

**Próximo paso**: `sdd-proposal` ajusta el proposal original con estos hallazgos y lo presenta para aprobación de David. Antes de eso, **sesión interactiva** con David para validar las decisiones tentativas.