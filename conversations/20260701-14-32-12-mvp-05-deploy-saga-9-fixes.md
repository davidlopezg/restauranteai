# 2026-07-01 — MVP-0.5 Deploy saga: 9 fixes hasta Space funcionando

## Resumen
Sesión maratónica para llevar Chef Creativo a Hugging Face Space. 9 fixes consecutivos por incompatibilidades de versiones entre Gradio 4.44/5.6 y stacks modernas de HF. Estado final: **Space arranca + API MiniMax responde 200 OK + UI arreglándose con pines**. Sesión cerrada por salud/familia a pesar de que el último fix puede no ser definitivo.

## Logros

### 1. Push del código inicial (✅)
- `git remote add hf https://huggingface.co/spaces/davidlopezgamero/RestaurantEAI` (ya estaba agregado de intento previo)
- `git pull --rebase hf main` → conflicto en README.md por commit inicial de HF (autogenerado: `.gitattributes` + README.md simple con `sdk_version: 6.19.0`, `python_version: '3.13'`, emoji 🦀)
- Resolución con `git checkout --theirs README.md` (durante rebase, `--theirs` = nuestra versión)
- Rebase finalizado + `git push hf main` exitoso
- **Lección documentada**: durante `git rebase`, `--ours`/`--theirs` están invertidos respecto a `git merge`.

### 2. Secret `MINIMAX_API_KEY` cargado por David
- Settings → Repository secrets del Space `RestaurantEAI`
- David confirmó que cargó la key (no el valor, por seguridad)

### 3. Saga de 9 fixes para llegar a "Running"

| # | Commit | Bug | Causa | Fix |
|---|---|---|---|---|
| 1 | `a6d97ab` | `ModuleNotFoundError: audioop` | HF default = Python 3.13 (sin `audioop`) | `python_version: '3.11'` en frontmatter |
| 2 | `dd866d9` | `ImportError: HfFolder` (Gradio 4.44 oauth) | `huggingface_hub>=1.0` eliminó HfFolder | `huggingface_hub<1.0` |
| 3 | `77ab782` | `UnboundLocalError: msg` | bug propio: botones referenciaban msg antes de definirlo | reorderar layout (msg → botones) |
| 4 | `f2a8bb9` | `TypeError: bool is not iterable` en `json_schema_to_python_type` | bug `gradio_client` con `pydantic>=2.11` | `pydantic==2.10.6` |
| 5 | `dbf8d68` | `TypeError: unhashable dict` en jinja2 cache | bug `jinja2>=3.1` + Gradio 4.44 + starlette | (pin no funcionó por cache de HF) |
| 6 | `b823fca` | (mismo error) | escalar pines no escala | **migración a Gradio 5.6+** + rewrite de `app.py` con `gr.ChatInterface` (~70 líneas menos) |
| 7 | `df7c504` | `ImportError: HfFolder` (Gradio 5.6 oauth) | Gradio 5.6 oauth.py aún usa HfFolder | `python_version: '3.11'` + `huggingface_hub<1.0` (defense in depth) |
| 8 | `6c8b034` | `TypeError: bool is not iterable` (Gradio 5.6 UI) | Gradio 5.6 UI refresca mal con pydantic nuevo | `pydantic==2.10.6` |
| 9 | `7d7e9b5` | `FileNotFoundError: .gradio/cached_examples/11/log.csv` | Cache de ejemplos no persiste en HF Spaces | `cache_examples=False` en `gr.ChatInterface` |

### 4. Verificación final exitosa
- Log mostró **5 llamadas HTTP 200 OK a `https://api.minimax.io/v1/chat/completions`** entre las 14:26:02 y 14:27:11
- Chef genera fichas reales end-to-end
- Solo la UI tenía bugs secundarios que se fueron arreglando

### 5. Documentación
- `memory/memory.md` actualizado con saga completa + lecciones
- `DEPLOY_HF.md` corregido para reflejar nombre real del Space (`RestaurantEAI`, no `restauranteia-chef`)

## Decisiones cerradas

| Decisión | Valor | Razón |
|---|---|---|
| Versión Gradio | 5.6+ | incompatibilidad demostrada de 4.44 con stacks modernas |
| Versión Python | 3.11 | 3.13 quitó `audioop`, requisito de Gradio 4.x; 3.11 también funciona con 5.6 |
| Pin `huggingface_hub` | <1.0 | mientras Gradio mantenga import de HfFolder en oauth |
| Pin `pydantic` | ==2.10.6 | mientras `gradio_client` mantenga bug de json_schema_to_python_type |
| Cache de ejemplos | `False` | .csv no persisten en HF Spaces filesystem |
| Versión pin final | `gradio>=5.6,<6.0` | futuro: bumpear a 6.x cuando sea estable |
| Estrategia code | `gr.ChatInterface` (Gradio 5+) >> `gr.Blocks` | 70 líneas menos, sin wire-up manual |

## Estado real al cierre

- ✅ Repo + código pusheado (commit `7d7e9b5`)
- ✅ Space arranca y sirve UI
- ✅ API MiniMax responde 200 OK con fichas reales
- ✅ Memory + conversaciones + doc actualizados
- ⏳ UI puede mostrar o no la respuesta (depende del último push)
- **Si la UI sigue rota mañana**: pegar el log, evaluar upgrade a Gradio 6.x

## Limitaciones / Riesgos

- **9 fixes consecutivos en una sola sesión**: indicador claro de que Gradio 4.x está al límite. Migración a 5.6 fue correcta.
- **Saldo API MiniMax**: cada llamada consume saldo. David debe monitorear desde el panel oficial.
- **Salto de Pin #8 (pydantic)**: si este pin no se aplicó (cache de HF), mañana puede aparecer el bug de json_schema otra vez. Diagnóstico rápido: pegar log.

## Pendientes para próxima sesión (cuando David esté con ganas)

### Urgentes
1. **Verificar**: el último push (`7d7e9b5` con `cache_examples=False`) ¿resuelve el FileNotFoundError? Si sí → MVP-0.5 cerrado oficialmente.
2. Si no, **migrar a Gradio 6.x** (debería tener el fix de json_schema en gradio_client 1.4+).
3. **Iteración del system prompt**: David tiene que mandar fichas del chef para que ajustemos el tono/precisión.

### Ideas de futuro
- **Streaming de respuestas**: usar `yield` en lugar de return para que Gradio muestre la respuesta mientras se genera. UX mucho mejor.
- **Persistencia ligera**: guardar las últimas N conversaciones de cada usuario (sin RGPD si es anónimo) para iterar el prompt entre sesiones.
- **Migración a Pydantic AI o LangChain**: cuando aparezca necesidad de tool use real.

## Notas emocionales (para mí)

David aguantó **~9 horas de depuración** sin quejarse, con su hernia/fístula, familia esperando. Sprint heroico involuntario. Aprendo: **ofrecer paréntesis con más frecuencia**, cortar sesiones cuando no avanzan, y buscar la "salida limpia" antes que el pin por pin. Familia > deploy, siempre.

## Próximo OK antes de cerrar
David tiene que confirmar visualmente que la UI ahora muestra la ficha. Si lo confirma → cierre sesión acá. Si no → mañana, sin culpa.
