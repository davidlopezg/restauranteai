"""
Chef Creativo — Agente MVP-0
============================

Recibe una petición culinaria en lenguaje natural y devuelve una ficha estructurada
(nombre, historia, ficha técnica, maridaje, prompt de imagen).

Uso:
    python -m agents.creativo.agent "Quiero un entrante vegetariano con calabaza y queso de cabra"
    python -m agents.creativo.agent  # modo interactivo

Variables de entorno necesarias (.env):
    MINIMAX_API_KEY      — tu clave de la API
    MINIMAX_BASE_URL     — endpoint base (ej: https://api.minimax.chat/v1)
    MINIMAX_MODEL        — nombre del modelo (ej: MiniMax-M3)
"""

from __future__ import annotations

import os
import sys
import json
import re
from pathlib import Path
from typing import Optional

import httpx
from dotenv import load_dotenv

# --- Paths del proyecto ------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROMPT_PATH = PROJECT_ROOT / "agents" / "creativo" / "prompts" / "system_chef.md"
ESTACIONALIDAD_PATH = PROJECT_ROOT / "agents" / "creativo" / "knowledge" / "estacionalidad.json"

load_dotenv(PROJECT_ROOT / ".env")


# --- Configuración ------------------------------------------------------------

API_KEY = os.getenv("MINIMAX_API_KEY")

# Base URL por defecto verificada contra documentación oficial de MiniMax.
# Fuente: https://platform.minimax.io/docs/guides/quickstart-preparation
# (Modo OpenAI-compatible, sección "Compatible OpenAI API")
DEFAULT_BASE_URL = "https://api.minimax.io/v1"
BASE_URL = os.getenv("MINIMAX_BASE_URL", DEFAULT_BASE_URL).rstrip("/")

# Modelo por defecto verificado contra doc oficial.
# Fuente: https://platform.minimax.io/docs/guides/models-intro
# MiniMax-M3: 1M context window, modelo frontier multimodal.
DEFAULT_MODEL = "MiniMax-M3"
MODEL = os.getenv("MINIMAX_MODEL", DEFAULT_MODEL)

# Timeout y reintentos
REQUEST_TIMEOUT = 60.0
MAX_RETRIES = 2
LANGUAGE_RETRIES = 2  # reintentos adicionales si el chef responde en inglés

# Palabras de alta confianza que NO deberían aparecer en una ficha en castellano.
# Son function words + vocabulario común inglés sin cognados en español.
_PALABRAS_GATILLO_INGLES: set[str] = {
    "the", "and", "with", "for", "you", "this", "that", "are",
    "your", "from", "have", "would", "will", "each", "into",
    "just", "also", "well", "after", "our", "when", "which",
    "their", "what", "been", "has", "its", "over", "than",
    "then", "these", "some", "them", "very", "much", "such",
}


# --- Carga de recursos -------------------------------------------------------

def load_system_prompt() -> str:
    """Carga el system prompt del chef desde el .md"""
    if not PROMPT_PATH.exists():
        raise FileNotFoundError(
            f"No se encontró el system prompt en {PROMPT_PATH}. "
            f"Asegúrate de que el archivo existe."
        )
    return PROMPT_PATH.read_text(encoding="utf-8")


def load_skill_prompt(skill_key: str) -> str:
    """
    Carga el system prompt de una skill específica (ej: 'ficha', 'proceso_creativo').
    Por retrocompatibilidad, 'ficha' usa el system_chef.md clásico.

    Import local para evitar circular import: agent.py -> skills.py -> agent.py
    """
    if skill_key == "ficha":
        # Retrocompat: la skill original sigue viviendo en system_chef.md
        return load_system_prompt()
    from agents.creativo.skills import load_skill_prompt as _loader
    return _loader(skill_key)


