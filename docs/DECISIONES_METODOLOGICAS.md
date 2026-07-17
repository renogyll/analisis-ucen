# Decisiones Metodológicas — Análisis UCEN
**Proyecto:** Impacto del perfeccionamiento docente en el aprendizaje estudiantil  
**Contraparte:** Vicerrectoría Académica / Dirección de Desarrollo Académico  
**Última actualización:** 2026-07-11  
**Estado:** Documento vivo — actualizar al tomar nuevas decisiones

---

## Índice de decisiones

| # | Tema | Estado | Universo |
|---|------|--------|----------|
| 1 | Identificador único (RUT) | ✅ Resuelto | Ambos |
| 2 | Duplicados en NOMINA | ✅ Resuelto | Ambos |
| 3 | Universos de análisis (492 y 917) | ✅ Resuelto | — |
| 4 | Jerarquía válida — criterio de inclusión | ✅ Resuelto | Ambos |
| 5 | `tiene_perfil_completo` | ✅ Resuelto | 917 |
| 6 | Formato `fecha_retiro` en DOTACION | ✅ Resuelto | Ambos |
| 7 | IDs canónicos de preguntas | ✅ Resuelto | Ambos |
| 8 | Cambio de texto MET_04 (2023-01) | ✅ Resuelto | Ambos |
| 9 | Estructura de encabezados eval. estudiantil | ✅ Resuelto | Ambos |
| 10 | Umbral de cobertura evaluaciones SAT (CM-1) | ✅ Resuelto | Ambos |
| 11 | Promedio SAT ponderado por alumnos (CM-2) | ✅ Resuelto | Ambos |
| 12 | Reglas de período baseline / resultado (P3) | ✅ Resuelto | Ambos |
| 13 | Granularidad de `periodo_evento` | ✅ Resuelto | Ambos |
| 14 | Criterio `apto_p3` | ✅ Resuelto | Ambos |
| 15 | Docentes con múltiples instancias de formación | ✅ Resuelto | Ambos |
| 16 | Z-score SAT: metodología de estandarización | ✅ Resuelto | Ambos |
| 17 | Grupo de control | ✅ Resuelto | 492 |
| 18 | Columnas restituidas de evaluación de jefes | ✅ Resuelto | 492 |
| 19 | Agregación SAT universo 917 para docentes solo-nómina | ⚠️ Pendiente revisión | 917 |
| 20 | Sub-universo Jornada/Planta (N=545) | ✅ Resuelto | 917 |
| 21 | "NO INFORMA" como dato faltante en variables categóricas | ✅ Resuelto | Ambos |
| 22 | Brecha de dotación en Jornada/Planta (60 sin dotación) | ✅ Caracterizado | 917 |
| 23 | Sub-cascadas de calidad de datos — Jornada con dotación | ✅ Resuelto | 917 |
| 24 | P2 desagregado para Jornada/Planta | ✅ Resuelto | 917 |

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

**Contexto:** 424 docentes del universo 917 no tienen datos de dotación (`tiene_perfil_completo = False`). Sin embargo, 382 de ellos (90%) tienen SAT válido.

**Pregunta abierta:** ¿Son comparables los SAT de docentes solo-nómina con los de perfil completo para el análisis de impacto? Los primeros no tienen dato de `unidad_facultad`, lo que afecta el z-score (se les asigna "Otras" como facultad de referencia).

**Estado:** Los 68 docentes solo-nómina aptos P3 están incluidos en el análisis actual con z-score calculado usando la categoría "Otras" como referencia. Revisar si esto introduce sesgo antes de presentar resultados finales.

---

---

## 20. Sub-universo Jornada/Planta (N=545)

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

## Registro de cambios

| Fecha | Cambio |
|---|---|
| 2026-05-09 | Versión inicial (decisiones 1–13, varios pendientes) |
| 2026-05-21 | Actualización completa: resolución CM-1 y CM-2, universo 917, duplicados resueltos, z-score, apto_p3, múltiples instancias |
| 2026-07-11 | Agregadas D20–D24: sub-universo Jornada/Planta, tratamiento "NO INFORMA", brecha de dotación, sub-cascadas calidad datos, P2 desagregado. Actualizado D3 con tercer universo. |
