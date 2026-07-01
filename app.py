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
    load_skill_prompt,
    load_estacionalidad,
    check_estacionalidad,
    call_minimax,
)
from agents.creativo.skills import (
    list_skills,
    skill_names_for_ui,
    load_skill_prompt as load_skill_prompt_from_registry,
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

# Cache de prompts por skill para evitar releer el .md en cada request
_SKILL_PROMPTS: dict[str, str] = {}


def _get_skill_prompt(skill_key: str) -> str:
    """Carga y cachea el system prompt de la skill."""
    if skill_key not in _SKILL_PROMPTS:
        try:
            _SKILL_PROMPTS[skill_key] = load_skill_prompt_from_registry(skill_key)
        except (KeyError, FileNotFoundError) as e:
            logger.warning(f"No se pudo cargar skill '{skill_key}': {e}. Fallback a 'ficha'.")
            _SKILL_PROMPTS[skill_key] = SYSTEM_PROMPT  # fallback al prompt clásico
    return _SKILL_PROMPTS[skill_key]


def responder(mensaje: str, historial: list, skill: str = "ficha") -> dict:
    """
    Procesa una petición del usuario y devuelve la ficha del chef.

    Firma compatible con gr.ChatInterface de Gradio 5+ en formato 'messages':
        fn(mensaje: str, historial: list, skill: str) -> dict con {role, content}

    Args:
        mensaje: texto crudo que escribió el usuario.
        historial: lista de mensajes previos (formato messages API).
        skill: key de la skill ('ficha' o 'proceso_creativo').

    Returns:
        Dict con la respuesta del chef en formato messages.
    """
    mensaje = (mensaje or "").strip()
    if not mensaje:
        return {"role": "assistant", "content": ""}

    timestamp = datetime.now().strftime("%H:%M:%S")
    logger.info(f"[{timestamp}] Nueva petición (skill={skill}, len={len(mensaje)})")

    system_prompt = _get_skill_prompt(skill)

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

        # 🚨 RECORDATORIO FINAL DE IDIOMA — posicionalmente es lo que más autoridad tiene.
        instruccion_idioma = (
            "\n\n---\n\n"
            "⚠️ RECORDATORIO FINAL ⚠️\n"
            "Responde SOLO en espa\u00f1ol (castellano). El \u00fanico campo que admite ingl\u00e9s "
            "es el \"\ud83c\udfa8 PROMPT PARA IMAGEN DEL PLATO\" al final. "
            "Prohibido: ingl\u00e9s, franc\u00e9s, cir\u00edlico, hanzi, kanji. Solo alfabeto latino."
        )
        user_message = user_message + instruccion_idioma

        respuesta = call_minimax(system_prompt, user_message)
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

# Lista dinámica de skills (cargada del registry)
SKILLS = list_skills()
SKILL_CHOICES = skill_names_for_ui()  # [(key, nombre_visible), ...]

# Ejemplos para la skill 'ficha' (la default). Los de otras skills viven en skills.py.
EJEMPLOS_FICHA = next(
    s["ejemplos"] for s in SKILLS if s["key"] == "ficha"
)

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
#   - additional_inputs pasa inputs adicionales al fn (aca: selector de skill)
with gr.Blocks() as demo:
    skill_selector = gr.Radio(
        choices=SKILL_CHOICES,
        value="ficha",
        label="¿Qué necesitás del chef?",
        info=(
            "Ficha técnica: respuesta estructurada directa. "
            "Proceso creativo: muestra paso a paso cómo piensa el chef, después la ficha."
        ),
    )
    gr.ChatInterface(
        fn=responder,
        title="🍂 Chef Creativo — RestaurantEAI",
        cache_examples=False,
        description=(
            "Generador de fichas culinarias con IA. Pedime un plato en lenguaje natural "
            "y te devuelvo nombre, historia, ficha técnica, maridaje y prompt para imagen. "
            "Cambiá el selector de arriba para ver el proceso creativo paso a paso."
        ),
        examples=EJEMPLOS_FICHA,
        additional_inputs=[skill_selector],
        chatbot=gr.Chatbot(
            avatar_images=(None, "🍂"),
        ),
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Bootstrap del contexto compartido del restaurante.
    # En un entorno interactivo (TTY local), pregunta.
    # En HF Spaces (sin TTY), genera archivos vacíos con warning.
    from agents.knowledge_context import (
        bootstrap_necesario,
        cargar_restaurante,
        guardar_restaurante,
        guardar_catalogo,
    )
    from agents.init_phase import _schema_doc_restaurante, _schema_doc_catalogo

    if bootstrap_necesario():
        if sys.stdin.isatty():
            from agents.init_phase import fase_init_interactiva
            fase_init_interactiva()
        else:
            # HF Space o CI: sin TTY. Generamos vacíos + warning.
            logger.warning(
                "Knowledge base no inicializada. "
                "Para personalizarla, corré localmente: python -m agents.init_phase"
            )
            guardar_restaurante({}, _schema_doc_restaurante())
            guardar_catalogo([], _schema_doc_catalogo())
            logger.info("Archivos vacíos generados automáticamente.")

    # Carga del contexto (ya disponible para todos los agentes)
    restaurante = cargar_restaurante()
    logger.info(f"Restaurante cargado: {restaurante.get('nombre', '(sin nombre)')}")

    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        show_error=True,
        theme=gr.themes.Soft(primary_hue="orange"),
        css=CUSTOM_CSS,
    )
