# Explore — Archivo de Ideas (validado por David)

## Hallazgo
Skill `ideas_creativas` YA EXISTE (genera 10 ideas por LLM, ephemeral).
Archivo de Ideas es complemento persistente, no duplicado.

## Decisiones validadas por David (2026-07-02)
1. D4 comandos transversales OK + refuerzo: `/guardar` debe funcionar con ideas que NO vengan de ideas_creativas
2. Nombres de comandos OK
3. Categorías OK (con plan para cambiarlas: JSON externo)
4. Palabras gatillo OK
5. Schema OK (libertad para detalles)

## 3 variantes de `/guardar` diseñadas
- `/guardar [texto]` → texto literal libre, cualquier skill
- `/guardar` (sin args) → último mensaje del agente
- `/guardar N` → idea N de la última respuesta (caso típico desde ideas_creativas)

## Lección operativa
`sdd-explore` no tiene `write`/`edit`. Tuve que sintetizar yo el explore.md.
Workaround para próximas fases SDD: pedir al subagent que devuelva el contenido del artifact como string, yo lo persisto.
