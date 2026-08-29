# 🐦 Thread de Twitter/X — Lanzamiento RestaurantEAI

> **Formato**: 11 tweets (puede partirse en 2 si LinkedIn pide más).
> **Audiencia**: hosteleros, chefs, devs con interés en IA aplicada.
> **Hashtags finales**: #ai #llm #restaurant #opensource #buildinpublic
> **Día óptimo**: martes o miércoles, 9-11am CET o 2-4pm LATAM.

---

## Tweet 1/11 (hook)

> Acabo de lanzar algo que me hubiera gustado tener cuando renovaba la carta cada 3 meses.
>
> **Chef Creativo** 🍂 — un agente IA que conoce tu restaurante (ticket, línea, carta, temporada) y te ayuda a crear platos coherentes con tu casa, no genéricos.
>
> 🧵👇

---

## Tweet 2/11 (el problema)

> Renovar la carta me llevaba 2 meses y rara vez el resultado era memorable.
>
> El sprint creativo no entra en el calendario de un hostelero que además gestiona sala, compras y personal.
>
> La IA genérica (GPT, Claude) te da una receta, pero **no conoce tu casa**.

---

## Tweet 3/11 (la diferencia)

> La diferencia es el contexto.
>
> El Chef Creativo tiene en cuenta:
> • Ticket medio (25-60 € en mi caso)
> • Línea culinaria (mediterránea, no sushi)
> • Carta actual (no duplicar, llenar huecos)
> • Productos y técnicas dominantes
> • Estacionalidad
>
> Cada respuesta inyecta 15 dimensiones + tu carta.

---

## Tweet 4/11 (4 modos)

> Tiene 4 modos:
>
> 🍂 **Ficha técnica** — una petición → ficha estructurada
> 🧠 **Proceso creativo** — state machine de 7 fases (cómo piensa el chef, paso a paso)
> 💡 **Ideas creativas** — 10 ideas para explorar, refinables con métodos de ElBulli
> 💬 **Chat con el chef** — conversación libre sobre producto, técnica, carta
>
> Los 4 comparten contexto y memoria.

---

## Tweet 5/11 (memoria)

> Tiene memoria.
>
> Cuando el chef dice algo que querés recordar: `/guardar 5`. Cuando querés revisar: `/ideas`. Cuando ya no aplica: `/olvidar`.
>
> SQLite local, WAL mode, RGPD desde el día uno. Tus ideas viven en tu instancia, no en un servidor mío.

---

## Tweet 6/11 (idioma)

> Detalle que importa: el LLM a veces responde en inglés cuando le hablás en español.
>
> El chef detecta el drift con heurística de palabras gatillo y **reintenta automáticamente** con instrucción reforzada + temperatura baja.
>
> Tasa de éxito >95%. Detalle pequeño, diferencia enorme para el usuario.

---

## Tweet 7/11 (open core)

> El modelo es **open core**:
>
> ✅ Software gratis (MIT). Lo podés clonar, leer, modificar, deployar.
> ✅ Sin features premium escondidas, sin suscripción mensual.
> 💰 Monetización por servicio: si querés esto funcionando en TU restaurante con TU carta, te lo implemento yo.

---

## Tweet 8/11 (demo)

> Probá la demo en 10 segundos, sin registro:
>
> 👉 https://huggingface.co/spaces/davidlopezgamero/RestaurantEAI
>
> Usa un perfil demo genérico (mediterráneo, ticket medio). La primera visita puede tardar 30s (HF Space duerme los procesos).

---

## Tweet 9/11 (screenshots)

> Capturas reales de los 4 modos:
>
> [imagen adjunta: demo-ficha.png + demo-proceso-creativo.png + demo-ideas.png + demo-chat.png]
>
> Cada una muestra el chef trabajando con el contexto del perfil demo. Nada de mockups: contenido que el modelo realmente genera.

---

## Tweet 10/11 (stack técnico)

> Por si te interesa el stack:
>
> • LLM: MiniMax M3 (1M context, Anthropic y OpenAI SDK)
> • UI: Gradio 6.19 sobre HF Spaces (gratis)
> • Memoria: SQLite con WAL
> • 132 tests + CI en GitHub Actions
> • Python 3.11
>
> Todo el código:
> 👉 https://github.com/davidlopezg/restauranteai

---

## Tweet 11/11 (CTA)

> Si renovás carta cada 3 meses y querés hacerlo en 1 semana, probá el Chef Creativo.
>
> Para feedback, ideas o críticas: thread abierto o DM.
>
> Si querés que lo configure para tu restaurante, escribime:
> 📩 davidlopezgamero@gmail.com
>
> 🍂

---

## Notas operativas

- **Engagement en los primeros 30 min**: responder CADA reply en la primera hora (el algoritmo lo mide).
- **Quote-tweets con capturas**: 2-3 quote-tweets con una imagen y un mini-hook cada uno.
- **Pin al perfil**: pinear el tweet 1 al perfil durante 1 semana.
- **Cross-post en LinkedIn**: el tweet 1 + 7 + 11 funcionan como post de LinkedIn standalone.
- **Hash principal**: #ai #buildinpublic
- **Evitar**: hype ("revolucionario", "cambiará el mundo"), superlativos, capturas de competidores.

---

## Variante LinkedIn (post standalone)

> Acabo de lanzar algo que me hubiera gustado tener cuando renovaba la carta cada 3 meses.
>
> **Chef Creativo** 🍂 — un agente IA para hostelería que conoce tu restaurante (ticket, línea culinaria, carta actual, temporada) y propone platos coherentes con tu casa.
>
> El truco: en cada respuesta se inyectan 15 dimensiones de contexto + tu catálogo completo. El chef no improvisa — trabaja sobre tu base.
>
> 4 modos: ficha técnica, proceso creativo paso a paso, 10 ideas con métodos de ElBulli, chat libre.
>
> Es **open source (MIT)** y **open core**: el software es gratis, el modelo de monetización es servicio de implementación. Si querés esto funcionando en tu restaurante con tu carta, te lo configuro yo.
>
> Probá la demo en 10 segundos (sin registro):
> 👉 https://huggingface.co/spaces/davidlopezgamero/RestaurantEAI
>
> Repo: https://github.com/davidlopezg/restauranteai
>
> Soy hostelero en Cataluña. Esto empezó como herramienta interna para mi restaurante. Ahora es open source porque creo que le puede servir a más gente.
>
> Si tenés un restaurante y querés probarlo en serio, DM o mail a davidlopezgamero@gmail.com.
