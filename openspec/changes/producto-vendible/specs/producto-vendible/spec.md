# Spec — producto-vendible

> Change: `producto-vendible` · Fase: `sdd-spec` · Proyecto: `restauranteia`
> Base: `openspec/changes/producto-vendible/proposal.md` (APROBADO 2026-08-05, decisiones 1-14 cerradas) + `openspec/changes/producto-vendible/explore.md` (evidencia)
> Convención: no existe spec canónico en `openspec/specs/` ni spec en `openspec/changes/archivo-de-ideas/`; este spec es **spec completo de dominio nuevo** que archive copiará a `openspec/specs/producto-vendible/spec.md`.
> Requerimientos en RFC 2119 (MUST / SHOULD / MAY). Cada RF conserva su ID del proposal para trazabilidad.

## Propósito

Hacer vendible la primera capa del producto (Chef Creativo / RestaurantEAI) sin cambiar la lógica del chef ni las dependencias: (D2) landing trilingüe single-file orientada a conversión con oferta open core, (D1) perfil demo genérico seedeado en el Space que reemplaza el perfil vacío actual, (D3) polish honesto de la app Gradio, y (D5) documentación del stack real de dependencias. Todo con infraestructura 100% gratis (GitHub Pages + HF Space) y cero datos reales en superficies públicas.

## Requisitos funcionales

### Landing trilingüe (D2)

#### RF-1 — Single-file y zero-deps

`docs/index.html` MUST ser un único archivo HTML autocontenido servible desde GitHub Pages (`main` + `/docs`): sin CDNs, sin fuentes externas, sin build step; CSS y JS inline en vanilla (system-ui, sin librerías). No MAY contener `<script src=`, `<link rel="stylesheet">` con URLs externas, `@import` remoto ni `url(http…)` hacia recursos de terceros. Los únicos enlaces externos permitidos son los tres destinos aprobados: Space HF, repositorio GitHub y `mailto:`.

**Verificación:** `grep -nE "<script[^>]*src=|<link[^>]*stylesheet[^>]*href=|<style>@import|url\(https?://" docs/index.html` → 0 coincidencias; navegación manual en Pages.

#### RF-2 — Trilingüe completo (català · castellano · English)

`docs/index.html` MUST contener **3 versiones completas del mismo contenido** (català, castellano, English), gestionadas por un diccionario JS (patrón `data-i18n` o equivalente) y un selector en el header. Sub-requisitos:

- **RF-2.1 — Diccionario JS**: el diccionario de idiomas MUST incluir las 3 versiones de **todos** los strings visibles (hero, skills, demo, oferta, FAQ, footer, CTAs, selector, aviso de cold start). No se permite texto visible fuera del diccionario (verificación: recorrido manual de cada sección en cada idioma).
- **RF-2.2 — Selector en el header**: MUST existir un selector visible con exactamente 3 opciones: `català · castellano · English`, con el idioma activo marcado. El cambio de idioma MUST re-renderizar todo el contenido sin recarga de página (verificación: manual en las 3 opciones).
- **RF-2.3 — `lang` / `title` / `meta` por idioma**: el atributo `lang` del `<html>`, el `<title>` y el `<meta name="description">` MUST actualizarse al idioma activo (`ca`/`es`/`en`; default inicial `es`). Los `og:` MUST ser coherentes con el default castellano (verificación: manual + inspección del DOM tras cada cambio de idioma).
- **RF-2.4 — Default castellano**: ante cualquier carga sin interacción previa, el contenido visible MUST ser la versión castellana completa, independientemente del `Accept-Language` del navegador (verificación: manual con navegador en català/English configurados).

**Verificación:** CA-1 + navegación manual trilingüe.

#### RF-3 — Hero problema→solución

El hero MUST abrir con el dolor del comprador no técnico (p. ej. "¿renovar la carta te lleva semanas? ¿los platos nuevos no sorprenden?") y MUST resolverlo con la propuesta del Chef Creativo (pensar cada plato con la carta y el ticket del restaurante en mente). MUST tener CTA primario → demo (Space HF) y CTA secundario → oferta de implementación. El hero MUST eliminar la jerga interna: el badge "MVP-0.5" queda prohibido (ver RF-9).

