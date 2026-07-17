-- ============================================================
-- schema.sql — Documentación del esquema PostgreSQL
-- Proyecto: Análisis P3 UCEN  |  DB: ucen  |  2026-07-16
-- ============================================================
--
-- PROPÓSITO: Este archivo no se ejecuta de una sola vez.
-- Es la referencia viva de qué existe en la base de datos,
-- por qué tiene esas filas y cómo se construyó.
-- Los tipos son aproximados (df.to_sql usa TEXT para object,
-- FLOAT8 para float64, BOOLEAN para bool).
--
-- ORDEN DE EJECUCIÓN DE LOS ETL:
--   1. consolidados.*   → cargados desde CSV externos (etl/complementarios/)
--   2. analisis.*       → generados por ETL Python (etl/00_base/ … etl/05_aptos_p3/)
--   3. intel.*          → derivados estadísticos (etl/complementarios/etl_intel_*.py)
-- ============================================================


-- ============================================================
-- SCHEMA: consolidados
-- Datos maestros cargados desde los archivos fuente (Excel/CSV).
-- NINGÚN ETL de analisis o intel debe escribir aquí.
-- Estas tablas son el "suelo" del proyecto: se recargan cuando
-- llega una nueva entrega de datos de la contraparte.
-- ============================================================

CREATE SCHEMA IF NOT EXISTS consolidados;


-- consolidados.docente
-- ─────────────────────
-- FUENTE: etl/complementarios/etl_docente.py
-- ORIGEN DE LOS DATOS: hoja NOMINA + hoja DOTACION del Excel maestro
--   (CONSOLIDADO DOCENTES 3-05-2026.xlsx)
--
-- N DE FILAS: ~2.300 (NO es N de docentes únicos)
-- Por qué no son docentes únicos: hay una fila por COMBINACIÓN de
-- fuente de datos (NOMINA, DOTACION, SOLO_EVALUACIONES). Un mismo RUT
-- puede aparecer en varias fuentes y tendrá varias filas aquí.
-- El universo analítico de RUTs únicos está en analisis.universo_base.
--
-- CAMPO CLAVE: fuente
--   NOMINA            → presente solo en NOMINA (957 RUTs en el dataset actual)
--   NOMINA_DOTACION   → presente en ambas  (520 RUTs en el dataset actual)
--   SOLO_DOTACION     → presente solo en DOTACION (27 RUTs + 1 excluido = 28 originalmente)
--   SOLO_EVALUACIONES → tiene eval de alumnos pero NO está en NOMINA ni DOTACION
--
-- NOTA ESPINOZA: RUT 16322128 excluido de todos los universos analíticos
-- por ambigüedad de identidad (dos personas distintas con el mismo RUT).
-- El campo rut_key es el RUT sin dígito verificador, sin puntos.

CREATE TABLE IF NOT EXISTS consolidados.docente (
    rut_key                 TEXT,        -- PK lógica: RUT sin dígito verificador
    fuente                  TEXT,        -- NOMINA | NOMINA_DOTACION | SOLO_DOTACION | SOLO_EVALUACIONES
    nombre                  TEXT,
    sexo                    TEXT,        -- MASCULINO | FEMENINO (tal como viene del Excel)
    tipo_contrato           TEXT,        -- JORNADA | HONORARIO (col "JORNADA/HONORARIO" de NOMINA)
    estamento               TEXT,
    funcion_principal       TEXT,
    departamento            TEXT,
    jerarquia               TEXT,        -- Jerarquía académica UCEN (o SIN JERARQUÍA / NO INFORMA)
    fecha_jerarquizacion    TEXT,
    observaciones_nomina    TEXT,
    -- Columnas de DOTACION (NULL para SOLO_NOMINA y SOLO_EVALUACIONES)
    cargo_dot               TEXT,        -- cargo en planilla de dotación
    area_carrera            TEXT,
    unidad_facultad         TEXT,
    centro_costo            TEXT,
    ubicacion               TEXT,
    clasificacion           TEXT,
    fecha_ingreso           TEXT,
    fecha_retiro            TEXT,
    antiguedad_anios        NUMERIC,
    fecha_nacimiento        TEXT,
    edad_anios              NUMERIC,
    jornada_dot             TEXT,
    nivel_formacion         TEXT,        -- Pregrado | Magíster | Doctorado | etc.
    nombre_grado            TEXT,
    institucion_grado       TEXT,
    pais_grado              TEXT
);

