# 📣 Plan de lanzamiento — RestaurantEAI

> **Fecha objetivo**: semana del 2026-09-01 al 2026-09-07.
> **Audiencia target**: hosteleros catalanes, devs con interés en foodtech, early adopters de IA en restauración, comunidad open source.
> **Stack de canales**: HN, Reddit, Twitter/X, LinkedIn, Product Hunt (opcional), outreach directo.

## 🎯 Objetivo del lanzamiento

**Awareness + feedback temprano**, no viralidad. El target es conseguir:

- 50-200 stars en GitHub en el primer mes.
- 5-15 usuarios que prueben la demo y dejen feedback.
- 3-5 conversaciones con hosteleros con potencial de implementación.
- 1-2 colaboraciones técnicas (código, traducciones, feedback arquitectónico).

**No estamos buscando viralidad inmediata**: el modelo open core se valida con conversaciones, no con likes.

## 📅 Cronograma de la semana

| Día | Acción | Asset |
|---|---|---|
| Lunes | Publicar post en dev.to (cross-post con Medium) | [blog-post.md](blog-post.md) |
| Lunes | Thread de Twitter/X (11 tweets) | [twitter-thread.md](twitter-thread.md) |
| Martes | Post en Reddit r/MachineLearning + r/sideproject + r/restauranteur | Adaptación del blog post (más corto, tono comunidad) |
| Miércoles | Submit a Hacker News (Show HN) | [show-hn.md](show-hn.md) |
| Jueves | Outreach directo: 15 emails | [outreach-templates.md](outreach-templates.md) |
| Viernes | Recopilar feedback, ajustar FAQ de la landing, segunda oleada de outreach | — |

## 📊 Métricas a trackear

Subir a `docs/METRICS.md` al final del día:

| Métrica | Baseline | Target día 7 | Target día 30 |
|---|---|---|---|
| Stars GitHub | 0 | 50-100 | 200+ |
| Forks | 0 | 5-15 | 30+ |
| Visits HF Space | ~0 | 200-500 | 1000+ |
| Issues abiertos (feedback/bugs) | 0 | 3-10 | 15+ |
| Mensajes de outreach | 0 | 5-15 | 25+ |
| Conversaciones de implementación | 0 | 1-3 | 3-7 |
| Posts en redes (likes/reshares) | 0 | 50-200 | 200-500 |

## 🚨 Riesgos y planes de contingencia

| Riesgo | Mitigación |
|---|---|
| HN top → mantener 12h respondiendo TODO | Calendario bloqueado. Si no podés, responder en 24h. |
| HN flop (no llega a frontpage) | No resubmit. Esperar 2 semanas, intentar ángulo diferente. |
| Crítica muy dura ("es solo un wrapper") | Responder con elegancia ("Sí, el wrapper es el contexto"). |
| Bug reportado en el Space | Acknowledgement público + fix inmediato + update en thread. |
| Pregunta sobre privacidad de datos | Responder con [SECURITY.md](../../SECURITY.md) y "demo pública no es para uso real". |
| Outbound rate-limited / bounced | Esperar 24h antes de segundo intento. |

## 📋 Pre-lanzamiento (checklist del lunes)

- [ ] El CI de GitHub Actions está verde en `main`.
- [ ] La landing `https://davidlopezg.github.io/restauranteai/` carga sin errores.
- [ ] El HF Space `https://huggingface.co/spaces/davidlopezgamero/RestaurantEAI` está "Running" y responde en <30s.
- [ ] El perfil demo está cargado y la 4ª skill (`chat`) funciona.
- [ ] Las 4 capturas reales están en la landing y se ven bien.
- [ ] El repo público tiene LICENSE, CONTRIBUTING, CHANGELOG, CODE_OF_CONDUCT, SECURITY.
- [ ] El README tiene la sección "¿Por qué este proyecto?" y un quote-block de ejemplo.
- [ ] El blog post está revisado (ortografía, links rotos).
- [ ] El thread de Twitter está guardado como borrador.
- [ ] 15 emails de outreach están personalizados y listos.
- [ ] El calendario de la semana está libre para responder feedback.

## 📚 Assets listos

| Archivo | Contenido | Estado |
|---|---|---|
| [blog-post.md](blog-post.md) | Post completo (~2.000 palabras) para dev.to/Medium | ✅ Listo |
| [twitter-thread.md](twitter-thread.md) | 11 tweets + variante LinkedIn standalone | ✅ Listo |
| [show-hn.md](show-hn.md) | Post HN + respuestas anticipadas a 9 preguntas | ✅ Listo |
| [outreach-templates.md](outreach-templates.md) | 3 templates personalizables (hostelero, foodie, dev) | ✅ Listo |

## 📝 Post-lanzamiento (semana 2)

- Responder a TODOS los issues abiertos en GitHub en 48h.
- Agradecer públicamente a los que dejaron feedback (Twitter + GitHub).
- Cerrar issues que ya no aplican.
- Abrir issues nuevos derivados del feedback.
- Considerar follow-up HN si el ángulo cambia.

## 🙏 Agradecimientos

A todos los que prueban, reportan bugs, sugieren mejoras o comparten. El proyecto se construye así: una idea, un commit, una conversación a la vez.

---

**Nota sobre privacidad**: ninguno de los assets de lanzamiento menciona "Sol de Nit" ni datos de clientes reales. La demo pública es con perfil genérico. Regla memoria 2026-07-02: **nada de datos reales en superficies públicas**.
