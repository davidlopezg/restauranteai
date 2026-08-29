# Explore — init-web (UI de configuración del restaurante en navegador)

> **Change**: `init-web` · **Fase**: `sdd-explore` · **Proyecto**: `restauranteia`
> **Fecha**: 2026-08-29 · **Explorador**: orquestador (evidencia de primera mano, sin sub-agent por lecciones de `sdd-explore` documentadas en memory 2026-07-02)

## Resumen ejecutivo

**Hallazgo crítico**: el **núcleo de init ya está implementado y es reutilizable casi en su totalidad**. La UI web es fundamentalmente una capa de presentación sobre `agents/init_phase.py` que ya tiene:

- ✅ 15 preguntas data-driven (`PREGUNTAS_RESTAURANTE` con `key/prompt/type/options/help`).
- ✅ Opciones externalizadas en `agents/init_options.json` (fuente de verdad, fallback a código si falta).
- ✅ "Otra (escribir)" automático al final de cada choice/multichoice.
- ✅ 3 modos de catálogo (pegar carta / manual / saltar).
- ✅ LLM extrae JSON estructurado desde carta en texto libre (`_extraer_platos_de_carta`).
- ✅ Validación contra `init_options.json` (mapeos en `formatear_restaurante_para_chef`).
- ✅ Persistencia con `guardar_restaurante()` / `guardar_catalogo()` (sobrescriben, idempotente por archivo).

**Lo que falta es la UI web**. Es un change **M (mediano)**, no L: la lógica está, hay que exponerla.

## Evidencia del codebase

### Núcleo reutilizable (sin cambios)

**`agents/init_phase.py`** (verificado L1-L480):

- `PREGUNTAS_RESTAURANTE`: lista cerrada de 15 dicts con keys `precio_target_*`, `sofisticacion`, `productos_dominantes`, `tecnicas_dominantes`, `tipo_servicio`, `grupos`, `clases_comedores`, `origen_inspiracion`, `orientacion_nutricional`, `localizacion`, `religion`, `tiempo_preparacion`, `epoca_estilo`.
- `PREGUNTAS_POR_PLATO`: 4 preguntas (nombre, categoria, descripcion, precio).
- `_ask_question(q)`: dispatcher según tipo (`text` / `number` / `choice` / `multichoice`).
- `_input_choice` / `_input_multichoice`: con "otra (escribir)" al final.
- `_recolectar_restaurante()` / `_recolectar_catalogo()`: entry points.
- `_extraer_platos_de_carta(carta_texto)`: usa `call_minimax` para extraer JSON.

**`agents/init_options.json`** (verificado L1-100+):

- 15 keys con `type` (choice/multichoice) y `values` (lista cerrada).
- Es la fuente de verdad: si una key está, sus opciones ganan sobre las del código.

**`agents/knowledge_context.py`** (verificado L60-L80):

- `restaurante_existe()` / `catalogo_existe()`: booleans.
- `guardar_restaurante(data, schema_doc)` / `guardar_catalogo(platos, schema_doc)`: **sobrescriben siempre** (`open("w")` incondicional) — verificado en L63-77.
- `cargar_restaurante()` / `cargar_catalogo()`: lectura.
- `bootstrap_necesario()`: True si falta cualquiera.

**`app.py` ya tiene `bootstrap_necesario()`** integrado en el `__main__` (verificado L403-L425): si falta init y hay TTY → `fase_init_interactiva()`; si falta y no hay TTY → `_seed_demo_profile()`.

### Validación cruzada con `formatear_restaurante_para_chef` (`agents/creativo/agent.py` L180-L300)

Mapeos cerrados para enums:
- `SOFISTICACION`: `muy_alta|alta|media|baja|muy_baja` (5 valores).
- `GRUPOS`: `sin_grupos|con_grupos_pequenos|con_grupos_grandes|banquetes_eventos` (4 valores).
- `LOCALIZACION`: `urbana|rural|litoral_mar|montana|singular_edificio_historico` (5 valores).
- `TIEMPO`: `comida_rapida|medio|slow_food` (3 valores).
- `ORIGEN`: 9 valores (`local_pueblo` ... `internacional_fusion`).
- `EPOCA`: 11 valores (`medieval` ... `pizzeria_contemporanea`).
- Valores custom (los que el usuario escribió con "otra (escribir)"): se aceptan raw (memory 2026-07-01 D11 — consumidores tratan custom como abierto).

### Restricciones de UI conocidas

**Gradio 6.19** (verificado en `scripts/test_app.py` + frontmatter del README):

- `gr.Number`, `gr.Dropdown`, `gr.CheckboxGroup`, `gr.Textbox`, `gr.Dataframe`: todos disponibles.
- `gr.Tabs` para alternar Chat | Configurar.
- `gr.Button` + handlers que llaman a funciones de negocio.
- `gr.Markdown` para hints y validación visual.
- `gr.Dataframe` editable (con `interactive=True`): soporta CRUD básico de filas.

**Patrón `gr.Tabs` + handlers**: ya implementado en el ejemplo de Gradio 6 (oficial). No rompe invariantes de `test_app.py` (que solo verifica `responder()` firma + kwargs prohibidos).

