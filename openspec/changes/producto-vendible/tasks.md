# Tasks — producto-vendible

> Change: `producto-vendible` · Fase: `sdd-tasks` · Proyecto: `restauranteia`
> Base: `openspec/changes/producto-vendible/designs/producto-vendible/design.md` (DD-1..DD-8, contenido exacto de seeds y snippets) + `spec.md` (RF-1..RF-21) + `proposal.md` (CA-1..CA-11)
> Estado: listo para `sdd-apply`. Este artifact es planificación — no genera código.

## Resumen

Hacer vendible la primera capa del producto (Chef Creativo / RestaurantEAI) en 5 commits reversibles e independientes:

| Commit | Contenido | Push |
|---|---|---|
| **C1** | Seed demo (2 JSON) + `_seed_demo_profile()` + rama no-TTY del `__main__` + `scripts/test_seed_demo.py` | `origin` + `hf` |
| **C2** | Indicador `_estado_perfil()` + `gr.Markdown` + `description` de venta + link a la landing | `origin` + `hf` |
| **C3** | `docs/index.html` trilingüe single-file + `docs/assets/` | `origin` solo |
| **C4** | `memory/memory.md` (D5) + `README.md` drift 3→4 skills (SHOULD) | `origin` solo |
| **C5** | Bump `VERSION` v1.3.0 → v1.4.0 + tag (solo si David aprueba) | `origin` + tag |

Reglas de oro: `openspec/` **nunca** a `hf`; `requirements.txt` y `.gitignore` **no se tocan**; firma de `responder()` y `theme=`/`css=` del constructor de Blocks **no cambian**; `agents/init_phase.py` core y prompts/skills del chef **no se tocan**.

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~1.120–1.350 en C1–C4 (C1 ~175-200 · C2 ~25-30 · C3 ~900-1.100 · C4 ~18) |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 (C1) → PR 2 (C2) → PR 3 (C3) → PR 4 (C4) → PR 5 (C5, si aprueba David) |
| Delivery strategy | ask-on-risk |
| Chain strategy | stacked-to-main |

```text
Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High
```

**La landing sola excede el budget de 400 líneas — por diseño**: `docs/index.html` es una reescritura completa (~490 líneas borradas + 450-600 nuevas). El slicing (DD-6) es la mitigación: C3 es un commit propio aislado, C1/C2 quedan muy por debajo de 400. Si aun así se quiere un PR único, se documenta como excepción con el riesgo de review workload explícito.

## Convenciones (idioma de código, tests, commits)

- **Idioma del código/copy**: strings de UI en castellano (neutro peninsular en superficies públicas, decisión 10); identificadores y nombres de skill en inglés/snake_case como el resto del repo. El `description` del Space usa el texto lockeado en el design §4.2 (voseo) — ver Riesgo R6 (decisión pendiente).
- **Tests**: `scripts/test_*.py` usan el mini-helper `check()` + `main() -> int` con exit code (estilo de `scripts/test_app.py`), sin pytest ni red. La suite de memoria usa pytest. No TDD estricto (`strictTDD: false`), pero todo cambio debe terminar con sus tests verdes en el mismo commit.
- **Commits**: conventional commits en inglés, uno por unidad (C1..C5), cada uno revertible por separado (`git revert`). Sugerencia: `feat(seed): ...`, `feat(ui): ...`, `docs(landing): ...`, `docs(memory): ...`, `chore(version): ...`.
- **Push**: alias `git pushall` = `git push hf main && git push origin main` (C1-C2); C3/C4 solo `git push origin main`; C5 `git push origin main && git push origin v1.4.0`. Antes de pushear a `hf`, verificar que `openspec/` no forme parte del árbol de trabajo (NFR-7).
- **Fuente de verdad de valores seed**: `agents/init_options.json` (NUNCA valores inventados fuera del set — el formatter pasa crudos los valores custom).

## Tareas de implementación (checkboxes - [ ])

### C1 — Seed demo + test

