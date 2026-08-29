# Apply Progress — init-web

> **Change**: `init-web` · **Fase**: `sdd-apply` · **Inicio**: 2026-08-29
> **Estrategia**: 3 PRs stacked a `main`, merge en orden (PR 1 → PR 2 → PR 3).
> **Push**: hf para PRs con cambios de código, origin para todos.

## Estado por PR

| PR | Contenido | Tareas | Estado | Merge commit | Push |
|---|---|---|---|---|---|
| **PR 1** | Helpers + tests | T1.1..T1.6 (6/6) | ✅ MERGED | `be42ff7` / `4e31b02` (hf) | ✅ origin + ✅ hf |
| **PR 2** | UI web + auth | T2.1..T2.8 (0/8) | ⏳ Pendiente | — | — |
| **PR 3** | Docs + release | T3.1..T3.6 (0/6) | ⏳ Pendiente | — | — |

## PR 1 — Detalle

### Tareas ejecutadas (2026-08-29)

- [x] **T1.1** `cargar_restaurante_con_default()` en `knowledge_context.py` ✅
- [x] **T1.2** `cargar_catalogo_con_default()` en `knowledge_context.py` ✅
- [x] **T1.3** `guardar_con_backup()` en `knowledge_context.py` ✅
- [x] **T1.4** `guardar_catalogo_con_backup()` en `knowledge_context.py` ✅
- [x] **T1.5** `leer_con_backup_dir()` en `knowledge_context.py` ✅
- [x] **T1.6** `scripts/test_init_web.py` con 8 checks ✅

### Verificación

```
test_init_web.py:  8/8 PASS
test_app.py:       PASS
test_seed_demo.py: PASS
pytest tests/:     132 PASS
```

### Push

- `origin/main`: `2c49529..be42ff7` ✅
- `hf/main`: `f7a3c9d..4e31b02` ✅ (cherry-pick desde f7a3c9d para evitar docs/assets/*.png binarios en HF)

### Hallazgo operacional

**HF Space rechaza pushes que contengan archivos binarios** (`docs/assets/*.png`). El commit `c98517d feat(landing): capturas reales` agregó 4 PNG que viven solo en `origin/main`. Para mantener hf sincronizado sin contaminar el Space con assets de landing, se optó por **cherry-pick de cada PR sobre `hf/main`** en vez de fast-forward completo. Esto preserva hf como espejo de código puro.

## Próximo paso

→ **PR 2**: agregar pestaña "Configurar mi restaurante" a `app.py` + auth HF.