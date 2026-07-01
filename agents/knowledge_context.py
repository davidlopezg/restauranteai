"""
knowledge_context.py — archivos compartidos entre TODOS los agentes del proyecto.

Estos archivos viven en `.agent_knowledge/` (en la raíz del repo) y se generan
una sola vez en la fase init. Cualquier agente nuevo los lee al iniciar.

Diferencia vs `agents/creativo/knowledge/`:
- `agents/creativo/knowledge/` = conocimiento ESTÁTICO del agente creativo
  (estacionalidad, combinaciones clásicas). Recursos del chef, no se generan.
- `.agent_knowledge/` (gestionado por este módulo) = conocimiento DINÁMICO del
  restaurante, generado en init, compartido entre todos los agentes.
"""

from __future__ import annotations

import json
from pathlib import Path

# Ubicación física: <raíz del proyecto>/.agent_knowledge/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = PROJECT_ROOT / ".agent_knowledge"

RESTAURANTE_PATH = KNOWLEDGE_DIR / "restaurante.json"
RESTAURANTE_DOC_PATH = KNOWLEDGE_DIR / "restaurante.md"
CATALOGO_PATH = KNOWLEDGE_DIR / "catalogo_platos.json"
CATALOGO_DOC_PATH = KNOWLEDGE_DIR / "catalogo_platos.md"


def ensure_dir() -> Path:
    """Crea el directorio .agent_knowledge/ si no existe. Idempotente."""
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    return KNOWLEDGE_DIR


def restaurante_existe() -> bool:
    return RESTAURANTE_PATH.exists()


def catalogo_existe() -> bool:
    return CATALOGO_PATH.exists()


def bootstrap_necesario() -> bool:
    """True si falta cualquiera de los dos archivos clave."""
    return not (restaurante_existe() and catalogo_existe())


def ensure_initialized() -> bool:
    """
    Si falta el init, lo corre interactivamente.
    Helper para que cada agente lo llame en su entry point.

    Returns:
        True si se ejecutó el init, False si ya estaba listo.
    """
    if bootstrap_necesario():
        from agents.init_phase import fase_init_interactiva
        return fase_init_interactiva()
    return False


def cargar_restaurante() -> dict:
    if not restaurante_existe():
        raise FileNotFoundError(
            f"No existe {RESTAURANTE_PATH}. Corre la fase init primero."
        )
    with RESTAURANTE_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def cargar_catalogo() -> list[dict]:
    if not catalogo_existe():
        raise FileNotFoundError(
            f"No existe {CATALOGO_PATH}. Corre la fase init primero."
        )
    with CATALOGO_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def guardar_restaurante(data: dict, schema_doc: str | None = None) -> Path:
    """Guarda el dict del restaurante como JSON. Opcionalmente, un .md companion."""
    ensure_dir()
    with RESTAURANTE_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    if schema_doc:
        with RESTAURANTE_DOC_PATH.open("w", encoding="utf-8") as f:
            f.write(schema_doc)
    return RESTAURANTE_PATH


def guardar_catalogo(platos: list[dict], schema_doc: str | None = None) -> Path:
    """Guarda la lista de platos como JSON. Opcionalmente, un .md companion."""
    ensure_dir()
    with CATALOGO_PATH.open("w", encoding="utf-8") as f:
        json.dump(platos, f, ensure_ascii=False, indent=2)
    if schema_doc:
        with CATALOGO_DOC_PATH.open("w", encoding="utf-8") as f:
            f.write(schema_doc)
    return CATALOGO_PATH


def listar_archivos_knowledge() -> list[Path]:
    """Lista todos los archivos en .agent_knowledge/ (útil para debug)."""
    if not KNOWLEDGE_DIR.exists():
        return []
    return sorted(KNOWLEDGE_DIR.iterdir())


def resumen_estado() -> str:
    """Devuelve un string con el estado actual del knowledge base."""
    if not KNOWLEDGE_DIR.exists():
        return ".agent_knowledge/ no existe aún (no se corrió la fase init)."

    lineas = [".agent_knowledge/:"]
    for path in listar_archivos_knowledge():
        size = path.stat().st_size
        lineas.append(f"  - {path.name} ({size} bytes)")

    if bootstrap_necesario():
        lineas.append("  ⚠️  INIT PENDIENTE (falta restaurante.json o catalogo_platos.json)")
    else:
        lineas.append("  ✓ INIT COMPLETO")

    return "\n".join(lineas)
