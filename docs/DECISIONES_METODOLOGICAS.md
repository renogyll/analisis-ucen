# Decisiones Metodológicas — Análisis UCEN
**Proyecto:** Impacto del perfeccionamiento docente en el aprendizaje estudiantil  
**Contraparte:** Vicerrectoría Académica / Dirección de Desarrollo Académico  
**Última actualización:** 2026-08-03  
**Estado:** Documento vivo — actualizar al tomar nuevas decisiones

---

## Vigencia de universos — leer antes que el índice

El proyecto pasó por 3 universos de análisis en momentos distintos. Las decisiones
1–24 se escribieron durante los primeros dos; **desde 2026-07-30 el universo vigente
es `analisis.universo_base` (1.144) y su sub-universo Jornada (624, usado en P1)**.

| Universo | N | Vigencia | Período en que fue "el" universo |
|---|---:|---|---|
| 492 (`Analisis_UCEN_v2/`) | 492 | 🕰️ Histórico | Hasta ~2026-05 |
| 917 (`UNIVERSO_918/`) | 917 | 🕰️ Histórico | ~2026-05 a 2026-07-29 |
| **`analisis.universo_base`** | **1.144** | ✅ **Vigente** | Desde 2026-07-30 (ver D25) |
| **Jornada/Planta (sub-filtro de universo_base)** | **624** | ✅ **Vigente**, es el universo de P1 | Desde 2026-07-30 |

**Qué significa esto para las decisiones 1–24:**
- Las **reglas metodológicas** (cómo tratar `NO INFORMA`, el umbral de cobertura CM-1,
  la ponderación CM-2, el formato de RUT, las reglas de período baseline/resultado, etc.)
  **siguen vigentes** — son criterios de calidad de datos independientes del universo.
- Los **N y conteos específicos** atados a 492/917/545 (D3, D5, D17, D19, D20, D22–D24)
  son **históricos** — quedan como registro de cómo se llegó hasta acá, pero **no se
  deben citar como si fueran el estado actual**. Cada una de esas decisiones tiene ahora
  una nota "⚠️ HISTÓRICO" señalando su equivalente vigente cuando existe.
- D25 y D26 en adelante ya documentan el universo vigente (1.144 / Jornada 624).

---

## Índice de decisiones

| # | Tema | Estado | Universo | Vigencia |
|---|------|--------|----------|----------|
| 1 | Identificador único (RUT) | ✅ Resuelto | Ambos | ✅ Regla vigente |
| 2 | Duplicados en NOMINA | ✅ Resuelto | Ambos | 🕰️ Histórico (casos puntuales de 492/917) |
| 3 | Universos de análisis (492 y 917) | ✅ Resuelto | — | 🕰️ Histórico — ver tabla de vigencia arriba |
| 4 | Jerarquía válida — criterio de inclusión | ✅ Resuelto | Ambos | ✅ Regla vigente (ver nota en D25) |
| 5 | `tiene_perfil_completo` | ✅ Resuelto | 917 | 🕰️ Histórico |
| 6 | Formato `fecha_retiro` en DOTACION | ✅ Resuelto | Ambos | ✅ Regla vigente |
| 7 | IDs canónicos de preguntas | ✅ Resuelto | Ambos | ✅ Regla vigente |
| 8 | Cambio de texto MET_04 (2023-01) | ✅ Resuelto | Ambos | ✅ Regla vigente |
| 9 | Estructura de encabezados eval. estudiantil | ✅ Resuelto | Ambos | ✅ Regla vigente |
| 10 | Umbral de cobertura evaluaciones SAT (CM-1) | ✅ Resuelto | Ambos | ✅ Regla vigente (usada en P1 evaluación e instrumento) |
| 11 | Promedio SAT ponderado por alumnos (CM-2) | ✅ Resuelto | Ambos | ✅ Regla vigente |
| 12 | Reglas de período baseline / resultado (P3) | ✅ Resuelto | Ambos | ✅ Regla vigente (P3) |
| 13 | Granularidad de `periodo_evento` | ✅ Resuelto | Ambos | ✅ Regla vigente |
| 14 | Criterio `apto_p3` | ✅ Resuelto | Ambos | 🕰️ N histórico (197/357), regla vigente |
| 15 | Docentes con múltiples instancias de formación | ✅ Resuelto | Ambos | ✅ Regla vigente |
| 16 | Z-score SAT: metodología de estandarización | ✅ Resuelto | Ambos | ✅ Regla vigente |
| 17 | Grupo de control | ✅ Resuelto | 492 | 🕰️ Histórico |
| 18 | Columnas restituidas de evaluación de jefes | ✅ Resuelto | 492 | ✅ Regla vigente (columnas siguen existiendo) |
| 19 | Agregación SAT universo 917 para docentes solo-nómina | ⚠️ Pendiente revisión | 917 | 🕰️ Histórico |
| 20 | Sub-universo Jornada/Planta (N=545) | ✅ Resuelto | 917 | 🕰️ Histórico — hoy Jornada = 624 (ver D25/D26) |
| 21 | "NO INFORMA" como dato faltante en variables categóricas | ✅ Resuelto | Ambos | ✅ Regla vigente |
| 22 | Brecha de dotación en Jornada/Planta (60 sin dotación) | ✅ Caracterizado | 917 | 🕰️ Histórico — ver D26 para cobertura actual (624) |
| 23 | Sub-cascadas de calidad de datos — Jornada con dotación | ✅ Resuelto | 917 | 🕰️ Histórico |
| 24 | P2 desagregado para Jornada/Planta | ✅ Resuelto | 917 | 🕰️ Histórico — pendiente recalcular sobre 624 |
| 25 | Normalización de `jerarquia` — universo actual (1.144) | ✅ Resuelto | 1.144 (`universo_base`) | ✅ Vigente |
| 26 | Aprobación/reprobación de alumnos — tags + universo Jornada | ✅ Resuelto | 624 (Jornada) | ✅ Vigente |
| 27 | Grupo de dificultad de asignaturas (terciles de % aprobación histórico) | ✅ Resuelto | 624 (Jornada), cortes sobre universo completo | ✅ Vigente |

---

## 1. Identificador único de docente (RUT)

**Decisión:** Usar RUT sin dígito verificador (DV) como llave universal en todas las tablas.

**Razón:** Las fuentes transaccionales (evaluaciones estudiantiles, detalle de calificaciones) entregan el RUT sin DV. Las tablas maestras (NOMINA, DOTACION, diplomados, talleres, proyectos) lo traen con DV. Estandarizar sin DV evita joins fallidos y es la forma más simple de cruzar todas las fuentes.

**Aplicación:** Al cargar tablas maestras a la DB, stripear el DV. Al leer evaluaciones, usar el RUT tal como viene.

---

## 2. Duplicados en NOMINA

**Contexto:** NOMINA tiene 967 filas pero solo 957 RUTs únicos — 10 pares duplicados. Al ampliar el universo a 917, se identificaron 6 RUTs adicionales con doble fila (Jornada + Honorario) en la nómina, y 1 caso de persona equivocada.

**Decisión por caso:**

