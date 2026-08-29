# 📝 Changelog

Todos los cambios notables de **RestaurantEAI** (alias local: `restauranteia`) se documentan acá. El formato sigue [Keep a Changelog](https://keepachangelog.com/es/1.1.0/), y el proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

> **Repos:**
> - Template (público): [`davidlopezg/restauranteai`](https://github.com/davidlopezg/restauranteai) → esta es la fuente de verdad del CHANGELOG.
> - HF Space: [`davidlopezgamero/RestaurantEAI`](https://huggingface.co/spaces/davidlopezgamero/RestaurantEAI).
> - Landing: [davidlopezg.github.io/restauranteai](https://davidlopezg.github.io/restauranteai/).

---

## [1.5.0] — 2026-08-29 — "init-web: Configurar mi restaurante"

> Pestaña web en el HF Space para configurar el restaurante y la carta sin tocar terminal. Cierra la **Fase 2 del producto vendible**.

### Added
- Pestaña **"⚙️ Configurar mi restaurante"** en el HF Space (`gr.Tabs(Chat, Configurar)`). Self-service del hostelero en navegador.
- Módulo nuevo `app_init_web.py` (~520 líneas) con render data-driven desde `PREGUNTAS_RESTAURANTE` y `PREGUNTAS_POR_PLATO`.
- Helpers de carga/guarda con guard + backup en `agents/knowledge_context.py`: `cargar_restaurante_con_default`, `cargar_catalogo_con_default`, `guardar_con_backup`, `guardar_catalogo_con_backup`, `leer_con_backup_dir`. Mitigan el bug F1 (sobrescritura cruzada de `guardar_*`).
- Modo **"Pegar carta completa"**: extracción LLM desde texto libre con feedback visual (`gr.Markdown`).
- Búsqueda en vivo del catálogo (case-insensitive sobre nombre/categoría/descripción) + paginación a 25 filas.
- Confirmación obligatoria antes de sobrescribir un perfil real (`gr.Group` + `gr.Checkbox`).
- Botón **"Restaurar perfil demo"** con doble-check (`solo funciona si demo=true`).
- Vista **"Ver JSON"** colapsable con `restaurante.json` + `catalogo_platos.json` formateados.
- Auth básica (`auth=(user, password)`) en `.launch()` leída de env vars (`CONFIG_USER`, `CONFIG_PASSWORD`) configurables como Secrets de HF. La pestaña "Chat" sigue pública.
- Tests `scripts/test_init_web.py` con 8/8 checks verdes.
- Sección "Autenticación" en `SECURITY.md` documentando el modelo.

### Changed
- `app.py`: la UI ahora vive dentro de `gr.Tabs` (antes estaba directamente en `gr.Blocks`).
- `scripts/test_seed_demo.py`: stub de Gradio extendido con `.change()`/`.click()`/`.submit()` no-ops (para poder importar `app_init_web.py` sin gradio real).
- `README.md`: estado del proyecto + roadmap actualizado.

### Fixed
- Bug **F1** de `explore.md`: `guardar_restaurante()`/`guardar_catalogo()` sobrescribían siempre. Ahora `guardar_con_backup()` crea backup automático del archivo previo antes de sobrescribir.

### Seguridad
- Las credenciales de la pestaña "Configurar" se leen de HF Secrets (`CONFIG_USER`, `CONFIG_PASSWORD`). NO se commitean al repo.
- El perfil demo es público por diseño (no contiene datos reales).

### Push
- `origin/main`: PR 1 (`be42ff7`) + PR 2 (`6eb3fdb`) + PR 3 (este).
- `hf/main`: PR 1 (`4e31b02`) + PR 2 (`781456d`) — cherry-pick para evitar los `docs/assets/*.png` que HF rechaza.
- Tag `v1.5.0` por crear.

### Notas
- Patrón "externalización de opciones en JSON + fallback hardcoded" se mantiene para las 15 dims de `PREGUNTAS_RESTAURANTE`.
- Patrón "data-driven UI desde el schema" funciona sin tocar `app_init_web.py` cuando se agregan dims nuevas (basta con `PREGUNTAS_RESTAURANTE` + `init_options.json`).
- HF OAuth nativo (Q1 del proposal) **no se implementó** en esta versión: fallback a auth básica con Secrets. OAuth queda como upgrade futuro cuando HF lo soporte out-of-the-box en Spaces free.

---

## [Unreleased]

### Planeado
- **v1.6.0** — Capturas de pantalla reales de la demo (mejora pendiente del verify-report 2026-08-05) + neutralizar voseo residual en `skill_selector` del Space.
- **v2.0.0** — Segundo agente del ecosistema (Producción o Marketing, a decidir por tracción).
- Búsqueda full-text en el Archivo de Ideas (FTS5 de SQLite).
- Categorización automática de ideas (LLM).
- HF OAuth nativo (reemplaza auth básica cuando esté soportado en Spaces free).

---

## [1.4.0] — 2026-08-05 — "Producto vendible (Fase 1)"

> El proyecto deja de ser "un proyecto personal" y pasa a ser "una página que vende". Modelo **open core**: software gratis MIT, monetización por servicio de implementación.

### ✨ Added
- **Perfil demo genérico** que se seedea automáticamente al boot del Space HF cuando no hay TTY (`agents/creativo/knowledge/demo_restaurante.json` + `demo_catalogo_platos.json`, mediterráneo, ticket 25-60 €, 10 platos). Reemplaza los archivos vacíos + warning.
- **Landing trilingüe** (`docs/index.html`): single-file, zero-deps, 3 versiones completas (català · castellano · English) con selector funcional y default castellano. Hero problema→solución, las 4 skills reales, sección demo con visual, oferta open core con CTA `mailto:` con subject pre-armado por idioma, FAQ y footer honesto. Sin "Sol de Nit", sin métricas inventadas.
- **Indicador de perfil** en el Space (componente `gr.Markdown` dentro de `gr.Blocks`): muestra "🧪 Demo: …", "🍽️ Perfil activo: …" o "(sin contexto)".
- **Link a la landing** desde el Space.
- **`description` del ChatInterface** alineado a venta (4 modos + perfil demo precargado, castellano neutro peninsular).
- **`scripts/test_seed_demo.py`** (5 checks): valida schema del seed, valores válidos contra `init_options.json`, no-sobrescritura de perfiles existentes (casos A/B1/B2).

### 🐛 Fixed
- **`test_firma_responder` roto pre-existente** en `scripts/test_app.py` (esperaba 2 args; la firma real tiene 3 con default). Test corregido, código intacto.
- Landing anterior que decía "MVP-0.5" (jerga interna) y omitía 2 de 4 skills.
- Drift del README "3 skills" → "4 skills" (drift menor).

### 📚 Changed
- Documentación del stack real de deps en `memory/memory.md` (D5): `gradio>=6.19,<7.0` + `huggingface_hub>=1.2,<2.0` + Python 3.11 es la fuente de verdad; el combo de la era Gradio 5.6 está obsoleto y no debe reintroducirse.
- `app.py` rama no-TTY: en vez de warning de archivos vacíos, ahora seedea el perfil demo.

### 🧪 Tests
- 6/6 checks en `scripts/test_app.py` (incluye fix del test de firma).
- 5/5 checks en `scripts/test_seed_demo.py` (nuevo).
- **132 tests** verdes en `pytest tests/ -q`.

### 📦 Deploy
- 5 commits apilados (C1 seed → C2 UI → C3 landing → C4 memory → C5 bump versión).
- `git pushall` para C1 y C2; `git push origin main` para C3 y C4; tag `v1.4.0` creado.
- `openspec/changes/producto-vendible/` archivado tras verificación exitosa.

---

## [1.3.0] — 2026-07-02 — "Archivo de Ideas"

> El chef deja de ser de "usar y tirar": ahora tiene memoria persistente del proyecto. **El consentimiento humano explícito es invariante: solo se guarda lo que el usuario ordena con `/guardar`.**

### ✨ Added
- **Módulo `agents/memoria/`**: persistencia local SQLite con WAL mode para concurrencia segura en HF Space.
- **11 comandos transversales** disponibles desde cualquier skill:
  - `/guardar [texto]`, `/guardar` (último mensaje), `/guardar N` (de lista numerada), `/guardar igual` (post-duplicado)
  - `/editar N [texto]`
  - `/ideas [filtro]`
  - `/olvidar N`, `/olvidar todo`
  - `/export-ideas`
  - `/silenciar-contador`
  - `/ayuda`
- **Detección de duplicados**: exacta (case-insensitive via `COLLATE NOCASE`) + fuzzy (≥80% similitud vía `difflib.SequenceMatcher`).
- **RGPD desde el día uno**: borrado granular con doble confirmación, export portable a JSON, sin telemetría, SQLite local.
- **Categorías externalizadas** en `agents/ideas_categorias.json`.
- **Skill `chat`** (`agents/creativo/prompts/system_chat.md` + handler `procesar_mensaje_chat`): conversación libre con el chef que inyecta restaurante + catálogo + últimas 10 ideas guardadas como contexto.
- **Script `scripts/restauranteai-sync`**: sincronización entre repos template↔instancia viva con detección de versión (`VERSION` raíz vs `.template-version` gitignored).
- **Patrón template → instancia viva** documentado: repo público (`davidlopezg/restauranteai`) + repo privado (`davidlopezg/restauranteia-live`) sincronizable.

### 🧪 Tests
- **120 tests** pytest verdes: storage, formatters, commands, duplicates, counter, RGPD, concurrencia WAL, regresión de skills.
- Helpers de test reusables en `tests/test_regresion_skills.py` y `tests/test_skill_chat.py` (mockean gradio con `sys.modules` para entornos sin Gradio).

### 📚 Changed
- `agents/creativo/agent.py`: dispatcher de comandos del Archivo de Ideas al inicio de cada handler (transversal a todas las skills).
- `app.py`: dispatcha comandos del Archivo de Ideas ANTES del dispatcher de skills (decisión arquitectónica: el archivo es transversal).
- README reescrito para documentar el módulo y el patrón template↔live.

---

## [1.2.0] — 2026-07-02 — "Sistema de skills + proceso creativo"

> El chef pasa de tener un único modo a tener un sistema extensible de skills con estado.

### ✨ Added
- **Sistema de skills extensible** (`agents/creativo/skills.py`): registry cerrado y explícito (no magic discovery por filesystem). 4 skills iniciales:
  1. `ficha` — Ficha técnica estructurada
  2. `proceso_creativo` — State machine de 7 fases con persistencia
  3. `ideas_creativas` — Exploración de 10 ideas con métodos creativos de ElBulli
  4. `chat` — *(añadido en v1.3.0, listado en v1.2 a modo de placeholder en el roadmap)*
- **State machine de proceso creativo** (`agents/creativo/proceso_creativo.py`): 7 fases (alma, métodos creativos, equilibrio, técnica, storytelling, descartadas, preguntas) con persistencia en `.agent_knowledge/sessions/`.
- **Comandos del proceso creativo**: `/estado`, `/fase N`, `/fase nombre`, `/volver`, `/ficha`, `/ficha forzar`, `/reiniciar`, `/salir`, `/sesiones`, `/reanudar ID`.
- **Persistencia de sesiones** en `.agent_knowledge/sessions/<id>.json` (en `.gitignore`).
- **Ideas creativas**: 10 ideas por consulta, refinamiento con 13 métodos creativos de ElBulli (`aplicá [método] a la idea N`), conversión a ficha técnica.
- **Contexto automático del restaurante**: 15 dimensiones de `restaurante.json` se inyectan en el system prompt de cada skill.
- **Catálogo automático**: hasta 30 platos de `catalogo_platos.json` se inyectan en cada respuesta (sin duplicar, llenando huecos, sugiriendo complementos).

### 🐛 Fixed
- **Idioma**: detección + reintento automático si el chef responde en inglés (`_es_principalmente_espanol()` con heurística de palabras gatillo + instrucción reforzada + temperatura 0.2; máx 2 reintentos).
- **UTF-8 surrogate fix**: emojis y caracteres especiales encodeados correctamente con `\U0001F3A8` (no `\ud83c\udfa8`).

### 📚 Changed
- `init_options.json` externalizado (oportunidad de extender las opciones del init sin tocar código; el sistema ofrece "otra (escribir)" automáticamente).
- Init con carta completa: el LLM extrae JSON estructurado desde texto libre (con robustez: JSON puro, markdown JSON, texto alrededor, normalización de campos).
- Opciones del init externalizadas (decisión 2026-07-01 en memory).

---

## [1.1.0] — 2026-07-01 — "MVP-0.5 — Hugging Face Space"

> El agente deja de ser un script CLI y pasa a ser una app web desplegada en HF Spaces.

### ✨ Added
- **`app.py`** (UI Gradio): wrapper sobre `agents/creativo/agent.py` con `gr.ChatInterface` en formato `messages`.
- **Deploy a Hugging Face Space** `davidlopezgamero/RestaurantEAI` con `app_file: app.py`, `python_version: '3.11'`, `sdk: gradio`, `sdk_version: 6.19.0`.
- **Frontmatter YAML** en el README (HF lo lee automáticamente).
- **Landing page inicial** (`docs/index.html`): HTML autocontenido, sin dependencias externas, deployable vía GitHub Pages.
- **Fixes de deploy** (8 fixes consecutivos documentados en `memory/memory.md` 2026-07-01):
  1. `python_version: '3.11'` (HF default 3.13 rompe Gradio).
  2. `huggingface_hub>=0.19.3,<1.0` (luego actualizado a ≥1.2 con Gradio 6).
  3. Reorden de layout en `app.py` (bug propio: `msg` antes de definirlo).
  4. `pydantic==2.10.6` (compatibilidad con `gradio_client 1.3.0`).
  5. `jinja2<3.1.0` (compatibilidad con starlette).
  6. Migración a Gradio 5.6 (`gr.ChatInterface` reemplazó código custom).
  7. Re-fix de `HfFolder` (Gradio 5.6 oauth).

### 📚 Changed
- **Iteración del system prompt**: integración de los 17 métodos creativos de ElBulli (`docs/metodos-creativos.md`) como caja de herramientas creativas del chef (no se nombran explícitamente en la ficha, pero el chef los usa como lentes internos).
- **`agents/creativo/agent.py`**: validación de idioma y reintentos.

### 🧪 Tests
- **`scripts/test_app.py`** (6 checks): sintaxis, kwargs prohibidos Gradio 6+, firma de `responder()`, ChatInterface dentro de Blocks, theme/css en `.launch()`, detección de idioma.
- **`scripts/probar_estructura.py`**: validación sin API (dependencias, recursos, config, conformidad con endpoints/modelos oficiales).

---

## [1.0.0] — 2026-06-30 — "MVP-0 — Agente Chef Creativo CLI"

> Primer agente funcional: CLI que toma una petición culinaria en lenguaje natural y devuelve una ficha estructurada.

### ✨ Added
- **`agents/creativo/agent.py`**: entry point CLI del Chef Creativo (`python -m agents.creativo.agent "petición"`).
- **`agents/init_phase.py`**: fase init con 15 preguntas sobre el restaurante + catálogo de platos (3 modos: pegar carta / manual / saltar).
- **`agents/knowledge_context.py`**: archivos compartidos (`restaurante.json`, `catalogo_platos.json`) en `.agent_knowledge/`.
- **`agents/creativo/knowledge/estacionalidad.json`**: calendario de temporada Cataluña.
- **`agents/creativo/knowledge/combinaciones_clasicas.csv`**: combinaciones clásicas (referencia).
- **System prompt del chef** (`agents/creativo/prompts/system_chef.md`) con personalidad mediterránea/catalana.
- **Integración con MiniMax API** (modo OpenAI-compatible): `MINIMAX_API_KEY`, `MINIMAX_BASE_URL`, `MINIMAX_MODEL` con defaults verificados (`https://api.minimax.io/v1`, `MiniMax-M3`).
- **`call_minimax()`**: cliente HTTP con `httpx`, timeout 60s, hasta 2 reintentos.
- **`check_estacionalidad()`**: detecta ingredientes fuera de temporada y los inyecta como contexto privado al chef.
- **`formatear_restaurante_para_chef()`**: inyecta las 15 dimensiones del restaurante al system prompt del chef.
- **`formatear_catalogo_para_chef()`**: inyecta hasta 30 platos del catálogo como contexto.

### 📦 Deploy
- Repositorio inicial: [`davidlopezg/restauranteai`](https://github.com/davidlopezg/restauranteai) (público).
- Validación end-to-end por David: ✅ (URL corregida de `api.minimax.chat` → `api.minimax.io`).
- API key operativa: ✅ (con salvaguarda "fija/no rotable" — ver `SECURITY.md`).

---

## Tipos de cambios

- `✨ Added` — funcionalidades nuevas.
- `🐛 Fixed` — correcciones de bugs.
- `🔒 Security` — fixes de seguridad o política.
- `📚 Changed` — cambios en funcionalidad existente.
- `⚠️ Deprecated` — funcionalidades que se van a quitar.
- `🗑️ Removed` — funcionalidades quitadas.
- `🧪 Tests` — agregados o correcciones de tests.
- `📦 Deploy` — deploys, infra, releases.
- `📝 Docs` — solo documentación.

[Unreleased]: https://github.com/davidlopezg/restauranteai/compare/v1.5.0...HEAD
[1.5.0]: https://github.com/davidlopezg/restauranteai/compare/v1.4.0...v1.5.0
[1.4.0]: https://github.com/davidlopezg/restauranteai/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/davidlopezg/restauranteai/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/davidlopezg/restauranteai/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/davidlopezg/restauranteai/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/davidlopezg/restauranteai/releases/tag/v1.0.0
