# Design — init-web

> **Change**: `init-web` · **Fase**: `sdd-design` · **Estado**: BORRADOR para review de David
> **Base**: [`spec.md`](../../specs/init-web/spec.md) (22 RFs + 11 CAs + decisiones cerradas)
> **Convención**: snippets en Python/Gradio 6.19, ASCII wireframes para UI, ASCII tables para estructuras de datos.

## Resumen del diseño

La implementación es **una nueva pestaña en `app.py`** llamada "Configurar mi restaurante" + 3 componentes en `agents/knowledge_context.py` para carga/guarda segura. Todo lo demás reusa código existente.

**Cambio principal**: `app.py` pasa de 467 a ~850 líneas (+383, dentro del budget). `agents/knowledge_context.py` +80 líneas. Tests nuevos: `scripts/test_init_web.py` con ~150 líneas.

---

## Estructura de archivos (DD-1)

```
agents/
├── knowledge_context.py       (+80 líneas: helpers de carga/guarda segura)
├── init_phase.py              (sin cambios, reusa total)
├── init_options.json          (sin cambios)
└── creativo/
    └── knowledge/
        ├── demo_restaurante.json     (sin cambios, reusa)
        └── demo_catalogo_platos.json (sin cambios, reusa)

app.py                          (+383 líneas: pestaña Configurar)
├── _SKILL_PROMPTS                       (sin cambios)
├── _responder_chat()                    (sin cambios)
├── _responder_ideas_creativas()         (sin cambios)
├── _responder_proceso_creativo()        (sin cambios)
├── _responder_ficha()                   (sin cambios)
├── _seed_demo_profile()                 (sin cambios)
├── _estado_perfil()                     (sin cambios)
└── NUEVO: módulo _init_web_tab()       (~380 líneas, separado por claridad)

scripts/
└── test_init_web.py              (nuevo, ~150 líneas)

docs/
├── SECURITY.md                  (+15 líneas: sección auth)
├── index.html                   (+5-10 líneas: copy open core)
├── CHANGELOG.md                 (+25-30 líneas: v1.5.0)
└── README.md                    (+5-10 líneas: roadmap)

SECURITY.md                      (sección auth: HF OAuth + riesgos)
VERSION                          (v1.4.0 → v1.5.0)
.github/ISSUE_TEMPLATE/          (sin cambios)
.github/PULL_REQUEST_TEMPLATE.md (sin cambios — los checks actuales cubren esto)
```

## Wireframe de la UI (DD-2)

### Pestaña "Chat" (existente — sin cambios)

```
┌──────────────────────────────────────────────────────┐
│ 🧪 Demo: Restaurante de demostración · Volver a la web │
├──────────────────────────────────────────────────────┤
│ [Ficha técnica] [Proceso creativo] [Ideas] [Chat]    │ ← skill selector
├──────────────────────────────────────────────────────┤
│ [Chat existente, sin cambios]                       │
└──────────────────────────────────────────────────────┘
```

### Pestaña "Configurar mi restaurante" (NUEVA)

```
┌──────────────────────────────────────────────────────┐
│ 🍂 Chef Creativo — RestaurantEAI                    │
├──────────────────────────────────────────────────────┤
│ 🧪 Demo: Restaurante de demostración · Volver a la web │
├──────────────────────────────────────────────────────┤
│ [Chat] [⚙️ Configurar mi restaurante]                │ ← tab selector
├──────────────────────────────────────────────────────┤
│ ⚠️ Importante: el HF Space free duerme los procesos. │
│    Tu configuración se pierde en cold starts. Para  │
│    uso real, montá tu instancia privada.             │
│                                                     │
│ ▼ Datos del restaurante                             │
│   Nombre del restaurante:  [_____________________]   │
│   Ticket mínimo (€):      [______]                  │
│   Ticket máximo (€):       [______]                  │
│   Ticket típico (€):       [______]                  │
│   Sofisticación:           [▼ media            ]    │
│   Productos dominantes:    [✓ vegetales] [✓ pescado] │
│                            [✗ carne] [✓ mariscos]    │
│                            [ ] Otra (escribir):     │
│                            [_____________________]   │
│   ... (resto de las 15 dims, mismo patrón)          │
│                                                     │
│ ▼ Carta del restaurante                              │
│   [Modo: Pegar carta completa | Manual]              │
│   Si "Pegar carta completa":                         │
│     [_________________textarea_______________]      │
│     [Extraer estructura ⏳]                          │
│   Si "Manual" o tras extracción:                     │
│     Buscar: [_________________________]              │
│     Página 1/4                                        │
│     ┌──────────────────────────────────────┐          │
│     │ nombre | categoría | descripción | € │          │
│     │ Tomate de ramallet | entrante | ... | 14│       │
│     │ Coca de trampó | entrante | ...    | 12│       │
│     │ ... (25 filas)                      │          │
│     │ [<] [1] 2 3 4 [>]                       │          │
│     └──────────────────────────────────────┘          │
│     [+ Agregar fila]  [– Borrar seleccionadas]      │
│                                                     │
│ ▼ Acciones                                           │
│   [💾 Guardar cambios]  [🔄 Restaurar perfil demo]   │
│   [📋 Ver JSON] (colapsable)                        │
│                                                     │
└──────────────────────────────────────────────────────┘
```

