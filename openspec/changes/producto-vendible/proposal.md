# Proposal — producto-vendible

> Fase: proposal · Change: `producto-vendible` · Proyecto: `restauranteia`
> Base: `openspec/changes/producto-vendible/explore.md` (evidencia verificada, hallazgos, riesgos R1-R11)
> Estado: **APROBADO por David (2026-08-05)** — ronda de preguntas resuelta, decisiones 10-14 cerradas. Listo para `sdd-spec`.

## Resumen ejecutivo

El producto (Chef Creativo / RestaurantEAI) es técnicamente sólido (MVP-3, 4 skills, memoria SQLite, Space HF funcionando) pero **no es vendible**. Tres gaps concretos lo frenan:

1. **La demo pública miente sin querer**: en el Space de HF (sin TTY) se generan `restaurante.json = {}` y `catalogo_platos.json = []` vacíos. El chef corre **sin contexto de restaurante** mientras la landing promete "te hace 15 preguntas y las recuerda para siempre".
2. **La landing no vende**: dice "MVP-0.5" (jerga interna), omite 2 de las 4 skills reales (`ideas_creativas`, `chat`), no enmarca problema→solución, no tiene oferta de implementación, no captura leads ni muestra la demo visualmente.
3. **El init es CLI-only**: un cliente no técnico no puede configurar su restaurante sin terminal (esto se resuelve en **Fase 2**, change `init-web`, solo se referencia acá).

Este change entrega la **primera capa vendible** con infraestructura 100% gratis: un perfil demo genérico seedeado (D1), una landing trilingüe single-file orientada a conversión con oferta open core (D2), un polish honesto de la app Gradio (D3) y la documentación del stack real de dependencias (D5). Modelo de negocio confirmado: **open core** — software gratis (MIT), monetización por servicio de implementación pago. Sin tocar `requirements.txt`, sin cambiar la firma de `responder()`, sin exponer datos reales.

## Problema / oportunidad

**Problema (estado actual verificado):**

- **Demo pública con perfil vacío**: `app.py` (bloque `__main__`) detecta `bootstrap_necesario()` y, al no haber TTY (HF/CI), genera archivos **vacíos** con warning. El chef del Space público genera fichas **sin ningún contexto de restaurante** — la promesa de la landing ("el chef te conoce") no se cumple en la demo.
- **Landing desactualizada y no comercial**: `docs/index.html` dice "MVP-0.5 · Desplegado en Hugging Face" (el README declara MVP-3), no cubre las skills `ideas_creativas` ni `chat` (2 de 4), no tiene enmarque problema→solución, ni oferta de implementación, ni captura de leads, ni visual de la demo. Viola la regla operativa de `memory/memory.md` (2026-07-02): "toda capacidad nueva debe quedar explícita en la landing" y "nunca prometer lo que el código no hace".
- **Init CLI-only**: `agents/init_phase.py` recolecta 15 dimensiones + catálogo vía `input()` (TTY). Un restaurante no técnico no puede configurar nada desde el navegador. El núcleo reutilizable ya existe (preguntas data-driven + `init_options.json` + `_extraer_platos_de_carta()` pura), pero la UI web es Fase 2 (`init-web`).

**Oportunidad:**

