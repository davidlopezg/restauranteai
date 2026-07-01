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
short_description: Chef IA: fichas y proceso creativo
---

# 🍂 Chef Creativo — RestaurantEAI

> Estado: **MVP-2** — Chef Creativo con sistema de skills (ficha + proceso creativo por fases). Deployado en Hugging Face Spaces. End-to-end con la API oficial de MiniMax.

**¿Qué es?** Ecosistema de agentes IA para restauración. Empezamos con el **Chef Creativo**, que ahora ofrece dos modos:

1. 🍂 **Ficha técnica** — Generador clásico: una petición → ficha estructurada (nombre, historia, ficha técnica, maridaje, prompt de imagen).
2. 🧠 **Proceso creativo** — State machine de 7 fases que muestra **cómo piensa el chef** paso a paso (alma, métodos creativos elBulli, equilibrio, técnica, storytelling, alternativas descartadas, preguntas), con persistencia entre sesiones y comandos para iterar.

**¿Cómo se usa?** Abrí el chat, elegí el modo en el selector de arriba a la izquierda, y escribí tu petición.

- **Modo Ficha**: `"Entrante vegetariano con calabaza y queso de cabra"`
- **Modo Proceso creativo**: `"Risotto de setas con trufa, para noche de gala"` y vas avanzando fase por fase

*(Abajo encontrás documentación técnica completa: cómo correrlo local, estructura, decisiones de diseño, skills, proceso creativo.)*

---

## 📑 Tabla de contenidos