| Docente | RUT | Causa | Tratamiento |
|---|---|---|---|
| GONZALO ALVAREZ, JOAQUÍN GARCÍA, FERNANDA INOSTROZA, JULIO GÓMEZ (universo original) | Varios | Jornada vs Honorario | Una fila, `tipo_contrato = Jornada+Honorario` |
| ROYFEL SISO / ROYFFEL SISO | — | Error tipográfico | Normalizar nombre, una fila |
| VIVIANA ABARCA, LUIS RÍOS, RAFAEL SALFATE | — | Filas completamente idénticas | Eliminar duplicado |
| Duplicados Jornada+Honorario universo ampliado (4 nuevos) | Varios | Jornada vs Honorario | **Conservar fila Jornada, eliminar Honorario** |
| JORG ALFRED STIPPEL | 25600736 | Dos departamentos distintos | **Conservar una fila (deduplicar en ETL)** |
| RODRIGO ESPINOZA / CARLOS ESPINOZA BARDALES | 16322128-4 | Dos personas distintas con mismo RUT | **Conservar RODRIGO ESPINOZA** (jerarquizado). Carlos Espinoza Bardales (RUT real: 27711156) no es jerarquizado → no entra al universo |

**Razón para preferir Jornada sobre Honorario:** El contrato de Jornada refleja el vínculo principal e institucional del docente. El honorario es complementario. Para análisis de formación y jerarquía, la fila de Jornada es la fuente más confiable.

---

## 3. Universos de análisis paralelos

> ⚠️ **HISTÓRICO.** Los universos 492/917/545 descritos acá fueron reemplazados desde
> 2026-07-30 por `analisis.universo_base` (1.144) y su sub-universo Jornada (624).
> Ver "Vigencia de universos" al inicio del documento y D25/D26.

El análisis opera con **tres universos** que se mantienen en carpetas separadas o como sub-filtros:

| Universo | N docentes | Carpeta/Filtro | Descripción |
|---|---|---|---|
| **492** | 492 | `Analisis_UCEN_v2/` (raíz) | Docentes con perfil completo: en NOMINA **y** DOTACION, con jerarquía válida en ambas fuentes. Datos demográficos completos (edad, antigüedad, facultad). |
| **917** | 917 | `UNIVERSO_918/` | Todos los docentes jerarquizados de cualquier fuente (NOMINA o DOTACION). Amplía el universo pero 424 docentes carecen de datos demográficos (solo-nómina). |
| **Jornada/Planta** | 545 | Sub-filtro de 917 | Docentes del universo 917 con contrato de Jornada (planta), excluyendo Honorarios. Ver D20. |

**Razón de mantener múltiples universos:** El 492 permite análisis más ricos con variables como antigüedad, edad y facultad. El 917 da mayor potencia estadística y representatividad institucional. El sub-universo Jornada aísla el cuerpo de planta donde la formación docente tiene mayor impacto institucional esperado. Los resultados pueden diferir entre universos y todos tienen valor analítico.

**Nota de nomenclatura:** La carpeta se llama `UNIVERSO_918/` por el número provisional al iniciar el trabajo; el N definitivo es 917 tras deduplicación en BD.

---

## 4. Jerarquía válida — criterio de inclusión

Para ser incluido en el universo de análisis, un docente debe tener jerarquía válida en al menos una fuente.

| Fuente | Valores que se EXCLUYEN (jerarquía inválida) |
|---|---|
| NOMINA (`jerarquia`) | `"SIN JERARQUÍA"`, `"SIN JERARQUIA"`, `""` (vacío) |
| DOTACION (`jerarquia_dot`) | `"NO INFORMA"`, `"SIN JERARQUÍA"`, `"SIN JERARQUIA"`, `""` (vacío) |

**Razón:** Los docentes sin jerarquía no han completado el proceso de jerarquización UCEN y no son comparables con los jerarquizados en el análisis de impacto de formación.

**Validación:** Los 28 docentes que en el universo 492 aparecen con `SIN JERARQUÍA` en nómina también tienen `NO INFORMA` en dotación — ninguna fuente les asigna jerarquía real. El recorte es consistente entre fuentes.

---

## 5. `tiene_perfil_completo`

> ⚠️ **HISTÓRICO.** Columna del universo 917 (`docente_918.csv`). En `universo_base`
> (1.144) el equivalente conceptual es el campo `origen` (AMBOS/SOLO_NOMINA/
> SOLO_DOTACION/SOLO_FORMACION) — ver D25.

Columna booleana en `docente_918.csv` que indica si el docente tiene datos de dotación disponibles.

| Valor | Criterio | N aprox. |
|---|---|---|
| `True` | Docente aparece en `analisis.docente_ambos` (tiene datos de DOTACION: edad, antigüedad, unidad_facultad, nivel_formacion) | 493 |
| `False` | Docente proviene solo de `analisis.docente_solo_nomina` (sin datos demográficos de dotación) | 424 |

**Implicancia:** Los análisis que usan antigüedad, edad, facultad o nivel de formación solo son válidos para los 493 con `tiene_perfil_completo = True`.

---

## 6. Formato de `fecha_retiro` en DOTACION

**Problema:** La columna `F. RETIRO` usa el texto `"INDEFINIDO"` para docentes activos en lugar de NULL.

**Decisión:** Al cargar a DB, convertir `"INDEFINIDO"` a `NULL`. Guardar fecha real solo para docentes retirados. Esto permite `WHERE fecha_retiro IS NULL` para filtrar activos.

---

## 7. IDs canónicos de preguntas del instrumento

**Problema:** El instrumento de evaluación estudiantil usa IDs numéricos (ej: 4509, 4515) que pueden variar entre períodos.

**Decisión:** Asignar IDs semánticos por dimensión:

| ID canónico | Dimensión | Orden |
|---|---|---|
| APR_01, APR_02, APR_03 | Aprendizajes | 1–3 |
| MET_01, MET_02, MET_03, MET_04, MET_05 | Metodologías y Evaluación | 4–8 |
| AFO_01 … AFO_09 | Aspectos Formales | 9–17 |
| SAT_BIN | Satisfacción (binario: ¿recomendaría?) | 18 |
| SAT_NOTA | Satisfacción (nota 1–7) | 19 |

---

## 8. Cambio de texto en MET_04 (pregunta 4515)

**Hallazgo:** La pregunta en posición 7 (MET_04) cambió de redacción entre períodos:

| Período | Texto |
|---|---|
| **2023-01** | "Cuando una explicación no satisface de manera efectiva..." |
| **2023-02 en adelante** | "El profesor(a) frente a las dudas o consultas de los estudiantes, orienta y clarifica..." |

**Decisión:** Mantener ID canónico `MET_04`. Registrar ambos textos en la tabla `pregunta` con `periodos_texto_alt = "2023-01"`. Mencionar en análisis del instrumento.

---

## 9. Estructura de encabezados en archivos de evaluación estudiantil

**Estructura estándar (2023-01 a 2025-01):** 3 filas de encabezado → leer con `skiprows=2`.

**Excepción 2025-02:** Solo 2 filas de encabezado → leer con `skiprows=1`.

---

## 10. Umbral de cobertura evaluaciones SAT (CM-1)

**Decisión:** Excluir del cálculo SAT toda sección de evaluación donde `cobertura_pct < 40`.

**Razón:** Una sección donde menos del 40% de los alumnos evaluó produce un dato poco representativo. Incluirla puede distorsionar el promedio del docente en ese período, especialmente cuando tiene pocas secciones.

**Columna fuente:** `consolidados.evaluacion_periodo.cobertura_pct`

**Implementación:**
```sql
WHERE e.cobertura_pct >= 40
  AND r.pregunta_id = 'SAT_NOTA'
```

**Impacto medido (universo 917):** De 836 docentes con algún SAT, algunos pierden períodos completos al aplicar CM-1. El N final con SAT válido se reduce levemente respecto a sin filtro.

**Aplica a:** Todos los cálculos SAT en universo 492 y 917.

