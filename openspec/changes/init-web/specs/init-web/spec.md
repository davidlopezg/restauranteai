# Spec — init-web

> **Change**: `init-web` · **Fase**: `sdd-spec` (BORRADOR — pendiente aprobación de proposal)
> **Base**: [`proposal.md`](../../proposal.md) (decisiones 1-14 + 6 preguntas abiertas) + [`explore.md`](../../explore.md) (F1-F7, R1-R9)
> **Convención**: RFC 2119 (MUST / SHOULD / MAY). RF IDs preservados desde el proposal para trazabilidad.

## Propósito

Exponer la configuración del restaurante (perfil + carta) en una pestaña web dentro del HF Space, exponiendo el núcleo `agents/init_phase.py` ya implementado. Hoy ese núcleo solo se accede vía CLI (`python -m agents.init_phase`), lo que excluye al comprador target (hostelero/chef no técnico, decisión 2 del proposal `producto-vendible`).

## Objetivos

1. **Self-service en navegador**: el hostelero configura su restaurante en 5-10 minutos sin tocar terminal.
2. **Reutilización del núcleo**: 95% del trabajo es capa de presentación sobre código que ya existe (verificado en explore.md §"Núcleo reutilizable").
3. **Persistencia segura**: confirmar antes de sobrescribir; no pisar perfiles reales existentes.
4. **Honestidad operativa**: disclaimer claro de que el Space es demo pública (filesystem efímero); uso real = instancia privada (servicio pago).

## Alcance

### In scope (este change)

- Pestaña "Configurar mi restaurante" en `app.py` con `gr.Tabs(Chat, Configurar)`.
- Edición de las 15 dimensiones con el widget correcto por tipo.
- Editor de catálogo con `gr.Dataframe` (CRUD básico).
- Modo "pegar carta completa" con extracción vía LLM.
- Validación live contra `agents/init_options.json`.
- Confirmación antes de sobrescribir archivos existentes.
- Disclaimer de persistencia efímera siempre visible.
- Botón "Restaurar perfil demo" (solo si `demo == true`).
- Tests `scripts/test_init_web.py` con ≥6 checks.

### Out of scope (explícito)

- ❌ Autenticación / multi-tenant (Space es público; uso real = instancia privada).
- ❌ Importar carta desde PDF/imagen (OCR) — v2 si hay demanda.
- ❌ Versionado del restaurante.json (rollback) — v2 si hay demanda.
- ❌ Drag-and-drop de cartas — v2 fancy UI.
- ❌ Persistencia fuera del filesystem del Space (S3, etc.) — fuera del modelo open core.
- ❌ Editor JSON crudo editable — solo lectura en v1.
- ❌ Sincronización bidireccional con CLI — solo lectura del JSON generado por CLI en v1.
- ❌ Cambio del Space UI a otro idioma — castellano neutro en v1; la landing es trilingüe.

## Requisitos funcionales

### Carga inicial (RF-1..RF-4)

**RF-1**: la pestaña "Configurar mi restaurante" carga en ≤3 segundos en el HF Space con perfil demo precargado.

**RF-2**: al abrir la pestaña, lee `restaurante.json` y `catalogo_platos.json` actuales vía `cargar_restaurante()` / `cargar_catalogo()` (de `agents/knowledge_context.py`) y precarga TODOS los inputs.

**RF-3**: si `restaurante.json` no existe, los inputs arrancan vacíos y el indicador muestra "Estás editando el perfil demo genérico".

**RF-4**: el indicador del perfil (existente `_estado_perfil()` en `app.py`) sigue funcionando en la pestaña Chat (sin cambios).

### Edición de las 15 dimensiones (RF-5..RF-8)

**RF-5**: cada pregunta de `PREGUNTAS_RESTAURANTE` (en `agents/init_phase.py`) se renderiza con el widget correcto según su `type`:

