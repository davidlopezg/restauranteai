# Proposal — Archivo de Ideas

> **Change**: `archivo-de-ideas`
> **Phase**: `sdd-proposal` ✅
> **Status**: 🟢 Aprobado por David (validación interactiva cerrada)
> **Created**: 2026-07-02
> **Owner**: David López Gamero
> **Orquestador**: el Gentleman (Pi)

---

## 1. Why

### 1.1 Problema de negocio

David (hostelero, Sol de Nit) **pierde ideas valiosas cada sesión**. El escenario es cotidiano:

> "Che, se me ocurrió probar kumquat en el postre de temporada… algún día habría que hacer un menú de setas… el cliente X siempre pide algo fuera de carta… el de la mesa 7 me pidió una opción sin gluten…"

Hoy, esas ideas se generan conversacionalmente y **se evaporan al cerrar el chat**. La skill `ideas_creativas` (ya en producción desde MVP-0.5) genera 10 ideas por LLM por mensaje — pero son **efímeras**, no hay forma de guardarlas para volver a ellas dos semanas después.

Costo operativo real: David repite contextos. Cuando vuelve a una conversación con "esa idea de fermentos que te dije la semana pasada", el chef arranca en blanco. Eso es fricción, pérdida de oportunidad, y un techo invisible sobre cuánto puede delegarle al agente.

### 1.2 Brecha del estado actual

| Hoy | Mañana (con este change) |
|---|---|
| Skill `ideas_creativas` genera 10 ideas nuevas por mensaje, sin memoria | Las ideas que David quiera guardar **persisten entre sesiones** |
| No existe forma de "guardar la idea 3 para siempre" | `/guardar 3` la guarda, `/ideas` la lista, `/olvidar 3` la borra |
| Roadmap Fase 2 (Agente Memoria) bloqueado — sin decisiones de storage/consentimiento/RGPD | Las decisiones quedan tomadas en el caso concreto más valioso, **patrón replicable** para memorias futuras |
| Cuestionario fijo de 15 dimensiones en `restaurante.json` es lo único persistente | David pasa a tener una **memoria viva de sus propias ideas** |

### 1.3 Lo que destraba

- **Roadmap Fase 2 destrabado**: las decisiones tomadas para Archivo de Ideas (storage, consentimiento, RGPD, UX en HF + CLI) son las decisiones de fondo que el Agente Memoria necesita. Este change es el **caso concreto** que valida el patrón; futuras memorias (preferencias, catálogo dinámico) lo replican.
- **Memory layer del stack**: con este change, el proyecto pasa de "stateless por sesión" a "stateless por sesión + persistente opt-in por idea". Es un antes/después arquitectónico, no solo un feature.
- **Inversión de retorno alta con scope acotado**: el alcance de v1 está deliberadamente recortado (v1 NO modifica el prompt de `ideas_creativas`, NO consulta automática al chef, NO sincroniza entre dispositivos). Es la **primera ficha** del memory layer, no el memory layer entero.

---

## 2. What changes

### 2.1 Capacidades nuevas

- **Almacenamiento persistente de ideas** en SQLite local (`.agent_knowledge/ideas.db`), WAL mode, concurrencia segura para HF Space.
- **Consentimiento humano explícito como invariante dura**: el único disparador válido para guardar es un **comando explícito del usuario**. No hay heurística, no hay propuesta del agente. El comando ES el consentimiento. Sin excepciones.
- **Comando `/guardar` con tres variantes**:
  - `/guardar [texto libre]` — guarda el texto literal. Funciona en cualquier skill. Es la variante más común.
  - `/guardar` (sin argumentos) — guarda el **último mensaje del asistente** como idea (extrae el contenido reciente).
  - `/guardar N` — guarda la idea N del último mensaje del asistente que contenía una lista numerada. Falla con mensaje claro si el último mensaje del asistente no tiene lista numerada.
- **Edición post-guardado**: comando `/editar N [nuevo texto]` — la idea guardada es editable; el campo `updated_at` registra la última modificación.
- **Detección de duplicados**: match exacto + fuzzy (≥80% similitud) implementado en `storage.py`. Si hay duplicado, se le ofrece al usuario navegar al existente o guardar igual.
- **Contador visible opcional**: después de cada guardado el agente muestra `📁 X guardadas`. Opt-out con `/silenciar-contador`.
- **RGPD desde día uno**: comandos `/olvidar [todo|N]` (con confirmación explícita) y `/export-ideas` (JSON portable en `.agent_knowledge/`).
- **Comandos transversales** disponibles en TODAS las skills (`ficha`, `ideas_creativas`, `proceso_creativo`). Detectados **ANTES del dispatcher de skill**, tanto en `responder()` (HF Gradio) como en `_loop_*` (CLI).