COMMENT ON TABLE consolidados.docente IS
'Tabla maestra de docentes. ~2.300 filas ≠ docentes únicos.
 El universo analítico de RUTs únicos está en analisis.universo_base (~985).';


-- consolidados.evaluacion_periodo
-- ─────────────────────────────────
-- FUENTE: etl/complementarios/etl_evaluaciones.py
-- ORIGEN: 6 archivos de evaluación estudiantil (2023-01 a 2025-02)
--   + 1 archivo de evaluación de jefes (formato distinto, ver evaluacion_jefes)
--
-- N DE FILAS: ~2.300 instancias (una fila = docente × asignatura × sección × periodo)
-- No confundir con docentes únicos. Un docente que dicta 4 secciones en 2024-01
-- genera 4 filas en esta tabla.
--
-- CAMPO CLAVE: cobertura_pct
--   Todos los análisis SAT aplican el CRITERIO CM-1: cobertura_pct >= 40
--   (al menos 40% de alumnos respondió). Filas con cobertura < 40 existen en la
--   tabla pero no se usan en análisis.

CREATE TABLE IF NOT EXISTS consolidados.evaluacion_periodo (
    evaluacion_id           BIGINT,      -- PK autonumérica generada en ETL
    periodo                 TEXT,        -- formato YYYY-SS, ej: "2024-01"
    rut_director            TEXT,
    rut_docente             TEXT,        -- FK lógica → consolidados.docente.rut_key
    nombre_docente          TEXT,
    cod_facultad            TEXT,
    facultad                TEXT,
    cod_plan                TEXT,
    plan                    TEXT,
    cod_asignatura          TEXT,
    nombre_asignatura       TEXT,
    seccion                 TEXT,
    n_alumnos_matriculados  INTEGER,
    n_alumnos_evaluaron     INTEGER,
    cobertura_pct           NUMERIC      -- n_alumnos_evaluaron / n_alumnos_matriculados × 100
);

COMMENT ON TABLE consolidados.evaluacion_periodo IS
'Metadata de cada instancia de evaluación estudiantil.
 Una fila = docente × asignatura × sección × periodo.
 Criterio CM-1 de calidad: cobertura_pct >= 40.';


-- consolidados.evaluacion_respuesta
-- ───────────────────────────────────
-- FUENTE: etl/complementarios/etl_evaluaciones.py  (misma ejecución que evaluacion_periodo)
-- ESTRUCTURA: formato largo (long format). Una fila por instancia × pregunta.
-- Cada evaluacion_id de evaluacion_periodo tiene múltiples filas aquí.
--
-- PREGUNTAS:
--   APR_01…03 : dimensión Aprendizaje (Likert)
--   MET_01…05 : dimensión Metodología (Likert)
--   AFO_01…09 : dimensión Ambiente Formativo (Likert)
--   SAT_BIN    : Satisfacción binaria (% SÍ / % NO)
--   SAT_NOTA   : Satisfacción nota 1-7 ← INDICADOR PRINCIPAL del proyecto

CREATE TABLE IF NOT EXISTS consolidados.evaluacion_respuesta (
    respuesta_id            BIGINT,      -- PK
    evaluacion_id           BIGINT,      -- FK → consolidados.evaluacion_periodo.evaluacion_id
    pregunta_id             TEXT,        -- APR_01 | MET_01 | AFO_01 | SAT_BIN | SAT_NOTA | …
    tipo_pregunta           TEXT,        -- LIKERT | BINARIO | NOTA
    -- Para LIKERT: porcentajes de acuerdo/indiferente/desacuerdo
    pct_acuerdo             NUMERIC,
    pct_indiferente         NUMERIC,
    pct_desacuerdo          NUMERIC,
    -- Para SAT_BIN: porcentaje que recomienda
    pct_si                  NUMERIC,
    pct_no                  NUMERIC,
    -- Para SAT_NOTA: nota promedio de la sección (1-7)
    nota_promedio           NUMERIC
);

