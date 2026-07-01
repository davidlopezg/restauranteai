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


# --- Carga de recursos -------------------------------------------------------

def load_system_prompt() -> str:
    """Carga el system prompt del chef desde el .md"""
    if not PROMPT_PATH.exists():
        raise FileNotFoundError(
            f"No se encontró el system prompt en {PROMPT_PATH}. "
            f"Asegúrate de que el archivo existe."
        )
    return PROMPT_PATH.read_text(encoding="utf-8")


def load_estacionalidad() -> dict:
    """Carga el calendario de estacionalidad de Cataluña."""
    if not ESTACIONALIDAD_PATH.exists():
        return {}
    return json.loads(ESTACIONALIDAD_PATH.read_text(encoding="utf-8"))


# --- Llamada a la API --------------------------------------------------------

def call_minimax(system_prompt: str, user_prompt: str) -> str:
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

    last_error: Optional[Exception] = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                
                # Parseo compatible con formato OpenAI:
                return data["choices"][0]["message"]["content"]
        except (httpx.HTTPError, KeyError, ValueError) as e:
            last_error = e
            if attempt < MAX_RETRIES:
                print(f"  [retry {attempt}/{MAX_RETRIES}] Error: {e}", file=sys.stderr)
            continue
    
    raise RuntimeError(f"Falló la llamada a MiniMax tras {MAX_RETRIES} intentos: {last_error}")


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

def generar_ficha(peticion: str) -> str:
    """Genera la ficha estructurada del chef."""
    system_prompt = load_system_prompt()
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
        "⚠️ RECORDATORIO FINAL — INSTRUCCIÓN DE IDIOMA OBLIGATORIA ⚠️\n\n"
        "Responde a esta petici\u00f3n escrita en espa\u00f1ol **\u00fanica y exclusivamente en espa\u00f1ol** (castellano). "
        "**PROHIBIDO** responder en ingl\u00e9s, franc\u00e9s u otro idioma en ninguna parte "
        "del cuerpo de la ficha. La \u00fanica secci\u00f3n que admite ingl\u00e9s es el campo "
        "\"\ud83c\udfa8 PROMPT PARA IMAGEN DEL PLATO\" al final (por convenci\u00f3n universal para "
        "generadores de im\u00e1genes como DALL-E / Midjourney / Stable Diffusion).\n\n"
        "Si tu respuesta contiene t\u00e9rminos en ingl\u00e9s fuera de ese campo, ES UN ERROR. "
        "Re-escribe la ficha completa en espa\u00f1ol antes de devolverla.\n\n"
        "PROHIBIDO tambi\u00e9n: caracteres cir\u00edlicos (rusos), hanzi (chinos), hangul (coreanos), "
        "kanji (japoneses). Solo alfabeto latino."
    )

    user_message = user_message + instruccion_idioma
    
    print(f"🍳 Generando ficha para: \"{peticion}\"...\n", file=sys.stderr)
    respuesta = call_minimax(system_prompt, user_message)
    return respuesta


def modo_interactivo():
    """Modo interactivo por línea de comandos."""
    print("=" * 60)
    print("🍂 Chef Creativo — Modo Interactivo")
    print("=" * 60)
    print("Escribí tu petición culinaria y presioná Enter.")
    print("Escribí 'salir' para terminar.\n")
    
    while True:
        try:
            peticion = input("➤ ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n¡Hasta luego!")
            break
        
        if not peticion:
            continue
        if peticion.lower() in ("salir", "exit", "quit"):
            break
        
        try:
            ficha = generar_ficha(peticion)
            print("\n" + ficha + "\n")
            print("-" * 60 + "\n")
        except Exception as e:
            print(f"\n❌ Error: {e}\n", file=sys.stderr)


def main():
    if len(sys.argv) > 1:
        # Modo CLI: un solo argumento = una sola ficha
        peticion = " ".join(sys.argv[1:])
        ficha = generar_ficha(peticion)
        print(ficha)
    else:
        # Sin argumentos = modo interactivo
        modo_interactivo()


if __name__ == "__main__":
    main()