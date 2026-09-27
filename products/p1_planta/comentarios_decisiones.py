"""
P1 — Comentarios de PowerPoint con las decisiones de construcción de cada diapositiva.

Pedido del usuario (2026-09-26): dejar como comentarios del pptx, a nombre de Renato
González, las decisiones tomadas al construir las diapositivas (sobre todo las nuevas),
para que la contraparte evalúe su coherencia y decida si las acepta.

python-pptx no escribe comentarios, así que se agregan con PowerPoint vía COM
(`Comments.Add2`, comentarios "modernos": la contraparte puede responderlos y
resolverlos). Requiere Windows + PowerPoint instalado + pywin32.

Como `generar_presentacion.py` crea el pptx desde cero en cada corrida, los comentarios
se reaplican al final del ensamblado (`aplicar(ruta)`). También corre standalone sobre
un pptx ya generado. Cada diapositiva se ubica por el INICIO DE SU TÍTULO (sin distinguir
mayúsculas), no por número, para que siga funcionando si se reordena el deck. Un título que
no aparece se avisa en consola, no rompe la generación. Los textos se escriben con números
en formato inglés y pasan por `formato_cl` (coma decimal), igual que el resto del deck.
"""
import sys; sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))
from pptx_helpers import formato_cl

AUTOR, INICIALES = "Renato González", "RG"

