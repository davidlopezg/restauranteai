# Explore — producto-vendible

## Resumen ejecutivo

El producto (Chef Creativo / RestaurantEAI) ya es **técnicamente sólido** (MVP-3: 4 skills, conocimiento del restaurante inyectado, memoria SQLite, deploy HF Space funcionando), pero **no es vendible** hoy por tres gaps concretos:

1. **La demo pública miente sin querer**: el Space de HF arranca sin TTY y genera `restaurante.json = {}` y `catalogo_platos.json = []` vacíos (`app.py`, bloque `__main__`). El chef corre **sin contexto de restaurante** — la landing promete "El chef te conoce (15 preguntas, las recuerda para siempre)" y eso **no ocurre en la demo pública**. Un perfil demo genérico seedeado resuelve esto con cambio mínimo.
2. **La landing está desactualizada y no vende**: dice "MVP-0.5" (el README dice MVP-3), no cubre las skills `ideas_creativas` ni `chat`, no tiene enmarque problema→solución, ni oferta de implementación, ni captura de leads, ni prueba visual de la demo. Todo lo que falta es 100% factible gratis en un HTML estático en GitHub Pages (con la salvedad de que no hay evidencia de que la landing esté **live** todavía).
3. **El init es CLI-only**: un cliente no técnico no puede configurar su restaurante sin tocar terminal. El core reutilizable para una versión web YA existe (`PREGUNTAS_RESTAURANTE` de 15 preguntas data-driven + `_extraer_platos_de_carta()` que es función pura sin `input()`), pero no hay UI web ni handler que lo hospede. Es viable, pero es el pedazo más grande del cambio y conviene dimensionarlo aparte.

**Restricción central verificada**: el combo de deps pineadas en `memory/memory.md` (era Gradio 5.6: `gradio>=5.6,<6.0`, `huggingface_hub<1.0`, `pydantic==2.10.6`, `jinja2<3.1.0`) **está obsoleto** — `requirements.txt` actual migró a Gradio 6.19 (`gradio>=6.19,<7.0`, `huggingface_hub>=1.2,<2.0`, sin pins de pydantic/jinja2) y `scripts/test_app.py` valida explícitamente que `huggingface_hub` **NO** se pinee a `<1.0` con Gradio 6. Reintroducir el combo viejo **rompería el deploy y los tests**. No tocar deps.

## Estado actual (mapeo)

| Área | Estado verificado | Fuente |
|---|---|---|
| Space HF vivo | ✅ Funciona end-to-end (README: "MVP-3 ... Deployado en Hugging Face Spaces"; memory: logs con HTTP 200 de MiniMax) | `README.md` (estado del proyecto), `memory/memory.md` (cierre 2026-07-01) |
| Stack HF | Gradio `6.19.0` (frontmatter `sdk_version`), Python `3.11` (obligatorio), `app_file: app.py`, `pinned: false` | `README.md` frontmatter |
| Deps | `httpx>=0.27.0`, `python-dotenv>=1.0.0`, `gradio>=6.19,<7.0`, `huggingface_hub>=1.2,<2.0`. **Sin** pydantic/jinja2 | `requirements.txt` |
| Landing | Código ✅ (`docs/index.html`); **live en GitHub Pages: sin evidencia** (memory marca "Subir landing a producción" como PENDIENTE) | `README.md` hito MVP-1, `memory/memory.md` 2026-07-02 |
| Skills | 4: `ficha`, `proceso_creativo`, `ideas_creativas`, `chat` (README dice "3 skills" → doc drift) | `agents/creativo/skills.py` |
| Init | CLI-only con TTY; 15 preguntas data-driven; opciones externalizadas en `init_options.json` + patrón "otra (escribir)" | `agents/init_phase.py`, `agents/init_options.json` |
| Knowledge | `.agent_knowledge/` (gitignored) con `restaurante.json` + `catalogo_platos.json` + `ideas.db` + `sessions/` | `agents/knowledge_context.py`, `memory/memory.md`, `.gitignore` |
| No-TTY hoy | Genera archivos **vacíos** + warning | `app.py` bloque `__main__` |
| Tests | `scripts/test_app.py` (6 checks de regresión app) + 120 tests memoria | `scripts/test_app.py`, `README.md` |
| Versión | `v1.3.0` | `VERSION` |
| Repos | Template público `davidlopezg/restauranteai` + instancia privada `davidlopezg/restauranteia-live` (patrón template→instancia) | `README.md` |