def load_estacionalidad() -> dict:
    """Carga el calendario de estacionalidad de Cataluña."""
    if not ESTACIONALIDAD_PATH.exists():
        return {}
    return json.loads(ESTACIONALIDAD_PATH.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Catálogo de platos — inyectado al system prompt del chef
# ---------------------------------------------------------------------------

CATALOGO_MAX_PLATOS_INYECTADOS: int = 30  # cap para no inflar el system prompt


def load_catalogo() -> list[dict]:
    """Carga el catálogo de platos del restaurante (de la fase init).

    Devuelve lista vacía si no existe.
    """
    from agents.knowledge_context import cargar_catalogo
    try:
        return cargar_catalogo()
    except FileNotFoundError:
        return []


def formatear_catalogo_para_chef(catalogo: list[dict] | None = None) -> str:
    """
    Formatea el catálogo para inyectarlo como contexto al chef.

    Args:
        catalogo: lista de platos. Si None, se carga del disco.

    Returns:
        String con el catálogo formateado, o string vacío si no hay.
    """
    if catalogo is None:
        catalogo = load_catalogo()

    if not catalogo:
        return ""

    lineas = [
        "\n\n---\n",
        "## CATÁLOGO ACTUAL DEL RESTAURANTE",
        "",
        "Estos son los platos que ya están en la carta del restaurante.",
        "Usá esta información para:",
        "- NO proponer platos idénticos o muy similares a los existentes.",
        "- Sugerir COMPLEMENTOS: si ya hay una pasta, proponer un segundo plato de otra familia.",
        "- Mantener la LÍNEA CULINARIA: si la carta es mediterránea, no proponer sushi.",
        "- Si el usuario pide un plato similar a uno existente, ofrecé EXTENDER la línea "
        "(versión contemporánea, variante de temporada, etc.) en vez de duplicar.",
        "",
        f"Total de platos en carta: {len(catalogo)}.",
        "",
    ]

    # Limitar para no inflar el prompt
    platos_mostrar = catalogo[:CATALOGO_MAX_PLATOS_INYECTADOS]
    if len(catalogo) > CATALOGO_MAX_PLATOS_INYECTADOS:
        lineas.append(
            f"(mostrando los primeros {CATALOGO_MAX_PLATOS_INYECTADOS} de {len(catalogo)})\n"
        )

    # Agrupar por categoría para que sea más legible
    por_categoria: dict[str, list[dict]] = {}
    for p in platos_mostrar:
        cat = str(p.get("categoria", "otro")).strip().lower()
        por_categoria.setdefault(cat, []).append(p)

    for cat in sorted(por_categoria.keys()):
        lineas.append(f"### {cat.capitalize()}")
        for p in por_categoria[cat]:
            nombre = str(p.get("nombre", "")).strip()
            if not nombre:
                continue
            desc = str(p.get("descripcion", "")).strip()
            precio = p.get("precio")
            partes = [f"- **{nombre}**"]
            if desc:
                partes.append(f" — {desc}")
            if precio is not None:
                try:
                    partes.append(f" ({float(precio):.2f}€)")
                except (ValueError, TypeError):
                    pass
            lineas.append("".join(partes))
        lineas.append("")

    return "\n".join(lineas)


# --- Detección de idioma ----------------------------------------------------

def _es_principalmente_espanol(texto: str) -> bool:
    """
    Detecta si el texto está mayoritariamente en español.
    Excluye la sección 'PROMPT PARA IMAGEN' porque puede ir en inglés por convención.
    
    Heurística: cuenta palabras gatillo inglesas en el cuerpo.
    Si más del 8% de las palabras son gatillos ingleses → no es español.
    """
    # Recortar la sección de prompt para imagen (puede estar en inglés)
    prompt_markers = [
        "🎨 PROMPT PARA IMAGEN DEL PLATO",
        "PROMPT PARA IMAGEN DEL PLATO",
        "🎨 PROMPT PARA IMAGEN",
        "PROMPT PARA IMAGEN",
    ]
    cuerpo = texto
    for marker in prompt_markers:
        idx = cuerpo.find(marker)
        if idx != -1:
            cuerpo = cuerpo[:idx]
            break

    # Tokenizar: solo palabras de 2+ letras en alfabeto latino
    palabras = re.findall(r'\b[a-záéíóúñü]{2,}\b', cuerpo.lower())
    if len(palabras) < 10:
        return True  # muestra muy pequeña, asumimos OK

    inglesas = sum(1 for p in palabras if p in _PALABRAS_GATILLO_INGLES)
    ratio = inglesas / len(palabras)

    return ratio < 0.08


# --- Llamada a la API --------------------------------------------------------

def call_minimax(system_prompt: str, user_prompt: str, force_spanish: bool = True) -> str:
    """
    Llama a la API de MiniMax en modo OpenAI-compatible.
    
    Datos verificados contra documentación oficial de MiniMax:
      - Base URL:  https://api.minimax.io/v1
      - Endpoint:  POST /chat/completions
      - Auth:      Authorization: Bearer <MINIMAX_API_KEY>
      - Modelo:    MiniMax-M3 (1M context window)
    
    Fuentes:
      - https://platform.minimax.io/docs/guides/quickstart-preparation
      - https://platform.minimax.io/docs/api-reference/text-chat-openai
      - https://platform.minimax.io/docs/guides/models-intro
    
    Nota: MiniMax también expone un modo Anthropic-compatible (que la doc
    oficial recomienda como primera opción). Se mantiene el modo OpenAI
    porque el parser de response coincide exactamente con el código.
    Migrar a Anthropic es un upgrade futuro si aparece la necesidad
    de tool use / multi-agente nativo.
    """
    if not API_KEY:
        raise RuntimeError(
            "Falta MINIMAX_API_KEY en el entorno. "
            "Copia .env.example a .env y rellena tu clave."
        )
    if not BASE_URL:
        raise RuntimeError(
            "MINIMAX_BASE_URL está vacío. "
            "El default verificado es https://api.minimax.io/v1 "
            "(modo OpenAI-compatible). "
            "Ver: https://platform.minimax.io/docs/guides/quickstart-preparation"
        )

    url = f"{BASE_URL}/chat/completions"
    
    headers = {
        # Formato verificado contra docs oficiales de MiniMax
        # (modo OpenAI-compatible)
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        # Parámetros estándar OpenAI-completions soportados por MiniMax.
        # temperature 0.8 = creatividad media-alta, adecuada para brainstorming culinario.
        # max_tokens 1500 = holgura para ficha técnica + maridaje + prompt de imagen.
        "temperature": 0.8,
        "max_tokens": 1500,
    }

    current_user_prompt = user_prompt
    current_temp = 0.8
    total_attempts = MAX_RETRIES + LANGUAGE_RETRIES
    last_error: Optional[Exception] = None
    language_failures = 0

    for attempt in range(1, total_attempts + 1):
        payload["messages"][1]["content"] = current_user_prompt
        payload["temperature"] = current_temp

        try:
            with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]

                # Validación de idioma (solo si force_spanish=True)
                if force_spanish and not _es_principalmente_espanol(content):
                    language_failures += 1
                    if language_failures <= LANGUAGE_RETRIES:
                        print(
                            f"  [idioma] respuesta en inglés detectada "
                            f"(intento {language_failures}/{LANGUAGE_RETRIES}), "
                            f"reintentando con instrucción reforzada...",
                            file=sys.stderr,
                        )
                        # Reforzar instrucción de idioma y bajar temperatura
                        current_user_prompt = current_user_prompt + (
                            "\n\n---\n\n"
                            "⚠️⚠️⚠️ AVISO URGENTE PARA EL MODELO ⚠️⚠️⚠️\n"
                            "Tu respuesta anterior estaba en inglés. "
                            "ESTO ES UN ERROR GRAVE.\n"
                            "Debes responder ÍNTEGRAMENTE en CASTELLANO (español). "
                            "La única sección que admite inglés es "
                            "el PROMPT PARA IMAGEN DEL PLATO al final.\n"
                            "Reescribe TODO el cuerpo de la ficha en español. "
                            "No mezcles idiomas. Solo castellano."
                        )
                        current_temp = 0.2
                        continue
                    else:
                        # Agotados los reintentos de idioma: devolvemos igual
                        # pero loggeamos el warning
                        print(
                            f"  [idioma] ⚠️ agotados {LANGUAGE_RETRIES} reintentos, "
                            f"devolviendo respuesta mixta (español+inglés)",
                            file=sys.stderr,
                        )

                return content

        except (httpx.HTTPError, KeyError, ValueError) as e:
            last_error = e
            if attempt < total_attempts:
                print(f"  [retry {attempt}/{total_attempts}] Error: {e}", file=sys.stderr)
            continue

    raise RuntimeError(
        f"Falló la llamada a MiniMax tras {total_attempts} intentos: {last_error}"
    )


