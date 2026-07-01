---
title: Chef Creativo — RestaurantEAI
emoji: 🍂
colorFrom: red
colorTo: yellow
sdk: gradio
sdk_version: 6.19.0
python_version: '3.11'
app_file: app.py
pinned: false
license: mit
short_description: "Chef IA: fichas y proceso creativo"
---

# 🍂 Chef Creativo — RestaurantEAI

> Estado: **MVP-3** — Chef Creativo con 3 skills (ficha + proceso creativo + ideas creativas), conocimiento del restaurante y carta inyectados automáticamente. Deployado en Hugging Face Spaces. End-to-end con la API oficial de MiniMax.

**¿Qué es?** Ecosistema de agentes IA para restauración. El **Chef Creativo** ofrece tres modos, todos con conocimiento automático de tu restaurante (ticket, línea culinaria, carta) y catálogo de platos:

1. 🍂 **Ficha técnica** — Una petición → ficha estructurada (nombre, historia, ficha técnica, maridaje, prompt de imagen).
2. 🧠 **Proceso creativo** — State machine de 7 fases que muestra **cómo piensa el chef** paso a paso, con persistencia entre sesiones y comandos para iterar.
3. 💡 **Ideas creativas** — 10 ideas variadas para explorar (renovar carta, ideas de temporada, llenar huecos), con refinamiento vía métodos creativos de ElBulli.

**¿Cómo se usa?** Abrí el chat, elegí el modo en el selector de arriba a la izquierda, y escribí tu petición.

- **Modo Ficha**: `"Entrante vegetariano con calabaza y queso de cabra"`
- **Modo Proceso creativo**: `"Risotto de setas con trufa"` y avanzás fase por fase
- **Modo Ideas creativas**: `"Ideas para otoño"` y recibís 10 ideas iterables

*(Abajo: documentación técnica completa, diagrama de flujo, cómo correrlo local, estructura, decisiones de diseño.)*

---

## 📑 Tabla de contenidos

