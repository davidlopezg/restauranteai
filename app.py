"""
Chef Creativo — App Gradio (MVP-0.5 / HF Space)
================================================

Wrapper web sobre la lógica del agente (agents/creativo/agent.py).
La lógica de generación queda intacta; solo se agrega capa de presentación.

Pensado para correr en:
  - Local:    python app.py
  - HF Space: se levanta solo si las Secrets están bien configuradas.

Variables de entorno (en HF Space: configurar como Secrets):
    MINIMAX_API_KEY      — clave de la API (obligatoria)
    MINIMAX_BASE_URL     — opcional, default https://api.minimax.io/v1
    MINIMAX_MODEL        — opcional, default MiniMax-M3

Decisiones de seguridad:
  - Los logs NO muestran el valor de la key. Solo el nombre del tipo de error.
  - El aviso de estacionalidad se inyecta como contexto al chef, no se muestra al usuario.
  - No hay base de datos: cada conversación es stateless (no se guarda entre requests).
"""

from __future__ import annotations

import sys
import logging
from pathlib import Path
from datetime import datetime

# Path del proyecto — permite que app.py corra tanto desde la raíz como desde HF Space
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

import gradio as gr

from agents.creativo.agent import (
    load_system_prompt,
    load_estacionalidad,
    check_estacionalidad,
    call_minimax,
)

# Logger seguro (no expone la key ni stack traces completos)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("chef_creativo")

# Carga única al inicio — evita releer el .md en cada request
SYSTEM_PROMPT = load_system_prompt()
ESTACIONALIDAD = load_estacionalidad()

logger.info("Chef Creativo — recursos cargados correctamente")


# ---------------------------------------------------------------------------
# Lógica del chat
# ---------------------------------------------------------------------------

def responder(mensaje: str, historial: list) -> dict:
    """
    Procesa una petición del usuario y devuelve la ficha del chef.

    Firma compatible con gr.ChatInterface de Gradio 5+ en formato 'messages':
        fn(mensaje: str, historial: list) -> dict con {role, content}

    Args:
        mensaje: texto crudo que escribió el usuario.
        historial: lista de mensajes previos (formato messages API).

    Returns:
        Dict con la respuesta del chef en formato messages.
    """
    mensaje = (mensaje or "").strip()
    if not mensaje:
        return {"role": "assistant", "content": ""}

    timestamp = datetime.now().strftime("%H:%M:%S")
    logger.info(f"[{timestamp}] Nueva petición (len={len(mensaje)})")

    try:
        # Inyectamos el aviso de estacionalidad como contexto privado al chef.
        # El usuario lo ve solo si el chef decide mencionarlo en su ficha.
        aviso = check_estacionalidad(mensaje, ESTACIONALIDAD)
        contexto_adicional = ""
        if aviso:
            contexto_adicional = (
                f"\n\n[CONTEXTO PRIVADO — NO INCLUIR EN LA SALIDA]: {aviso}"
            )

        user_message = mensaje + contexto_adicional
        respuesta = call_minimax(SYSTEM_PROMPT, user_message)
        return {"role": "assistant", "content": respuesta}

    except Exception as e:
        # NO loggear el valor de la key. Solo el tipo + mensaje truncado.
        tipo = type(e).__name__
        logger.error(f"[{timestamp}] Error procesando petición: {tipo}")
        return {
            "role": "assistant",
            "content": (
                f"❌ Error ({tipo}). "
                f"Detalle: {str(e)[:200]}\n\n"
                f"Si persiste: API key inválida o sin saldo, o timeout de la API."
            ),
        }


# ---------------------------------------------------------------------------
# UI con Gradio 5+
# ---------------------------------------------------------------------------

PROMPT_EJEMPLOS = [
    "Entrante vegetariano con calabaza y queso de cabra",
    "Postre con chocolate y aceite de oliva",
    "Principal de carne para menú degustación de 7 pasos",
    "Plato de verano con tomate y anchoas",
    "Risotto de setas con trufa, para noche de gala",
]

CUSTOM_CSS = """
#titulo {
    text-align: center;
    margin-bottom: 0.5em;
}
footer {visibility: hidden}
"""


# Gradio 6.19+ cambió varias cosas:
#   - 'theme' y 'css' NO van al gr.Blocks() constructor, van al .launch()
#   - ChatInterface no acepta 'type' (ya no existe como kwarg)
#   - Chatbot no acepta 'type' (en 6 es default 'messages' automático)
#   - Mi responder() ya devuelve dict {role, content}, así que messages es el default natural
with gr.Blocks() as demo:
    gr.ChatInterface(
        fn=responder,
        title="🍂 Chef Creativo — RestaurantEAI",
        cache_examples=False,
        description=(
            "Generador de fichas culinarias con IA. Pedime un plato en lenguaje natural "
            "y te devuelvo nombre, historia, ficha técnica, maridaje y prompt para imagen."
        ),
        examples=PROMPT_EJEMPLOS,
        chatbot=gr.Chatbot(
            avatar_images=(None, "🍂"),
        ),
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        show_error=True,
        theme=gr.themes.Soft(primary_hue="orange"),
        css=CUSTOM_CSS,
    )
