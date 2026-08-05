# Design — producto-vendible

> **Change**: `producto-vendible`
> **Phase**: `sdd-design`
> **Status**: 🟢 Escrito — listo para `sdd-tasks`
> **Creado**: 2026-08-05
> **Dominio**: `producto-vendible`
> **Base**: `proposal.md` → `spec.md` (decisiones lockeadas 1-14, RF-1..RF-21, CA-1..CA-11)
> **Nota de proceso**: la fase fue delegada a `sdd-design` dos veces y el subagente crasheó (grep no disponible + OOM del runtime) sin persistir. El orquestador completó el design con evidencia verificada de primera mano (workaround documentado en `memory/memory.md` para fases que no persisten).

---

## 1. Decisiones de diseño

| # | Decisión | Opción elegida | Alternativas rechazadas |
|---|---|---|---|
| DD-1 | **Visual de demo (R7)** | **Screenshot estático commiteado** en `docs/assets/demo-ficha.png` como vía principal; iframe NO recomendado. | iframe del Space: Gradio 6 Spaces se sirven con `X-Frame-Options`/CSP que bloquean embedding de terceros en la mayoría de configs; además el cold start del free tier degrada la UX del embed. El screenshot es 100% estable, no depende del Space y funciona offline. |
| DD-2 | **Arquitectura i18n de la landing** | **Un solo skeleton HTML + diccionario JS por idioma** (`LANG` object + atributos `data-i18n`). | Tres bloques paralelos por idioma: duplica el HTML (~3× tamaño), rompe el mantenimiento y el budget de 400 líneas. |
| DD-3 | **Componente indicador de perfil** | `gr.Markdown` dentro de `with gr.Blocks()`, antes del ChatInterface, renderizado en el flujo `__main__` con helper `_estado_perfil()`. | Componentes custom/HTML: más riesgo. No toca `theme=`/`css=` (invariante `test_kwarg_prohibidos`), no cambia firma de `responder()`. |
| DD-4 | **Seed demo: archivos trackeados** | 2 JSON en `agents/creativo/knowledge/` (fuera de `.agent_knowledge/`), copiados a boot no-TTY vía helper `_seed_demo_profile()`. | Generar por código en boot: menos editable, rompe patrón `init_options.json` (JSON editable sin tocar código). Commitear dentro de `.agent_knowledge/`: viola `.gitignore` y la regla template→instancia. |
| DD-5 | **Valores del seed** | Perfil mediterráneo moderno, ticket medio (25-60-40), `sofisticacion: media`, `demo: true`, nombre "Restaurante de demostración". Todos los valores validados contra `agents/init_options.json` (ver §3). | Cualquier valor inventado fuera de los sets válidos: rompería los mapeos de `formatear_restaurante_para_chef` (que usa `mapping.get(v, v)` — valores custom pasan crudos, degradando el contexto). |
| DD-6 | **Slicing de review** | 3 commits en orden: (1) seed demo + helper + test, (2) indicador + description + link, (3) landing trilingüe + assets. | Un solo commit gigante: rompe el budget de 400 líneas y la revisión. Cada commit es revertible por separado. |
| DD-7 | **Catálogo demo** | 10 platos mediterráneos de ticket medio (2 entrantes, 3 principales, 2 postres, 1 guarnición, 2 "otro"), precios 8-28€, categorías del set válido. | Catálogo vacío o de 3-4 platos: empobrece el contexto del chef y la demo de "ideas" no tiene base. |
| DD-8 | **Deploy** | Push 1 y 2 a `origin` + `hf`; push 3 (landing) solo a `origin`. `openspec/` nunca a `hf`. | — |

---

## 2. Arquitectura general

