# Proposal — init-web (UI de configuración del restaurante en navegador)

> **Change**: `init-web` · **Fase**: `sdd-proposal` · **Proyecto**: `restauranteia`
> **Base**: [`explore.md`](explore.md) (95% del núcleo reutilizable; la UI es una capa de presentación)
> **Estado**: 🟡 BORRADOR — pendiente ronda de preguntas con David

## Resumen ejecutivo

El Chef Creativo es un producto sólido, pero **solo el comprador técnico puede configurarlo hoy** (requiere `python -m agents.init_phase` en terminal). El **comprador target** (hostelero/chef no técnico, decisión 2 del proposal `producto-vendible`) **no puede** usar el producto en serio porque el init es CLI-only.

Este change entrega la **primera capa de auto-servicio**: una pestaña "Configurar mi restaurante" dentro del Space HF que reutiliza el núcleo `agents/init_phase.py` ya implementado. El hostelero configura su perfil (15 dimensiones) y su carta (catálogo de platos) desde el navegador, sin tocar terminal. Persistencia: `agentes/knowledge_context.py` ya lo hace correctamente (con guard explícito para evitar pisar perfiles existentes, ver F1 en explore).

**Decisión arquitectónica clave**: 95% del núcleo es reutilizable; el change es **M (mediano)**, no L. ~3-5 commits según budget SDD.

## Problema / oportunidad

**Problema (estado actual verificado en explore.md)**:

- **Init CLI-only**: `agents/init_phase.py` usa `input()` (TTY-only) para recolectar 15 dimensiones + carta. Un hostelero no técnico no puede configurar nada desde el navegador.
- **Fricción con el modelo open core**: la landing ofrece "implementación en tu restaurante = servicio pago". Pero si el producto fuera self-service, la implementación sería más barata y escalable. **Self-service reduce el coste del servicio de implementación y abre mercado más amplio**.
- **Inconsistencia con la promesa de la landing**: dice "Probá en 10 segundos sin instalación". Pero configurar tu restaurante lleva 5-10 min **en terminal**, que el visitante no tiene.

**Oportunidad**:

- Reutilizando el núcleo ya implementado (`init_phase.py` data-driven + `init_options.json` externalizado + `_extraer_platos_de_carta` con LLM), la UI web es **fundamentalmente una capa de presentación**.
- El hostelero configura su restaurante en 5-10 minutos desde el navegador, ve inmediatamente que el chef cambia sus respuestas (de demo genérico a su perfil), y puede probar las 4 skills con su contexto real.
- **No requiere infra nueva**: todo corre dentro del mismo HF Space.

## Objetivos del change

1. **(D1) Auto-servicio en navegador**: nueva pestaña "Configurar mi restaurante" en `app.py` con `gr.Tabs` que alterna Chat | Configurar.
2. **(D2) Carga inicial automática**: al abrir la pestaña, lee `restaurante.json` y `catalogo_platos.json` actuales y precarga los inputs.
3. **(D3) Edición data-driven de las 15 dimensiones**: cada pregunta se renderiza con el widget correcto (`gr.Number`, `gr.Dropdown`, `gr.CheckboxGroup`, `gr.Textbox`) según su tipo en `PREGUNTAS_RESTAURANTE`.
4. **(D4) Editor de catálogo con `gr.Dataframe`**: CRUD (agregar/editar/borrar filas) sobre la lista de platos.
5. **(D5) Modo "pegar carta completa"**: `gr.Textbox` multilinea + botón "Extraer estructura" → llama a `_extraer_platos_de_carta()` (LLM) → preview editable.
6. **(D6) Validación live contra `init_options.json`**: opciones siempre vienen del JSON (fuente de verdad); valores custom (escritos por el usuario) se aceptan raw (consistente con CLI).
7. **(D7) Persistencia segura**: confirmación antes de sobrescribir (riesgo F1 del explore); guard explícito por archivo (no sobrescribe si solo falta uno).
8. **(D8) Botón "Restaurar perfil demo"**: vuelve al estado inicial (re-seedea desde `agents/creativo/knowledge/demo_*.json`).
9. **(D9) Disclaimer sobre persistencia efímera**: el Space HF duerme los procesos; las ediciones se pierden en cold start. La solución real es la instancia privada (servicio pago).
10. **(D10) Tests**: `scripts/test_init_web.py` cubre carga, edición de cada tipo de input, persistencia con confirmación, validación, no-sobrescritura, modo demo.
11. **(D11) Update de copy de landing**: el modelo open core se mantiene, pero la oferta de implementación se ajusta (incluye "configuración inicial de tu restaurante" como entregable).