> Nota de evidencia: `.env.example` no pudo leerse (bloqueo de policy del entorno); las 3 variables (`MINIMAX_API_KEY`, `MINIMAX_BASE_URL`, `MINIMAX_MODEL`) están documentadas en `README.md` y `DEPLOY_HF.md`, que sí se leyeron.

## Hallazgos por área

### Landing

**Estructura actual de `docs/index.html` (evidencia verificada):**

1. **Hero** — badge "MVP-0.5 · Desplegado en Hugging Face", emoji 🍂, H1 "Chef Creativo", subtítulo "Generador de fichas culinarias con inteligencia artificial...", CTAs: "🍳 Probar ahora" (→ HF Space) y "Cómo funciona →". **Severidad: alta** — "MVP-0.5" es jerga interna, no un argumento de venta; el H1 describe una feature, no un resultado para el hostelero.
2. **"El chef te conoce"** — callout "La primera vez te hace **15 preguntas**... las **recuerda para siempre**" + 6 feature-cards (ticket, técnicas, comensales, valores, entorno, límites). **Severidad: alta** — promesa que la demo pública NO cumple (ver App/Init): en HF no hay 15 preguntas (no-TTY) y el filesystem del contenedor es efímero (no "recuerda para siempre").
3. **"Qué hace el chef"** — 6 cards (nombre, storytelling, ficha técnica, maridaje, prompt imagen, estacionalidad). No menciona `ideas_creativas` ni `chat` (2 de las 4 skills reales). **Severidad: media** — viola la regla operativa de memory (2026-07-02): "toda capacidad nueva debe quedar explícita en la landing".
4. **Demo / ejemplos** — 5 prompts de ejemplo en `demo-box` + CTA "Ir al chat". No hay **visualización** de la demo (sin screenshot, sin iframe): solo texto. **Severidad: media** — para un comprador no técnico, "ver" el output antes de cliquear es decisivo.
5. **"Cómo funciona"** — 4 pasos (escribís, el chef pregunta, razona, recibís la ficha).
6. **"Proceso creativo"** — callout + 7 fase-cards + 11 pills de métodos ElBulli. Buen contenido, pero habla el idioma del chef, no el del dueño.
7. **"Tecnología"** — 3 cards (MiniMax-M3, HF Spaces, Python+Gradio "Código abierto (MIT)"). **Severidad: baja** — para el comprador no técnico esto es ruido; el dato "MIT / gratis" sí sirve al modelo open core.
8. **Footer** — GitHub, HF Space, Licencia MIT, "Construido con 🍂 por David López Gamero · Cataluña, 2026".

**Lo que falta para un comprador no técnico (todas factibles 100% gratis):**
- **Problema→solución**: "¿Renovar la carta te lleva semanas? ¿Los platos nuevos no sorprenden?" — hoy la landing abre con la solución, no con el dolor.
- **Oferta de implementación (open core)**: ninguna sección "¿Querés esto en tu restaurante? Te lo implementamos". Falta explicitar el modelo: software gratis (MIT), servicio pago.
- **Captura de leads**: no hay formulario, mailto, WhatsApp ni nada. Opciones gratis: `mailto:` (cero infra), Google Form (gratis), enlace WhatsApp (gratis, expone número personal — decisión de David).
- **Prueba social / proof**: no hay testimonios ni casos (no se puede usar "Sol de Nit" públicamente — ver Riesgos). Alternativa honrada: casos anónimos genéricos o métricas verificables del propio producto.
- **Visualización de demo**: iframe del Space HF (gratis, **verificar que Gradio 6 permita embedding** — puede estar bloqueado por CSP/X-Frame-Options) o screenshot estático commiteado al repo (100% seguro).
- **GitHub Pages**: memory documenta activación vía Settings → Pages → Source: `main` + `/docs` (sin workflow). **No hay evidencia en README/memory de que la landing esté live** (el último registro dice "Subir landing a producción (push a origin) — es lo que dispara GitHub Pages" como pendiente). Nota adicional: la carpeta local es `restauranteia` pero el README linkea `github.com/davidlopezg/restauranteai` — la URL de GH Pages depende del nombre real del repo; verificar antes de fijar links.

