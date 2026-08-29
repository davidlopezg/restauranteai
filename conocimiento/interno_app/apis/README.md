# APIs externas

Documentación de las APIs externas que invoca la aplicación. Esta carpeta es **lectura humana**, no código: sirve para saber qué APIs usamos, con qué parámetros y cómo configurarlas.

## Índice

- [MiniMax](#minimax) — LLM que genera todas las respuestas del agente creativo

---

## MiniMax

API de inferencia de LLM compatible con OpenAI, utilizada para todas las llamadas del agente creativo (fichas técnicas, chat, ideas, proceso creativo).

### Variables de entorno

| Variable | Obligatoria | Default | Descripción |
|---|---|---|---|
| `MINIMAX_API_KEY` | ✅ Sí | — | Clave de la API |
| `MINIMAX_BASE_URL` | ❌ No | `https://api.minimax.io/v1` | Endpoint base (modo OpenAI-compatible) |
| `MINIMAX_MODEL` | ❌ No | `MiniMax-M3` | Modelo a usar (frontier multimodal, 1M context) |

Configurar en `.env` (local) o como Secrets en HF Space.

### Uso

Toda llamada al LLM pasa por `agents/creativo/agent.py::call_minimax(messages, ...)`. Es una función wrapper sobre `httpx` que:

- Reintenta hasta `MAX_RETRIES=2` veces ante errores transitorios
- Tiene `REQUEST_TIMEOUT=60.0s`
- Fuerza castellano en todas las respuestas (`LANGUAGE_RETRIES=2` reintentos adicionales si el chef responde en otro idioma)
- Inyecta automáticamente el contexto del restaurante y catálogo como system prompt

### Endpoints

| Operación | Endpoint | Notas |
|---|---|---|
| Chat completion | `POST {BASE_URL}/chat/completions` | OpenAI-compatible |

### Modelo

**`MiniMax-M3`**: frontier multimodal, ventana de contexto 1M tokens. Soporta texto e imagen. Por defecto se usa solo texto.

### Limitaciones conocidas

- **Rate limits**: no documentados públicamente. Si ves `429 Too Many Requests`, esperar y reintentar.
- **Idioma**: el modelo tiende a responder en inglés si la pregunta es ambigua. El wrapper fuerza castellano con reintentos, pero no es infalible.

### Referencias

- Doc oficial: https://platform.minimax.io/docs/guides/quickstart-preparation (sección "Compatible OpenAI API")
- Modelos: https://platform.minimax.io/docs/guides/models-intro