## Alcance (In scope / Out of scope)

### In scope

| Área | Qué incluye |
|---|---|
| **`app.py` UI** | Nueva pestaña "Configurar mi restaurante" con `gr.Tabs(Chat, Configurar)`. |
| **Edición de las 15 dimensiones** | Inputs precargados desde `restaurante.json` actual; persistencia con confirmación; validación live. |
| **Edición del catálogo** | `gr.Dataframe` editable con CRUD básico (add row, edit cell, delete row). |
| **Modo "pegar carta completa"** | `gr.Textbox` multilinea → botón "Extraer estructura" → `gr.Dataframe` preview con los platos extraídos → botón "Guardar". |
| **Botón "Restaurar perfil demo"** | Re-seedea desde `agents/creativo/knowledge/demo_*.json` (idempotente, no pisa si existen). |
| **Validación contra `init_options.json`** | Las opciones siempre vienen del JSON. Valores custom aceptados como string libre (consistente con CLI). |
| **Tests** | `scripts/test_init_web.py` con ≥6 checks (carga, edición, persistencia, validación, no-sobrescritura, modo demo). |
| **Update de CHANGELOG.md y README.md** | bump v1.4.0 → v1.5.0 + tag. |
| **Update de `docs/index.html`** | Copy del modelo open core se ajusta: "incluye configuración inicial de tu restaurante". |

### Out of scope (explícito)

| Área | Por qué fuera |
|---|---|
| Autenticación / multi-tenant | El Space público es "demo + evaluación", no "uso serio". Datos reales no deberían estar acá (regla memory 2026-08-05 R2). |
| Importar carta desde PDF/imagen (OCR) | v2 si hay demanda; añade complejidad significativa. |
| Versionado del restaurante.json (rollback) | v2 si hay demanda; complejidad de UI. |
| Drag-and-drop de cartas | v2 fancy UI; v1 cubre el 90% del caso. |
| Persistencia fuera del filesystem del Space | Cambia infra (S3, etc.); fuera del modelo open core. |
| Editor JSON crudo editable | Solo lectura en v1 (botón "Ver JSON" para inspección). |
| Sincronización bidireccional con CLI `init_phase` | Solo lectura del JSON generado por CLI en v1. |
| Cambio del Space UI a otro idioma | Castellano neutro en v1 (la landing es trilingüe; el Space sigue monolingüe). |

## Decisiones de producto (cerradas con David — 2026-08-29)

> ✅ Decididas. Locked-in para `sdd-spec` y siguientes.

1. **Auth REQUERIDA vía HF OAuth** (nativa de Gradio en HF Spaces). Descarta la suposición original "pública". Solo la pestaña "Configurar" requiere auth; "Chat" sigue siendo pública.
2. **Catálogo con `gr.Dataframe` + paginación a 25 filas + búsqueda en vivo** (`gr.Textbox` filtra por nombre/categoría/descripcion).
3. **Botón "Restaurar perfil demo"**: sí.
4. **JSON crudo**: `gr.Group` colapsable con JSON formateado + **botón Copiar** al portapapeles. Solo lectura.
5. **Modo "pegar carta"**: sí.
6. **Idioma del Space**: castellano neutro peninsular.

## Criterios de aceptación (tentativos, se afinan en `sdd-spec`)

