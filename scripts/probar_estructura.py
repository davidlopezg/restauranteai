"""
probar_estructura.py
====================

Script de validación SIN API. Sirve para confirmar que:
- Las dependencias están instaladas
- Los archivos de recursos existen y son legibles
- La configuración se carga bien
- El system prompt tiene la estructura esperada

NO hace llamadas a MiniMax. NO consume créditos.

Uso:
    python scripts/probar_estructura.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Hacer importable el paquete agents
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")


def check(label: str, ok: bool, detalle: str = "") -> bool:
    icono = "✅" if ok else "❌"
    print(f"  {icono} {label}" + (f" — {detalle}" if detalle else ""))
    return ok


def main():
    print("\n" + "=" * 60)
    print("🧪 Validación de estructura — RestaurantEAI MVP-0")
    print("=" * 60 + "\n")

    todo_ok = True

    # 1. Dependencias
    print("1. Dependencias Python")
    try:
        import httpx
        check("httpx", True, f"versión {httpx.__version__}")
    except ImportError:
        check("httpx", False, "ejecutá: pip install -r requirements.txt")
        todo_ok = False

    try:
        import dotenv
        check("python-dotenv", True)
    except ImportError:
        check("python-dotenv", False, "ejecutá: pip install -r requirements.txt")
        todo_ok = False

    print()

    # 2. Archivos de recursos
    print("2. Archivos del agente")
    from agents.creativo.agent import (
        PROMPT_PATH, ESTACIONALIDAD_PATH, load_system_prompt, load_estacionalidad
    )

    todo_ok &= check(
        "System prompt existe",
        PROMPT_PATH.exists(),
        str(PROMPT_PATH.relative_to(PROJECT_ROOT))
    )

    todo_ok &= check(
        "Estacionalidad existe",
        ESTACIONALIDAD_PATH.exists(),
        str(ESTACIONALIDAD_PATH.relative_to(PROJECT_ROOT))
    )

    csv_path = PROJECT_ROOT / "agents" / "creativo" / "knowledge" / "combinaciones_clasicas.csv"
    todo_ok &= check(
        "Combinaciones clásicas existe",
        csv_path.exists(),
        str(csv_path.relative_to(PROJECT_ROOT))
    )

    print()

    # 3. Carga de contenido
    print("3. Contenido legible")
    try:
        prompt = load_system_prompt()
        check("System prompt cargable", len(prompt) > 500, f"{len(prompt)} caracteres")
    except Exception as e:
        check("System prompt cargable", False, str(e))
        todo_ok = False

    try:
        est = load_estacionalidad()
        n_productos = len(est.get("productos", {}))
        check("Estacionalidad cargable", n_productos > 10, f"{n_productos} productos catalogados")
    except Exception as e:
        check("Estacionalidad cargable", False, str(e))
        todo_ok = False

    print()

    # 4. Configuración
    print("4. Variables de entorno (.env)")
    import os
    api_key = os.getenv("MINIMAX_API_KEY")
    base_url = os.getenv("MINIMAX_BASE_URL")  # None si no está
    model = os.getenv("MINIMAX_MODEL")        # None si no está

    # Importamos los defaults verificados del agente cableado.
    from agents.creativo.agent import DEFAULT_BASE_URL, DEFAULT_MODEL, BASE_URL as AGENT_BASE_URL

    # 4a) MINIMAX_API_KEY — bloqueante, sin esto no se puede llamar a la API.
    api_key_ok = bool(api_key) and api_key != "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    if api_key_ok:
        check("MINIMAX_API_KEY configurada", True, "OK (no se muestra por seguridad)")
    else:
        check(
            "MINIMAX_API_KEY configurada",
            False,
            "BLOQUEANTE — pegá tu key real en .env antes de probar el agente"
        )
        todo_ok = False

    # 4b) MINIMAX_BASE_URL — si no está, usa default verificado de MiniMax.
    if base_url:
        check("MINIMAX_BASE_URL configurada", True, base_url)
    else:
        check(
            "MINIMAX_BASE_URL configurada",
            True,  # OK porque hay default verificado
            f"no seteada → usará default verificado: {DEFAULT_BASE_URL}"
        )

    # 4c) MINIMAX_MODEL — idem.
    if model:
        check("MINIMAX_MODEL configurado", True, model)
    else:
        check(
            "MINIMAX_MODEL configurado",
            True,
            f"no seteado → usará default verificado: {DEFAULT_MODEL}"
        )

    print()

    # 5. Validación de URL y modelo contra la lista oficial de MiniMax
    print("5. Conformidad con endpoints y modelos oficiales MiniMax")
    import re

    # Lista de modelos oficiales MiniMax (texto-generation):
    # Fuente: https://platform.minimax.io/docs/guides/models-intro
    MODELOS_OFICIALES = {
        "MiniMax-M3",
        "MiniMax-M2.7",
        "MiniMax-M2.7-highspeed",
        "MiniMax-M2.5",
        "MiniMax-M2.5-highspeed",
        "MiniMax-M2.1",
        "MiniMax-M2.1-highspeed",
        "MiniMax-M2",
    }

    # URL debe apuntar al dominio oficial api.minimax.io
    url_efectiva = base_url or AGENT_BASE_URL
    url_ok = ("api.minimax.io" in url_efectiva)
    if url_ok:
        check(
            "URL apunta a api.minimax.io (oficial)",
            True,
            url_efectiva
        )
    else:
        check(
            "URL apunta a api.minimax.io (oficial)",
            False,
            f"⚠️  La URL ({url_efectiva}) NO es la oficial. "
            f"Esto te va a dar 401 o respuestas vacías. "
            f"Cambiala a https://api.minimax.io/v1 o dejala vacía para usar el default verificado."
        )
        todo_ok = False

    modelo_efectivo = model or DEFAULT_MODEL
    if modelo_efectivo in MODELOS_OFICIALES:
        check(
            f"Modelo '{modelo_efectivo}' está en la lista oficial",
            True,
            "OK"
        )
    else:
        check(
            f"Modelo '{modelo_efectivo}' está en la lista oficial",
            False,
            f"Modelo desconocido. Lista oficial: {sorted(MODELOS_OFICIALES)}"
        )
        todo_ok = False

    print()

    # 6. Validación de estacionalidad (ejemplo)
    print("5. Validación de estacionalidad (ejemplo)")
    from agents.creativo.agent import check_estacionalidad

    ejemplos = [
        "Entrante con calabaza y queso de cabra",  # calabaza fuera de temporada en junio
        "Gazpacho de tomate y pepino",              # tomate en temporada
        "Risotto de setas y trufa",                 # ambas fuera en junio
    ]

    for ej in ejemplos:
        aviso = check_estacionalidad(ej, load_estacionalidad())
        if aviso:
            print(f"     · \"{ej}\" → {aviso.splitlines()[0].strip()}")
        else:
            print(f"     · \"{ej}\" → todo en temporada ✓")

    print()
    print("=" * 60)
    if todo_ok:
        print("🎉 Todo OK. Podés correr el agente:")
        print("    python -m agents.creativo.agent \"tu petición aquí\"")
    else:
        print("⚠️  Hay cosas para arreglar antes de ejecutar el agente.")
        print("    Revisá los ❌ de arriba.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()