**Verificación:** revisión de copy + CA-2.

#### RF-4 — Las 4 skills reales

La sección "Qué hace el chef" (o equivalente) MUST reflejar las **4 skills reales del registry** (`agents/creativo/skills.py`) con su `nombre` exacto y una descripción fiel a su `descripcion`:

| key | nombre (obligatorio en la landing) |
|---|---|
| `ficha` | Ficha técnica |
| `proceso_creativo` | Proceso creativo |
| `ideas_creativas` | Ideas creativas |
| `chat` | Chat con el chef |

Cada skill MUST describir solo lo que el código hace (regla memory 2026-07-02: nunca prometer capacidades inexistentes).

**Verificación:** `grep -n "Ficha técnica\|Proceso creativo\|Ideas creativas\|Chat con el chef" docs/index.html` → 4 coincidencias (una por skill, en las 3 versiones del diccionario) + CA-3.

#### RF-5 — Sección demo con visual

La landing MUST mostrar la demo de forma **visual**, no solo con texto. Decisión de diseño (Q2 cerrada): intentar **iframe** del Space primero; si el embedding no funciona, **fallback obligatorio** a screenshot(s) estático(s) commiteado(s) al repo. Sub-requisitos:

- **RF-5.1 — Spike del iframe en design**: al inicio de `sdd-design` MUST verificarse si `https://huggingface.co/spaces/davidlopezgamero/RestaurantEAI` permite embedding (respuesta HTTP 200 + ausencia de bloqueo por `X-Frame-Options`/`frame-ancestors`). Este spike determina iframe vs screenshot; no bloquea el change.
- **RF-5.2 — Fallback screenshot**: si el iframe no carga (riesgo R7), el change MUST commitear 2-3 capturas representativas (ficha, proceso creativo, ideas) como assets estáticos en `docs/` y usarlas en la sección demo. Las capturas MUST NO contener datos reales ni "Sol de Nit".
- **RF-5.3 — Texto explícito de demo genérica**: la sección demo MUST declarar explícitamente "demo con perfil genérico de restaurante mediterráneo, marcada como demo" (verificación: grep de "genéric"/"mediterráne" en `docs/index.html`).
- **RF-5.4 — Aviso de cold start**: MUST incluir una línea discreta de que la primera visita al Space puede tardar unos segundos en arrancar (riesgo R8, Q4 cerrada).

**Verificación:** CA-6 + manual (iframe cargando o `ls docs/` con los assets) + header check del Space.

#### RF-6 — Oferta open core + CTA mailto

La landing MUST incluir una sección de oferta que explique el modelo open core: "el software es gratis, código abierto (MIT); si querés que **tu** restaurante quede configurado y funcionando, lo hacemos por vos (implementación paga)". El CTA MUST ser `mailto:davidlopezgamero@gmail.com` con parámetro `subject=` **pre-armado y no vacío** en las 3 versiones del diccionario (p. ej. "Quiero el Chef Creativo en mi restaurante"; el subject MAY variar por idioma, el destinatario MUST ser siempre el mismo). Sin testimonios inventados: solo "construido por un hostelero real" + open source + demo live.

**Verificación:** `grep -n 'mailto:davidlopezgamero@gmail.com' docs/index.html` → ≥1 por versión + inspección del parámetro `subject=` (CA-4).

#### RF-7 — FAQ / objeciones

La landing MUST incluir una sección FAQ de 4-6 preguntas/objeciones reales del comprador no técnico, con respuestas honestas. Ejemplos exigidos en contenido (traducidos a cada idioma): "¿Necesito saber programar? No — la implementación la hacemos nosotros"; "¿Cuánto tarda la demo? Está online, probala"; "¿Y mis datos? La demo usa un perfil de ejemplo; tu restaurante vive en tu instancia privada".

**Verificación:** revisión de copy + conteo manual de ítems FAQ.