---

## 11. Promedio SAT ponderado por número de alumnos (CM-2)

**Decisión:** El SAT de un docente en un período es el promedio ponderado de sus secciones, usando `n_alumnos_evaluaron` como peso.

**Fórmula:**
```
SAT_docente_período = SUM(nota_promedio × n_alumnos_evaluaron) / SUM(n_alumnos_evaluaron)
                      (solo secciones con cobertura_pct ≥ 40)
```

**Razón:** Un docente puede dictar asignaturas con volúmenes de alumnos muy distintos. Sin ponderación, una sección de 5 alumnos pesa igual que una de 50, distorsionando el promedio. Ejemplo concreto: Edison Otero Bello dicta asignaturas de perfil completamente distintos con N muy variables.

**Columnas fuente:**
- `evaluacion_respuesta.nota_promedio` → nota de la sección (ya es promedio de los alumnos de esa sección)
- `evaluacion_periodo.n_alumnos_evaluaron` → peso

**Aplica a:** Todos los cálculos SAT en universo 492 y 917.

---

## 12. Reglas de período baseline / resultado (P3)

**Marco general:** Diseño cuasi-experimental pre/post para evaluar impacto de la formación.

| Tipo | Período baseline | Evento | Período resultado |
|---|---|---|---|
| DIPLOMADO (año X) | Cualquier semestre de año X−1 | Año X | Cualquier semestre de año X+1 |
| PROYECTO (año X) | Cualquier semestre de año X−1 | Año X | Cualquier semestre de año X+1 |
| TALLER 2023-02 | 2023-01 | 2023-02 | 2024-01 |
| TALLER 2024-01 | 2023-02 | 2024-01 | 2024-02 |
| TALLER 2024-02 | 2024-01 | 2024-02 | 2025-01 |

**Razón del año de separación (DIPLOMADO/PROYECTO):** No se usan evaluaciones del año de la capacitación como baseline porque el docente puede estar cursando la formación durante ese año, contaminando la medición.

**Casos fuera de rango (se conservan pero no son aptos P3):**
- Diplomado/Proyecto 2022, 2023: sin baseline (datos parten en 2023-01)
- Diplomado/Proyecto 2025: sin resultado (no hay datos de 2026)
- Talleres fuera de los períodos mapeados arriba

**Cálculo SAT para DIPLOMADO/PROYECTO (baseline y resultado a nivel anual):** Se promedian los SAT ponderados de todos los semestres disponibles en el año de baseline / año de resultado. Si solo existe un semestre, se usa ese.

---

## 13. Granularidad de `periodo_evento`

**Decisión:** `periodo_evento` (semestre) se llena **solo para TALLERES**.

Para DIPLOMADOS y PROYECTOS, `periodo_evento = NULL` — solo se usa `anio_evento`. Inventarles un semestre sería fabricar datos inexistentes.

---

## 14. Criterio `apto_p3`

**Definición:** Un docente × evento de formación es apto para el análisis de impacto (P3) si:

```
apto_p3 = tiene_sat_baseline AND tiene_sat_resultado
```

Donde `tiene_sat_X` = el docente tiene al menos una sección con SAT válido (CM-1: cobertura ≥ 40%) en el período baseline o resultado correspondiente.

**Resultado universo 917:** 197 RUTs únicos aptos de 357 con formación registrada (55%).
🕰️ *N histórico — sobre `universo_base` el número vigente es 316 aptos P3 (ver
`etl_formados_p3.py`, deck P3 actual). La regla de la fórmula sigue siendo la misma.*

**Razón de excluir sin baseline o sin resultado:** Sin ambos puntos de medición no hay diseño pre/post. Incluirlos sin SAT haría imposible calcular el cambio.

---

## 15. Docentes con múltiples instancias de formación

**Contexto:** Algunos docentes participaron en más de un evento de formación con períodos distintos (ej: TALLER 2023-02 y TALLER 2024-01 son dos filas separadas).

**Decisión:** En el output final (`p3_sat_zscore_918.csv`, `p3_sat_zscore.csv`), **se promedian** las métricas de todas las instancias apto_p3 del docente en una sola fila.

**Columnas de control:** `n_instancias` indica cuántos eventos se promediaron; `tipos_formacion` lista los tipos involucrados (ej: `"DIPLOMADO | TALLER"`).

**Razón:** Permite una fila por docente para visualizaciones y estadísticas descriptivas simples. La granularidad evento × docente se conserva en `p3_918.csv` para análisis más finos.

**Pendiente:** Evaluar si conviene analizar separadamente docentes con instancias múltiples vs. única instancia.

---

## 16. Z-score SAT: metodología de estandarización

**Decisión:** El z-score posiciona a cada docente dentro de su facultad y período.

**Fórmula:**
```
z_docente_período = (SAT_docente_período − μ_facultad_período) / σ_facultad_período
```

**Población de referencia para μ y σ:** Todos los docentes del universo correspondiente (917 o 492) que tienen SAT válido en esa facultad × período, aplicando CM-1 y CM-2.

**Unidades pequeñas (n < 30 RUTs en el universo 917 / n < 50 en 492):** Se colapsan en la categoría `"Otras"` para garantizar que μ y σ estén basados en muestras suficientes.

| Universo | Umbral colapso | Unidades colapsadas |
|---|---|---|
| 492 | < 50 RUTs | DIRECCION DE ASEGURAMIENTO DE LA CALIDAD, JUNTA DIRECTIVA, SEDE LA SERENA, VICERRECTORIA ACADEMICA |
| 917 | < 30 RUTs | DIRECCION DE ASEGURAMIENTO DE LA CALIDAD, JUNTA DIRECTIVA, SEDE LA SERENA, VICERRECTORIA ACADEMICA |

**Fallback:** Si no hay estadísticas para una combinación facultad × período, se usa la media y desviación estándar global del universo.

**Interpretación:**
- z = 0 → el docente está en el promedio de su facultad ese semestre
- z = +1 → está 1 desviación estándar por sobre sus colegas
- z = −1 → está 1 desviación estándar por debajo

**Diferencia con SAT crudo:** El z-score controla el contexto. Si toda la facultad mejoró ese semestre por razones ajenas a la formación, el z-score lo descuenta. El delta_z es por tanto más limpio como indicador de efecto relativo.

---

## 17. Grupo de control (universo 492)

> ⚠️ **HISTÓRICO.** Ver `analisis.p3_grupo_tratamiento`/`etl_formados_p3.py` para el
> grupo de control vigente sobre `universo_base`, ya usado en el deck P3 actual.

**Definición:** Docentes del grupo AMBOS (492 con perfil completo) que:
1. No participaron en ningún diplomado, taller ni proyecto en 2022–2025
2. Tienen evaluación estudiantil en al menos un período

**Resultado:** 219 docentes  
**Archivo:** `PROCESADO/P3_docentes_perfil_completo_sinformacion.csv`

**Estado universo 917:** Pendiente de definir grupo de control equivalente para los 917. El grupo potencial son los 560 sin formación registrada, de los cuales una parte tiene SAT válido.

---

## 18. Columnas restituidas de evaluación de jefes

Las siguientes columnas fueron inicialmente descartadas y luego restituidas por decisión explícita:

| Columna | Nombre en DB | Razón |
|---|---|---|
| `OBSERVACIÓN` | `observacion_jefe` | Texto cualitativo del director |
| `COD_OBSERVACION` | `cod_observacion` | Código de la observación cualitativa |
| `PORCENTAJE CONCEPTO` | `porcentaje_concepto` | Distribución de conceptos |