### 2.2 Capacidades NO cambiadas

- Skill `ideas_creativas` intacta en su handler y su prompt (no se toca `_responder_ideas_creativas` ni `system_ideas_creativas.md` para esta v1).
- Skill `proceso_creativo` intacta (no se toca `_responder_proceso_creativo`).
- Skill `ficha` intacta.
- MVP-0.5 (Chef Creativo en HF Space) **sin regresión**. Los cambios en `app.py` son estrictamente aditivos: un dispatcher nuevo antes del switch de skill.
- El chef **NO consulta** la DB de ideas automáticamente al generar fichas (es v2).
- `restaurante.json`, `catalogo_platos.json`, `init_options.json` intactos.

### 2.3 Comando `/guardar` — comportamiento por variante

| Variante | Input | Comportamiento | Falla clara |
|---|---|---|---|
| Texto libre | `/guardar "probar kumquat en el postre"` | Inserta row con `origen='comando'`, `origen_skill=<skill_activa>`, `confirmada_por_usuario=1` | N/A |
| Sin args | `/guardar` | Extrae el contenido del último assistant message y lo guarda entero | Si no hay historial previo, muestra "no tengo un mensaje reciente para guardar" |
| Por número | `/guardar 3` (después de una lista de ideas) | Parsea la línea "3." del último assistant message con patrón numerado, guarda solo esa idea | Si el último assistant message no contiene lista numerada, muestra "el último mensaje no es una lista numerada" y sugiere `/guardar` o `/guardar [texto]` |

Invariante: en las tres variantes, **`/guardar` ES el consentimiento**. No hay segundo turno, no hay confirmación adicional, no hay heurística previa. Eso es lo que David eligió.

---

## 3. Scope (in / out)

### 3.1 In scope (v1)

- Módulo `agents/memoria/` con `storage.py`, `commands.py`, `formatters.py` (consent NO es módulo separado porque el invariante vive dentro de `storage.py` y `commands.py` — comando directo ES consentimiento, no hace falta una capa de consent explícita).
- Archivo `.agent_knowledge/ideas.db` con schema definido (ver D2 abajo), autogenerado en runtime, cubierto por `.gitignore`.
- Companion `.agent_knowledge/ideas.md` con documentación del schema (patrón replicado de `knowledge_context.py` con `restaurante.md`).
- Dispatcher de comandos transversales en `app.py` (`responder()`) y en `agents/creativo/agent.py` (`_loop_*`).
- Tests (ver criterios de éxito abajo).

### 3.2 Out of scope (v1) — explícito

| Out | Razón |
|---|---|
| **NO** hay propuesta automática del agente / sin heurística de keywords / sin `agents/ideas_triggers.json` / sin `agents/memoria/triggers.py` / sin `test_memoria_triggers.py` | **Q1 lockeada por David: solo comando explícito**. Esto elimina el mayor riesgo de falsos positivos y la complejidad de la capa de consentimiento en 2 turnos. |
| **NO** hay cifrado en reposo | **D5**: la DB vive en la máquina local de David; cifrar añade complejidad sin beneficio real en este contexto. |
| **NO** hay sync entre dispositivos | v2 si David lo pide; problema RGPD no trivial. |
| **NO** hay categorización automática con LLM | Q2 + Q3 lockeadas: las categorías vienen del JSON precargado (en v2 ver abajo) + heurística de keywords simple; sin LLM. |
| **NO** hay retrieval automático del chef desde la DB | El chef sigue arrancando por skill/contexto, no consulta ideas previas. Eso es v2. |
| **NO** se commitean `.agent_knowledge/ideas.db` ni exports a git | Ya cubierto por `.gitignore` (línea `.agent_knowledge/`). |
| **NO** se modifican las skills existentes | `ideas_creativas`, `proceso_creativo`, `ficha` quedan intactas. La integración es solo dispatcher transversal. |
| **NO** hay relación catálogo ↔ ideas en v1 | **Q5 lockeada**: sí en v2 al final de `proceso_creativo` cuando un plato se diseña completo, se le ofrece linkearlo a ideas del archivo. |

