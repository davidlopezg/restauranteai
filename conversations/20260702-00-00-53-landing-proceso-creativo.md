# Landing — proceso creativo y fase introductoria

## Contexto
Usuario pidió dejar claro en la landing que el chef tiene una **fase introductoria** (entrevista para obtener el máximo de información) y que se puede **ejecutar el proceso creativo** explícito.

## Cambios aplicados (docs/index.html)
1. **Sección "Cómo funciona"** — de 3 a 4 pasos:
   - Escribís tu idea
   - **El chef pregunta** (NUEVO): detecta lo que falta y pregunta lo mínimo (estacionalidad, ocasión, comensales, presupuesto, restricciones). No inventa.
   - El chef razona (ahora menciona explícitamente las 7 fases)
   - Recibís la ficha

2. **Sección nueva "Proceso creativo"** entre "Cómo funciona" y "Tecnología":
   - Callout: deja claro que existe un modo directo Y un proceso creativo explícito a demanda
   - 7 fase-cards con las fases reales del state machine (proceso_creativo.py):
     alma → métodos creativos → equilibrio → técnica → storytelling → descartadas → preguntas
   - 11 métodos creativos como pills (los de ElBulli documentados en metodos-creativos.md):
     lo autóctono, influencias externas, los sentidos, sexto sentido, simbiosis dulce/salado,
     asociación, inspiración, adaptación, deconstrucción, minimalismo, sinergia
   - Acento visual en 4 métodos "estrella" (lo autóctono, sexto sentido, asociación, sinergia)

3. **CSS agregado**: `.callout`, `.fase-grid`, `.fase-card`, `.methods-block`, `.methods-pills`, `.pill`, `.pill-accent`

## Verificación
- HTML válido (parser sin errores, 0 tags sin cerrar)
- Tamaño final: 21.583 bytes (+3.207 sobre la versión previa de 18.376)
- Diseño intacto: misma paleta, mismas fuentes, mismos paddings

## Decisión de producto (memory)
- La landing debe reflejar fielmente las capacidades del sistema.
- Cualquier feature nueva → actualizar la landing en el mismo cambio.