---

## 19. SAT de docentes solo-nómina (universo 917) — PENDIENTE REVISIÓN

> ⚠️ **HISTÓRICO.** Quedó sin resolver en el universo 917 y no se retomó tras la
> migración a `universo_base` — la pregunta sigue siendo válida (docentes `SOLO_NOMINA`
> sin `unidad_facultad` para el z-score) pero no se ha revisado sobre el universo actual.

**Contexto:** 424 docentes del universo 917 no tienen datos de dotación (`tiene_perfil_completo = False`). Sin embargo, 382 de ellos (90%) tienen SAT válido.

**Pregunta abierta:** ¿Son comparables los SAT de docentes solo-nómina con los de perfil completo para el análisis de impacto? Los primeros no tienen dato de `unidad_facultad`, lo que afecta el z-score (se les asigna "Otras" como facultad de referencia).

**Estado:** Los 68 docentes solo-nómina aptos P3 están incluidos en el análisis actual con z-score calculado usando la categoría "Otras" como referencia. Revisar si esto introduce sesgo antes de presentar resultados finales.

---

---

## 20. Sub-universo Jornada/Planta (N=545)

> ⚠️ **HISTÓRICO.** El sub-universo Jornada vigente hoy es 624 (filtro
> `tipo_contrato_tag='JORNADA'` sobre `universo_base`) — es el universo que usa todo
> el bloque de gráficos de P1 (`caracterizacion/`, `aprobacion_reprobacion*`). El
> razonamiento de por qué aislar Jornada sigue siendo el mismo, solo cambió el N.

**Decisión:** Crear un sub-universo de análisis restringido a los docentes del universo 917 con contrato de Jornada (planta), excluyendo Honorarios.

**Criterio de filtro:**
```python
doc["tipo_contrato"].str.strip().str.lower().str.startswith("jornada")
```

**Resultado:**

| Grupo | N |
|---|---|
| Universo 917 total | 917 |
| Jornada/Planta | 545 |
| — con DOTACION | 485 |
| — solo NOMINA (sin dotación) | 60 |
| Honorarios (excluidos del sub-universo) | 372 |

**Razón:** Los docentes de Jornada tienen vínculo estable con la institución, perfil de carrera más definido y mayor relevancia de la formación docente para efectos del PEI y acreditación CNA. El análisis desagregado permite detectar patrones específicos del cuerpo de planta que quedarían diluidos en el universo total (donde los 372 Honorarios tienen perfiles muy distintos de acceso a perfeccionamiento y continuidad).

**Nota:** A diferencia del universo 917 donde 424 no tienen dotación (mayoritariamente Honorarios), en Jornada la brecha es solo de 60 — mucho más manejable y potencialmente recuperable con una solicitud a la contraparte.

---

## 21. "NO INFORMA" como equivalente a NULL en variables categóricas

**Decisión:** En las variables categóricas provenientes de la hoja DOTACION, los valores `"NO INFORMA"` y `"NO INFORMA "` (con espacio en blanco al final) se tratan como dato no disponible, equivalente a NULL.

**Variables afectadas:** `jerarquia_dot`, `nivel_formacion`, `nombre_grado`

**Criterio Python:**
```python
# Valor válido (no nulo y no "NO INFORMA"):
ser.notna() & ~ser.isin({"NO INFORMA", "NO INFORMA "})
```

**Razón:** `"NO INFORMA"` es la convención que usa la fuente de datos para registrar ausencia de clasificación o información no disponible al momento de la extracción. No es un nivel real de jerarquía ni de formación. Incluirlo como valor categórico contaminaría las distribuciones y los análisis de completitud.

**Impacto cuantificado (Jornada con dotación, N=485):**

| Variable | Registros con "NO INFORMA" |
|---|---|
| `jerarquia_dot` | 11 docentes |
| `nivel_formacion` | 5 docentes |
| `nombre_grado` | 0 docentes |

---

## 22. Brecha de dotación en Jornada/Planta

> ⚠️ **HISTÓRICO** (N=545). Sobre el Jornada vigente (624), la brecha equivalente y
> la cobertura por variable están cuantificadas en D26 (tabla de cobertura por sexo/
> jerarquía/edad) y en cada script de `caracterizacion/` (`N_SIN_DATOS` en el subtítulo).

**Contexto:** 60 de los 545 docentes Jornada aparecen en NOMINA pero no tienen registro en DOTACION.

**Variables ausentes para estos 60:**

| Variable | Disponible |
|---|---|
| Sexo | ✅ (NOMINA) |
| Jerarquía académica | ✅ (NOMINA) |
| Tipo contrato (Jornada) | ✅ (NOMINA) |
| Función principal académica | ✅ (NOMINA) |
| Fecha jerarquización (~95%) | ✅ (NOMINA) |
| Edad / fecha nacimiento | ❌ |
| Antigüedad / fecha ingreso | ❌ |
| Unidad / Facultad detallada | ❌ |
| Nivel de formación | ❌ |
| Nombre grado / título | ❌ |
| Institución y país grado | ❌ |
| Carga horaria semanal | ❌ |
| Cargo específico | ❌ |

**Posible causa:** Nuevos ingresos 2026 aún no procesados en DOTACION, o discrepancia de RUT entre ambas fuentes que impide el cruce.

**Decisión sobre estos 60:** Se mantienen en el universo general (N=545) pero quedan excluidos de análisis que requieren variables de dotación (P1 completo, z-score por facultad). Se documenta como brecha recuperable.

**Solicitud pendiente a contraparte:** Verificar los 60 RUTs en DOTACION o enviar complemento con los datos faltantes. Esto elevaría la cobertura de análisis P1 de 485 a 545 en el sub-universo Jornada.

---

## 23. Sub-cascadas de calidad de datos — Jornada con dotación

> ⚠️ **HISTÓRICO** (base 545/485). No se ha rehecho esta cascada completa sobre el
> Jornada vigente (624) — lo más cercano hoy es la cobertura por variable documentada
> en D26 y en los subtítulos de cada gráfico de `caracterizacion/`.

**Contexto:** Dentro de los 485 Jornada con dotación, no todos tienen cada variable completa. La cascada de calidad muestra las pérdidas sucesivas al aplicar cada filtro de completitud.

**Cascada:**

| Nivel | N | Baja | Causa |
|---|---|---|---|
| Jornada con dotación | 485 | — | Punto de partida |
| Con jerarquía válida en dot. | 474 | −11 | `"NO INFORMA"` en `jerarquia_dot` (ver D21) |
| Con nivel formación válido | 469 | −5 | `"NO INFORMA"` en `nivel_formacion` (ver D21) |
| Con grado clasificado | 469 | 0 | Todos tienen `nombre_grado` informado |
| Con fecha jerarquización | 447 | −22 | NULL en `FECHA_JERARQUIZACION` (estimado desde NOMINA) |

**Nota sobre fecha jerarquización:** La hoja NOMINA del archivo CONSOLIDADO DOCENTES 3-05-2026.xlsx tiene aproximadamente 45 nulos en 967 filas para esta columna. Proporcionalmente para Jornada (545 de 917): ≈22 sin dato. Este valor es una estimación; no se cuenta directamente desde DOTACION porque la columna equivalente no está disponible en esa fuente.

**Dato relevante:** El 100% de los 545 Jornada tiene jerarquía informada en NOMINA (ninguno con `"SIN JERARQUÍA"`). Esto contrasta con el universo 917 donde existe un número de docentes sin jerarquía válida. El salto principal de la cascada Jornada no es la jerarquía sino la brecha NOMINA→DOTACION (545→485, ver D22).