COMMENT ON TABLE consolidados.evaluacion_respuesta IS
'Respuestas en formato largo (una fila por evaluacion × pregunta).
 El indicador principal del proyecto es pregunta_id = ''SAT_NOTA''.
 Criterio CM-2 de calidad: SAT ponderado por n_alumnos_evaluaron.';


-- consolidados.participacion_formacion
-- ──────────────────────────────────────
-- FUENTE: etl/complementarios/etl_participacion_formacion.py
-- ORIGEN: archivos de Diplomados 2022-2025, Talleres 2023-2 a 2025-2,
--         Proyectos de Investigación
--
-- N DE FILAS: varía (una fila por docente × actividad de formación)
-- Un docente que hizo 2 diplomados y 1 taller tiene 3 filas.
--
-- TIPO DE FORMACIÓN:
--   DIPLOMADO  → anio_evento=YYYY, periodo_evento=NULL (anuales)
--   TALLER     → anio_evento=YYYY, periodo_evento=YYYY-SS (semestrales)
--   PROYECTO   → anio_evento=YYYY, periodo_evento=NULL (anuales)
--
-- PERIODOS TALLER VIGENTES (actualizado 2026-07-16):
--   2023-02 | 2024-01 | 2024-02 | 2025-01 | 2025-02

CREATE TABLE IF NOT EXISTS consolidados.participacion_formacion (
    pf_id                   BIGINT,      -- PK
    rut_key                 TEXT,        -- FK lógica → consolidados.docente.rut_key
    tipo_formacion          TEXT,        -- DIPLOMADO | TALLER | PROYECTO
    nombre_actividad        TEXT,        -- nombre del diplomado/taller/proyecto
    anio_evento             INTEGER,
    periodo_evento          TEXT,        -- NULL para anuales; YYYY-SS para talleres
    facultad                TEXT,
    carrera                 TEXT,
    sede                    TEXT
);

COMMENT ON TABLE consolidados.participacion_formacion IS
'Una fila por docente × evento de formación P3.
 Fuente de los universos analíticos universo_formados_p3 y universo_aptos_p3.';


-- consolidados.evaluacion_jefes
-- ───────────────────────────────
-- FUENTE: etl/complementarios/etl_consolidado_con_jefes.py
-- ORIGEN: archivo de Evaluación de Jefes (hoja separada del Excel maestro)
--
-- N DE FILAS: varía por docente
-- CAMPO CLAVE: tiene_eval_jefe = 'SI' | 'NO'

CREATE TABLE IF NOT EXISTS consolidados.evaluacion_jefes (
    ej_id                   BIGINT,
    rut_key                 TEXT,
    anio                    INTEGER,
    tiene_eval_jefe         TEXT,        -- 'SI' | 'NO'
    puntaje_jefe            NUMERIC
);


-- consolidados.calificacion_alumno
-- ──────────────────────────────────
-- FUENTE: etl/complementarios/etl_calificacion_alumno.py
-- ORIGEN: archivos de notas finales de alumnos por asignatura y sección
-- Usado en el análisis de aprobación y en el bloque EDD (Evaluación del Desempeño).

CREATE TABLE IF NOT EXISTS consolidados.calificacion_alumno (
    cal_id                  BIGINT,
    rut_alumno              TEXT,
    rut_docente             TEXT,
    periodo                 TEXT,
    cod_asignatura          TEXT,
    nombre_asignatura       TEXT,
    seccion                 TEXT,
    nota_final              NUMERIC,
    aprobado                BOOLEAN
);


