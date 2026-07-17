# Diccionario de Datos — Análisis UCEN
**Proyecto:** Impacto del perfeccionamiento docente en el aprendizaje estudiantil  
**Base de datos:** PostgreSQL `ucen` (Docker `ucen_db`)  
**Última actualización:** 2026-05-09  

Cada columna indica su **tabla de origen** (archivo fuente original antes del ETL) y su **columna de origen** (nombre exacto en el archivo fuente). Las columnas marcadas con `ETL` son derivadas o calculadas por los scripts de procesamiento.

---

## Schema `consolidados` — Tablas maestras y transaccionales

---

### `consolidados.docente`
Tabla maestra de docentes. PK del sistema. Integra NOMINA + DOTACION en una sola fila por docente.  
**Fuentes:** `NOMINA .csv` + `DOTACION.csv` + `evaluacion_periodo.csv` + archivos de formación + `calificacion_alumno`

| Columna | Tipo | Tabla origen | Columna origen | Descripción |
|---|---|---|---|---|
| `rut_key` | TEXT | NOMINA / DOTACION | `RUT` | RUT sin dígito verificador. Clave universal del sistema. |
| `nombre` | TEXT | NOMINA | `NOMBRE` | Nombre completo del docente. |
| `sexo` | TEXT | NOMINA | `SEXO` | Sexo del docente (M/F). |
| `tipo_contrato` | TEXT | NOMINA | `JORNADA/HONORARIO` | Tipo de contrato: Jornada, Honorario o Jornada+Honorario (fusionado en ETL). |
| `estamento` | TEXT | NOMINA | `ESTAMENTO FUNCIONAL` | Categoría funcional del cargo. |
| `funcion_principal` | TEXT | NOMINA | `FUNCIÓN PRINCIPAL ACADÉMICA` | Función académica principal declarada. |
| `departamento` | TEXT | NOMINA | `NOMBRE DEPARTAMENTO FUNCIÓN PRINCIPAL` | Departamento al que pertenece la función principal. |
| `jerarquia` | TEXT | NOMINA | `JERARQUÍA` | Jerarquía académica registrada en nómina. |
| `fecha_jerarquizacion` | TEXT | NOMINA | `FECHA JERARQUIZACIÓN` | Fecha en que se asignó la jerarquía actual. |
| `observaciones_nomina` | TEXT | NOMINA | `OBSERVACIONES` | Observaciones libres registradas en nómina. |
| `fuente` | TEXT | ETL | — | Origen del registro: NOMINA_DOTACION / NOMINA / SOLO_DOTACION / SOLO_EVALUACIONES / SOLO_CALIFICACIONES / SOLO_FORMACION. |
| `cargo` | TEXT | DOTACION | `CARGO` | Cargo formal en la institución. |
| `centro_costo` | TEXT | DOTACION | `CENTRO COSTO` | Código del centro de costo asignado. |
| `area_carrera` | TEXT | DOTACION | `ÁREA / CARRERA` | Área o carrera donde ejerce la docencia. |
| `unidad_facultad` | TEXT | DOTACION | `UNIDAD/ FACULTAD` | Facultad o unidad académica. |
| `ubicacion` | TEXT | DOTACION | `UBICACIÓN` | Campus o sede de adscripción. |
| `fecha_ingreso` | DATE | DOTACION | `F. INGRESO` | Fecha de ingreso a la institución (normalizada a YYYY-MM-DD). |
| `fecha_retiro` | DATE | DOTACION | `F. RETIRO` | Fecha de retiro. NULL = activo (valor original "INDEFINIDO" convertido a NULL). |
| `antiguedad_anios` | FLOAT | DOTACION | `ANTIGÜEDAD (AÑOS)` | Antigüedad en años al momento del corte de datos. |
| `clasificacion` | TEXT | DOTACION | `CLASIFICACIÓN` | Clasificación contractual (Académico, etc.). |
| `jornada_dot` | TEXT | DOTACION | `JORNADA` | Jornada en horas semanales según dotación. |
| `fecha_nacimiento` | DATE | DOTACION | `FECHA NACIMIENTO` | Fecha de nacimiento (normalizada a YYYY-MM-DD). |
| `edad_anios` | FLOAT | DOTACION | `EDAD (AÑOS)` | Edad en años al momento del corte. |
| `jerarquia_dot` | TEXT | DOTACION | `JERARQUÍA` | Jerarquía según dotación (puede diferir de jerarquia de nómina). |
| `nivel_formacion` | TEXT | DOTACION | `NIVEL FORMACIÓN` | Nivel académico más alto alcanzado (Doctor, Magíster, etc.). |
| `nombre_grado` | TEXT | DOTACION | `NOMBRE GRADO TÍTULO` | Nombre del grado o título de postgrado. |
| `institucion_grado` | TEXT | DOTACION | `INSTITUCIÓN GRADO TÍTULO` | Institución donde obtuvo el grado. |
| `pais_grado` | TEXT | DOTACION | `PAÍS GRADO TÍTULO` | País de la institución donde obtuvo el grado. |