#### RF-8 — Footer honesto

El footer MUST incluir: enlace a GitHub, enlace al Space HF, licencia MIT, y "construido por un hostelero real (David López Gamero) · Cataluña, 2026". El footer MUST NO mencionar "Sol de Nit", ni datos reales, ni "MVP-0.5", ni métricas inventadas.

**Verificación:** CA-5 + revisión de copy.

#### RF-9 — Honestidad total (claims verificables)

Ningún claim de la landing MAY prometer algo que el código no hace. El copy de "el chef te conoce / 15 preguntas / recuerda para siempre" queda reemplazado por lo que la demo realmente hace: perfil demo precargado; la personalización real por restaurante es parte del servicio de implementación. La cadena "MVP-0.5" MUST estar ausente de todo `docs/` (verificación: `grep -rn "MVP-0.5" docs/` → 0 coincidencias, CA-2).

**Verificación:** CA-2 + CA-5 + revisión de copy contra `agents/creativo/skills.py` y `app.py`.

### Seed demo genérico (D1)

#### RF-10 — Archivos seed trackeados fuera de `.agent_knowledge/`

Los seeds MUST vivir en archivos JSON nuevos **trackeados** en `agents/creativo/knowledge/`: `demo_restaurante.json` y `demo_catalogo_platos.json` (carpeta de conocimiento estático del agente). MUST NO modificarse `.gitignore` y MUST NO commitearse nada dentro de `.agent_knowledge/` (frontera de privacidad del patrón template→instancia).

**Verificación:** `git status`/`git ls-files` → los 2 JSON en `agents/creativo/knowledge/`, cero archivos en `.agent_knowledge/`; `.gitignore` sin cambios (`git diff .gitignore`).

#### RF-11 — Perfil demo válido contra el schema

`demo_restaurante.json` MUST contener:

- **Las 15 dimensiones de `PREGUNTAS_RESTAURANTE`** (`agents/init_phase.py`) con valores **válidos** del set correspondiente en `agents/init_options.json` (fuente de verdad; fallback: opciones hardcoded de `init_phase.py`), para que los mapeos de `formatear_restaurante_para_chef()` resuelvan bien. Perfil canon confirmado en el proposal (decisión 4 + Q1 cerrada):
  - `precio_target_min` / `precio_target_max` / `precio_target_moda`: números (canon: 25 / 60 / 40, ticket medio)
  - `sofisticacion`: `"media"`
  - `productos_dominantes`: MUST incluir `["vegetales", "pescado", "mariscos"]` (subconjunto válido)
  - `epoca_estilo`: MUST incluir `"mediterranea_moderna"` (subconjunto válido)
  - El resto de dimensiones (tecnicas_dominantes, tipo_servicio, grupos, clases_comedores, origen_inspiracion, orientacion_nutricional, localizacion, religion, tiempo_preparacion) MUST tomar valores válidos coherentes con un perfil mediterráneo de ticket medio (valores exactos: decisión de diseño dentro del set válido).
- **`"demo": true`** (marca legible por el indicador de UI, RF-14).
- **`"nombre"` explícito de demostración**: `"Restaurante de demostración"` (puede variar la traducción/redacción solo si design lo justifica, pero MUST ser inequívocamente un nombre de demostración, nunca un restaurante real).

**Verificación:** test unitario del seed (RF-15) + revisión de los valores contra `agents/init_options.json`.

#### RF-12 — Catálogo demo

`demo_catalogo_platos.json` MUST ser una lista de **8-12 platos**, cada uno con las keys `nombre` / `categoria` / `descripcion` / `precio` (schema de `PREGUNTAS_POR_PLATO`). `categoria` MUST pertenecer al set válido `{entrante, principal, postre, guarnicion, bebida, otro}`. Los platos MUST ser coherentes con el perfil mediterráneo de ticket medio (sin ingredientes exóticos fuera de línea). `precio` MUST ser un número positivo coherente con el rango de ticket medio (o `null` si design decide mantener el campo opcional del schema).

