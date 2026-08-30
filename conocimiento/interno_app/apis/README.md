# APIs externas

Documentación de las APIs externas que invoca la aplicación. Esta carpeta es **lectura humana**, no código: sirve para saber qué APIs usamos, con qué parámetros y cómo configurarlas.

## Índice

- [MiniMax](#minimax) — LLM que genera todas las respuestas del agente creativo
- [Flavor Engine](#flavor-engine--capa-1) — Motor de combinaciones moleculares (PubChem + mapping curado)
- [Spoonacular (pendiente)](#spoonacular--capa-2-pendiente) — Ancla de viabilidad con recipes reales

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
## Flavor Engine — capa 1

Motor de combinaciones moleculares que el agente Chef Creativo consulta automáticamente cuando se invoca la skill `idea_cientifica`. Combina:

- **Mapping curado local** (~300 KB): 84 ingredientes mediterráneos con sus CIDs de PubChem clave.
- **PubChem REST API** (NIH): resolución on-demand con caché SQLite para ~140 ingredientes adicionales.

Para la documentación completa, ver [`flavor_engine.md`](flavor_engine.md).

### Variables de entorno

Ninguna — PubChem es libre y no requiere autenticación.

### Uso

Internamente, la skill `idea_cientifica` invoca:

```python
from agents.herramientas import suggest_pairings, get_compound_overlap
pairings = suggest_pairings("ajo", top_k=10)
overlap = get_compound_overlap("ajo", "limon")
```

### Limitaciones

- Cobertura: 225 ingredientes (84 curados + 141 PubChem-resolubles).
- Latencia PubChem: ~250ms/primera consulta, instantáneo en cache hits.
- Rate limit: 5 req/s (respetado por el cliente).
- Sin coste: NIH PubChem es 100% gratuito.

## Spoonacular — capa 2 (pendiente)

**Estado**: pendiente de integración. Necesita `SPOONACULAR_API_KEY` en `.env`.

Plan: cuando esté disponible, agregar `agents/herramientas/spoonacular.py` con funciones:

- `find_recipes_with(ing_a, ing_b)` — recipes reales que combinan ambos ingredientes.
- `extract_bridge_element(recipes)` — qué grasa/ácido/crujiente conecta la combinación en esas recipes.
- `nutrition_per_100g(ingredient)` — datos nutricionales para la skill.

La skill `idea_cientifica` invocará Spoonacular como segundo validador después del flavor engine.