```
┌──────────────────────────────────────────────────────────────┐
│  docs/index.html  (landing trilingüe, single-file, zero-deps) │
│  · skeleton HTML + LANG{es,ca,en} + selector header           │
│  · secciones: hero, problema, skills, demo, oferta, faq, foot │
│  · assets/ demo-ficha.png (+ proceso-creativo.png, ideas.png) │
└──────────────────────────────┬───────────────────────────────┘
                               │ GitHub Pages (origin/main, /docs)
┌──────────────────────────────▼───────────────────────────────┐
│  app.py (Gradio 6.19, HF Space)                               │
│  __main__: bootstrap_necesario()                              │
│    ├─ TTY      → fase_init_interactiva() (intacto)            │
│    └─ no-TTY   → _seed_demo_profile()  ← RF-13                │
│  UI: gr.Markdown (indicador perfil) + ChatInterface           │
│       + description venta + link landing                      │
└──────────────────────────────┬───────────────────────────────┘
                               │ lee/copia
┌──────────────────────────────▼───────────────────────────────┐
│  agents/creativo/knowledge/                                   │
│  · demo_restaurante.json (trackeado, demo:true)               │
│  · demo_catalogo_platos.json (trackeado, 10 platos)           │
└──────────────────────────────────────────────────────────────┘
```

**Principio rector**: el perfil demo vive como **conocimiento estático del agente** (`agents/creativo/knowledge/` — misma carpeta que `estacionalidad.json`), NO en `.agent_knowledge/` (conocimiento dinámico del restaurante, gitignored). En boot no-TTY se copia a `.agent_knowledge/` para que todos los consumidores existentes (`load_restaurante()`, `formatear_restaurante_para_chef()`, `load_catalogo()`) funcionen sin cambios.

---

## 3. Seed demo (D1) — diseño detallado

### 3.1 Archivo `agents/creativo/knowledge/demo_restaurante.json`

Contenido exacto (valores 100% del set válido de `agents/init_options.json`):

```json
{
  "demo": true,
  "nombre": "Restaurante de demostración",
  "precio_target_min": 25,
  "precio_target_max": 60,
  "precio_target_moda": 40,
  "sofisticacion": "media",
  "productos_dominantes": ["vegetales", "pescado", "mariscos", "fruta"],
  "tecnicas_dominantes": ["plancha", "brasas", "vapor", "fermentacion"],
  "tipo_servicio": ["servicio_tradicional", "picoteo_terraza"],
  "grupos": "con_grupos_pequenos",
  "clases_comedores": ["sociales_familia", "mixto", "turistas"],
  "origen_inspiracion": "mediterraneo",
  "orientacion_nutricional": ["temporada", "km0"],
  "localizacion": "litoral_mar",
  "religion": ["ninguna"],
  "tiempo_preparacion": "medio",
  "epoca_estilo": ["mediterranea_moderna", "casual_mediterraneo"]
}
```

Validación de cada valor contra `init_options.json`:
- `sofisticacion: "media"` ✓ (choice: muy_alta..muy_baja)
- `productos_dominantes` ✓ (vegetales, pescado, mariscos, fruta ∈ multichoice)
- `tecnicas_dominantes` ✓ (plancha, brasas, vapor, fermentacion ∈ multichoice)
- `tipo_servicio` ✓ (servicio_tradicional, picoteo_terraza ∈ multichoice)
- `grupos: "con_grupos_pequenos"` ✓ (choice)
- `clases_comedores` ✓ (sociales_familia, mixto, turistas ∈ multichoice)
- `origen_inspiracion: "mediterraneo"` ✓ (choice)
- `orientacion_nutricional` ✓ (temporada, km0 ∈ multichoice)
- `localizacion: "litoral_mar"` ✓ (choice)
- `religion: ["ninguna"]` ✓ (multichoice)
- `tiempo_preparacion: "medio"` ✓ (choice)
- `epoca_estilo` ✓ (mediterranea_moderna, casual_mediterraneo ∈ multichoice)
- `nombre` y `demo` son keys adicionales toleradas (el formatter usa `.get("nombre")` y el indicador usa `demo`); las 15 dimensiones del schema están completas.

### 3.2 Archivo `agents/creativo/knowledge/demo_catalogo_platos.json`

