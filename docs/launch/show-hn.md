# Show HN: RestaurantEAI – Chef IA que conoce tu carta

> **Plataforma**: Hacker News · **Audiencia**: devs, makers, gente curiosa de IA aplicada.
> **Título corto**: "Show HN: RestaurantEAI – Chef IA que conoce tu carta"
> **Día óptimo**: martes a jueves, 8-10am US Eastern.
> **Tiempo de permanencia en frontpage**: si llega al top 30 en 2 horas, mantener el thread activo durante 8-12 horas respondiendo TODO.

---

## Versión final del post (lista para submit)

**Título** (máx 80 chars):

```
Show HN: RestaurantEAI – Chef IA que conoce tu carta
```

**URL**: `https://huggingface.co/spaces/davidlopezgamero/RestaurantEAI` (la demo, no el repo — HN prefiere vivir el producto)

**Texto del post**:

```
Hola HN,

Soy hostelero en Cataluña. Construí RestaurantEAI porque estaba cansado de
renovar la carta cada 3 meses con el mismo proceso lento (pensar 2h,
anotar 3 ideas, olvidarme, repetir, cocinar prototipo 3 veces, ponerlo en
carta sin convicción, sacarlo a los 2 meses).

Es un agente IA (LLM) que conoce el contexto de tu restaurante (15
dimensiones: ticket medio, línea culinaria, productos dominantes, técnicas,
estacionalidad, restricciones religiosas, etc.) y propone platos
coherentes con tu casa, no genéricos. La diferencia con "pídele una receta
a GPT" es la inyección automática del contexto en cada prompt.

Tiene 4 modos:

  🍂 Ficha técnica – una petición → ficha estructurada (nombre, historia,
     ficha técnica, maridaje, prompt de imagen).
  🧠 Proceso creativo – state machine de 7 fases (alma, métodos creativos
     de ElBulli, equilibrio, técnica, storytelling, descartadas,
     preguntas). Muestra cómo piensa el chef paso a paso.
  💡 Ideas creativas – 10 ideas para explorar (renovar carta, llenar
     huecos, ideas de temporada), refinables con métodos creativos.
  💬 Chat con el chef – conversación libre con todo el contexto cargado.

Stack:
  - LLM: MiniMax M3 (1M context, OpenAI-compatible).
  - UI: Gradio 6.19 sobre Hugging Face Spaces (gratis).
  - Memoria: SQLite local con WAL. RGPD desde el día uno (borrado granular,
    export JSON, sin telemetría).
  - 132 tests, CI en GitHub Actions.
  - Python 3.11, ~5500 LOC.

Modelo de negocio: open core. El software es open source MIT, gratis. Si
alguien quiere esto funcionando en SU restaurante con SU carta
configurada, le hago la implementación como servicio pago. Deliberadamente
low-overhead, sin suscripción mensual, sin vendor lock-in.

Lo que NO es:
  - No es multi-tenant: el Space público tiene un perfil demo único.
  - No es para "uso real" en producción: el HF Space duerme los procesos
    (filesystem efímero). La demo es para probar; para uso serio, instancia
    privada del cliente.
  - No es un sustituto del cocinero: la decisión final es tuya.

Repo: https://github.com/davidlopezg/restauranteai
Landing: https://davidlopezg.github.io/restauranteai/

Construido con cariño desde Cataluña. Críticas bienvenidas (especialmente
las duras).
```

**Largo**: ~1500 caracteres. HN tolera hasta ~10000. Si querés acortar, podés sacar la lista de "Lo que NO es".

---

## Template alternativo (más corto, si el primero no genera engagement)

**Título**:

```
Show HN: Chef IA con contexto del restaurante (open source)
```

**Texto**:

```
RestaurantEAI es un agente IA para hosteleros. La diferencia con "pídele
una receta a GPT" es la inyección automática del contexto del restaurante
(15 dimensiones + carta actual) en cada respuesta.

4 modos: ficha técnica, proceso creativo de 7 fases, ideas con métodos
de ElBulli, chat libre. Memoria SQLite local (RGPD desde el día uno).
Open source (MIT), modelo open core.

Soy hostelero en Cataluña, lo construí porque estaba cansado de renovar
la carta cada 3 meses con el mismo proceso lento.

Demo (sin registro): https://huggingface.co/spaces/davidlopezgamero/RestaurantEAI
Repo: https://github.com/davidlopezg/restauranteai
```

---

## Plan de respuesta (lo más crítico)

### Reglas

