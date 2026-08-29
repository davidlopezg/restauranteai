# Pull Request

> Gracias por contribuir al Chef Creativo 🍂. Por favor, completá este template antes de pedir review.
>
> Leé primero [CONTRIBUTING.md](../CONTRIBUTING.md) si no lo hiciste — hay reglas duras que pueden hacer que tu PR sea rechazado o revertido.

## 📋 Descripción

<!-- ¿Qué cambia este PR? ¿Por qué? Referenciá el issue si existe (ej: "Fixes #123"). -->

### Tipo de cambio

<!-- Marcá con [x] lo que aplique. -->

- [ ] 🐛 Bug fix (cambio que arregla un problema sin romper funcionalidad existente)
- [ ] ✨ Nueva feature (cambio que agrega funcionalidad sin romper existente)
- [ ] ⚠️ Breaking change (fix o feature que **rompe** compatibilidad — ver "Notas para el maintainer")
- [ ] 📚 Docs (solo cambios en documentación)
- [ ] 🧪 Tests (solo cambios en tests)
- [ ] 🔧 Refactor / chore (cambio interno sin efecto funcional observable)
- [ ] ⚡ Performance (cambio que mejora performance sin tocar API)

### Issues relacionados

<!--
- Fixes #N (issue que cierra)
- Relates to #N (issue relacionado, no cierra)
- Bloqueado por #N (PR dependiente)
-->

## ✅ Checklist

### Reglas duras (leer antes de pedir review)

> Estas reglas están en [CONTRIBUTING.md](../CONTRIBUTING.md#-reglas-duras-invariantes-del-proyecto). Si tu PR las viola, va a ser rechazado o revertido.

- [ ] **Sin datos reales en superficies públicas**: no incluí nombres de restaurantes reales, platos de clientes reales, ni outputs generados con perfil real. Usé el perfil demo (`demo: true`) o un restaurante ficticio en cualquier ejemplo/captura/fixture.
- [ ] **Sin API keys ni secrets**: no commiteé mi `.env`, no pegué keys en código ni en logs de tests. Verifiqué con `git diff --cached | grep -iE '(api[_-]?key|secret|password|token).*=.*[a-zA-Z0-9]{20,}'`.
- [ ] **No cambié `requirements.txt`** sin issue previo (o lo cambié **solo** para fixear algo acordado).
- [ ] **No cambié `.gitignore`** sin issue previo.
- [ ] **No cambié la firma de `responder()`** (o si lo hice, actualicé `scripts/test_app.py` en el mismo commit y está documentado en "Notas").
- [ ] **No subí `openspec/`, `.pi-subagents/`, ni `.pi/` a `hf`** (push a `hf` solo de código que corre en el Space).

### Tests

- [ ] Agregué tests para el cambio nuevo (o documenté por qué no aplica).
- [ ] Corrí localmente las 3 suites y todas pasan:
  - [ ] `python scripts/test_app.py` (esperado: 6/6)
  - [ ] `python scripts/test_seed_demo.py` (esperado: 5/5)
  - [ ] `python -m pytest tests/ -q` (esperado: 132+ tests)
- [ ] Si agregué un script de tests nuevo, sigue el patrón de `scripts/test_*.py` (mini-helper `check()` + `main() -> int` con exit code).

### Docs

- [ ] Actualicé el README si el cambio afecta comandos, skills, despliegue o estructura.
- [ ] Actualicé `docs/COMMANDS.md` si agregué/modifiqué un comando.
- [ ] Actualicé `docs/index.html` (en sus 3 idiomas) si el cambio afecta la cara pública.
- [ ] Actualicé `CHANGELOG.md` con la entrada en la sección `[Unreleased]` (el maintainer lo mueve a la versión correcta al release).

### Idioma y estilo

- [ ] Strings visibles al usuario en **castellano neutro peninsular** (no voseo en superficies públicas; voseo OK en conversaciones con David).
- [ ] Commits en **conventional commits en inglés** (`feat(creativo): …`, `fix(app): …`, `docs(readme): …`, etc.).
- [ ] Si el PR tiene >400 líneas, sigue el patrón SDD (`openspec/changes/<nombre>/`) y los commits están apilados por unidad lógica.

## 🧪 Cómo probar localmente

<!-- Pegá los comandos exactos para que el reviewer pueda reproducir tu cambio. -->

```bash
# Pasos para reproducir
git checkout <branch>
pip install -r requirements.txt
python scripts/test_app.py
# ...
```

### Resultado esperado

<!-- Qué debería pasar al correr los pasos de arriba. -->

## 📸 Screenshots / capturas (si aplica)

<!-- Especialmente importante si el cambio toca UI. Sin datos reales. -->

## 📝 Notas para el maintainer

<!-- Todo lo que el reviewer necesita saber que no entra en los otros campos. -->
<!-- Por ejemplo: decisión de diseño no obvia, workaround aplicado, deuda técnica que queda pendiente, riesgo residual. -->

---

### Recordatorio

- **No mergear tu propio PR**: pedí al menos 1 review (idealmente de David o de quien mantenga el área que tocaste).
- **PRs pequeños < 400 líneas** se revisan y mergean más rápido. Si tu cambio es más grande, considerá partirlo o abrir un proposal SDD primero.
- Si tenés dudas, abrí un issue con la etiqueta `question` antes de empezar a codear.