**Habilitaciones analíticas por nivel:**

| N disponible | Análisis habilitado |
|---|---|
| 485 | Edad × Jerarquía; Sexo; Facultad; Antigüedad; Carga |
| 474 | Jerarquía clasificada × Nivel formación |
| 469 | Nivel formación × Institución × País; GRADOREC |
| 447 | Años hasta jerarquización (trayectoria académica) |

---

## 24. P2 desagregado para Jornada/Planta

> ⚠️ **HISTÓRICO** (base 545). Pendiente recalcular sobre el Jornada vigente (624)
> cuando se retome P2 — ver `products/p2_formacion/`.

**Decisión:** El análisis de participación en perfeccionamiento (Producto 2) se replica para el sub-universo Jornada, con los mismos criterios de fuente y conteo que el universo 917, pero filtrado a los 545 docentes de planta.

**Resultados:**

| Indicador | Valor |
|---|---|
| Universo base | 545 docentes Jornada |
| Con formación registrada | 246 (45.1%) |
| Sin formación registrada | 299 (54.9%) |
| Total eventos de formación | 416 |
| — Talleres | 246 docentes |
| — Diplomados | 133 docentes |
| — Proyectos de investigación | 37 docentes |

**Fuentes de datos:**

| Tipo | Hojas consultadas |
|---|---|
| Talleres | TALLERES 2023_2, TALLERES 2024_1, TALLERES 2024_2 |
| Diplomados | DIPLOMADO 2022, DIPLOMADO 2023, DIPLOMADO 2024, DIPLOMADO 2025 |
| Proyectos | PROYECTOS DE INVESTIGACION |

Todas las hojas provienen del archivo `CONSOLIDADO DOCENTES 3-05-2026.xlsx`.

**Nota:** Los números 246, 133, 37 representan docentes únicos por tipo, no eventos. Un mismo docente puede aparecer en múltiples hojas (ej: TALLER 2023_2 y TALLER 2024_1); en ese caso se cuenta una vez por tipo. El total de 416 corresponde a iniciativas/eventos, donde un docente puede contribuir a más de uno.

**Razón del análisis desagregado:** La tasa de participación en perfeccionamiento del 45.1% en Jornada vs. el universo total es un indicador de política institucional relevante. Permite evaluar si el cuerpo de planta accede proporcionalmente a las iniciativas disponibles y si existen brechas por facultad, jerarquía o antigüedad.

---

## 25. Normalización de `jerarquia` — universo actual (`analisis.universo_base`, N=1.144)

**Contexto:** Este universo (1.144, vigente desde la migración P1–P4) reemplaza a los universos 492/917 documentados en D3. La columna `jerarquia` se arma en `shared/etl/00_base/etl_universo_base.py` a partir de 4 fuentes: NOMINA, DOTACION, `CERTIFICACION OFERTA FORMATIVA 2025.xlsx` (Talleres) y `CONSOLIDADO DOCENTES...PROYECTOS DE INVESTIGACION.csv`. Las 2 últimas (origen `SOLO_FORMACION`, 160 docentes que no están ni en NOMINA ni en DOTACION) traían el texto de "Jerarquía" escrito con un formato distinto al de NOMINA/DOTACION — mayúscula/minúscula libre, formas cortas ("Instructor/a") en vez del texto canónico ("INSTRUCTOR DOCENTE"), tildes inconsistentes — lo que producía 17 valores distintos en la columna en vez de 8 + "sin jerarquía".

**Decisión:** Normalizar en el ETL fuente (no en cada script consumidor) mapeando toda variante corta/desacentuada a su forma canónica, y asumir **DOCENTE** (no REGULAR) para las formas cortas ambiguas (`"Asistente"`, `"Instructor/a"`, `"Asociado/a"`, `"Titular"`, `"Asistente Docente"`) — decisión explícita del usuario vía consulta directa, ya que esas 4 fuentes de Talleres/Proyectos no traen el dato de escalafón (Docente vs. Regular) que sí distingue NOMINA/DOTACION.

**Mapeo completo (17 valores originales → 9 categorías + NULL real):**

| Valor original | N | → | Categoría final |
|---|---:|---|---|
| `INSTRUCTOR DOCENTE` | 343 | → | INSTRUCTOR DOCENTE *(ya venía bien, NOMINA/DOTACION)* |
| `Instructor/a` | 7 | → | INSTRUCTOR DOCENTE *(forma corta, SOLO_FORMACION → asumido Docente)* |
| `INSTRUCTOR REGULAR` | 14 | → | INSTRUCTOR REGULAR *(ya venía bien)* |
| `ASISTENTE DOCENTE` | 262 | → | ASISTENTE DOCENTE *(ya venía bien)* |
| `Asistente` | 10 | → | ASISTENTE DOCENTE *(forma corta, SOLO_FORMACION → asumido Docente)* |
| `Asistente Docente` | 1 | → | ASISTENTE DOCENTE *(mismo dato, solo mayúscula distinta)* |
| `ASISTENTE REGULAR` | 38 | → | ASISTENTE REGULAR *(ya venía bien)* |
| `ASOCIADO DOCENTE` | 143 | → | ASOCIADO DOCENTE *(ya venía bien)* |
| `Asociado/a` | 4 | → | ASOCIADO DOCENTE *(forma corta, SOLO_FORMACION → asumido Docente)* |
| `ASOCIADO REGULAR` | 39 | → | ASOCIADO REGULAR *(ya venía bien)* |
| `TITULAR DOCENTE` | 56 | → | TITULAR DOCENTE *(ya venía bien)* |
| `Titular` | 2 | → | TITULAR DOCENTE *(forma corta, SOLO_FORMACION → asumido Docente)* |
| `TITULAR REGULAR` | 21 | → | TITULAR REGULAR *(ya venía bien)* |
| `Sin Jerarquía` | 133 | → | SIN JERARQUÍA *(mayúscula distinta)* |
| `SIN JERARQUÍA` | 41 | → | SIN JERARQUÍA *(ya venía bien)* |
| `Sin jerarquía` | 3 | → | SIN JERARQUÍA *(mayúscula distinta)* |
| *(vacío real / NULL)* | 27 | → | *(vacío real, sin tocar)* |

**Resultado verificado (9 categorías finales + NULL, suma exacta a 1.144):**

| Categoría final | N |
|---|---:|
| INSTRUCTOR DOCENTE | 350 |
| ASISTENTE DOCENTE | 273 |
| SIN JERARQUÍA | 177 |
| ASOCIADO DOCENTE | 147 |
| TITULAR DOCENTE | 58 |
| ASOCIADO REGULAR | 39 |
| ASISTENTE REGULAR | 38 |
| *(NULL real)* | 27 |
| TITULAR REGULAR | 21 |
| INSTRUCTOR REGULAR | 14 |

**Implementación:** función `normalizar_jerarquia()` en `shared/etl/00_base/etl_universo_base.py` — usa `unicodedata.normalize("NFKD", ...)` para comparar sin depender de la codificación de tildes, un diccionario `_JERARQUIA_CORTAS` para las 5 formas cortas, y detecta "sin jerarquía" en cualquier variante de mayúscula/tilde. Se aplica una sola vez, en el punto de entrada de los datos — todos los scripts derivados (`etl_jornada.py`, `etl_honorario.py`, `etl_jerarquizados.py`, y los CSV de `data/cascade/`) heredan el valor ya limpio, sin normalizar cada uno por su cuenta.