---

## 4. Affected areas

Archivos nuevos/modificados para esta change. **Listado refinado desde el explore** (se eliminan `triggers.py`, `ideas_triggers.json`, `test_memoria_triggers.py` y el test/consent_de_2_turnos por Q1).

### 4.1 Crear

```
agents/memoria/__init__.py                                 [NUEVO]
agents/memoria/storage.py                                  [NUEVO] SQLite + schema + CRUD + detección de duplicados (exacta + fuzzy ≥80%)
agents/memoria/commands.py                                 [NUEVO] /guardar (3 variantes), /ideas, /editar, /olvidar, /export-ideas, /ayuda, /silenciar-contador
agents/memoria/formatters.py                               [NUEVO] formato de salida para chat (CLI y Gradio)

agents/ideas_categorias.json                               [NUEVO] categorías precargadas + "otro (escribir)" (libre)

.agent_knowledge/ideas.db                                  [NUEVO, autogenerado en runtime, en .gitignore]
.agent_knowledge/ideas.md                                  [NUEVO] documentación del schema

tests/test_memoria_storage.py                              [NUEVO] CRUD básico + concurrencia WAL
tests/test_memoria_commands.py                             [NUEVO] /guardar (3 variantes), /editar, /ideas, /olvidar, /export-ideas, /ayuda
tests/test_memoria_duplicates.py                           [NUEVO] detección exacta + fuzzy ≥80%
tests/test_memoria_counter.py                              [NUEVO] "📁 X guardadas" + opt-out /silenciar-contador
tests/test_memoria_rgpd.py                                 [NUEVO] /olvidar + /export-ideas (incluye confirmación explícita de olvidar)
tests/test_regresion_skills.py                             [NUEVO] /guardar en ficha / ideas_creativas / proceso_creativo sin romper flujos
```

### 4.2 Modificar

```
app.py                                                     [MODIFICADO] dispatcher transversal de comandos en responder() ANTES del switch por skill — aditivo, no rompe handlers existentes
agents/creativo/agent.py                                   [MODIFICADO] dispatcher transversal en _loop_ficha / _loop_ideas_creativas / _loop_proceso_creativo (CLI)
openspec/changes/archivo-de-ideas/proposal.md              [este archivo, reemplazado por la versión final]
openspec/changes/archivo-de-ideas/spec.md                  [próxima fase]
openspec/changes/archivo-de-ideas/design.md                [próxima fase]
openspec/changes/archivo-de-ideas/tasks.md                 [próxima fase]
```

### 4.3 NO se crean

```
~ agents/memoria/triggers.py                              [DESCARTADO por Q1]
~ agents/memoria/consent.py                               [DESCARTADO por Q1] (no hay 2-turn consent)
~ agents/ideas_triggers.json                               [DESCARTADO por Q1]
~ tests/test_memoria_triggers.py                           [DESCARTADO por Q1]
~ tests/test_memoria_consent.py                           [DESCARTADO por Q1] (no hay consent explícito fuera del comando)
```

---

## 5. Decisiones lockeadas (D1–D6 + Q1–Q5)

### Decisiones técnicas (de `sdd-explore`)

- **D1 — Storage**: SQLite 3 stdlib en `.agent_knowledge/ideas.db`. WAL mode (`PRAGMA journal_mode=WAL`), `check_same_thread=False`, `timeout=5.0`. Sin nuevas dependencias.
- **D2 — Schema (8 campos + `updated_at`)**: `id, created_at, updated_at, idea, categoria, contexto, confirmada_por_usuario, origen, origen_skill`. Índices en `created_at DESC`, `categoria`, `origen_skill`.
  ```sql
  CREATE TABLE ideas (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      created_at TEXT NOT NULL,           -- ISO 8601 con timezone
      updated_at TEXT,                    -- ISO 8601, NULL hasta primer edit
      idea TEXT NOT NULL,
      categoria TEXT,                     -- de ideas_categorias.json o custom
      contexto TEXT,                      -- skill activa + hash del último mensaje si aplica
      confirmada_por_usuario INTEGER NOT NULL DEFAULT 1,  -- siempre 1 en v1 (comando es consentimiento)
      origen TEXT NOT NULL,               -- 'comando' | 'ideas_creativas_N'
      origen_skill TEXT                   -- 'ficha' | 'ideas_creativas' | 'proceso_creativo'
  );
  CREATE INDEX idx_ideas_created_at ON ideas(created_at DESC);
  CREATE INDEX idx_ideas_categoria ON ideas(categoria);
  CREATE INDEX idx_ideas_origen_skill ON ideas(origen_skill);
  ```