- **CA-1**: la pestaña "Configurar mi restaurante" carga en <3s en el Space HF con perfil demo precargado.
- **CA-2**: la pestaña precarga los 15 inputs desde `restaurante.json` actual (vacíos si no existe, demo si existe demo).
- **CA-3**: editar un input + click "Guardar" persiste el cambio en `.agent_knowledge/restaurante.json` (verificable con `cargar_restaurante()` tras refresh).
- **CA-4**: si el archivo `restaurante.json` ya existe y NO es demo, "Guardar" pide confirmación ("Vas a perder tu configuración actual. ¿Continuar?").
- **CA-5**: el catálogo es editable con `gr.Dataframe` (agregar, borrar, editar celdas).
- **CA-6**: el modo "pegar carta completa" extrae platos vía LLM y los muestra en un preview editable antes de confirmar.
- **CA-7**: si `init_options.json` tiene una opción nueva, se refleja en la UI sin restart.
- **CA-8**: el disclaimer de persistencia efímera está visible siempre en la pestaña.
- **CA-9**: el botón "Restaurar perfil demo" vuelve al estado inicial sin afectar otros archivos.
- **CA-10**: la pestaña Configurar es pública (sin login), pero el disclaimer es claro sobre el carácter de demo.
- **CA-11**: `scripts/test_init_web.py` con ≥6 checks, todos verdes.
- **CA-12**: las invariantes de `test_app.py` se mantienen (firma `responder()`, theme/css en `.launch()`, sin `type=` kwarg).
- **CA-13**: la UI del Space sigue en castellano neutro peninsular.
- **CA-14**: la versión se bumpea a `v1.5.0` + tag.

## Impacto y riesgos

### Impacto

| Área | Archivos | Líneas estimadas |
|---|---|---|
| `app.py` | Nueva pestaña `gr.Tabs` + handlers (cargar, editar, guardar, restaurar) | ~300-400 |
| `scripts/test_init_web.py` | Nuevo: ≥6 checks | ~150-200 |
| `agents/knowledge_context.py` | Helper `restaurante_existe` ya existe; posiblemente nuevo helper `seed_demo_from_static()` | ~30-50 |
| `agents/init_phase.py` | Reutilizar; sin cambios | 0 |
| `agents/init_options.json` | Reutilizar; sin cambios | 0 |
| `docs/index.html` | Copy del open core ajustado (~10 líneas) | ~20 |
| `CHANGELOG.md` | Entrada v1.5.0 | ~30 |
| `README.md` | Actualizar estado del proyecto + roadmap | ~5 |
| `VERSION` | bump v1.4.0 → v1.5.0 | 1 |
| **Total estimado** | | **~540-700 líneas** |

**Nota**: este es un change **M (mediano)**. Está en el límite del budget SDD de 400 líneas. **Estrategia slicing**:

- **PR 1 (backend)**: helpers en `agents/knowledge_context.py` para carga/guarda seguro + tests.
- **PR 2 (UI web)**: pestaña en `app.py` + handlers.
- **PR 3 (tests + docs)**: `test_init_web.py` + updates de CHANGELOG/README/landing.
- **PR 4 (release)**: bump VERSION + tag.

Cada PR < 400 líneas.

### Riesgos

| # | Riesgo | Sev. | Mitigación |
|---|---|---|---|
| R1 | Sobrescritura accidental del perfil del usuario | Alta | Confirmación obligatoria antes de guardar; guard por archivo (idempotente). |
| R2 | "Restaurar perfil demo" pisa un perfil real | Alta | Solo funciona si `restaurante["demo"] is True`. Si es perfil real, deshabilita el botón. |
| R3 | Extracción de carta falla (timeout, JSON malformado) | Media | Mostrar error con detalle + permitir edición manual del JSON parseado (preview editable). |
| R4 | Validación live rompe la UI si `init_options.json` está malformado | Baja | Try/except al cargar opciones; fallback a valores del código con warning en log. |
| R5 | Catálogo grande (>100 platos) hace lenta la UI | Media | Límite a 100 visibles + warning; paginación en v2. |
| R6 | Cold start del Space pierde config | Media | Disclaimer siempre visible + sugerencia de instancia privada (servicio pago). |
| R7 | Datos sensibles en logs de HF | Baja | No loggear contenido de restaurante.json; solo IDs y longitudes. |
| R8 | Cambio de UI rompe invariantes de `test_app.py` | Baja | Mismas reglas: `theme=`/`css=` solo en `.launch()`, sin `type=` kwarg, ChatInterface dentro de Blocks. |
| R9 | El usuario quiere editar el JSON crudo | Baja | Botón "Ver JSON" (solo lectura en v1). |