**Verificación:** test unitario del seed (RF-15).

#### RF-13 — Copia en boot sin TTY (idempotente, sin sobrescribir)

En `app.py`, bloque `__main__`, la lógica de bootstrap MUST quedar así:

- Si `bootstrap_necesario()` es `False` → no hacer nada (init completo).
- Si hay TTY (`sys.stdin.isatty()` True) → `fase_init_interactiva()` **sin cambios** (flujo CLI intacto; los seeds NO se copian).
- Si **no** hay TTY (HF Space / CI) → leer `demo_restaurante.json` y `demo_catalogo_platos.json` desde `agents/creativo/knowledge/` y copiar **por archivo faltante** a `.agent_knowledge/` usando `guardar_restaurante(...)` / `guardar_catalogo(...)` con los schema docs companion (`_schema_doc_restaurante()`, `_schema_doc_catalogo()`). El invariante de no-sobrescritura: un archivo destino que **ya existe** MUST permanecer intacto (solo se escriben los archivos faltantes — `bootstrap_necesario()` es True si falta cualquiera de los dos). MUST loggearse que se usó el perfil demo.
- Como el filesystem de HF free es efímero (riesgo R3), el reseed MUST repetirse en cada boot no-TTY (comportamiento idempotente, no un flag persistente).

**Verificación:** test unitario del seed (RF-15) con simulación no-TTY + CA-7.

#### RF-14 — Marca demo legible por la UI

El indicador de perfil (RF-16) MUST derivar su estado del `restaurante.json` cargado:

| Estado del perfil cargado | Texto del indicador |
|---|---|
| `demo == true` | `Demo: <nombre>` (p. ej. "Demo: Restaurante de demostración") |
| sin perfil / perfil vacío `{}` | `(sin contexto)` |
| perfil real (`demo` ausente o `false`) | `<nombre>` del restaurante real |

**Verificación:** manual en Space tras deploy (CA-8) + lectura del componente en `app.py`.

#### RF-15 — Test unitario del seed

El change MUST incluir un test unitario nuevo (p. ej. `scripts/test_seed_demo.py`; nombre a fijar en design) que, sin red y sin API:

1. Valide que `demo_restaurante.json` tiene las 15 dimensiones con valores en los sets válidos de `init_options.json`, `"demo": true` y nombre de demostración.
2. Valide que `demo_catalogo_platos.json` tiene 8-12 platos con las keys obligatorias y categorías válidas.
3. Valide el invariante de no-sobrescritura: con archivos destino ya presentes, el flujo de seed no-TTY los deja intactos.

**Verificación:** `python scripts/test_seed_demo.py` → exit 0 (CA-9).

### App polish (D3)

#### RF-16 — Indicador de perfil

La UI del Space MUST mostrar un indicador de estado del perfil como componente visible dentro de `with gr.Blocks()` (p. ej. `gr.Markdown` ubicado antes del ChatInterface, junto al selector de skill), con los estados de RF-14. El indicador MUST NO tocar `theme=`/`css=` del constructor de Blocks (invariante `test_kwarg_prohibidos`: theme/css solo en `.launch()`).

**Verificación:** CA-8 + `grep -n "Demo" app.py` + `python scripts/test_app.py`.

#### RF-17 — Link a la landing

El Space MUST mostrar un enlace visible a la landing `https://davidlopezg.github.io/restauranteai/` (hoy el Space no enlaza a nada). Implementación sugerida: `gr.HTML`/`gr.Markdown` con `<a href="https://davidlopezg.github.io/restauranteai/" target="_blank">`; el link MAY convivir con el indicador de perfil en el mismo componente.

**Verificación:** manual en Space tras deploy + lectura de `app.py`.

#### RF-18 — Copy de `description` alineado a venta

El `description` del `gr.ChatInterface` MUST mencionar los **4 modos reales** (selector de skill) y el **perfil demo precargado**. El copy MUST NO prometer "15 preguntas" ni "recuerda para siempre" (falso en el Space efímero, riesgo R5). La UI del Space se mantiene en castellano (decisión 14 — el trilingüe es exclusivo de la landing).