- [x] **T1.1** — Crear `agents/creativo/knowledge/demo_restaurante.json` con el contenido EXACTO del design §3.1: 15 dimensiones de `PREGUNTAS_RESTAURANTE` con valores del set válido (ticket 25/60/40, `sofisticacion: "media"`, `productos_dominantes: [vegetales, pescado, mariscos, fruta]`, `epoca_estilo: [mediterranea_moderna, casual_mediterraneo]`, resto según design), más `"demo": true` y `"nombre": "Restaurante de demostración"`.
  - RF-11, RF-10 → CA-7.
  - Verificar: cruzar cada choice/multichoice contra `agents/init_options.json` (`options.<key>.values`) + `python scripts/test_seed_demo.py` (tras T1.4).

- [x] **T1.2** — Crear `agents/creativo/knowledge/demo_catalogo_platos.json` con los 10 platos EXACTOS del design §3.2 (2 entrantes, 3 principales, 1 guarnición, 2 postres, 2 "otro"; precios 5-26€; categorías ∈ {entrante, principal, postre, guarnicion, bebida, otro}).
  - RF-12 → CA-7.
  - Verificar: `python scripts/test_seed_demo.py` (check 4: 8-12 platos, keys `nombre/categoria/descripcion/precio`, categorías válidas).

- [x] **T1.3** — Modificar `app.py`: agregar helper `_seed_demo_profile()` (design §3.3) y reemplazar la rama no-TTY del bloque `if __name__ == "__main__":` (design §3.4): hoy genera vacíos + warning; pasa a llamar `_seed_demo_profile()`. El branch TTY (`fase_init_interactiva()`) queda **intacto**.
  - **Hallazgo verificado (crítico)**: `guardar_restaurante()` / `guardar_catalogo()` en `agents/knowledge_context.py` (L63-77) **sobrescriben siempre** (`open("w")` incondicional) — el design §3.3-3.4 asume que solo escriben archivos faltantes, y eso NO es cierto en el código actual. `bootstrap_necesario()` es True si falta CUALQUIERA de los dos archivos, así que el helper DEBE guardar por archivo faltante usando `restaurante_existe()` / `catalogo_existe()` (ya expuestos por `agents.knowledge_context`); de lo contrario un `restaurante.json` real existente se pisaría con el demo (viola RF-13).
  - Además: `app.py` NO importa `json` al tope (verificado) → `import json` local dentro del helper.
  - Loggear "Perfil demo genérico seedeado (no-TTY boot)" con `logger.info`.
  - RF-10, RF-13 → CA-7.
  - Verificar: `python scripts/test_seed_demo.py` (check 5, incluido el caso "un archivo existe y el otro falta").

- [x] **T1.4** — Crear `scripts/test_seed_demo.py` (estilo `check()` de `scripts/test_app.py`), sin red ni API, con los 5 checks del design §6: (1) `demo_restaurante.json` parsea y tiene las 15 claves del schema; (2) `demo: true` + nombre no vacío; (3) cada valor choice/multichoice ∈ set válido de `agents/init_options.json`; (4) `demo_catalogo_platos.json` 8-12 platos con keys obligatorias y categoría válida; (5) `_seed_demo_profile()` no sobrescribe archivos existentes — preparar archivos destino con contenido real en un dir temporal (monkeypatch de `RESTAURANTE_PATH`/`CATALOGO_PATH` o `KNOWLEDGE_DIR`) y verificar contenido intacto tras llamar. El check 5 debe cubrir **ambos** casos: ninguno falta y solo falta uno (donde vive el bug de sobrescritura).
  - RF-15 → CA-7, CA-9.
  - Verificar: `python scripts/test_seed_demo.py` → exit 0.