**Factible en HTML estático single-file sin build step**: todo lo anterior (copy, secciones, CTAs, mailto/Google Form embed, iframe o screenshot, CSS/JS vanilla). Mantener la filosofía actual de cero dependencias externas (fonts system-ui, paleta inline) para no depender de CDNs.

### App Gradio

**Estado actual (`app.py`, verificado):**
- Importa desde `agents/creativo/agent.py`: `call_minimax`, `load_restaurante`, `formatear_restaurante_para_chef`, etc. + registry de skills.
- `responder(mensaje, historial, skill="ficha") -> dict` — firma compatible con `gr.ChatInterface` formato messages. Dispatch: 1º comandos del módulo memoria (`handle_command` transversal, consola de ideas), 2º skills `proceso_creativo` (state machine con `_SESION_PC` global + lock), `ideas_creativas` y `chat` (handlers propios), 3º default `ficha` (prompt + contexto restaurante + catálogo + aviso estacionalidad + instrucción idioma).
- UI: `with gr.Blocks() as demo:` → `skill_selector = gr.Radio(choices=SKILL_CHOICES, value="ficha", ...)` → `gr.ChatInterface(fn=responder, title="🍂 Chef Creativo — RestaurantEAI", cache_examples=False, description=..., examples=..., additional_inputs=[skill_selector], chatbot=gr.Chatbot(avatar_images=(None, "🍂")))`.
- `CUSTOM_CSS` oculta el footer (`footer {visibility: hidden}`); `demo.launch(server_name="0.0.0.0", server_port=7860, show_error=True, theme=gr.themes.Soft(primary_hue="orange"), css=CUSTOM_CSS)` — theme/css van al `.launch()` (Gradio 6+), no al constructor de Blocks.
- `__main__`: `bootstrap_necesario()` → si `sys.stdin.isatty()` corre `fase_init_interactiva()`; si no (HF/CI): warning + `guardar_restaurante({}, schema)` + `guardar_catalogo([], schema)` → **perfil vacío**.

**Conflicto de deps (verificado, severidad: alta):**
- `memory/memory.md` (saga deploy 2026-07-01) recomienda: `gradio>=5.6,<6.0`, `huggingface_hub>=0.19.3,<1.0`, `pydantic==2.10.6`, `jinja2<3.1.0`, `sdk_version: 5.6.0`.
- `requirements.txt` actual: `gradio>=6.19,<7.0`, `huggingface_hub>=1.2,<2.0` (comentario: "Gradio 6.19 ya no usa HfFolder"), **sin** pins de pydantic/jinja2. Frontmatter README: `sdk_version: 6.19.0`, `python_version: '3.11'`.
- `scripts/test_app.py` (`test_kwarg_prohibidos`) verifica que `huggingface_hub` **no** esté pineado `<1.0` cuando `gradio>=6`.
- **Conclusión**: el combo de memory pertenece a la era Gradio 5.6 y ya fue migrado. Los pins "pydantic==2.10.6 / jinja2<3.1.0 / hf_hub<1.0" **NO deben reintroducirse** (rompería Gradio 6 y el test). La lección vigente de memory es estructural: Python 3.11 obligatorio, `cache_examples=False`, defensa en profundidad, no confiar en defaults de HF.

**Polish factible sin romper el deploy (todas verificadas contra los invariantes de `test_app.py`):**
- Cambiar hue del theme / CSS (ya parametrizado en `.launch()`).
- Añadir indicador de perfil activo: "Demo: Restaurante Mediterráneo" vs "(sin contexto)" — informativo y honesto, clave para la venta.
- Link de vuelta a la landing (hoy el Space no enlaza a ninguna parte).
- Añadir skill `chat` e `ideas_creativas` correctamente cubiertas (ya están en el selector Radio automáticamente — 4 opciones; la UI ya las muestra, es la **landing** la que no las refleja).
- **Cuidado**: cualquier cambio en la firma de `responder()` rompe `test_firma_responder` (2 args, return `dict`); cualquier `theme=`/`css=` en el constructor de Blocks rompe `test_kwarg_prohibidos`. Si se cambia, actualizar `scripts/test_app.py` en el mismo cambio.

### Init / conocimiento

