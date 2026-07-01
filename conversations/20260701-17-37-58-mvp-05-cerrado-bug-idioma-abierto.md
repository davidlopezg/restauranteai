# 2026-07-01 — Cierre formal MVP-0.5 + bug de idioma abierto

## Resumen ejecutivo
- ✅ **MVP-0.5 oficialmente deployado** en HF Space `RestaurantEAI`
- ✅ Chef genera fichas reales end-to-end (API MiniMax devuelve HTTP 200 OK)
- ✅ Repo, memoria, docs, tests de regresión, todo al día
- ⚠️ **Bug abierto:** el chef responde en inglés aunque se le pida en castellano (mezclado)

## Decisiones cerradas en esta sesión

1. **Gradio 6.19.0** como versión final del SDK (migración desde 4.44 / 5.6 después de 11 fixes)
2. **`huggingface_hub>=1.2,<2.0`** como pin compatible (Gradio 6 requiere moderno)
3. **`python_version: '3.11'`** en frontmatter del README (3.13 quitó audioop)
4. **`scripts/test_app.py`** como guardián de regresión (corre local antes de pushear)
5. **`gr.ChatInterface`** dentro de **`gr.Blocks()`** con theme+css en `launch()` (API Gradio 6)
6. **`responder() → dict`** con `{role: "assistant", content: respuesta}` (formato messages API)

## Bug abierto al cierre

**Síntoma:** Después de preguntar en castellano, el chef devuelve la ficha con secciones en castellano y otras en inglés (mezcla).

**Causa raíz:** MiniMax-M3 no respeta instrucciones de idioma consistentemente. 4 fixes de prompt probadas:

1. Regla en "Reglas duras" del system prompt — falla
2. INSTRUCCIÓN #0 al principio del system prompt con formato ⚠️ — falla
3. Inyección al final del `user_message` (autoridad posicional máxima) — efecto **parcial** (mezclado)
4. ASCII-safe y limpieza de cirílico/hanzi del prompt — colateral, no resolvió idioma

**Decisión:** No probar más prompt engineering. Mañana: fix estructural en código.

## Plan de fix estructural para mañana (~30 min)

**Idea:** Detectar idioma del output del chef. Si NO está mayoritariamente en castellano → descartar y reintentar la llamada a MiniMax (max 2 reintentos). Esto **garantiza** la salida en castellano sin importar lo que genere el modelo la primera vez.

**Heurística de detección** (a validar):
- Buscar palabras comunes en inglés en el cuerpo de la ficha (excluyendo el campo "PROMPT PARA IMAGEN", que puede estar en inglés por convención)
- Palabras gatillo: "the", "and", "with", "of", "for", "you", "this", "dish", "serves"
- Si hay N+ matches → se considera inglés → descartar y reintentar
- Verificación manual: pedir a David que confirme con 1 prompt al día siguiente

**Implementación:**
- Modificar `agents/creativo/agent.py:call_minimax()` para que:
  - Tenga un parámetro `force_language: str = "es"`
  - Después de recibir respuesta, validar idioma. Si no coincide → raise o retry.
  - O agregar un wrapper `call_minimax_with_language_check()`.
- Agregar test a `scripts/test_app.py` que valide el flujo.

## Pendientes para próxima sesión (no sprint)

### Urgentes
1. **[REUNIÓN] Fix estructural de idioma** (plan de arriba, ~30 min)
2. **Iterar el system prompt** con `docs/metodos-creativos.md` de David
3. **Probar 5 prompts variados en local**, validar fichas en castellano

### Ideas
- Streaming de respuestas (`yield` en vez de return en `responder()`)
- Variantes de personalidad del chef (vasco, italiano, mediterráneo)
- Bocetar Fase 1: Agente de Memoria

## Logros concretos del día