| Tipo en PREGUNTAS | Widget Gradio | Comportamiento |
|---|---|---|
| `number` | `gr.Number` | Acepta enteros/ decimales, valida rango si tiene `help` con patrón. |
| `choice` | `gr.Dropdown` | `choices=` derivado de `init_options.json[key].values`. Opción "Otra (escribir)" + campo libre si el usuario la elige. |
| `multichoice` | `gr.CheckboxGroup` + opcional `gr.Textbox` para customs | Mismo patrón. |
| `text` | `gr.Textbox` | Input libre. |

**RF-6**: las opciones SIEMPRE vienen de `agents/init_options.json` (fuente de verdad). Si una key no está en el JSON, fallback a las opciones hardcoded en `init_phase.py` (no rompe nada).

**RF-7**: valores custom (escritos por el usuario con "Otra") se aceptan como string libre, consistente con la lógica CLI.

**RF-8**: la edición se valida contra los valores válidos de `init_options.json` antes de guardar. Inputs inválidos se marcan en rojo y "Guardar" queda deshabilitado.

### Edición del catálogo (RF-9..RF-11)

**RF-9**: el catálogo se muestra en un `gr.Dataframe` con columnas `nombre | categoria | descripcion | precio`. Editable (`interactive=True`).

**RF-10**: hay 3 botones: "Agregar fila", "Borrar fila(s) seleccionada(s)", "Restaurar catálogo demo".

**RF-11**: si el catálogo tiene >100 platos, se muestra un warning + las primeras 100 filas. Paginación en v2.

### Modo "pegar carta completa" (RF-12..RF-14)

**RF-12**: hay un `gr.Textbox` multilinea donde el usuario pega su carta completa, + un botón "Extraer estructura" que llama a `_extraer_platos_de_carta()` (en `agents/init_phase.py`).

**RF-13**: durante el call al LLM (5-15 segundos), se muestra `gr.Markdown("⏳ Extrayendo platos... (5-15 segundos)")` con spinner implícito de Gradio.

**RF-14**: tras la extracción, los platos aparecen en un `gr.Dataframe` preview editable. El usuario revisa, ajusta, y solo entonces confirma con "Guardar catálogo".

### Persistencia segura (RF-15..RF-17)

**RF-15**: el botón "Guardar cambios" abre un `gr.Group` modal de confirmación:
- Si **ningún archivo** existe (`restaurante.json` Y `catalogo_platos.json`): guarda directo, sin confirmación.
- Si **algún archivo existe y es demo** (`restaurante["demo"] == true`): confirma con mensaje "Vas a reemplazar el perfil demo genérico con tu configuración. ¿Continuar?".
- Si **algún archivo existe y NO es demo**: confirma con mensaje más fuerte "Vas a perder tu configuración anterior. ¿Continuar?" + opción de descargar backup antes.

**RF-16**: la implementación usa `restaurante_existe()` / `catalogo_existe()` (de `agents/knowledge_context.py`) como guard, NO `guardar_restaurante()` directo (que sobrescribe siempre — riesgo F1 de explore.md).

**RF-17**: tras guardar exitosamente, se muestra mensaje "✅ Configuración guardada. Próximo cold start del Space puede perder estos cambios — montá tu instancia privada para uso real." + sugerencia de mailto.

### Botón "Restaurar perfil demo" (RF-18..RF-19)

**RF-18**: el botón está visible solo si el perfil actual es demo (`restaurante.get("demo") == True`). Si es perfil real, el botón está deshabilitado con tooltip "No se puede restaurar el demo sobre un perfil real — primero borrá `.agent_knowledge/restaurante.json` desde CLI".

**RF-19**: al hacer click, pide confirmación ("Vas a perder tu configuración actual y volver al perfil demo genérico. ¿Continuar?") y luego re-seedea desde `agents/creativo/knowledge/demo_restaurante.json` + `agents/creativo/knowledge/demo_catalogo_platos.json`.