10 platos mediterráneos de ticket medio (categorías del set válido: entrante/principal/postre/guarnicion/bebida/otro):

```json
[
  {"nombre": "Tomate de ramallet con ventresca", "categoria": "entrante", "descripcion": "Tomate de ramallet aliñado con aceite de oliva virgen extra y ventresca de bonito.", "precio": 14},
  {"nombre": "Coca de trampó con anchoa", "categoria": "entrante", "descripcion": "Coca fina con pimiento, tomate y cebolla, anchoa del Cantábrico.", "precio": 12},
  {"nombre": "Arroz de montaña con setas", "categoria": "principal", "descripcion": "Arroz meloso con setas de temporada y hierbas del bosque.", "precio": 22},
  {"nombre": "Lubina a la brasa con verduras", "categoria": "principal", "descripcion": "Lubina salvaje a la brasa con verduras de temporada asadas.", "precio": 26},
  {"nombre": "Secreto ibérico con peras", "categoria": "principal", "descripcion": "Secreto de cerdo ibérico con peras al vino tinto y puré de patata.", "precio": 21},
  {"nombre": "Escalivada con queso fresco", "categoria": "guarnicion", "descripcion": "Escalivada de berenjena, pimiento y cebolla con queso fresco.", "precio": 9},
  {"nombre": "Crema catalana", "categoria": "postre", "descripcion": "Crema catalana tradicional con costra de azúcar caramelizada.", "precio": 7},
  {"nombre": "Tarta de almendra", "categoria": "postre", "descripcion": "Tarta de almendra con helado de vainilla.", "precio": 8},
  {"nombre": "Pan con tomate y aceite", "categoria": "otro", "descripcion": "Pan de payés con tomate, aceite de oliva y sal.", "precio": 5},
  {"nombre": "Ensalada de la casa", "categoria": "otro", "descripcion": "Mezclum, tomate, atún, huevo y aceitunas.", "precio": 13}
]
```

### 3.3 Helper en `app.py`

```python
# ── Seed demo (Fase 1 — producto-vendible) ──────────────────────────────
def _estado_perfil() -> str:
    """Devuelve el texto del indicador de perfil según restaurante.json."""
    try:
        restaurante = load_restaurante()
    except FileNotFoundError:
        return "*(sin contexto de restaurante)*"
    nombre = (restaurante.get("nombre") or "").strip()
    if restaurante.get("demo"):
        return f"🧪 **Demo**: {nombre or 'Restaurante de demostración'} — perfil de ejemplo precargado."
    if nombre:
        return f"🍽️ **Perfil activo**: {nombre}"
    return "*(sin contexto de restaurante)*"


def _seed_demo_profile() -> None:
    """Boot no-TTY: copia el perfil demo a .agent_knowledge/ si falta (idempotente)."""
    from agents.init_phase import _schema_doc_restaurante, _schema_doc_catalogo
    from agents.knowledge_context import guardar_restaurante, guardar_catalogo

    demo_dir = Path(__file__).resolve().parent / "agents" / "creativo" / "knowledge"
    demo_rest = json.loads((demo_dir / "demo_restaurante.json").read_text(encoding="utf-8"))
    demo_cat = json.loads((demo_dir / "demo_catalogo_platos.json").read_text(encoding="utf-8"))
    guardar_restaurante(demo_rest, _schema_doc_restaurante())
    guardar_catalogo(demo_cat, _schema_doc_catalogo())
    logger.info("Perfil demo genérico seedeado (no-TTY boot).")
```

> Nota: `json` ya se importa en el bloque `__main__` vía `agents.knowledge_context`; el helper agrega su propio `import json` local si hace falta (el archivo `app.py` no importa `json` al tope — verificar en apply y agregar si es necesario).

### 3.4 Reemplazo del bloque `__main__` no-TTY