-- consolidados.pregunta
-- ──────────────────────
-- FUENTE: etl/complementarios/etl_pregunta.py
-- Catálogo de preguntas del instrumento de evaluación estudiantil.
-- Referencia para los pregunta_id de evaluacion_respuesta.

CREATE TABLE IF NOT EXISTS consolidados.pregunta (
    pregunta_id             TEXT,        -- PK: APR_01 | MET_01 | AFO_01 | SAT_BIN | SAT_NOTA
    dimension               TEXT,        -- APRENDIZAJE | METODOLOGIA | AMBIENTE_FORMATIVO | SATISFACCION
    tipo_pregunta           TEXT,        -- LIKERT | BINARIO | NOTA
    texto_pregunta          TEXT,
    orden                   INTEGER
);


-- ============================================================
-- SCHEMA: analisis
-- Universos filtrados generados por ETL Python.
-- Cada tabla es reproducible corriendo el ETL correspondiente.
-- Convención de nombres: universo_* = subconjunto de docentes.
-- ============================================================

CREATE SCHEMA IF NOT EXISTS analisis;


-- analisis.universo_base
-- ────────────────────────
-- FUENTE: etl/00_base/etl_universo_base.py
-- FILTRO: RUT único de NOMINA ∪ DOTACION (FULL OUTER JOIN)
-- N esperado: ~985 RUTs únicos
--
-- CAMPO CLAVE: origen
--   AMBOS        → RUT en NOMINA y DOTACION (~520)
--   SOLO_NOMINA  → RUT solo en NOMINA (~437)
--   SOLO_DOTACION → RUT solo en DOTACION (~27, excluye ESPINOZA 16322128)
--
-- CAMPO CLAVE: tipo_contrato_tag
--   JORNADA | HONORARIO para todos los 985 RUTs.
--   Fuente: col "JORNADA/HONORARIO" de NOMINA para AMBOS y SOLO_NOMINA.
--   Fuente: diccionario CARGO_TAG (ver etl_universo_base.py) para SOLO_DOTACION.
--
-- CAMBIO METODOLÓGICO 2026-07-16:
--   Antes el universo base era solo los 520 AMBOS (docente_ambos).
--   Ahora incluye todos los RUTs únicos de ambas fuentes.
--   El campo origen permite reproducir el universo anterior con WHERE origen='AMBOS'.

CREATE TABLE IF NOT EXISTS analisis.universo_base (
    rut_key                 TEXT,        -- PK lógica: RUT sin dígito verificador
    origen                  TEXT,        -- AMBOS | SOLO_NOMINA | SOLO_DOTACION
    tipo_contrato_tag       TEXT,        -- JORNADA | HONORARIO
    nombre                  TEXT,
    sexo                    TEXT,        -- HOMBRE | MUJER (recodificado desde MASCULINO/FEMENINO)
    jerarquia               TEXT,        -- jerarquía académica (de NOMINA)
    jerarquia_dot           TEXT,        -- jerarquía académica (de DOTACION, si difiere)
    estamento               TEXT,
    funcion_principal       TEXT,
    departamento            TEXT,
    cargo_dot               TEXT,
    area_carrera            TEXT,
    unidad_facultad         TEXT,
    centro_costo            TEXT,
    ubicacion               TEXT,
    clasificacion           TEXT,
    fecha_ingreso           TEXT,
    fecha_retiro            TEXT,
    anio_ingreso            INTEGER,     -- año extraído de fecha_ingreso
    antiguedad_anios        NUMERIC,
    tramo_antiguedad        TEXT,        -- 0-4 | 5-9 | 10-14 | 15-19 | 20-24 | 25-29 | 30+
    fecha_nacimiento        TEXT,
    edad_anios              NUMERIC,
    tramo_edad              TEXT,        -- <30 | 30-34 | … | 70+
    jornada_dot             TEXT,
    nivel_formacion         TEXT,
    nombre_grado            TEXT,
    institucion_grado       TEXT,
    pais_grado              TEXT,
    fecha_jerarquizacion    TEXT,
    anio_jerarquizacion     INTEGER,
    observaciones_nomina    TEXT
);