### Disclaimer de persistencia efímera (RF-20)

**RF-20**: en la pestaña "Configurar" hay un `gr.Markdown` siempre visible en la parte superior:

> ⚠️ **Importante**: el HF Space free duerme los procesos después de un rato de inactividad. Tu configuración se pierde cuando el Space se reinicia. Para uso real, montá tu instancia privada (ver [`SECURITY.md`](../../../SECURITY.md) o escribime a davidlopezgamero@gmail.com).

### Tests (RF-21)

**RF-21**: `scripts/test_init_web.py` (estilo mini-helper `check()` de `scripts/test_app.py`) con al menos 6 checks:

1. Carga de inputs desde `restaurante.json` existente.
2. Carga de inputs vacíos si no existe `restaurante.json`.
3. Cambio de un input `choice` persiste correctamente.
4. Cambio de un input `multichoice` persiste correctamente.
5. Guardar pide confirmación si el archivo existe y no es demo.
6. Guardar NO sobrescribe un archivo real si solo falta el otro (caso bug de `guardar_*`).
7. Botón "Restaurar perfil demo" solo funciona si `demo == true`.
8. Validación live marca inputs inválidos en rojo.

### Update de copy de landing (RF-22)

**RF-22**: la sección "Oferta open core" del `docs/index.html` se ajusta: la implementación incluye "configuración inicial de tu restaurante en el navegador" como entregable explícito (cuando el change esté live). Hasta entonces, sigue mencionando "configuración por mi".

## Requisitos no funcionales

- **NFR-1 — Compatibilidad**: `python scripts/test_app.py` sigue verde (6/6) tras el cambio. `pytest tests/` sigue verde (132+).
- **NFR-2 — Performance**: la pestaña carga en ≤3s; las llamadas LLM (extracción de carta) en ≤15s.
- **NFR-3 — Sin secretos en logs**: el código NO loggea contenido de `restaurante.json` ni `catalogo_platos.json`, solo IDs y longitudes.
- **NFR-4 — Sin datos reales en commits**: las pruebas usan el seed demo como fixture; el `tests/test_init_web.py` no tiene hardcoded datos reales.
- **NFR-5 — Idioma**: la UI del Space sigue en castellano neutro peninsular (consistente con `app.py` actual).
- **NFR-6 — Accesibilidad básica**: contraste suficiente, labels asociados, navegación por teclado.
- **NFR-7 — Deploy**: push a `hf` (Space) cuando esté completo; push a `origin` para cambios de docs (`docs/index.html`, `README.md`, `CHANGELOG.md`).
- **NFR-8 — Versionado**: bump `VERSION` v1.4.0 → v1.5.0 + tag.

## Criterios de aceptación

### CA-1: carga inicial

- [ ] Abrir la pestaña Configurar en HF Space con perfil demo → todos los 15 inputs se precargan con valores del seed demo en ≤3s.
- [ ] Abrir la pestaña Configurar en HF Space sin `restaurante.json` → todos los inputs arrancan vacíos; el indicador muestra "Estás editando el perfil demo genérico".

### CA-2: edición de las 15 dimensiones

- [ ] Editar un input `number` (ej: `precio_target_max`) → cambio visible en el input, no en disco todavía.
- [ ] Editar un input `choice` (ej: `sofisticacion`) → opciones del dropdown vienen de `init_options.json`.
- [ ] Editar un input `multichoice` (ej: `productos_dominantes`) → checkboxes con opción "Otra (escribir)".
- [ ] Editar un input `text` (no hay en las 15 actuales, pero el patrón debe estar listo).

### CA-3: edición del catálogo

- [ ] Catálogo visible en `gr.Dataframe` editable.
- [ ] Botón "Agregar fila" añade una fila vacía al final.
- [ ] Botón "Borrar fila(s)" elimina filas seleccionadas.
- [ ] Botón "Restaurar catálogo demo" funciona solo si el catálogo actual es demo.
- [ ] Catálogo >100 platos: warning visible + primeras 100 filas.