- [x] **T1.5** — Verificación integral de C1 (invariantes intactos): `python scripts/test_seed_demo.py` (exit 0) + `python scripts/test_app.py` (6/6) + `python -m pytest tests/ -q` (120 tests memoria verdes). Además `git status`/`git ls-files`: 2 JSON nuevos trackeados en `agents/creativo/knowledge/`, **cero** archivos en `.agent_knowledge/`, `git diff .gitignore` → vacío.
  - RF-19, RF-10 → CA-9, CA-10 (parcial).
  - ⚠️ **Baseline roto pre-existente (verificado 2026-08-05)**: `test_firma_responder` de `scripts/test_app.py` espera `responder()` con 2 argumentos, pero el código real tiene 3 (`mensaje, historial, skill="ficha"` — el parámetro `skill` se agregó al añadir el selector de skills en la UI). El test quedó desactualizado y **ya fallaba antes de este change**. Para cumplir CA-9, incluir en C1 (o C2, donde toca `responder`) un fix mínimo del test: permitir 2 args + 1 opcional con default (`len(args) == 2 or (len(args) == 3 and default para el 3º)`). NO cambiar la firma del código — solo corregir el test para reflejar la realidad. Documentar en el commit.
  - Verificar: `python scripts/test_app.py` → 6/6 tras el fix.

- [x] **T1.6** — Deploy C1: commit + `git push origin main` + `git push hf main` (NFR-7; `openspec/` nunca a `hf`). Rollback: `git revert d109e5e` (commit C1).

### C2 — Indicador + description + link

- [x] **T2.1** — Modificar `app.py`: agregar helper `_estado_perfil()` con el código EXACTO del design §3.3 (estados: `demo == true` → `🧪 **Demo**: <nombre>…`; `FileNotFoundError` o nombre vacío → `*(sin contexto de restaurante)*`; perfil real → `🍽️ **Perfil activo**: <nombre>`).
  - RF-14 → CA-8.
  - Verificar: `grep -n "Demo" app.py` (CA-8) + manual en Space tras deploy.

- [x] **T2.2** — Modificar `app.py`: dentro de `with gr.Blocks() as demo:` (sección `# UI con Gradio 5+`), ANTES del `gr.ChatInterface` (junto al `skill_selector`), agregar `perfil_md = gr.Markdown(_estado_perfil())`. NO tocar `theme=`/`css=` del constructor de Blocks (invariante `test_kwarg_prohibidos` — theme/css solo en `.launch()`).
  - RF-16 → CA-8.
  - Verificar: `python scripts/test_app.py` (6/6).

- [x] **T2.3** — Modificar `app.py`: reemplazar el `description=` del `gr.ChatInterface` por el copy EXACTO del design §4.2 (**neutro peninsular**, decisión 10 — menciona los 4 modos reales Ficha técnica · Proceso creativo · Ideas creativas · Chat con el chef y el perfil demo precargado; sin "15 preguntas" ni "recuerda para siempre").
  - RF-18 → CA-8.
  - Verificar: lectura de `app.py` + manual en Space (CA-8). (Riesgo R6 cerrado: el design §4.2 fue corregido a neutro peninsular — el Space es superficie pública.)

- [x] **T2.4** — Modificar `app.py`: link a la landing en el Markdown del indicador (o segundo `gr.Markdown` contiguo): `  ·  [🌐 Volver a la web](https://davidlopezg.github.io/restauranteai/)` (design §4.3).
  - RF-17.
  - Verificar: `grep -n "restauranteai" app.py` + manual en Space.

- [x] **T2.5** — Verificación de orden: `_estado_perfil()` se evalúa al construir la UI, y el seed corre ANTES en `__main__` (riesgo T4 del design). Verificar lanzando `python app.py` local con `.agent_knowledge/` ausente y sin TTY simulado (o revisar el orden del bloque `__main__`), confirmando que el indicador muestra "🧪 Demo: Restaurante de demostración". Si el orden se rompiera, el indicador caería a "(sin contexto)".
  - RF-14, RF-16 → CA-8.

- [x] **T2.6** — Deploy C2: commit + `git push origin main` + `git push hf main`. Rollback: `git revert <commit C2>`.

### C3 — Landing trilingüe