COMMENT ON TABLE analisis.universo_base IS
'Universo analítico completo: ~985 RUTs únicos de NOMINA ∪ DOTACION.
 Todos tienen tipo_contrato_tag (JORNADA|HONORARIO) y ninguno tiene DESCONOCIDO.
 Excluye ESPINOZA RUT 16322128 (dos personas distintas, mismo RUT).';


-- analisis.universo_jornada
-- ───────────────────────────
-- FUENTE: etl/01_jornada/etl_jornada.py
-- FILTRO: universo_base WHERE tipo_contrato_tag = 'JORNADA'
-- N esperado: confirmar con ETL (mayoría de los 985)
-- Mismas columnas que universo_base.

CREATE TABLE IF NOT EXISTS analisis.universo_jornada
    (LIKE analisis.universo_base);

COMMENT ON TABLE analisis.universo_jornada IS
'Subconjunto de universo_base con tipo_contrato_tag = ''JORNADA''.';


-- analisis.universo_honorario
-- ─────────────────────────────
-- FUENTE: etl/02_honorario/etl_honorario.py
-- FILTRO: universo_base WHERE tipo_contrato_tag = 'HONORARIO'
-- N esperado: confirmar con ETL
-- Mismas columnas que universo_base.

CREATE TABLE IF NOT EXISTS analisis.universo_honorario
    (LIKE analisis.universo_base);

COMMENT ON TABLE analisis.universo_honorario IS
'Subconjunto de universo_base con tipo_contrato_tag = ''HONORARIO''.';


-- analisis.universo_jerarquizados
-- ─────────────────────────────────
-- FUENTE: etl/03_jerarquizados/etl_jerarquizados.py
-- FILTRO: universo_base WHERE jerarquia válida
--   (excluye SIN JERARQUÍA, SIN JERARQUIA, NO INFORMA, NULL, vacío)
-- N esperado: ~917
-- NOTA: Los jerarquizados son una RAMA PARALELA, NO un prerequisito para
--   universo_formados_p3 ni universo_aptos_p3. Un honorario sin jerarquía
--   puede haber participado en P3 y estar en formados_p3.
--
-- HISTÓRICO: El N era 918 antes de excluir ESPINOZA (RUT 16322128,
--   dos personas distintas identificadas en junio 2026). N correcto = 917.
--
-- COMPATIBILIDAD: El ETL también escribe docente_918.csv en
--   data/cascade/03_jerarquizados/ como alias para scripts legacy.

CREATE TABLE IF NOT EXISTS analisis.universo_jerarquizados
    (LIKE analisis.universo_base);

COMMENT ON TABLE analisis.universo_jerarquizados IS
'~917 docentes de universo_base con jerarquía académica válida.
 Rama paralela de análisis, no relacionada causalmente con formados_p3.
 Ver docs/CASCADE.md sección 3.';


-- analisis.universo_formados_p3
-- ───────────────────────────────
-- FUENTE: etl/04_formados_p3/etl_formados_p3.py
-- FILTRO: docentes de universo_base que participaron en ≥1 actividad P3
--   (Taller, Diplomado o Proyecto) según consolidados.participacion_formacion
-- N DE FILAS: uno por docente × evento de formación (no por docente único)
-- N de RUTs únicos: confirmar con ETL
--
-- CAMBIO METODOLÓGICO 2026-07-16:
--   Antes solo incluía los 520 AMBOS con jerarquía.
--   Ahora incluye TODO universo_base (985 RUTs): honorarios sin jerarquía
--   que participaron en P3 quedan incluidos correctamente.
--
-- PERIODOS TALLER VIGENTES (incluye 2025-01 y 2025-02 nuevos):
--   2023-02 → baseline 2023-01, resultado 2024-01
--   2024-01 → baseline 2023-02, resultado 2024-02
--   2024-02 → baseline 2024-01, resultado 2025-01
--   2025-01 → baseline 2024-02, resultado 2025-02  ← NUEVO
--   2025-02 → baseline 2025-01, resultado 2026-01  ← NUEVO (sin datos resultado aún)
--
-- CAMPO CLAVE: apto_p3
--   TRUE si el docente tiene SAT medido en AMBOS periodo_baseline Y periodo_resultado.
--   Un docente puede tener apto_p3=FALSE si le falta evaluación en uno de los periodos.