- **D3 — Trigger**: ÚNICAMENTE comando explícito `/guardar`. NO hay auto-propuesta. Sin heurística. **Invariante: el comando es el consentimiento.**
- **D4 — Integración**: comandos transversales disponibles en TODAS las skills. Detectados ANTES del dispatcher de skill en `app.py:responder()` y en `agents/creativo/agent.py:_loop_*`. **NO es una skill nueva.**
- **D5 — RGPD**: sin cifrado en reposo + `/olvidar [todo|N]` (con confirmación explícita) + `/export-ideas` (JSON portable en `.agent_knowledge/`).
- **D6 — Out of scope v1**: ver §3.2 arriba.

### Decisiones de producto (de la sesión interactiva con David)

- **Q1 — Momento del guardado**: SOLO comando `/guardar`. NO hay propuesta automática del agente. *(Esta decisión eliminó `agents/ideas_triggers.json`, `agents/memoria/triggers.py`, la lógica de consentimiento en 2 turnos y `test_memoria_triggers.py` del scope. Es la decisión de fondo del change.)*
- **Q2 — Duplicados**: detección con match exacto + fuzzy ≥80% similitud, implementada en `storage.py`. Si hay duplicado probable, se le ofrece al usuario "ya tenés algo parecido (#ID). ¿Guardar igual?"
- **Q3 — Edición post-guardado**: SÍ, editable vía `/editar N [nuevo texto]`. Campo `updated_at` agregado al schema para registrar la última modificación.
- **Q4 — Contador visible**: SÍ, después de cada guardado se muestra `📁 X guardadas`. Opt-out con `/silenciar-contador` (estado en memoria; vuelve a activarse al reiniciar la sesión).
- **Q5 — Relación con catálogo**: NO en v1. SÍ en v2 al final de `proceso_creativo` (cuando un plato nuevo está completamente diseñado, prompt "estos 3 platos nuevos podrían linkearse a las ideas #X, #Y, #Z que ya tenés guardadas. ¿Querés linkear?").

---

## 6. Success criteria

Cada criterio es **observable y testeable** desde el primer TDD en `sdd-apply`.

### 6.1 Funcionales

- **C1**: `/guardar "mi idea"` guarda la fila y devuelve confirmación con el ID y el contador `📁 X guardadas`.
- **C2**: `/guardar` (sin args) guarda el último mensaje del assistant.
- **C3**: `/guardar 3` después de un mensaje del assistant con lista numerada guarda la idea #3 exacta. Si el último mensaje no es una lista numerada, devuelve error claro sugiriendo `/guardar` o `/guardar [texto]`.
- **C4**: Duplicados exactos detectados → ofrecer ver el existente en lugar de duplicar.
- **C5**: Duplicados fuzzy ≥80% detectados (test con dos textos casi idénticos con cambios menores) → ofrecer ver existente o guardar igual.
- **C6**: `/editar 3 "texto nuevo"` actualiza la fila 3, marca `updated_at`, devuelve confirmación.
- **C7**: Contador `📁 X guardadas` se muestra después de cada guardado. Después de `/silenciar-contador` deja de mostrarse en la sesión actual.
- **C8**: `/olvidar todo` pide confirmación explícita ("escribí `olvidar todo` para confirmar"); tras confirmar, la DB queda vacía.
- **C9**: `/olvidar N` borra la idea N pidiendo confirmación.
- **C10**: `/export-ideas` crea `.agent_knowledge/ideas_export_<timestamp>.json` con todas las filas en formato portable (id, created_at, updated_at, idea, categoria, contexto, origen, origen_skill).

### 6.2 No regresión

- **C11**: `ficha` (default), `ideas_creativas` y `proceso_creativo` siguen respondiendo idéntico a inputs no-comando. Test: snapshot de respuesta a 10 inputs canónicos por skill.
- **C12**: Los handlers existentes (`_responder_proceso_creativo`, `_responder_ideas_creativas`, flujo de `ficha`) **no se modifican**. El dispatcher de comandos transversales actúa antes y devuelve un dict response cuando matchea un comando.
- **C13**: `.agent_knowledge/ideas.db` está cubierto por `.gitignore` y NO se commitea (verificable con `git check-ignore .agent_knowledge/ideas.db`).