# --- Validación de estacionalidad --------------------------------------------

def check_estacionalidad(peticion: str, estacionalidad: dict) -> Optional[str]:
    """
    Busca ingredientes en la petición y avisa si alguno está fuera de temporada.
    Devuelve un string con la advertencia o None si todo OK.
    """
    if not estacionalidad:
        return None
    
    mes_actual = __import__("datetime").datetime.now().month
    meses_nombre = ["", "enero", "febrero", "marzo", "abril", "mayo", "junio",
                    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    mes_actual_nombre = meses_nombre[mes_actual]
    
    pet_lower = peticion.lower()
    avisos = []
    
    # Iteramos solo el sub-diccionario de productos, no las claves raíz (region, fuente, etc.)
    productos_dict = estacionalidad.get("productos", {})
    for producto, meses in productos_dict.items():
        if producto in pet_lower and mes_actual not in meses:
            avisos.append(
                f"· {producto.capitalize()}: mejor en {', '.join(meses_nombre[m] for m in meses)}"
            )
    
    if avisos:
        return (
            f"\n⚠️  Aviso de estacionalidad ({mes_actual_nombre}):\n"
            + "\n".join(avisos)
            + "\n\nEl chef recibirá esta información como contexto. "
              "Si querés ignorar el aviso, simplemente no menciones el producto."
        )
    return None


# --- Loop principal ----------------------------------------------------------

# Comandos soportados en modo proceso_creativo.
# Estos se detectan al inicio del mensaje del usuario.
PROCESO_COMANDOS: set[str] = {
    "/estado", "/volver", "/ficha", "/reiniciar", "/salir",
}


def iniciar_proceso_creativo(peticion: str, sesion_id: str | None = None):
    """
    Inicia (o reanuda) una sesión del proceso creativo.

    Args:
        peticion: petición culinaria del usuario.
        sesion_id: si se pasa, reanuda una sesión existente.

    Returns:
        Instancia de ProcesoCreativo.
    """
    # Import local para evitar circular import
    from agents.creativo.proceso_creativo import ProcesoCreativo
    if sesion_id:
        return ProcesoCreativo(peticion="", cargar_de=sesion_id)
    return ProcesoCreativo(peticion=peticion)


def procesar_mensaje_proceso(sesion, mensaje: str) -> str:
    """
    Procesa un mensaje del usuario dentro de una sesión de proceso creativo.

    Soporta:
    - Comandos: /estado, /fase N|nombre, /volver, /ficha, /reiniciar, /salir
    - Mensaje normal: se interpreta como input para la fase actual.
      El chef trabaja la fase, y se marca como completa automáticamente.

    Args:
        sesion: instancia de ProcesoCreativo.
        mensaje: texto del usuario.

    Returns:
        String con la respuesta para mostrar al usuario.
    """
    from agents.creativo.proceso_creativo import FASES_POR_KEY, FASES

    mensaje = (mensaje or "").strip()
    if not mensaje:
        return ""

    # Comandos
    lower = mensaje.lower()

    if lower == "/estado":
        return sesion.resumen_estado()

    if lower.startswith("/fase "):
        arg = mensaje[6:].strip()
        # Acepta número (1-7) o nombre de fase
        target_key = None
        if arg.isdigit():
            idx = int(arg) - 1
            if 0 <= idx < len(FASES):
                target_key = FASES[idx]["key"]
        elif arg in FASES_POR_KEY:
            target_key = arg
        if not target_key:
            disponibles = ", ".join(f["key"] for f in FASES)
            return f"❌ Fase '{arg}' no reconocida. Disponibles: {disponibles}"
        sesion.ir_a_fase(target_key)
        return (
            f"↪️ Salté a la fase {target_key.upper()} — {FASES_POR_KEY[target_key]['nombre']}\n\n"
            f"{sesion.resumen_estado()}"
        )

    if lower == "/volver":
        if sesion.fase_actual_key is None:
            return "⚠️  No hay fase activa (el proceso está completo). Usá /fase 1 para volver al inicio."
        sesion.regenerar_fase_actual()
        return (
            f"↪️ Regenerando la fase {sesion.fase_actual_key.upper()}.\n\n"
            f"{sesion.resumen_estado()}"
        )

    if lower == "/ficha" or lower.startswith("/ficha "):
        forzar = "forzar" in lower
        try:
            ficha = sesion.generar_ficha_final(forzar=forzar)
            return (
                f"🍂 Ficha final generada.\n\n"
                f"---\n\n"
                f"{ficha}"
            )
        except ValueError as e:
            return f"❌ {e}"

    if lower == "/reiniciar":
        sesion.reiniciar()
        return f"↪️ Proceso reiniciado.\n\n{sesion.resumen_estado()}"

    if lower == "/salir":
        sesion.save()
        return (
            f"👋 Sesión guardada. Para reanudar: {sesion.sesion_id}\n\n"
            f"{sesion.resumen_estado()}"
        )

    # Mensaje normal: trabajar la fase actual con LLM y marcarla completa
    if sesion.fase_actual_key is None:
        return (
            "✅ Todas las fases están completas. Usá /ficha para generar la ficha final, "
            "o /fase 1 para volver al inicio."
        )

    # Capturar la fase ACTUAL antes de trabajar (porque después puede ser None)
    fase_trabajada = sesion.fase_actual

    # Aviso de estacionalidad como contexto (igual que en ficha normal)
    estacionalidad = load_estacionalidad()
    aviso = check_estacionalidad(mensaje, estacionalidad)
    contexto_adicional = ""
    if aviso:
        contexto_adicional = (
            f"\n\n[CONTEXTO PARA TI — NO INCLUIR EN LA SALIDA]: {aviso}"
        )

    # Generar contenido de la fase con LLM
    contenido = sesion.trabajar_fase_actual()

    # Marcar completa y avanzar
    sesion.marcar_fase_completa(contenido)

    # Preparar respuesta al usuario
    if sesion.fase_actual_key is None:
        # Llegamos al final: todas completas
        return (
            f"✓ Fase {fase_trabajada['orden']} ({fase_trabajada['nombre']}) completada:\n\n"
            f"{contenido}\n\n"
            f"---\n\n"
            f"🎉 ¡Todas las fases completas! Usá `/ficha` para generar la ficha final."
        )

    prox_fase = sesion.fase_actual  # después de avanzar
    return (
        f"✓ Fase {fase_trabajada['orden']} ({fase_trabajada['nombre']}) completada:\n\n"
        f"{contenido}\n\n"
        f"---\n\n"
        f"▶ Siguiente: Fase {prox_fase['orden']} — {prox_fase['nombre']}\n\n"
        f"Seguí trabajando, o usá:\n"
        f"- `/estado` — ver progreso\n"
        f"- `/volver` — regenerar esta fase\n"
        f"- `/fase N` — saltar a otra fase\n"
        f"- `/ficha` — generar ficha final (cuando estén todas completas)"
    )


def generar_ficha(peticion: str, skill_key: str = "ficha") -> str:
    """
    Genera la respuesta del chef usando la skill indicada.

    Args:
        peticion: texto libre del usuario con la petición culinaria.
        skill_key: 'ficha' (default, ficha técnica estructurada) o 'proceso_creativo'
                   (proceso paso a paso + ficha al final).

    Returns:
        String con la respuesta del chef.
    """
    system_prompt = load_skill_prompt(skill_key)
    estacionalidad = load_estacionalidad()

    # Aviso de estacionalidad (se inyecta al prompt como contexto, no como instrucción dura)
    aviso = check_estacionalidad(peticion, estacionalidad)
    contexto_adicional = ""
    if aviso:
        contexto_adicional = (
            f"\n\n[CONTEXTO PARA TI — NO INCLUIR EN LA SALIDA]: {aviso}"
        )

    user_message = peticion + contexto_adicional

    # 🚨 INSTRUCCIÓN DE IDIOMA AL FINAL DEL MENSAJE — máxima autoridad posicional.
    # Si la regla del system prompt no basta, esta actúa como recordatorio ineludible.
    # El chef NO DEBE derivar al inglés. Solo el "Prompt para imagen" va en inglés.
    instruccion_idioma = (
        "\n\n---\n\n"
        "\u26a0\ufe0f RECORDATORIO FINAL \u2014 INSTRUCCIÓN DE IDIOMA OBLIGATORIA \u26a0\ufe0f\n\n"
        "Responde a esta petici\u00f3n escrita en espa\u00f1ol **\u00fanica y exclusivamente en espa\u00f1ol** (castellano). "
        "**PROHIBIDO** responder en ingl\u00e9s, franc\u00e9s u otro idioma en ninguna parte "
        "del cuerpo de la ficha. La \u00fanica secci\u00f3n que admite ingl\u00e9s es el campo "
        "\"PROMPT PARA IMAGEN DEL PLATO\" al final (por convenci\u00f3n universal para "
        "generadores de im\u00e1genes como DALL-E / Midjourney / Stable Diffusion).\n\n"
        "Si tu respuesta contiene t\u00e9rminos en ingl\u00e9s fuera de ese campo, ES UN ERROR. "
        "Re-escribe la ficha completa en espa\u00f1ol antes de devolverla.\n\n"
        "PROHIBIDO tambi\u00e9n: caracteres cir\u00edlicos (rusos), hanzi (chinos), hangul (coreanos), "
        "kanji (japoneses). Solo alfabeto latino."
    )

    user_message = user_message + instruccion_idioma
    
    print(f"🍳 Generando (skill={skill_key}) para: \"{peticion}\"...\n", file=sys.stderr)
    respuesta = call_minimax(system_prompt, user_message)
    return respuesta


def _loop_ficha(skills: list[dict]) -> str | None:
    """
    Loop de la skill 'ficha': cada input genera una ficha y se queda ahí.
    Devuelve la skill_key si el usuario cambia de skill, None si sale.
    """
    print("Escribí tu petición culinaria y presioná Enter.")
    print("Comandos especiales:")
    print("  /skill        — cambiar skill")
    print("  /skills       — listar skills disponibles")
    print("  salir         — terminar\n")

    skill_key = "ficha"
    while True:
        try:
            peticion = input("➤ ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n¡Hasta luego!")
            return None

        if not peticion:
            continue
        if peticion.lower() in ("salir", "exit", "quit"):
            return None

        # Comandos de cambio de skill
        nueva = _manejar_comandos_skill(peticion, skill_key, skills)
        if nueva is not None and nueva != skill_key:
            return nueva  # cambia de skill
        if nueva == skill_key:
            continue  # comando procesado, misma skill, seguir

        try:
            ficha = generar_ficha(peticion, skill_key=skill_key)
            print("\n" + ficha + "\n")
            print("-" * 60 + "\n")
        except Exception as e:
            print(f"\n❌ Error: {e}\n", file=sys.stderr)


def _loop_proceso_creativo(skills: list[dict], sesion_inicial=None) -> str | None:
    """
    Loop de la skill 'proceso_creativo': state machine con 7 fases.
    Devuelve la skill_key si el usuario cambia de skill, None si sale.

    Args:
        skills: lista de skills disponibles (para comandos /skill).
        sesion_inicial: si se pasa, se usa esa sesión en vez de crear una nueva.
    """
    from agents.creativo.proceso_creativo import listar_sesiones_activas
    # _iniciar y procesar_mensaje_proceso viven en este mismo módulo (agent.py)
    _iniciar = iniciar_proceso_creativo
    _procesar = procesar_mensaje_proceso

    sesion = sesion_inicial

    print("🍂  PROCESO CREATIVO — state machine de 7 fases")
    print()
    print("Cada mensaje que escribas hace que el chef trabaje la fase actual.")
    print("Las fases se guardan automáticamente. Podés cerrar y volver.")
    print()
    print("Comandos especiales:")
    print("  /estado       — ver progreso de las 7 fases")
    print("  /fase N       — saltar a fase N (1-7) o por nombre")
    print("  /volver       — regenerar la fase actual")
    print("  /ficha        — generar ficha final (auto cuando estén todas)")
    print("  /ficha forzar — generar aunque falten fases")
    print("  /reiniciar    — volver al inicio con la misma petición")
    print("  /sesiones     — listar sesiones guardadas")
    print("  /reanudar ID  — retomar una sesión anterior")
    print("  /skill        — cambiar a otra skill")
    print("  /skills       — listar skills disponibles")
    print("  salir         — terminar")
    print()

    # Si nos pasaron una sesión inicial, mostramos su estado
    if sesion is not None:
        print(f"▶ Sesión activa: {sesion.sesion_id}")
        print()
        print(sesion.resumen_estado())
        print()

    while True:
        try:
            mensaje = input("➤ ").strip()
        except (EOFError, KeyboardInterrupt):
            if sesion is not None:
                sesion.save()
            print("\n¡Hasta luego!")
            return None

        if not mensaje:
            continue
        if mensaje.lower() in ("salir", "exit", "quit"):
            if sesion is not None:
                sesion.save()
                print(f"\n👋 Sesión guardada: {sesion.sesion_id}")
            return None

        # Comandos de cambio de skill (mata la sesión actual)
        nueva = _manejar_comandos_skill(mensaje, "proceso_creativo", skills)
        if nueva is not None and nueva != "proceso_creativo":
            if sesion is not None:
                sesion.save()
                print(f"\n(Sesión guardada: {sesion.sesion_id})")
            return nueva
        if nueva == "proceso_creativo":
            continue

        # Comandos especiales del proceso creativo
        lower = mensaje.lower()

        if lower == "/sesiones":
            sesiones = listar_sesiones_activas()
            if not sesiones:
                print("\n  (no hay sesiones guardadas)\n")
            else:
                print("\n  Sesiones guardadas:")
                for s in sesiones[:10]:
                    estado = "✓" if s.get("completa") else "▶"
                    print(f"    {estado} {s['sesion_id']}  —  {s['peticion'][:50]}")
                print()
            continue

        if lower.startswith("/reanudar "):
            sesion_id = mensaje[len("/reanudar "):].strip()
            try:
                sesion = _iniciar("", sesion_id=sesion_id)
                print(f"\n↪️  Sesión reanudada: {sesion.sesion_id}\n")
                print(sesion.resumen_estado())
                print()
            except FileNotFoundError as e:
                print(f"\n❌ {e}\n")
            continue

        # Primer mensaje o mensaje normal: crear o usar sesión
        if sesion is None:
            sesion = _iniciar(mensaje)
            print(f"\n🆕 Sesión: {sesion.sesion_id}")
            print()
            print(sesion.resumen_estado())
            print()
            print("Cuando me digas 'siguiente' (o cualquier cosa), trabajo la fase 1.")
            print()
            continue

        try:
            respuesta = _procesar(sesion, mensaje)
            print()
            print(respuesta)
            print()
            print("-" * 60)
            print()
        except Exception as e:
            print(f"\n❌ Error: {e}\n", file=sys.stderr)


def _manejar_comandos_skill(mensaje: str, skill_actual: str, skills: list[dict]) -> str | None:
    """
    Maneja comandos de cambio de skill (/skill, /skills) de forma transversal.
    Devuelve:
        - None: no era un comando de skill
        - skill_actual: era un comando de skill pero la skill no cambió
        - otra_key: era un comando de skill y el usuario eligió cambiar
    """
    lower = mensaje.lower()

    if lower == "/skills":
        print("\nSkills disponibles:")
        for s in skills:
            marker = " (actual)" if s["key"] == skill_actual else ""
            print(f"  · {s['nombre']}{marker}  —  {s['descripcion']}")
        print()
        return skill_actual  # procesado, misma skill

    if lower == "/skill":
        print("\nCambiar skill:")
        for i, s in enumerate(skills, 1):
            marker = " (actual)" if s["key"] == skill_actual else ""
            print(f"  {i}. {s['nombre']}{marker}")
        while True:
            r = input(f"   Elige 1-{len(skills)} > ").strip()
            if r.isdigit() and 1 <= int(r) <= len(skills):
                nueva_key = skills[int(r) - 1]["key"]
                if nueva_key != skill_actual:
                    nueva_nombre = next(s["nombre"] for s in skills if s["key"] == nueva_key)
                    print(f"\n✓ Cambiando a: {nueva_nombre}\n")
                return nueva_key
            print(f"   (elegí un número entre 1 y {len(skills)})")

    return None  # no era un comando de skill


def modo_interactivo():
    """Modo interactivo por línea de comandos. Selector de skill + dispatch."""
    # Bootstrap del contexto compartido del restaurante.
    # Si faltan los archivos, hace las preguntas automáticamente.
    from agents.knowledge_context import ensure_initialized, cargar_restaurante, cargar_catalogo
    if ensure_initialized():
        print("(A partir de ahora, el agente conoce tu restaurante y catálogo.)\n")

    # Cargar lista de skills disponibles dinámicamente
    from agents.creativo.skills import list_skills

    print("=" * 60)
    print("🍂 Chef Creativo — Modo Interactivo")
    print("=" * 60)
    rest = cargar_restaurante()
    if rest.get("nombre"):
        print(f"Restaurante: {rest.get('nombre')}")

    # Selector de skill al inicio
    skills = list_skills()
    print("\nElegí la skill con la que querés trabajar:")
    for i, s in enumerate(skills, 1):
        print(f"  {i}. {s['nombre']}  —  {s['descripcion']}")

    skill_key = "ficha"
    while True:
        r = input(f"   Elige 1-{len(skills)} [{skill_key}] > ").strip()
        if not r:
            break
        if r.isdigit() and 1 <= int(r) <= len(skills):
            skill_key = skills[int(r) - 1]["key"]
            break
        print(f"   (elegí un número entre 1 y {len(skills)})")

    skill_actual = next(s for s in skills if s["key"] == skill_key)
    print(f"\n✓ Skill activa: {skill_actual['nombre']}\n")

    # Dispatch al loop apropiado
    while True:
        if skill_key == "proceso_creativo":
            skill_key = _loop_proceso_creativo(skills)
            if skill_key is None:
                break
        else:
            skill_key = _loop_ficha(skills)
            if skill_key is None:
                break
        # Si el usuario cambió skill, vuelve al inicio del while
        nueva = next(s for s in skills if s["key"] == skill_key)
        print(f"\n✓ Skill activa: {nueva['nombre']}\n")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "pc":
        # Modo CLI directo para proceso creativo:
        #   python -m agents.creativo.agent pc [--reanudar SESION_ID] [peticion]
        args = sys.argv[2:]

        reanudar_id = None
        peticion = None
        i = 0
        while i < len(args):
            if args[i] == "--reanudar" and i + 1 < len(args):
                reanudar_id = args[i + 1]
                i += 2
            else:
                peticion = " ".join(args[i:])
                break

        from agents.creativo.skills import list_skills

        if reanudar_id:
            sesion = iniciar_proceso_creativo("", sesion_id=reanudar_id)
        elif peticion:
            sesion = iniciar_proceso_creativo(peticion)
        else:
            sesion = None

        if sesion is not None:
            print(sesion.resumen_estado())
            print()

        # Loop interactivo enfocado solo en proceso creativo
        skills = list_skills()
        _loop_proceso_creativo(skills, sesion_inicial=sesion)
    elif len(sys.argv) > 1:
        # Modo CLI: un solo argumento = una sola ficha
        peticion = " ".join(sys.argv[1:])
        ficha = generar_ficha(peticion)
        print(ficha)
    else:
        # Sin argumentos = modo interactivo
        modo_interactivo()


if __name__ == "__main__":
    main()