### CA-4: modo "pegar carta"

- [ ] Pegar carta de ejemplo + click "Extraer estructura" → spinner visible durante 5-15s.
- [ ] Tras extracción, platos aparecen en preview editable.
- [ ] Edición en preview → guardar persiste los cambios.

### CA-5: persistencia segura

- [ ] Sin `restaurante.json` + click "Guardar" → guarda directo sin confirmación.
- [ ] Con `restaurante.json` demo + click "Guardar" → confirma con mensaje.
- [ ] Con `restaurante.json` real + click "Guardar" → confirma con mensaje fuerte + opción backup.
- [ ] Bug F1 (sobrescritura cruzada): si solo falta `catalogo_platos.json` y existe `restaurante.json` real, guardar catálogo NO pisa el restaurante.

### CA-6: restaurar perfil demo

- [ ] Botón visible solo cuando `restaurante["demo"] == true`.
- [ ] Click → confirma → reseed desde `demo_restaurante.json`.
- [ ] Click cuando NO es demo → botón deshabilitado con tooltip.

### CA-7: disclaimer

- [ ] Disclaimer siempre visible arriba de la pestaña Configurar.
- [ ] Incluye link a SECURITY.md (sin dominio completo — relativo al root del repo).

### CA-8: tests

- [ ] `python scripts/test_init_web.py` con ≥6/8 checks pasando.
- [ ] `python scripts/test_app.py` sigue 6/6 verde.
- [ ] `python scripts/test_seed_demo.py` sigue 5/5 verde.
- [ ] `python -m pytest tests/ -q` sigue 132+ tests verde.

### CA-9: invariantes

- [ ] `responder()` mantiene la firma `(mensaje, historial, skill="ficha")`.
- [ ] `theme=` y `css=` siguen en `.launch()`, no en el constructor de `gr.Blocks`.
- [ ] Sin `type=` kwarg en `gr.ChatInterface` ni `gr.Chatbot`.
- [ ] `ChatInterface` sigue dentro de `with gr.Blocks()`.

### CA-10: idioma

- [ ] Toda la UI en castellano neutro peninsular.
- [ ] Sin voseo en strings visibles.

### CA-11: release

- [ ] `VERSION` bumped a `v1.5.0`.
- [ ] Tag `v1.5.0` creado en `origin`.
- [ ] CHANGELOG.md actualizado con la entrada v1.5.0.
- [ ] README.md actualizado con el estado del proyecto.

## Out of scope confirmado

| Feature | Por qué fuera |
|---|---|
| Autenticación | Demo pública es abierta; uso real = instancia privada. |
| OCR de cartas PDF/imagen | Complejidad significativa; v2 si hay demanda. |
| Versionado del JSON | UI no-trivial; v2 si hay demanda. |
| Editor JSON crudo editable | Superficie de error; solo lectura en v1. |
| Drag-and-drop | v2 fancy UI. |
| Sincronización bidireccional CLI | Solo lectura en v1. |
| Persistencia fuera del Space | Fuera del modelo open core. |
| Multi-idioma del Space | Solo castellano; la landing es trilingüe. |

## Decisiones pendientes (deben cerrarse antes de `sdd-design`)

Las 6 preguntas del proposal (asunciones por defecto en negrita, alternativa entre paréntesis):

1. **Q1 — Autenticación**: **pública** (con auth básica HF OAuth).
2. **Q2 — Catálogo**: **gr.Dataframe** (lista virtualizada).
3. **Q3 — Restaurar demo**: **sí** (no incluir).
4. **Q4 — JSON crudo**: **solo lectura en v1** (edición completa).
5. **Q5 — Pegar carta**: **sí** (diferir a v2).
6. **Q6 — Idioma**: **castellano neutro peninsular** (mantener voseo).