---

### `consolidados.pregunta`
Catálogo canónico de las 19 preguntas del instrumento de evaluación estudiantil.  
**Fuente:** ETL construido a partir del instrumento (IDs semánticos propios, no los numéricos originales).

| Columna | Tipo | Tabla origen | Columna origen | Descripción |
|---|---|---|---|---|
| `pregunta_id` | TEXT | ETL | — | ID semántico: APR_01-03, MET_01-05, AFO_01-09, SAT_BIN, SAT_NOTA. |
| `dimension` | TEXT | ETL | — | Dimensión del instrumento: Aprendizajes, Metodologías y Evaluación, Aspectos Formales, Satisfacción. |
| `orden` | INT | ETL | — | Orden de la pregunta dentro del instrumento (1-19). |
| `tipo_respuesta` | TEXT | ETL | — | Tipo: LIKERT (acuerdo/indiferente/desacuerdo), BINARIO (sí/no), NOTA (1-7). |
| `texto_principal` | TEXT | Instrumento eval | fila 2 encabezado CSV | Texto vigente de la pregunta (2023-02 en adelante). |
| `texto_alternativo` | TEXT | Instrumento eval | fila 2 encabezado CSV | Texto anterior (solo MET_04 en 2023-01). NULL para el resto. |
| `periodos_texto_alt` | TEXT | ETL | — | Períodos donde aplica el texto alternativo. Solo "2023-01" para MET_04. |
| `id_original` | TEXT | Instrumento eval | fila 3 encabezado CSV | ID numérico original del instrumento (4509-4527). |

---

### `consolidados.catalogo_calificacion`
Catálogo de los 13 códigos de calificación cualitativa.  
**Fuente:** ETL + `DOCUMENTO EXPLICATIVO DE CATEGORIA VARIAS 9-05-2026.docx`

| Columna | Tipo | Tabla origen | Columna origen | Descripción |
|---|---|---|---|---|
| `codigo` | TEXT | ETL | — | Código de calificación (B, MB, SO, SU, M, MM, I, A, R, NP, P, SC, SD). |
| `descripcion` | TEXT | ETL | — | Nombre corto (Bueno, Muy Bueno, etc.). |
| `descripcion_oficial` | TEXT | Documento UCEN | DOCUMENTO EXPLICATIVO... | Definición institucional oficial. |
| `aprueba` | BOOL | ETL | — | True = aprueba, False = reprueba, NULL = estado administrativo. |
| `tiene_nota` | BOOL | ETL | — | True si el código tiene nota numérica asociada. |

---

### `consolidados.evaluacion_periodo`
Una fila por instancia de evaluación estudiantil (docente × asignatura × sección × período).  
**Fuente:** `CONSOLIDADO EVALUACION ESTUDIANTES UCEN 3-5-2026 / {periodo}.csv` — columnas 0-13.