### 6.3 Calidad

- **C14**: Tests en `tests/test_memoria_*.py` corren contra una DB de tests (temporal, pytest fixture) — `storage.py` acepta un path injectable para no contaminar `.agent_knowledge/`.
- **C15**: Concurrencia: dos escrituras concurrentes en HF Space (dos usuarios guardan al mismo tiempo) NO corrompen la DB. Test con `ThreadPoolExecutor` + assertions de `last_insert_rowid` y `count(*)`.
- **C16**: Tests verdes antes de merge (evidencia TDD en `sdd-apply`).

---

## 7. Risks

| ID | Riesgo | Severidad | Mitigación |
|---|---|---|---|
| **R1** | El consentimiento se interpreta mal (UX de `/guardar` confunde) y el usuario termina guardando sin querer | 🟢 BAJO (antes ALTO) | **Q1 lockeada: el comando ES el consentimiento. Sin heurística ni propuesta.** No hay capa de consent separada porque no hace falta: la fricción de "tengo que escribir /guardar" es la UX de opt-in. Test C1–C3 cubren el flujo. |
| **R2** | El agente propone guardar cosas que David no quería (falsos positivos) | 🟢 BAJO (antes ALTO) | **Riesgo eliminado por Q1**: ya no hay heurística de propuesta. `/guardar` es 100% opt-in por construcción. `/editar` y `/olvidar` dan la red de seguridad si David se arrepiente. |
| **R3** | Concurrencia SQLite en HF Space (múltiples usuarios simultáneos) | 🟡 MEDIO | WAL mode + `check_same_thread=False` + `timeout=5.0` + test C15 con threads concurrentes. Fallback graceful: si la DB está locked >5s, mensaje "⚠️ no pude guardar ahora, intentá de nuevo". |
| **R4** | Schema se vuelve rígido (David quiere nuevas categorías) | 🟡 MEDIO | Categorías en JSON editable (`agents/ideas_categorias.json`); campo `categoria` libre (sin FK constraint); posibilidad de "otro (escribir)" para custom. |
| **R5** | David olvida los comandos | 🟡 MEDIO | `/ayuda` lista todos los comandos del archivo de ideas. En esta v1, sección en `/ayuda` visible; en v2, sección en `docs/index.html` (landing). |
| **R6** | Ruptura de compatibilidad con MVP-0.5 (Chef Creativo en HF Space) | 🟢 BAJO | Cambios estrictamente aditivos en `app.py` (nuevo dispatcher de comandos transversales, sin tocar handlers existentes); tests C11–C12 de regresión por skill. |
| **R7** | HF cachea deps y rompe SQLite (improbable; SQLite es stdlib) | 🟢 BAJO | SQLite es stdlib en Python 3.4+, sin riesgo de version mismatch. |
| **R8** | Export contiene datos sensibles que David no quiere compartir | 🟢 BAJO | `/export-ideas` es estrictamente local (escribe en `.agent_knowledge/`), NO sube a ningún lado. Mensaje claro en la confirmación: "se creó un archivo local, no se subió a ningún servidor". |

---

## 8. Open questions

### 8.1 Lockeadas en esta sesión (resueltas)

- ✅ ~~Q1 trigger moment~~ → **LOCKED**: solo comando `/guardar`. Sin heurística, sin propuesta automática.
- ✅ ~~Q2 duplicates~~ → **LOCKED**: detección exacta + fuzzy ≥80% en `storage.py`.
- ✅ ~~Q3 edit post-save~~ → **LOCKED**: editable vía `/editar N [texto]`; schema incluye `updated_at`.
- ✅ ~~Q4 counter visible~~ → **LOCKED**: `📁 X guardadas` después de cada guardado; opt-out con `/silenciar-contador`.
- ✅ ~~Q5 catalog relation~~ → **LOCKED**: NO en v1, SÍ en v2 al final de `proceso_creativo`.

### 8.2 Nuevas o pendientes (a validar en `sdd-spec` o `sdd-design`)