**Verificación:** revisión de `app.py` + manual en Space (CA-8).

#### RF-19 — Invariantes de la app intactos

El change MUST mantener: firma `responder(mensaje, historial, skill="ficha") -> dict`; `theme=`/`css=` solo en `.launch()`; `cache_examples=False`; ChatInterface dentro de Blocks; sin kwarg `type=` en ChatInterface/Chatbot. Si algún cambio toca un invariante, `scripts/test_app.py` MUST actualizarse en el mismo commit.

**Verificación:** `python scripts/test_app.py` → 6/6 (CA-9) + `git diff` del commit.

### Deps / documentación (D5)

#### RF-20 — `memory/memory.md` documenta el stack real

`memory/memory.md` MUST recibir una entrada que fije: stack vigente = `gradio>=6.19,<7.0` + `huggingface_hub>=1.2,<2.0` + Python 3.11, sin pins de `pydantic`/`jinja2`; `requirements.txt` y el frontmatter del README son la fuente de verdad; el combo de la era Gradio 5.6 (`gradio>=5.6,<6.0`, `huggingface_hub<1.0`, `pydantic==2.10.6`, `jinja2<3.1.0`) quedó **obsoleto** (riesgo R1) y reintroducirlo rompe Gradio 6 y `test_app.py`; se conservan como vigentes las lecciones estructurales de la deploy saga (Python 3.11 obligatorio, `cache_examples=False`, defensa en profundidad).

**Verificación:** `grep -n "6.19\|Gradio 6\|5.6" memory/memory.md` → entrada presente + `git diff requirements.txt` → vacío (CA-10).

#### RF-21 — (Menor) Drift README 3→4 skills

El README MUST corregir el drift documental "3 skills" → "4 skills" (incluye `chat`) si el budget de review lo permite; si no, queda anotado como pendiente para el change `init-web`. Este requisito es SHOULD (menor, honestidad documental, ~5 líneas).

**Verificación:** `grep -n "4 skills\|3 skills" README.md` + nota en la PR si queda pendiente.

## Escenarios

### Scenario: La landing abre en castellano por defecto

- GIVEN un visitante en `https://davidlopezg.github.io/restauranteai/` con navegador configurado en català o English
- WHEN el navegador carga la página sin interacción previa
- THEN el contenido visible es la versión castellana completa (RF-2.4)
- THEN el selector del header muestra las 3 opciones `català · castellano · English` con castellano marcado como activo
- THEN `document.documentElement.lang` es `es` y el `<title>` / `<meta name="description">` están en castellano (RF-2.3)

### Scenario: Cambio de idioma a català

- GIVEN la landing cargada en castellano
- WHEN el visitante selecciona "català" en el selector
- THEN todo el contenido visible (hero, skills, demo, oferta, FAQ, footer, aviso de cold start) cambia a la versión catalana completa, sin recarga (RF-2.1, RF-2.2)
- THEN `lang`/`title`/`meta description` pasan a `ca`
- THEN los CTAs conservan sus destinos (Space HF y mailto)

### Scenario: Cambio de idioma a English

- GIVEN la landing cargada en castellano
- WHEN el visitante selecciona "English"
- THEN todo el contenido visible cambia a la versión inglesa completa, sin recarga
- THEN `lang`/`title`/`meta description` pasan a `en`

### Scenario: El visitante abre la demo

- GIVEN la landing cargada (cualquier idioma)
- WHEN el visitante hace clic en el CTA primario de la demo
- THEN se abre (o se embebe) el Space `https://huggingface.co/spaces/davidlopezgamero/RestaurantEAI`
- THEN el texto adjunto declara que la demo usa un perfil genérico de restaurante mediterráneo marcado como demo (RF-5.3)
- THEN una línea discreta avisa que la primera visita puede tardar unos segundos en arrancar (RF-5.4)
- THEN (si aplica fallback) el asset screenshot commiteado se muestra en lugar del iframe (RF-5.2)

