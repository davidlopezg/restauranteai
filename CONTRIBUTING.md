# 🤝 Contribuir a RestaurantEAI

> Gracias por tu interés en mejorar el Chef Creativo. Esta guía te ayuda a arrancar en 5 minutos y a evitar los errores más comunes.

## 📜 Código de conducta

Este proyecto adhiere al [Contributor Covenant v2.1](CODE_OF_CONDUCT.md). Al participar, esperás y promovés un ambiente respetuoso.

## 🧭 Maneras de contribuir

- 🐛 **Reportar bugs** → [`bug_report.yml`](.github/ISSUE_TEMPLATE/bug_report.yml)
- 💡 **Proponer features** → [`feature_request.yml`](.github/ISSUE_TEMPLATE/feature_request.yml)
- ❓ **Hacer preguntas** → [`question.yml`](.github/ISSUE_TEMPLATE/question.yml)
- 🔧 **Abrir PRs** → revisá la [plantilla](.github/PULL_REQUEST_TEMPLATE.md)
- 📖 **Mejorar docs** → issues etiquetados `docs` son bienvenidos sin coordinación previa
- 🌐 **Traducir la landing** → `docs/index.html` ya es trilingüe (es · ca · en); PRs a otros idiomas se aceptan si están completos

---

## 🛠️ Setup local (5 minutos)

### Requisitos
- **Python 3.11** (obligatorio — HF Space default 3.13 rompe Gradio; ver [memory 2026-08-05](memory/memory.md))
- Git
- Una API key de **MiniMax** (gratis para empezar)

### Pasos

```bash
# 1. Clonar
git clone https://github.com/davidlopezg/restauranteai.git
cd restauranteai

# 2. Crear entorno virtual
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Instalar deps
pip install -r requirements.txt

# 4. Configurar credenciales
cp .env.example .env
nano .env   # pegar tu MINIMAX_API_KEY

# 5. Validar estructura SIN consumir API
python scripts/probar_estructura.py

# 6. Correr la app local
python app.py
# → http://localhost:7860
```

> 💡 Si `python scripts/probar_estructura.py` muestra todo ✅, tu setup está OK.

### Setup alternativo (solo CLI, sin UI web)

```bash
python -m agents.init_phase       # 15 preguntas + carta
python -m agents.creativo.agent   # chat interactivo
```

---

## ✅ Tests

Hay tres suites. Todas deben pasar antes de abrir un PR.

### 1. Tests de regresión de la app (`scripts/test_app.py`)

```bash
python scripts/test_app.py
```

Valida sintaxis de `app.py`, kwargs prohibidos de Gradio 6+, firma de `responder()`, theme/css en `.launch()`. **6/6 checks.**

### 2. Tests del seed demo (`scripts/test_seed_demo.py`)

```bash
python scripts/test_seed_demo.py
```

Valida que los JSON demo cumplen el schema y que `_seed_demo_profile()` no sobrescribe perfiles reales. **5/5 checks.**

### 3. Tests pytest (módulo de memoria + regresión de skills + chat)

```bash
python -m pytest tests/ -q
```

**132+ tests** (storage, formatters, commands, duplicates, counter, RGPD, concurrencia WAL, regresión skills, skill chat).

---

## 🚫 Reglas duras (invariantes del proyecto)

Estas reglas **no se rompen** salvo acuerdo explícito del maintainer en un issue. Si tu PR las viola, va a ser rechazada o se te va a pedir revertir.

### 1. ❌ Sin datos reales en superficies públicas

Regla operativa desde 2026-07-02 ([memory](memory/memory.md)). Se aplica a:

- Código (`app.py`, prompts, ejemplos, fixtures de test).
- Documentación pública (`README.md`, `docs/index.html`).
- Commits, issues, PRs (sin logs con datos de clientes reales).
- El Space HF público (solo perfil `demo: true`).

**Cómo cumplirlo:**
- Usa los JSON demo de `agents/creativo/knowledge/demo_*.json` como base para ejemplos.
- Si necesitás un dato de un restaurante ficticio, **inventá uno** (ej: "Restaurante La Higuera" — no usar nombres de restaurantes reales ni de Sol de Nit).
- Para tests, usá `tmp_path` o bases SQLite en memoria.

### 2. ❌ Sin API keys ni secrets en el repo

- `.env` está en `.gitignore` — no lo commitees nunca.
- Si ves un log con tu key, **rotala** antes de commitear (en este proyecto la key es fija/no rotable — ver `SECURITY.md`).
- Los `.env.example` solo tienen placeholders literales (`sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`), nunca keys reales.

### 3. ❌ No tocar `requirements.txt` ni `.gitignore` sin discutir

`requirements.txt` está pineado a un combo verificado ([memory 2026-08-05 D5](memory/memory.md)):

```
gradio>=6.19,<7.0
huggingface_hub>=1.2,<2.0
python_version: '3.11'  (en el frontmatter del README)
```