**Nota para D4 (jerarquía válida — criterio de inclusión, universos legacy 492/917):** el criterio de exclusión de esa decisión sigue vigente conceptualmente para el universo 1.144 — `SIN JERARQUÍA` (177 aquí) y NULL (27) se tratan como "sin jerarquía válida" en cualquier análisis que la use como variable de agrupación (ej. `edad_jerarquia`).

---

## 26. Aprobación/reprobación de alumnos — tags de perfil docente + universo Jornada

**Contexto:** La contraparte pidió reportar % de aprobación/reprobación de alumnos. La
tabla fuente (`consolidados.calificacion_alumno`, 333.067 filas) trae `rut_docente`
directo (contrario a lo que parecía en una vista recortada de DBeaver) pero la columna
`calificacion` es un código categórico (B, SU, MB, SO, I, MM, M, A, NP, R, P, SC, SD),
no un booleano aprobado/reprobado.

**Decisión 1 — usar `consolidados.catalogo_calificacion` como fuente de verdad del
mapeo aprobado/reprobado**, en vez de hardcodear la lista de códigos en cada script:

| Aprueba | Códigos |
|---|---|
| `True` | SO, MB, B, SU, A |
| `False` | I, MM, M, R |
| `NULL` (no evaluable, estado administrativo) | NP, P, SC, SD |

**Decisión 2 — enriquecer `intel.rendimiento_academico_alumnos` con tags de perfil
docente en vez de generar un CSV aparte.** Se extendió el `LEFT JOIN` contra
`analisis.universo_base` que ya traía `tipo_contrato_tag` (pendiente de ejecutar desde
Fase 1) para sumar `sexo`, `tramo_edad`, `edad_anios`, `jerarquia`, más un segundo
`LEFT JOIN` contra `catalogo_calificacion` para `aprueba`. Permite filtrar/agrupar
directo en SQL (`WHERE tipo_contrato_tag='JORNADA'`, `GROUP BY sexo`, etc.) sin repetir
el join a mano. **Se descartó la alternativa de un CSV "más adaptado"**: mismo patrón
de riesgo que `ped-001 jerarquizados.csv` / `intel.pre_post_sat` / `p3_grupo_tratamiento`
— snapshots congelados que se desalinean de la fuente viva sin que nadie lo note.
Ejecutado 2026-08-01: se recreó la tabla (330.578 filas, 1.810 docentes) y se borró la
tabla huérfana `intel.notas_docente` (nombre anterior, sin estos tags).

**Decisión 3 — acotar todo el análisis de aprobación/reprobación a Jornada (624)**,
igual que el resto de P1. Motivo: `tramo_edad`/`edad_anios` dependen de DOTACION, y la
brecha de cobertura es mucho mayor en Honorario que en Jornada (mismo patrón que D22),
además de ser el universo que ya usan el resto de los gráficos de este bloque.

**Cobertura verificada (Jornada, N=624 — cuántos tienen al menos una calificación
registrada en `intel.rendimiento_academico_alumnos`, no filas sino docentes únicos):**

| Total Jornada | Con calificaciones | Cobertura |
|---:|---:|---:|
| 624 | 515 | 82.5% |

Desglose por sexo, jerarquía y tramo de edad — usar estos N° en los subtítulos de los
gráficos de aprobación/reprobación (evitar volver a calcularlo a mano cada vez):

| Sexo | N° Jornada | N° con calificaciones | Cobertura |
|---|---:|---:|---:|
| MUJER | 332 | 274 | 82.5% |
| HOMBRE | 271 | 235 | 86.7% |
| *(sin dato)* | 21 | 6 | 28.6% |

| Jerarquía | N° Jornada | N° con calificaciones | Cobertura |
|---|---:|---:|---:|
| INSTRUCTOR DOCENTE | 168 | 145 | 86.3% |
| ASISTENTE DOCENTE | 150 | 137 | 91.3% |
| ASOCIADO DOCENTE | 113 | 105 | 92.9% |
| SIN JERARQUÍA | 45 | 16 | 35.6% |
| TITULAR DOCENTE | 37 | 30 | 81.1% |
| ASOCIADO REGULAR | 35 | 32 | 91.4% |
| ASISTENTE REGULAR | 27 | 24 | 88.9% |
| *(sin dato)* | 21 | 6 | 28.6% |
| TITULAR REGULAR | 21 | 16 | 76.2% |
| INSTRUCTOR REGULAR | 7 | 4 | 57.1% |

| Tramo de edad | N° Jornada | N° con calificaciones | Cobertura |
|---|---:|---:|---:|
| 40-44 | 105 | 91 | 86.7% |
| *(sin dato)* | 90 | 55 | 61.1% |
| 45-49 | 87 | 76 | 87.4% |
| 35-39 | 85 | 75 | 88.2% |
| 50-54 | 69 | 59 | 85.5% |
| 55-59 | 47 | 43 | 91.5% |
| 30-34 | 44 | 38 | 86.4% |
| 60-64 | 33 | 31 | 93.9% |
| 70+ | 30 | 19 | 63.3% |
| 65-69 | 21 | 18 | 85.7% |
| <30 | 13 | 10 | 76.9% |

**% de aprobación de referencia** (sobre filas evaluables, no sobre docentes —
ver Decisión 1 para qué cuenta como evaluable): Jornada 88.5% vs Honorario 87.4%;
Mujeres 90.4% vs Hombres 85.7% (calculado sobre el universo completo antes del recorte
a Jornada de la Decisión 3; recalcular acotado a Jornada al construir cada gráfico).

---

## 27. Grupo de dificultad de asignaturas (terciles de % aprobación histórico)

**Contexto:** La contraparte pidió una forma de aislar el efecto de la dificultad de
la asignatura sobre el % de aprobación, para no leer "este docente reprueba mucho"
cuando en realidad dicta un curso intrínsecamente más exigente para todo el mundo.
Se descartó por arbitraria una clasificación cualitativa/manual de dificultad.

**Decisión — dificultad empírica por tercil de aprobación histórica, no z-score:**
Para cada `cod_asignatura` se calcula su % de aprobación agregado histórico
(**todas** las calificaciones de esa asignatura, todos los docentes — Jornada y
Honorario — y todos los períodos 2023-2025 juntos), y se ordenan las asignaturas en
3 grupos de igual tamaño (terciles):

| Grupo | Rango de % aprobación institucional | N° asignaturas | % aprobación medio del grupo |
|---|---|---:|---:|
| Baja | 0.0% – 90.9% | 858 | 79.2% |
| Media | 91.0% – 97.8% | 836 | 94.9% |
| Alta | 97.8% – 100.0% | 842 | 99.6% |

Se evaluó usar un z-score por asignatura (mismo espíritu que el z-score SAT de P3,
D16: comparar a cada docente contra el promedio de quienes dictan lo mismo) pero se
descartó: **957 de 1.709 asignaturas (56%) las dicta un solo docente** — un z-score
necesita pares de comparación y no los hay para más de la mitad de los casos. Los
terciles sí funcionan con un solo docente por asignatura porque solo requieren
volumen de calificaciones históricas (mediana 58 calificaciones/asignatura), no
múltiples docentes.

**Limitación reconocida:** para esas 957 asignaturas de un solo docente, el "% histórico
de la asignatura" es literalmente el % de ese mismo docente — el tercil no es una
medida externa/independiente en esos casos, es circular. Se documenta pero no se
corrige (no hay con qué comparar); al interpretar resultados por grupo, tener
presente que ~56% de las asignaturas no tienen esa validación cruzada.