- **N1 — Comando de edición**: se propone **`/editar N [nuevo texto]`** (variante pensada para mantener consistencia con `/olvidar N`). Si David prefiere `/modificar N`, `/cambiar N` o `/update N`, se cambia en `sdd-design`. **A validar.**
- **N2 — Semántica de sync en HF Space (múltiples usuarios)**: la DB vive en `.agent_knowledge/ideas.db` que es **un único archivo**. En HF Space, si hay múltiples usuarios concurrentes en la misma instancia de Space, la DB contendrá ideas de **todos los usuarios mezcladas** (con WAL protegiendo la integridad, pero sin partición por usuario).
  - **v1 (este change)**: se asume **single-user local**. David es hoy el único usuario; el HF Space personal es de él. La DB es "la DB de David", no una DB multi-tenant.
  - **Si en el futuro el HF Space se expone a otros usuarios (público)**: pasar a `data/ideas_<user_hash>.db` con un hash del session_id de Gradio. NO se hace en v1.
  - **A documentar** en el companion `.agent_knowledge/ideas.md` para que quede explícito.
- **N3 — Categorías precargadas exactas**: la lista tentativa es `["concepto", "plato", "técnica", "producto", "proveedor", "menú completo", "ocasión/evento", "restricción", "otro (escribir)"]`. Si David quiere ajustar, se ajusta en `sdd-design` antes de `agents/ideas_categorias.json`.
- **N4 — Formato de salida del contador**: `📁 X guardadas` (propuesto). Variante alternativa: `📁 Guardadas: X`. **Trivial, se valida en `sdd-design`.**
- **N5 — Confirmación explícita de `/olvidar todo`**: se propone tipear exactamente `olvidar todo` para confirmar. Variante más segura: tipear el ID random de 6 chars que el prompt muestra. Para v1 alcanza con tipear `olvidar todo`, pero **se deja nota en design** para que David decida.

---

## 9. Rollback

Si el change causa problemas en producción (David reporta bug crítico, regresión en MVP-0.5, problema de RGPD):

### 9.1 Pasos de rollback

1. **Revertir el merge del PR** que introduce el change. Esto es git revert estándar. Los handlers de skills (`_responder_proceso_creativo`, `_responder_ideas_creativas`, ficha) **no se tocan**, así que revirtiendo el commit se vuelve al estado MVP-0.5 intacto.
2. **Eliminar el dispatcher transversal** de `responder()` (HF) y `_loop_*` (CLI). Esto está incluido en la reversión porque vive en los archivos modificados.
3. **Decidir qué hacer con `.agent_knowledge/ideas.db`**: la DB **sobrevive a la reversión** porque es un archivo ignorado por git. Si David quiere perderla (porque los datos estaban corruptos o porque el rollback fue por desconfianza), se borra manualmente. Si quiere conservarla (porque los datos están bien y va a usar el feature en otro momento), se deja. Es decisión de David.

### 9.2 Por qué el rollback es seguro

- Cambios **estrictamente aditivos** en código (sin modificar handlers existentes).
- DB es local e ignorada por git: no contamina el historial del repo.
- Tests C11–C12 (no regresión) son el candado: si pasan antes del merge, el rollback deja al chef funcionando igual que antes.
- Ningún archivo del codebase depende del módulo `agents/memoria/` para arrancar: `app.py` puede ser revertido completamente y sigue funcionando (es el estado MVP-0.5).

### 9.3 Edge case: David quiere desactivar el feature sin perder la DB

- Agregar variable de entorno `ARCHIVO_IDEAS_ENABLED=0` (ya contemplado para `sdd-design`): el dispatcher lee la variable y devuelve "comando no disponible" en vez de ejecutar. El módulo queda instalado pero inerte. David conserva la DB para cuando reactive.
- Si David quiere esto, se agrega en `sdd-design` (es trivial, ~3 líneas).

---

## 10. Out of scope (v1) — lista explícita con racional