1. **Responder TODO en las primeras 4 horas.** HN mide engagement en las primeras horas. Si dejas un comentario técnico sin responder, perdiste el upvote.
2. **Tono: humble, técnico, directo.** HN odia el hype. Odiá el "revolucionario", "cambiará el mundo". Hablá como dev.
3. **No defenderse de críticas.** Si alguien dice "esto es solo un wrapper de un LLM", respondé "Sí, lo es. El wrapper es el contexto." y seguí.
4. **Aceptar feedback sin pelear.** Si alguien sugiere algo bueno, decí "Buenísimo, lo agrego al roadmap" y dejá el link al issue si lo creaste.
5. **Si alguien pregunta por el costo del LLM**: ser honesto sobre el unit economics.

### Preguntas anticipadas y respuestas pre-fabricadas

**Q: ¿Es solo un wrapper de un LLM?**

> Sí, técnicamente. La diferencia es el contexto inyectado y el flujo (state machine de 7 fases en el proceso creativo). El wrapper ES el producto. Es como decir que un framework web es "solo un wrapper sobre HTTP". Técnicamente correcto, pero falta el punto.

**Q: ¿Por qué MiniMax y no OpenAI/Anthropic?**

> Porque empecé el proyecto con la API de MiniMax y el código se cableó a esa API. La capa de abstracción (`call_minimax()` en `agents/creativo/agent.py`) hace que migrar sea ~50 líneas. Está en el roadmap si aparece la necesidad.

**Q: ¿Cuánto cuesta cada request?**

> El modelo M3 es económico (no tengo el número exacto a mano, tendría que mirar el panel). El demo público no cobra al visitante — el costo lo asumo yo como marketing. Para uso real, el costo es marginal.

**Q: ¿Por qué no usar GPT-4?**

> GPT-4 también funcionaría. El código ya está abstraído. La razón de usar MiniMax es que es el proveedor que tengo acceso. La interfaz OpenAI-compatible hace que migrar sea trivial.

**Q: ¿Cómo evitás alucinaciones?**

> Triple: (1) el system prompt restringe el output a estructura fija, (2) el contexto del restaurante limita el espacio de respuestas razonables, (3) cuando el chef NO sabe algo, dice "no tengo info de X en tu configuración" en vez de inventar. Pero sí, alucina a veces — como cualquier LLM. Por eso el output es un borrador, no un plato terminado.

**Q: ¿Y la propiedad intelectual de las recetas?**

> El chef genera ideas/platos a partir del contexto. La IP de las recetas finales es del cocinero que las ejecuta y prueba. Si el LLM te sugiere algo que ya existía en otro restaurante, es porque la combinación de ingredientes es lógica — no porque "copió" algo. Pero es una pregunta válida y abierta en general para todo output de LLM.

**Q: ¿Multi-tenant?**

> No en el Space público. Una instancia por restaurante en producción. Esto es deliberado: el perfil de cada restaurante es contexto sensible.

**Q: ¿Dónde están los datos?**

> El Space público tiene un perfil demo. Lo que vos configurés en la demo se guarda en el filesystem del Space (efímero). Para uso real, instancia privada con tus datos aislados. Política completa en el SECURITY.md.

**Q: ¿Por qué no es self-service completo?**

> Está en el roadmap. El change `init-web` (SDD abierto) agrega una UI web de configuración. Por ahora, init es CLI (`python -m agents.init_phase`).

---

## Plan de contingencia

| Escenario | Acción |
|---|---|
| Top 30 en 2h → mantener 12h | Responder TODO. Cross-tweet. Pedir a 3 amigos que upvoten comentarios útiles. |
| Top 100 → decay natural | Responder todo durante 6h. No desesperar. |
| Quedó en "new" sin tracción | No pasa nada. Esperar al próximo intento (no resubmit el mismo post; cambiar título o timing). |
| Crítica muy dura ("es inútil") | Responder con respeto. Si es válida, anotarla como issue en GitHub. NO pelearse. |
| Usuario reporta bug serio | Acknowledgement público + fix inmediato + update en el thread. |
| Pregunta técnica que no podés responder | "Buena pregunta, dejame verificarlo. Te respondo en 1h." Y volvé con respuesta. |

---

## Métricas a trackear (post-HN)

- Posición final en frontpage.
- Upvotes / comentarios.
- Visitas al repo durante las 24h post-HN (pico esperado).
- Stars nuevas.
- Issues abiertos por el thread.
- Mensajes de outreach pidiendo implementación.

Subir a `docs/METRICS.md` cuando termine el día.