| Columna | Tipo | Tabla origen | Columna origen | Descripción |
|---|---|---|---|---|
| `evaluacion_id` | INT | ETL | — | ID único de instancia, continuo entre períodos. PK. |
| `periodo` | TEXT | CSV evaluación | col 0 `4495 Periodo` | Semestre académico (2023-01 a 2025-02). |
| `rut_director` | TEXT | CSV evaluación | col 1 `4496 Rut Director` | RUT sin DV del director de carrera. |
| `rut_docente` | TEXT | CSV evaluación | col 2 `4497 Rut Docente` | RUT sin DV del docente evaluado. FK → docente.rut_key. |
| `nombre_docente` | TEXT | CSV evaluación | col 3 | Nombre del docente tal como aparece en el sistema. |
| `cod_facultad` | TEXT | CSV evaluación | col 4 | Código de facultad. |
| `facultad` | TEXT | CSV evaluación | col 5 | Nombre de la facultad. |
| `cod_plan` | TEXT | CSV evaluación | col 6 | Código del plan de estudios. |
| `plan` | TEXT | CSV evaluación | col 7 | Nombre del plan de estudios. |
| `cod_asignatura` | TEXT | CSV evaluación | col 8 | Código de la asignatura. |
| `nombre_asignatura` | TEXT | CSV evaluación | col 9 | Nombre de la asignatura. |
| `seccion` | TEXT | CSV evaluación | col 10 | Sección de la asignatura. |
| `total_alumnos_evaluar` | FLOAT | CSV evaluación | col 11 | Total de alumnos habilitados para evaluar. |
| `n_alumnos_evaluaron` | FLOAT | CSV evaluación | col 12 | Cantidad de alumnos que efectivamente evaluaron. |
| `cobertura_pct` | FLOAT | CSV evaluación | col 13 | Porcentaje de cobertura de la evaluación (n_evaluaron / total). |

---

### `consolidados.evaluacion_respuesta`
Respuestas en formato largo: una fila por instancia × pregunta (24.514 × 19 = 465.766 filas).  
**Fuente:** `CONSOLIDADO EVALUACION ESTUDIANTES UCEN 3-5-2026 / {periodo}.csv` — columnas 14-67.

| Columna | Tipo | Tabla origen | Columna origen | Descripción |
|---|---|---|---|---|
| `id` | INT | ETL | — | ID único de respuesta. PK. |
| `evaluacion_id` | INT | ETL | — | FK → evaluacion_periodo.evaluacion_id. |
| `pregunta_id` | TEXT | ETL | — | FK → pregunta.pregunta_id. ID semántico asignado por posición de columna. |
| `pct_acuerdo` | FLOAT | CSV evaluación | cols LIKERT (pos 0) | % de alumnos en acuerdo. Solo para preguntas LIKERT. |
| `pct_indiferente` | FLOAT | CSV evaluación | cols LIKERT (pos 1) | % de alumnos indiferentes. Solo para preguntas LIKERT. |
| `pct_desacuerdo` | FLOAT | CSV evaluación | cols LIKERT (pos 2) | % de alumnos en desacuerdo. Solo para preguntas LIKERT. |
| `pct_si` | FLOAT | CSV evaluación | col 65 | % de respuestas SÍ. Solo SAT_BIN. |
| `pct_no` | FLOAT | CSV evaluación | col 66 | % de respuestas NO. Solo SAT_BIN. |
| `nota_promedio` | FLOAT | CSV evaluación | col 67 | Nota promedio 1-7. Solo SAT_NOTA. Promedio global = 6.01. |

---

### `consolidados.calificacion_alumno`
Notas individuales de alumnos por asignatura, período y docente.  
**Fuente:** `DETALLE DE EVALUACION DE CADA ESTUDIANTE A DOCENTE 3-5-2026 / datos.csv`

| Columna | Tipo | Tabla origen | Columna origen | Descripción |
|---|---|---|---|---|
| `calificacion_id` | INT | ETL | — | ID único de registro. PK. |
| `periodo` | TEXT | datos.csv | `Periodo Asignatura` | Semestre académico. |
| `rut_alumno` | TEXT | datos.csv | `Rut` | RUT del alumno sin DV. |
| `cod_plan` | TEXT | datos.csv | `Código Plan` | Código del plan de estudios del alumno. |
| `plan` | TEXT | datos.csv | `Plan` | Nombre del plan de estudios. |
| `sede` | TEXT | datos.csv | `Sede` | Sede donde cursó la asignatura. |
| `facultad` | TEXT | datos.csv | `Facultad` | Facultad correspondiente. |
| `cohorte` | TEXT | datos.csv | `Cohorte` | Cohorte de ingreso del alumno (ej: 2020-01). |
| `cod_asignatura` | TEXT | datos.csv | `Código Asignatura` | Código de la asignatura. |
| `nombre_asignatura` | TEXT | datos.csv | `Asignatura` | Nombre de la asignatura. |
| `seccion` | TEXT | datos.csv | `Sección` | Sección de la asignatura. |
| `convocatoria` | TEXT | datos.csv | `Convocatoria` | Convocatoria del acta (JUL, DIC, AGO, ENE, etc.). |
| `calificacion` | TEXT | datos.csv | `Calificación` | Código cualitativo. FK → catalogo_calificacion.codigo. |
| `nota` | FLOAT | datos.csv | `Nota` | Nota numérica. NULL para códigos sin nota (NP, SC, etc.). |
| `rut_docente` | TEXT | datos.csv | `Rut Docente` | RUT del docente sin DV. FK → docente.rut_key. |
| `nombre_docente` | TEXT | datos.csv | `NOMBRE DOCENTE` | Nombre completo del docente. |