## Siguientes pasos

1. ✅ Explore completado.
2. ✅ Proposal borrador (este artefacto).
3. → **Ronda de preguntas con David** sobre las 6 decisiones de producto (asunciones por defecto).
4. → **Spec** con RFs y CAs afinados.
5. → **Design** con wireframes ASCII + snippets de código.
6. → **Tasks** con slicing en 3-4 PRs.
7. → **Apply** con verificación de tests verde.
8. → **Verify** contra CAs.
9. → **Sync + Archive**.

---

## Preguntas a David (ronda de propuesta)

> **6 preguntas, todas de producto**. Mis asunciones por defecto están marcadas. Si querés cambiar alguna, decímelo y actualizo el proposal.

**Q1 — Autenticación**: ¿la pestaña Configurar debe ser pública (sin login, mi asunción) o requerir autenticación?

- **Asume (recomendado)**: pública. El Space es "demo + evaluación", no "uso serio". El uso serio es en instancia privada.
- **Alternativa**: agregar auth básica (HF OAuth). Añade fricción al visitante casual; resuelve un problema que no existe en la demo pública.

**Q2 — Catálogo con `gr.Dataframe` o lista virtualizada**: ¿`gr.Dataframe` simple (mi asunción) o lista paginada/virtualizada?

- **Asume (recomendado)**: `gr.Dataframe` con límite a 100 filas visibles (warning si excede).
- **Alternativa**: lista virtualizada con búsqueda. Más potente pero más UI.

**Q3 — Botón "Restaurar perfil demo"**: ¿incluir (mi asunción) o no?

- **Asume (recomendado)**: sí. Útil para demos y para que usuarios que jugaron vuelvan al estado inicial.
- **Alternativa**: no incluir; el usuario puede borrar `.agent_knowledge/restaurante.json` desde CLI si quiere (no es viable para no-técnicos).

**Q4 — Edición JSON crudo**: ¿solo lectura (mi asunción) o edición?

- **Asume (recomendado)**: solo lectura (botón "Ver JSON" para inspección). Edición añade superficie de error.
- **Alternativa**: edición completa del JSON. Potente pero scary; rompe el flujo de la UI web.

**Q5 — Modo "pegar carta completa" en la UI**: ¿incluir (mi asunción) o diferir a v2?

- **Asume (recomendado)**: incluir. Reusa `_extraer_platos_de_carta()` que ya existe; es el flujo más común para cargar carta.
- **Alternativa**: solo editor fila por fila. Más tedioso pero menos UI.

**Q6 — Idioma del Space**: ¿castellano neutro peninsular (mi asunción) o mantener voseo (decisión 10 del proposal `producto-vendible`)?

- **Asume (recomendado)**: castellano neutro peninsular. Consistente con el resto de la UI y la landing.
- **Alternativa**: voseo. Consistente con las conversaciones con vos, pero menos presentable como producto público.

---

## Decisiones operativas (cerradas, no se reabren)

- Sin cambios en `requirements.txt`.
- Sin cambios en `.gitignore`.
- Sin cambios en la firma de `responder()`.
- Sin cambios en `agents/init_phase.py` (solo se reusa).
- Sin cambios en `agents/init_options.json` (solo se reusa).
- Push a `hf` solo cuando todo el PR afecta a `app.py`; cambios de docs a `origin` solo.
- `openspec/` nunca a `hf`.

---

**Versión tentativa**: `v1.5.0` (siguiente después de `v1.4.0`).

**Estrategia de delivery**: stacked PRs (3-4 PRs, cada uno < 400 líneas).

**Etiqueta de prioridad**: media. No bloquea lanzamiento público (la demo funciona sin esto), pero es la pieza que destraba el "uso real" del producto.
