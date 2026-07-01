# SDD — Archivo de Ideas (iniciado)

## Contexto
David propuso un feature: DB local tipo SQL donde el agente guarde ideas que el usuario mencione, con consentimiento humano como invariante. Lo llamó "archivo de ideas". Conecta con la Fase 2 (Agente Memoria) del roadmap, bloqueada desde 2026-06-30.

## Decisión
Iniciar SDD con change `archivo-de-ideas`. Preflight:
- executionMode: interactive
- artifactStore: openspec
- chainedPRStrategy: ask-always
- reviewBudget: 400

## Archivos creados
- `openspec/config.yaml` (2519 bytes) — config del proyecto + preflight
- `openspec/changes/archivo-de-ideas/proposal.md` (6330 bytes) — esqueleto

## Push
- ✅ origin (GitHub)
- ❌ hf (no aplica — son docs/dev, no tocan el Space)

## Próxima sesión
`sdd-explore` + `sdd-proposal` con David.