---

### `consolidados.participacion_formacion`
Registro de participación docente en actividades de formación 2022-2025.  
**Fuentes:** `DIPLOMADO {año}.csv` + `TALLERES {periodo}.csv` + `PROYECTOS DE INVESTIGACION.csv`

| Columna | Tipo | Tabla origen | Columna origen | Descripción |
|---|---|---|---|---|
| `rut_key` | TEXT | DIPLOMADO/TALLERES/PROYECTOS | `RUT` | RUT sin DV. FK → docente.rut_key. |
| `tipo_formacion` | TEXT | ETL | — | Tipo de actividad: DIPLOMADO, TALLER o PROYECTO. |
| `periodo_evento` | TEXT | TALLERES | `Periodo` | Semestre del taller (ej: 2023-02). NULL para DIPLOMADO y PROYECTO. |
| `anio_evento` | TEXT | ETL / PROYECTOS | `Año` | Año del evento. Derivado del archivo para DIPLOMADOS y TALLERES. |
| `nombre_docente` | TEXT | DIPLOMADO/TALLERES/PROYECTOS | `NOMBRE DOCENTE` | Nombre del docente en la fuente. |
| `nombre_actividad` | TEXT | DIPLOMADO/TALLERES/PROYECTOS | `Tipo formación` / `Actividad` / `Nombre proyecto` | Nombre de la actividad de formación. |
| `facultad` | TEXT | DIPLOMADO/TALLERES/PROYECTOS | `Facultad` | Facultad del docente al momento del evento. |
| `carrera` | TEXT | DIPLOMADO/TALLERES/PROYECTOS | `Carrera` | Carrera asociada al evento. |
| `sede` | TEXT | DIPLOMADO/TALLERES/PROYECTOS | `Sede` | Sede donde se realizó la actividad. |
| `jerarquia_evento` | TEXT | PROYECTOS | `Jerarquía` | Jerarquía del docente al momento del proyecto. NULL para DIPLOMADO y TALLER. |
| `contrato_evento` | TEXT | PROYECTOS | `Tipo de contrato` | Tipo de contrato al momento del proyecto. NULL para DIPLOMADO y TALLER. |
| `linea_proyecto` | TEXT | PROYECTOS | `Linea` | Línea temática del proyecto. NULL para DIPLOMADO y TALLER. |

---

### `consolidados.consolidado_jefes`
Perfil completo del docente cruzado con evaluación de jefes directos por año.  
**Fuentes:** `consolidados.docente` (fuente=NOMINA o NOMINA_DOTACION) + `EVALUACION DE JEFES A DOCENTES .csv`