- [x] **T3.1** — Reescribir `docs/index.html` (single-file, zero-deps, reemplaza la landing actual) con el patrón del design §5: skeleton HTML + `<style>` inline (paleta mediterránea: texto `#1a1714`, acento `#c44d34`, fondo crema `#faf7f2`, system-ui) + diccionario JS `LANG = { es: {...}, ca: {...}, en: {...} }` con TODAS las claves visibles en los 3 idiomas + atributos `data-i18n` / `data-i18n-href` + selector en header (3 botones `ES | CA | EN`, idioma activo marcado) + función `aplicar_idioma(lang)` que actualiza `document.documentElement.lang`, `<title>` y `<meta name="description">` sin recarga + init: `localStorage > navigator.language (ca/es/en) > "es"`. Sin `<script src=>`, sin `<link rel="stylesheet">` externo, sin `@import`, sin `url(http…)` hacia terceros. Los únicos enlaces externos: Space HF, GitHub y `mailto:`.
  - RF-1, RF-2 (2.1-2.4) → CA-1.
  - Verificar: grep CA-1 (T3.4) + navegación manual trilingüe (T3.5).

- [x] **T3.2** — Escribir el copy completo dentro de T3.1 (verificable por greps), en castellano neutro peninsular (decisión 10):
  - **Hero** problema→solución ("¿renovar la carta te lleva semanas?…") con CTA primario → Space HF y CTA secundario → oferta (RF-3; sin "MVP-0.5").
  - **Skills**: las 4 skills con `nombre` EXACTO del registry (`agents/creativo/skills.py`): Ficha técnica · Proceso creativo · Ideas creativas · Chat con el chef, descripciones fieles (RF-4).
  - **Demo**: texto explícito "perfil genérico de restaurante mediterráneo, marcada como demo" (RF-5.3) + línea discreta de cold start "la primera visita puede tardar unos segundos en arrancar" (RF-5.4).
  - **Oferta open core**: "el software es gratis, código abierto (MIT); la implementación en tu restaurante es un servicio pago" + CTA `mailto:davidlopezgamero@gmail.com` con `subject=` pre-armado URL-encoded por idioma: es `Quiero el Chef Creativo en mi restaurante`, ca `Vull el Chef Creativo al meu restaurant`, en `I want Chef Creativo in my restaurant` (design §5.3; destinatario siempre el mismo) (RF-6).
  - **FAQ**: 4-6 objeciones reales traducidas a los 3 idiomas (programar, tiempo de demo, datos/privacidad, ticket, carta, demo) (RF-7).
  - **Footer honesto**: GitHub + Space HF + MIT + "construido por un hostelero real (David López Gamero) · Cataluña, 2026". Sin testimonios inventados, sin "Sol de Nit", sin métricas falsas (RF-8).
  - RF-3..RF-9 → CA-2..CA-6.

- [x] **T3.3** — Crear `docs/assets/demo-ficha.png` (obligatorio) + `demo-proceso-creativo.png` y `demo-ideas.png` (opcionales si el budget lo permite): capturas de la demo con el perfil demo (sin datos reales, sin "Sol de Nit"). Plan A: captura local (navegador o playwright) y commitear; **si el entorno de apply no tiene playwright ni navegador**, usar el fallback documentado: celda de ejemplo renderizada en HTML puro en la sección demo (CA-6 "visual" se cumple igual; el screenshot queda como mejora pendiente).
  - RF-5.2 → CA-6. ⚠️ **Decisión de David en apply**: método de generación de capturas.

- [x] **T3.4** — Verificación por grep (CA-1..CA-6):
  - `grep -nE "<script[^>]*src=|<link[^>]*stylesheet[^>]*href=|<style>@import|url\(https?://" docs/index.html` → **0 coincidencias** (CA-1).
  - `grep -rn "MVP-0.5" docs/` → **0 coincidencias** (CA-2).
  - `grep -n "Ficha técnica\|Proceso creativo\|Ideas creativas\|Chat con el chef" docs/index.html` → **≥4 coincidencias** (una por skill; CA-3).
  - `grep -n 'mailto:davidlopezgamero@gmail.com' docs/index.html` → 3 subjects distintos, no vacíos (CA-4).
  - `grep -rni "sol de nit" docs/ agents/creativo/knowledge/` → **0 coincidencias** (CA-5).
  - `grep -ni "genéric\|mediterráne" docs/index.html` → coincidencias (CA-6) + `ls docs/assets/` → asset presente (o celda HTML renderizada).