### Vista "Ver JSON" (RF-23)

```
▼ 📋 Ver JSON

▼ restaurante.json
  ┌──────────────────────────────────────┐
  │ {                                    │
  │   "demo": true,                      │
  │   "nombre": "Restaurante de demo",   │
  │   "precio_target_min": 25,           │
  │   ...                                │
  │ }                                    │
  └──────────────────────────────────────┘
  [📋 Copiar]

▼ catalogo_platos.json
  ┌──────────────────────────────────────┐
  │ [                                    │
  │   { "nombre": "Tomate...", ... },    │
  │   ...                                │
  │ ]                                    │
  └──────────────────────────────────────┘
  [📋 Copiar]
```

## Estructura de datos (DD-3)

### Inputs de las 15 dimensiones

Gradio widgets por tipo (mismo patrón que `app.py` actual con `skill_selector`):

| Pregunta (key) | Tipo | Widget | Choices default |
|---|---|---|---|
| `nombre` | text | `gr.Textbox` | — |
| `precio_target_min` | number | `gr.Number` | — |
| `precio_target_max` | number | `gr.Number` | — |
| `precio_target_moda` | number | `gr.Number` | — |
| `sofisticacion` | choice | `gr.Dropdown` | de init_options.json |
| `productos_dominantes` | multichoice | `gr.CheckboxGroup` + `gr.Textbox` | de init_options.json |
| `tecnicas_dominantes` | multichoice | `gr.CheckboxGroup` + `gr.Textbox` | de init_options.json |
| `tipo_servicio` | multichoice | `gr.CheckboxGroup` + `gr.Textbox` | de init_options.json |
| `grupos` | choice | `gr.Dropdown` | de init_options.json |
| `clases_comedores` | multichoice | `gr.CheckboxGroup` + `gr.Textbox` | de init_options.json |
| `origen_inspiracion` | choice | `gr.Dropdown` | de init_options.json |
| `orientacion_nutricional` | multichoice | `gr.CheckboxGroup` + `gr.Textbox` | de init_options.json |
| `localizacion` | choice | `gr.Dropdown` | de init_options.json |
| `religion` | multichoice | `gr.CheckboxGroup` + `gr.Textbox` | de init_options.json |
| `tiempo_preparacion` | choice | `gr.Dropdown` | de init_options.json |
| `epoca_estilo` | multichoice | `gr.CheckboxGroup` + `gr.Textbox` | de init_options.json |

### Patrón para renderizar desde `PREGUNTAS_RESTAURANTE`

Helper que genera los widgets data-driven:

```python
def _render_inputs_restaurante() -> dict[str, gr.components.Component]:
    """
    Genera widgets Gradio desde PREGUNTAS_RESTAURANTE.
    Devuelve {key: widget} para usar en la UI.
    Los valores default vienen del restaurante actual (o vacío si no existe).
    """
    from agents.init_phase import PREGUNTAS_RESTAURANTE
    from agents.knowledge_context import cargar_restaurante
    
    restaurante = cargar_restaurante() or {}
    widgets = {}
    
    for q in PREGUNTAS_RESTAURANTE:
        key = q["key"]
        valor_actual = restaurante.get(key)
        choices = _opciones_para_widget(key)  # lee init_options.json
        
        if q["type"] == "number":
            widgets[key] = gr.Number(
                label=q["prompt"],
                value=valor_actual if valor_actual is not None else None,
                info=q.get("help"),
                precision=0 if "ticket" in key or "precio" in key else 2,
            )
        elif q["type"] == "choice":
            widgets[key] = gr.Dropdown(
                label=q["prompt"],
                choices=choices,
                value=valor_actual if valor_actual in choices else None,
                info=q.get("help"),
            )
        elif q["type"] == "multichoice":
            widgets[key] = gr.CheckboxGroup(
                label=q["prompt"],
                choices=choices,
                value=[v for v in (valor_actual or []) if v in choices],
                info=q.get("help"),
            )
        elif q["type"] == "text":
            widgets[key] = gr.Textbox(
                label=q["prompt"],
                value=valor_actual or "",
                info=q.get("help"),
                lines=1,
            )
    
    return widgets
```

## Snippet del módulo `_init_web_tab()` en `app.py` (DD-4)

Estructura del código nuevo en `app.py` (separado en módulo `_init_web_tab()` para mantener `app.py` legible):