**Cómo funciona hoy (verificado):**
- `agents/knowledge_context.py`: `KNOWLEDGE_DIR = PROJECT_ROOT / ".agent_knowledge"`; `RESTAURANTE_PATH`/`CATALOGO_PATH`; `bootstrap_necesario()` = True si falta **cualquiera** de los dos archivos; `ensure_initialized()` corre la fase init interactiva; `cargar_/guardar_*` con schema_doc `.md` companion.
- `agents/init_phase.py`: `PREGUNTAS_RESTAURANTE` = **15 preguntas** (3 number de ticket, choice `sofisticacion`, multichoice `productos_dominantes`/`tecnicas_dominantes`/`tipo_servicio`, choice `grupos`, multichoice `clases_comedores`, choice `origen_inspiracion`, multichoice `orientacion_nutricional`, choice `localizacion`, multichoice `religion`, choice `tiempo_preparacion`, multichoice `epoca_estilo`). Tipos: `number` / `choice` / `multichoice` / `text`. Toda la interacción es `input()` (TTY).
- Opciones externalizadas en `agents/init_options.json` (fuente de verdad si la key existe; fallback hardcoded) + sufijo automático **"otra (escribir)"** en cada choice/multichoice (patrón `SUFIJO_OTRA`/`OTRO_LITERAL`) — lección de memory 2026-07-01.
- Catálogo: 3 modos — pegar carta (LLM extrae JSON vía `_extraer_platos_de_carta(carta_texto)`, **función pura sin `input()`**, con robustez de parsing), manual (uno por uno), saltar.
- Consumidores del contexto: `formatear_restaurante_para_chef()` (mapeos SOFISTICACION/GRUPOS/LOCALIZACION/TIEMPO/ORIGEN/EPOCA — valores custom del patrón "otra (escribir)" caen al fallback `mapping.get(v, v)`, es decir, se pasan crudos: el chef los trata como contexto cualitativo; memory confirma que `system_chef.md` no asume listas cerradas) y `formatear_catalogo_para_chef()` (cap 30 platos).

**Lo que implica llevarlo a web (mapa de capacidades, sin diseñar):**
- **Núcleo reutilizable**: el schema de preguntas (data-driven) + `init_options.json` + `_extraer_platos_de_carta()` son agnósticos de TTY. Solo la capa de input (`_input_*`, `_leer_multilinea`) es CLI.
- **No existe hoy** ningún handler/skill que hospede un cuestionario guiado en la web. Los patrones cercanos disponibles:
  1. **State machine de `proceso_creativo`** (7 fases, sesión en dict global `_SESION_PC` + persistencia JSON en `.agent_knowledge/sessions/`) — probado para flujo paso-a-paso por turnos en el chat.
  2. **Dispatch transversal de `agents/memoria/commands.py`** (`handle_command`, detectado antes del dispatcher de skill) — patrón listo para comandos tipo `/config` o `/restaurante`.
  3. **Gradio Blocks + estado**: `skill_selector` ya demuestra componentes extra; un tab/accordion de configuración con `gr.Radio`/`gr.CheckboxGroup`/`gr.Number`/`gr.Textbox` mapearía 1:1 los 4 tipos de pregunta.
- **Restricción dura verificada**: el filesystem del contenedor HF free es **efímero** (memory: los `.csv` de `cache_examples` no persisten entre reinicios; el Space free se duerme/rebootea). Cualquier config guardada en `.agent_knowledge/` **se pierde en el reinicio**. Por eso el perfil demo debe **reseedearse en cada boot**, y un init web para clientes reales pertenece a la **instancia privada del cliente** (servicio de implementación), no al demo público.
- Opciones a evaluar en proposal (solo listado): (a) tab Gradio de configuración con persistencia efímera (sirve para demo en sesión); (b) skill/chat guiado (reusa patrón proceso creativo, UX más lenta pero cero UI nueva); (c) comando transversal `/config` (reusa memoria commands); (d) dejar el init web fuera de este change y vender "implementación = nosotros lo configuramos por vos" (requiere TTY/local o instancia privada, que es donde ya funciona).

### Demo genérica

**Hechos verificados:**
- `bootstrap_necesario()` → True si falta `restaurante.json` o `catalogo_platos.json`.
- `app.py` no-TTY hoy: genera **vacíos** (`{}` y `[]`) con warning — el chef del Space público funciona **sin ningún contexto de restaurante**.
- `.gitignore` excluye `.agent_knowledge/` (regla de oro del patrón template→instancia: "El template nunca toca `.agent_knowledge/`").