# título (inicio) → lista de comentarios, uno por decisión, para que la contraparte
# pueda responder o resolver cada uno por separado
COMENTARIOS = {
    "Contenido de la presentación": [
        "Decisión: el deck sigue los 4 bloques de esta grilla. La participación en formación quedó "
        "toda en el Bloque II y EDD pasó antes que Aprobación.",
        "Revisión de coherencia (26-27/09): cada par 'descriptivo + prueba t' se fundió en una sola "
        "diapositiva, se quitaron gráficos que repetían información y se agregó un anexo con todas las "
        "pruebas estadísticas, incluidas las no significativas.",
        "Regla de significancia: una diferencia es significativa solo si su p, corregido por comparaciones "
        "múltiples dentro de su bloque (Holm), es menor a 0.05. Si no, se informa como 'sin diferencia'.",
    ],
    "Bloque I —": [
        "Se declara aquí, una sola vez, que 90 docentes (14%) no tienen registro en dotación y quedan "
        "fuera de los gráficos de edad, antigüedad, cargo y jornada. Su perfil difiere algo del resto "
        "(más mujeres, menos Regulares), así que esos gráficos pueden subrepresentarlos.",
        "Se definen jerarquía (8 categorías) y escalafón (Docente/Regular) porque el deck usa ambos.",
    ],
    "Distribución de la edad según jerarquía": [
        "El título original 'según edad y categoría docente' repetía 'edad'; se usa 'jerarquía', el "
        "término que el deck usa para las 8 categorías.",
    ],
    "Años de trayectoria promedio": [
        "Decisión: 'años de trayectoria' = años en UCEN desde la fecha de ingreso (antigüedad). No hay "
        "dato de la carrera previa a UCEN; se indica en la bajada.",
        "Se usan las mismas 8 categorías, orden por magnitud y colores que la diapositiva de edad por "
        "jerarquía, para leerlas como par.",
    ],
    "Distribución por unidad/facultad": [
        "Decisión: se normalizaron los nombres de unidad. La fuente escribe algunas facultades de "
        "dos formas ('FAC. DE MEDICINA…' / 'Facultad de Medicina…'); se suman en una sola barra.",
        "VR de Investigación y Postgrado va como barra propia (80 docentes). Junta Directiva, Sede La "
        "Serena, Dir. de Aseguramiento de la Calidad y Gabinete de Rectoría se agrupan en 'Otras "
        "unidades' (13 docentes). Los 73 sin unidad registrada se informan en la bajada, no como barra.",
    ],
    "Distribución de la carga académica": [
        "Fuente: archivo 'CONSOLIDADO DOCENTES 3-05-2026 — dotacion_con_clasificacion' (547 docentes), "
        "cruzado por RUT con el universo Jornada: 534 de 624 están en el archivo.",
        "Categoría = columna CLASIFICACION del archivo, con dos ajustes: 'DOCENTE' (1 caso, cargo "
        "'Profesor') se sumó a Docencia, y los Vicedecano(a) y las autoridades superiores (Rector, "
        "Vicerrectores, Decanos(as) y Junta Directiva) pasaron de Vinculación con el Medio a Gestión "
        "Académica, por ser cargos de gestión.",
        "Cada docente cuenta una sola vez, con su cargo principal en dotación.",
    ],
    "Grado académico según sexo": [
        "El punteo 4 se presenta como 'posible implicancia': relaciona dos distribuciones (grado × sexo "
        "y grado × escalafón), no mide trayectorias de ascenso individuales.",
        "Técnico (N°=2) se sumó a Profesional por tamaño; 'No informa' se trata como sin dato (D21).",
    ],
    "Participación en instancias formativas y modalidades": [
        "Las diapositivas de modalidades, Venn, intensidad, antigüedad y tipo por grupo replican gráficos "
        "del informe P3, pero sobre el universo Jornada (624 docentes, 418 formados), no sobre los 316 "
        "'Aptos P3'. Por eso los N° no coinciden con P3.",
        "Terminología: 'instancias formativas' = cualquier Taller, Diplomado o Proyecto; 'Oferta "
        "formativa (Taller)' = solo el tipo Taller, como en P3. Quien combina 2 o más tipos tiene "
        "'Participación Mixta'.",
    ],
    "Tipos de formación (diagrama de Venn)": [
        "El Venn es esquemático: el tamaño de los círculos NO es proporcional al N° (con 381 vs 31 "
        "docentes, un Venn proporcional dejaría Proyecto casi invisible). El número de cada región sí "
        "es el conteo real.",
    ],
    "Intensidad de participación": [
        "Instancia = actividad distinta (nombre + período). Se descartó 1 registro duplicado exacto; "
        "cursar la misma actividad en 2 períodos cuenta 2 veces.",
        "El punteo 2 (docentes con 3+ instancias como grupo clave para efectos acumulativos) es una "
        "orientación para el análisis, no un resultado medido en P1.",
    ],
    "¿Difiere la participación en instancias formativas según sexo": [
        "La diapositiva descriptiva y la de prueba t mostraban las mismas barras; quedó una sola, con el "
        "intervalo de confianza y el resultado de la prueba.",
        "Títulos '¿Difiere…?' en vez de '¿Influye…?': una prueba t muestra asociación, no causa.",
    ],
    "Participación en instancias formativas según facultad": [
        "Solo facultad: el panel por jerarquía se quitó porque repetía la diapositiva de participación "
        "según jerarquía.",
        "Se agregó la prueba de cada unidad vs el resto (como en EDD). Con la corrección por comparaciones "
        "múltiples solo VR Investigación difiere; Educación y Derecho eran significativas sin corregir.",
    ],
    "Antigüedad en la institución de los docentes formados": [
        "Se agregó la tasa de participación por tramo (formados / todos los docentes del tramo). Mirando "
        "solo conteos parecía que los antiguos participan menos; con tasas la participación es pareja "
        "(65%-72%) en los tramos con N° suficiente.",
    ],
    "Tipo de formación según antigüedad, sexo y edad": [
        "Se muestra la composición por tipo de formación (réplica del gráfico de P3); la tasa Cursa / No "
        "cursa por grupo está en las diapositivas de participación.",
        "El ancho de cada barra es proporcional al N° del grupo (mosaico): con barras de igual ancho, "
        "un grupo de 190 docentes se veía igual que uno de 23. Antigüedad 15-19 y 20+ se fusionaron en "
        "'15+' por tamaño.",
    ],
    "Calidad de los datos de la EDD por año": [
        "Hallazgo clave (D37): en 2024 y 2025 hay notas EDD dañadas. 62 notas de 2025 valen exactamente 0 "
        "(37 con concepto 'Muy Bueno': son datos vacíos) y un grupo de notas de 2024-2025 vale casi "
        "exactamente la mitad del puntaje del director (un componente faltante contado como 0).",
        "Criterio: se excluyen las notas de 0 y las menores a 0.55 en 2024-2025 (en 2022-2023 solo el 5% "
        "de las notas era menor a 0.55; en 2024-2025, el 38%). Sin ellas la EDD es estable los 4 años. "
        "Conviene informar el problema a quien administra la base de EDD.",
        "Esto reemplaza el 'ajuste por año' de la versión anterior (D36), que suponía un cambio de escala "
        "que no existió.",
    ],
    "¿Difiere la calificación EDD según sexo": [
        "Con la nota limpia no hay diferencia por sexo. La ventaja de los hombres que mostraba la versión "
        "anterior venía de las notas dañadas, que afectaron más a las mujeres (43% vs 32%).",
    ],
    "Calificación EDD según jerarquía": [
        "Con la nota limpia tampoco hay diferencia por escalafón: la diferencia Docente vs Regular de la "
        "versión anterior venía de las notas dañadas.",
    ],
    "Calificación EDD según facultad": [
        "Con la nota limpia ninguna facultad difiere del resto. Las diferencias anteriores (VR "
        "Investigación y Medicina más bajas) venían de las notas dañadas; VR Investigación solo tiene "
        "evaluaciones 2024-2025.",
        "Se usan los nombres de facultad del Bloque I en vez de siglas. Aquí la facultad es la de la "
        "jefatura que evalúa (facultad_jefe), otro campo que la unidad del Bloque I; por eso los N° no "
        "coinciden.",
    ],
    "¿Difiere el % de aprobación según sexo": [
        "Se usa una sola medida, el % de aprobación promedio por docente (la unidad de la prueba t). La "
        "versión ponderada por calificación daba otras cifras para la misma comparación; queda en notas.",
    ],
    "% de aprobación según sexo, dentro de cada grupo de dificultad": [
        "Análisis de control: como los hombres dictan más asignaturas de baja aprobación, la brecha por "
        "sexo podía deberse a la dificultad del curso. Comparando dentro de cada grupo, la diferencia "
        "desaparece: no es que las docentes aprueben más en cursos comparables.",
    ],
    "¿Difiere el % de aprobación según escalafón": [
        "Misma medida que en sexo: % de aprobación promedio por docente.",
    ],
    "% de aprobación según antigüedad del docente": [
        "Se agregó un ANOVA entre los 4 tramos (antes esta diapositiva no tenía prueba): no hay diferencia "
        "significativa.",
    ],
    "Composición de los grupos de dificultad": [
        "Grupos = terciles del % de aprobación histórico de cada asignatura, con todos los docentes "
        "y contratos 2023-2025 (D27). Cada grupo tiene aproximadamente un tercio de las asignaturas.",
        "Limitación: el 56% de las asignaturas las dicta un solo docente; en esos casos el % "
        "histórico de la asignatura es el del propio docente (medida circular).",
    ],
    "Antigüedad de los docentes según grupo de dificultad": [
        "Descriptivo y prueba usan la misma unidad: 1 valor por docente en su grupo predominante. Sin "
        "corregir la diferencia era significativa; con la corrección por comparaciones múltiples no lo es "
        "(lo mismo ocurre con la edad).",
    ],
    "Anexo — Resumen de pruebas estadísticas": [
        "Se muestran todas las pruebas, incluidas las no significativas. La columna 'p ajustado' corrige "
        "por hacer muchas comparaciones a la vez, dentro de cada bloque (Holm); en dorado, las "
        "significativas según la regla del deck.",
    ],
}


