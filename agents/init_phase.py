"""
init_phase.py — fase de inicialización de un agente.

Se corre UNA SOLA VEZ, la primera vez que se usa cualquier agente del proyecto.
Recolecta información del restaurante y catálogo de platos, y los guarda en
.agent_knowledge/ para que estén disponibles para todos los agentes.

Entrada CLI explícita:
    python -m agents.init_phase

Típicamente se invoca automáticamente vía `ensure_initialized()` desde el entry
point de cada agente (modo_interactivo() para CLI, __main__ para app.py).

Después de la primera corrida:
- NO vuelve a preguntar (idempotente, detecta archivos existentes)
- Cualquier agente nuevo hereda el contexto automáticamente
"""

from __future__ import annotations

from agents.knowledge_context import (
    RESTAURANTE_PATH,
    CATALOGO_PATH,
)


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  PREGUNTAS — Editá estas listas cuando tengas la lista cerrada.           ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
#
# Estructura: lista de tuplas (clave_json, prompt_para_usuario).
# La clave_json se usa en restaurante.json / catalogo_platos.json.
# El prompt es lo que se muestra al usuario en la terminal.
#
# Mientras las listas estén vacías ([]), la fase init no pregunta nada y
# genera archivos con objetos {}. David las va a llenar después.

PREGUNTAS_RESTAURANTE: list[tuple[str, str]] = [
    # Pendiente: David completará con preguntas reales.
    # Ejemplo de estructura:
    # ("nombre", "Nombre del restaurante"),
    # ("ciudad", "Ciudad donde está"),
    # ("tipo_cocina", "Tipo de cocina (mediterránea, catalana, fusión, ...)"),
    # ...
]

PREGUNTAS_POR_PLATO: list[tuple[str, str]] = [
    # Pendiente: David completará.
    # Ejemplo:
    # ("nombre", "Nombre del plato"),
    # ("categoria", "Categoría (entrante, principal, postre, ...)"),
    # ...
]


# ═══════════════════════════════════════════════════════════════════════════════
# Inputs por consola
# ═══════════════════════════════════════════════════════════════════════════════

def _input_opcional(label: str) -> str:
    """Acepta vacío (devuelve string vacío)."""
    return input(f"➤ {label}: ").strip()


def _input_obligatorio(label: str) -> str:
    """No acepta vacío, repregunta hasta tener respuesta."""
    while True:
        r = input(f"➤ {label}: ").strip()
        if r:
            return r
        print("   (obligatorio, no puede quedar vacío)")


def _input_entero(label: str, minimo: int = 0) -> int:
    """Acepta un entero, por defecto 'minimo'."""
    while True:
        r = input(f"➤ {label} [{minimo}]: ").strip()
        if not r:
            return minimo
        try:
            n = int(r)
            if n < minimo:
                print(f"   (mínimo {minimo})")
                continue
            return n
        except ValueError:
            print("   (introduce un número entero)")


# ═══════════════════════════════════════════════════════════════════════════════
# Fase init interactiva
# ═══════════════════════════════════════════════════════════════════════════════

def _imprimir_header() -> None:
    print("\n" + "═" * 60)
    print("🍂  FASE INIT — primera vez del agente")
    print("═" * 60)
    print("Voy a hacerte algunas preguntas para conocerte.")
    print("Esta fase SOLO corre la primera vez. Después arranco directo.")
    print("─" * 60)


def _recolectar_restaurante() -> dict:
    """Ejecuta las preguntas del restaurante y devuelve el dict."""
    if not PREGUNTAS_RESTAURANTE:
        print("\n⚠️  PREGUNTAS_RESTAURANTE está vacío en init_phase.py.")
        print("   Editá el archivo y agregá las preguntas cuando las tengas.")
        print("   Por ahora, restaurante.json se generará como objeto vacío {}.")
        return {}

    print("\n📍 SOBRE TU RESTAURANTE\n")
    respuestas: dict = {}
    for clave, prompt in PREGUNTAS_RESTAURANTE:
        respuestas[clave] = _input_obligatorio(prompt)
    return respuestas