**Implementación:** el % histórico se calcula sobre `intel.rendimiento_academico_alumnos`
completo (no solo Jornada — la dificultad es propiedad del curso, no del tipo de
contrato de quien lo dicta), vía `pd.qcut(..., 3, labels=["Baja","Media","Alta"])`
en `etl_intel_rendimiento_academico_alumnos.py`. El resultado (`grupo_dificultad`,
más `pct_aprob_asignatura` de respaldo) se agrega como columna nueva a la tabla —
cada fila queda tageada con el grupo de su propia asignatura — para poder filtrar/
agrupar por dificultad igual que por sexo/jerarquía/antigüedad, sin recalcular a mano.

**Cobertura y resultado sobre Jornada (624), una vez tageada la tabla completa:**

| Grupo | N° asignaturas (Jornada) | N° calificaciones | N° docentes | % aprobación (Jornada) |
|---|---:|---:|---:|---:|
| Baja | 596 | 53.666 | 335 | 76.5% |
| Media | 589 | 52.010 | 401 | 94.9% |
| Alta | 524 | 28.964 | 352 | 99.1% |

La brecha de % aprobación entre grupos (76.5% → 99.1%) confirma que la dificultad de
la asignatura explica una parte real y grande de la variación — controlar por esto
antes de comparar docentes entre sí es metodológicamente necesario, no cosmético.

**Prueba t sobre un atributo fijo del docente (ej. antigüedad) — "grupo predominante":**
la convención general de este documento para pruebas t es 1 valor *por docente*, para
evitar pseudo-repetición (ver "Convención de las pruebas t" más abajo). Esa convención
asume que la métrica varía por instancia (ej. `aprueba`, que cambia calificación a
calificación) y por eso se promedia por docente. La antigüedad **no** varía por
instancia — es un atributo fijo de la persona — así que promediarla por docente y
grupo no tiene sentido (un docente que dicta en 2 grupos tendría el mismo valor en
ambos, inflando artificialmente ambas muestras con el mismo dato). Para este caso se
usa en cambio el **grupo de dificultad predominante**: el grupo (Baja/Media/Alta)
donde el docente tiene más instancias docente×asignatura×período. Cada docente aporta
así un solo valor a una sola muestra, preservando la independencia que el t-test
necesita.

Resultado (Jornada, `caracterizacion/antiguedad_dificultad/`, prueba t Baja
predominante vs Media+Alta predominante): Baja N°=196 docentes, media 7.0 años;
Media+Alta N°=264 docentes, media 5.8 años; t=2.09, **p=0.0375 — significativa al 5%**.
Con el criterio de instancia-ponderada del gráfico descriptivo (sin esta corrección)
los promedios habían dado 8.2 vs 6.9 años — la corrección de unidad de análisis achica
la brecha pero la significancia se mantiene.

**Mismo criterio aplicado a edad, sexo y jerarquía (2026-08-03):** para variables
categóricas binarias (sexo, escalafón) se codifica 0/1 y se aplica el mismo t-test
de Welch sobre "grupo predominante" por docente — matemáticamente equivalente a una
prueba de diferencia de proporciones, pero reusa el mismo código y la misma
convención que el resto del documento.

| Variable | Carpeta | Baja (predominante) | Media+Alta (predominante) | t | p | Resultado |
|---|---|---|---|---:|---:|---|
| Edad | `edad_dificultad/` | 49.0 años (N°=196) | 46.8 años (N°=264) | 2.07 | 0.0387 | Significativa |
| Sexo (% Mujer) | `sexo_dificultad/` | 43.8% (N°=217) | 61.3% (N°=292) | -3.96 | 0.0001 | Muy significativa |
| Escalafón (% Regular) | `jerarquia_dificultad/` | 18.9% (N°=212) | 12.8% (N°=281) | 1.81 | 0.0716 | No significativa |

El hallazgo de sexo es el más fuerte de las 4 variables probadas contra dificultad
(antigüedad, edad, sexo, escalafón): los hombres están claramente sobrerrepresentados
en las asignaturas de baja aprobación histórica. Jerarquía/escalafón es la única de
las 4 que no alcanza significancia al 5% (p=0.0716, borderline) — a diferencia de
edad/antigüedad/sexo, que si la alcanzan.

---

## Catálogo de visualizaciones P1 confirmadas

De aquí en adelante, **cada visualización de P1 que se dé por aprobada y se
commitee** se registra acá con su fuente y filtros — para no tener que releer el
script cada vez que alguien pregunte "¿de dónde sale este número?". Todas comparten
el universo Jornada (624, `tipo_contrato_tag='JORNADA'` sobre `universo_base`) salvo
que se indique lo contrario.

| # | Carpeta (`products/p1_planta/caracterizacion/`) | Fuente | Filtros aplicados | Estado |
|---|---|---|---|---|
| 1 | `edad_sexo/` | `data/cascade/01_jornada/docentes_jornada.csv` | `sexo`+`tramo_edad` no nulos (N=513/624); tramos 65-69 y 70+ fusionados en "65+" | ✅ Aprobado |
| 2 | `edad_jerarquia/` | mismo CSV | `jerarquia`+`edad_anios` no nulos (N=485/624); excluye SIN JERARQUÍA/NULL; 8 categorías D25, ordenadas por edad desc., N<15 marcado con textura | ✅ Aprobado |
| 3 | `grado_academico_sexo/` | mismo CSV | `nivel_formacion`+`sexo` no nulos (N=478/624); excluye "NO INFORMA" (D21); Técnico fusionado con Profesional (N°=2) | ✅ Aprobado |
| 4 | `evaluacion_apr/` | `consolidados.evaluacion_respuesta` JOIN `evaluacion_periodo` | CM-1 (`cobertura_pct≥40`, D10) + CM-2 (ponderado por `n_alumnos_evaluaron`, D11); `rut_docente` en Jornada; descarta "indiferente"; APR_01-03 × 6 semestres 2023-01→2025-02 | ✅ Aprobado |
| 5 | `evaluacion_met/` | mismo JOIN | Igual que APR; MET_01-05, repartidas 2+3 en 2 diapositivas/pptx | ✅ Aprobado |
| 6 | `evaluacion_afo/` | mismo JOIN | Igual que APR; AFO_01-09, repartidas 3+3+3 en 3 diapositivas/pptx | ✅ Aprobado |
| 7 | `aprobacion_reprobacion/` | `intel.rendimiento_academico_alumnos` (D26) | `tipo_contrato_tag='JORNADA'` AND `aprueba IS NOT NULL`; N°=134.640 calificaciones, 515 docentes (82.5% cobertura) | ✅ Aprobado |
| 8 | `aprobacion_reprobacion_sexo/` | misma tabla | Igual + `GROUP BY sexo`. Prueba t de Welch por docente (Mujer 91.1% vs Hombre 87.7%): t=3.18, **p=0.0016 — significativa** | ✅ Aprobado (con prueba t) |
| 9 | `aprobacion_reprobacion_jerarquia/` | misma tabla | Igual + escalafón **Docente vs Regular** (colapsado desde las 8 categorías D25, no el cruce completo). Prueba t de Welch por docente (Docente 90.5% vs Regular 84.3%): t=3.47, **p=0.0008 — significativa** | ✅ Aprobado (con prueba t) |
| 10 | `aprobacion_reprobacion_antiguedad_4tramos/` | misma tabla + `tramo_antiguedad` (D26, agregado 2026-08-02) | `tramo_antiguedad` regrupado a 0-4 / 5-9 / 10-14 / 15+; excluye sin dato (55/624). Prueba t probada (15+ vs resto, por docente): p=0.157 — **no significativa, diapositiva descartada** | ✅ Aprobado (sin prueba t) |
| 11 | `aprobacion_reprobacion_antiguedad_3tramos/` | misma tabla | `tramo_antiguedad` regrupado a 0-4 / 5-9 / 10+. Prueba t probada (10+ vs resto, por docente): p=0.552 — **no significativa, diapositiva descartada** | ✅ Aprobado (sin prueba t) |
| 12 | `evolucion_aprobacion_sexo/` | misma tabla | `GROUP BY LEFT(periodo,4)` (año) × `sexo`; 2 barras (Hombre/Mujer) × 3 años (2023-2025), sin split aprobación/reprobación (solo tasa de aprobación) | ⏳ Generado, pendiente confirmación |
| 13 | `dificultad_composicion/` | misma tabla + `grupo_dificultad` (D27, agregado 2026-08-03) | Sin gráfico — 3 cajas de texto (Baja/Media/Alta): rango institucional + N° asignaturas/calificaciones/docentes/% aprobación en Jornada por grupo | ✅ Aprobado |
| 14 | `antiguedad_dificultad/` | misma tabla | Antigüedad promedio por `grupo_dificultad` (ponderado por instancia). Prueba t con "grupo predominante" por docente (Baja 7.0 años vs Media+Alta 5.8 años): t=2.09, **p=0.0375 — significativa** | ✅ Aprobado (con prueba t) |
| 15 | `edad_dificultad/` | misma tabla | Igual patrón que antiguedad_dificultad. Edad promedio por `grupo_dificultad`. Prueba t "grupo predominante" (Baja 49.0 años vs Media+Alta 46.8 años): t=2.07, **p=0.0387 — significativa** | ⏳ Generado, pendiente confirmación |
| 16 | `sexo_dificultad/` | misma tabla | % de docentes mujeres por `grupo_dificultad`. Prueba t "grupo predominante", sexo codificado Mujer=1/Hombre=0 (Baja 43.8% vs Media+Alta 61.3%): t=-3.96, **p=0.0001 — muy significativa** | ⏳ Generado, pendiente confirmación |
| 17 | `jerarquia_dificultad/` | misma tabla | % de docentes escalafón Regular por `grupo_dificultad` (colapso Docente/Regular, no las 8 categorías D25 — mismo criterio que aprobacion_reprobacion_jerarquia/). Prueba t "grupo predominante" (Baja 18.9% vs Media+Alta 12.8%): t=1.81, **p=0.0716 — no significativa** | ❌ Descartada del consolidado (no significativa) — pptx suelto y script siguen existiendo |