## Hallazgos críticos

### F1. `guardar_*` sobrescribe siempre (riesgo de UX)

`guardar_restaurante()` y `guardar_catalogo()` abren con `open("w", ...)` (verificado L64, L73). En la UI web esto significa:

- Si el usuario abre la pestaña "Configurar" y toca "Guardar" sin querer, pisa su perfil actual.
- **Mitigación obligatoria**: confirmación antes de sobrescribir ("Vas a perder tu configuración actual. ¿Continuar?").
- **Idempotencia por archivo** (como el seed demo): antes de guardar, verificar si el archivo existe. Si existe, pedir confirmación explícita.

### F2. Perfil `demo: true` se preserva hasta primer guardado real

El indicador de UI (`_estado_perfil()`) muestra "🧪 Demo" cuando `restaurante["demo"] is True`. La UI web debe:

- Cargar restaurante.json al abrir la pestaña.
- Si `demo is True`: mostrar "Estás editando el perfil demo genérico. Al guardar, se reemplazará con tu configuración real."
- Al guardar: persistir el nuevo dict (sin `demo: true`) → el indicador pasa automáticamente a "🍽️ Perfil activo: …".

### F3. Validación contra `init_options.json` es live

Cada `gr.Dropdown` debe usar `choices=` derivado de `init_options.json`. Si el usuario agrega una opción nueva al JSON, la UI la refleja sin restart. Si escribe un valor custom, se persiste como string libre (consistente con la lógica CLI).

### F4. El catálogo puede tener 100+ platos

- `gr.Dataframe` con 100+ filas: OK pero lento. Estrategia: lista virtualizada o paginada.
- **Decisión propuesta**: lista con `gr.Dataframe` (max 100 filas visibles, warning si excede), con botones "Agregar fila" / "Editar fila" / "Borrar fila" que abren un modal o un row expandible.
- **Alternativa descartada para v1**: editor JSON crudo (más potente pero más scary).

### F5. Modo "pegar carta" requiere llamada LLM

Al click "Extraer estructura", se llama a `_extraer_platos_de_carta(carta)`. Esto:
- Consume API (1 request por extracción).
- Tarda 5-15 segundos.
- Devuelve lista cruda → preview editable antes de confirmar.

**Decisión propuesta**: mostrar `gr.Markdown("⏳ Extrayendo platos... (5-15 segundos)")` durante el call, luego `gr.Dataframe` con los platos extraídos para que el usuario edite antes de confirmar.

### F6. La pestaña "Configurar" debe ser accesible sin reiniciar el Space

El HF Space mantiene el filesystem efímero. Si el usuario edita y guarda, **el siguiente boot del Space pierde la edición**. Esto es un problema conocido (memory 2026-08-05 R3).

**Decisión propuesta**: la pestaña "Configurar" tiene un disclaimer claro: *"Las ediciones persisten en este Space hasta que se duerma (cold start). Para uso serio, montá tu instancia privada (ver [SECURITY.md](../../SECURITY.md) y patrón template↔live)."*

Esta decisión está alineada con el modelo open core: la demo pública no es donde se hacen configuraciones reales; el servicio de implementación paga es donde se monta la instancia privada del cliente.

### F7. Datos sensibles del cliente real

**NO** se commitea nada de `restaurante.json` ni `catalogo_platos.json` al template (ya cubierto por `.gitignore`: `.agent_knowledge/`). La UI web no cambia esto, pero el indicador debe recordar al usuario que lo que configure en la demo **es público** (es la demo, no su instancia privada).

## Riesgos identificados

| # | Riesgo | Sev. | Mitigación propuesta |
|---|---|---|---|
| R1 | Sobrescritura accidental del perfil | Alta | Confirmación obligatoria antes de guardar |
| R2 | "Editar" sin querer pisa la demo | Alta | Botón "Restaurar perfil demo" + warning al inicio |
| R3 | Extracción de carta falla | Media | Mostrar error con detalle + permitir edición manual del JSON parseado |
| R4 | Validación live rompe la UI si init_options.json está malformado | Baja | Try/except al cargar opciones; fallback a valores del código |
| R5 | Catalog grande (>100 platos) hace lenta la UI | Media | Límite a 100 visibles + paginación |
| R6 | Cold start del Space pierde config | Media | Disclaimer + sugerencia de instancia privada |
| R7 | Datos del cliente terminan en log de HF | Baja | No loggear contenido de restaurante.json; solo IDs y longitudes |
| R8 | Cambio de UI rompe invariantes de `test_app.py` | Baja | Mismas reglas: `theme=`/`css=` solo en `.launch()`, sin `type=` kwarg, ChatInterface dentro de Blocks |
| R9 | El usuario quiere editar el JSON crudo | Baja | Botón "Ver JSON" (solo lectura en v1; edición en v2 si hay demanda) |

## Out of scope (explícito)

