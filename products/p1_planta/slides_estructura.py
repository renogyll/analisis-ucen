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
                      "Septiembre 2026"])
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


def grid_bloques(prs):
    """Apertura única (2026-09-25): 4 franjas horizontales, una por bloque, en el orden de la
    contraparte. Revisión 2026-09-26: período de cada bloque (obs. 12) y listas alineadas con las
    diapositivas fundidas (obs. 21)."""
    sl = _nueva(prs)
    kit.title(sl, "Contenido de la presentación — Bloques I a IV", fs=17)
    kit.subtitulo(sl, "Universo: 624 docentes Jornada  ·  cada bloque indica su período de datos")
    kit.franjas_bloques(sl, [
        ("Bloque I — Caracterización del cuerpo académico",
         ["Universo: 624 docentes Jornada",
          "Período: dotación vigente; carga académica según archivo de mayo 2026"],
         ["Sexo y tramo de edad · edad y trayectoria según jerarquía",
          "Unidad/facultad · carga académica · grado académico según sexo",
          "Jornada completa/parcial: composición y según sexo"]),
        ("Bloque II — Análisis de la participación en el perfeccionamiento docente",
         ["Universo: 624 docentes Jornada, 418 (67.0%) con al menos una instancia formativa "
          "(Oferta formativa (Taller), Diplomado o Proyecto)",
          "Período: 2022-2025 (el 74% de los registros son de 2025)"],
         ["Participación y modalidades · tipos (Venn) · intensidad",
          "Participación según sexo, jerarquía/escalafón y facultad",
          "Antigüedad de los formados · participación según edad",
          "Tipo de formación según antigüedad, sexo y edad"]),
        ("Bloque III — Evaluación de Desempeño Docente (EDD)",
         ["Universo: 624 docentes Jornada, 491 con EDD (hecha por la jefatura, distinta de la "
          "evaluación que hacen los estudiantes)",
          "Período: 2022-2025, EDD ajustada por año por un cambio de escala en 2024"],
         ["EDD por año y sexo",
          "EDD según sexo, jerarquía/escalafón y facultad, con sus pruebas"]),
        ("Bloque IV — Aprobación y reprobación de alumnos",
         ["Universo: 624 docentes Jornada, 515 con calificaciones registradas",
          "Período: 2023-01 a 2025-02"],
         ["Aprobación global · según sexo (y dentro de cada grupo de dificultad) · escalafón · antigüedad",
          "Evolución de la aprobación según sexo (2023-2025)",
          "Grupos de dificultad: composición, y antigüedad/edad/sexo según grupo",
          "Anexo: resumen de todas las pruebas estadísticas"]),
    ])
    return sl


# ── Anexo: resumen de pruebas estadísticas (revisión 2026-09-26, obs. 6-7) ────────
# El deck mostraba solo las pruebas significativas; esta tabla reúne TODAS las del P1
# (incluidas las no significativas) y agrega el valor p ajustado por Holm, que corrige por
# hacer muchas comparaciones a la vez. Cada script expone su lista `PRUEBAS`.

def _holm(pvals):
    orden = sorted(range(len(pvals)), key=lambda i: pvals[i])
    m = len(pvals); ajust = [0.0] * m; previo = 0.0
    for rango, i in enumerate(orden):
        previo = max(previo, min(1.0, (m - rango) * pvals[i]))
        ajust[i] = previo
    return ajust


def _fmt_p(p):
    return "<0.0001" if p < 0.0001 else f"{p:.4f}"


def holm_por_bloque(pruebas):
    """p ajustado por Holm DENTRO de cada bloque (familia de pruebas), no sobre el total.
    Decisión del usuario 2026-09-26: Holm sobre las 21 pruebas juntas era demasiado estricto
    (mezcla preguntas de bloques distintos); lo habitual es corregir por familia."""
    ajust = [None] * len(pruebas)
    for bloque in dict.fromkeys(pr["bloque"] for pr in pruebas):
        idx = [i for i, pr in enumerate(pruebas) if pr["bloque"] == bloque]
        for i, h in zip(idx, _holm([pruebas[i]["p"] for i in idx])):
            ajust[i] = h
    return ajust


