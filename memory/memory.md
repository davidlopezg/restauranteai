# 🧠 Memory — restauranteia

> Memoria de aprendizaje del agente para el proyecto `restauranteia` (ecosistema de agentes IA para restauración).

## Decisiones de arquitectura cerradas

### 2026-06-30 — Proveedor de LLM confirmado: MiniMax API (no OpenAI, no Ollama)

**Contexto:** David venía con un master plan que asumía OpenAI API como proveedor. Al implementar, aclaró que NO tiene OpenAI API ni Ollama local. Tiene acceso a la **API de MiniMax** (la empresa que me crea a mí como modelo).

**Implicaciones:**
- Script se enchufa contra `https://[ENDPOINT_MINIMAX]/v1/chat/completions` o equivalente.
- Formato de autenticación **pendiente de confirmar con David** (probablemente Bearer token estilo OpenAI, pero NO asumir).
- Unit economics del SaaS posterior dependerán del coste por request de MiniMax (a confirmar cuando tenga acceso a su panel de pricing).
- Si MiniMax no tiene SDK oficial, uso `httpx` directo contra endpoint REST.

**Pendiente (original):**
- [x] David confirma endpoint exacto base URL → verificado, ver bloque de abajo
- [x] David confirma header de auth → verificado, ver bloque de abajo
- [x] David confirma nombre del modelo → verificado, ver bloque de abajo
- [x] Verificar si MiniMax API es OpenAI-compatible → confirmado por doc oficial

### 2026-06-30 — Decisión sobre la API key: fija, no rotable

**Contexto:** David intentó seguir el flujo de "rotar la key tras exposición por chat", pero la API key que tiene es **fija/no rotable** (probablemente plan de suscripción fijo, no pay-as-you-go). Esto cambia la política de seguridad.

**Implicaciones:**
- La key sigue comprometida en el log de la sesión de chat (no editable por nosotros desde acá).
- No podemos aplicar la mitigación estándar de "rotar y listo".
- Hay que compensar con controles en otra capa.

**Medidas compensatorias acordadas:**
1. **Monitoreo de uso** desde el panel de MiniMax (David debe revisar periódicamente si hay requests que él no hizo).
2. **Restricción de scopes** (si MiniMax lo permite): la key idealmente solo debería tener scope `chat/completions`. Si la key tiene más permisos de los necesarios, ver si se puede degradar.
3. **Frontera explícita en código**: el código del agente **nunca debe loggear el valor de la key**, ni siquiera truncado. Ya está así (solo verificamos que esté presente).
4. **Documentar el incidente** en el README para que cualquier colaborador futuro sepa que esa key específica no debe pegarse en issues, chats, ni screenshots.

**Política aplicada en código:**
- `agent.py`: nunca loggea el valor de la key. Errores exponen si la key está presente o no, pero no su contenido.
- `.env.example`: solo placeholders literales, nunca key real.
- `conversations/*.md`: redactado si alguna vez contiene key (verificado: la de esta sesión NO la contiene).
- `memory.md`: este registro menciona la key como "fija, no rotable" pero no reproduce su valor.

**Estado del proyecto (actualizado):**
- Repo inicializado: ✅
- Estructura de carpetas: ✅
- MVP-0 código: ✅ (cableado, sin TODOs críticos)
- MVP-0 validado end-to-end por David: ✅ (URL corregida de api.minimax.chat → api.minimax.io)
- API key operativa: ✅ (con salvaguarda "fija/no rotable")
- Iteración de system prompt: ⏳ (próximo paso)
- MVP-0.5 código (app.py + Gradio): ✅ (cableado, pendiente deploy a HF)
- MVP-0.5 deploy a HF Space: ⏳ (espera instrucciones paso a paso de David)

### 2026-06-30 — Inicio de MVP-0.5 (HF Space con Gradio)

**Decisiones tomadas:**
- **Username de HF**: `davidlopezgamero` (decidido por David)
- **Privacidad de la key fija**: opción A+C → Secret en HF Space + Space con link privado ("Anyone with link") para empezar.
- **Framework UI**: Gradio (mantener consistencia con la decisión original; simple de mantener).
- **Backend**: se mantiene `httpx` directo (no se migra a SDK `openai`) para preservar la superficie validada en MVP-0.

**Riesgos identificados:**
- La API key fija queda cargada como Secret en HF (un proveedor más donde queda expuesta). David debe aceptarlo conscientemente. Plan de mitigación: monitoreo de uso desde el panel de MiniMax.
- Mi sandbox tiene restricciones de red que impidieron `pip install gradio` para test local del wrapper. **Esto NO afecta al producto**: la instalación se hará en la máquina de David / HF Space, no en mi sandbox.
- Test local del wrapper Gradio en mi sandbox queda pendiente para una verificación post-deploy. Si algo crashea, se diagnostica con el log de HF.

**Estado del deploy:**
- Código listo: `app.py`, `requirements.txt` con `gradio>=4.44.0`, `README.md` con frontmatter HF.
- Pendiente de David: crear Space en HF, cargar Secret con la API key, subir código (push desde local o usar un repo Git), verificar arranque público.