```python
def _render_init_web_tab() -> dict:
    """
    Renderiza la pestaña 'Configurar mi restaurante'.
    Devuelve {componente_id: componente} para usar en gr.Tabs().
    
    Estructura:
      - Disclaimer de persistencia efímera (siempre visible)
      - Accordion "Datos del restaurante" con los 16 widgets de las 15 dims + nombre
      - Accordion "Carta del restaurante" con tabs Pegar/Manual + Dataframe
      - Accordion "Acciones" con botones Guardar/Restaurar/Ver JSON
      - JSON viewer colapsable
    
    Estado en gr.State (no en globales):
      - state_restaurante: dict actual en memoria
      - state_catalogo: list actual en memoria
      - state_pagina: int (paginación)
      - state_busqueda: str (filtro en vivo)
    """
    # ... ~380 líneas ...


def _handle_guardar(restaurante_dict, catalogo_list, state_es_demo, state_existe):
    """
    Handler del botón 'Guardar cambios'.
    
    Lógica:
      1. Validar tipos (tipos de los 15 dims contra schema)
      2. Si state_existe (alguno existe):
         - Mostrar modal de confirmación (gr.Group visible=True)
         - Si confirma → llamar a _save_with_guard()
      3. Si state_no_existe:
         - Llamar a _save_with_guard() directo
    
    Retorna: dict con {toast: str, status: "saved"|"cancelled"|"error"}
    """
    # ... ~60 líneas ...


def _save_with_guard(restaurante_dict, catalogo_list):
    """
    Guarda con guard explícito (mitiga bug F1 de explore.md).
    
    Args:
        restaurante_dict: dict con los 15+1 dims
        catalogo_list: lista de platos
    
    Returns:
        (success: bool, message: str)
    
    Lógica:
      - Si restaurante_existe() y el restaurante actual NO es demo:
        - NO sobrescribir. Crear backup en .agent_knowledge/backups/<ts>.json
        - Devolver (False, "Backup creado, archivo preservado")
      - Si restaurante_existe() pero el actual SÍ es demo:
        - Sobrescribir (es esperado)
      - Si restaurante_existe() es False:
        - Crear nuevo
      - Mismo patrón para catálogo
    
    IMPORTANTE: este helper SIEMPRE valida ANTES de guardar.
    """
    # ... ~40 líneas ...


def _handle_restaurar_demo():
    """
    Handler del botón 'Restaurar perfil demo'.
    
    Pre-condición: el restaurante actual debe tener demo=True.
    Si no, devolver error (botón está deshabilitado en UI pero doble check).
    
    Returns:
        (success: bool, message: str, new_state)
    """
    # ... ~30 líneas ...


def _render_catalogo_editor(catalogo: list[dict]) -> tuple:
    """
    Renderiza el editor de catálogo con paginación + búsqueda.
    
    Args:
        catalogo: lista completa de platos
    
    Returns:
        (dataframe_component, pagination_state, search_state)
    
    Lógica:
      - Filtra por búsqueda (case-insensitive, LIKE)
      - Pagina a 25 filas
      - Devuelve el slice actual
    """
    # ... ~50 líneas ...


def _handle_pegar_carta(carta_texto: str, state_actual: list[dict]):
    """
    Handler del botón 'Extraer estructura' (modo pegar carta).
    
    Args:
        carta_texto: texto pegado por el usuario
        state_actual: catálogo actual en memoria
    
    Returns:
        (preview_dataframe, status_markdown, confirm_button_visible)
    
    Lógica:
      - Llama a _extraer_platos_de_carta(carta_texto) (de init_phase.py)
      - Renderiza en gr.Dataframe editable
      - Muestra count: "✓ 12 platos extraídos. Revisá y guardá."
    """
    # ... ~30 líneas ...
```

## Cambios en `agents/knowledge_context.py` (DD-5)

```python
def cargar_restaurante_con_default(default: dict | None = None) -> dict:
    """
    Como cargar_restaurante() pero devuelve `default` si el archivo no existe
    (en vez de raise FileNotFoundError). Útil para la UI web.
    """
    if not restaurante_existe():
        return default or {}
    return cargar_restaurante()


def cargar_catalogo_con_default(default: list | None = None) -> list:
    """Como cargar_catalogo() pero devuelve default si no existe."""
    if not catalogo_existe():
        return default or []
    return cargar_catalogo()


def guardar_con_backup(
    data: dict, schema_doc: str | None = None,
    backup_dir: str | None = None,
) -> tuple[bool, str]:
    """
    Guarda restaurante.json con backup automático del archivo previo.
    
    Returns:
        (success, message)
        - success=True si guardó OK
        - message describe qué pasó (incluye path del backup si lo hubo)
    
    Si no existe archivo previo, no crea backup (no hay nada que respaldar).
    Si existe archivo previo, lo copia a backup_dir/<sesion_id>.json antes de sobrescribir.
    """
    # ... ~30 líneas ...


def guardar_catalogo_con_backup(
    platos: list[dict], schema_doc: str | None = None,
    backup_dir: str | None = None,
) -> tuple[bool, str]:
    """Como guardar_con_backup() pero para el catálogo."""
    # ... ~30 líneas ...


def leer_con_backup_dir(backup_dir: str | None = None) -> list[Path]:
    """Lista todos los backups existentes (útil para UI de rollback futuro)."""
    # ... ~10 líneas ...
```