- ❌ Multi-tenant / multi-usuario (cada restaurante es su propio Space).
- ❌ Importar carta desde PDF/imagen (OCR) — v2 si hay demanda.
- ❌ Versionado del restaurante.json (rollback a versión anterior) — v2.
- ❌ Drag-and-drop de cartas (UI fancy) — v2 si bloquea adopción.
- ❌ Persistencia fuera del filesystem del Space (S3, etc.) — cambiaría infra, fuera del modelo open core.
- ❌ Editor JSON crudo (todos los campos) — solo lectura en v1.
- ❌ Sincronización con el CLI `init_phase` (round-trip bidireccional) — solo lectura del JSON generado por CLI en v1.

## In scope (explícito)

- ✅ UI de Configurar (con Tabs Chat | Configurar en `app.py`).
- ✅ Carga inicial: lee `restaurante.json` y `catalogo_platos.json` actuales → precarga los inputs.
- ✅ Edición de las 15 dimensiones con los widgets correctos por tipo:
  - `number` → `gr.Number`
  - `choice` → `gr.Dropdown` con choices del JSON + opción "Otra (escribir)"
  - `multichoice` → `gr.CheckboxGroup` + opción "Otra (escribir)" + campo libre
  - `text` → `gr.Textbox`
- ✅ Edición del catálogo con `gr.Dataframe` (CRUD: agregar fila, borrar fila, editar celda).
- ✅ Modo "pegar carta completa" (`gr.Textbox` multilinea + botón "Extraer estructura" → LLM → preview editable).
- ✅ Validación live (los inputs inválidos se marcan en rojo, no se puede guardar).
- ✅ Confirmación antes de guardar (especialmente si el archivo existe).
- ✅ Disclaimer sobre persistencia efímera.
- ✅ Botón "Restaurar perfil demo" (re-seedea desde `agents/creativo/knowledge/demo_*.json`).
- ✅ Tests (`scripts/test_init_web.py`): carga, edición de cada tipo de input, persistencia, validación, no-sobrescritura, modo demo.
- ✅ CHANGELOG y bump de VERSION (v1.4.0 → v1.5.0).
- ✅ Landing `docs/index.html`: actualizar copy del modelo open core (la UI web es parte del servicio de implementación).

## Decisiones de producto (a cerrar con David en proposal)

> **Por defecto asumo** (David las puede cambiar):

1. **Sin autenticación**: el Space público no requiere login. Quien abre la pestaña Configurar puede editar. Esto es OK porque:
   - El perfil demo es público de todas formas.
   - Los datos reales nunca deberían estar en el Space público (regla memoria 2026-08-05 R2).
   - La demo es "juguete" + "evaluación", no "uso real".

2. **Catálogo con `gr.Dataframe`**: mejor balance funcionalidad/simplicidad. Lista virtualizada queda para v2.

3. **Edición JSON crudo solo lectura en v1**: suficiente para usuarios avanzados que quieran ver qué se persiste, sin abrir superficie de error.

4. **Botón "Restaurar perfil demo"**: feature explícita para usuarios que juegan y quieren volver al estado inicial. Útil para demos.

5. **Sin import de carta PDF/imagen en v1**: alinea con "minimalismo en superficie de error". Se agrega si la demanda lo justifica.

6. **Modo "pegar carta" disponible en la UI web**: reusa `_extraer_platos_de_carta()` que ya existe.

7. **Cambiar idioma del Space**: la UI web queda en castellano (consistente con el Space; la landing es la que es trilingüe).

## Siguientes pasos

1. ✅ Explore completado (este artefacto).
2. → **Proposal** con preguntas de producto a David:
   - Q1: ¿La pestaña Configurar debe tener autenticación o ser pública?
   - Q2: ¿Catálogo con `gr.Dataframe` o lista virtualizada?
   - Q3: ¿Botón "Restaurar perfil demo" sí o no?
   - Q4: ¿Edición JSON crudo (solo lectura) sí o no?
3. → **Spec** con RFs y CAs una vez David apruebe el proposal.
4. → **Design** con wireframes ASCII + snippets de código.
5. → **Tasks** con el slicing (probable 3 PRs: backend · UI web · tests).
6. → **Apply** con verificación de `test_app.py` y `test_init_web.py` verde.
7. → **Verify** contra CAs.
8. → **Archive** tras merge.

## Notas operativas (lecciones de memoria)

- **No pushear a `hf`** cambios que no afecten al Space (siguiendo regla de memory 2026-07-02).
- **No tocar `requirements.txt`** sin issue previo (siguiendo regla del proyecto).
- **Mantener invariantes de `test_app.py`** (firma de `responder()`, theme/css en `.launch()`, sin `type=` kwarg, ChatInterface dentro de Blocks).
- **Sin datos reales en commits**: usar `demo_restaurante.json` como base para fixtures y ejemplos.
- **Patrón SDD aplicado**: 1 commit por unidad lógica; stacked PRs si excede 400 líneas.

---

## Resumen del explore (1 línea)

El núcleo de init es 95% reutilizable; la UI web es una capa de presentación data-driven sobre `agents/init_phase.py` + `agents/init_options.json` + `agents/knowledge_context.py`, con `gr.Tabs` en `app.py` para alternar Chat | Configurar, validación live contra el JSON de opciones, y confirmación antes de sobrescribir para evitar pérdida accidental del perfil.