- [x] **T3.5** — Verificación manual trilingüe (escenarios del spec): cargar sin interacción → castellano completo + selector con castellano activo + `lang="es"`; cambiar a català → todo el contenido cambia sin recarga + `lang`/`title`/`meta` → `ca`; a English → ídem; CTAs conservan destinos (Space y mailto). Revisar que ningún texto visible quede fuera del diccionario (RF-2.1) y que la página siga responsive (NFR-6).
  - RF-2 → CA-1.

- [x] **T3.6** — Deploy C3: `git push origin main` SOLO (**NO** a `hf`) + `curl -sI https://davidlopezg.github.io/restauranteai/` → HTTP 200 (CA-11). Rollback: `git revert <commit C3>` restaura la landing anterior al instante.

### C4 — Memoria + README (SHOULD)

- [x] **T4.1** — Modificar `memory/memory.md`: entrada D5 con el stack real — vigente: `gradio>=6.19,<7.0` + `huggingface_hub>=1.2,<2.0` + Python 3.11, sin pins de `pydantic`/`jinja2` (`requirements.txt` y frontmatter del README como fuente de verdad); el combo de la era Gradio 5.6 (`gradio>=5.6,<6.0`, `huggingface_hub<1.0`, `pydantic==2.10.6`, `jinja2<3.1.0`) quedó **obsoleto** y reintroducirlo rompe Gradio 6 y `test_app.py`; se conservan vigentes las lecciones estructurales de la deploy saga (Python 3.11 obligatorio, `cache_examples=False`, defensa en profundidad).
  - RF-20 → CA-10.
  - Verificar: `grep -n "6.19\|Gradio 6\|5.6" memory/memory.md` → entrada presente + `git diff requirements.txt` → **vacío**.

- [x] **T4.2** — Modificar `README.md` (SHOULD, ~3 líneas): corregir el drift documental "3 skills" → "4 skills" (estado del proyecto, sección "Probar las 3 skills", tabla de skills si entra en el diff acotado — mínimo: el estado y el encabezado). Si el budget no lo permite, dejar anotado como pendiente para el change `init-web`.
  - RF-21.
  - Verificar: `grep -n "4 skills\|3 skills" README.md`.

- [x] **T4.3** — Deploy C4: commit + `git push origin main` SOLO. Rollback: `git revert <commit C4>`.

### C5 — Versionado (si David aprueba)

- [x] **T5.1** — Modificar `VERSION`: `v1.3.0` → `v1.4.0`. ⚠️ **Decisión de David en apply**: aprobación del bump + tag.
  - Verificar: `cat VERSION` → `v1.4.0`.

- [x] **T5.2** — Tag de release: `git tag v1.4.0 && git push origin v1.4.0` (+ `git push origin main`). ⚠️ **Decisión de David en apply**.
  - Verificar: `git ls-remote --tags origin` → `v1.4.0`.

- [x] **T5.3** — Verificación opcional: en la instancia viva (`restauranteia-live`), `./scripts/restauranteai-sync` detecta la versión nueva (v1.3.0 → v1.4.0) y ofrece el resumen de cambios. Manual, solo si la instancia existe y David lo pide.

## Orden de ejecución

```
C1 (seed+test) → C2 (indicador+description+link) → C3 (landing+assets) → C4 (memory+README) → C5 (versionado, si aprueba David)
```

Comandos de verificación por stage (los mismos que en las tareas):