def anexo_pruebas(prs, pruebas, holm, por_diapo=12):
    """Una o más diapositivas de tabla con todas las pruebas; filas doradas = significativas
    al 5% después del ajuste de Holm por bloque."""
    filas = [[pr["bloque"], pr["comparacion"], pr["resultado"], pr["n"], pr["prueba"],
              _fmt_p(pr["p"]), _fmt_p(h), "Sí" if h < 0.05 else "No"]
             for pr, h in zip(pruebas, holm)]
    n_sig, n_sig_holm = sum(pr["p"] < 0.05 for pr in pruebas), sum(h < 0.05 for h in holm)
    partes = [filas[i:i + por_diapo] for i in range(0, len(filas), por_diapo)]
    slides = []
    for k, parte in enumerate(partes):
        sl = _nueva(prs)
        sufijo = f" ({k + 1}/{len(partes)})" if len(partes) > 1 else ""
        kit.title(sl, f"Anexo — Resumen de pruebas estadísticas{sufijo}", fs=18)
        kit.subtitulo(sl, f"{len(pruebas)} pruebas en total: {n_sig} significativas al 5% sin ajuste, "
                          f"{n_sig_holm} tras el ajuste de Holm por bloque (en dorado)")
        kit.tabla(sl, ["Bloque", "Comparación", "Resultado", "N°", "Prueba", "p",
                       "p ajustado (Holm por bloque)", "¿Signif.? (Holm)"],
                  parte, anchos=[0.10, 0.32, 0.17, 0.05, 0.10, 0.07, 0.09, 0.10], fs=8.5,
                  resaltar=lambda i, parte=parte: parte[i][-1] == "Sí")
        kit.notas(sl,
            "Ajuste de Holm por bloque: dentro de cada bloque, ordena los p de menor a mayor y multiplica "
            "cada uno por el número de pruebas que quedan; controla la probabilidad de declarar significativa "
            "al menos una diferencia que no lo es dentro de esa familia de preguntas. Todas las pruebas usan "
            "1 valor por docente. Incluye las no significativas que no tienen diapositiva propia (escalafón "
            "según grupo de dificultad).")
        slides.append(sl)
    return slides


def marcar_no_sostenidas(slides_por_modulo, pruebas, holm):
    """Agrega un aviso al punteo de las diapositivas cuyo resultado era significativo sin ajuste
    pero deja de serlo con Holm por bloque (decisión del usuario 2026-09-26). El aviso va en la
    última diapositiva que generó el script de esa prueba."""
    from pptx.util import Pt
    from pptx.dml.color import RGBColor
    from pptx_helpers import formato_cl
    avisos = {}
    for pr, h in zip(pruebas, holm):
        if pr["p"] < 0.05 and h >= 0.05:
            avisos.setdefault(pr["carpeta"], []).append((pr, h))
    for carpeta, lista in avisos.items():
        sl = slides_por_modulo[carpeta][-1]
        cuerpo = [sh for sh in sl.shapes if sh.has_text_frame and sh.text_frame.text.startswith("1.")]
        if not cuerpo:
            continue
        if len(lista) == 1:
            texto = (f"⚠ Con la corrección de Holm por bloque esta diferencia deja de ser significativa "
                     f"(p ajustado={lista[0][1]:.2f}): tomarla como indicio, no como hallazgo firme.")
        else:
            nombres = ", ".join(pr["comparacion"].split(": ")[-1].replace(" vs resto", "") for pr, _ in lista)
            punto = "" if nombres.endswith(".") else "."    # "Economía, Gob. y Com." ya termina en punto
            texto = (f"⚠ Con la corrección de Holm por bloque dejan de ser significativas: {nombres}{punto} "
                     f"Tomarlas como indicio, no como hallazgo firme.")
        tf = cuerpo[0].text_frame
        ref = tf.paragraphs[0].runs[0].font
        p = tf.add_paragraph(); p.space_before = Pt(4)
        run = p.add_run(); run.text = formato_cl(texto)
        # blanco en negrita: el dorado se leía mal sobre la parte clara (inferior) del fondo
        run.font.size = ref.size; run.font.name = ref.name; run.font.bold = True
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    return avisos