| Columna | Tipo | Tabla origen | Columna origen | Descripción |
|---|---|---|---|---|
| *(cols 1-28)* | — | consolidados.docente | — | Todas las columnas de docente (perfil completo). Ver tabla docente. |
| `anio_evaluacion` | TEXT | EVALUACION JEFES | `PERIODO` | Año de la evaluación de jefe (2022-2025). NULL = docente sin evaluación. |
| `tiene_eval_jefe` | TEXT | ETL | — | "SI" / "NO" — indica si esa fila tiene evaluación de jefe. |
| `concepto` | TEXT | EVALUACION JEFES | `CONCEPTO` | Concepto cualitativo: Muy Bueno, Bueno, Insuficiente, Deficiente. |
| `porcentaje_concepto` | FLOAT | EVALUACION JEFES | `PORCENTAJE CONCEPTO` | Porcentaje asociado al concepto. |
| `cumplimiento_cd` | FLOAT | EVALUACION JEFES | `CUMPLIMIENTO CD` | Porcentaje de cumplimiento de compromisos de desempeño. |
| `edd_total` | FLOAT | EVALUACION JEFES | `EDD` | Puntaje total de evaluación de desempeño docente. |
| `edd_director` | FLOAT | EVALUACION JEFES | `EDD Director` | Componente director del EDD. |
| `edd_docente` | FLOAT | EVALUACION JEFES | `EDD Docente` | Componente docente del EDD. |
| `activo_ucen` | TEXT | EVALUACION JEFES | `ACTIVO EN UCEN` | Indica si el docente estaba activo al momento de la evaluación. |
| `facultad_jefe` | TEXT | EVALUACION JEFES | `FACULTAD` | Facultad registrada en la evaluación de jefes. |
| `carrera_jefe` | TEXT | EVALUACION JEFES | `CARRERA` | Carrera registrada en la evaluación de jefes. |
| `sede_jefe` | TEXT | EVALUACION JEFES | `SEDE` | Sede registrada en la evaluación de jefes. |
| `observacion_jefe` | TEXT | EVALUACION JEFES | `OBSERVACIÓN` | Texto cualitativo libre del director sobre el docente. |
| `cod_observacion` | TEXT | EVALUACION JEFES | `COD_OBSERVACION` | Código de la observación cualitativa. |

---

## Schema `analisis` — Subconjuntos y tablas P1–P3

---

### `analisis.docente_ambos`
Los 520 docentes con perfil completo (en NOMINA y DOTACION).  
**Fuente:** ETL — filtro de `consolidados.docente` WHERE fuente = 'NOMINA_DOTACION'.  
**Columnas:** idénticas a `consolidados.docente` (28 cols). Ver tabla docente.

---

### `analisis.docente_solo_nomina`
437 docentes presentes en nómina pero sin datos de dotación.  
**Fuente:** ETL — filtro de `consolidados.docente` WHERE fuente = 'NOMINA'.  
**Columnas:** idénticas a `consolidados.docente`. Columnas de DOTACION en NULL.

---

### `analisis.docente_solo_dotacion`
28 docentes en dotación pero ausentes de nómina activa.  
**Fuente:** ETL — filtro de `consolidados.docente` WHERE fuente = 'SOLO_DOTACION'.  
**Columnas:** idénticas a `consolidados.docente`. Columnas de NOMINA en NULL.

---

### `analisis.docente_solo_evaluaciones`
1.153 docentes que aparecen en evaluaciones estudiantiles pero no en nómina ni dotación.  
**Fuente:** ETL — filtro de `consolidados.docente` WHERE fuente = 'SOLO_EVALUACIONES'.  
**Columnas:** idénticas a `consolidados.docente`. Solo rut_key, nombre y fuente tienen datos.

---

### `analisis.grupo_control_p3`
219 docentes del grupo AMBOS sin formación registrada 2022-2025 y con evaluaciones estudiantiles.  
**Fuente:** ETL — subconjunto de `analisis.docente_ambos` cruzado contra `participacion_formacion` y `evaluacion_periodo`.

| Columna | Tipo | Tabla origen | Descripción |
|---|---|---|---|
| *(cols 1-28)* | — | consolidados.docente | Perfil completo. Ver tabla docente. |
| `grupo` | TEXT | ETL | Valor fijo: "CONTROL_SIN_FORMACION". |

---

### `analisis.resumen_participacion`
Resumen ejecutivo de participación en formación por tipo y año.  
**Fuente:** ETL — agregación de `consolidados.participacion_formacion`.

| Columna | Tipo | Tabla origen | Descripción |
|---|---|---|---|
| `tipo_formacion` | TEXT | participacion_formacion | DIPLOMADO, TALLER o PROYECTO. |
| `anio_evento` | TEXT | participacion_formacion | Año del evento. |
| `total_registros` | INT | ETL | Total de registros en esa combinación. |
| `ruts_unicos` | INT | ETL | RUTs únicos de docentes participantes. |

---