**Cambio mínimo propuesto (para evaluar en proposal):**
- Seedear un **perfil demo genérico** (p.ej. restaurante mediterráneo de ticket medio: `sofisticacion: media`, `productos_dominantes: [vegetales, pescado, mariscos]`, `epoca_estilo: [mediterranea_moderna]`, catálogo de 8-12 platos de ejemplo) desde archivos **trackeados en el repo fuera de `.agent_knowledge/`** (p.ej. `agents/creativo/knowledge/demo_restaurante.json` + `demo_catalogo_platos.json`), copiados a `.agent_knowledge/` **en boot** cuando `bootstrap_necesario()` y no hay TTY.
- Alternativas descartables/riesgosas: (a) commitear dentro de `.agent_knowledge/` — viola `.gitignore` y la regla template→instancia (la instancia viva heredaría el seed y arriesga commitear datos reales encima); (b) generar en boot por código — válido también (determinista, cero archivos trackeados), pero un JSON trackeado es editable sin tocar código (consistente con el patrón `init_options.json`).
- **Riesgo de fuga**: el perfil demo debe llevar marca explícita de demo (p.ej. `"demo": true`, nombre "Restaurante de demostración") para que el chef no hable como si fuera un restaurante real de un cliente, y para que el indicador de la UI lo muestre. **Nunca** "Sol de Nit" ni datos reales (ver Riesgos).
- Beneficio colateral: la landing puede entonces decir la verdad ("probá con un restaurante mediterráneo de ejemplo") y el paso "El chef te conoce" deja de ser una mentira en el demo.

### Mensajes de venta

**Inventario actual de la landing (secciones):** hero · El chef te conoce · Qué hace el chef · Demo/ejemplos · Cómo funciona · Proceso creativo · Tecnología · Footer. **Activos existentes**: copy voseo coherente (es-AR), ejemplos de prompts, las 7 fases del proceso creativo, 11 métodos ElBulli, dato MIT/open source. **Activos ausentes**: problema→solución, propuesta de valor en resultados ("carta que vende", "diferenciación", "menos horas pensando platos"), prueba/caso, captura de leads, oferta de implementación paga (open core), FAQ/objeciones ("¿necesito saber programar? No"), nota de privacidad de datos, cobertura de las skills reales (ideas + chat), visual de la demo, des-jerga (MVP-0.5).

**Restricción de honestidad (regla de memory 2026-07-02)**: nada de prometer capacidades que el código no hace. Ejemplo verificado: el prompt del chef dice "has asesorado a más de 40 restaurantes" — eso es **persona del prompt**, no un hecho comercial verificable; no usarlo como prueba social en la landing.

## Decisiones tentativas

> Para confirmar/ajustar en la ronda de preguntas del proposal. Ninguna es diseño cerrado.

- **D1 — Perfil demo genérico**: seedear perfil demo desde JSON trackeado en repo (fuera de `.agent_knowledge/`), copiado a boot cuando falta y no hay TTY; marcado `"demo": true`; indicador visible en la UI del Space. Reemplaza el "perfil vacío + warning" actual de `app.py`.
- **D2 — Landing reescrita (open core)**: single-file HTML en `docs/`, cero build, cero dependencias externas; secciones problema→solución, cómo es la demo (visual), oferta de implementación ("el software es gratis (MIT); la implementación se paga"), captura de leads (canal a decidir: mailto/Google Form/WhatsApp), FAQ, y cobertura real de las 4 skills. Quitar jerga interna (MVP-0.5). Mantener voseo.
- **D3 — App polish acotado**: theme/css, indicador de perfil, enlace a landing, copy de description alineado a venta. **Sin** cambiar firma de `responder()` ni reintroducir pins viejos; actualizar `scripts/test_app.py` si algún invariante cambia.
- **D4 — Init web**: evaluar como **parte del mismo change solo si el scope lo aguanta** (budget 400 líneas); si no, proponerlo como change aparte con prioridad alta, o arrancar con la opción (d) "implementación = configuramos por vos" (que es el modelo de negocio de todos modos).
- **D5 — Deps**: congelar el stack actual (`gradio>=6.19,<7.0`, `huggingface_hub>=1.2,<2.0`, Python 3.11). No tocar pins; documentar en memory que el combo 5.6 quedó obsoleto.
- **D6 — GitHub Pages**: verificar el estado live antes de prometer URL; fijar la URL real del repo (restauranteai vs restauranteia).

