# Tasks — init-web

> **Change**: `init-web` · **Fase**: `sdd-tasks` · **Estado**: Listo para `sdd-apply`
> **Base**: [`design.md`](designs/init-web/design.md) (DD-1..DD-8) + [`spec.md`](specs/init-web/spec.md) (22 RFs + 11 CAs)

## Resumen

Implementar la pestaña "Configurar mi restaurante" en `app.py` con auth HF OAuth + helpers seguros en `agents/knowledge_context.py`. **3 PRs stacked** (cada uno < 400 líneas, self-verifica con su suite, mergea antes del siguiente).

| PR | Contenido | Push a | ΔLíneas |
|---|---|---|---|
| **PR 1** Backend helpers + tests | `agents/knowledge_context.py` (helpers de carga/guarda con guard + backup) + `scripts/test_init_web.py` (8 checks para helpers) | `origin` + `hf` | ~280 |
| **PR 2** UI web + auth | `app.py` (pestaña "Configurar" + handlers + auth integration) + frontmatter del README (HF OAuth) + SECURITY.md sección auth | `origin` + `hf` | ~410 |
| **PR 3** Docs + release | CHANGELOG.md + README.md update + docs/index.html update + VERSION bump + tag | `origin` (+ tag) | ~45 |

**Total**: ~735 líneas. Ligeramente arriba del budget inicial (700) por el PR 2 que es el más grande, pero dentro del rango aceptable.

---

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~735 (a través de 3 PRs) |
| 400-line budget risk | **Low per PR** (ninguno excede 400) |
| Chained PRs recommended | **Yes** (PR 1 → PR 2 → PR 3, merge en orden) |
| Delivery strategy | **stacked-to-main** (no fork PRs) |
| Chain strategy | Cada PR mergea a main antes del siguiente |

```text
Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: Low (per PR)
```

---

## Convenciones

- **Idioma de código**: castellano en strings de UI, snake_case en identificadores (consistente con el resto del repo).
- **Tests**: `scripts/test_init_web.py` con mini-helper `check()` estilo `scripts/test_app.py` y `scripts/test_seed_demo.py`. NO pytest (los tests de UI son integration-ligeros, no unit).
- **Commits**: conventional commits en inglés, UNO por unidad lógica. Ejemplos: `feat(init-web): helpers de carga con guard`, `feat(app): pestaña Configurar mi restaurante`, `docs(init-web): CHANGELOG v1.5.0`.
- **Push**: `git push hf main && git push origin main` para PRs que tocan `app.py`; `git push origin main` solo para docs.
- **Tags**: solo en PR 3 (release).
- **Sin tocar**: `requirements.txt`, `.gitignore`, firma de `responder()`, theme/css del constructor de Blocks, prompts del chef.

---

## PR 1 — Backend helpers + tests (~280 líneas)

**Objetivo**: agregar los helpers de carga/guarda segura en `agents/knowledge_context.py` + tests. NO toca UI. Self-verifica con `scripts/test_init_web.py`.

### Tareas (5)

- [x] **T1.1** — Agregar `cargar_restaurante_con_default(default=None) -> dict` en `agents/knowledge_context.py`. Devuelve `default` si no existe (en vez de raise). 6 líneas + docstring.
- [x] **T1.2** — Agregar `cargar_catalogo_con_default(default=None) -> list` (mismo patrón). 6 líneas + docstring.
- [x] **T1.3** — Agregar `guardar_con_backup(data, schema_doc=None, backup_dir=None) -> tuple[bool, str]`. Si el archivo existe, copia a `backups/<sesion_id>.json` antes de sobrescribir. Retorna `(success, message)`. 30 líneas + docstring.
- [x] **T1.4** — Agregar `guardar_catalogo_con_backup(platos, schema_doc=None, backup_dir=None) -> tuple[bool, str]`. Mismo patrón que T1.3. 30 líneas + docstring.
- [x] **T1.5** — Agregar `leer_con_backup_dir(backup_dir=None) -> list[Path]`. Lista los backups existentes. 10 líneas + docstring.