### `analisis.p3_grupo_tratamiento`
Una fila por docente × evento de formación para los 520 AMBOS con participación registrada.  
Incluye períodos baseline/resultado calculados y flags de aptitud para análisis P3.  
**Fuente:** ETL — cruza `analisis.docente_ambos` + `participacion_formacion` + `evaluacion_periodo` + `consolidado_jefes`.

| Columna | Tipo | Tabla origen | Columna origen | Descripción |
|---|---|---|---|---|
| `rut_key` | TEXT | docente_ambos | `rut_key` | RUT sin DV del docente. |
| `nombre` | TEXT | docente_ambos | `nombre` | Nombre completo. |
| `departamento` | TEXT | docente_ambos | `departamento` | Departamento de adscripción. |
| `jerarquia` | TEXT | docente_ambos | `jerarquia` | Jerarquía académica. |
| `nivel_formacion` | TEXT | docente_ambos | `nivel_formacion` | Nivel de formación (Doctor, Magíster, etc.). |
| `antiguedad_anios` | FLOAT | docente_ambos | `antiguedad_anios` | Antigüedad en años. |
| `clasificacion` | TEXT | docente_ambos | `clasificacion` | Clasificación contractual. |
| `area_carrera` | TEXT | docente_ambos | `area_carrera` | Área o carrera. |
| `unidad_facultad` | TEXT | docente_ambos | `unidad_facultad` | Facultad. |
| `sexo` | TEXT | docente_ambos | `sexo` | Sexo del docente. |
| `tipo_contrato` | TEXT | docente_ambos | `tipo_contrato` | Tipo de contrato. |
| `fuente` | TEXT | docente_ambos | `fuente` | Siempre NOMINA_DOTACION para este grupo. |
| `tipo_formacion` | TEXT | participacion_formacion | `tipo_formacion` | DIPLOMADO, TALLER o PROYECTO. |
| `nombre_actividad` | TEXT | participacion_formacion | `nombre_actividad` | Nombre de la actividad de formación. |
| `anio_evento` | TEXT | participacion_formacion | `anio_evento` | Año del evento formativo. |
| `periodo_evento` | TEXT | participacion_formacion | `periodo_evento` | Semestre del taller. NULL para DIPLOMADO y PROYECTO. |
| `periodo_baseline` | TEXT | ETL | — | Período antes de la formación: año X-1 (diplomados/proyectos) o semestre S-1 (talleres). |
| `periodo_resultado` | TEXT | ETL | — | Período después de la formación: año X+1 (diplomados/proyectos) o semestre S+2 (talleres). |
| `tiene_eval_alumnos_baseline` | BOOL | ETL | — | TRUE si el docente tiene evaluación estudiantil en el período baseline. |
| `tiene_eval_alumnos_resultado` | BOOL | ETL | — | TRUE si el docente tiene evaluación estudiantil en el período resultado. |
| `tiene_eval_jefe` | BOOL | ETL | — | TRUE si el docente tiene al menos una evaluación de jefe en cualquier año. |
| `apto_p3` | BOOL | ETL | — | TRUE si tiene_eval_alumnos_baseline AND tiene_eval_alumnos_resultado. Criterio de inclusión en análisis de impacto. |

---

## Schema `intel` — Análisis específicos a pedido

*Vacío actualmente. Las tablas se agregan aquí a medida que se construyen análisis específicos.*

---

## Notas generales de diseño

| Decisión | Detalle |
|---|---|
| **RUT sin DV** | Todos los `rut_key` y `rut_docente` están sin dígito verificador. Permite joins directos entre fuentes transaccionales y maestras. |
| **Fechas** | `fecha_ingreso`, `fecha_retiro`, `fecha_nacimiento` normalizadas a `YYYY-MM-DD`. Valor "INDEFINIDO" en F. RETIRO convertido a NULL (activo). |
| **ESPINOZA (16322128)** | Dos personas distintas con mismo RUT. Ambas filas eliminadas de todas las tablas — no se puede distinguir a cuál pertenecen los datos. |
| **STIPPEL (25600736)** | Misma persona, dos departamentos distintos. Conserva 2 filas en docente_ambos. Pendiente confirmar con contraparte. |
| **Sin FK constraints** | Las tablas se cargaron sin restricciones de FK. La integridad referencial fue validada por script (0 RUTs huérfanos). Se pueden agregar constraints en una segunda fase. |