# ── Universo / Índice / Hallazgos por bloque (2026-09-26) ─────────────────────
# Reorden acordado con el usuario: los 4 bloques abren con su UIH en formato franjas y
# siguen el orden que anuncia la grilla (I Caracterización, II Participación, III EDD,
# IV Aprobación). Referencias internas (D-números, tablas) van a notas del orador, no en
# pantalla. Hallazgos = cifras ya impresas por cada script del bloque.

def uih_b1(prs):
    sl = _nueva(prs)
    kit.title(sl, "Bloque I — Caracterización del cuerpo académico de Jornada (N°624)", fs=16)
    kit.franjas_universo_indice_hallazgos(sl,
        universo_txt=(
            "624 docentes con contrato de Jornada (planta), universo de todo el Producto 1. "
            "Jerarquía = 8 categorías (Instructor a Titular, cada una Docente o Regular); escalafón = "
            "Docente o Regular. 90 docentes (14%) no tienen registro en dotación (sin edad, antigüedad, "
            "cargo ni jornada): son más mujeres (66% vs 51%) y menos Regulares (7% vs 16%)."),
        indice_items=[
            "Distribución por sexo y tramo de edad",
            "Distribución de la edad según jerarquía",
            "Años de trayectoria según jerarquía",
            "Distribución por unidad/facultad",
            "Distribución de la carga académica",
            "Grado académico según sexo",
            "Composición de la jornada (horas semanales)",
            "Jornada completa/parcial según sexo",
        ],
        hallazgos_items=[
            "Las mujeres son mayoría (53% con dato), pero solo el 46% de los Doctores.",
            "Edad y trayectoria crecen con la jerarquía: de 41.2 a 67.3 años de edad y de 3.2 a 14.9 "
            "años en la universidad entre Instructor Docente y Titular Docente.",
            "Medicina y C. Salud concentra el 32% de los docentes; Docencia es la función principal del 49%.",
            "Los hombres tienen jornada completa con más frecuencia que las mujeres (82% vs 75%).",
        ])
    kit.notas(sl,
        "Universo: sub-universo Jornada de analisis.universo_base (1,144 docentes totales). Los 90 sin "
        "dotación (brecha NOMINA→DOTACION, D22/D23) quedan fuera de los gráficos de edad, antigüedad, "
        "carga académica y jornada; el 81% tampoco tiene unidad registrada. Su tasa de participación en "
        "formación es igual al resto (66% vs 67%).")
    return sl


def uih_b2(prs):
    sl = _nueva(prs)
    kit.title(sl, "Bloque II — Participación en el perfeccionamiento docente (N°624)", fs=16)
    kit.franjas_universo_indice_hallazgos(sl,
        universo_txt=(
            "624 docentes Jornada; 418 (67%) cursaron al menos una instancia formativa: Oferta "
            "formativa (Taller), Diplomado o Proyecto, entre 2022 y 2025. Primero, cuánto y cómo "
            "participan; después, quién participa, con su prueba estadística en la misma diapositiva."),
        indice_items=[
            "Participación y modalidades de formación",
            "Tipos de formación (Venn)",
            "Intensidad de participación",
            "Participación según sexo",
            "Participación según jerarquía / escalafón",
            "Participación según facultad",
            "Antigüedad de los docentes formados",
            "Participación según tramo de edad",
            "Tipo de formación según antigüedad, sexo y edad",
        ],
        hallazgos_items=[
            "67% participa; entre ellos, 61% solo en Oferta formativa y 30% combina 2 o más tipos "
            "(Participación Mixta). La mitad cursó 3 o más instancias.",
            "Las mujeres participan más que los hombres (74% vs 62%, p=0.0016) y el escalafón Docente "
            "mucho más que el Regular (77% vs 49%, p<0.0001).",
            "Por facultad, de 80% (Derecho y Humanidades) a 42% (VR Investigación). Por antigüedad la "
            "tasa es pareja (65%-72%) y por edad la diferencia no es significativa (p=0.0724).",
        ])
    kit.notas(sl,
        "Participación = al menos 1 registro en analisis.universo_formados_p3, sin filtrar a apto_p3 "
        "(D31). Unidad de análisis: 1 valor por docente.")
    return sl