```python
if bootstrap_necesario():
    if sys.stdin.isatty():
        from agents.init_phase import fase_init_interactiva
        fase_init_interactiva()
    else:
        # HF Space o CI: sin TTY. Seed de perfil demo genérico (RF-13).
        _seed_demo_profile()
```

(invariante: `guardar_*` escribe SOLO si los archivos no existen; en HF el filesystem es efímero así que el reseed ocurre en cada boot — idempotente por diseño.)

---

## 4. Indicador de perfil + description + link (D3)

### 4.1 Indicador

Dentro de `with gr.Blocks() as demo:`, ANTES del `gr.ChatInterface`:

```python
with gr.Blocks() as demo:
    perfil_md = gr.Markdown(_estado_perfil())
    skill_selector = gr.Radio(...)   # sin cambios
    gr.ChatInterface(...)            # sin cambios
```

- No toca `theme=`/`css=` del constructor (invariante `test_kwarg_prohibidos`).
- No cambia la firma de `responder()` (invariante `test_firma_responder`).
- `_estado_perfil()` se llama al construir la UI → se evalúa con los archivos ya seedeados (el seed corre antes en `__main__`).

### 4.2 Description alineado a venta

```python
description=(
    "Generador de fichas culinarias con IA. Elige un modo y prueba con la demo "
    "(restaurante mediterráneo de ejemplo) o pide algo a tu medida. "
    "Modos: Ficha técnica · Proceso creativo · Ideas creativas · Chat con el chef."
),
```

> Nota de idioma (decisión 10): el Space es una superficie pública → castellano **neutro peninsular** (no voseo), consistente con la landing.

### 4.3 Link a la landing

```python
# En el Markdown del indicador o un segundo gr.Markdown:
"  ·  [🌐 Volver a la web](https://davidlopezg.github.io/restauranteai/)"
```

---

## 5. Landing trilingüe (D2) — diseño detallado

### 5.1 Estructura del archivo `docs/index.html`

```
<head>
  <meta charset / viewport>
  <title data-i18n="title"> (default castellano)
  <meta name=description data-i18n="meta_desc">
  <style> (CSS vanilla, zero-deps, paleta mediterránea: #1a1714 texto, #c44d34 acento, crema #faf7f2)</style>
</head>
<body>
  <header> logo/emoji 🍂 + selector idioma (3 botones: ES | CA | EN) </header>
  <main>
    <section id="hero">        h1 + subtitle + CTA demo + CTA oferta </section>
    <section id="problema">    dolor del hostelero → solución </section>
    <section id="skills">      4 cards (ficha, proceso_creativo, ideas_creativas, chat) </section>
    <section id="demo">        screenshot(s) + texto "perfil genérico" + link al Space </section>
    <section id="oferta">      "El software es gratis (MIT). La implementación se paga." + mailto CTA </section>
    <section id="faq">         accordion 4-6 preguntas </section>
  </main>
  <footer> GitHub · HF Space · MIT · "construido por un hostelero real" </footer>
  <script> LANG = { es: {...}, ca: {...}, en: {...} }; i18n init + selector listener </script>
</body>
```

### 5.2 Patrón i18n (JS vanilla)

```html
<!-- Cada elemento traducible lleva data-i18n -->
<h1 data-i18n="hero_title">El chef que piensa la carta contigo</h1>
<p data-i18n="hero_subtitle">...</p>
<a class="btn" data-i18n-href="cta_demo" href="https://huggingface.co/spaces/davidlopezgamero/RestaurantEAI">Probar la demo</a>

<script>
const LANG = {
  es: {
    hero_title: "El chef que piensa la carta contigo",
    hero_subtitle: "...",
    cta_demo: "Probar la demo",
    // ... todas las claves
  },
  ca: { hero_title: "El xef que pensa la carta amb tu", /* ... */ },
  en: { hero_title: "The chef who thinks the menu with you", /* ... */ },
};

function aplicar_idioma(lang) {
  const d = LANG[lang] || LANG.es;
  document.documentElement.lang = lang;
  document.title = d.title;
  document.querySelector('meta[name="description"]').content = d.meta_desc;
  document.querySelectorAll("[data-i18n]").forEach(el => {
    const k = el.getAttribute("data-i18n");
    if (d[k] !== undefined) el.textContent = d[k];
  });
  document.querySelectorAll("[data-i18n-href]").forEach(el => {
    const k = el.getAttribute("data-i18n-href");
    if (d[k] !== undefined) el.href = d[k];
  });
  localStorage.setItem("lang", lang);
}
// init: localStorage > navigator.language (ca/es/en) > "es"
</script>
```

