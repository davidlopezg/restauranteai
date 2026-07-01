"""
init_phase.py — fase de inicialización de un agente.

Se corre UNA SOLA VEZ, la primera vez que se usa cualquier agente del proyecto.
Recolecta 15 dimensiones conceptuales del restaurante y catálogo de platos,
y los guarda en .agent_knowledge/ para que estén disponibles para todos
los agentes del proyecto.

Entrada CLI explícita:
    python -m agents.init_phase

Típicamente se invoca automáticamente vía `ensure_initialized()` desde el entry
point de cada agente (modo_interactivo() para CLI, __main__ para app.py).
"""

from __future__ import annotations

from agents.knowledge_context import (
    RESTAURANTE_PATH,
    CATALOGO_PATH,
)


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  PREGUNTAS — Cada dict define una dimensión del restaurante.              ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
#
# Tipos de pregunta:
#   - "number":     pide un número
#   - "choice":     una opción de N
#   - "multichoice": varias opciones de N (índices separados por coma)
#   - "text":       input libre
#
# Campos:
#   - "key":     clave en restaurante.json
#   - "prompt":  texto que ve el usuario
#   - "type":    uno de los 4 tipos de arriba
#   - "options": lista (solo para choice / multichoice)
#   - "help":    (opcional) texto auxiliar

