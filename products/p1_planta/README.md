# P1 — Caracterización del Cuerpo Académico de Planta

**Monto TdR:** $2.000.000 · **Estado:** no iniciado (esqueleto de carpeta)

## Alcance

Caracterizar al cuerpo académico de **planta (Jornada)** de UCEN: perfil sociodemográfico,
trayectoria académica y carga docente.

## Universo

**624 docentes de Jornada** → `data/cascade/01_jornada/docentes_jornada.csv`
(generado por `shared/etl/01_jornada/etl_jornada.py`, filtro `tipo_contrato_tag = JORNADA`
sobre el universo base de 1.144).

De esos 624: 534 tienen perfil completo vía DOTACION (edad, facultad, nivel de formación,
carga horaria); 90 están solo en NÓMINA. Sub-cascadas dentro de los 534: 513 con sexo
registrado, 485 con fecha de jerarquización.

## Variables disponibles (vía `shared/`)

- Sexo, jerarquía, edad, antigüedad, `unidad_facultad`, nivel de formación, carga horaria
  (`jornada_dot`), fecha de jerarquización — todas en `docentes_jornada.csv` y en
  `analisis.docente_ambos` (enriquecida con `tramo_edad`/`tramo_antiguedad` por
  `shared/etl/complementarios/etl_ped001_perfil.py`).
- EDD (evaluación de jefes): `data/cascade/complementarios/evaluacion_jefes.csv`.
- Rendimiento académico de alumnos: tabla `intel.rendimiento_academico_alumnos`
  (incluye `tipo_contrato_tag` para filtrar por Jornada directo).

## Ya existe

- `slides/fichas/generar_ficha_p1_p2.py` (en este mismo folder) — ficha técnica de
  cascada P1/P2 (6 slides, universo_base correcto, genera `FICHA_P1_P2_v2.pptx`).
- `slides/fichas/generar_ficha_p1_p2_jornada.py` — **roto, pendiente de rehacer**: fuente
  de datos es el universo viejo 917/918, no `universo_base`. No usar sin reescribir.

## Pendiente

Construir el análisis por bloque temático (script + CSV de referencia + PNG juntos por
sub-tema, ver principio de organización en el plan de reorganización), siguiendo el
mismo patrón que P3: distribución por sexo, edad, jerarquía, facultad, nivel de
formación, antigüedad, carga horaria. Revisar TdR para confirmar variables y cruces
exactos pedidos por la contraparte.
