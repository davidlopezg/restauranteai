---
title: Chef Creativo — RestaurantEAI
emoji: 🍂
colorFrom: orange
colorTo: red
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
license: mit
short_description: Generador de fichas creativas de platos con IA
---

# 🍂 Chef Creativo — RestaurantEAI

> Estado: **MVP-0.5** — Agente Chef Creativo deployado en Hugging Face Spaces con UI Gradio. Funciona end-to-end con la API oficial de MiniMax.

**¿Qué es?** Generador de fichas culinarias con IA. Pedime un plato en lenguaje natural y te devuelvo una ficha estructurada: nombre evocador, historia, ficha técnica, maridaje sugerido y prompt para generar la imagen del plato.

**¿Cómo se usa?** Escribí tu petición en el chat de abajo. Algunos ejemplos para arrancar:

- *"Entrante vegetariano con calabaza y queso de cabra"*
- *"Postre con chocolate y aceite de oliva"*
- *"Principal de carne para menú degustación de 7 pasos"*

*(Abajo encontrás la documentación técnica del proyecto — cómo correrlo local, estructura de archivos, decisiones de diseño.)*

---

## 🛠️ Documentación técnica (para devs)

Sistema multi-agente de IA especializado en hostelería, inspirado en proyectos como Gentleman AI / CrewAI / AutoGen, pero con **conocimiento real del sector restauración** aplicado verticalmente.

## Estado actual

- ✅ Repo inicializado
- ✅ Estructura de carpetas
- ✅ **MVP-0: Agente Chef Creativo** (script local + system prompt, validado end-to-end)
- 🔄 **MVP-0.5: Despliegue público en Hugging Face Space** (código listo, pendiente deploy)
- ⏳ Fase 1: Agente de Memoria / CRM
- ⏳ Fase 2: Resto de agentes (Producción, Marketing, Recepción, Financiero)
- ⏳ Fase 3: SaaS + monetización

## Quick start (MVP-0)

### 1. Requisitos

- Python 3.10 o superior
- Una API key de **MiniMax** (el proveedor de este modelo)
- 5 minutos de tu tiempo

### 2. Instalación

```bash
# Clonar el repo (cuando esté en GitHub)
git clone https://github.com/[usuario]/restaurante-ai.git
cd restaurante-ai

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate   # En Windows: .venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Configurar credenciales

```bash
# Copiar plantilla de variables de entorno
cp .env.example .env

# Editar .env con tus valores reales
nano .env  # o tu editor favorito
```

Valores a rellenar:
- `MINIMAX_API_KEY` → tu clave privada de MiniMax
- `MINIMAX_BASE_URL` → endpoint base (ej: `https://api.minimax.chat/v1`)
- `MINIMAX_MODEL` → nombre del modelo a invocar

> ⚠️ **Si no sabés el endpoint exacto de MiniMax**, consultá la documentación oficial de MiniMax o contactá a su soporte. NO asumas un endpoint inventado.

### 4. Probar el Chef Creativo

**Modo interactivo** (recomendado para probar):

```bash
python -m agents.creativo.agent
```

Luego escribís peticiones como:
```
➤ Quiero un entrante vegetariano con calabaza, queso de cabra y avellanas, que evoque otoño
➤ Un postre con chocolate y aceite de oliva
➤ Principal de carne para menú degustación de 7 pasos
```

**Modo de una sola consulta**:

```bash
python -m agents.creativo.agent "Risotto de setas con trufa, para noche de gala"
```

## Estructura del proyecto

```
restauranteia/
├── agents/
│   └── creativo/              # Agente Chef Creativo (MVP-0)
│       ├── agent.py           # Script principal ejecutable
│       ├── prompts/
│       │   └── system_chef.md # Personalidad del chef
│       └── knowledge/
│           ├── estacionalidad.json  # Calendario de temporada Cataluña
│           └── combinaciones_clasicas.csv  # Maridajes y contrastes probados
├── memory/
│   └── memory.md              # Aprendizaje del agente
├── conversations/             # Historial de sesiones (futuro)
├── scripts/                   # Utilidades (futuro)
├── .env.example               # Plantilla de variables de entorno
├── requirements.txt           # Dependencias
└── README.md                  # Este archivo
```

## Lo que hace el Chef Creativo (MVP-0)

Toma una petición en lenguaje natural y devuelve una ficha estructurada con:

- 🍂 **Nombre del plato** (evocador, 2-4 palabras)
- 📝 **Historia / storytelling** (por qué este plato, qué evoca)
- 📋 **Ficha técnica** (ingredientes para 4 raciones + elaboración resumida)
- 🍷 **Maridaje sugerido** (con justificación técnica)
- 🎨 **Prompt para imagen** (en inglés, listo para DALL-E / Stable Diffusion)

**Lo que NO hace todavía** (y por qué):

- ❌ **Coste numérico por ración**: depende de tu mercado local y relaciones con proveedores. El chef solo da rango orientativo (€ a €€€€€).
- ❌ **Validación de alérgenos**: eso es responsabilidad del restaurante, no del agente.
- ❌ **Generación de imagen real**: solo da el prompt. La generación la hace otra herramienta (DALL-E, etc.) que vos decidís cuándo integrar.
- ❌ **Persistencia / memoria entre sesiones**: cada consulta es independiente. La memoria entre sesiones viene en MVP-0.5.

## Próximos pasos (no commits, solo roadmap mental)

1. **MVP-0 validado por vos** (5-10 prompts de prueba, ajustar system prompt si hace falta).
2. **MVP-0.5**: Levantar en Hugging Face Spaces con Gradio → chat público sin instalar nada.
3. **MVP-1**: GitHub Pages con HTML propio que conecte al Space.
4. **Fase 2**: Empezar Agente de Memoria (el siguiente más sencillo).
5. **Fase 3**: Empezar a plantear modelo SaaS (cuando haya tracción real, no antes).

## Licencia

MIT (a confirmar cuando se decida). Ver `LICENSE` cuando se añada.

## Contribuir

Por definir. Este proyecto está en fase muy temprana — antes de aceptar contribuciones externas, hace falta tener el MVP validado y documentar el flujo de contribución.

---

**Para preguntas, issues o ideas**: abrir un issue en GitHub cuando el repo esté público.