PREGUNTAS_RESTAURANTE: list[dict] = [
    # ─── PRECIO / TARGET ────────────────────────────────────────────────────
    {
        "key": "precio_target_min",
        "prompt": "Ticket medio mínimo que querés ofrecer (en €, por persona)",
        "type": "number",
        "help": "Por ej: 30",
    },
    {
        "key": "precio_target_max",
        "prompt": "Ticket medio máximo que querés ofrecer (en €, por persona)",
        "type": "number",
        "help": "Por ej: 80",
    },
    {
        "key": "precio_target_moda",
        "prompt": "Ticket medio 'modo' (el más típico que apuntás, en €)",
        "type": "number",
        "help": "Por ej: 50",
    },
    # ─── SOFISTICACIÓN ───────────────────────────────────────────────────────
    {
        "key": "sofisticacion",
        "prompt": "Sofisticación de la oferta",
        "type": "choice",
        "options": ["muy_alta", "alta", "media", "baja", "muy_baja"],
        "help": "De muy sofisticada a muy básica.",
    },
    # ─── PRODUCTOS DOMINANTES ────────────────────────────────────────────────
    {
        "key": "productos_dominantes",
        "prompt": "Productos dominantes de tu cocina (podés elegir varios)",
        "type": "multichoice",
        "options": [
            "vegetales", "carne", "pescado", "mariscos",
            "integrales", "lacteos", "fermentados", "fruta",
            "legumbres", "cereales_granos", "setas",
        ],
        "help": "Los productos que más mandan en tu carta.",
    },
    # ─── TÉCNICAS DOMINANTES ─────────────────────────────────────────────────
    {
        "key": "tecnicas_dominantes",
        "prompt": "Técnicas / elaboraciones dominantes (podés elegir varias)",
        "type": "multichoice",
        "options": [
            "brasas", "arroces", "ahumado", "fermentacion",
            "crudo", "baja_temperatura", "fritura", "guisos",
            "plancha", "horno_leña", "vapor", "salazón",
        ],
        "help": "Las técnicas que más usás día a día.",
    },
    # ─── TIPO DE SERVICIO ────────────────────────────────────────────────────
    {
        "key": "tipo_servicio",
        "prompt": "Tipo de servicio principal (podés elegir varios)",
        "type": "multichoice",
        "options": [
            "servicio_tradicional", "barra", "autoservicio",
            "take_away", "delivery", "catering_eventos",
        ],
        "help": "Cómo recibís al cliente.",
    },
    # ─── GRUPOS ──────────────────────────────────────────────────────────────
    {
        "key": "grupos",
        "prompt": "¿Cómo es tu política con grupos?",
        "type": "choice",
        "options": [
            "sin_grupos",
            "con_grupos_pequenos",
            "con_grupos_grandes",
            "banquetes_eventos",
        ],
        "help": "Si no recibís grupos vs. si los banquetes son parte del negocio.",
    },
    # ─── CLASES DE COMEDORES ─────────────────────────────────────────────────
    {
        "key": "clases_comedores",
        "prompt": "Clase de comedores (podés elegir varias)",
        "type": "multichoice",
        "options": ["privados_vip", "sociales_familia", "mixto", "business", "turistas"],
        "help": "A qué tipo de cliente apuntás.",
    },
    # ─── ORIGEN / INSPIRACIÓN ────────────────────────────────────────────────
    {
        "key": "origen_inspiracion",
        "prompt": "Origen o inspiración geográfica / sociopolítica dominante",
        "type": "choice",
        "options": [
            "local_pueblo",
            "regional_provincia",
            "nacional_pais",
            "mediterraneo",
            "latinoamericano",
            "asiatico",
            "norte_europeo",
            "frances_gourmet",
            "internacional_fusion",
        ],
        "help": "De dónde viene la inspiración principal de tu cocina.",
    },
    # ─── ORIENTACIÓN NUTRICIONAL ─────────────────────────────────────────────
    {
        "key": "orientacion_nutricional",
        "prompt": "Orientación nutricional prioritaria (podés elegir varias)",
        "type": "multichoice",
        "options": [
            "ninguna",
            "origen_producto",
            "vegetariana",
            "vegana",
            "sin_gluten",
            "baja_azucar",
            "baja_sal",
            "ecologica_bio",
            "km0",
            "temporada",
        ],
        "help": "Lo que ofrecés como identidad nutricional o valores.",
    },
    # ─── LOCALIZACIÓN ────────────────────────────────────────────────────────
    {
        "key": "localizacion",
        "prompt": "Localización del restaurante",
        "type": "choice",
        "options": ["urbana", "rural", "litoral_mar", "montana", "singular_edificio_historico"],
        "help": "Dónde está físicamente (afecta producto y oferta).",
    },
    # ─── RELIGIÓN / RESTRICCIONES ────────────────────────────────────────────
    {
        "key": "religion",
        "prompt": "Restricciones religiosas prioritarias que manejás (varias)",
        "type": "multichoice",
        "options": [
            "ninguna",
            "musulmana_halal",
            "judia_kosher",
            "hindu_vegetariana",
            "budista",
        ],
        "help": "Si tu cocina contempla estas restricciones de forma estable.",
    },
    # ─── TIEMPO ──────────────────────────────────────────────────────────────
    {
        "key": "tiempo_preparacion",
        "prompt": "Tiempo de preparación / ingestión del comensal",
        "type": "choice",
        "options": ["comida_rapida", "medio", "slow_food"],
        "help": "Si tu cliente está 20 minutos o 3 horas en la mesa.",
    },
    # ─── ÉPOCA / ESTILO ──────────────────────────────────────────────────────
    {
        "key": "epoca_estilo",
        "prompt": "Época, movimiento o estilo dominante (podés elegir varios)",
        "type": "multichoice",
        "options": [
            "medieval",
            "clasica_francesa",
            "tradicional_popular",
            "rustica_pais",
            "mediterranea_moderna",
            "nouvelle_cuisine",
            "autor_contemporanea",
            "street_food_gourmet",
            "casual_actual",
        ],
        "help": "La corriente / estilo que más te representa.",
    },
]

PREGUNTAS_POR_PLATO: list[dict] = [
    # Lo definiremos cuando sepamos qué catalogar exactamente.
]


# ═══════════════════════════════════════════════════════════════════════════════
# Inputs por consola — UI adaptativa según tipo
# ═══════════════════════════════════════════════════════════════════════════════

def _ask_header(prompt: str, help_text: str | None = None) -> None:
    """Imprime el prompt + ayuda antes de pedir input."""
    print(f"\n➤ {prompt}")
    if help_text:
        print(f"   ({help_text})")