Cualquier cambio de versión debe pasar por un issue previo.

### 4. ❌ No cambiar la firma de `responder()` ni romper `test_app.py`

`scripts/test_app.py` valida invariantes de la UI Gradio 6+. Si necesitás agregar un parámetro, **actualizá el test en el mismo commit**.

### 5. ❌ No pushear `openspec/` ni `.pi-subagents/` ni `.pi/` a `hf`

Push a `hf` solo va al Space (lo que afecta a `app.py` y código que corre allá). Los artefactos de desarrollo (specs, memoria de subagents) se quedan en `origin` (GitHub) o local.

> Recordatorio: `git pushall` (alias) = `git push hf main && git push origin main`. Usalo solo cuando TODO el commit deba ir a ambos remotes. Si no, `git push origin main` para docs, `git push hf main` para código.

---

## 📐 Estilo de código

### Python
- PEP 8 + type hints en funciones públicas.
- Docstrings en formato Google o NumPy (consistente con el código existente).
- Imports ordenados: stdlib, terceros, locales.
- Línea máxima: 100 caracteres (tolerancia: 110).

### Commits
- [Conventional Commits](https://www.conventionalcommits.org/) en **inglés**:
  - `feat(creativo): nueva skill de maridaje`
  - `fix(app): corregir seed no-TTY cuando solo falta un archivo`
  - `docs(readme): agregar sección de quick start`
  - `chore(deps): bump gradio a 6.20`
  - `test(memoria): cubrir /olvidar todo con confirmación`
- Un commit por unidad lógica. Si tu feature tiene 5 archivos y 300 líneas, idealmente son 2-3 commits.
- Mensaje en imperativo presente ("agregar", no "agregado" ni "agregamos").

### Idioma en código y copy
- Identificadores y nombres de skill: inglés o `snake_case` consistente.
- Strings visibles al usuario: **castellano neutro peninsular** (decisión 10 del proposal `producto-vendible`).
- La landing `docs/index.html` es trilingüe; cualquier cambio de copy debe actualizar las 3 versiones.

---

## 🧩 Cómo extender el sistema

### Agregar una skill nueva al Chef Creativo

1. Crear el system prompt: `agents/creativo/prompts/system_<nombre>.md`.
2. Agregar el dict en la lista `SKILLS` de [`agents/creativo/skills.py`](agents/creativo/skills.py).
3. Si la skill necesita comportamiento custom (state machine, comandos, parser), implementar el handler y conectarlo en `agents/creativo/agent.py` y `app.py`.
4. Actualizar el `description` del ChatInterface y la landing `docs/index.html` para reflejar la nueva skill.
5. Agregar tests de regresión en `tests/`.
6. Actualizar `README.md` (sección "Skills disponibles") y `docs/COMMANDS.md`.

### Agregar una pregunta al init

1. Agregar el dict en `agents/init_options.json` bajo `"options"`.
2. **No tocar** `agents/init_phase.py` — el JSON es la fuente de verdad y el código hace fallback a las opciones hardcoded solo si la key no está en el JSON.
3. Verificar que el formatter (`formatear_restaurante_para_chef` en `agents/creativo/agent.py`) sepa mapear el nuevo valor (si es `choice`/`multichoice`).

### Agregar un método creativo nuevo

1. Agregar el string a `METODOS_CREATIVOS` en `agents/creativo/agent.py`.
2. Documentarlo en `docs/metodos-creativos.md` si es原创 (原创 =原创).
3. El chef lo usará como lente creativo en `ideas_creativas` y `proceso_creativo` automáticamente.

### Agregar un comando al Archivo de Ideas

1. Editar `agents/memoria/commands.py` (parsing regex + handler).
2. Agregar tests en `tests/test_memoria_commands.py`.
3. Documentar en `_AYUDA_TEXTO` (visible al usuario con `/ayuda`) y en el README.

---

## 🧪 Patrón SDD (Spec-Driven Development)

Cambios grandes (>400 líneas) siguen el flujo SDD documentado en `openspec/`:

```
explore → proposal → spec → design → tasks → apply → verify → sync → archive
```

Cada fase produce un artefacto en `openspec/changes/<nombre>/`. Si tu feature excede el budget de revisión, **abrí un proposal primero** en lugar de un PR directo.

---

## 📬 Contacto

- Issues y PRs: en este repo.
- Email: davidlopezgamero@gmail.com (solo para temas privados: seguridad, colaboraciones grandes, prensa).
- HF Space: [RestaurantEAI](https://huggingface.co/spaces/davidlopezgamero/RestaurantEAI).
- Landing: [davidlopezg.github.io/restauranteai](https://davidlopezg.github.io/restauranteai/).

---

## 🙏 Reconocimientos

Gracias a todos los que ayudaron con código, issues, feedback y difusión. El proyecto se construye una idea, un commit y una conversación a la vez.

— David López Gamero (maintainer)
