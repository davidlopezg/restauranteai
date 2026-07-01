# 2026-07-01 21:18 — Opciones del init externalizadas a JSON + "otra (escribir)"

## Resumen

David pidió poder extender las opciones de las preguntas del `init_phase.py` (la fase que recolecta las 15 dimensiones del restaurante) sin tocar código. Tras analizar los gaps para una pizzería mediterránea catalana, eligió la opción C (híbrida): JSON externo + fallback "otra (escribir)" en tiempo de CLI.

## Trabajo realizado

### Archivos modificados/creados

1. **`agents/init_options.json`** (NUEVO)
   - 12 preguntas con `options` externalizadas.
   - Incluye gaps detectados para pizzería mediterránea catalana:
     - `productos_dominantes`: `embutidos`, `quesos_curados`, `conservas`, `hierbas_aromaticas`, `frutos_secos`, `productos_mar_especificos`
     - `tecnicas_dominantes`: `horno_piedra` (gap crítico), `masa_larga_fermentacion`, `coccion_lenta_salsas`, `reposteria`, `marinados`
     - `tipo_servicio`: `picoteo_terraza`, `vermut_dominguero`, `menu_diario_ejecutivo`, `delivery_propio`
     - `clases_comedores`: `jovenes_nocturno`, `grupos_amigos_grandes`
     - `epoca_estilo`: `pizzeria_tradicional_italiana`, `pizzeria_contemporanea`, `casual_mediterraneo`

2. **`agents/init_phase.py`** (4 edits)
   - Loader `_cargar_opciones_externas()` que carga el JSON al import del módulo.
   - Helper `_opciones_para(key, fallback)` con precedencia JSON > código.
   - Constantes `OTRO_LITERAL` y `SUFIJO_OTRA = "otra (escribir)"`.
   - `_input_choice` ahora ofrece automáticamente "otra" al final y pide input libre.
   - `_input_multichoice` permite elegir "otra" mezclada con opciones numeradas y acepta múltiples customs separados por coma.
   - `_ask_question` dispatcha usando las opciones del JSON cuando existen.
   - `_schema_doc_restaurante` documenta el patrón de extensión.

### Tests

9/9 pasaron (ejecutados con `unittest.mock.patch` sobre `builtins.input`):
- choice: normal, custom, vacío re-pregunta
- multichoice: normal, vacío, con "otra" + customs múltiples, solo "otra", input inválido reintenta
- dispatch de `_ask_question` carga opciones del JSON correctamente

## Decisiones de arquitectura

- **Precedencia**: JSON gana sobre código cuando la key está en `init_options.json`. Si no, fallback graceful a las opciones hardcoded.
- **JSON ausente o inválido**: warning por consola + fallback a código (no rompe nada).
- **HF Space**: el init interactivo solo corre con TTY (local). En HF se siguen generando archivos vacíos automáticamente. No requiere redeploy.
- **Schema del JSON de salida (`restaurante.json`)**: sin cambios — los valores siguen siendo `string` o `list[string]`.

## Próximos pasos opcionales

- Auditar consumidores de `restaurante.json` que asuman listas cerradas (búsqueda inicial: `system_chef.md` no lo hace).
- Extender el patrón JSON + "otra" a otras dimensiones que puedan crecer (catálogo de ingredientes, productores locales).