### 5.3 Subjects de mailto por idioma

```html
<a class="btn" data-i18n-href="cta_oferta" href="mailto:davidlopezgamero@gmail.com?subject=Quiero%20el%20Chef%20Creativo%20en%20mi%20restaurante">
  Implementar en mi restaurante
</a>
```

- es: `Quiero el Chef Creativo en mi restaurante`
- ca: `Vull el Chef Creativo al meu restaurant`
- en: `I want Chef Creativo in my restaurant`
(URL-encoded en el href; editable en el diccionario.)

### 5.4 Screenshots (assets)

- `docs/assets/demo-ficha.png` — captura del modo Ficha con el perfil demo (obligatorio, RF-5/CA-6).
- `docs/assets/demo-proceso-creativo.png`, `docs/assets/demo-ideas.png` — opcionales si el budget lo permite (decisión Q3: 2-3 capturas).
- Generación: manual (navegador → screenshot) o con playwright si está disponible en apply; commiteado al repo. **El entorno de apply probablemente no tiene playwright** → plan A: generar capturas localmente y commitearlas; si no es posible, la landing usa una sola captura o una celda de ejemplo renderizada en HTML puro (fallback documentado, CA-6 requiere visual).

---

## 6. Test del seed (RF-15)

Nuevo archivo `scripts/test_seed_demo.py` (mismo estilo mini-helper que `test_app.py`):

```python
"""test_seed_demo.py — valida el seed demo del perfil genérico (Fase 1)."""
# Checks:
# 1. demo_restaurante.json parsea y tiene las 15 claves del schema
# 2. demo_restaurante.json["demo"] is True y nombre no vacío
# 3. cada valor choice/multichoice ∈ set válido de agents/init_options.json
#    (carga init_options.json y compara contra options.<key>.values)
# 4. demo_catalogo_platos.json: 8-12 platos, cada uno con nombre/categoria/
#    descripcion/precio y categoria ∈ set válido
# 5. _seed_demo_profile() no sobrescribe archivos existentes:
#    (a) guardar en temp dir → (b) llamar de nuevo → (c) contenido intacto
#    (usa monkeypatch de agents.knowledge_context.KNOWLEDGE_DIR o
#     copia a un dir temporal vía monkeypatch de RESTAURANTE_PATH/CATALOGO_PATH)
```

- `scripts/test_app.py`: **no requiere cambios** — ninguno de los invariantes se toca. (Opcional, si el budget lo permite: un check nuevo de que `_estado_perfil` existe; NO obligatorio.)
- Correr: `python scripts/test_seed_demo.py` + `python scripts/test_app.py` + `python -m pytest tests/ -q` (120 tests memoria).

---

## 7. Mapa de archivos y presupuesto de líneas

| Archivo | Acción | Naturaleza | Líneas est. |
|---|---|---|---|
| `agents/creativo/knowledge/demo_restaurante.json` | crear | datos (seed) | ~25 |
| `agents/creativo/knowledge/demo_catalogo_platos.json` | crear | datos (seed) | ~35 |
| `app.py` | modificar | `_estado_perfil()`, `_seed_demo_profile()`, `__main__` no-TTY, indicador, description, link | ~+60 |
| `scripts/test_seed_demo.py` | crear | tests | ~80 |
| `docs/index.html` | reescribir | landing trilingüe | ~450-600 (el archivo completo) |
| `docs/assets/demo-ficha.png` (+2 opcionales) | crear | assets | binario |
| `memory/memory.md` | modificar | D5 docs deps | ~+15 |
| `README.md` | modificar (SHOULD) | drift 3→4 skills | ~+3 |

