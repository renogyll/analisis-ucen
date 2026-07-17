# Cascada de universos — Análisis UCEN

Cada nivel representa un filtro aplicado al nivel anterior.
**Nunca se sobreescribe una fila — se agrega una nueva con fecha cuando cambia un criterio.**
Git guarda el historial completo de decisiones.

## Niveles actuales

| Nivel | Carpeta | N | Filtro aplicado | Fecha decisión |
|-------|---------|---|-----------------|----------------|
| 00 | `00_base` | pendiente | NOMINA × DOTACION, RUT único, sin filtros adicionales | 2026-07-15 |
| 01 | `01_jornada` | pendiente | `tipo_contrato` IN (Planta Activa, Media Jornada, Contrata, Contrata Indefinida...) | 2026-07-15 |
| 02 | `02_honorario` | pendiente | `tipo_contrato` IN (Honorario, Por Hora) | 2026-07-15 |
| 03 | `03_jerarquizados` | ≈918 | jerarquía académica válida (excluye "SIN JERARQUÍA", "NO INFORMA", vacíos) | pre-2026 |
| 04 | `04_formados_p3` | ≈357 | participó en ≥1 actividad P3 (Taller / Diplomado / Proyecto) | pre-2026 |
| 05 | `05_aptos_p3` | 197 | SAT docente disponible en período PRE y en período POST a la formación | pre-2026 |

> **Nota:** Los N de niveles 00–02 se completarán al correr `etl/00_base/etl_nomina_dotacion.py`
> con el tag de tipo_contrato incorporado (pendiente en rama `feat/universo-base`).

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