## Riesgos y restricciones

| # | Riesgo | Severidad | Detalle/evidencia |
|---|---|---|---|
| R1 | Reintroducir deps de la era Gradio 5.6 | **Alta** | Rompe Gradio 6 + `test_app.py` (`huggingface_hub<1.0` falla explícitamente con `gradio>=6`). `requirements.txt` actual es la fuente de verdad. |
| R2 | Fuga de datos del restaurante real | **Alta** | "Sol de Nit" es solo credibilidad interna (nunca expuesto). `.agent_knowledge/` está en `.gitignore`; el seed demo debe vivir fuera de esa carpeta y estar marcado demo. El template jamás commitea `.agent_knowledge/` (regla de oro README). |
| R3 | Persistencia efímera en HF free | **Alta** | El filesystem del contenedor no persiste entre reinicios (lección `cache_examples` en memory). Config web guardada en `.agent_knowledge/` se pierde; el seed debe regenerarse en cada boot. Venta = instancia privada del cliente, no el demo público. |
| R4 | Landing desactualizada vs código | **Media** | Dice MVP-0.5 (código MVP-3), omite skills ideas/chat. Violación de la regla operativa de memory (2026-07-02). |
| R5 | Landing "El chef te conoce" falsa hoy | **Media** | En el Space no-TTY el contexto es vacío; no hay 15 preguntas ni "recuerda para siempre" (efímero). Se corrige con D1 y copy honesto. |
| R6 | Romper invariantes de `test_app.py` | **Media** | Firma `responder` (2 args → dict), theme/css solo en `.launch()`, sin `type=` kwarg, ChatInterface dentro de Blocks. Cualquier cambio debe actualizar el test en el mismo commit. |
| R7 | iframe de la demo en la landing | **Media** | Gradio 6 Space puede bloquear embedding (CSP/X-Frame-Options). Verificar antes de prometer; fallback = screenshot estático en el repo. |
| R8 | Espacio HF free: cold starts / sleep | **Baja** | CPU basic se duerme; primera visita tarda. No bloquea venta si la landing lo enmarca bien. |
| R9 | URL de GH Pages incierta | **Baja** | Repo dir `restauranteia` vs README `restauranteai`; y sin evidencia de que Pages esté live. Verificar nombre real del repo y estado del deploy. |
| R10 | Cambios de `openspec/` no deben pushearse a `hf` | **Baja** | Lección de memory 2026-07-02: push solo a `origin` (GitHub). |
| R11 | Init web: prueba social inexistente | **Baja** | "40 restaurantes asesorados" es persona del prompt, no hecho verificable. No usar en la landing. |

## Recomendaciones para el proposal

1. **Scope sugerido para este change** (dentro de ~400 líneas): D1 (seed demo genérico + indicador), D2 (landing reescrita open core), D3 (polish app acotado), D5 (documentar deps). **Init web completo (D4) como change separado** — es el de mayor superficie y merece su propio proposal con preguntas de producto.
2. **Orden de implementación sugerido**: seed demo → indicador UI → landing (ahora puede decir la verdad) → GH Pages live (verificar) → oferta/leads.
3. **Modelo de venta a reflejar en la landing**: "El software es tuyo, gratis, MIT. Si querés que **tu** restaurante quede configurado y funcionando, lo hacemos por vos (implementación paga)". El init web queda entonces como demo de onboarding en la instancia privada, no como feature del demo público.
4. **Honestidad como feature de venta**: la demo con perfil genérico + indicador "Demo" es más creíble que un perfil vacío; usar eso como diferenciador ("probá en 10 segundos, sin registro, sin terminal").
5. **No tocar**: `requirements.txt`, frontmatter del README del Space (excepto nada), `.gitignore`, `agents/init_phase.py` (salvo que D4 entre), la API key/secrets.
6. **Tests**: ampliar `scripts/test_app.py` si cambia la UI; mantener 120 tests de memoria verdes; test unitario para el seed (verifica `bootstrap_necesario()` → archivos demo válidos contra el schema de `_schema_doc_restaurante`).

## Archivos relevantes