**Por qué MVP-0.5 antes que Fase 2 (Agente Memoria):**
- Es la culminación natural del MVP-0 (ya validado). Pone el agente en internet en 3 horas, no en varias sesiones de diseño.
- El Agente Memoria necesita decisiones de fondo (RGPD, dónde almacenar datos, qué datos se guardan) que bloquean diseño. Empezar por ahí sin tener datos reales que recolectar tiene poco sentido.
- Una vez MVP-0.5 funcionando, podemos usar el agente público como canal para juntar ideas/reacciones de usuarios reales (socios, David mismo, posibles clientes iniciales) — información útil para diseñar el siguiente agente.

### 2026-06-30 — Verificación oficial de MiniMax API (fuente: platform.minimax.io)

**Fuentes consultadas y verificadas en esta sesión:**
- https://platform.minimax.io/docs/api-reference/api-overview
- https://platform.minimax.io/docs/guides/quickstart-preparation
- https://platform.minimax.io/docs/guides/models-intro
- https://platform.minimax.io/docs/api-reference/text-chat-openai

**Datos confirmados por la doc oficial:**
- Modo elegido: **OpenAI-compatible** (porque el parser del código coincide 1:1 con el formato OpenAI).
- Base URL: **`https://api.minimax.io/v1`**.
- Header de auth: **`Authorization: Bearer <MINIMAX_API_KEY>`**.
- Endpoint: **`POST /chat/completions`**.
- Modelo por defecto: **`MiniMax-M3`** (1M context window, frontier multimodal coding).
- Formato de response validado: `data["choices"][0]["message"]["content"]` (mismo que OpenAI).
- SDKs oficiales disponibles: OpenAI SDK, Anthropic SDK, AI SDK. La doc recomienda Anthropic como primera opción para casos nuevos; nosotros elegimos OpenAI por compatibilidad con el código actual.
- Modo alternativo: también existe modo **Anthropic-compatible** (`/anthropic`). Queda como upgrade futuro cuando aparezca necesidad de tool use nativo o multi-agente.

**Implicaciones técnicas:**
- El código `agent.py` se cableó con los defaults verificados. Ya no quedan TODOs críticos.
- Parser de response existente (`data["choices"][0]["message"]["content"]`) sigue siendo válido — cero cambios.
- Las variables de entorno esperadas son: `MINIMAX_API_KEY`, `MINIMAX_BASE_URL`, `MINIMAX_MODEL`.

**Decisión de seguridad — NO se guarda la API key en el repo:**
- La API key que David pasó por chat se considera **comprometida** (quedó en el log de conversación, que se persiste en `conversations/`).
- Política aplicada: la key **NO** se escribe en `.env.example`, ni en código, ni en memoria. Vive solo en el `.env` local de David.
- Pendiente de David: rotar la key en el panel oficial antes de la primera llamada real.
  URL de rotación: https://platform.minimax.io/user-center/basic-information/interface-key

**Por qué modo OpenAI-compatible y no Anthropic:**
- El código existente ya implementa la forma OpenAI (POST /chat/completions, formato `messages: [{role, content}]`).
- Migrar a Anthropic implica reescribir el cliente HTTP y manejar el formato distinto de messages. No aporta valor para MVP-0 (solo texto in → texto out).
- Si en el futuro aparece necesidad de tool use nativo o prompt caching, se justifica migrar.

**Nuevo estado del proyecto:**
- Repo inicializado: ✅
- Estructura de carpetas: ✅
- MVP-0 código: ✅ (cableado con docs verificadas, sin TODOs críticos)
- Validación de estructura (sin API): ⏳ (próximo paso en esta sesión)
- Primera llamada real: ⏳ (espera: key rotada por David + validación)

## Decisiones de scope cerradas

### 2026-06-30 — MVP-0 = solo Chef Creativo, sin más agentes ni hosting público

**Por qué se recortó el master plan original:**
- David tiene hernia operada, fístula, tesorería ajustada → no puede sostener un sprint heroico.
- Protocolo de verdad (Capa 6) prohíbe inventar las "20 reglas de creatividad culinaria" que el plan original me pedía.
- Multi-agente sin MVP validado = castillo de naipes (anti-patrón visto en fooday).

**Lo que SÍ se hace en MVP-0:**
- Script Python ejecutable localmente que toma petición NL y devuelve ficha estructurada (nombre, historia, ficha técnica, maridaje, prompt de imagen).
- System prompt del chef con personalidad mediterránea/catalana.
- Datos mínimos de conocimiento (estacionalidad Cataluña, combinaciones clásicas).

**Lo que NO se hace todavía:**
- Cost estimator numérico (necesita base de precios que David tiene que aportar).
- HF Space / GitHub Pages / hosting público (espera a que MVP-0 esté validado).
- Otros 5 agentes (cada uno es un proyecto).
- Monetización SaaS (primero producto, después plan de negocio).

## Estado del proyecto

- Repo inicializado: ✅ (commit vacío)
- Estructura de carpetas: ✅ (`agents/creativo/`, `memory/`, `conversations/`, `scripts/`)
- MVP-0 código: 🔄 (en generación)
- MVP-0 probado por David: ⏳
- MVP-0.5 (HF Space público): ⏳

## Datos del usuario (David)

- Hostelero real, Sol de Nit (pizzería en Cataluña).
- Conocimiento gastronómico profundo: input crítico para el Chef Creativo.
- Patrón conocido: llega con ideas grandes, tiende a inflar expectativa. El agente debe anclar a tierra y validar paso a paso.
- Limitaciones físicas: hernia discal operada, fístula. No permitir "sprint heroico".
- Familia: María y Abril (prioridad máxima).