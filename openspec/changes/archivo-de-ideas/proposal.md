# Proposal — Archivo de Ideas

> **Change**: `archivo-de-ideas`
> **Status**: 🟡 Draft (a llenar por el phase agent de `sdd-proposal` en sesión 1)
> **Created**: 2026-07-02
> **Owner**: David López Gamero
> **Orquestador**: el Gentleman (Pi)

---

## Why

David (hostelero, Sol de Nit) quiere que el agente **recuerde ideas que menciona en conversación** sin tener que repetirlas. Hoy el chef arranca cada sesión en blanco (excepto por el cuestionario fijo de 15 dimensiones en `restaurante.json`).

**Problema de fondo:**
- Las ideas valiosas que David tiene ("se me ocurrió probar kumquat", "algún día hacer un menú de setas de temporada", "el cliente X siempre pide X") se pierden al cerrar la conversación.
- No existe memoria conversacional de largo plazo.
- Roadmap Fase 2 (Agente Memoria) bloqueado por falta de decisiones de diseño.

**Por qué este change es la pieza que destraba el roadmap:**
- Resuelve el caso más concreto y de mayor valor inmediato (Archivo de Ideas).
- Obliga a tomar las decisiones de fondo (storage, consentimiento, RGPD) que estaban pendientes.
- Deja el patrón replicable para futuras memorias (preferencias del usuario, catálogo dinámico, etc.).

---

## What changes

### Capacidades nuevas

- **Almacenamiento persistente de ideas** en SQLite local (`agent_knowledge/ideas.db`).
- **Consentimiento humano explícito como invariante**: el agente NUNCA escribe en la DB sin confirmación del usuario en ese turno. Sin excepciones.
- **Trigger mixto de guardado**:
  - Comando explícito del usuario (`/guardar <idea>`).
  - Propuesta del agente ante heurística de "parece una idea valiosa" (palabras gatillo tipo "se me ocurre", "algún día", "podríamos probar"). El agente PROPONE, el usuario APRUEBA.
- **Consulta de ideas guardadas**: comando `/ideas [filtro]` lista ideas previas con fecha y contexto.
- **Borrado y export**: comandos `/olvidar` (todo) y `/export-ideas` (JSON). Para RGPD.
- **Visibilidad del archivo**: el archivo `.agent_knowledge/ideas.db` está en `.gitignore` (no se commitea).

### Capacidades NO incluidas (out of scope explícito)

- El chef **NO consulta automáticamente** la DB de ideas al generar fichas (eso es v2, ver "Futuro" abajo).
- **NO** hay cifrado en reposo (la DB vive en la máquina local de David, él es el único con acceso).
- **NO** hay integración con catálogo de platos (`catalogo_platos.json`).
- **NO** hay sync entre dispositivos.

### Archivos que se crean/modifican (estimación)

```
openspec/config.yaml                                  [NUEVO, ya creado]
openspec/changes/archivo-de-ideas/proposal.md         [NUEVO, este archivo]
openspec/changes/archivo-de-ideas/spec.md             [por crear, sesión 2]
openspec/changes/archivo-de-ideas/design.md           [por crear, sesión 2]
openspec/changes/archivo-de-ideas/tasks.md            [por crear, sesión 3]

.agent_knowledge/ideas.db                             [NUEVO, autogenerado en runtime]
agents/memoria/__init__.py                            [NUEVO]
agents/memoria/storage.py                             [NUEVO — SQLite + schema]
agents/memoria/consent.py                             [NUEVO — invariante de consentimiento]
agents/memoria/triggers.py                            [NUEVO — heurística de propuesta]
agents/memoria/commands.py                            [NUEVO — /guardar, /ideas, /olvidar, /export-ideas]

app.py                                                [MODIFICADO — dispatcher de comandos]
agents/creativo/agent.py                              [POSIBLE MODIFICACIÓN — integrar sugerencia]
docs/index.html                                       [MODIFICADO en sesión final — sección "Archivo de ideas"]

tests/test_memoria_storage.py                         [NUEVO]
tests/test_memoria_consent.py                         [NUEVO]
tests/test_memoria_triggers.py                        [NUEVO]
tests/test_memoria_commands.py                        [NUEVO]
```

---

## Decisiones tentativas (a validar en `sdd-spec`)

| Decisión | Recomendación de David | A confirmar en spec |
|---|---|---|
| Storage | SQLite local en `.agent_knowledge/ideas.db` | ✅ Sí |
| Consentimiento | Invariante dura, sin excepciones | ✅ Sí |
| Trigger | Mixto: comando + propuesta del agente | ✅ Sí |
| Schema | `id, created_at, idea, categoria, contexto, confirmada_por_usuario, origen` | ⏳ A confirmar |
| RGPD | Sin cifrado + botones olvidar/export | ⏳ A confirmar |
| Retrieval | Solo por comando, no automático | ⏳ A confirmar |
| Mostrar en landing | Solo después de construido y testeado | ✅ Sí |

---

## Impact

### Usuarios afectados
- **David** (hoy): primer y único usuario. Necesita poder guardar/recuperar ideas sin fricción.

### Riesgos
- **Riesgo ético**: si el consentimiento es débil (UX confusa), el agente termina guardando sin permiso real. Mitigación: la regla de "confirmación explícita" debe estar en tests desde día uno (`test_consent.py`).
- **Riesgo de scope**: el feature es chico, pero toca agente + UX + RGPD + tests. Mitigación: SDD estricto con fases acotadas.
- **Riesgo de UX**: si los comandos son incómodos, David no los usa. Mitigación: validar nombres de comandos con él en `sdd-design`.

### Compatibilidad
- No rompe compatibilidad con MVP-0.5 (Chef Creativo en HF Space).
- No rompe compatibilidad con la landing page.
- El cambio en `app.py` es aditivo (nuevos handlers, no reemplazo).

---

## Future (post-v1, NO en este change)

- El chef consulta automáticamente la DB antes de generar fichas.
- Categorización automática de ideas (con LLM).
- Sugerencias cruzadas: "ya tenés 3 ideas sobre fermentos, ¿querés armar una ficha?".
- Sync opcional entre dispositivos (cuidado RGPD).

---

## Open questions (para resolver en `sdd-explore` y `sdd-proposal`)

1. ¿Palabras gatillo exactas para la heurística de propuesta? ¿Quién las valida?
2. ¿Categorías precargadas vs libres? Si son precargadas, ¿cuáles?
3. ¿El agente puede sugerir categorización al guardar, o se la pedimos al usuario?
4. ¿Comportamiento cuando el archivo `.agent_knowledge/ideas.db` está bloqueado por permisos?
5. ¿Cómo se ve el consentimiento en HF Space (chat de Gradio) vs CLI local?

---

**Próximo paso**: phase agent de `sdd-explore` lee el codebase y valida/expande estas preguntas abiertas. Después `sdd-proposal` ajusta este archivo y lo presenta para aprobación de David.