# Archive Report — producto-vendible

> Change: `producto-vendible` · Fase: `sdd-archive` · Proyecto: `restauranteia`
> Fecha: 2026-08-05

## Status: ✅ ARCHIVED

## Resumen del change

Fase 1 de "hacer vendible el producto" (open core):
- **D1** Seed demo genérico (mediterráneo, ticket 25/60/40, `demo: true`) en boot no-TTY del Space — reemplaza el perfil vacío que hacía que la demo "mintiera" (chef sin contexto).
- **D2** Landing trilingüe (es · ca · en) single-file zero-deps orientada a conversión: problema→solución, 4 skills reales, demo con visual, oferta open core con CTA mailto, FAQ, footer honesto.
- **D3** App polish: indicador de perfil, description de venta (neutro peninsular), link a la landing.
- **D5** Documentación del stack real de deps en memory + drift README 3→4 skills.
- **C5** VERSION v1.3.0 → v1.4.0 + tag.

## Artefactos del change

| Artifact | Path |
|---|---|
| explore | `openspec/changes/producto-vendible/explore.md` |
| proposal | `openspec/changes/producto-vendible/proposal.md` |
| spec | `openspec/changes/producto-vendible/specs/producto-vendible/spec.md` |
| design | `openspec/changes/producto-vendible/designs/producto-vendible/design.md` |
| tasks | `openspec/changes/producto-vendible/tasks.md` (24/24 ✅) |
| apply-progress | `openspec/changes/producto-vendible/apply-progress.md` |
| verify | `openspec/changes/producto-vendible/verify-report.md` |
| archive | `openspec/changes/producto-vendible/archive-report.md` |

## Deploy final

- origin/main: `3d88439` + tag `v1.4.0`
- hf/main: `f7a3c9d` (Space con seed demo + indicador; landing no aplica a HF)
- GitHub Pages: HTTP 200 (landing live)

## Pendiente (Fase 2 — change `init-web`)

- UI de configuración del restaurante en el navegador (para que un cliente no técnico configure su perfil sin terminal).
- Google Form como canal de leads (diferido).
- Screenshots reales de la demo (mejora opcional).
- Neutralizar voseo en `skill_selector` del Space (2 líneas, opcional).