## Cambios en `app.py` para auth (DD-6)

```python
# In __main__ o antes del launch():
# auth_message = """Esta sección requiere autenticación.
# Inicia sesión con tu cuenta de Hugging Face para acceder."""

# El HF Space ya tiene OAuth nativo. Solo necesitamos:

if __name__ == "__main__":
    # ... bootstrap del contexto ...
    
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        show_error=True,
        theme=gr.themes.Soft(primary_hue="orange"),
        css=CUSTOM_CSS,
        # En HF Space, esto habilita OAuth nativo:
        auth=("davidlopezgamero", os.getenv("CONFIG_PASSWORD", "chef2024"))  # HF OAuth es separado
    )

# NOTA: el HF OAuth nativo se activa automáticamente cuando se deploya
# a HF Spaces con el flag OAuth en el README del Space. Ver DEPLOY_HF.md.
# El auth= de Gradio es para auth básica (usuario/password) en local.
```

Para HF Spaces nativo: agregar al frontmatter del README:

```yaml
---
title: Chef Creativo — RestaurantEAI
emoji: 🍂
# ... otros campos ...
hf_oauth: true  # ← NUEVO: habilita OAuth de HF en el Space
---
```

(Confirmar la sintaxis exacta del frontmatter contra docs de Gradio/HF al momento de implementar PR 2.)

## Tests (`scripts/test_init_web.py`) (DD-7)

Mismos patrones que `scripts/test_seed_demo.py` (mini-helper `check()`, sin pytest, sin red, sin API):

```python
"""
test_init_web.py
================

Tests de la UI web de configuración (Fase init-web).

Cubre:
1. cargar_restaurante_con_default() devuelve default si no existe
2. cargar_catalogo_con_default() devuelve default si no existe
3. guardar_con_backup() crea backup cuando ya existe
4. guardar_con_backup() no crea backup cuando NO existe
5. guardar_con_backup() sobrescribe correctamente
6. La pestaña "Configurar" requiere auth (la función _render_init_web_tab expone un flag)
7. El JSON viewer formatea correctamente
8. La búsqueda en vivo filtra por nombre/categoría/descripcion

Sin red, sin API, sin Gradio instalado (la UI se testea con mocks si es necesario).
"""

# 8 checks, ~150 líneas
```

## Riesgos del diseño y mitigaciones (DD-8)

| # | Riesgo | Mitigación |
|---|---|---|
| D1 | `gr.Dataframe` con catálogo >100 filas puede ser lento | Paginación a 25 + búsqueda (DD-3). Medir en PR 2. |
| D2 | HF OAuth puede no funcionar en HF Spaces free | Verificar el flag del frontmatter antes de merge. Si falla, fallback a auth= de Gradio (user/password en HF Secrets). |
| D3 | Estado en `gr.State` se pierde al cambiar de tab | Usar `gr.State` con persistencia de sesión (Gradio 6.19 lo soporta). |
| D4 | `_extraer_platos_de_carta()` puede tardar >15s y bloquear la UI | Usar `gr.Progress` (built-in en Gradio 6.19) para feedback visual. |
| D5 | El catálogo de demo genérico tiene 10 platos, no >100 — la paginación es over-engineering | OK, la paginación es "preparada para futuro" pero no visible con el seed. Aceptable. |
| D6 | El usuario autenticado puede borrar su propio perfil | UX: el botón "Restaurar demo" crea backup automático. "Borrar restaurante.json" no se expone (debe hacerse por CLI). |
| D7 | Cambio en `app.py` rompe invariantes de `test_app.py` | Verificar firma de `responder()` sigue intacta (RF-25). Test_app.py corre en CI antes del merge. |

## Estimación final

| Archivo | ΔLíneas |
|---|---|
| `app.py` | +383 |
| `agents/knowledge_context.py` | +80 |
| `scripts/test_init_web.py` | +150 (nuevo) |
| `docs/SECURITY.md` | +15 |
| `docs/index.html` | +8 |
| `CHANGELOG.md` | +28 |
| `README.md` | +8 |
| `VERSION` | +1 |
| **Total** | **~673** |

Dentro del budget de 700 líneas para el change completo.

## Siguiente fase

→ **Tasks** (`sdd-tasks`): slicing por PR, dependencies, criterios de merge.