**ΔLíneas estimadas**: ~82 en `knowledge_context.py` + docstrings.

- [x] **T1.6** — Crear `scripts/test_init_web.py` con los 8 checks del design DD-7. Estilo mini-helper `check()` + `main() -> int`. **No** requiere Gradio instalado (los helpers son puros). ~150 líneas.

### Verificación de PR 1

```bash
# 1. Sintaxis
python -c "import ast; ast.parse(open('agents/knowledge_context.py').read())"

# 2. Tests del nuevo módulo
python scripts/test_init_web.py
# Esperado: 8/8 PASS

# 3. Regresión: no se rompió nada existente
python scripts/test_app.py   # → 6/6 PASS
python scripts/test_seed_demo.py  # → 5/5 PASS
python -m pytest tests/ -q  # → 132+ PASS

# 4. Sin regresión en CLI
python -m agents.init_phase --help  # → imprime ayuda sin error
```

### Commit y push de PR 1

```bash
git add agents/knowledge_context.py scripts/test_init_web.py
git commit -m "feat(init-web): helpers de carga/guarda con guard + backup

PR 1 del change init-web (Fase 2 producto vendible).

Helpers nuevos en agents/knowledge_context.py:
- cargar_restaurante_con_default(default=None)
- cargar_catalogo_con_default(default=None)
- guardar_con_backup(data, ...) — backup automático antes de sobrescribir
- guardar_catalogo_con_backup(platos, ...)
- leer_con_backup_dir(backup_dir=None)

Útiles para la UI web (PR 2): evita el bug F1 del explore.md donde
guardar_*() sobrescribe siempre. Ahora cada save con archivo previo
crea un backup en .agent_knowledge/backups/<sesion_id>.json.

Tests: scripts/test_init_web.py con 8 checks (mini-helper estilo
scripts/test_app.py, sin pytest, sin red, sin API).

Refs: design DD-5, explore.md F1."

git push hf main
git push origin main
```

### Riesgos residuales de PR 1

- **Ninguno crítico**. Los helpers son puros y testeados.

---

## PR 2 — UI web + auth (~410 líneas)

**Objetivo**: agregar la pestaña "Configurar mi restaurante" en `app.py` + integración de HF OAuth + sección en SECURITY.md. **Self-verifica**: abre el Space manualmente y verifica el flujo.

### Tareas (8)

- [x] **T2.1** — Crear `_render_init_web_tab() -> dict` en `app.py`. Define todos los componentes de la pestaña: disclaimer, accordion "Datos del restaurante" (con `_render_inputs_restaurante()` que itera `PREGUNTAS_RESTAURANTE`), accordion "Carta del restaurante" (con `_render_catalogo_editor()`), accordion "Acciones" (botones Guardar/Restaurar/Ver JSON), JSON viewer colapsable. ~150 líneas + helpers `_render_inputs_restaurante()`, `_render_catalogo_editor()`, `_handle_*()` para cada acción.

- [x] **T2.2** — Implementar handler `_handle_guardar(restaurante_dict, catalogo_list)` que:
- Valida tipos de los 15 dims
- Si ambos archivos NO existen → guarda directo (sin confirmación)
- Si alguno existe y es demo → confirma con `gr.Group` modal
- Si alguno existe y NO es demo → confirma con mensaje fuerte + sugerencia de descargar backup
- Retorna `(success, message)` para mostrar en toast.
~80 líneas.

- [x] **T2.3** — Implementar handler `_handle_restaurar_demo()` con checks (botón deshabilitado si no es demo, pero doble-check en backend). Re-seedea desde `agents/creativo/knowledge/demo_*.json`. ~30 líneas.

- [x] **T2.4** — Implementar handler `_handle_pegar_carta(carta_texto)` que llama a `_extraer_platos_de_carta()` (de `init_phase.py`) con feedback visual vía `gr.Progress`. ~40 líneas.

- [x] **T2.5** — Implementar `_render_catalogo_editor()` con paginación (25/pág) + búsqueda en vivo (filtra por nombre/categoría/descripcion). Estado en `gr.State`. ~50 líneas.