def _recolectar_catalogo() -> list[dict]:
    """Pregunta cuántos platos catalogar y luego pregunta por cada uno."""
    if not PREGUNTAS_POR_PLATO:
        print("\n⚠️  PREGUNTAS_POR_PLATO está vacío en init_phase.py.")
        print("   Editá el archivo y agregá las preguntas cuando las tengas.")
        print("   Por ahora, catalogo_platos.json se generará como lista vacía [].")
        return []

    print("\n🍽️  CATÁLOGO DE PLATOS\n")
    n = _input_entero("¿Cuántos platos querés catalogar ahora?", minimo=0)
    if n == 0:
        print("   (sin platos por ahora — podés catalogar más tarde)")
        return []

    platos: list[dict] = []
    for i in range(n):
        print(f"\n   --- Plato {i + 1}/{n} ---")
        plato: dict = {}
        for clave, prompt in PREGUNTAS_POR_PLATO:
            plato[clave] = _input_obligatorio(prompt)
        platos.append(plato)

    return platos


def _schema_doc_restaurante() -> str:
    return f"""# Contexto del Restaurante

Este archivo documenta el schema de `restaurante.json`.

## Cómo se genera

La fase init (este proyecto, archivo `agents/init_phase.py`) recolecta las
respuestas a `PREGUNTAS_RESTAURANTE` y las guarda acá. Editá manualmente
si querés agregar info que la fase init no recolecta.

## Ubicación física

`{RESTAURANTE_PATH}`

## Cómo lo consumen los agentes

```python
from agents.knowledge_context import cargar_restaurante

data = cargar_restaurante()
print(data["nombre"])
```
"""


def _schema_doc_catalogo() -> str:
    return f"""# Catálogo de Platos

Lista curada de platos que sirve el restaurante. Sirve como referencia para que
los agentes (chef, marketing, costos) tengan un vocabulario común.

## Cómo se genera

La fase init (`agents/init_phase.py`) pregunta cuántos platos querés catalogar
y luego recolecta las respuestas de `PREGUNTAS_POR_PLATO` por cada uno.

## Ubicación física

`{CATALOGO_PATH}`

## Cómo lo consumen los agentes

```python
from agents.knowledge_context import cargar_catalogo

platos = cargar_catalogo()
for plato in platos:
    print(plato["nombre"])
```
"""


def fase_init_interactiva() -> bool:
    """
    Corre el flujo de init si faltan los archivos.

    Returns:
        True si se ejecutó el init, False si los archivos ya existían.
    """
    from agents.knowledge_context import (
        restaurante_existe,
        catalogo_existe,
        guardar_restaurante,
        guardar_catalogo,
    )

    if restaurante_existe() and catalogo_existe():
        return False  # Ya estaba inicializado

    _imprimir_header()

    restaurante = _recolectar_restaurante()
    if restaurante:
        guardar_restaurante(restaurante, _schema_doc_restaurante())
        print(f"\n✓ Guardado: restaurante.json")

    catalogo = _recolectar_catalogo()
    guardar_catalogo(catalogo, _schema_doc_catalogo())
    print(f"✓ Guardado: catalogo_platos.json")

    print("\n" + "═" * 60)
    print("✅ INIT COMPLETO")
    print("═" * 60)
    print("Tus datos están en .agent_knowledge/.")
    print("Cualquier agente nuevo los va a leer automáticamente.")
    print()

    return True


# ═══════════════════════════════════════════════════════════════════════════════
# Entry point CLI
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    """Entry point: python -m agents.init_phase"""
    if not fase_init_interactiva():
        from agents.knowledge_context import resumen_estado
        print("Init ya estaba completo. Estado actual:")
        print(resumen_estado())
        print("(Borrá .agent_knowledge/ si querés volver a correr el init)")


if __name__ == "__main__":
    main()