CREATE TABLE IF NOT EXISTS analisis.universo_formados_p3 (
    -- Perfil del docente (copiado desde universo_base)
    rut_key                 TEXT,
    nombre                  TEXT,
    sexo                    TEXT,
    jerarquia               TEXT,
    jerarquia_dot           TEXT,
    tipo_contrato           TEXT,
    tipo_contrato_tag       TEXT,
    unidad_facultad         TEXT,
    departamento            TEXT,
    nivel_formacion         TEXT,
    nombre_grado            TEXT,
    antiguedad_anios        NUMERIC,
    tramo_antiguedad        TEXT,
    edad_anios              NUMERIC,
    tramo_edad              TEXT,
    origen                  TEXT,        -- AMBOS | SOLO_NOMINA | SOLO_DOTACION
    -- Evento de formación
    tipo_formacion          TEXT,        -- DIPLOMADO | TALLER | PROYECTO
    nombre_actividad        TEXT,
    anio_evento             INTEGER,
    periodo_evento          TEXT,
    periodo_baseline        TEXT,        -- periodo SAT a comparar antes de la formación
    periodo_resultado       TEXT,        -- periodo SAT a comparar después de la formación
    -- Flags
    tiene_sat_baseline      BOOLEAN,
    tiene_sat_resultado     BOOLEAN,
    apto_p3                 BOOLEAN      -- TRUE = tiene_sat_baseline AND tiene_sat_resultado
);

COMMENT ON TABLE analisis.universo_formados_p3 IS
'Docentes de universo_base que participaron en ≥1 actividad P3.
 Una fila por docente × evento. apto_p3=TRUE cuando hay SAT medido en ambos periodos.
 Ver etl/04_formados_p3/etl_formados_p3.py para el mapeo completo de periodos.';


-- analisis.universo_aptos_p3
-- ────────────────────────────
-- FUENTE: etl/05_aptos_p3/etl_aptos_p3.py
-- FILTRO: universo_formados_p3 WHERE apto_p3 = true,
--   más cálculo de SAT crudo y z-score estandarizado
-- N DE FILAS: subconjunto de universo_formados_p3 (solo aptos)
--
-- COLUMNAS CLAVE:
--   sat_baseline / sat_resultado : SAT promedio ponderado (CM-2) en cada periodo
--   delta_sat   : sat_resultado - sat_baseline (escala 1-7)
--   z_baseline / z_resultado : z-score relativo a la unidad_facultad × periodo
--   delta_z     : z_resultado - z_baseline (indica mejora relativa al grupo de referencia)
--   mejoro_z    : TRUE si delta_z > 0
--
-- POBLACIÓN DE REFERENCIA PARA Z-SCORE:
--   universo_base completo (985 RUTs) con SAT medido.
--   Unidades con menos de 30 docentes se colapsan en "Otras" para estabilidad.