### Scenario: El visitante pide la implementación

- GIVEN la landing cargada (cualquier idioma)
- WHEN el visitante hace clic en el CTA de la oferta open core
- THEN se abre el cliente de correo con destinatario `davidlopezgamero@gmail.com` y `subject=` pre-armado no vacío (RF-6)
- THEN el copy de la oferta aclara que el software es gratis (MIT) y que la implementación del restaurante del cliente es un servicio pago

### Scenario: El Space arranca sin knowledge base (no-TTY)

- GIVEN un boot del Space HF (sin TTY) con `.agent_knowledge/` ausente (`bootstrap_necesario() == True`)
- WHEN `app.py` ejecuta el bloque `__main__`
- THEN se crean `.agent_knowledge/restaurante.json` y `.agent_knowledge/catalogo_platos.json` a partir de los seeds (RF-13)
- THEN `restaurante.json` contiene las 15 dimensiones válidas + `"demo": true` + `"nombre": "Restaurante de demostración"` (RF-11)
- THEN `catalogo_platos.json` contiene 8-12 platos válidos (RF-12)
- THEN se escriben los schema docs companion `restaurante.md` y `catalogo_platos.md` (RF-13)
- THEN se loggea que se usó el perfil demo
- THEN el indicador de la UI muestra `Demo: Restaurante de demostración` (RF-14, RF-16)

### Scenario: El Space arranca con archivos existentes (no-TTY)

- GIVEN un boot no-TTY con `restaurante.json` o `catalogo_platos.json` ya presente (`bootstrap_necesario() == True` por el archivo faltante)
- WHEN `app.py` ejecuta el bloque `__main__`
- THEN los archivos existentes NO se sobrescriben (RF-13)
- THEN solo se copia desde el seed el archivo faltante
- THEN el indicador refleja el perfil existente (demo o real) o `(sin contexto)` si el archivo está vacío (RF-14)

### Scenario: Boot TTY local (init interactivo intacto)

- GIVEN un boot local con terminal (`sys.stdin.isatty() == True`) y `bootstrap_necesario() == True`
- WHEN `python app.py` se ejecuta
- THEN corre `fase_init_interactiva()` sin cambios (15 preguntas + catálogo) (RF-13)
- THEN los seeds demo NO se copian
- THEN el indicador (perfil real sin `demo`) muestra el nombre real del restaurante (RF-14)

### Scenario: La landing refleja las 4 skills reales

- GIVEN la landing cargada (cualquier idioma)
- WHEN el visitante revisa la sección de capacidades del chef
- THEN aparecen las 4 skills con su nombre real: Ficha técnica, Proceso creativo, Ideas creativas, Chat con el chef (RF-4)
- THEN cada descripción coincide con lo que `agents/creativo/skills.py` declara que hace la skill

### Scenario: Sin "MVP-0.5" en la landing

- GIVEN `docs/index.html`
- WHEN se busca la cadena "MVP-0.5"
- THEN no hay coincidencias (RF-9, CA-2)

### Scenario: Sin "Sol de Nit" ni datos reales en superficies públicas

- GIVEN `docs/index.html` y los seeds demo (`agents/creativo/knowledge/demo_*.json`)
- WHEN se busca "Sol de Nit" (case-insensitive) y nombres de restaurantes reales
- THEN no hay coincidencias en la landing ni en los JSON demo (RF-8, RF-10, CA-5, NFR-2)

## Criterios de aceptación

Mapa CA-1..CA-11 del proposal → requisitos del spec + verificación concreta:

| CA | Criterio (proposal) | Requisitos | Verificación |
|---|---|---|---|
| CA-1 | Single-file trilingüe, selector funcional en 3 versiones, default castellano, sin deps/build | RF-1, RF-2 (2.1-2.4) | Navegación manual en las 3 versiones + `grep -nE "<script[^>]*src=|<link[^>]*stylesheet[^>]*href=|url\(https?://" docs/index.html` → 0 |
| CA-2 | "MVP-0.5" eliminado de la landing | RF-9 | `grep -rn "MVP-0.5" docs/` → 0 coincidencias |
| CA-3 | Las 4 skills reales con su nombre real | RF-4 | `grep -n "Ficha técnica\|Proceso creativo\|Ideas creativas\|Chat con el chef" docs/index.html` → 4 coincidencias |
| CA-4 | CTA implementación = `mailto:davidlopezgamero@gmail.com` con subject pre-armado | RF-6 | `grep -n 'mailto:davidlopezgamero@gmail.com' docs/index.html` + inspección de `subject=` (no vacío) en las 3 versiones |
| CA-5 | Sin testimonios inventados, sin "Sol de Nit", sin métricas falsas | RF-8, RF-9, NFR-1 | `grep -rni "sol de nit" docs/ agents/creativo/knowledge/` → 0 + revisión de copy en review |
| CA-6 | Sección demo con visual (iframe o screenshot commiteado) + texto perfil genérico | RF-5 (5.1-5.3) | Manual (iframe cargando) o `ls docs/` con assets screenshot + `grep -ni "genéric\|mediterráne" docs/index.html` |
| CA-7 | Seed demo: boot no-TTY crea archivos válidos con schema docs; no sobrescribe existentes; TTY intacto | RF-10..RF-13 | `python scripts/test_seed_demo.py` (incluye simulación no-TTY) |
| CA-8 | Indicador de perfil muestra "Demo: \<nombre\>" cuando demo | RF-14, RF-16 | Manual en Space tras deploy + `grep -n "Demo" app.py` |
| CA-9 | Tests verdes: `test_app.py` 6/6, 120 tests memoria, test seed | RF-15, RF-19, NFR-4 | `python scripts/test_app.py` + suite memoria (comando en README, 120 tests) + `python scripts/test_seed_demo.py` |
| CA-10 | `requirements.txt` sin cambios; memory documenta stack real y obsolescencia del combo 5.6 | RF-20 | `git diff requirements.txt` → vacío + `grep -n "6.19\|5.6" memory/memory.md` |
| CA-11 | Landing live HTTP 200 tras push a `origin`; `openspec/` no se pushea a `hf` | NFR-7 | `curl -sI https://davidlopezg.github.io/restauranteai/` → 200 + push: `git push origin main` y `git push hf main` solo con archivos de app (nunca `openspec/`) |

## No-funcionales

- **NFR-1 — Honestidad como invariante**: nada en landing/demo/copy que el código no haga (regla memory 2026-07-02). Todo claim MUST verificarse contra `agents/creativo/skills.py` y `app.py` antes de escribirse. La persona del prompt ("40 restaurantes asesorados") no puede usarse como claim comercial.
- **NFR-2 — Privacidad**: cero datos reales en template, landing, demo o Space público; seed marcado `"demo": true`; `.agent_knowledge/` MUST seguir en `.gitignore`; "Sol de Nit" nunca en superficies públicas (CA-5).
- **NFR-3 — Cero deps e infra gratis**: landing sin dependencias externas ni build; sin costos de hosting (GitHub Pages + HF Space free).
- **NFR-4 — Compatibilidad de la app**: `python scripts/test_app.py` 6/6 verde; suite de memoria (120 tests, comando en README) verde; test del seed nuevo verde (CA-9).
- **NFR-5 — Rendimiento**: HTML estático liviano, sin JS de terceros; único request externo posible = iframe del Space (opcional, con fallback definido).
- **NFR-6 — Accesibilidad básica**: contraste suficiente, HTML semántico, responsive (la landing actual ya es responsive; MUST mantenerse).
- **NFR-7 — Deploy**: push de `app.py` a `hf` (Space) y de `docs/` a `origin` (Pages); los archivos de `openspec/` MUST nunca pushearse a `hf` (riesgo R10, lección memory 2026-07-02).
- **NFR-8 — SEO básico**: `title`/`meta description`/`og:` coherentes (castellano default) y actualizados por idioma vía JS (RF-2.3).

## Fuera de alcance