**Budget review**: la landing sola (450-600 líneas) **excede** el budget de 400 líneas de un solo diff. → **Slicing obligatorio** (DD-6): la landing es el commit 3, separado de seed+app (commit 1-2). El reviewer ve 3 diffs acotados en vez de uno gigante. Si aún así se quiere un PR único, se documenta como excepción con el riesgo de review workload explícito.

---

## 8. Plan de slicing para review (DD-6 / DD-8)

| Commit | Contenido | Test a correr | Push |
|---|---|---|---|
| **C1** | seed JSONs + `_seed_demo_profile()` + `__main__` no-TTY | `python scripts/test_seed_demo.py` | `origin` + `hf` |
| **C2** | indicador `_estado_perfil()` + `gr.Markdown` + description + link | `python scripts/test_app.py` | `origin` + `hf` |
| **C3** | `docs/index.html` trilingüe + `docs/assets/` | grep checks CA-1..CA-6 (sin "MVP-0.5", mailto, 4 skills, sin Sol de Nit) | `origin` solo |
| **C4** | `memory/memory.md` (D5) + `README.md` drift (si entra) | — | `origin` |
| **C5** (deploy) | bump `VERSION` v1.3.0 → v1.4.0 + tag (si David lo aprueba en apply) | — | `origin` + tag |

Reglas:
- `openspec/` **nunca** a `hf` (riesgo R10).
- Tras merge de C1-C3 → push `origin` (Pages live al instante) + `hf` (Space) en el mismo comando `git pushall` (C1-C2; C3 solo origin).
- Rollback: `git revert` por commit, independiente.

---

## 9. Riesgos técnicos de implementación

| # | Riesgo | Mitigación |
|---|---|---|
| T1 | `app.py` no importa `json` al tope (verificar en apply) | Agregar `import json` local en `_seed_demo_profile()` o al tope — decision trivial en apply. |
| T2 | Screenshot no generable en entorno de apply | Plan A: local + commit; fallback: celda de ejemplo renderizada en HTML puro (CA-6 "visual" se cumple con la celda; el screenshot queda como mejora). |
| T3 | Landing > budget 400 | Slicing C1-C4; la landing es commit separado (DD-6). |
| T4 | `_estado_perfil()` lee antes del seed si el orden del `__main__` cambia | El seed corre antes de construir `demo` (orden actual de `__main__` ya lo garantiza); test manual en apply. |
| T5 | Valores seed no mapean (custom keys) | Todos los valores verificados contra `init_options.json` (§3.1) — el formatter los mapea limpio. |
| T6 | Gradio 6 cambia `gr.Markdown` render en `Blocks` | Solo lectura → sin eventos; riesgo mínimo; verificar en apply con `python scripts/test_app.py`. |
| T7 | Cold start Space tras deploy | Copy honesto en landing (decisión 13): "la primera visita puede tardar unos segundos en arrancar". |

---

## 10. Referencias

- `openspec/changes/producto-vendible/proposal.md` — decisiones 1-14, RFs, CAs.
- `openspec/changes/producto-vendible/specs/producto-vendible/spec.md` — 21 RFs + 11 escenarios + mapa de aceptación.
- `agents/init_options.json` — sets válidos para el seed.
- `agents/creativo/agent.py` (L135-270) — `formatear_restaurante_para_chef` (mapeos).
- `agents/knowledge_context.py` — `bootstrap_necesario`, `guardar_*`, paths.
- `agents/init_phase.py` (L635-760) — `_schema_doc_*`, `PREGUNTAS_RESTAURANTE`.
- `scripts/test_app.py` — invariantes (firma, theme/css en launch, sin type=).
- `docs/index.html` — landing actual a reemplazar.