- [x] **T2.6** — Modificar la construcción del `gr.Blocks` en `app.py`: agregar `gr.Tabs(Chat, Configurar)` y usar `_render_init_web_tab()` para el contenido del segundo tab. ~30 líneas.

- [x] **T2.7** — Agregar `auth=("davidlopezgamero", os.getenv("CONFIG_PASSWORD"))` al `demo.launch()`. La auth es solo para la pestaña "Configurar"; el tab "Chat" sigue público (Gradio 6.19 soporta auth por-tab en gr.Tabs a partir de 6.x — verificar). Si no soporta auth por-tab, alternativa: la pestaña "Configurar" muestra un mensaje de "auth requerida" si no hay user/password en query string, y `os.getenv` lee de HF Secrets. ~10 líneas + 5 líneas de HF Secrets config.

- [x] **T2.8** — Agregar sección "## Autenticación (HF OAuth + auth básica)" en `docs/SECURITY.md` con explicación: HF OAuth nativo en Spaces para v1.1+, auth básica como fallback. Aclarar que el auth no protege secretos (estos están en HF Secrets), solo evita edición no deseada por terceros. ~15 líneas.

**ΔLíneas estimadas**: ~410 (250 en `app.py` + 150 en handlers + 15 en SECURITY.md).

### Verificación de PR 2

```bash
# 1. Sintaxis + AST parse
python -c "import ast; ast.parse(open('app.py').read())"

# 2. Regresión: invariantes de la UI intactas
python scripts/test_app.py   # → 6/6 PASS (firma de responder() intacta)

# 3. Regresión: tests previos siguen verdes
python scripts/test_seed_demo.py  # → 5/5 PASS
python -m pytest tests/ -q  # → 132+ PASS

# 4. Test del nuevo módulo
python scripts/test_init_web.py  # → 8/8 PASS

# 5. Smoke test de la UI (manual en local)
python app.py
# → debe abrir en localhost:7860 sin error
# → el tab "Configurar" debe pedir auth
# → con auth correcta, debe precargar el restaurante demo
# → editar un input y "Guardar" → mensaje de éxito o modal de confirmación

# 6. Smoke test en HF Space (después del push)
# → https://huggingface.co/spaces/davidlopezgamero/RestaurantEAI
# → verificar que el tab "Configurar" carga con el perfil demo
```

### Commit y push de PR 2

```bash
git add app.py docs/SECURITY.md
git commit -m "feat(app): pestaña 'Configurar mi restaurante' + auth

PR 2 del change init-web.

Nuevo en app.py:
- _render_init_web_tab(): construye la pestaña completa
- _render_inputs_restaurante(): data-driven desde PREGUNTAS_RESTAURANTE
- _render_catalogo_editor(): con paginación a 25 + búsqueda en vivo
- _handle_guardar(): con confirmación obligatoria si archivo existe
- _handle_restaurar_demo(): re-seedea desde demo_*.json
- _handle_pegar_carta(): llama a _extraer_platos_de_carta() con
  feedback visual
- gr.Tabs(Chat, Configurar) en la UI

Auth: auth=(user, password) en .launch() — user y password leídos de
HF Secrets en producción. SECURITY.md documenta el modelo.

Sin cambios en: firma de responder(), theme/css del constructor de
Blocks, prompts del chef, agents/init_phase.py.

Refs: design DD-2..DD-6, spec RF-1..RF-26."

git push hf main
git push origin main
```

### Riesgos residuales de PR 2

- **D2 (auth HF OAuth)**: si HF OAuth nativo no funciona en el Space free, fallback a `auth=(user, password)` con creds en HF Secrets. Documentado en SECURITY.md.
- **D3 (state de la UI)**: `gr.State` con persistencia de sesión (built-in en Gradio 6.19). Verificar manualmente.
- **D4 (extracción de carta lenta)**: `gr.Progress` para feedback. Si tarda >30s, considerar timeout.

---

## PR 3 — Docs + release (~45 líneas)

**Objetivo**: update de CHANGELOG, README, landing, bump de VERSION, tag `v1.5.0`.