def _input_text(prompt: str, help_text: str | None = None, allow_empty: bool = True) -> str:
    """Input libre. Si allow_empty=True, acepta vacío."""
    _ask_header(prompt, help_text)
    return input("   > ").strip()


def _input_number(prompt: str, help_text: str | None = None) -> float:
    """Input numérico (acepta entero o decimal). Reintenta si no parsea."""
    _ask_header(prompt, help_text)
    while True:
        r = input("   > ").strip()
        try:
            return float(r)
        except ValueError:
            print("   (introduce un número válido)")


def _input_choice(prompt: str, options: list[str], help_text: str | None = None) -> str:
    """Elige UNO de N opciones numeradas."""
    print(f"\n➤ {prompt}")
    if help_text:
        print(f"   ({help_text})")
    for i, opt in enumerate(options, 1):
        print(f"   {i}. {opt}")
    while True:
        r = input(f"   Elige 1-{len(options)} > ").strip()
        if r.isdigit() and 1 <= int(r) <= len(options):
            return options[int(r) - 1]
        print(f"   (elegí un número entre 1 y {len(options)})")


def _input_multichoice(prompt: str, options: list[str], help_text: str | None = None) -> list[str]:
    """Elige VARIOS de N opciones, separadas por coma. Vacío = []."""
    print(f"\n➤ {prompt}")
    if help_text:
        print(f"   ({help_text})")
    for i, opt in enumerate(options, 1):
        print(f"   {i}. {opt}")
    print("   (separá los números con coma, ej: 1,3,5 — vacío = ninguno)")
    while True:
        r = input("   > ").strip()
        if not r:
            return []
        partes = [p.strip() for p in r.split(",") if p.strip()]
        if all(p.isdigit() and 1 <= int(p) <= len(options) for p in partes):
            indices_unicos = sorted(set(int(p) for p in partes))
            return [options[i - 1] for i in indices_unicos]
        print("   (formato: 1,3,5 — números válidos separados por coma)")


def _ask_question(q: dict):
    """Dispatcher: ejecuta una pregunta según su type y devuelve el valor."""
    qtype = q["type"]
    options = q.get("options", [])
    help_text = q.get("help")

    if qtype == "text":
        return _input_text(q["prompt"], help_text, allow_empty=True)
    elif qtype == "number":
        return _input_number(q["prompt"], help_text)
    elif qtype == "choice":
        return _input_choice(q["prompt"], options, help_text)
    elif qtype == "multichoice":
        return _input_multichoice(q["prompt"], options, help_text)
    else:
        raise ValueError(f"Tipo de pregunta desconocido: {qtype}")


# ═══════════════════════════════════════════════════════════════════════════════
# Recolección de datos
# ═══════════════════════════════════════════════════════════════════════════════

def _imprimir_header() -> None:
    print("\n" + "═" * 60)
    print("🍂  FASE INIT — primera vez del agente")
    print("═" * 60)
    print("Voy a hacerte 15 preguntas sobre tu restaurante.")
    print("Esta fase SOLO corre la primera vez. Después arranco directo.")
    print("─" * 60)


def _recolectar_restaurante() -> dict:
    """Ejecuta las 15 preguntas del restaurante y devuelve el dict final."""
    if not PREGUNTAS_RESTAURANTE:
        print("\n⚠️  PREGUNTAS_RESTAURANTE está vacío en init_phase.py.")
        print("   Por ahora, restaurante.json se generará como objeto vacío {}.")
        return {}

    print("\n📍 SOBRE TU RESTAURANTE")
    print(f"   ({len(PREGUNTAS_RESTAURANTE)} preguntas, ~5-10 min)")
    print("   En cualquier momento podés responder vacío en multichoice\n")

    respuestas: dict = {}
    total = len(PREGUNTAS_RESTAURANTE)
    for i, q in enumerate(PREGUNTAS_RESTAURANTE, 1):
        print(f"\n── Pregunta {i}/{total} ──")
        respuestas[q["key"]] = _ask_question(q)

    return respuestas


