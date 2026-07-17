# Cascada de universos — Análisis UCEN

Cada nivel representa un filtro aplicado al nivel anterior.
**Nunca se sobreescribe una fila — se agrega una nueva con fecha cuando cambia un criterio.**
Git guarda el historial completo de decisiones.

## Niveles actuales

| Nivel | Carpeta | N | Filtro aplicado | Fecha decisión |
|-------|---------|---|-----------------|----------------|
| 00 | `00_base` | pendiente | NOMINA × DOTACION, RUT único, sin filtros adicionales | 2026-07-15 |
| 01 | `01_jornada` | pendiente | `tipo_contrato_tag` = JORNADA | 2026-07-15 |
| 02 | `02_honorario` | pendiente | `tipo_contrato_tag` = HONORARIO | 2026-07-15 |
| 03 | `03_jerarquizados` | 917 | jerarquía académica válida (excluye "SIN JERARQUÍA", "NO INFORMA", vacíos) | pre-2026 |
| 04 | `04_formados_p3` | pendiente | participó en ≥1 actividad P3 — desde universo_base sin filtro jerarquía | 2026-07-15 |
| 05 | `05_aptos_p3` | pendiente | SAT docente disponible en período PRE y POST — desde formados_p3 sin filtro jerarquía | 2026-07-15 |

> **Nota:** Los N pendientes se confirman al correr `etl/00_base/etl_universo_base.py`
> (pendiente en rama `feat/universo-base`).
>
> El N=917 (nivel 03) corresponde al universo con jerarquía válida después de excluir ESPINOZA (RUT 16322128),
> persona eliminada por ambigüedad de identidad. La cifra histórica 918 era previa a esa exclusión.

## Decisiones metodológicas relevantes

### Jerarquía como campo, no como filtro
A partir de 2026-07-15, la jerarquía académica pasa a ser una **variable descriptiva**
dentro del universo base, no un criterio de exclusión. El nivel 03 (jerarquizados) existe
como subconjunto de análisis específico, pero no es el punto de partida del proyecto.

### Tipo de contrato
La variable `tipo_contrato` proviene de la hoja DOTACION del Excel maestro.
Los docentes presentes solo en NOMINA (sin match en DOTACION) quedan con `tipo_contrato = DESCONOCIDO`.

## Historial de cambios de criterio

| Fecha | Nivel afectado | Cambio | Responsable |
|-------|----------------|--------|-------------|
| 2026-07-15 | Global | Replanteamiento: universo base pasa de jerarquizados a NOMINA × DOTACION | Equipo |