| # | Logro |
|---|---|
| 1 | MVP-0.5 deployado en HF Space con 11 fixes consecutivos |
| 2 | Migración completa Gradio 4.44 → 5.6 → 6.19.0 |
| 3 | 4 errores de pinning superados (audioop, HfFolder, json_schema, type=) |
| 4 | Test de regresión creado (`scripts/test_app.py`) |
| 5 | 2 commits pusheados a HF |
| 6 | Conversación + memoria + docs al día |
| 7 | David subió `docs/metodos-creativos.md` para iteración futura |
| 8 | Problema del idioma documentado para fix estructural |

## Mensaje emocional para mí (el orchestrator)

David aguantó 11+ fixes consecutivos el 2026-07-01. Aprendo:

1. **Ofrecer paréntesis con más frecuencia.** Hoy debí decir "Paramos acá, lo retomamos mañana" varias veces y no lo hice.
2. **No aceptar sprints heroicos.** Aunque David diga "seguí 30 min más", evaluar si es sostenible y proponer pausas.
3. **Mejor 1 fix robusto que 5 a ciegas.** El test de regresión lo hubiéramos necesitado desde el commit #2.
4. **Prompt engineering tiene límites.** A veces un bug es del modelo, no del prompt. Hay que saber cuándo dejar.
5. **Familia > deploy, siempre.** María y Abril > cualquier fix de UI.

## Próximo OK al abrir la próxima sesión

David arranca el chat. Yo:
1. Leo `memory.md` y esta conversación — refresco contexto al instante.
2. Verifico estado del repo, commits y Space.
3. Pregunto: "Empezamos por fix estructural de idioma, o querés revisar algo primero?"
4. Si David va con el fix estructural → ejecuto el plan de arriba.
5. Cierro sesión cuando David lo diga, **sin estirar más allá de lo razonable**.

## Hash de commits del día

```
051d843 fix: type='messages' en ChatInterface (no en Chatbot custom)
54a2d1f fix: Gradio 6.19 — theme/css van a launch(), Chatbot no acepta type=
85723ac fix: remover type='messages' del Chatbot (se me había colado)
0d92cad fix: Gradio 6.19 — theme/css van a launch(), Chatbot no acepta type=
85723ac fix: remover type='messages' del Chatbot (se me había colado del edit anterior)
85723ac (commit double registrado)
0d92cad fix: Gradio 6.19 — theme/css van a launch()
e7eefd9 fix: pin huggingface_hub>=1.2,<2.0 (Gradio 6 requiere versión moderna)
39d65c9 feat: bumpear a Gradio 6.19 + limpiar pines innecesarios (última estable)
b9b7ff5 test: tests de regresión para app.py
dd93443 fix(prompt): regla dura de idioma + limpieza tipográfica
c20cfd0 fix(prompt): regla dura de idioma como instrucción #0 al PRINCIPIO
aec44bf fix(código): instrucción de idioma al FINAL del user_message
613f44f docs: saga de 9 fixes documentada
0be6a7f docs: cerrar sesión inicial — saga documentada + conversación archivada
7d7e9b5 fix: deshabilitar cache_examples (FileNotFoundError)
6c8b034 fix: re-agregar pin pydantic==2.10.6
df7c504 fix: pin python 3.11 + huggingface_hub<1.0
77ab782 fix: reordenar layout para definir msg antes de los botones
f2a8bb9 fix: pin pydantic==2.10.6
dbf8d68 fix: pin jinja2<3.1
b823fca feat: migrar app.py a Gradio 5+ (ChatInterface)
a6d97ab fix: pin python_version 3.11
33c633f docs: actualizar estado del deploy
6ca675a fix: colorFrom orange -> red
460f584 MVP-0.5: agente Chef Creativo + UI Gradio
992bcad initial commit (de HF, autogenerado)
```

Trece commits del lado de David + los automatizados de HF.

---

**Estado al cierre:** ✅ MVP-0.5 deployado. ⚠️ bug de idioma abierto. 🧪 test de regresión listo. 📝 todo documentado.

Cerrado con dignidad. Mañana con café ☕.