| Item | Rational |
|---|---|
| Auto-propuesta del agente ante heurística de keywords | **Q1 lockeada: solo comando**. Elimina R2 y la complejidad de la capa de consent. |
| `agents/memoria/triggers.py` | Idem: no existe sin heurística. |
| `agents/ideas_triggers.json` | Idem: no existe sin heurística. |
| `agents/memoria/consent.py` (módulo separado) | No hace falta: el comando ES el consentimiento. El invariante vive en `commands.py` y `storage.py` (campo `confirmada_por_usuario` siempre `=1` en v1). |
| `test_memoria_triggers.py` | No existe. La cobertura del invariante vive en C1–C3. |
| Cifrado en reposo | **D5**: David es el único con acceso físico a su máquina. Cifrar mete complejidad y posibles bugs sin beneficio real en v1. |
| Sync entre dispositivos | v2 si David lo pide. Problema RGPD no trivial (dónde vive la fuente de verdad, qué se sube, qué se borra). |
| Categorización automática con LLM | Caro, lento, inconsistente. Heurística de keywords simple en `storage.py` alcanza para sugerir. Sin LLM. |
| Retrieval automático del chef desde la DB | El chef sigue arrancando por skill, no consulta ideas previas. **Q5 lockeada: sí en v2 al final de `proceso_creativo`.** |
| Modificación del prompt de `ideas_creativas` (solo se menciona en `/ayuda` y en `docs/index.html`) | El handler `_responder_ideas_creativas` y `system_ideas_creativas.md` **quedan intactos** en v1. Esto elimina riesgo de regresión. |
| Modificación del handler de `proceso_creativo` | Idem: intacto en v1. La integración catálogo↔ideas del Q5 para v2 sí toca ese handler. |
| UI nueva en Gradio (tab/botón dedicado al archivo) | Comandos transversales cubren el caso. Si David quiere UI dedicada, es change aparte. |
| Multi-tenant en HF Space (DB particionada por usuario) | **N2**: en v1 se asume single-user local. Si el Space se abre a otros usuarios en el futuro, se hace `ideas_<user_hash>.db`. |
| Relación catálogo ↔ ideas | **Q5 lockeada**: NO en v1, SÍ en v2. |
| Sugerencias cruzadas automáticas ("ya tenés 3 ideas sobre fermentos, ¿armamos una ficha?") | v2 si David lo pide tras usar el archivo un tiempo. |
| Migración de las ideas actuales que David tiene en JSON / papel / chat viejo | No hay ideas previas persistidas en este proyecto; no hay nada que migrar. Cuando David empiece a guardar, empieza de cero. |
| `docs/index.html` (landing page) con sección "Archivo de ideas" | Cambio **fuera** de este change (es contenido de la landing, no del MVP-0.5). Se hace en una sesión de archive cuando David lo pida. Quedan documentados los comandos en `/ayuda` dentro del chat. |

---

## 11. Resultado de fase

```yaml
status: proposal-complete
artifacts:
  - openspec/changes/archivo-de-ideas/proposal.md  (este archivo, FINAL)
next_recommended: sdd-spec
locked_decisions:
  - D1 storage SQLite WAL
  - D2 schema 8 campos + updated_at + 3 índices
  - D3 trigger solo comando /guardar
  - D4 integración transversal (no nueva skill)
  - D5 RGPD sin cifrado
  - D6 out-of-scope v1 (ver §3.2 + §10)
  - Q1 trigger solo comando
  - Q2 duplicados exacta + fuzzy ≥80%
  - Q3 editable + updated_at
  - Q4 contador visible con opt-out
  - Q5 catálogo NO en v1, sí en v2
pending_decisions_to_resolve_in_spec_or_design:
  - N1 nombre exacto de /editar vs /modificar
  - N2 semántica multi-tenant HF Space (v1 asume single-user local)
  - N3 categorías precargadas finales
  - N4 formato del contador
  - N5 forma de confirmación de /olvidar todo
risks:
  - R1 consentimiento: BAJO (antes ALTO, mitigado por Q1)
  - R2 falsos positivos: BAJO (antes ALTO, eliminado por Q1)
  - R3 concurrencia SQLite: MEDIO (WAL + timeout + tests)
  - R4 rigidez schema: MEDIO (categorías en JSON + libre)
  - R5 comandos olvidados: MEDIO (/ayuda documentado)
  - R6 regresión MVP-0.5: BAJO (cambios aditivos + tests no-regresión)
  - R7 dep mismatch: BAJO (SQLite stdlib)
  - R8 export sensible: BAJO (export local, sin upload)
skill_resolution: none
```

---

## 12. Próximo paso

`sdd-spec` con David en sesión interactiva. Temas a llevar:

1. Confirmar N1 (nombre exacto del comando de edición).
2. Confirmar N3 (categorías precargadas finales).
3. Decidir si la lista de comandos aparece en `docs/index.html` ahora o después (documentación de la landing).
4. Si David quiere más variantes de `/guardar` (ej. guardar la idea actual que el chef está describiendo en un system message), se agregan en `sdd-design`.

No se pregunta sobre test commands, PR shape, ni changed-line budget (esas son decisiones de delivery, no de producto).
