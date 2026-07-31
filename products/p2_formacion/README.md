# P2 — Participación en Formación Docente

**Monto TdR:** $600.000 · **Estado:** no iniciado (esqueleto de carpeta)

## Alcance

Analizar la participación del cuerpo académico en las actividades de formación docente
de P3 (Talleres, Diplomados, Proyectos): cobertura, distribución por tipo de iniciativa,
jerarquía y facultad.

A diferencia de P1, P2 **incluye Jornada y Honorario** — no se acota a planta.

## Universo

**726 docentes únicos** con al menos 1 iniciativa de formación →
`data/cascade/04_formados_p3/docentes_formados.csv` (2.190 filas, una por iniciativa).

Tipos de iniciativa: TALLER (1.906), DIPLOMADO (242), PROYECTO (42).
**418 docentes** del universo base (de 1.144) no participaron en ninguna iniciativa.

## Variables disponibles (vía `shared/`)

- `shared/etl/complementarios/etl_participacion_formacion.py` genera la cadena completa:
  participación sin filtrar (`P3_participacion_formacion_todos.csv`), el grupo control
  natural (520 AMBOS sin formación), y el resumen por tipo/año.
- Perfil de cada docente (edad, facultad, jerarquía, `tramo_edad`/`tramo_antiguedad`) vía
  `analisis.docente_ambos`.

## Ya existe

- `products/p1_planta/slides/fichas/generar_ficha_p1_p2.py` — ficha técnica de cascada
  P1/P2 (slide 5 y 6 cubren la cascada P2: 1.144 → 726 formados → 2.190 iniciativas, más
  solicitudes de datos para ampliar el universo).
- Referencia legacy (universo 917/918, no usar como fuente): `archive/legacy_918/ENTREGABLE_P2_918.docx`.

## Pendiente

Construir el análisis por bloque temático (script + CSV de referencia + PNG juntos por
sub-tema): cobertura de formación, distribución por tipo de iniciativa, cruces con
jerarquía y facultad. Revisar TdR para confirmar variables y cruces exactos pedidos por
la contraparte.