def uih_b3(prs):
    sl = _nueva(prs)
    kit.title(sl, "Bloque III — Evaluación de desempeño docente (N°624)", fs=16)
    kit.franjas_universo_indice_hallazgos(sl,
        universo_txt=(
            "624 docentes Jornada; 491 (78.7%) tienen al menos una evaluación de desempeño docente (EDD) "
            "entre 2022 y 2025, hecha por la jefatura. La escala cambió en 2024 (promedio 0.87 → 0.68), "
            "así que las comparaciones usan la EDD ajustada por año, expresada en la escala 2025."),
        indice_items=[
            "Calificación EDD por año y sexo",
            "Calificación EDD según sexo",
            "Calificación EDD según jerarquía / escalafón",
            "Calificación EDD según facultad",
        ],
        hallazgos_items=[
            "La brecha por sexo se invierte entre períodos: mujeres más alto en 2022-2023 y hombres en "
            "2024-2025. En el total (hombres 0.66 vs mujeres 0.61) la diferencia no se sostiene al "
            "corregir por comparaciones múltiples.",
            "El escalafón Docente supera al Regular (0.66 vs 0.52, p=0.0011).",
            "Por facultad, con la corrección se sostienen 3 diferencias: Derecho y Humanidades por encima "
            "del resto; Medicina y VR Investigación por debajo.",
        ])
    kit.notas(sl,
        "Fuente: intel.evaluacion_jefes (D28/D29). EDD ajustada por año según D36: cada evaluación se "
        "estandariza dentro de su año y se expresa en la escala de 2025; después se promedia por docente. "
        "Sin el ajuste, VR Investigación (evaluada solo en 2024-2025) aparecía artificialmente más baja.")
    return sl


def uih_b4(prs):
    sl = _nueva(prs)
    kit.title(sl, "Bloque IV — Aprobación y reprobación de alumnos (N°624)", fs=16)
    kit.franjas_universo_indice_hallazgos(sl,
        universo_txt=(
            "624 docentes Jornada, de los cuales 515 (82.5%) tienen al menos una calificación de alumnos "
            "entre 2023-01 y 2025-02. Las comparaciones usan el % de aprobación promedio por docente y "
            "controlan por la dificultad de las asignaturas cuando corresponde."),
        indice_items=[
            "Aprobación y reprobación — global",
            "Según sexo del docente",
            "Según sexo, dentro de cada grupo de dificultad",
            "Según escalafón",
            "Según antigüedad del docente",
            "Evolución de la aprobación según sexo (2023-2025)",
            "Composición de los grupos de dificultad",
            "Antigüedad, edad y sexo según grupo de dificultad",
            "Anexo: resumen de pruebas estadísticas",
        ],
        hallazgos_items=[
            "El 88.5% de las calificaciones de alumnos de docentes Jornada son aprobaciones.",
            "Las mujeres aprueban más en el total (91.1% vs 87.7%, p=0.0016), pero dentro de cada grupo "
            "de dificultad la diferencia desaparece: se explica porque los hombres dictan más asignaturas "
            "de baja aprobación (56% vs 39%).",
            "El escalafón Docente aprueba más que el Regular (90.5% vs 84.3%, p=0.0008). Por antigüedad no "
            "hay diferencia significativa (p=0.2832).",
        ])
    kit.notas(sl,
        "Estados administrativos excluidos según D26; grupos de dificultad según D27. Escalafón según "
        "grupo de dificultad: no significativo (p=0.0716), en el anexo. Antigüedad y edad según grupo de "
        "dificultad: significativas sin ajuste, no se sostienen con Holm por bloque (ver anexo).")
    return sl
