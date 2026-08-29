# 🤖 Un chef IA que conoce tu carta (y la de tu competencia)

> **Blog post / dev.to / Medium cross-post**.
> **Autor**: David López Gamero · **Fecha**: 2026-08-29 · **Tags**: #ai #llm #restaurant #opensource
> **Demo**: [huggingface.co/spaces/davidlopezgamero/RestaurantEAI](https://huggingface.co/spaces/davidlopezgamero/RestaurantEAI) · **Repo**: [github.com/davidlopezgamero/restauranteai](https://github.com/davidlopezgamero/restauranteai)

---

> 🍂 *"Risotto cremoso de setas de temporada con trufa negra laminada al emplatar. La cremosidad del Carnaroli dialoga con el umami del boletus y los trompetas del Montseny; el Barolo joven envuelve sin imponerse."*

Eso lo escribió un agente IA. Pero no un agente genérico: uno que sabe que mi restaurante (o el tuyo, si lo configuras) es **mediterráneo de ticket 40 €**, que **no sirve sushi**, que el risotto **no debe competir con tu pasta del martes**, y que la trufa **se lamina al emplatar para preservar los aromáticos volátiles**.

Se llama **Chef Creativo**, es open source (MIT), y está deployado en Hugging Face Spaces. Probá la demo en 10 segundos — sin registro, sin instalación, sin tarjeta.

[→ Probar la demo](https://huggingface.co/spaces/davidlopezgamero/RestaurantEAI)

---

## El problema: renovar la carta no escala

Soy hostelero. Llevo años peleándome con la misma pregunta cada trimestre:

> *¿Qué plato nuevo pongo?*

El proceso clásico:

1. Pensar 2 horas qué quiero.
2. Anotar 3 ideas vagas.
3. Olvidarme por una semana.
4. Volver, repetir el paso 1.
5. Después de 3 meses, tener una idea a medio hacer.
6. Cocinar el prototipo 3 veces.
7. Cambiar dos cosas porque "no funciona".
8. Ponerla en carta sin convicción.
9. Que se venda regular.
10. Sacarla a los 2 meses.

**Renovar la carta me llevaba 2 meses y rara vez el resultado era memorable**. Y esto siendo cocinero — imagínate un hostelero que además tiene que gestionar sala, compras, personal y proveedores. El sprint creativo simplemente no entra en el calendario.

## La promesa: IA que **piensa** contigo, no que **sustituye** tu criterio

Los generadores de recetas con IA ya existen (GPT, Claude, etc.). Les pides "un risotto de setas" y te dan 5 opciones genéricas. El problema no es el LLM: **es que no conoce tu casa**.

Le pedí a GPT-4 un risotto de setas. Me dio esto:

> *Risotto de setas con parmesano y trufa...*

Genérico. No sabe que mi ticket medio es 40 €. No sabe que mi carta ya tiene una pasta con boletus. No sabe que la trufa laminada al emplatar es un gesto técnico que justifica subir el plato a la sección "degustación". No sabe que el Barolo joven marida mejor que el Barolo reserva para no matar el umami del plato.

**Un LLM genérico te da una receta. Un LLM con contexto te da una ficha para tu restaurante.**

## La arquitectura: skills + contexto inyectado

El Chef Creativo tiene **4 modos** (skills), cada una con su system prompt optimizado:

1. **🍂 Ficha técnica** — Una petición → ficha estructurada (nombre, historia, ficha técnica, maridaje, prompt de imagen).
2. **🧠 Proceso creativo** — State machine de 7 fases que muestra **cómo piensa el chef** paso a paso (alma → métodos creativos de ElBulli → equilibrio → técnica → storytelling → alternativas descartadas → preguntas).
3. **💡 Ideas creativas** — 10 ideas variadas para explorar (renovar carta, llenar huecos, ideas de temporada), refinables con métodos creativos (`aplicá deconstrucción a la idea 3`).
4. **💬 Chat con el chef** — Conversación libre sobre producto, técnica, carta, estacionalidad, proveedores.

Lo que las hace diferentes: **en cada respuesta, el system prompt se enriquece con tu contexto**:

- Las **15 dimensiones de tu restaurante** (ticket medio, sofisticación, productos dominantes, técnicas, época/estilo, religión, etc.).
- Tu **catálogo de platos** (para no duplicar, llenar huecos, sugerir extensiones de la línea).
- **Estacionalidad Cataluña** (cuando mencionas un ingrediente).
- Las **ideas que guardaste** en conversaciones previas (módulo de memoria SQLite local).

El chef no improvisa desde cero: **siempre trabaja sobre tu base**.

## El detalle que importa: el idioma

El modelo base ([MiniMax-M3](https://platform.minimax.io/docs/guides/models-intro), frontier multimodal con ventana de 1M tokens) a veces responde en inglés cuando le pides en español. Lo detectamos con una heurística de palabras gatillo y **reintentamos automáticamente con instrucción reforzada + temperatura 0.2** hasta 2 veces. Si sigue saliendo mezclado, lo loggeamos y devolvemos igual — pero la tasa de éxito es >95% en la práctica.

Pequeño detalle, enorme diferencia para el usuario.

## El módulo de memoria: el chef no olvida

Otra pieza clave: cuando el chef dice algo que querés recordar, lo guardás con `/guardar`. Cuando querés revisar, `/ideas`. Cuando ya no aplica, `/olvidar`. Todo en SQLite local con WAL, RGPD desde el día uno (borrado granular con confirmación, export a JSON, sin telemetría).

```text
➤ Ideas para renovar los principales en otoño
[chef genera 10 ideas variadas]

➤ /guardar 5
✅ Idea #5 guardada: "Lubina a la brasa con salsa verde de perejil y avellana"

➤ /ideas
#1 | sin categoría | 2026-08-15
> Lubina a la brasa con salsa verde de perejil y avellana
#2 | sin categoría | 2026-08-15
> Probar boniato con chimichurri de avellanas
...

➤ ficha de la idea 1
[chef convierte la idea en ficha técnica completa con tu contexto]
```

La idea #5 va a aparecer como contexto cuando le preguntes al chef cualquier cosa sobre lubina. La memoria **no es un cuaderno**: es **input para las próximas conversaciones**.

## El modelo open core: por qué software gratis

Hay dos modelos extremos:

1. **SaaS cerrado** (JPM-style): cobro mensual, código cerrado, los datos viven en mis servidores, te vas si dejás de pagar.
2. **Open source puro**: código gratis, sin modelo de negocio, el maintainer se quema en 6 meses.

El Chef Creativo usa **open core**:

- **El software es gratis y open source (MIT)**. Lo podés clonar, leer, modificar, deployar en tu propia infraestructura. Sin "features premium" escondidas.
- **La monetización es por servicio de implementación**. Si querés esto funcionando en tu restaurante con **tu** carta y **tu** contexto configurados, te lo implementamos. Sin suscripción mensual, sin vendor lock-in.

Es el modelo que mejor se ajusta al comprador target: hosteleros/chefs no técnicos que quieren usar IA sin convertirse en devs.

## Lo que NO es

Por honestidad (regla del proyecto: nunca prometer lo que el código no hace):

- **No es multi-tenant**: el Space público tiene un único perfil demo. Tu restaurante real necesita una instancia privada (el servicio de implementación).
- **No persiste entre cold starts**: el HF Space free duerme los procesos. Si configurás algo en la demo, se pierde al rato. Por eso la instancia privada.
- **No es un sustituto del cocinero**: es una herramienta de brainstorming acelerado. La decisión final es tuya. La idea final la cocinás vos. El plato lo pruebas vos.
- **No tiene testimonio de clientes todavía**: está en MVP-3 desde hace 2 meses, con un perfil demo. Los primeros usos serios se están haciendo ahora.

## El stack

Por si te interesa la parte técnica:

- **LLM**: [MiniMax API](https://platform.minimax.io) (modelo `MiniMax-M3`, ventana 1M tokens, modo OpenAI-compatible).
- **UI**: Gradio 6.19 (single-file Python) sobre Hugging Face Spaces.
- **Almacenamiento de conocimiento del restaurante**: JSON en `.agent_knowledge/` (generado por fase init).
- **Memoria del proyecto** (Archivo de Ideas): SQLite con WAL mode, schema de 9 columnas, 11 comandos transversales, detección de duplicados (exacta + fuzzy ≥80%), RGPD desde el día uno.
- **Lenguaje de prompts**: castellano neutro peninsular (con recordatorio reforzado al final de cada mensaje del usuario para evitar drift a inglés).
- **Tests**: 132 tests pytest + 6 checks de regresión de la UI + 5 checks del seed demo = **143 invariantes automatizadas**. CI en GitHub Actions con Python 3.11.

## Cómo lo pruebo en 10 segundos

1. Abrí [la demo](https://huggingface.co/spaces/davidlopezgamero/RestaurantEAI).
2. Elegí un modo arriba a la izquierda (Ficha técnica es el más directo).
3. Escribí tu petición (ej: *"Risotto de setas con trufa, para noche de gala"*).
4. El chef genera una ficha coherente con el perfil demo genérico (mediterráneo, ticket 40 €).

La primera visita puede tardar 30 segundos en arrancar (HF Space free duerme los procesos). Después es instantáneo.

## ¿Y si quiero configurarlo con MI restaurante?

Acá entra el modelo open core:

- **Si te animás con la terminal**: `git clone`, `pip install`, `python -m agents.init_phase` (15 preguntas), `python app.py`. Listo.
- **Si preferís que te lo dejemos funcionando**: [escribime](mailto:davidlopezgamero@gmail.com?subject=Quiero%20el%20Chef%20Creativo%20en%20mi%20restaurante) y armamos un presupuesto. La configuración inicial lleva 2-4 horas de trabajo remoto + 1 sesión de 1 hora con vos para alinear.

(Próximamente: UI web de configuración en el navegador, sin terminal — está en el [roadmap público](https://github.com/davidlopezg/restauranteai#-roadmap-p%C3%BAblico).)

## ¿Querés contribuir?

El repo es público: [github.com/davidlopezg/restauranteai](https://github.com/davidlopezg/restauranteai). El [CONTRIBUTING.md](https://github.com/davidlopezg/restauranteai/blob/main/CONTRIBUTING.md) tiene las 5 reglas duras (la más importante: **nada de datos reales en el template** — si tu restaurante se llama "Sol de Nit", mantenelo en una instancia privada).

Ideas de contribution que serían especialmente útiles:

- 🌐 Traducción de la [landing](https://davidlopezg.github.io/restauranteai/) a otros idiomas (francés, portugués, italiano).
- 📸 Capturas reales de la demo en más estados (variantes del proceso creativo, ideas aplicadas con métodos diferentes).
- 🍽️ Más métodos creativos en `agents/creativo/agent.py` (`METODOS_CREATIVOS`).
- 🧠 Tests de integración que cubran flujos completos (init → ficha → guardar idea → consulta).

Si querés algo que no ves en el roadmap, abrí un [issue con la plantilla](https://github.com/davidlopezg/restauranteai/issues/new/choose). El maintainer (yo) responde en 3-7 días.

## TL;DR

> Si renovás carta cada 3 meses y querés hacerlo en 1 semana, probá el Chef Creativo. Software gratis (MIT), modelo open core, deployado en Hugging Face. 10 segundos para probar, 5 minutos para entender, 1 hora para configurar.

[→ Demo](https://huggingface.co/spaces/davidlopezgamero/RestaurantEAI) · [→ Repo](https://github.com/davidlopezg/restauranteai) · [→ Landing](https://davidlopezg.github.io/restauranteai/)

---

**Sobre el autor**: David López Gamero es hostelero en Cataluña y constructor de este proyecto. Empezó como herramienta interna para su propio restaurante; ahora es open source. Contacto: [davidlopezgamero@gmail.com](mailto:davidlopezgamero@gmail.com).
