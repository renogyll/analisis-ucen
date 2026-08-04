"""
P1 — Caracterización del Cuerpo Académico de Planta
Diapositivas estructurales del consolidado: portada, grillas de apertura por bloque,
y las diapositivas "Universo / Índice / Hallazgos" de cada bloque.

Mismo patrón visual que usaba P3 (`generar_presentacion_v2.py`: `slide_01`, `_grid_2x2`,
`_uih_slide`), pero construido sobre `UcenSlideKit` (`shared/pptx_helpers.py`) en vez de
duplicar los helpers de bajo nivel — los 3 layouts nuevos (`portada`, `caja_grid_2x2`,
`caja_universo_indice_hallazgos`) viven ahí para que cualquier bloque futuro (II, IV...)
los reuse sin copiar código.

Bloque I = caracterización demográfica del docente (sexo/edad, jerarquía, grado
académico). Bloque II = evaluación estudiantil por dimensión (APR/MET/AFO) —
reclasificado 2026-08-03: originalmente vivía dentro de Bloque I, se separó a
pedido de la contraparte porque conceptualmente es otro tema (cómo evalúan los
alumnos la docencia, no quién es el docente); desde 2026-08-04 también cierra
con `distribucion_horas/` (jornada completa/parcial, D30) — no es evaluación
estudiantil en sentido estricto, pero se integró ahí a pedido explícito de la
contraparte, a continuación de lo que ya había en Bloque II. Bloque III =
aprobación/reprobación de alumnos. Bloque IV = Evaluación de Desempeño Docente
(EDD, D28/D29) — agregado 2026-08-04, evaluación hecha por la jefatura/director,
distinta de la de Bloque II; desde el mismo día también cierra con
`participacion_formacion_*/` (D31, participación en Taller/Diplomado/Proyecto) —
tampoco es EDD en sentido estricto, mismo criterio de integración que
`distribucion_horas/` en Bloque II, a pedido explícito de la contraparte.

Llamado por `generar_presentacion.py`, no standalone (no tiene bloque `__main__`
propio — no hay "un tema" que generar solo, son piezas de armado del consolidado).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "shared"))
from pptx_helpers import UcenSlideKit

HERE = Path(__file__).parent
kit = UcenSlideKit(out_dir=HERE)


def _nueva(prs):
    kit.ensure_bg()
    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    return sl


def portada(prs):
    sl = _nueva(prs)
    kit.portada(sl,
        titulo="Resultados del Perfeccionamiento Docente",
        subtitulo1="Análisis de Incidencia",
        footer_lines=["Universidad Central",
                      "Producto 1: Caracterización Cuerpo Académico Jornada",
                      "Agosto 2026"])
    return sl


def grid_b1_b2(prs):
    """Apertura: resumen Bloque I (caracterización demográfica) + Bloque II (evaluación estudiantil)."""
    sl = _nueva(prs)
    kit.title(sl, "Bloques I y II — Caracterización y Evaluación Estudiantil", fs=17)
    kit.subtitulo(sl, "Universo: 624 docentes Jornada")
    cajas = [
        ("Bloque I — Caracterización del Cuerpo Académico",
         "• Universo: 624 docentes Jornada\n"
         "• Sexo y tramo de edad, edad por jerarquía, grado académico por sexo"),
        ("Bloque II — Evaluación Estudiantil por Dimensión",
         "• Universo: 624 docentes Jornada, 6 semestres (2023-01 a 2025-02)\n"
         "• Dimensiones del instrumento: Aprendizajes (APR), Metodologías y "
         "Evaluación (MET), Aspectos Formales (AFO)\n"
         "• % Acuerdo / % Desacuerdo por pregunta, evolución semestral"),
        ("Qué vas a ver en Bloque I",
         "1. Distribución por sexo y tramo de edad\n"
         "2. Edad promedio por jerarquía\n"
         "3. Grado académico por sexo"),
        ("Qué vas a ver en Bloque II",
         "1. Dimensión Aprendizajes (APR)\n"
         "2. Dimensión Metodologías y Evaluación (MET, 2 diapositivas)\n"
         "3. Dimensión Aspectos Formales (AFO, 3 diapositivas)"),
    ]
    kit.caja_grid_2x2(sl, cajas)
    return sl


def grid_b3(prs):
    """Apertura: resumen Bloque III (aprobación/reprobación) + Bloque IV (EDD)."""
    sl = _nueva(prs)
    kit.title(sl, "Bloques III y IV — Rendimiento Académico y Evaluación de Desempeño Docente", fs=15)
    kit.subtitulo(sl, "Universo: 624 docentes Jornada")
    cajas = [
        ("Bloque III — Aprobación y Reprobación de Alumnos",
         "• Universo: 624 docentes Jornada, 515 con calificaciones registradas\n"
         "• % de aprobación/reprobación global, por sexo, por escalafón "
         "(Docente/Regular) y por antigüedad\n"
         "• Pruebas t de significancia estadística por corte\n"
         "• Evolución de la tasa de aprobación por sexo, 2023-2025"),
        ("Bloque IV — EDD y Participación en Instancias Formativas",
         "• Universo: 624 docentes Jornada, 491 con evaluación EDD 2022-2025 "
         "(hecha por la jefatura/director — distinta de la evaluación estudiantil "
         "de Bloque II)\n"
         "• Calificación EDD promedio según sexo, escalafón y facultad\n"
         "• Participación en instancias formativas (Taller/Diplomado/Proyecto) "
         "según sexo, escalafón y edad\n"
         "• Pruebas t de Welch por corte"),
        ("Qué vas a ver en Bloque III",
         "1. % Aprobación/Reprobación — global\n"
         "2. Según sexo del docente + prueba t\n"
         "3. Según escalafón (Docente/Regular) + prueba t\n"
         "4. Según antigüedad (2 variantes: 4 y 3 tramos)\n"
         "5. Evolución de la tasa de aprobación por sexo (2023-2025)\n"
         "6. Grupos de dificultad de asignaturas: composición, y antigüedad/edad/"
         "sexo según grupo, cada uno con su prueba t"),
        ("Qué vas a ver en Bloque IV",
         "1. Calificación EDD según sexo del docente + prueba t\n"
         "2. Calificación EDD según escalafón (Docente/Regular) + prueba t\n"
         "3. Calificación EDD según facultad + 6 pruebas t (cada facultad vs. "
         "el resto)\n"
         "4. Participación en instancias formativas según sexo + prueba t\n"
         "5. Según escalafón (Docente/Regular) + prueba t\n"
         "6. Según tramo de edad (sin prueba t — no significativa)"),
    ]
    kit.caja_grid_2x2(sl, cajas)
    return sl


def uih_b1(prs):
    sl = _nueva(prs)
    kit.title(sl, "Bloque I — Caracterización del Cuerpo Académico de Jornada (N°624)", fs=16)
    kit.caja_universo_indice_hallazgos(sl,
        universo_txt=(
            "624 docentes con contrato de Jornada (planta), sub-universo de "
            "analisis.universo_base (1.144 docentes totales). Es el universo de "
            "trabajo de todo el Producto 1. Este bloque caracteriza quién es el "
            "docente de Jornada — sexo, edad, jerarquía y grado académico."),
        indice_items=[
            "Distribución por Sexo y Tramo de Edad",
            "Edad Promedio por Jerarquía",
            "Grado Académico por Sexo",
        ],
        hallazgos_items=[
            "Las mujeres son mayoría en el cuerpo académico Jornada (273 vs 240 "
            "hombres), pero su representación cae en el grado más alto: son 53% "
            "del universo con dato pero solo 46% de quienes tienen Doctorado.",
            "La edad promedio aumenta de forma consistente con la jerarquía "
            "académica: de 41 años en Instructor a 67 años en Titular Docente.",
        ])
    return sl


def uih_b2(prs):
    sl = _nueva(prs)
    kit.title(sl, "Bloque II — Evaluación Estudiantil por Dimensión (N°624)", fs=16)
    kit.caja_universo_indice_hallazgos(sl,
        universo_txt=(
            "624 docentes Jornada, 6 semestres (2023-01 a 2025-02). Instrumento "
            "de evaluación estudiantil, 3 dimensiones: Aprendizajes (APR, 3 "
            "preguntas), Metodologías y Evaluación (MET, 5 preguntas), Aspectos "
            "Formales (AFO, 9 preguntas). Solo secciones con cobertura ≥40% "
            "(ver docs/DECISIONES_METODOLOGICAS.md D10); % ponderado por alumnos "
            "evaluadores (D11). Se descarta la respuesta \"indiferente\"."),
        indice_items=[
            "Dimensión Aprendizajes (APR_01-03)",
            "Dimensión Metodologías y Evaluación (MET_01-02)",
            "Dimensión Metodologías y Evaluación (MET_03-05)",
            "Dimensión Aspectos Formales (AFO_01-03)",
            "Dimensión Aspectos Formales (AFO_04-06)",
            "Dimensión Aspectos Formales (AFO_07-09)",
        ],
        hallazgos_items=[
            "Tendencia positiva y estable en las 3 dimensiones entre 2023 y "
            "2025: el % de acuerdo se mantiene sobre 83% y el % de desacuerdo "
            "baja de forma sostenida en las 17 preguntas del instrumento.",
            "AFO_07 (\"Entrega evaluaciones a tiempo\") y MET_02/MET_03 "
            "(evaluación y metodología) son las preguntas con mayor % de "
            "desacuerdo relativo — las más \"duras\" del instrumento.",
        ])
    return sl


def uih_b3(prs):
    sl = _nueva(prs)
    kit.title(sl, "Bloque III — Aprobación y Reprobación de Alumnos (N°624)", fs=16)
    kit.caja_universo_indice_hallazgos(sl,
        universo_txt=(
            "624 docentes de Jornada, de los cuales 515 (82.5%) tienen al menos "
            "una calificación de alumnos registrada en el período 2023-01 a "
            "2025-02. % de aprobación calculado sobre calificaciones evaluables "
            "(se excluyen estados administrativos como No Presentado o "
            "Postergado — ver docs/DECISIONES_METODOLOGICAS.md D26)."),
        indice_items=[
            "% de Aprobación y Reprobación — global",
            "% de Aprobación y Reprobación según Sexo del Docente + prueba t",
            "% de Aprobación y Reprobación según Escalafón (Docente/Regular) + prueba t",
            "% de Aprobación y Reprobación según Antigüedad — variante 4 tramos",
            "% de Aprobación y Reprobación según Antigüedad — variante 3 tramos",
            "Evolución de la Tasa de Aprobación por Sexo del Docente (2023-2025)",
            "Composición de los Grupos de Dificultad de Asignaturas",
            "Antigüedad según Grupo de Dificultad + prueba t",
            "Edad según Grupo de Dificultad + prueba t",
            "Sexo según Grupo de Dificultad + prueba t",
        ],
        hallazgos_items=[
            "El 88.5% de las calificaciones de alumnos de docentes Jornada "
            "corresponde a aprobación (N°=134.640 calificaciones evaluables).",
            "Las docentes mujeres tienen mayor % de aprobación que los hombres "
            "(91.1% vs 87.7%) — diferencia estadísticamente significativa "
            "(prueba t de Welch, p=0.0016).",
            "Los docentes de escalafón Docente aprueban más que los de "
            "escalafón Regular (90.5% vs 84.3%, p=0.0008); según tramo de edad "
            "o de antigüedad (frente a % de aprobación directo) no hubo "
            "diferencias significativas.",
            "Controlando por dificultad de la asignatura (D27): los docentes "
            "de asignaturas de baja aprobación histórica son más frecuentemente "
            "hombres (56% vs 39% en el resto, p=0.0001), y en promedio mayores "
            "y con más antigüedad. El escalafón no mostró diferencia "
            "significativa por dificultad (p=0.0716) — se probó pero no se "
            "incluyó como diapositiva, ver D27.",
        ])
    return sl


def uih_b4(prs):
    sl = _nueva(prs)
    kit.title(sl, "Bloque IV — EDD y Participación en Instancias Formativas (N°624)", fs=15)
    kit.caja_universo_indice_hallazgos(sl,
        universo_txt=(
            "624 docentes de Jornada. 491 (78.7%) tienen al menos una evaluación de "
            "desempeño docente (EDD) registrada entre 2022 y 2025 — la hace la "
            "jefatura/director, distinta de la evaluación estudiantil de Bloque II "
            "(D28/D29). 418 (67.0%) participaron en al menos una instancia formativa "
            "(Taller/Diplomado/Proyecto) — fuente analisis.universo_formados_p3, sin "
            "filtrar a apto_p3 (D31). Unidad de análisis en ambos casos: 1 valor por "
            "docente — ver docs/DECISIONES_METODOLOGICAS.md D28/D29/D31."),
        indice_items=[
            "Calificación EDD según Sexo del Docente + prueba t",
            "Calificación EDD según Jerarquía (8 categorías) / Escalafón + prueba t",
            "Calificación EDD según Facultad + 6 pruebas t (cada facultad vs. el resto)",
            "Participación en Instancias Formativas según Sexo + prueba t",
            "Participación en Instancias Formativas según Jerarquía / Escalafón + prueba t",
            "Participación en Instancias Formativas según Tramo de Edad",
        ],
        hallazgos_items=[
            "Los docentes hombres tienen una calificación EDD promedio más alta que "
            "las mujeres (0.72 vs 0.66, p=0.0183) — dirección opuesta a la evaluación "
            "estudiantil de Bloque II, donde las mujeres puntúan más alto.",
            "El escalafón Docente tiene una calificación EDD promedio más alta que el "
            "escalafón Regular (0.71 vs 0.59, p=0.0011); por facultad, 4 de 6 muestran "
            "diferencia significativa frente al resto (FACDEH/FINARQ por encima, "
            "FAMEDSA/VRIIP por debajo — sin corrección por comparaciones múltiples, D29).",
            "Las docentes mujeres participan más en instancias formativas que los "
            "hombres (74.4% vs 62.4%, p=0.0016), y el escalafón Docente mucho más que "
            "el Regular (76.5% vs 48.9%, p<0.0001) — la edad no mostró diferencia "
            "significativa (p=0.0724).",
        ])
    return sl
