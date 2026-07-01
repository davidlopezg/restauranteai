# Despliegue en Hugging Face Spaces — Paso a paso

> **Para:** David (username `davidlopezgamero`)
> **Nombre del Space real:** `RestaurantEAI` (NO `restauranteia-chef` — corregido 2026-07-01).
> **Objetivo:** deployar `app.py` (Gradio) en HF Spaces con la opción **A + C**: Secret cifrado + Space con link privado.
> **Tiempo estimado total:** 20-40 minutos la primera vez.

---

## ✅ Prerrequisitos

- [x] Cuenta en Hugging Face creada (username: `davidlopezgamero`)
- [ ] Código del proyecto en una carpeta local (la que ya tenés: `~/repos/restauranteia`)
- [ ] API key de MiniMax a mano (la vas a pegar en un Secret, no en el código)
- [ ] Git inicializado y al menos un commit (el repo tiene que ser "pusheable")

---

## ✅ Estado del doc

> **Actualizado 2026-07-01**: este doc se redactó asumiendo un Space de nombre `restauranteia-chef`, pero David terminó creando el Space con el nombre `RestaurantEAI`. Si volvés a deployar desde cero, ajustá el nombre al que corresponda. El doc sigue siendo válido conceptualmente; los nombres exactos pueden variar.

## 📦 Paso 1 — Inicializar git y hacer el primer commit (si no lo hiciste)

Si el repo todavía no es un repo git:

```bash
cd ~/repos/restauranteia
git init
git add .
git commit -m "MVP-0.5: agente Chef Creativo + UI Gradio"
```

(Si ya lo hiciste, saltá este paso.)

---

## 🌐 Paso 2 — Crear el Space en Hugging Face

1. Ir a https://huggingface.co/new-space
2. Completar el formulario:
   - **Owner:** `davidlopezgamero`
   - **Space name:** `RestaurantEAI` (o el nombre que quieras, sin espacios — **ojo, NO** `restauranteia-chef`, ese nombre ya quedó viejo)
   - **License:** MIT
   - **SDK:** Gradio
   - **Space hardware:** CPU basic (gratis) — suficiente para empezar
   - **Visibility:** **Private** (esto es la "C" — link privado, vos decidís después si lo hacés público)
3. Click **Create Space**

> Si elegiste **Private**, el Space no aparece en búsquedas globales pero cualquiera con el link puede verlo. Vos controlás quién tiene el link.

---

## 🔐 Paso 3 — Cargar la API key como Secret

**MUY IMPORTANTE:** la key NO va en el código ni en el commit. Va como "Secret" cifrado del Space.

1. Dentro del Space, ir a la pestaña **Settings** (arriba a la derecha o en el menú lateral).
2. Bajar hasta la sección **Repository secrets**.
3. Click **New secret** y agregar:
   - **Name:** `MINIMAX_API_KEY`
   - **Value:** tu API key real (la que NO está en el chat)
4. (Opcional, con defaults verificados podés omitir estos):
   - `MINIMAX_BASE_URL` = `https://api.minimax.io/v1`
   - `MINIMAX_MODEL` = `MiniMax-M3`
5. Confirmar.

> ⚠️ La API key queda almacenada cifrada en los servidores de HF. HF la pasa al Space en cada arranque vía variable de entorno. No aparece en logs ni en el código público.

---

## ⬆️ Paso 4 — Subir el código al Space

**Opción A — Clonar el Space como repo git y hacer push:**

```bash
# Clonar el Space vacío (HF te lo da como repo git)
cd ~/repos/restauranteia  # tu proyecto
git remote add hf https://huggingface.co/spaces/davidlopezgamero/restauranteia-chef
git fetch hf
git checkout -b main  # o master, lo que use tu repo local
# Si la rama del Space se llama distinto, ajustá:
# git branch --list
# git checkout -b <rama-del-space>

# Empujar el código
git push hf main
```