| Archivo | Rol en el cambio |
|---|---|
| `docs/index.html` | Landing a reescribir (D2). Single-file, zero-deps, GH Pages vía `main`+`/docs`. |
| `app.py` | UI Gradio + bloque `__main__` no-TTY (punto de inyección del seed demo D1) + indicador de perfil. |
| `agents/knowledge_context.py` | `bootstrap_necesario()`, paths, `guardar_restaurante/guardar_catalogo` — base del seed. |
| `agents/init_phase.py` | `PREGUNTAS_RESTAURANTE` (15 preguntas) + `_extraer_platos_de_carta()` (núcleo reutilizable web, D4). |
| `agents/init_options.json` | Opciones externalizadas + patrón "otra (escribir)" (reutilizable en UI web). |
| `agents/creativo/skills.py` | Registry de 4 skills (fuente de verdad para UI y para la landing). |
| `agents/creativo/agent.py` | `call_minimax`, `formatear_restaurante_para_chef`, handlers de skills. |
| `agents/creativo/prompts/system_chef.md` | Prompt del chef (contexto restaurante inyectado; no tocar sin necesidad). |
| `agents/memoria/storage.py` | `ideas.db` en `.agent_knowledge/` (efímero en HF; patrón de comandos transversales para D4). |
| `agents/creativo/proceso_creativo.py` | State machine 7 fases (patrón para cuestionario web, D4). |
| `requirements.txt` | Stack real: `gradio>=6.19,<7.0`, `huggingface_hub>=1.2,<2.0` (NO tocar). |
| `README.md` | Frontmatter HF (`sdk_version: 6.19.0`, `python 3.11`), patrón template→instancia, doc drift "3 skills". |
| `DEPLOY_HF.md` | Facts del Space `RestaurantEAI` (secrets, restart manual). |
| `memory/memory.md` | Lecciones deploy saga (era 5.6 — obsoleta en deps, vigente en estructura), regla landing-realidad, no-push a `hf`. |
| `scripts/test_app.py` | Invariantes de la app (firma `responder`, theme/css en launch, hf_hub no pineado <1.0). |
| `.gitignore` | `.agent_knowledge/` excluido (frontera de privacidad del seed). |
| `VERSION` | `v1.3.0` (bumpear en el change si aplica). |
| `openspec/config.yaml` | `artifactLanguage: es`, `reviewBudget: 400`, `executionMode: interactive`. |

## Preguntas abiertas

1. **¿La landing está live en GitHub Pages hoy?** ¿Y cuál es la URL real (nombre del repo: `restauranteai` vs `restauranteia`)? No hay evidencia en README/memory de que el push de producción se haya hecho.
2. **¿El init web entra en este change o es un change aparte?** (Presupuesto 400 líneas; recomendación: aparte, con su propia ronda de preguntas de producto.)
3. **¿Canal de captura de leads?** `mailto:` (cero infra), Google Form (gratis), WhatsApp (gratis pero expone número personal), o GitHub Issues (poco comercial).
4. **¿La demo genérica debe permitir al visitante reconfigurar el perfil durante su sesión** (efímero, in-memory) o solo perfil genérico estático? (Impacto en complejidad del Space.)
5. **¿Prueba social disponible?** ¿Hay algún restaurante (distinto de Sol de Nit, que es privado) que haya validado el producto y acepte ser mencionado de forma anónima o con permiso?
6. **¿El Space público queda como demo única con perfil genérico** y la venta se apoya en "implementación en tu instancia privada" (alineado con el patrón template→instancia ya existente)? Confirmar este encuadre con el modelo open core.
7. **¿Se mantiene el voseo es-AR en la landing** (consistente con `userLanguage: es-AR`) o se quiere español neutro para el mercado catalán/peninsular de David?
8. **¿Badge/estado**: el Space seguirá en CPU basic gratis con cold starts — ¿aceptable, o hay que mitigar con copy en la landing?

---

## Nota de proceso (para el orquestador)

- **Artifact store**: `openspec` (Engram no disponible en esta sesión). El `explore.md` completo está arriba, listo para persistir en `openspec/changes/producto-vendible/explore.md`. **No realicé escritura** (sin tool de escritura en esta sesión) — no reclamo persistencia.
- **`.env.example`**: lectura bloqueada por policy del entorno; los facts de env (`MINIMAX_API_KEY`, `MINIMAX_BASE_URL`, `MINIMAX_MODEL`) provienen de `README.md` y `DEPLOY_HF.md`.
- **`grep`/`rg`**: no disponible en este entorno (falló la descarga de ripgrep); toda la verificación se hizo con lecturas dirigidas.