```bash
# Stage C1
python scripts/test_seed_demo.py          # exit 0
python scripts/test_app.py                # 6/6 (invariantes intactos)
python -m pytest tests/ -q                # 120 tests memoria verdes
git status && git ls-files agents/creativo/knowledge/   # 2 JSON nuevos; cero en .agent_knowledge/
git diff .gitignore                       # vacío
git push origin main && git push hf main  # NFR-7: openspec/ nunca a hf

# Stage C2
python scripts/test_app.py                # 6/6
grep -n "Demo" app.py                     # componente indicador presente
grep -n "restauranteai" app.py            # link a la landing presente
python app.py                             # orden seed → UI (indicador "🧪 Demo: …")
git push origin main && git push hf main

# Stage C3 (greps de CA-1..CA-6, ver T3.4)
grep -nE "<script[^>]*src=|<link[^>]*stylesheet[^>]*href=|<style>@import|url\(https?://" docs/index.html   # → 0
grep -rn "MVP-0.5" docs/                  # → 0
grep -n "Ficha técnica\|Proceso creativo\|Ideas creativas\|Chat con el chef" docs/index.html   # → ≥4
grep -n 'mailto:davidlopezgamero@gmail.com' docs/index.html   # 3 subjects no vacíos
grep -rni "sol de nit" docs/ agents/creativo/knowledge/       # → 0
grep -ni "genéric\|mediterráne" docs/index.html               # ≥1
ls docs/assets/                           # asset screenshot o celda HTML renderizada
git push origin main                      # SOLO origin (NO hf)

# Stage C4
grep -n "6.19\|Gradio 6\|5.6" memory/memory.md   # entrada D5 presente
git diff requirements.txt                        # vacío (CA-10)
grep -n "4 skills\|3 skills" README.md           # drift corregido
git push origin main                             # SOLO origin

# Stage C5 (si aprueba David)
cat VERSION                            # v1.4.0
git tag v1.4.0 && git push origin v1.4.0
```

## Dependencias

- **C2 depende de C1**: `_estado_perfil()` lee `restaurante.json`; en boot no-TTY ese archivo solo existe tras el seed de C1. El orden del `__main__` (seed → construir `demo`) garantiza el estado correcto (riesgo T4 del design).
- **C3 no depende de código**, pero su copy DEBE ser honesto sobre el perfil demo (RF-5.3: "perfil genérico… marcada como demo") → es más seguro aplicar C3 después de que C1 esté en producción (el Space realmente muestra el demo). Si C3 se aplicara antes de C1, el texto seguiría siendo cierto (el seed es el diseño del Space), pero la verificación manual en el Space no sería posible hasta C1.
- **C4 es independiente** de C1-C3; se deja al final por ser SHOULD y menor.
- **C5 va al final**, tras el merge de C1-C4: el bump + tag marcan la release completa de la Fase 1.

## Forecast de review (líneas estimadas por commit)

| Commit | Archivos | Líneas est. (add+del) | ≤ 400? |
|---|---|---|---|
| C1 | `agents/creativo/knowledge/demo_restaurante.json` (~25) + `demo_catalogo_platos.json` (~35) + `app.py` (~+35) + `scripts/test_seed_demo.py` (~80) | ~175-200 | ✅ |
| C2 | `app.py` (`_estado_perfil` ~12 + `gr.Markdown` ~2 + `description` ~8 + link ~2) | ~25-30 | ✅ |
| C3 | `docs/index.html` (reescritura: ~490 borradas + 450-600 nuevas) + `docs/assets/*.png` (binario) | ~900-1.100 + binarios | ❌ por diseño (commit propio aislado) |
| C4 | `memory/memory.md` (~+15) + `README.md` (~+3) | ~18 | ✅ |
| C5 | `VERSION` (1) + tag | ~2 | ✅ |
| **Total C1-C4** | — | **~1.120-1.350** | ❌ — el slicing es la mitigación |

> Nota de review: aunque el diff total de C1-C4 excede 400, cada commit individual (salvo C3) queda muy por debajo; C3, el más grande, es HTML estático de una sola sección de review y es revertible al instante. Confirmar con David la estrategia (stacked-to-main según design §8 vs. PRs por commit) — config `chainedPRStrategy: ask-always`.

## Criterios de aceptación por commit (CA mapping)