Si David no contesta antes de `sdd-design`, **se mantienen las asunciones por defecto**.

## Riesgos y mitigaciones

| # | Riesgo | Sev. | Mitigación | Trazabilidad |
|---|---|---|---|---|
| R1 | Sobrescritura accidental del perfil | Alta | Confirmación obligatoria + guard por archivo (RF-15, RF-16) | explore.md F1 |
| R2 | Restaurar demo pisa perfil real | Alta | Botón deshabilitado si `demo != true` (RF-18) | explore.md F2 |
| R3 | Extracción de carta falla | Media | Mostrar error con detalle + permitir edición manual (RF-14) | explore.md F3 |
| R4 | Validación live rompe si `init_options.json` malformado | Baja | Try/except + fallback a valores del código (RF-6) | explore.md F4 |
| R5 | Catálogo >100 platos hace lenta la UI | Media | Límite a 100 + warning (RF-11) | explore.md F5 |
| R6 | Cold start pierde config | Media | Disclaimer siempre visible (RF-20) | explore.md F6 |
| R7 | Datos sensibles en logs | Baja | No loggear contenido de restaurante/catálogo (NFR-3) | explore.md F7 |
| R8 | Cambio de UI rompe invariantes de `test_app.py` | Baja | Test invariants verificados en CA-9 | memoria memory 2026-08-05 D5 |
| R9 | Usuario quiere editar JSON crudo | Baja | Botón "Ver JSON" solo lectura (RF-22 parcial) | explore.md R9 |

## Dependencias

- **Código existente**: `agents/init_phase.py`, `agents/knowledge_context.py`, `agents/init_options.json`, `agents/creativo/knowledge/demo_*.json` (todos verificados en explore.md).
- **Sin dependencias nuevas**: no se agrega nada a `requirements.txt`.
- **Sin cambios en `.gitignore`**: `.agent_knowledge/` sigue gitignored.

## Estimación de impacto

| Área | Líneas estimadas |
|---|---|
| `app.py` (pestaña + handlers) | +300-400 |
| `scripts/test_init_web.py` | +120-150 |
| `agents/knowledge_context.py` (helpers de carga con guard) | +30-50 |
| `docs/index.html` (copy open core) | +5-10 |
| `CHANGELOG.md` (entrada v1.5.0) | +25-30 |
| `README.md` (estado del proyecto + roadmap) | +5-10 |
| `VERSION` | +1 |
| **Total** | **~485-650** |

Estrategia slicing (stacked PRs, cada uno < 400 líneas):

- **PR 1 — Backend helpers**: `agents/knowledge_context.py` (carga/guarda con guard por archivo) + tests.
- **PR 2 — UI web**: pestaña en `app.py` + handlers.
- **PR 3 — Tests + docs**: `scripts/test_init_web.py` + updates de CHANGELOG/README/landing/VERSION.

Cada PR mergeado antes del siguiente. Cada PR self-verifica con su suite.

## Siguientes pasos

1. ✅ Explore + Proposal + Spec completos (este artefacto).
2. → **Decisión sobre las 6 preguntas** del proposal (David).
3. → **Design** (`sdd-design`): wireframes ASCII de la UI + snippets de código + estructura de handlers.
4. → **Tasks** (`sdd-tasks`): slicing detallado por PR.
5. → **Apply** (`sdd-apply`): PR 1 → PR 2 → PR 3, cada uno con tests verdes.
6. → **Verify** (`sdd-verify`): CAs 1-11 verificados.
7. → **Sync + Archive** (`sdd-sync` + `sdd-archive`): push a `hf` + `origin`, archive del change.

---

**Estado**: BORRADOR — pendiente decisión sobre las 6 preguntas de producto.
**Próxima fase**: `sdd-design` (no requiere decisiones cerradas, sí las RFs).
**Estimación**: ~3-5 días de implementación + 1-2 días de verify + sync.
