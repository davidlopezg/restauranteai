# 2026-06-30 — Verificación de MiniMax API y cableado de MVP-0

## Resumen
Sesión centrada en destrabar el cableado del agente Chef Creativo con la API real de MiniMax. Búsqueda y verificación de docs oficiales, edición del agent.py para reemplazar TODOs por referencias verificadas, actualización de memoria, y arreglo de bug en script de validación.

## Logros

### 1. Verificación oficial de MiniMax API
Búsqueda web en platform.minimax.io confirma:
- **Base URL** (modo OpenAI-compatible): `https://api.minimax.io/v1`
- **Auth**: `Authorization: Bearer <MINIMAX_API_KEY>`
- **Endpoint**: `POST /chat/completions`
- **Modelo por defecto**: `MiniMax-M3` (1M context window)
- **Formato de response**: compatible OpenAI (`choices[0].message.content`)
- SDKs oficiales disponibles: OpenAI SDK, Anthropic SDK, AI SDK.

Fuentes verificadas (4 páginas):
- platform.minimax.io/docs/api-reference/api-overview
- platform.minimax.io/docs/guides/quickstart-preparation
- platform.minimax.io/docs/guides/models-intro
- platform.minimax.io/docs/api-reference/text-chat-openai

### 2. Cableado de `agents/creativo/agent.py`
- Removidos TODOs críticos (endpoint, header, modelo, parámetros)
- `DEFAULT_BASE_URL = "https://api.minimax.io/v1"` agregado como constante
- `DEFAULT_MODEL = "MiniMax-M3"` extraído como constante
- Docstring de `call_minimax()` documenta los 4 datos verificados con links a la doc oficial
- Comentarios inline reemplazan TODOs por referencias a fuentes

### 3. Actualización de `memory/memory.md`
Sección nueva: "Verificación oficial de MiniMax API (fuente: platform.minimax.io)"
- Cita las 4 fuentes consultadas
- Lista los datos confirmados (BASE_URL, auth, endpoint, modelo)
- Justifica elección de modo OpenAI sobre modo Anthropic
- Establece política de seguridad: API key nunca se guarda en el repo
- Actualiza estado del proyecto (código cableado, validación pendiente)

### 4. Fix de bug en `scripts/probar_estructura.py`
- Sección "Variables de entorno" no conectaba ❌ al flag `todo_ok` → imprimía "🎉 Todo OK" contradictorio
- Reescrito para distinguir:
  - API key faltante → ❌ BLOQUEANTE
  - BASE_URL/Modelo sin override → ✅ usa default verificado (no bloqueante)
- Mensaje final ahora coherente

## Decisiones técnicas

### Modo OpenAI-compatible elegido sobre Anthropic
- El código existente ya implementaba formato OpenAI (messages, payload, parser)
- Migrar a Anthropic no aporta valor para MVP-0 (solo texto in/out)
- Modo Anthropic queda como upgrade futuro para tool use nativo / multi-agente

### Política de seguridad: API key nunca persiste en el repo
- David pasó su API key por chat → quedó en log de conversación
- Política aplicada: la key **NO** se escribe en código, `.env.example` ni memoria
- Vive solo en `.env` local del usuario
- Pendiente: David debe rotar la key en el panel oficial antes de la primera llamada real

## Pendientes

### Para David
- [ ] **Rotar la API key** (panel: platform.minimax.io/user-center/basic-information/interface-key) — la del chat quedó comprometida
- [ ] **Crear `.env`** desde `.env.example` con la key nueva
- [ ] **Correr `python scripts/probar_estructura.py`** para validar que la base sigue sana con la key real
- [ ] **Probar end-to-end**: `python -m agents.creativo.agent "Entrante vegetariano con calabaza"` (o similar)
- [ ] **Ajustar system prompt** si la salida no tiene el tono/forma esperada

### Para próxima sesión
- Revisar output del agente con David y refinar system prompt
- Decidir si pasamos a MVP-0.5 (HF Space) o iteramos más el prompt
- Si todo OK, planear Fase 1 (Agente de Memoria / CRM)

## Archivos modificados
- `agents/creativo/agent.py` — cableado con defaults verificados
- `memory/memory.md` — sección de verificación agregada
- `scripts/probar_estructura.py` — bug fix + distinción bloqueante/no-bloqueante

## Notas para continuidad
- El agente sigue siendo Python estándar (`httpx` + `python-dotenv`), sin SDKs externos
- El parser de response coincide 1:1 con formato OpenAI
- Si David quiere overridear defaults, las vars son `MINIMAX_BASE_URL` y `MINIMAX_MODEL`
- Estacionalidad cubre 42 productos (calabaza, tomate, setas, trufa, mariscos, carnes, lácteos, frutas)
- Combinaciones clásicas: 22 pares cargados
