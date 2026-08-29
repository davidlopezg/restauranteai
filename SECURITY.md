# 🔒 Política de seguridad

> Este documento describe cómo reportar vulnerabilidades, qué versiones reciben parches, y las políticas específicas de seguridad del proyecto (incluida la política sobre la API key de MiniMax).

## 📣 Reportar una vulnerabilidad

**No abras un issue público para reportar vulnerabilidades.** En su lugar:

📧 **Email**: [davidlopezgamero@gmail.com](mailto:davidlopezgamero@gmail.com)
Asunto sugerido: `[SECURITY] RestaurantEAI — <descripción corta>`

Incluí:
- Descripción del problema y su impacto potencial.
- Pasos para reproducir (si aplica).
- Versión afectada (tag, commit, o rama).
- Tu evaluación de severidad (Crítica / Alta / Media / Baja).
- Si lo deseás, tu nombre y/o forma de contacto para seguimiento.

**Tiempo de respuesta esperado**: 3-7 días hábiles. Si el reporte es crítico, lo confirmo en 24-48h.

### Divulgación coordinada

Acepto reportes por divulgación coordinada. Si necesitás un periodo de gracia antes de hacer pública la vulnerabilidad, acordamos una fecha límite (típicamente 90 días desde el reporte).

---

## 🛡️ Versiones soportadas

| Versión | Soporte | Notas |
|---|---|---|
| `v1.4.x` (actual) | ✅ Soporte completo | Recibe parches de seguridad y bugs. |
| `v1.3.x` | ⚠️ Solo críticos | Backport de fixes críticos hasta 6 meses después del release de `v1.4.0`. |
| `v1.2.x` y anteriores | ❌ Fin de soporte | Por favor, actualizá a `v1.4.0` o superior. |

Las versiones LTS siguen el modelo de [Python](https://devguide.python.org/versions/): soporte completo durante el ciclo de release activo + 6 meses de backport de críticos.

---

## 🔐 Política específica: API key de MiniMax

> ⚠️ **Contexto**: la API key de MiniMax de este proyecto es **fija, no rotable** (plan de suscripción, no pay-as-you-go). Esto cambia la política estándar de "rotar y listo" cuando hay exposición.

### Lo que NUNCA debés hacer

1. **Commitear tu `.env`** al repositorio (ya está cubierto por `.gitignore`, pero verificá antes de cada `git add .`).
2. **Pegar tu key en issues, PRs, discussions, screenshots, logs o conversaciones** (incluso si "no se va a publicar"). Las conversaciones se persisten en logs, índices de búsqueda, y a veces se comparten.
3. **Loggear tu key en código**, ni siquiera truncada. El log puede terminar en un sistema de monitoring, en un dump de error de HF, o en un screenshot de un issue.
4. **Compartir tu key** con terceros (amigos, "para probar", etc.). Si alguien necesita probar el proyecto, que use **su propia** key.
5. **Versionar tu key en un gist público**, Notion público, o cualquier servicio accesible.

### Qué hacer si tu key quedó expuesta

Como **la key es fija y no rotable**, no podemos aplicar la mitigación estándar "rotar la key y listo". Las medidas compensatorias son:

1. **Monitoreo de uso**: revisá periódicamente el panel de MiniMax (`https://platform.minimax.io/user-center/basic-information/interface-key`) para detectar requests que vos no hiciste.
2. **Restricción de scopes** (si MiniMax lo permite): idealmente la key solo debería tener scope `chat/completions`. Si tiene más permisos, intentá degradarla.
3. **Revocar acceso al proyecto**: si la exposición es seria y no podés contenerla, lo más sano es dejar de usar esa key y crear un proyecto nuevo con una key nueva (sí, asumiendo que la key no es realmente rotable, esto es doloroso).
4. **Reportar el incidente**: en `davidlopezgamero@gmail.com` para que el incidente quede documentado y podamos prevenir casos similares.

### Cómo verifico que NO hay keys en el repo

```bash
# Buscar strings que parezcan API keys (sk-... con 32+ chars)
git grep -nE 'sk-[a-zA-Z0-9]{32,}' -- ':!*.md' ':!LICENSE' ':!.env.example'

# Verificar que .env está en .gitignore
grep -E '^\.env$' .gitignore
```

Si esto detecta algo, **es una emergencia**: tratá la key como comprometida y aplicá las medidas de arriba.

---

## 🚨 Política de secretos en general

| Tipo de secreto | Política |
|---|---|
| API keys (MiniMax) | ❌ Nunca en código ni en issues. Configurar en `.env` local o en **HF Space → Settings → Repository secrets**. |
| API keys de HF | ❌ Nunca en código. La CLI de HF (`huggingface-cli login`) las guarda localmente. |
| `.env` | ❌ En `.gitignore` siempre. Verificar con `git status` antes de commitear. |
| Tokens de GitHub | ❌ Nunca. Usar SSH keys o `gh auth login`. |
| Outputs de usuarios reales | ❌ Nunca en issues/PRs/docs públicos. Solo perfiles demo (`demo: true`). |

### Verificación rápida antes de cada commit

```bash
git diff --cached | grep -iE '(api[_-]?key|secret|password|token).*=.*[a-zA-Z0-9]{20,}'
```

Si esto matchea, **abortá el commit** (`git restore --staged <archivo>`) y revisá.

---

## 🔍 Hallazgos conocidos y su estado

### 2026-06-30 — API key comprometida en log de conversación

**Resumen**: durante el desarrollo inicial, la API key de MiniMax quedó persistida en el log de una sesión de chat (que el sistema guarda en `conversations/*.md`).

**Estado actual**:
- La key **NO** está en código, `.env.example`, ni memoria.
- La key está marcada como **comprometida** en `memory/memory.md` y **NO debe** reusarse para producción seria.
- Recomendación para uso en producción: **crear una key nueva** al deployar en una instancia privada.

**Mitigaciones aplicadas**:
- `call_minimax()` no loggea el valor de la key (solo verifica presencia).
- `.env.example` solo tiene placeholders literales.
- Las conversaciones en `conversations/` están en `.gitignore` (`*.log`, `logs/`).
- La política de este `SECURITY.md` documenta el incidente para futuros colaboradores.

---

## 📚 Referencias útiles

- [GitHub Security Advisories](https://docs.github.com/en/code-security/security-advisories) — para crear avisos de seguridad formales.
- [Hugging Face Settings → Repository secrets](https://huggingface.co/docs/hub/spaces-sdks-docker#secrets-and-environment-variables) — cómo gestionar Secrets en HF Spaces.
- [OWASP Top 10](https://owasp.org/www-project-top-ten/) — checklist general para apps web.
- [MiniMax API docs](https://platform.minimax.io/docs/guides/quickstart-preparation) — para entender los permisos de la key.

---

## 🙏 Agradecimientos

Gracias a quienes reportan vulnerabilidades de forma responsable. Si querés ser reconocido por un reporte válido, decímelo en el email y te agrego a una sección de "Reconocimientos" en releases futuros.

— David López Gamero (maintainer)
