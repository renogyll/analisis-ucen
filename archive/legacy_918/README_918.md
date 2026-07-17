# Legacy — Universo N≈918 (Jerarquizados)

## Qué contiene este directorio

Todo el trabajo de análisis realizado bajo el supuesto de que el universo base
del proyecto eran los docentes con **jerarquía académica asignada** (N≈918).

- `NOTEBOOKS/` — scripts de presentación PPTX, G*.py de visualización, scripts Word
- `PROCESADO/` — scripts ETL específicos para este universo
- `QA/` — scripts de validación de datos para este universo

## Por qué se replanteó (2026-07-15)

El criterio de "jerarquizados" era un **filtro implícito no documentado** que marginaba
a docentes honorarios y sin jerarquía formal del análisis, sin justificación metodológica
explícita. Al descubrir que el universo real (NOMINA × DOTACION) es considerablemente
más amplio, se decidió:

1. El universo base pasa a ser todos los RUTs únicos de NOMINA × DOTACION
2. La jerarquía académica pasa a ser un **campo descriptivo**, no un criterio de exclusión
3. La cascada de subconjuntos se documenta explícitamente en `docs/CASCADE.md`

## Cómo usar este archivo histórico

Los scripts aquí son **ejecutables** con los datos originales y producen los
resultados del análisis bajo el supuesto 918. Si necesitás reproducir el análisis
original, corrés los scripts desde esta carpeta apuntando a los datos originales.

El análisis vigente está en la raíz del repositorio (`slides/`, `analisis/`, `etl/`).

## Presentación generada

`slides/presentacion_principal/generar_presentacion.py` (en la raíz del repo)
genera la presentación de 37 slides bajo la nueva estructura.

La versión 918 del PPT se puede regenerar con:
`archive/legacy_918/NOTEBOOKS/generar_presentacion_33_numerada.py`