**Convención de las pruebas t (aplica a todas las de esta tabla):** unidad de análisis
= % de aprobación promedio *por docente* (no por calificación individual), para
evitar pseudo-repetición — un docente con 500 notas no debe pesar 500 veces más que
uno con 5. Siempre Welch (`equal_var=False`), sin asumir varianzas iguales entre
grupos. Diapositivas de prueba t no significativa (p≥0.05) se descartan a pedido de
la contraparte — el criterio y los N° quedan igual documentados acá aunque la
diapositiva no exista en el pptx final. **Excepción — atributos fijos del docente**
(ej. antigüedad, edad): no se promedia por docente×grupo, se usa el "grupo
predominante" del docente (ver detalle en D27) para que cada docente aporte un solo
valor a una sola muestra.

---

## Registro de cambios

| Fecha | Cambio |
|---|---|
| 2026-05-09 | Versión inicial (decisiones 1–13, varios pendientes) |
| 2026-05-21 | Actualización completa: resolución CM-1 y CM-2, universo 917, duplicados resueltos, z-score, apto_p3, múltiples instancias |
| 2026-07-11 | Agregadas D20–D24: sub-universo Jornada/Planta, tratamiento "NO INFORMA", brecha de dotación, sub-cascadas calidad datos, P2 desagregado. Actualizado D3 con tercer universo. |
| 2026-07-31 | Agregada D25: normalización de `jerarquia` (17→9 categorías) en el universo actual (`analisis.universo_base`, N=1.144), con mapeo completo valor-a-valor y decisión de asumir "Docente" para formas cortas de origen `SOLO_FORMACION`. |
| 2026-08-01 | Agregada D26: aprobación/reprobación de alumnos — mapeo `aprueba` vía `catalogo_calificacion`, enriquecimiento de `intel.rendimiento_academico_alumnos` con tags de perfil docente (sexo/tramo_edad/jerarquia/tipo_contrato_tag), decisión de acotar a Jornada, y snapshot de cobertura por tipología para reusar en subtítulos. |
| 2026-08-02 | Reordenamiento general: agregada sección "Vigencia de universos" al inicio, columna "Vigencia" en el índice, y notas ⚠️ HISTÓRICO en D3/D5/D14/D17/D19/D20/D22/D23/D24 marcando qué sigue siendo regla vigente vs. qué son conteos obsoletos de los universos 492/917/545. Agregado el "Catálogo de visualizaciones P1 confirmadas" (12 gráficos) con fuente y filtros de cada uno, como práctica a mantener hacia adelante para cada visualización que se apruebe. `tramo_antiguedad`/`antiguedad_anios` agregados a `intel.rendimiento_academico_alumnos` (D26). |
| 2026-08-03 | Agregada D27: grupo de dificultad de asignaturas por terciles de % de aprobación histórico (Baja/Media/Alta), calculado sobre el universo completo y tageado en `intel.rendimiento_academico_alumnos`. Se descartó un z-score por asignatura por falta de pares de comparación (56% de asignaturas con un solo docente). Confirmada la facultad/plan/código de plan del alumno ya presentes en `intel.rendimiento_academico_alumnos` (heredados de `consolidados.calificacion_alumno`), sin necesidad de agregarlos. |
| 2026-08-03 (2) | Agregadas 2 visualizaciones al catálogo (`dificultad_composicion/`, `antiguedad_dificultad/`) y documentado en D27 el criterio de "grupo predominante" para pruebas t sobre atributos fijos del docente (antigüedad) — no se promedia por docente×grupo como con `aprueba`, se asigna cada docente a un solo grupo para no romper la independencia del t-test. Resultado: antigüedad significativamente mayor en docentes de asignaturas de Baja aprobación histórica (7.0 vs 5.8 años, p=0.0375). |
| 2026-08-03 (3) | Agregadas 3 visualizaciones más al catálogo (`edad_dificultad/`, `sexo_dificultad/`, `jerarquia_dificultad/`), mismo criterio de "grupo predominante" aplicado a edad (continua) y a sexo/escalafón (binarias, codificadas 0/1). Resultados: edad significativa (p=0.0387, 49.0 vs 46.8 años), sexo muy significativa (p=0.0001, 43.8% vs 61.3% mujeres — hombres sobrerrepresentados en asignaturas difíciles), escalafón no significativa (p=0.0716, 18.9% vs 12.8% Regular). |
| 2026-08-04 | Gráficos descriptivos de `sexo_dificultad/` y `jerarquia_dificultad/` convertidos a barra 100% apilada (Hombre/Mujer, Docente/Regular) para mostrar la composición completa por grupo, no solo un lado del binario. `jerarquia_dificultad/` excluida del consolidado `P1_presentacion.pptx` (queda en BLOQUE_III de `generar_presentacion.py` comentada) por no ser significativa (p=0.0716) — sigue existiendo como script y pptx suelto, con el hallazgo documentado arriba. |
