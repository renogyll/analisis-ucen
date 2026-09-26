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
        "Revisión de coherencia (26-09): cada par 'descriptivo + prueba t' se fundió en una sola "
        "diapositiva, se quitaron gráficos que repetían información y se agregó un anexo con todas las "
        "pruebas estadísticas, incluidas las no significativas.",
        "Cada bloque indica su período: los datos no cubren los mismos años en todos los bloques.",
    ],
    "Bloque I —": [
        "Se declara aquí, una sola vez, que 90 docentes (14%) no tienen registro en dotación y quedan "
        "fuera de los gráficos de edad, antigüedad, cargo y jornada. Su perfil difiere algo del resto "
        "(más mujeres, menos Regulares), así que esos gráficos pueden subrepresentarlos.",
        "Se definen jerarquía (8 categorías) y escalafón (Docente/Regular) porque el deck usa ambos.",
    ],
    "Distribución de la edad según jerarquía": [
        "El título original 'según edad y categoría docente' repetía 'edad'; se usa 'jerarquía', el "
        "término que el deck usa para las 8 categorías. Confirmar si prefieren otro.",
    ],
    "Años de trayectoria promedio": [
        "Decisión: 'años de trayectoria' se midió como años en UCEN desde la fecha de ingreso "
        "(antigüedad), no como trayectoria académica total: no hay dato de la carrera previa a "
        "UCEN. ¿Es la lectura que buscaban?",
        "Quedan fuera los docentes sin fecha de ingreso registrada y los 'Sin jerarquía' "
        "(detalle en la bajada). Se usan las mismas 8 categorías, orden por magnitud y colores "
        "que la diapositiva de edad por jerarquía, para leerlas como par.",
        "El punteo 2 ('parte de los Regulares ingresa ya jerarquizado') es una interpretación, no "
        "un dato medido: no tenemos la fecha de paso a Regular. Evaluar si se deja, se suaviza o "
        "se quita.",
    ],
    "Distribución por unidad/facultad": [
        "Decisión: se normalizaron los nombres de unidad. La fuente escribe algunas facultades de "
        "dos formas ('FAC. DE MEDICINA…' / 'Facultad de Medicina…'); en la diapositiva de "
        "referencia de P3 eso producía barras duplicadas. Aquí se suman en una sola barra.",
        "VR de Investigación y Postgrado va como barra propia (80 docentes). Junta Directiva, Sede La "
        "Serena, Dir. de Aseguramiento de la Calidad y Gabinete de Rectoría se agrupan en 'Otras "
        "unidades' (13 docentes).",
        "Los 73 docentes sin unidad registrada no se grafican; los % son sobre los 551 con dato. "
        "Alternativa: agregarlos como barra 'Sin dato'. ¿Cuál prefieren?",
    ],
    "Distribución de la carga académica": [
        "Fuente nueva: archivo 'CONSOLIDADO DOCENTES 3-05-2026 — dotacion_con_clasificacion' "
        "(547 docentes). Se cruzó por RUT con el universo Jornada: 534 de 624 están en el archivo.",
        "Categoría = columna CLASIFICACION tal como viene. Único ajuste: 'DOCENTE' (1 caso, cargo "
        "'Profesor') se sumó a 'Docencia', porque los demás 'Profesor' ya estaban clasificados así.",
        "Cada docente cuenta una sola vez, con su cargo principal en dotación. Si en la práctica "
        "ejerce varias funciones, este gráfico no lo captura.",
        "A confirmar: la clasificación ubica 'Coordinador(a) Campos Clínicos' y 'Vicedecano(a)' en "
        "Vinculación con el Medio. Se respetó tal cual; conviene validarlo.",
    ],
    "Grado académico según sexo": [
        "El punteo 4 (implicancia) es una hipótesis: relaciona dos distribuciones (grado × sexo y "
        "grado × escalafón), no mide trayectorias de ascenso individuales. Evaluar si se deja, se "
        "suaviza o se quita.",
        "Técnico (N°=2) se sumó a Profesional por tamaño; 'No informa' se trata como sin dato (D21).",
    ],
    "Participación en instancias formativas y modalidades": [
        "Decisión: las diapositivas de modalidades, Venn, intensidad, antigüedad y tipo por grupo "
        "replican gráficos del informe P3, pero sobre el universo Jornada (624 docentes, 418 formados), "
        "no sobre los 316 'Aptos P3'. Por eso los N° no coinciden con P3.",
        "Terminología: 'instancias formativas' = cualquier Taller, Diplomado o Proyecto; 'Oferta "
        "formativa (Taller)' = solo el tipo Taller, como en P3. Quien combina 2 o más tipos tiene "
        "'Participación Mixta'.",
    ],
    "Tipos de formación (diagrama de Venn)": [
        "Decisión: el Venn es esquemático, el tamaño de los círculos NO es proporcional al N° (con "
        "381 vs 31 docentes, un Venn proporcional dejaría Proyecto casi invisible). El número de cada "
        "región sí es el conteo real.",
    ],
    "Intensidad de participación": [
        "Decisión: instancia = actividad distinta (nombre + período). Se descartó 1 registro duplicado "
        "exacto; cursar la misma actividad en 2 períodos cuenta 2 veces. ¿Coincide con cómo lo cuentan?",
        "El punteo 2 dice que los docentes con 3+ instancias son los más relevantes para efectos "
        "acumulativos: es una orientación para el análisis, no un resultado medido en P1.",
    ],
    "¿Difiere la participación en instancias formativas según sexo": [
        "Revisión de coherencia: la diapositiva descriptiva y la de prueba t mostraban las mismas barras; "
        "quedó una sola, con el intervalo de confianza y el resultado de la prueba.",
        "Títulos '¿Difiere…?' en vez de '¿Influye…?': una prueba t muestra asociación, no causa.",
    ],
    "Participación en instancias formativas según facultad": [
        "Solo facultad: el panel por jerarquía que acompañaba a este gráfico se quitó porque repetía "
        "la diapositiva de participación según jerarquía.",
        "Descriptivo, sin prueba t: por facultad no se pidió. Se puede agregar (cada facultad vs. el "
        "resto, como en EDD) si les interesa.",
    ],
    "Antigüedad en la institución de los docentes formados": [
        "Decisión: se agregó la tasa de participación por tramo (formados / todos los docentes del "
        "tramo). En P3 se interpretó 'a mayor antigüedad, menor participación' mirando solo conteos; "
        "con tasas, la participación es pareja (65%-72%) en los tramos con N° suficiente.",
    ],
    "Tipo de formación según antigüedad, sexo y edad": [
        "Decisión: se interpretó 'participación por antigüedad, sexo y edad' como la composición por "
        "tipo de formación (réplica del gráfico de P3). Si buscaban la tasa Cursa / No cursa por grupo, "
        "se puede cambiar.",
        "El ancho de cada barra es proporcional al N° del grupo (mosaico): con barras de igual ancho, "
        "un grupo de 190 docentes se veía igual que uno de 23. Antigüedad 15-19 y 20+ se fusionaron en "
        "'15+' por tamaño.",
    ],
    "Calificación EDD por año y sexo": [
        "Decisión clave (D36): la EDD promedio cae de 0.87 (2022-2023) a 0.68 (2024-2025) y su dispersión "
        "se duplica. Parece un cambio de escala o de instrumento, no de desempeño. ¿Pueden confirmar si "
        "el instrumento o la forma de calcular la EDD cambió en 2024?",
        "Por eso esta diapositiva muestra los años por separado (escala original) y las siguientes usan "
        "la EDD ajustada por año.",
    ],
    "¿Difiere la calificación EDD según sexo": [
        "EDD ajustada por año: cada evaluación se estandariza dentro de su año (se resta el promedio del "
        "año y se divide por su desviación) y se expresa en la escala de 2025. Así un docente evaluado "
        "solo en 2024-2025 no queda más bajo solo por el año.",
        "Con la EDD ajustada, la diferencia a favor de los hombres es más débil (p=0.0408 vs 0.0183 sin "
        "ajuste), proviene de 2024-2025 y no se sostiene al corregir por comparaciones múltiples dentro "
        "del Bloque III. En 2022-2023 las mujeres puntuaban más alto.",
    ],
    "Calificación EDD según facultad": [
        "Con la EDD ajustada, VR Investigación sigue más baja que el resto, pero la brecha se reduce: "
        "sin ajuste se comparaba solo contra años de escala alta, porque VRIIP no tiene evaluaciones "
        "2022-2023.",
        "Se usan los nombres de facultad del Bloque I en vez de siglas. Ojo: aquí la facultad es la de "
        "la jefatura que evalúa (facultad_jefe), otro campo que la unidad del Bloque I; por eso los N° "
        "no coinciden.",
        "Con la corrección de Holm por bloque se sostienen 3 de las 5 diferencias (Derecho y "
        "Humanidades, Medicina, VR Investigación); Ingeniería y Economía quedan como indicio.",
    ],
    "¿Difiere el % de aprobación según sexo": [
        "Decisión: se usa una sola medida, el % de aprobación promedio por docente (la unidad de la "
        "prueba t). La versión ponderada por calificación daba otras cifras (90.0% vs 86.7%) para la "
        "misma comparación y se leía como contradicción; queda en notas.",
    ],
    "% de aprobación según sexo, dentro de cada grupo de dificultad": [
        "Análisis nuevo: como los hombres dictan más asignaturas de baja aprobación, la brecha por sexo "
        "podía deberse a la dificultad del curso. Comparando dentro de cada grupo, la diferencia "
        "desaparece (ningún grupo significativo). Cambia la lectura: no es que las docentes aprueben "
        "más en cursos comparables.",
    ],
    "¿Difiere el % de aprobación según escalafón": [
        "Misma medida que en sexo: % de aprobación promedio por docente.",
    ],
    "% de aprobación según antigüedad del docente": [
        "Antes esta diapositiva no tenía prueba y el Bloque IV afirmaba 'sin diferencias significativas'. "
        "Se agregó un ANOVA entre los 4 tramos (p=0.2832) que respalda esa frase.",
    ],
    "Composición de los grupos de dificultad": [
        "Grupos = terciles del % de aprobación histórico de cada asignatura, con todos los docentes "
        "y contratos 2023-2025 (D27). Cada grupo tiene aproximadamente un tercio de las asignaturas.",
        "Limitación: el 56% de las asignaturas las dicta un solo docente; en esos casos el % "
        "histórico de la asignatura es el del propio docente (medida circular).",
    ],
    "Antigüedad de los docentes según grupo de dificultad": [
        "Revisión de coherencia: antes el descriptivo contaba instancias y comparaba Baja vs Alta, y la "
        "prueba usaba 1 valor por docente y comparaba Baja vs Media+Alta (dos cifras distintas para lo "
        "mismo). Ahora ambos usan 1 valor por docente en su grupo predominante, en una sola diapositiva.",
    ],
    "Anexo — Resumen de pruebas estadísticas": [
        "Decisión: se muestran todas las pruebas, incluidas las no significativas, para no sesgar la "
        "lectura. La columna 'p ajustado' corrige por hacer muchas comparaciones a la vez, dentro de cada "
        "bloque (familia de preguntas); en dorado, las que siguen siendo significativas después del ajuste. "
        "Las diapositivas cuyo resultado no se sostiene llevan un aviso en el punteo.",
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