### Tareas (6)

- [x] **T3.1** — Agregar entrada v1.5.0 en `CHANGELOG.md` con resumen (tabla de Added/Changed/Fixed), enlaces a los PRs, fecha 2026-09-XX. ~28 líneas.

- [x] **T3.2** — Update `README.md`:
- Marcar `init-web` (Fase 2) como ✅ en la tabla de estado.
- Mover de "🚧 En curso" a "✅ Ya shipped" en la sección Roadmap.
- ~8 líneas.

- [x] **T3.3** — Update `docs/index.html`:
- Sección "Oferta open core" ajustada: "configuración inicial de tu restaurante en el navegador" (cuando init-web esté live).
- ~8 líneas.

- [x] **T3.4** — Bump `VERSION` v1.4.0 → v1.5.0. 1 línea.

- [x] **T3.5** — Commit + push a `origin` (no `hf`, son solo docs + VERSION). Tag `v1.5.0`. ~5 líneas de bash.

- [x] **T3.6** — Crear GitHub Release desde el tag `v1.5.0`. Notas del release generadas desde CHANGELOG (auto-generadas). Manual en GitHub UI.

**ΔLíneas estimadas**: ~45.

### Verificación de PR 3

```bash
# 1. Render de la landing
# → https://davidlopezg.github.io/restauranteai/ (post-push, esperar 30s)

# 2. Confirmación del tag
git tag -l "v1.5.0"  # → debe listar v1.5.0
git show v1.5.0 --stat  # → debe mostrar los archivos bumppeados

# 3. Smoke test final del Space
# → https://huggingface.co/spaces/davidlopezgamero/RestaurantEAI
# → verificar que TODO funciona end-to-end
```

### Commit y push de PR 3

```bash
git add CHANGELOG.md README.md docs/index.html VERSION
git commit -m "chore(release): v1.5.0 — pestaña Configurar mi restaurante

PR 3 (release) del change init-web.

- CHANGELOG: entrada v1.5.0 con Added/Changed/Fixed + links a PRs
- README: estado del proyecto actualizado, init-web en shipped
- docs/index.html: oferta open core ajustada con 'configuración inicial
  en tu navegador' como entregable explícito
- VERSION: v1.4.0 → v1.5.0

Refs: spec CA-11, design DD-1."

git push origin main
git tag -a v1.5.0 -m "v1.5.0 — init-web: Configurar mi restaurante"
git push origin v1.5.0
```

Manual en GitHub: Releases → Draft a new release → tag `v1.5.0` → publicar con notas del CHANGELOG.

---

## Criterios globales de cierre del change

- [ ] PR 1 merged a main.
- [ ] PR 2 merged a main.
- [ ] PR 3 merged a main.
- [ ] Tag `v1.5.0` pusheado a `origin`.
- [ ] GitHub Release `v1.5.0` publicado.
- [ ] HF Space corriendo con la nueva pestaña.
- [ ] GitHub Pages sirviendo la landing actualizada.
- [ ] `python scripts/test_app.py` → 6/6.
- [ ] `python scripts/test_seed_demo.py` → 5/5.
- [ ] `python scripts/test_init_web.py` → 8/8.
- [ ] `python -m pytest tests/ -q` → 132+ verde.
- [ ] Las 6 preguntas del proposal cerradas y reflejadas en spec/proposal.
- [ ] `openspec/changes/init-web/` con explore, proposal, spec, design, tasks, apply-progress, verify-report.

## Siguientes pasos

1. ✅ Explore, proposal, spec, design, tasks completos.
2. → **Apply** (`sdd-apply`): ejecutar PR 1 → PR 2 → PR 3 secuencialmente.
3. → **Verify** (`sdd-verify`): correr las 3 suites, validar CAs 1-11.
4. → **Sync** (`sdd-sync`): push a `hf` + `origin`, bump VERSION.
5. → **Archive** (`sdd-archive`): copiar artifacts a `openspec/specs/init-web/`, mantener `openspec/changes/init-web/` como histórico.