| Commit | CAs que satisface | Verificación concreta |
|---|---|---|
| C1 | CA-7, CA-9 (parcial: seed test), CA-10 (parcial: `requirements.txt` sin cambios) | `python scripts/test_seed_demo.py` + `git status`/`git diff .gitignore` |
| C2 | CA-8, CA-9 (parcial: `test_app.py` 6/6) | `grep -n "Demo" app.py` + `python scripts/test_app.py` + manual en Space |
| C3 | CA-1, CA-2, CA-3, CA-4, CA-5, CA-6, CA-11 (parcial: Pages live 200) | greps T3.4 + navegación manual trilingüe + `curl -sI` |
| C4 | CA-10 | `grep "6.19\|5.6" memory/memory.md` + `git diff requirements.txt` vacío |
| C5 | (ninguno directo — decisión de delivery) | `cat VERSION` + tag |
| Global | CA-9 completo (seed + test_app + 120 memoria) | `python scripts/test_seed_demo.py` + `python scripts/test_app.py` + `python -m pytest tests/ -q` |
| Global | CA-11 completo | `git push origin main` + `git push hf main` (solo archivos de app; nunca `openspec/`) + HTTP 200 |

## Riesgos de implementación

| # | Riesgo | Sev. | Mitigación / acción en apply |
|---|---|---|---|
| R1 | **`guardar_*` sobrescribe siempre** (verificado en `agents/knowledge_context.py` L63-77: `open("w")` incondicional; el design §3.3-3.4 asume lo contrario) | **Alta** | `_seed_demo_profile()` (T1.3) guarda SOLO el archivo faltante vía `restaurante_existe()`/`catalogo_existe()`; el test T1.4 check 5 cubre el caso "solo falta uno". Sin esto, RF-13 se viola cuando existe solo `restaurante.json` o solo `catalogo_platos.json`. |
| R2 | `app.py` no importa `json` al tope (verificado) | Baja | `import json` local dentro de `_seed_demo_profile()` (ya contemplado en T1.3). |
| R3 | Screenshot no generable en el entorno de apply (sin playwright/navegador) | Media | Plan A: captura local + commit; fallback: celda de ejemplo en HTML puro (CA-6 se cumple; screenshot queda como mejora). ⚠️ Decidir con David. |
| R4 | Landing excede budget 400 | Media | Por diseño (DD-6): C3 es commit propio; el resto del diff queda muy por debajo. PR único = excepción documentada. |
| R5 | Orden `_estado_perfil()` vs seed en `__main__` | Media | El orden actual ya lo garantiza (seed antes de construir `demo`); verificar en apply con `python app.py` (T2.5). |
| R6 | **`description` del Space con voseo** ("Elegí/probá/pedile", design §4.2) vs decisión 10 (neutro peninsular en superficies públicas) | Baja | El design lockeó ese texto; la UI del Space es superficie pública. ⚠️ Confirmar con David en apply: mantener texto del design o alinearlo a neutro. |
| R7 | C5 (bump VERSION + tag) requiere aprobación de David | Baja | No ejecutar T5.1-T5.2 sin aprobación explícita; si no aprueba, queda documentado como pendiente para el próximo change. |
| R8 | Gradio 6 cambia render de `gr.Markdown` en Blocks | Baja | Componente de solo lectura, sin eventos; verificado por `python scripts/test_app.py` (T2.5/T2.6). |
| R9 | Valores seed fuera de set (rompen mapeos del formatter) | Baja | Contenido exacto del design §3.1-3.2 verificado contra `agents/init_options.json`; el test T1.4 check 3 lo vela. |
| R10 | Push accidental de `openspec/` a `hf` | Media | Regla NFR-7: verificar árbol antes de `git push hf main`; `git pushall` solo para C1-C2. |

**No tocar** (invariantes): `requirements.txt`, `.gitignore`, firma `responder(mensaje, historial, skill="ficha") -> dict`, `theme=`/`css=` en el constructor de Blocks, `cache_examples=False`, kwarg `type=` en ChatInterface/Chatbot, core de `agents/init_phase.py` (solo se reutilizan `_schema_doc_*`), prompts/skills del chef.