def _titulo(slide):
    """Texto del primer cuadro de texto de la diapositiva (el título, en todo P1)."""
    for i in range(1, slide.Shapes.Count + 1):
        sh = slide.Shapes.Item(i)
        if sh.HasTextFrame and sh.TextFrame.HasText:
            return sh.TextFrame.TextRange.Text.strip()
    return ""


def aplicar(ruta_pptx):
    import win32com.client

    ruta = str(Path(ruta_pptx).resolve())
    app = win32com.client.DispatchEx("PowerPoint.Application")   # instancia propia, no toca la del usuario
    pres = app.Presentations.Open(ruta, False, False, False)      # (ReadOnly, Untitled, WithWindow)
    try:
        titulos = {i: _titulo(pres.Slides.Item(i)).lower() for i in range(1, pres.Slides.Count + 1)}
        total = 0
        for clave, textos in COMENTARIOS.items():
            nums = [i for i, t in titulos.items() if t.startswith(clave.lower())]
            if not nums:
                print(f"  ⚠ Comentarios: no se encontró diapositiva con título '{clave}…'")
                continue
            sl = pres.Slides.Item(nums[0])
            for k, texto in enumerate(textos):
                sl.Comments.Add2(12, 12 + 18 * k, AUTOR, INICIALES, formato_cl(texto), "None", AUTOR)
            total += len(textos)
            print(f"  Diapo {nums[0]:>2}: {len(textos)} comentarios ({clave})")
        pres.Save()
        print(f"✓ {total} comentarios agregados a nombre de {AUTOR}")
    finally:
        pres.Close()
        app.Quit()


if __name__ == "__main__":
    ROOT = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(ROOT))
    from config import OUTPUTS
    aplicar(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(OUTPUTS) / "pptx" / "P1_presentacion.pptx")
