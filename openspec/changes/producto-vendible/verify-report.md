# Verify Report — producto-vendible

> Change: `producto-vendible` · Fase: `sdd-verify` · Proyecto: `restauranteia`
> Fecha: 2026-08-05 · Orquestador: el Gentleman (verificación integral post-apply)

## Status: ✅ VERIFIED

Todos los criterios de aceptación (CA-1..CA-11) del proposal se cumplen. Verificación ejecutada por el orquestador tras completar C1-C5.

## Evidencia por criterio

| CA | Criterio | Resultado | Evidencia |
|---|---|---|---|
| CA-1 | Landing single-file trilingüe, zero-deps, default castellano | ✅ | `grep -nE "<script[^>]*src=|...|url\(https?://" docs/index.html` → **0** coincidencias. JS validado con `node --check` + diccionario LANG {es, ca, en} con **65 keys idénticas** en los 3 idiomas; `data-i18n` (64 atributos) todos resueltos. Selector ES/CA/EN en header, `lang` dinámico, default es. |
| CA-2 | "MVP-0.5" eliminado de la landing | ✅ | `grep -rn "MVP-0.5" docs/` → **0** coincidencias. |
| CA-3 | Las 4 skills reales reflejadas | ✅ | `grep -c "Ficha técnica\|Proceso creativo\|Ideas creativas\|Chat con el chef"` → **8** (≥4 requeridas). Nombres tomados del registry `agents/creativo/skills.py`. |
| CA-4 | CTA implementación = mailto con subject pre-armado | ✅ | `grep -c 'mailto:davidlopezgamero@gmail.com'` → **4** (3 subjects por idioma en diccionario + 1 href estático fallback). Subjects: es/ca/en URL-encoded, destinatario único. |
| CA-5 | Sin testimonios inventados, sin Sol de Nit, sin métricas falsas | ✅ | `grep -rni "sol de nit" docs/ agents/creativo/knowledge/` → **0**. Copy usa solo "construido por un hostelero real" + MIT + demo live. |
| CA-6 | Sección demo con visual + texto "perfil genérico" | ✅ | `grep -ni "genéric\|mediterráne"` → **3**. Visual = celda de ficha de ejemplo renderizada en HTML puro (fallback aprobado, sin playwright en entorno). |
| CA-7 | Seed demo: boot no-TTY crea perfil demo; no sobrescribe existentes; TTY intacto | ✅ | `scripts/test_seed_demo.py` → **5/5 PASS** (schema 15 keys, demo flag, valores válidos vs init_options.json, catálogo 10 platos, no-overwrite casos A/B1/B2). |
| CA-8 | Indicador de perfil en Space muestra "Demo: …" | ✅ | `grep -n "Demo" app.py` → helper `_estado_perfil()` línea 342. Componente `gr.Markdown` dentro de Blocks. C2 desplegado a HF (`f7a3c9d`). |
| CA-9 | Tests verdes | ✅ | `python scripts/test_app.py` → **6/6 PASS** (incluye fix de test_firma_responder pre-existente); `python scripts/test_seed_demo.py` → **5/5**; `python -m pytest tests/ -q` → **132 passed**. |
| CA-10 | requirements.txt sin cambios + memory documenta stack real | ✅ | `git diff requirements.txt` → **0** líneas. memory.md contiene entradas de sesión (2026-08-05) + D5 stack real de deps. |
| CA-11 | Landing live + openspec nunca a hf | ✅ | `curl -sI https://davidlopezg.github.io/restauranteai/` → **HTTP 200**. `git ls-remote hf main` = `f7a3c9d` (C3/C4/C5 NO llegaron a HF); `git ls-remote origin main` = `3d88439` (C5). `openspec/` jamás stageado. |

## Commits desplegados

| Commit | Mensaje | Remotes |
|---|---|---|
| `d109e5e` | feat(seed): perfil demo genérico + fix test_firma_responder | origin + hf |
| `f7a3c9d` | feat(ui): indicador de perfil demo + description de venta + link a la landing | origin + hf |
| `a8ba297` | docs(landing): landing trilingüe orientada a conversión (open core) | origin solo |
| `a23562e` | docs(memory): stack real de deps (D5) + README drift 3→4 skills | origin solo |
| `3d88439` | chore(version): bump v1.3.0 → v1.4.0 | origin + tag v1.4.0 |

## Desviaciones documentadas (aprobadas en el proceso)

1. **`guardar_*` sobrescribe siempre**: hallazgo del apply — `_seed_demo_profile()` implementa guard por archivo faltante (`restaurante_existe()`/`catalogo_existe()`), no sobreescribe perfil real (RF-13).
2. **Orden módulo vs __main__**: el Blocks se construye a nivel de módulo antes del seed; helpers movidos arriba + `perfil_md.value = _estado_perfil()` re-evaluado tras el seed (riesgo T4 del design, resuelto).
3. **test_firma_responder roto pre-existente**: corregido test-only (la firma real tiene 3 args con default; el código no cambió).
4. **Visual de demo = celda HTML pura** (fallback aprobado): el entorno no tiene playwright/navegador; la celda cumple CA-6; screenshots reales quedan como mejora.
5. **Landing i18n**: mailto movido al diccionario (`data-i18n-href`) para subjects por idioma; href estático castellano como fallback en el HTML.
6. **Space UI en castellano neutro**: description del ChatInterface en neutro peninsular (decisión 10); label/info del `skill_selector` aún en voseo (fuera de scope C2, anotado como follow-up opcional).

## Riesgos residuales

- **Rendering real del Space**: Gradio no está instalado localmente (Python 3.13); la UI se verificó vía AST/greps/tests. El deploy a HF está hecho; validación visual final en el Space queda como paso manual de David.
- **Cold start del Space free**: primera visita tarda; mitigado con copy en landing (decisión 13).
- **Screenshots reales de la demo**: pendientes como mejora (CA-6 cumplido con celda HTML).
- **`skill_selector` voseo**: follow-up opcional de 2 líneas si David quiere neutralidad total del Space.

## Decisión

✅ **VERIFIED** — listo para `sdd-sync` + `sdd-archive`.