1. [Estado del proyecto](#estado-del-proyecto)
2. [Diagrama de flujo](#diagrama-de-flujo)
3. [Quick start (local)](#quick-start-local)
4. [Sistema de skills](#sistema-de-skills)
5. [Proceso creativo (state machine)](#proceso-creativo-state-machine)
6. [Ideas creativas](#ideas-creativas)
7. [Fase init — carga de conocimiento del restaurante](#fase-init--carga-de-conocimiento-del-restaurante)
8. [Arquitectura técnica](#arquitectura-técnica)
9. [Despliegue (HF Space)](#despliegue-hf-space)
10. [Repos y remotes](#repos-y-remotes)
11. [Roadmap](#roadmap)

> 📖 **¿Buscás un comando específico?** Mirá [`docs/COMMANDS.md`](docs/COMMANDS.md) — índice completo de entry points, comandos in-session, scripts, y paths importantes.

---

## Estado del proyecto

| Hito | Estado | Notas |
|---|---|---|
| MVP-0: Agente Chef Creativo (CLI local) | ✅ | Validado end-to-end |
| MVP-0.5: Deploy en Hugging Face Space | ✅ | https://huggingface.co/spaces/davidlopezgamero/RestaurantEAI |
| MVP-1: Landing page | ✅ | `docs/index.html` |
| MVP-1.1: Sistema de skills | ✅ | 3 skills: ficha, proceso_creativo, ideas_creativas |
| MVP-2: Proceso creativo con state machine | ✅ | 7 fases + persistencia + comandos |
| MVP-3: Ideas creativas | ✅ | 10 ideas + iteración con métodos ElBulli + ficha |
| Conocimiento automático del restaurante | ✅ | restaurante.json + catalogo_platos.json inyectados al chef |
| Opciones del init externalizadas | ✅ | `agents/init_options.json` + "otra (escribir)" en CLI |
| Init con carta completa | ✅ | LLM extrae el catálogo desde texto libre |
| Fix estructural de idioma | ✅ | Detección + reintento automático si chef responde en inglés |
| Fix de surrogate UTF-8 | ✅ | Encoding correcto de emoji en payload |
| Fase 4: Agente de Memoria / CRM | ⏳ | Próximo |
| Resto de agentes (Producción, Marketing, etc.) | ⏳ | Backlog |
| SaaS + monetización | ⏳ | Cuando haya tracción real |

---

## Diagrama de flujo

El diagrama de flujo completo del sistema (init phase, 3 skills, persistencia, detección de idioma, destinos) está en [`docs/FLOW.md`](docs/FLOW.md). Es un diagrama Mermaid — abrílo en [mermaid.live](https://mermaid.live/) o cualquier visor Mermaid para verlo renderizado.

**Resumen del flujo en una línea**: Init phase (carga restaurante + carta) → Knowledge inyectado automáticamente en cada skill → 3 skills disponibles (ficha / proceso creativo / ideas creativas) → Detección de idioma con reintentos → Deploy a HF Space + backup en GitHub.


## Quick start (local)

### 1. Requisitos

- Python 3.11 (recomendado — HF Space usa 3.11)
- Una API key de **MiniMax**
- 5 minutos

### 2. Instalación

```bash
git clone https://github.com/davidlopezg/restauranteai.git
cd restauranteai

python -m venv .venv
source .venv/bin/activate   # En Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### 3. Configurar credenciales

```bash
cp .env.example .env
nano .env
```

Variables:
- `MINIMAX_API_KEY` → tu clave privada de MiniMax
- `MINIMAX_BASE_URL` → `https://api.minimax.io/v1` (default)
- `MINIMAX_MODEL` → `MiniMax-M3` (default)

### 4. Inicializar el agente (solo la primera vez)

```bash
python -m agents.init_phase
```

Te hace 15 preguntas sobre el restaurante + te permite pegar tu carta/menú completo (recomendado) o meter los platos uno a uno. Genera `.agent_knowledge/restaurante.json` y `.agent_knowledge/catalogo_platos.json`.

### 5. Probar las 3 skills

**Modo interactivo** (selector de skill al inicio):

```bash
python -m agents.creativo.agent
```

**Ficha rápida**:

```bash
python -m agents.creativo.agent "Risotto de setas con trufa"
```

**Proceso creativo**:

```bash
python -m agents.creativo.agent pc "Risotto de setas con trufa"
python -m agents.creativo.agent pc --reanudar SESION_ID
```

**Ideas creativas**:

```bash
python -m agents.creativo.agent ideas "Ideas para otoño"
```

---

## Sistema de skills

El Chef Creativo tiene un **sistema de skills extensible**. Cada skill tiene su propio system prompt + comportamiento.

### Skills disponibles

| Key | Nombre | Cuándo usarla | Comandos especiales |
|---|---|---|---|
| `ficha` | Ficha técnica | Ya sabés qué ficha querés | (ninguno, one-shot) |
| `proceso_creativo` | Proceso creativo | Querés ver el razonamiento paso a paso con persistencia | `/estado`, `/fase N`, `/volver`, `/ficha`, `/reiniciar`, `/sesiones`, `/reanudar` |
| `ideas_creativas` | Ideas creativas | Querés **explorar** 10 ideas antes de comprometerte | `más ideas`, `aplicá [método] a la idea N`, `ficha de la idea N`, `ver métodos` |

### Cómo elegir skill

**En la UI web**: selector Radio en la parte superior del chat (automático con 3 opciones).

**En CLI**: el `modo_interactivo` te pregunta al inicio, y podés cambiar con `/skill` en cualquier momento.

### Cómo agregar una skill nueva

1. Crear `agents/creativo/prompts/system_<nombre>.md` con el system prompt.
2. Agregar el dict en la lista `SKILLS` de `agents/creativo/skills.py`:

```python
{
    "key": "mi_skill",
    "nombre": "Mi skill",
    "descripcion": "Qué hace esta skill",
    "prompt_path": PROMPTS_DIR / "system_mi_skill.md",
    "ejemplos": ["ejemplo 1", "ejemplo 2"],
}
```

3. (Opcional) Si la skill necesita comportamiento custom, agregar handler en `agent.py` + integrarla en `app.py`.
4. Commit + push.

---

## Proceso creativo (state machine)

La skill `proceso_creativo` es un **proceso iterativo de 7 fases** con persistencia en disco.

### Las 7 fases

| # | Fase | Qué trabaja el chef |
|---|---|---|
| 1 | Alma del plato | Qué evoca, qué recuerdo, qué estación, qué producto |
| 2 | Métodos creativos | 2-3 métodos específicos de ElBulli + propios, y por qué aplican |
| 3 | Equilibrio | Análisis dulce/salado/ácido/amargo/umami/graso |
| 4 | Técnica | Qué procesos potencian el producto sin enmascararlo |
| 5 | Storytelling | Qué historia va a contar el plato |
| 6 | Descartadas | 2-3 alternativas evaluadas con por qué no |
| 7 | Preguntas | Cosas que preocupan + 1 pregunta concreta si falta info |

Cuando las 7 fases están OK, el chef genera la **ficha final** integrando todo.

### Comandos

| Comando | Qué hace |
|---|---|
| `siguiente` o cualquier mensaje | Trabaja la fase actual y avanza |
| `/estado` | Ver progreso de las 7 fases |
| `/fase N` o `/fase nombre` | Saltar a una fase específica |
| `/volver` | Regenerar la fase actual |
| `/ficha` | Generar ficha final |
| `/ficha forzar` | Generar aunque falten fases |
| `/reiniciar` | Volver al inicio con la misma petición |
| `/salir` | Terminar y guardar sesión |
| `/sesiones` | Listar sesiones guardadas |
| `/reanudar ID` | Retomar sesión |

### Persistencia

- Sesiones en `.agent_knowledge/sessions/<id>.json` (privado, en `.gitignore`)
- Cerrás y abrís después → `/reanudar ID` seguís donde quedaste
- ID formato: `YYYYMMDD-HHMMSS-<8 chars random>`

---

## Ideas creativas

La skill `ideas_creativas` es una **exploración conversacional**: 10 ideas variadas → refinamiento → ficha opcional.

### El flujo

```
➤ Ideas para otoño
[chef genera 10 ideas variadas: platos, conceptos, formatos, extensiones]

➤ aplicá deconstrucción a la idea 3
[chef refina + 3-5 variaciones]

➤ más ideas
[chef genera 10 ideas NUEVAS distintas]

➤ ficha de la idea 5
[chef convierte en ficha técnica completa]

➤ ver métodos
[chef lista los 13 métodos creativos disponibles]
```

### Características

- **Considera siempre**: tipo de restaurante (ticket, sofisticación, productos, técnicas), carta actual (no duplicar, llenar huecos), estación.
- **Diversidad**: mezcla plato, concepto, técnica, formato, extensión, rompedor.
- **Estado en memoria**: las ideas viven mientras la sesión está activa. No persisten a disco todavía.

### Métodos creativos disponibles (de ElBulli + propios)

1. **Lo autóctono** — tradición culinaria local
2. **Influencias externas** — cocinas de otros lugares
3. **Búsqueda técnico-conceptual** — técnicas y conceptos nuevos
4. **Los sentidos** — vista, olfato, tacto, oído, gusto
5. **El sexto sentido** — emociones, ironía, recuerdos
6. **Simbiosis dulce/salado** — intercambio entre mundos
7. **Productos comerciales** — usar formatos de snacks, golosinas
8. **Deconstrucción** — disgregar elementos, modificar textura/temperatura
9. **Minimalismo** — mínimo de elementos, máxima magia
10. **Asociación** — combinar tablas de productos/técnicas
11. **Inspiración** — tomar una referencia (arte, naturaleza) como apoyo
12. **Adaptación** — revisar clásicos bajo nueva filosofía
13. **Sinergia** — todos los métodos interactúan entre sí

---

## Fase init — carga de conocimiento del restaurante

La fase init se corre **una sola vez** (o cuando quieras actualizar datos). Recolecta el contexto del restaurante y lo guarda en `.agent_knowledge/`.

### Lo que se recolecta

- **15 preguntas del restaurante** (ticket, sofisticación, productos, técnicas, etc.) — opciones externalizadas en `agents/init_options.json`.
- **Catálogo de platos** (3 modos):
  1. **Pegar carta/menú completo** (recomendado): el LLM extrae JSON estructurado.
  2. **Manual**: uno por uno.
  3. **Saltar**: catálogo vacío.

### Lo que el chef recibe automáticamente

Cada vez que genera una ficha o trabaja una fase, el system prompt se enriquece con:

1. **Contexto del restaurante** (restaurante.json):
   - Nombre, ticket medio (min/max/típico), sofisticación
   - Productos dominantes, técnicas dominantes, tipo de servicio
   - Política de grupos, clases de comedores, origen/inspiración
   - Orientación nutricional, localización, restricciones religiosas
   - Tiempo del comensal, época/estilo

2. **Catálogo de platos** (catalogo_platos.json, max 30 inyectados):
   - Agrupados por categoría
   - Con nombre, descripción, precio

3. **Estacionalidad Cataluña** (cuando la petición menciona un ingrediente)

4. **System prompt de la skill** (system_chef.md, system_proceso_creativo.md, system_ideas_creativas.md)

### Cómo lo usa el chef

- **NO propone** platos que contradigan el ticket o la sofisticación del restaurante
- **NO duplica** platos del catálogo actual
- **SÍ sugiere** complementos y extensiones de la línea
- **SÍ respeta** la época/estilo (pizzería italiana, mediterránea moderna, etc.)
- **SÍ avisa** si la petición contradice el contexto

---

## Arquitectura técnica

### Estructura del proyecto

```
restauranteia/
├── agents/
│   ├── creativo/                       # Agente Chef Creativo
│   │   ├── agent.py                    # Entry point CLI + handlers de las 3 skills
│   │   ├── skills.py                   # Registry de skills (extensible)
│   │   ├── proceso_creativo.py         # State machine de 7 fases + persistencia
│   │   ├── sessions.py                 # CRUD de sesiones en .agent_knowledge/
│   │   ├── prompts/
│   │   │   ├── system_chef.md          # System prompt de la skill 'ficha'
│   │   │   ├── system_proceso_creativo.md
│   │   │   └── system_ideas_creativas.md
│   │   └── knowledge/
│   │       ├── estacionalidad.json     # Calendario de temporada Cataluña
│   │       └── combinaciones_clasicas.csv
│   ├── init_phase.py                   # Fase init: 15 preguntas + carta
│   ├── init_options.json               # Opciones externalizadas (JSON editable)
│   └── knowledge_context.py            # Archivos compartidos entre agentes
├── docs/
│   ├── index.html                      # Landing page
│   ├── metodos-creativos.md            # Referencia métodos creativos ElBulli
│   └── COMMANDS.md                     # Índice de comandos y scripts
├── memory/
│   └── memory.md                       # Decisiones de arquitectura y aprendizaje
├── conversations/                      # Historial de sesiones de chat
├── scripts/
│   ├── test_app.py                     # Tests de regresión de app.py
│   └── probar_estructura.py            # Validación sin API
├── .agent_knowledge/                   # Generado, NO commitear
│   ├── restaurante.json                # Datos del init
│   ├── restaurante.md
│   ├── catalogo_platos.json            # Carta extraída
│   ├── catalogo_platos.md
│   └── sessions/                       # Sesiones del proceso creativo
├── .env.example                        # Plantilla de variables de entorno
├── requirements.txt
├── README.md
└── DEPLOY_HF.md                        # Notas específicas del deploy
```

### Decisiones de diseño

**Skills en lugar de un solo prompt gigante**: cada skill tiene su propio system prompt optimizado para su caso de uso.

**State machine para el proceso creativo**: en lugar de "responder y listo", el chef trabaja **una fase por turno**, con el sistema trackeando qué se completó.

**Persistencia en `.agent_knowledge/`**: knowledge base del restaurante (preferencias, contexto, sesiones) vive fuera del repo.

**Contexto del restaurante + catálogo inyectado automáticamente**: el chef nunca pierde de vista la línea del restaurante ni la carta actual.

**Opciones del init externalizadas**: editar `agents/init_options.json` para extender opciones sin tocar código.

**Init con carta completa**: LLM extrae el catálogo desde texto libre (con robustez: JSON puro, markdown JSON, texto alrededor, normalización de campos).

**Fix estructural de idioma**: `call_minimax` detecta si la respuesta salió en inglés (heurística de palabras gatillo + exclusión de "PROMPT PARA IMAGEN"). Si detecta, **reformula con instrucción reforzada y baja temperatura**, hasta 2 reintentos.

**Fix de surrogate UTF-8**: emoji y caracteres especiales se encodean correctamente con `\U0001F3A8` (no `\ud83c\udfa8` que produce surrogates inválidos).

### Cómo extender

- **Agregar skill**: ver "Cómo agregar una skill nueva" arriba
- **Agregar pregunta al init**: editar `agents/init_options.json`
- **Agregar fase al proceso creativo**: editar `FASES` en `agents/creativo/proceso_creativo.py`
- **Agregar método creativo**: agregar a `METODOS_CREATIVOS` en `agents/creativo/agent.py`
- **Agregar agente nuevo**: crear `agents/<nombre>/agent.py` siguiendo el patrón del chef

---

## Despliegue (HF Space)

El Space vive en: **https://huggingface.co/spaces/davidlopezgamero/RestaurantEAI**

### Frontmatter del README

El frontmatter YAML arriba (entre `---`) lo lee Hugging Face. NO modificar a mano sin saber qué hace cada campo:
- `sdk: gradio`, `sdk_version: 6.19.0` — versión del framework UI
- `python_version: '3.11'` — obligatorio (HF default = 3.13 que rompe Gradio)
- `app_file: app.py` — entry point
- `short_description` — aparece en el catálogo (**siempre entre comillas si contiene `:`**)

### Variables de entorno en HF

Configurar en **Settings → Repository secrets**:
- `MINIMAX_API_KEY` (obligatoria)
- `MINIMAX_BASE_URL` (opcional)
- `MINIMAX_MODEL` (opcional)

### Push al Space

```bash
git push hf main
```

(Si nunca se hizo, agregar remote: `git remote add hf https://huggingface.co/spaces/davidlopezgamero/RestaurantEAI`)

---

## Repos y remotes

| Remote | URL | Push | Notas |
|---|---|---|---|
| `origin` | `https://github.com/davidlopezg/restauranteai.git` | `git push origin main` | Repo de código fuente |
| `hf` | `https://huggingface.co/spaces/davidlopezgamero/RestaurantEAI` | `git push hf main` | Space deployado (rebuild automático) |

### Alias para pushear a ambos

```bash
git config alias.pushall '!git push hf main && git push origin main'
```

Después: `git pushall` sincroniza los dos remotes en un comando.

⚠️ **Si divergen** (caso típico: pusheaste desde otra máquina), el push falla. Solución:

```bash
git pull --rebase origin main
git pushall
```

Para forzar sincronización de HF con local (irreversible):

```bash
git push --force-with-lease=main:<hash-actual-de-hf> hf main
```

---

## Tests

```bash
python scripts/test_app.py        # Tests de regresión de app.py
python scripts/probar_estructura.py # Validación de estructura sin API
```

---

## Licencia

MIT. Ver `LICENSE` cuando se agregue formalmente.

## Contribuir

Por definir. El proyecto está en fase temprana.

---

## Links

- 🌐 **App en vivo**: https://huggingface.co/spaces/davidlopezgamero/RestaurantEAI
- 💻 **Código fuente**: https://github.com/davidlopezg/restauranteai
- 🏠 **Landing page**: `docs/index.html`

---

**Para preguntas, issues o ideas**: abrir un issue en GitHub.