> **Problema probable:** el Space te lo da en la rama `main` por defecto, y tu repo local puede estar en `master`. Si hay conflicto, la forma más simple es:
> 1. Renombrar tu rama local a `main`: `git branch -M main`
> 2. Hacer `git push hf main --force` (con cuidado).
>
> O pedirle a HF que use la rama que vos quieras desde el panel del Space.
>
> **Caso real registrado (2026-07-01):** HF crea un commit inicial en `main` con `.gitattributes` y `README.md` mínimo. El push directo es rechazado (`non-fast-forward`). Solución segura aplicada:
>
> ```bash
> git pull --rebase hf main
> # Conflicto esperado en README.md; resolver con:
> git checkout --theirs README.md    # durante rebase, --theirs = nuestra versión
> git add README.md
> git rebase --continue
> git push hf main
> ```
> Conserva el `.gitattributes` de HF (estándar LFS) y descarta el `README.md` autogenerado a favor del nuestro.

**Opción B — Desde la UI web de HF:**

1. En el Space, ir a **Files** → **Add file** → **Upload files**.
2. Subir: `app.py`, `requirements.txt`, `README.md`, y **las carpetas** `agents/`, `memory/` (carpetas enteras son pesadas para upload manual).
3. La Opción A (git push) es mucho más limpia. Recomendada.

---

## 🟢 Paso 5 — Esperar el build y verificar

1. Después del push, HF automáticamente empieza a construir el Space. Vas a ver logs en la pestaña **Logs**.
2. Esperá a que diga algo como *"Application startup complete"* (tarda 1-5 minutos la primera vez, porque instala dependencias).
3. Cuando esté listo, entrá a la **App** del Space (botón arriba a derecha o URL `https://huggingface.co/spaces/davidlopezgamero/RestaurantEAI`).
4. Escribí una petición chiquita de prueba: *"Entrante vegetariano con calabaza y queso de cabra"*
5. Si responde con la ficha estructurada → **MVP-0.5 deployado ✅**

---

## 🩺 Troubleshooting — Errores típicos

| Error | Causa probable | Solución |
|---|---|---|
| **`Application startup failed`** | Falta dependencia en `requirements.txt` | Verificar que `app.py` solo importa cosas que estén en `requirements.txt`. HF da el traceback completo en **Logs**. |
| **`RuntimeError: Falta MINIMAX_API_KEY`** | El Secret no se cargó bien | Volver a **Settings → Repository secrets**, verificar que el nombre sea `MINIMAX_API_KEY` (todo mayúsculas, snake_case). |
| **`401 Unauthorized` en el log** | La API key es inválida o fue rotada | Regenerar la key en el panel de MiniMax, actualizar el Secret en HF, **reiniciar el Space** (botón "Restart" en Settings). |
| **El Space se queda cargando eternamente** | `app.py` se traba al importar | Revisar Logs. Lo más probable es error de import o de path. |
| **`ModuleNotFoundError: agents`** | HF clonó el repo pero la estructura de carpetas no subió | Verificar en la pestaña **Files** del Space que la carpeta `agents/` está. Si no, hay que hacer push con todas las carpetas. |

---

## 🔁 Reiniciar el Space (cuando hagas cambios)

Cada vez que cambies código en `app.py`, `requirements.txt` o `agents/`, HF detecta el push y redespliega solo. **Pero hay un caso donde necesitás reinicio manual:** si cambiaste un Secret (ej. regeneraste la API key). En ese caso: **Settings → Restart this Space**.

---

## 🌐 Compartir el link

Cuando esté funcionando:

- **Link privado** (cualquiera con el link puede usarlo, pero no aparece en búsquedas): es el default si creaste el Space como Private.
- **Link público** (cualquiera en internet lo encuentra): cambiás la visibility del Space a Public. **Hacer esto solo cuando estés conforme con el estado del agente.**

---

## 📝 Para próximas iteraciones

Si querés cambiar el system prompt del chef, el branding, los ejemplos, etc.:

1. Editar localmente el archivo (ej. `agents/creativo/prompts/system_chef.md`).
2. Commit + push a HF.
3. Esperar el redespliegue (1-2 min).
4. Refrescar el browser en el Space.

No hace falta tocar el Secret a menos que cambies la API key.

---

**Última línea de defensa:** si después de seguir todos los pasos algo no anda, **pegame el log de HF** (Settings → Logs, copiar las últimas 30-50 líneas). Lo diagnostico con vos sin problema.