- Con un **perfil demo genérico** (restaurante mediterráneo de ticket medio), la demo pública se vuelve creíble en 10 segundos, sin registro y sin terminal; la landing puede decir la verdad ("probá con un restaurante de ejemplo") y el paso "el chef te conoce" deja de ser una mentira.
- Con una **landing trilingüe (català · castellano · English) orientada a conversión**, el proyecto pasa de "página de proyecto personal" a **página de venta**: problema→solución, 4 skills reales, demo visual, oferta open core ("el software es gratis MIT; si querés que tu restaurante quede configurado y funcionando, lo implementamos por vos") con CTA `mailto:`.
- Todo con **cero coste de infraestructura**: GitHub Pages (`docs/` en `main`) + HF Space free, ambos ya verificados live (HTTP 200 en https://davidlopezg.github.io/restauranteai/).

## Objetivos del change

1. **D1 — Demo pública creíble**: seedear un perfil demo genérico (mediterráneo, ticket medio, 8-12 platos) desde JSON trackeado en el repo, copiado a `.agent_knowledge/` en boot cuando `bootstrap_necesario()` y no hay TTY, marcado `demo: true`, con indicador visible en la UI del Space. Reemplaza el "perfil vacío + warning" actual.
2. **D2 — Landing trilingüe orientada a conversión (open core)**: reescribir `docs/index.html` como single-file HTML, cero build, cero dependencias externas, 3 idiomas completos (català · castellano · English) con selector JS y default castellano; secciones: hero problema→solución, 4 skills reales, demo con visual, oferta de implementación con CTA `mailto:`, FAQ, footer honesto.
3. **D3 — App polish honesto**: theme/css existente + indicador de perfil activo + enlace de vuelta a la landing + copy de `description` alineado a venta. **Sin** cambiar la firma de `responder()`, **sin** tocar deps, **sin** romper invariantes de `scripts/test_app.py`.
4. **D5 — Documentar el stack real de deps**: dejar escrito en `memory/memory.md` que el stack actual (`gradio>=6.19,<7.0`, `huggingface_hub>=1.2,<2.0`, Python 3.11) es la fuente de verdad y que el combo de la era Gradio 5.6 (`gradio>=5.6,<6.0`, `huggingface_hub<1.0`, `pydantic==2.10.6`, `jinja2<3.1.0`) quedó obsoleto y **no debe reintroducirse** (rompería Gradio 6 y `test_app.py`).

## Alcance (In scope / Out of scope)

### In scope

| Área | Qué incluye |
|---|---|
| **D1 — Seed demo genérico** | 2 JSON trackeados fuera de `.agent_knowledge/` (p. ej. `agents/creativo/knowledge/demo_restaurante.json` + `demo_catalogo_platos.json`), coherentes con el schema de `_schema_doc_restaurante()` / `_schema_doc_catalogo()` (15 dimensiones con valores válidos + `"demo": true` + nombre explícito de demostración; 8-12 platos con `nombre/categoria/descripcion/precio`). En `app.py` (bloque `__main__`): si `bootstrap_necesario()` y **no** hay TTY → copiar seed + generar schema docs companion; si hay TTY → init interactivo intacto; si ya existen archivos → no tocar nada. Marca `demo: true` legible por el indicador de UI. Test unitario del seed (valida contra schema y que respeta el invariante "no sobrescribe archivos existentes"). |
| **D2 — Landing trilingüe** | Reescritura completa de `docs/index.html`: single-file, cero build, cero dependencias externas (system-ui, JS vanilla). Diccionario de idiomas JS + selector en header, **3 versiones completas** (català · castellano · English), default castellano. Secciones: hero problema→solución; las **4 skills reales** (ficha, proceso_creativo, ideas_creativas, chat — fuente de verdad `agents/creativo/skills.py`); sección demo con **visual** (iframe del Space verificado o screenshot estático commiteado como fallback); oferta de implementación open core con CTA `mailto:davidlopezgamero@gmail.com` y subject pre-armado; FAQ/objeciones ("¿necesito saber programar? No"); footer honesto ("construido por un hostelero real" + MIT + open source + demo live, **sin** Sol de Nit ni datos reales). Eliminar "MVP-0.5". |
| **D3 — App polish** | Indicador de perfil activo en la UI del Space (p. ej. `gr.Markdown` dentro de `with gr.Blocks()`: "Demo: Restaurante Mediterráneo" vs "(sin contexto)"); link de vuelta a la landing; copy de `description` del `gr.ChatInterface` alineado a venta (menciona los 4 modos). Mantener theme/css en `.launch()`, firma de `responder()` intacta, `cache_examples=False`. Actualizar `scripts/test_app.py` **en el mismo commit** solo si algún invariante cambia. |
| **D5 — Deps / documentación** | Entrada en `memory/memory.md`: stack real = `gradio>=6.19,<7.0` + `huggingface_hub>=1.2,<2.0` + Python 3.11 (fuente de verdad, `requirements.txt`); combo 5.6 obsoleto (riesgo R1); lecciones vigentes de la deploy saga (Python 3.11 obligatorio, `cache_examples=False`, defensa en profundidad). **Menor/opcional**: corregir drift del README "3 skills" → 4 skills (honestidad documental; ~5 líneas). |

### Out of scope (explícito)

- **Init web** (Fase 2, change `init-web`): UI de configuración del restaurante en el navegador. Se referencia acá solo para enmarcar la oferta ("tu restaurante configurado y funcionando" = servicio de implementación pago que incluirá el config web).
- **Google Form / formularios de leads**: el canal de captura en Fase 1 es `mailto:` a davidlopezgamero@gmail.com.
- **Hosting/dominio pago**, SaaS multi-tenant, multi-instancia pública.
- **Datos reales de Sol de Nit** o de cualquier restaurante real: jamás en template, landing, demo ni Space público.
- **Cambios a la lógica del chef**: prompts (`system_*.md`), skills, proceso creativo, handlers, dispatch, `agents/init_phase.py` (salvo lo que D1 reutiliza), `agents/memoria/*`.
- **Cambios a `requirements.txt`** ni al frontmatter del README del Space.
- **Cambiar la firma de `responder()`** o el formato de ChatInterface/Chatbot (invariantes de `scripts/test_app.py`).
- Reconfiguración del perfil demo por el visitante durante su sesión (sería Fase 2).

## Requisitos funcionales (por área)

### Landing trilingüe (D2)

- **RF-1 — Single-file y zero-deps**: `docs/index.html` autocontenido; sin CDNs, sin fonts externas, sin build step; CSS/JS inline en vanilla. Debe seguir sirviendo desde GitHub Pages (`main` + `/docs`).
- **RF-2 — Trilingüe completo**: 3 versiones completas (català, castellano, English) del **mismo** contenido, gestionadas por un diccionario JS (patrón `data-i18n` o equivalente) y un selector en el header. Default: castellano. El `lang` del documento y el `title`/`meta description` deben reflejar el idioma activo.
- **RF-3 — Hero problema→solución**: abre con el dolor del comprador ("¿renovar la carta te lleva semanas? ¿los platos nuevos no sorprenden?") y resuelve con la propuesta ("el Chef Creativo piensa contigo cada plato, con tu carta y tu ticket en mente"). CTA primario → demo (Space); CTA secundario → oferta de implementación.
- **RF-4 — Las 4 skills reales**: sección "Qué hace el chef" con las 4 skills del registry (`ficha`, `proceso_creativo`, `ideas_creativas`, `chat`) con su nombre y descripción reales (fuente: `agents/creativo/skills.py`). Nada de prometer lo que el código no hace (regla memory 2026-07-02).
- **RF-5 — Sección demo con visual**: muestra la demo de forma visual — iframe del Space `https://huggingface.co/spaces/davidlopezgamero/RestaurantEAI` **si el embedding funciona** (verificar CSP/X-Frame-Options en diseño, riesgo R7) o, en su defecto, screenshot(s) estático(s) commiteado(s) al repo. Debe indicar explícitamente: "demo con perfil genérico de restaurante mediterráneo, marcada como demo".
- **RF-6 — Oferta open core + CTA mailto**: sección "¿Querés esto en tu restaurante?" que explica el modelo: "el software es gratis, código abierto (MIT); si querés que **tu** restaurante quede configurado y funcionando, lo hacemos por vos (implementación paga)". CTA = `mailto:davidlopezgamero@gmail.com?subject=<pre-armado>` (subject pre-armado, p. ej. "Quiero el Chef Creativo en mi restaurante"). Sin testimonios inventados: solo "construido por un hostelero real" + open source + demo live.
- **RF-7 — FAQ/objeciones**: 4-6 preguntas reales del comprador no técnico ("¿Necesito saber programar? No — la implementación la hacemos nosotros", "¿Cuánto tarda la demo? Está online, probala", "¿Y mis datos? La demo usa un perfil de ejemplo; tu restaurante vive en tu instancia privada").
- **RF-8 — Footer honesto**: GitHub, HF Space, licencia MIT, "construido por un hostelero real (David López Gamero) · Cataluña, 2026". **Sin** mención de Sol de Nit, sin datos reales, sin "MVP-0.5", sin métricas inventadas.
- **RF-9 — Honestidad total**: ningún claim que el código no haga; el copy de "el chef te conoce" se reemplaza por lo que la demo realmente hace (perfil demo precargado; la personalización real es parte del servicio de implementación).

### Seed demo genérico (D1)

- **RF-10 — Archivos seed trackeados fuera de `.agent_knowledge/`**: `agents/creativo/knowledge/demo_restaurante.json` y `demo_catalogo_platos.json` (carpeta de conocimiento estático del agente, ya gitignoreada aparte; **no** tocar `.gitignore` ni commitear nada dentro de `.agent_knowledge/`).
- **RF-11 — Perfil válido contra el schema**: `demo_restaurante.json` con las 15 dimensiones de `PREGUNTAS_RESTAURANTE` con valores **válidos** (de `init_options.json` para que los mapeos de `formatear_restaurante_para_chef` resuelvan bien): restaurante mediterráneo, ticket medio (p. ej. min 25 / max 60 / moda 40), `sofisticacion: media`, `productos_dominantes: [vegetales, pescado, mariscos]`, `epoca_estilo: [mediterranea_moderna]`, etc. **Más** `"demo": true` y `nombre` explícito de demostración (p. ej. "Restaurante de demostración").
- **RF-12 — Catálogo demo**: 8-12 platos con `nombre/categoria/descripcion/precio`, categorías del set válido (`entrante/principal/postre/guarnicion/bebida/otro`), coherentes con el perfil (mediterráneo, ticket medio).
- **RF-13 — Copia en boot sin TTY**: en `app.py` `__main__`: si `bootstrap_necesario()` → si `sys.stdin.isatty()`: `fase_init_interactiva()` (sin cambios); si **no** hay TTY: copiar ambos seeds a `.agent_knowledge/` con `guardar_restaurante(...)` / `guardar_catalogo(...)` + schema docs companion (`_schema_doc_restaurante()`, `_schema_doc_catalogo()`), y loggear que se usó el perfil demo. Si los archivos ya existen → no sobrescribir (idempotente; en HF el filesystem es efímero, así que el reseed se repite en cada boot, riesgo R3).
- **RF-14 — Marca demo legible por la UI**: el indicador lee `restaurante.json` cargado y muestra "Demo: <nombre>" cuando `demo == true`; "(sin contexto)" cuando no hay perfil; el nombre del restaurante real si algún día hay perfil real.
- **RF-15 — Test unitario del seed**: verifica que los 2 JSON seedean un perfil válido contra el schema y que el flujo no-TTY no sobrescribe archivos existentes.

### App polish (D3)

- **RF-16 — Indicador de perfil**: componente visible en el Space (p. ej. `gr.Markdown` dentro de `with gr.Blocks()`, antes del ChatInterface) que muestra el estado del perfil (RF-14). Sin tocar `theme`/`css` del constructor de Blocks (invariante `test_kwarg_prohibidos`).
- **RF-17 — Link a la landing**: enlace visible desde el Space a https://davidlopezg.github.io/restauranteai/ (el Space hoy no enlaza a nada).
- **RF-18 — Copy de description alineado a venta**: `description` del ChatInterface menciona los 4 modos reales y el perfil demo precargado; sin prometer "15 preguntas" ni "recuerda para siempre" (falso en el Space efímero).
- **RF-19 — Invariantes intactos**: firma `responder(mensaje, historial, skill="ficha") -> dict`; `theme=`/`css=` solo en `.launch()`; `cache_examples=False`; ChatInterface dentro de Blocks. Si algún cambio toca un invariante, `scripts/test_app.py` se actualiza en el mismo commit.

### Deps / documentación (D5)

- **RF-20 — memory.md documenta el stack real**: entrada explícita: stack vigente = `gradio>=6.19,<7.0`, `huggingface_hub>=1.2,<2.0`, Python 3.11, sin pins de pydantic/jinja2 (`requirements.txt` y frontmatter del README son la fuente de verdad); el combo 5.6 es historia (riesgo R1) y reintroducirlo rompe Gradio 6 + `test_app.py`.
- **RF-21 — (Menor) Drift README**: corregir "3 skills" → 4 skills si el budget lo permite; caso contrario queda anotado como pendiente para el change `init-web`.

## Requisitos no funcionales

- **NFR-1 — Honestidad como invariante**: nada en landing/demo/copy que el código no haga (regla memory 2026-07-02). Verificar claims contra código antes de escribirlos.
- **NFR-2 — Privacidad**: cero datos reales en el template; seed marcado `demo: true`; `.agent_knowledge/` sigue en `.gitignore`; "Sol de Nit" nunca aparece en superficies públicas.
- **NFR-3 — Cero deps e infra gratis**: landing sin dependencias externas ni build; sin costos de hosting (GH Pages + HF Space free).
- **NFR-4 — Compatibilidad de la app**: `test_app.py` 6/6 verde; 120 tests de memoria verdes; seed test nuevo verde.
- **NFR-5 — Rendimiento**: HTML estático liviano, sin JS de terceros; único request externo posible = iframe del Space (opcional, con fallback).
- **NFR-6 — Accesibilidad básica**: contraste suficiente, HTML semántico, responsive (la landing actual ya es responsive; mantener).
- **NFR-7 — Deploy**: push de app.py a `hf` (Space) y de `docs/` a `origin` (Pages); los archivos de `openspec/` **no** se pushean a `hf` (riesgo R10).
- **NFR-8 — SEO básico**: `title`/`meta description`/`og:` coherentes (castellano default) y actualizados por idioma vía JS.

## Decisiones de producto (confirmadas con David)

> Cerradas con el owner — **no reabrir**. Listadas para que spec/design las tomen como fijas.

1. **Modelo de negocio: OPEN CORE**. Software gratis (MIT). Monetización = servicio de implementación pago ("si alguien lo quiere implementado en su restaurante, paga").
2. **Comprador target**: hosteleros/chefs no técnicos (independientes, alta gama, grupos). Decide quien no es técnico.
3. **Presupuesto**: 100% infraestructura gratis (GitHub Pages + HF Space). Sin dominio ni hosting pago.
4. **Demo**: perfil GENERIC (mediterráneo, ticket medio), marcado como demo. **Nunca** "Sol de Nit" ni datos reales.
5. **Scope en 2 fases**: Fase 1 = este change (D1 + D2 + D3 + D5); Fase 2 = `init-web` (UI web de configuración), change aparte, NO diseñar acá.
6. **Lead capture Fase 1**: botones `mailto:` → davidlopezgamero@gmail.com (Google Form diferido a futuro). CTA de implementación con subject pre-armado.
7. **Landing trilingüe**: català · castellano · English, **3 versiones completas**; default castellano; single-file HTML, cero build, cero deps externas, diccionario JS + selector en header.
8. **Credibilidad**: sin testimonios inventados; solo "construido por un hostelero real" + open source + demo live. Sol de Nit nunca público.
9. **Landing live verificada**: https://davidlopezg.github.io/restauranteai/ (HTTP 200). Repo GitHub = `restauranteai` (local `restauranteia`). URL fija = la verificada.

## Criterios de aceptación

> Verificables y honestos. Todos deben cumplirse al cerrar el change.

- **CA-1** — `docs/index.html` es single-file trilingüe (català · castellano · English) con selector funcional en las 3 versiones y default castellano; sin dependencias externas ni build (verificación: navegación manual + grep sin CDNs externos).
- **CA-2** — "MVP-0.5" eliminado de la landing (verificación: grep sin coincidencias en `docs/index.html`).
- **CA-3** — Las **4 skills** reales (ficha, proceso_creativo, ideas_creativas, chat) están reflejadas con su nombre real en la landing (verificación: grep por las 4 keys/nombres).
- **CA-4** — CTA de implementación = `mailto:davidlopezgamero@gmail.com` con subject pre-armado (verificación: grep `href="mailto:`).
- **CA-5** — Sin testimonios inventados, sin "Sol de Nit", sin métricas falsas en landing/demo (verificación: grep + revisión de copy).
- **CA-6** — Sección demo con visual (iframe verificado o screenshot estático commiteado) y texto "demo con perfil genérico" (verificación: visual + `docs/` contiene el asset si aplica).
- **CA-7** — Seed demo (D1): boot sin TTY con `.agent_knowledge/` ausente → se crean `restaurante.json` (con `demo: true`, nombre de demostración, 15 dimensiones válidas) y `catalogo_platos.json` (8-12 platos) con schema docs; boot con archivos existentes → no se sobrescribe; boot TTY → init interactivo intacto (verificación: test unitario del seed + ejecución simulada no-TTY).
- **CA-8** — Indicador de perfil en el Space muestra "Demo: <nombre>" cuando el perfil es demo (verificación: manual en Space tras deploy + presencia del componente en `app.py`).
- **CA-9** — Tests verdes: `python scripts/test_app.py` (6/6), 120 tests de memoria, test del seed nuevo (verificación: comandos en apply/verify).
- **CA-10** — `requirements.txt` **sin cambios**; `memory/memory.md` documenta el stack real y la obsolescencia del combo 5.6 (verificación: `git diff` + grep en memory).
- **CA-11** — Landing live en https://davidlopezg.github.io/restauranteai/ tras push a `origin`; los cambios de `openspec/` no se pushean a `hf` (verificación: HTTP 200 + remotes).

## Impacto y riesgos

### Impacto

| Área | Archivos | Impacto |
|---|---|---|
| Landing | `docs/index.html` (reescritura total) | Superficie pública principal; cambio de copy completo. |
| App | `app.py` (seed no-TTY + indicador + description/link) | Deploy al Space vía `git push hf main` tras merge. |
| Datos demo | `agents/creativo/knowledge/demo_restaurante.json`, `demo_catalogo_platos.json` (nuevos) | Conocimiento estático trackeado; sin datos reales. |
| Tests | test del seed (nuevo); `scripts/test_app.py` solo si cambia un invariante | Cobertura del flujo no-TTY. |
| Docs | `memory/memory.md` (D5), `README.md` (menor, drift 3→4 skills) | Fuente de verdad de deps y de capacidades. |

**Rollback**: trivial y de bajo riesgo — no se tocan deps ni lógica del chef. Cada pieza es revertible por separado (`git revert`): la landing es HTML estático (revertir restaura la versión anterior al instante), el seed vive en un branch aislado del `__main__` no-TTY, y el indicador es un componente aditivo. Sin cambios de infraestructura.

### Riesgos (referencia R1-R11 de explore.md)

| # | Riesgo | Sev. | Mitigación en este change |
|---|---|---|---|
| R1 | Reintroducir deps de la era Gradio 5.6 | **Alta** | No tocar `requirements.txt` (CA-10); `test_app.py` vela por `huggingface_hub<1.0`; D5 documenta el stack real en memory. |
| R2 | Fuga de datos del restaurante real | **Alta** | Seed fuera de `.agent_knowledge/`, marcado `demo: true`, nombre de demostración; `.gitignore` intacto; sin "Sol de Nit" en ninguna superficie (CA-5); revisión de copy en review. |
| R3 | Persistencia efímera del filesystem en HF free | **Alta** | Seed reseedeado en cada boot (RF-13); copy honesto ("perfil demo precargado"); la venta de "tu restaurante" = instancia privada del cliente (servicio pago), no el demo público. |
| R4 | Landing desactualizada vs código | **Media** | D2 reescribe toda la landing con las 4 skills reales (CA-3); regla landing-realidad de memory. |
| R5 | Promesa falsa "el chef te conoce" en la demo | **Media** | D1 (perfil demo) + copy honesto en landing y `description` (RF-18); sin prometer "15 preguntas / recuerda para siempre" en el Space. |
| R6 | Romper invariantes de `test_app.py` | **Media** | D3 respeta firma de `responder()`, theme/css solo en `.launch()`, sin `type=` kwarg, ChatInterface dentro de Blocks; si algo cambia, el test se actualiza en el mismo commit (RF-19). |
| R7 | iframe de la demo bloqueado por Gradio 6 (CSP/X-Frame-Options) | **Media** | Verificación rápida al inicio de design; **fallback definido** = screenshot estático commiteado al repo (100% seguro). No bloquea el change (pregunta abierta Q2). |
| R8 | Cold starts del Space free (CPU basic duerme) | **Baja** | Copy discreto en la landing ("la primera visita puede tardar unos segundos en arrancar"); no bloquea venta (pregunta abierta Q4). |
| R9 | URL de GH Pages incierta | **Baja** | **Cerrada**: verificada live HTTP 200 en https://davidlopezg.github.io/restauranteai/ (decisión 9). |
| R10 | Push de `openspec/` a `hf` | **Baja** | Push solo a `origin`; `openspec/` jamás a `hf` (NFR-7, lección memory 2026-07-02). |
| R11 | Prueba social inexistente | **Baja** | Sin testimonios inventados; honestidad como feature de venta ("probá en 10 segundos, sin registro"); el prompt "40 restaurantes" es persona del prompt, nunca claim comercial. |

## Preguntas abiertas restantes

> Mínimas de verdad — la mayoría de las preguntas de explore.md quedaron cerradas por las decisiones 1-14. No quedan preguntas abiertas que bloqueen spec/design/tasks; las únicas decisiones de diseño (iframe vs screenshot) ya tienen preferencia y fallback definido.

### Cerradas en la ronda del proposal (2026-08-05, aprobado por David)

1. **Q1 — Idioma de la versión castellana**: **castellano neutro peninsular** (mercado real = Cataluña; objetivo = venta). El voseo queda solo para conversaciones internas con David (`userLanguage: es-AR` no aplica a superficies públicas).
2. **Q2 — Visual de la demo (R7)**: **intentar iframe** del Space al inicio de design; **fallback definido** = screenshot estático commiteado al repo. No bloquea.
3. **Q3 — Capturas (si screenshot)**: **2-3 capturas representativas** (ficha, proceso creativo, ideas) si el budget lo permite.
4. **Q4 — Cold start (R8)**: **sí**, incluir línea discreta en la landing ("la primera visita puede tardar unos segundos").
5. **Asunción validada**: la UI del **Space** queda **solo en castellano** en Fase 1; el trilingüe es exclusivo de la **landing**.

### Cerradas antes (no reabrir)

- Landing live verificada (decisión 9), init web → Fase 2, lead capture = mailto, sin testimonios, català en v1 completo (3 versiones), demo estática sin reconfiguración en sesión, modelo open core.

## Siguientes pasos

1. ✅ Proposal aprobado por David (2026-08-05) tras la ronda de preguntas (decisiones 10-14).
2. **`sdd-spec`** (siguiente fase): convertir RF-1..RF-21 y CA-1..CA-11 en spec del change `producto-vendible`.
3. **`sdd-design`**: arrancar con el spike de verificación del iframe (R7), elegir componente del indicador (sin romper `test_app.py`), definir el dict de idiomas y el subject exacto del mailto, y el contenido de los JSON demo (valores de `init_options.json`).
4. **`sdd-tasks` + `sdd-apply`**: orden sugerido por explore: seed demo → indicador UI → landing → tests → memory/README → bump `VERSION` (v1.3.0 → v1.4.0 + tag, decisión de delivery en apply) si aplica.
5. **`sdd-verify`**: `python scripts/test_app.py`, 120 tests de memoria, test del seed, verificación manual trilingüe y del Space.
6. **`sdd-sync` + `sdd-archive`**: push a `origin` (Pages live) + `git push hf main` (Space). `openspec/` nunca a `hf`.
7. **Fase 2 (change `init-web`)**: proposal propio con su ronda de preguntas de producto (web config UI). La landing ya enmarca "tu restaurante" como servicio de implementación que incluirá ese config web.

---

## Proposal question round

> Esta fase corre en modo interactivo, pero el executor no tiene UI interactiva en esta sesión. En lugar de bloquear, dejo acá la ronda de preguntas propuesta y las **asunciones** tomadas, para que David las revise/corrija antes de dar por finalizado el proposal. Tras las respuestas, se resumirán las asunciones ajustadas y se podrá pedir una segunda ronda si hace falta.

**Preguntas (4, de producto — no de harness):**

- **Q1 — Voseo vs neutro**: la landing actual usa voseo (es-AR, consistente con `userLanguage: es-AR`). El mercado real de David es catalán/peninsular. ¿Mantenemos voseo en la versión castellana o pasamos a español neutro? *(Asunción: mantengo voseo salvo que David pida neutro.)*
- **Q2 — Visual de la demo**: ¿preferís iframe del Space (demo viva; verificar rápido si Gradio 6 lo permite) o screenshot estático (100% estable, sin dependencia del Space)? *(Asunción: intentar iframe, verificar al inicio de design, fallback screenshot.)*
- **Q3 — Capturas de demo (si screenshot)**: ¿una captura del modo ficha o 2-4 capturas representativas de los modos (ficha, proceso creativo, ideas, chat)? *(Asunción: 2-3 capturas representativas si el budget lo permite.)*
- **Q4 — Cold start (R8)**: ¿incluimos una línea discreta en la landing ("la primera visita puede tardar unos segundos") por el sleep del Space free, o lo dejamos fuera? *(Asunción: incluir línea discreta.)*

**Asunciones tomadas sin confirmar (para revisión):** la UI del Space se mantiene en castellano en v1 (solo la landing es trilingüe); el perfil demo es estático por sesión (sin reconfiguración en el navegador, eso es Fase 2); `requirements.txt` no se toca; el indicador de perfil es un componente aditivo que no cambia la firma de `responder()`; la oferta de implementación es la vía de monetización (open core) y el CTA es mailto con subject pre-armado.
