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

def responder(mensaje: str, historial: list) -> tuple[str, list]:
    """
    Procesa una petición del usuario y devuelve la ficha del chef.

    Args:
        mensaje: texto crudo que escribió el usuario
        historial: lista de tuplas [(user_msg, bot_msg), ...] de Gradio

    Returns:
        Tupla (mensaje_vacío, historial_actualizado) — el input se limpia.
    """
    mensaje = (mensaje or "").strip()
    if not mensaje:
        return "", historial

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

        historial = historial + [(mensaje, respuesta)]
        return "", historial

    except Exception as e:
        # NO loggear el valor de la key. Solo el tipo + mensaje truncado.
        tipo = type(e).__name__
        logger.error(f"[{timestamp}] Error procesando petición: {tipo}")
        error_msg = (
            f"❌ Error ({tipo}). "
            f"Detalle: {str(e)[:200]}\n\n"
            f"Si este error persiste, puede ser:\n"
            f"- API key inválida o sin saldo\n"
            f"- Timeout de la API (reintentar en unos segundos)"
        )
        historial = historial + [(mensaje, error_msg)]
        return "", historial


# ---------------------------------------------------------------------------
# UI con Gradio
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
#subtitulo {
    text-align: center;
    color: #6b7280;
    margin-bottom: 1em;
}
footer {visibility: hidden}
"""


def construir_ui() -> gr.Blocks:
    with gr.Blocks(
        title="Chef Creativo — RestaurantEAI",
        theme=gr.themes.Soft(primary_hue="orange"),
        css=CUSTOM_CSS,
    ) as demo:
        gr.Markdown(
            """
            # 🍂 Chef Creativo — RestaurantEAI

            *Generador de fichas culinarias con IA. Pedime un plato en lenguaje
            natural y te devuelvo nombre, historia, ficha técnica, maridaje y
            prompt para imagen.*

            ---

            ### 💡 Ejemplos para probar
            """
        )

        with gr.Row():
            for ejemplo in PROMPT_EJEMPLOS[:3]:
                gr.Button(ejemplo, size="sm").click(
                    fn=lambda txt=ejemplo: txt,
                    outputs=msg,
                )

        with gr.Row():
            for ejemplo in PROMPT_EJEMPLOS[3:]:
                gr.Button(ejemplo, size="sm").click(
                    fn=lambda txt=ejemplo: txt,
                    outputs=msg,
                )

        chatbot = gr.Chatbot(
            label="Conversación",
            height=420,
            show_label=False,
            avatar_images=(None, "🍂"),
            type="tuples",
        )

        with gr.Row():
            msg = gr.Textbox(
                placeholder="Escribí tu petición culinaria y presioná Enter...",
                label="Petición",
                scale=4,
                autofocus=True,
            )
            send = gr.Button("Enviar 🍳", scale=1, variant="primary")

        clear = gr.Button("🧹 Limpiar conversación")

        gr.Markdown(
            """
            ---

            ⚠️ **MVP en desarrollo.** Cada llamada consulta la API de MiniMax y
            consume saldo. Latencia esperada: 5-15 segundos.

            💡 **Tip:** si el plato depende de ingredientes fuera de temporada
            (en Cataluña), el chef lo señala y propone alternativas.
            """
        )

        # Wire-up de eventos
        msg.submit(responder, inputs=[msg, chatbot], outputs=[msg, chatbot])
        send.click(responder, inputs=[msg, chatbot], outputs=[msg, chatbot])
        clear.click(lambda: [], outputs=chatbot)

    return demo


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    demo = construir_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        show_error=True,
    )