- **Init web** (Fase 2, change `init-web`): UI web de configuración del restaurante. Se referencia solo para enmarcar la oferta de implementación.
- **Google Form / formularios de leads**: el canal de captura en Fase 1 es `mailto:`.
- **Hosting/dominio pago**, SaaS multi-tenant, multi-instancia pública.
- **Datos reales de Sol de Nit** o de cualquier restaurante real (jamás en template, landing, demo ni Space público).
- **Cambios a la lógica del chef**: prompts (`system_*.md`), skills, proceso creativo, handlers, dispatch, `agents/init_phase.py` (salvo lo que D1 reutiliza: `_schema_doc_*` y `init_options.json` como referencia de valores válidos), `agents/memoria/*`.
- **Cambios a `requirements.txt`** ni al frontmatter del README del Space.
- **Cambiar la firma de `responder()`** ni el formato ChatInterface/Chatbot (invariantes de `scripts/test_app.py`).
- **Reconfiguración del perfil demo por el visitante** durante su sesión (Fase 2).
- **Trilingüe en la UI del Space**: el Space permanece solo en castellano (decisión 14); el trilingüe aplica exclusivamente a la landing.

## Referencias

### Archivos que toca el change

| Archivo | Cambio | Área |
|---|---|---|
| `docs/index.html` | Reescritura total: single-file trilingüe orientado a conversión | D2 |
| `agents/creativo/knowledge/demo_restaurante.json` | Nuevo (seed, fuera de `.agent_knowledge/`) | D1 |
| `agents/creativo/knowledge/demo_catalogo_platos.json` | Nuevo (seed, 8-12 platos) | D1 |
| `app.py` | Seed no-TTY (RF-13) + indicador (RF-16) + link landing (RF-17) + `description` (RF-18) | D1/D3 |
| `scripts/test_seed_demo.py` (nuevo; nombre a fijar en design) | Test unitario del seed (RF-15) | D1 |
| `scripts/test_app.py` | Solo si cambia un invariante (RF-19, mismo commit) | D3 |
| `memory/memory.md` | Entrada stack real + obsolescencia combo 5.6 (RF-20) | D5 |
| `README.md` | Drift "3 skills" → "4 skills" (RF-21, menor, según budget) | D5 |
| `docs/*.{png,jpg}` (si aplica) | Capturas estáticas de la demo como fallback del iframe (RF-5.2) | D2 |

### Evidencia y fuentes

- `openspec/changes/producto-vendible/proposal.md` — RF-1..RF-21, CA-1..CA-11, decisiones 1-14, riesgos R1-R11 (aprobado 2026-08-05).
- `openspec/changes/producto-vendible/explore.md` — evidencia del estado actual y riesgos.
- `agents/creativo/skills.py` — registry de las 4 skills (fuente de verdad del copy de RF-4).
- `agents/init_phase.py` — `PREGUNTAS_RESTAURANTE` (15 dimensiones), `PREGUNTAS_POR_PLATO` (nombre/categoria/descripcion/precio), `_schema_doc_restaurante()` / `_schema_doc_catalogo()`.
- `agents/init_options.json` — sets de valores válidos (fuente de verdad de RF-11/RF-12).
- `agents/knowledge_context.py` — `bootstrap_necesario()`, `guardar_restaurante`/`guardar_catalogo`, paths de `.agent_knowledge/`.
- `app.py` — bloque `__main__` actual (vacíos + warning), UI Gradio, invariantes.
- `scripts/test_app.py` — 6 invariantes de regresión (RF-19, NFR-4).
- `.gitignore` — `.agent_knowledge/` excluido (frontera de privacidad, no tocar).
- `memory/memory.md` — regla landing-realidad (2026-07-02), deploy saga y lecciones (deps), no-push de `openspec/` a `hf`.
- `README.md` — frontmatter HF, patrón template→instancia, drift "3 skills", comando de la suite de memoria (120 tests).
- `VERSION` — `v1.3.0` (bumpeo a `v1.4.0` + tag: decisión de delivery en apply).