CREATE TABLE IF NOT EXISTS analisis.universo_aptos_p3 (
    -- Perfil
    rut_key                 TEXT,
    nombre                  TEXT,
    sexo                    TEXT,
    jerarquia               TEXT,
    jerarquia_dot           TEXT,
    tipo_contrato_tag       TEXT,
    unidad_facultad         TEXT,
    nivel_formacion         TEXT,
    antiguedad_anios        NUMERIC,
    tramo_antiguedad        TEXT,
    edad_anios              NUMERIC,
    tramo_edad              TEXT,
    origen                  TEXT,
    -- Resumen de formación
    n_instancias            INTEGER,     -- cuántos eventos de formación tiene
    tipos_formacion         TEXT,        -- TALLER | DIPLOMADO | PROYECTO | combinaciones
    n_taller                INTEGER,
    n_diplomado             INTEGER,
    n_proyecto              INTEGER,
    -- Métricas SAT
    sat_baseline            NUMERIC,
    sat_resultado           NUMERIC,
    delta_sat               NUMERIC,
    z_baseline              NUMERIC,
    z_base_mu               NUMERIC,     -- media del grupo de referencia
    z_base_sigma            NUMERIC,     -- desviación estándar del grupo de referencia
    z_resultado             NUMERIC,
    z_res_mu                NUMERIC,
    z_res_sigma             NUMERIC,
    delta_z                 NUMERIC,
    mejoro_sat              BOOLEAN,
    mejoro_z                BOOLEAN
);

COMMENT ON TABLE analisis.universo_aptos_p3 IS
'Docentes con apto_p3=TRUE más z-score SAT calculado.
 Una fila por docente único (las métricas de múltiples eventos se promedian).
 Ver etl/05_aptos_p3/etl_aptos_p3.py para el cálculo del z-score.';


-- analisis.p3_grupo_tratamiento
-- ───────────────────────────────
-- FUENTE: etl/complementarios/etl_p3_grupo_tratamiento.py
-- FILTRO: docentes de universo_base × todos sus eventos P3
--   (incluye tiene_eval_jefe además de tiene_eval_alumnos_*)
-- N DE FILAS: similar a universo_formados_p3 pero con columna adicional de eval jefes
-- Diferencia vs universo_formados_p3:
--   universo_formados_p3 → fuente oficial de análisis P3
--   p3_grupo_tratamiento → tabla complementaria con flag de evaluación de jefes,
--     útil para cruces con el bloque EDD (Evaluación del Desempeño Docente)

CREATE TABLE IF NOT EXISTS analisis.p3_grupo_tratamiento (
    -- Perfil (desde universo_base)
    rut_key                 TEXT,
    nombre                  TEXT,
    sexo                    TEXT,
    jerarquia               TEXT,
    jerarquia_dot           TEXT,
    tipo_contrato_tag       TEXT,
    departamento            TEXT,
    area_carrera            TEXT,
    unidad_facultad         TEXT,
    nivel_formacion         TEXT,
    antiguedad_anios        NUMERIC,
    tramo_antiguedad        TEXT,
    edad_anios              NUMERIC,
    tramo_edad              TEXT,
    origen                  TEXT,
    -- Evento
    tipo_formacion          TEXT,
    nombre_actividad        TEXT,
    anio_evento             INTEGER,
    periodo_evento          TEXT,
    periodo_baseline        TEXT,
    periodo_resultado       TEXT,
    -- Flags
    tiene_eval_alumnos_baseline  BOOLEAN,
    tiene_eval_alumnos_resultado BOOLEAN,
    tiene_eval_jefe              BOOLEAN,
    apto_p3                      BOOLEAN
);


-- ============================================================
-- SCHEMA: intel
-- Resultados estadísticos derivados. Generados por los ETL
-- de etl/complementarios/etl_intel_*.py.
-- Son la capa más al final del pipeline: dependen de analisis.*.
-- ============================================================

CREATE SCHEMA IF NOT EXISTS intel;


-- intel.prepost_sat
-- ──────────────────
-- FUENTE: etl/complementarios/etl_intel_prepost_sat.py
-- FILTRO: analisis.p3_grupo_tratamiento WHERE apto_p3 = true
-- Una fila por docente × evento de formación.
-- Añade nota_durante (SAT en el período del propio evento formativo).

CREATE TABLE IF NOT EXISTS intel.prepost_sat (
    rut_key                 TEXT,
    tipo_formacion          TEXT,
    nombre_actividad        TEXT,
    anio_evento             INTEGER,
    periodo_evento          TEXT,
    periodo_baseline        TEXT,
    periodo_durante         TEXT,        -- el semestre del propio evento
    periodo_resultado       TEXT,
    nota_pre                NUMERIC,
    nota_durante            NUMERIC,
    nota_post               NUMERIC,
    delta_pre_post          NUMERIC      -- nota_post - nota_pre
);