1. [Estado del proyecto](#estado-del-proyecto)
2. [Quick start (local)](#quick-start-local)
3. [Sistema de skills](#sistema-de-skills)
4. [Proceso creativo (state machine)](#proceso-creativo-state-machine)
5. [Arquitectura técnica](#arquitectura-técnica)
6. [Despliegue (HF Space)](#despliegue-hf-space)
7. [Repos y remotes](#repos-y-remotes)
8. [Roadmap](#roadmap)

---

## Estado del proyecto

| Hito | Estado | Notas |
|---|---|---|
| MVP-0: Agente Chef Creativo (CLI local) | ✅ | Validado end-to-end |
| MVP-0.5: Deploy en Hugging Face Space | ✅ | https://huggingface.co/spaces/davidlopezgamero/RestaurantEAI |
| MVP-1: Landing page | ✅ | `docs/index.html` (lista para GitHub Pages) |
| MVP-1.1: Sistema de skills | ✅ | 2 skills: ficha + proceso_creativo |
| MVP-2: Proceso creativo con state machine | ✅ | 7 fases + persistencia + comandos de iteración |
| Opciones del init externalizadas | ✅ | `agents/init_options.json` + "otra (escribir)" en CLI |
| Fix estructural de idioma | ✅ | Detección + reintento automático si chef responde en inglés |
| Fase 3: Agente de Memoria / CRM | ⏳ | Próximo |
| Resto de agentes (Producción, Marketing, etc.) | ⏳ | Backlog |
| SaaS + monetización | ⏳ | Cuando haya tracción real |

## Quick start (local)

### 1. Requisitos

- Python 3.11 (recomendado — HF Space usa 3.11)
- Una API key de **MiniMax** (el proveedor de este modelo)
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
nano .env  # editar con tus valores
```

Variables:
- `MINIMAX_API_KEY` → tu clave privada de MiniMax
- `MINIMAX_BASE_URL` → `https://api.minimax.io/v1` (default verificado contra doc oficial)
- `MINIMAX_MODEL` → `MiniMax-M3` (default)

### 4. Probar el Chef Creativo

**Modo interactivo** (selector de skill al inicio):

```bash
python -m agents.creativo.agent
```

**Ficha rápida desde CLI**:

```bash
python -m agents.creativo.agent "Risotto de setas con trufa"
```

**Proceso creativo desde CLI**:

```bash
# Con petición inicial
python -m agents.creativo.agent pc "Risotto de setas con trufa"

# Reanudando sesión guardada
python -m agents.creativo.agent pc --reanudar 20260701-233625-ee198745

# Interactivo (te pide la petición en el primer input)
python -m agents.creativo.agent pc
```

---

## Sistema de skills

El Chef Creativo tiene un sistema de **skills extensible**. Cada skill es una capacidad especializada con su propio system prompt.

### Skills disponibles

| Key | Nombre | Descripción |
|---|---|---|
| `ficha` | Ficha técnica | Genera la ficha estructurada del plato |
| `proceso_creativo` | Proceso creativo | State machine de 7 fases, con persistencia |

### Cómo elegir skill

**En la UI web**: selector Radio en la parte superior del chat.

**En CLI**: el `modo_interactivo` te pregunta al inicio, y podés cambiar con `/skill` en cualquier momento.

### Cómo agregar una skill nueva

1. Crear el archivo del system prompt en `agents/creativo/prompts/system_<nombre>.md`
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

3. Commit + push. La skill aparece automáticamente en la UI y en el CLI.

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

### Comandos disponibles

| Comando | Qué hace |
|---|---|
| `siguiente` o cualquier mensaje | Trabaja la fase actual y avanza |
| `/estado` | Ver progreso de las 7 fases |
| `/fase N` o `/fase nombre` | Saltar a una fase específica (ej: `/fase 3` o `/fase equilibrio`) |
| `/volver` | Regenerar la fase actual |
| `/ficha` | Generar ficha final (auto cuando estén todas) |
| `/ficha forzar` | Generar aunque falten fases |
| `/reiniciar` | Volver al inicio con la misma petición |
| `/sesiones` | Listar sesiones guardadas |
| `/reanudar ID` | Retomar una sesión anterior |
| `/skill` o `/skills` | Cambiar de skill |
| `salir` | Terminar y guardar sesión |

### Persistencia

Cada sesión se guarda en `.agent_knowledge/sessions/<id>.json`. Esto es:

- **Privado** (directorio en `.gitignore`)
- **Cerrable y reanudable**: cerrás el chat, abrís después, `/reanudar ID` y seguís donde quedaste
- **Histórico**: podés revisar procesos creativos viejos con `/sesiones`

Formato del ID: `YYYYMMDD-HHMMSS-<8 chars random>` (ej: `20260701-233625-ee198745`).

---

## Arquitectura técnica

### Estructura del proyecto

```
restauranteia/
├── agents/
│   ├── creativo/                       # Agente Chef Creativo
│   │   ├── agent.py                    # Entry point CLI + modo_interactivo
│   │   ├── skills.py                   # Registry de skills (extensible)
│   │   ├── proceso_creativo.py         # State machine de 7 fases + persistencia
│   │   ├── sessions.py                 # CRUD de sesiones en .agent_knowledge/
│   │   ├── prompts/
│   │   │   ├── system_chef.md          # System prompt de la skill 'ficha'
│   │   │   └── system_proceso_creativo.md
│   │   └── knowledge/
│   │       ├── estacionalidad.json     # Calendario de temporada Cataluña
│   │       └── combinaciones_clasicas.csv
│   ├── init_phase.py                   # Fase init: 15 preguntas del restaurante
│   ├── init_options.json               # Opciones externalizadas (JSON editable)
│   └── knowledge_context.py            # Archivos compartidos entre agentes
├── docs/
│   ├── index.html                      # Landing page (MVP-1)
│   └── metodos-creativos.md            # Referencia métodos creativos elBulli
├── memory/
│   └── memory.md                       # Decisiones de arquitectura y aprendizaje
├── conversations/                      # Historial de sesiones
├── scripts/
│   └── test_app.py                     # Tests de regresión de app.py
├── .agent_knowledge/                   # Generado, NO commitear
│   ├── restaurante.json
│   ├── restaurante.md
│   ├── catalogo_platos.json
│   ├── catalogo_platos.md
│   └── sessions/                       # Sesiones del proceso creativo
├── .env.example                        # Plantilla de variables de entorno
├── requirements.txt
├── README.md
└── DEPLOY_HF.md                        # Notas específicas del deploy
```

### Decisiones de diseño

**Skills en lugar de un solo prompt gigante**: cada skill tiene su propio system prompt, optimizado para su caso de uso. Permite extender capacidades sin tocar código de UI.

**State machine para el proceso creativo**: en lugar de "responder y listo", el chef trabaja **una fase por turno**, con el sistema trackeando qué se completó. Permite iterar (`/volver`, `/fase N`) y reanudar sesiones.

**Persistencia en `.agent_knowledge/`**: la knowledge base del restaurante (preferencias, contexto, sesiones) vive fuera del repo, en `.gitignore`. Lo que se commitea es el código y la configuración general.

**Opciones del init externalizadas**: las opciones de las 15 preguntas del init viven en `agents/init_options.json`. Editar el JSON para extender, sin tocar código. Además, en el CLI el sistema ofrece automáticamente "otra (escribir)" al final de cada lista.

**Fix estructural de idioma**: `call_minimax` detecta si la respuesta salió en inglés (heurística de palabras gatillo + exclusión de la sección "PROMPT PARA IMAGEN"). Si detecta, **reformula con instrucción reforzada y baja temperatura** automáticamente, hasta 2 reintentos.

### Cómo extender

- **Agregar skill**: ver sección "Cómo agregar una skill nueva"
- **Agregar pregunta al init**: editar `agents/init_options.json`
- **Agregar fase al proceso creativo**: editar `FASES` en `agents/creativo/proceso_creativo.py`
- **Agregar agente nuevo**: crear `agents/<nombre>/agent.py` siguiendo el patrón del chef

---

## Despliegue (HF Space)

El Space vive en: **https://huggingface.co/spaces/davidlopezgamero/RestaurantEAI**

### Frontmatter del README

El frontmatter YAML arriba (entre `---`) lo lee Hugging Face. NO modificar a mano sin saber qué hace cada campo:
- `sdk: gradio`, `sdk_version: 6.19.0` — versión del framework UI
- `python_version: '3.11'` — obligatorio (HF default = 3.13 que rompe Gradio)
- `app_file: app.py` — entry point
- `short_description` — aparece en el catálogo

### Variables de entorno en HF

Configurar en **Settings → Repository secrets** del Space:
- `MINIMAX_API_KEY` (obligatoria)
- `MINIMAX_BASE_URL` (opcional, default `https://api.minimax.io/v1`)
- `MINIMAX_MODEL` (opcional, default `MiniMax-M3`)

### Push al Space

```bash
git push hf main
```

(Si nunca se hizo, agregar remote: `git remote add hf https://huggingface.co/spaces/davidlopezgamero/RestaurantEAI`)

### Por qué Gradio y no Streamlit

Gradio es el estándar en Hugging Face Spaces. Tiene mejor integración con el ecosistema HF (OAuth, Spaces, etc.) y `gr.ChatInterface` es muy simple para chatbots.

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
git pull --rebase origin main   # si divergencia con GitHub
git pushall
```

Para forzar sincronización de HF con local (irreversible):

```bash
git push --force-with-lease=main:<hash-actual-de-hf> hf main
```

---

## Tests

```bash
python scripts/test_app.py
```

Verifica:
- Sintaxis de `app.py`
- No usar kwargs deprecados de Gradio 6.19+
- Firma correcta de `responder()` para ChatInterface
- Estructura del `gr.Blocks` con `gr.ChatInterface` adentro

---

## Licencia

MIT. Ver `LICENSE` cuando se agregue formalmente.

## Contribuir

Por definir. El proyecto está en fase temprana — antes de aceptar contribuciones externas, hace falta documentar el flujo de contribución en `CONTRIBUTING.md`.

---

## Links

- 🌐 **App en vivo**: https://huggingface.co/spaces/davidlopezgamero/RestaurantEAI
- 💻 **Código fuente**: https://github.com/davidlopezg/restauranteai
- 🏠 **Landing page**: `docs/index.html` (lista para GitHub Pages)

---

**Para preguntas, issues o ideas**: abrir un issue en GitHub.