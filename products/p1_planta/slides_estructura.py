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
alumnos la docencia, no quién es el docente). Bloque IV todavía no tiene
contenido — sus cajas quedan con texto placeholder ("sin avance aún"), no se
inventan datos.

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
    """Apertura: resumen Bloque III (con contenido) + Bloque IV (sin definir todavía)."""
    sl = _nueva(prs)
    kit.title(sl, "Bloque III — Aprobación y Reprobación de Alumnos", fs=17)
    kit.subtitulo(sl, "Universo: 624 docentes Jornada  ·  515 con calificaciones registradas (82.5%)")
    cajas = [
        ("Bloque III — Aprobación y Reprobación de Alumnos",
         "• Universo: 624 docentes Jornada, 515 con calificaciones registradas\n"
         "• % de aprobación/reprobación global, por sexo, por escalafón "
         "(Docente/Regular) y por antigüedad\n"
         "• Pruebas t de significancia estadística por corte\n"
         "• Evolución de la tasa de aprobación por sexo, 2023-2025"),
        ("Bloque IV — Pendiente de definir",
         "Sin avance aún."),
        ("Qué vas a ver en Bloque III",
         "1. % Aprobación/Reprobación — global\n"
         "2. Según sexo del docente + prueba t\n"
         "3. Según escalafón (Docente/Regular) + prueba t\n"
         "4. Según antigüedad (2 variantes: 4 y 3 tramos)\n"
         "5. Evolución de la tasa de aprobación por sexo (2023-2025)"),
        ("Qué vas a ver en Bloque IV",
         "Pendiente."),
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
        ],
        hallazgos_items=[
            "El 88.5% de las calificaciones de alumnos de docentes Jornada "
            "corresponde a aprobación (N°=134.640 calificaciones evaluables).",
            "Las docentes mujeres tienen mayor % de aprobación que los hombres "
            "(91.1% vs 87.7%) — diferencia estadísticamente significativa "
            "(prueba t de Welch, p=0.0016).",
            "Los docentes de escalafón Docente aprueban más que los de "
            "escalafón Regular (90.5% vs 84.3%, p=0.0008); en cambio, ni la "
            "edad ni la antigüedad mostraron diferencias significativas.",
        ])
    return sl
