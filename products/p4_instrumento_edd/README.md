# P4 — Evaluación y Rediseño del Instrumento de Evaluación Docente

**Monto TdR:** $2.000.000 · **Estado:** no iniciado (esqueleto de carpeta) · **Cualitativo**

## Alcance

Evaluar el instrumento vigente con el que UCEN mide el desempeño docente (evaluación
estudiantil) y proponer su rediseño. A diferencia de P1-P3, el trabajo es
predominantemente cualitativo (análisis del instrumento, no de resultados agregados).

## Instrumento vigente

`shared/etl/etl_pregunta.py` (movido acá porque define el objeto de estudio de este
producto) documenta el catálogo canónico de preguntas actuales: 19 ítems —
3 Aprendizajes (APR), 5 Metodologías y Evaluación (MET), 9 Aspectos Formales (AFO),
1 Satisfacción binaria (SAT_BIN), 1 Satisfacción con nota (SAT_NOTA).

Fuentes de datos del instrumento actual (en `shared/`, útiles como insumo de diagnóstico,
no como objetivo de P4 en sí): `etl_evaluaciones.py` (respuestas crudas por período),
`etl_catalogo_calificacion.py` (códigos de calificación, en `products/p3_perfeccionamiento/`).

## Pendiente

Sin trabajo iniciado. Próximos pasos: revisar TdR para el alcance metodológico exacto
(entrevistas, benchmarking de instrumentos comparables, análisis de la literatura de
evaluación docente, etc.), y definir con la contraparte el formato de entrega
(informe cualitativo, no necesariamente PPTX/gráficos como P1-P3).