def _recolectar_catalogo() -> list[dict]:
    """Pregunta cuántos platos catalogar y luego pregunta por cada uno."""
    if not PREGUNTAS_POR_PLATO:
        print("\n⚠️  PREGUNTAS_POR_PLATO está vacío en init_phase.py.")
        print("   (catalogo_platos.json se generará como lista vacía [])")
        return []

    print("\n🍽️  CATÁLOGO DE PLATOS\n")
    n_str = ""
    while not n_str.isdigit():
        n_str = input("➤ ¿Cuántos platos querés catalogar ahora? (0 para saltar): ").strip()
    n = int(n_str)
    if n == 0:
        print("   (sin platos por ahora — podés catalogar más tarde editando)")
        return []

    platos: list[dict] = []
    for i in range(n):
        print(f"\n   --- Plato {i + 1}/{n} ---")
        plato: dict = {}
        for q in PREGUNTAS_POR_PLATO:
            plato[q["key"]] = _ask_question(q)
        platos.append(plato)

    return platos


# ═══════════════════════════════════════════════════════════════════════════════
# Schema docs (companion .md que explica el formato)
# ═══════════════════════════════════════════════════════════════════════════════

def _schema_doc_restaurante() -> str:
    return f"""# Contexto del Restaurante

Schema multidimensional del restaurante, recolectado en la fase init.

## Estructura JSON

El archivo `restaurante.json` contiene 15 dimensiones (ver `PREGUNTAS_RESTAURANTE`
en `agents/init_phase.py` para la lista cerrada). Tipos de valor:

- **number**: número (ticket min/max/moda)
- **choice**: string (un valor de la lista de opciones)
- **multichoice**: array de strings (subset de la lista de opciones)
- **text**: string libre

## Las 15 dimensiones

| Key | Tipo | Descripción |
|---|---|---|
| `precio_target_min` | number | Ticket mínimo en € por persona |
| `precio_target_max` | number | Ticket máximo en € por persona |
| `precio_target_moda` | number | Ticket típico/moda en € por persona |
| `sofisticacion` | choice | muy_alta / alta / media / baja / muy_baja |
| `productos_dominantes` | multichoice | vegetales, carne, pescado, mariscos, integrales, ... |
| `tecnicas_dominantes` | multichoice | brasas, arroces, ahumado, fermentacion, ... |
| `tipo_servicio` | multichoice | servicio_tradicional, barra, autoservicio, ... |
| `grupos` | choice | sin_grupos / con_grupos_pequenos / con_grupos_grandes / banquetes_eventos |
| `clases_comedores` | multichoice | privados_vip, sociales_familia, mixto, business, turistas |
| `origen_inspiracion` | choice | local_pueblo / regional / mediterraneo / ... |
| `orientacion_nutricional` | multichoice | vegetariana, vegana, sin_gluten, origen_producto, ... |
| `localizacion` | choice | urbana / rural / litoral_mar / montaña / singular |
| `religion` | multichoice | ninguna / musulmana_halal / judia_kosher / hindu_vegetariana / budista |
| `tiempo_preparacion` | choice | comida_rapida / medio / slow_food |
| `epoca_estilo` | multichoice | mediterranea_moderna, autor_contemporanea, tradicional_popular, ... |

## Ubicación física

`{RESTAURANTE_PATH}`

## Cómo lo consumen los agentes

```python
from agents.knowledge_context import cargar_restaurante

data = cargar_restaurante()
if data["sofisticacion"] == "alta":
    ...
if "vegetales" in data["productos_dominantes"]:
    ...
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


# ═══════════════════════════════════════════════════════════════════════════════
# Entry point principal
# ═══════════════════════════════════════════════════════════════════════════════

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
        return False

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


def main() -> None:
    """Entry point: python -m agents.init_phase"""
    if not fase_init_interactiva():
        from agents.knowledge_context import resumen_estado
        print("Init ya estaba completo. Estado actual:")
        print(resumen_estado())
        print("(Borrá .agent_knowledge/ si querés volver a correr el init)")


if __name__ == "__main__":
    main()