COMMENT ON TABLE intel.prepost_sat IS
'SAT en 3 momentos (pre, durante, post) para los docentes aptos_p3.
 Insumo principal del análisis de impacto del programa P3.';


-- intel.notas_docente
-- ──────────────────────
-- FUENTE: etl/complementarios/etl_intel_notas_docente.py
-- Agrega notas de alumnos por docente × periodo.
-- Permite analizar si las notas que pone el docente cambian post-formación.

CREATE TABLE IF NOT EXISTS intel.notas_docente (
    rut_key                 TEXT,
    periodo                 TEXT,
    n_alumnos               INTEGER,
    nota_promedio           NUMERIC,
    nota_mediana            NUMERIC,
    pct_aprobacion          NUMERIC
);


-- intel.trayectoria_alumno
-- ──────────────────────────
-- FUENTE: etl/complementarios/etl_intel_trayectoria_alumno.py
-- Seguimiento de alumnos que tomaron cursos con docentes P3 formados.

CREATE TABLE IF NOT EXISTS intel.trayectoria_alumno (
    rut_alumno              TEXT,
    rut_docente             TEXT,
    periodo_curso           TEXT,
    periodo_seguimiento     TEXT,
    nota_en_curso           NUMERIC,
    nota_en_siguiente       NUMERIC,
    delta_nota              NUMERIC,
    docente_formado         BOOLEAN      -- TRUE si el docente estaba formado en ese periodo
);


-- ============================================================
-- TABLAS LEGACY (NO USAR EN ANÁLISIS NUEVOS)
-- Dejadas en DB por compatibilidad hasta confirmar migración completa.
-- Reemplazadas por analisis.universo_base y derivadas.
-- ============================================================

-- analisis.docente_ambos        → REEMPLAZADA por analisis.universo_base (WHERE origen='AMBOS')
-- analisis.docente_solo_nomina  → REEMPLAZADA por analisis.universo_base (WHERE origen='SOLO_NOMINA')
-- analisis.docente_solo_dotacion → REEMPLAZADA por analisis.universo_base (WHERE origen='SOLO_DOTACION')

-- Para eliminarlas una vez validada la migración:
-- DROP TABLE IF EXISTS analisis.docente_ambos;
-- DROP TABLE IF EXISTS analisis.docente_solo_nomina;
-- DROP TABLE IF EXISTS analisis.docente_solo_dotacion;
-- DROP TABLE IF EXISTS analisis.docente_solo_evaluaciones;


-- ============================================================
-- CONSULTAS DE VALIDACIÓN RÁPIDA
-- Pegar en pgAdmin o psql para verificar conteos esperados.
-- ============================================================

/*
-- Conteo por origen (esperar AMBOS~520, SOLO_NOMINA~437, SOLO_DOTACION~27, TOTAL~985)
SELECT origen, COUNT(*) FROM analisis.universo_base GROUP BY 1 ORDER BY 1;

-- Conteo por tipo_contrato_tag (no debe haber DESCONOCIDO)
SELECT tipo_contrato_tag, COUNT(*) FROM analisis.universo_base GROUP BY 1;

-- Jerarquizados (esperar ~917)
SELECT COUNT(*) FROM analisis.universo_jerarquizados;

-- Formados P3 (RUTs únicos)
SELECT COUNT(DISTINCT rut_key) FROM analisis.universo_formados_p3;

-- Aptos P3 (RUTs únicos con análisis SAT completo)
SELECT COUNT(*) FROM analisis.universo_aptos_p3;

-- Periodos taller cubiertos
SELECT DISTINCT periodo_evento
FROM analisis.universo_formados_p3
WHERE tipo_formacion = 'TALLER'
ORDER BY 1;
-- Esperar: 2023-02, 2024-01, 2024-02, 2025-01, 2025-02
*/
