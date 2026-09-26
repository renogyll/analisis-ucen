"""
P1 — Caracterización del Cuerpo Académico de Planta
Composición de los Grupos de Dificultad de Asignaturas — Jornada.

Overview general de los 3 grupos de dificultad (Baja/Media/Alta) definidos en
docs/DECISIONES_METODOLOGICAS.md D27: terciles de % de aprobación histórico por
asignatura, calculados sobre el universo completo (no solo Jornada — la dificultad
es propiedad del curso) y tageados en intel.rendimiento_academico_alumnos. Esta
diapositiva no mide aprobación por sí — es el "mapa" de cuántas asignaturas,
calificaciones y docentes Jornada caen en cada tercio, para poder leer los
gráficos que vengan después (ej. antigüedad por grupo) con contexto de tamaño.

FUENTE: intel.rendimiento_academico_alumnos (Postgres, en vivo)
        + data/cascade/01_jornada/docentes_jornada.csv (universo de RUTs)
SALIDA: P1_dificultad_composicion.pptx (1 diapositiva) — sin gráfico, 3 cajas de texto
"""
import sys; sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "shared"))
from config import CASCADE, OUTPUTS
from pptx_helpers import UcenSlideKit

import pandas as pd
from sqlalchemy import create_engine, text
from pptx import Presentation
from pptx.util import Emu

HERE = Path(__file__).parent
OUT_PPTX = Path(OUTPUTS) / "pptx" / "P1_dificultad_composicion.pptx"
OUT_PPTX.parent.mkdir(parents=True, exist_ok=True)

DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"
GRUPOS_ORD = ["Baja", "Media", "Alta"]

# ── Datos ───────────────────────────────────────────────────────────────────
doc = pd.read_csv(Path(CASCADE) / "01_jornada" / "docentes_jornada.csv", encoding="utf-8-sig")
N_JORNADA = len(doc)

engine = create_engine(DB_URL)

# Rango institucional (todo el universo, no solo Jornada) de cada grupo
q_rango = text("""
    SELECT grupo_dificultad,
           MIN(pct_aprob_asignatura) AS pct_min, MAX(pct_aprob_asignatura) AS pct_max,
           COUNT(DISTINCT cod_asignatura) AS n_asignaturas_total
    FROM intel.rendimiento_academico_alumnos
    WHERE grupo_dificultad IS NOT NULL
    GROUP BY grupo_dificultad
""")
# Composición Jornada
q_jornada = text("""
    SELECT grupo_dificultad,
           COUNT(DISTINCT cod_asignatura) AS n_asignaturas,
           COUNT(*) FILTER (WHERE aprueba IS NOT NULL) AS n_calificaciones,
           COUNT(DISTINCT rut_docente) AS n_docentes,
           100.0 * AVG(aprueba::int) AS pct_aprobacion
    FROM intel.rendimiento_academico_alumnos
    WHERE tipo_contrato_tag = 'JORNADA' AND grupo_dificultad IS NOT NULL
    GROUP BY grupo_dificultad
""")
with engine.connect() as conn:
    rango = pd.read_sql(q_rango, conn).set_index("grupo_dificultad").reindex(GRUPOS_ORD)
    tab = pd.read_sql(q_jornada, conn).set_index("grupo_dificultad").reindex(GRUPOS_ORD)

print(f"Universo Jornada: {N_JORNADA}")
print("Rango institucional (todo el universo):"); print(rango)
print("\nComposición Jornada:"); print(tab)

N_ASIG_TOTAL = int(rango["n_asignaturas_total"].sum())
N_DOCENTES_TOTAL = int(tab["n_docentes"].sum())


# Formato franjas + explicación de cada grupo antes de los N° (2026-09-25, anotaciones de
# la contraparte: "Baja aprobación / Aprobación media / Aprobación alta, explicar en
# detalle qué significa cada ítem, antes de dejar los N°").
NOMBRES = {"Baja": "Baja aprobación", "Media": "Aprobación media", "Alta": "Aprobación alta"}
SIGNIFICADO = {
    "Baja": ("Tercio de asignaturas donde históricamente reprueban más alumnos. Son los "
             "cursos más exigentes de la universidad, para cualquier docente que los dicte."),
    "Media": ("Tercio intermedio: asignaturas donde la gran mayoría aprueba, pero con una "
              "reprobación todavía visible. Representan la exigencia típica de la universidad."),
    "Alta": ("Tercio de asignaturas donde prácticamente todos los alumnos aprueban. Son los "
             "cursos de menor exigencia relativa en términos de aprobación."),
}


def agregar(prs):
    """Construye la diapositiva (franjas, sin gráfico) y la agrega a `prs`."""
    kit = UcenSlideKit(out_dir=HERE)
    kit.ensure_bg()

    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.title(sl, "Composición de los grupos de dificultad de asignaturas — Docentes Jornada")
    kit.subtitulo(sl,
        f"Cada una de las {N_ASIG_TOTAL:,} asignaturas se clasifica según su % de aprobación "
        f"histórico (todos los docentes y contratos, 2023-2025), en 3 grupos de igual tamaño")

    filas = []
    for g in GRUPOS_ORD:
        r, t = rango.loc[g], tab.loc[g]
        significado = (
            f"Qué significa\n{SIGNIFICADO[g]}\n"
            f"Rango: entre {r['pct_min']:.1f}% y {r['pct_max']:.1f}% de aprobación histórica "
            f"de la asignatura.")
        cifras = (
            f"En cifras — docentes Jornada\n"
            f"•  N° asignaturas: {int(t['n_asignaturas'])}\n"
            f"•  N° calificaciones: {int(t['n_calificaciones']):,}\n"
            f"•  N° docentes: {int(t['n_docentes'])}\n"
            f"•  % de aprobación: {t['pct_aprobacion']:.1f}%")
        filas.append((NOMBRES[g], [significado, cifras]))
    kit.franjas(sl, filas, fs=10, col_split=0.46)

    kit.notas(sl,
        "Metodología completa en docs/DECISIONES_METODOLOGICAS.md D27. El % histórico se "
        "calcula por cod_asignatura sobre TODO el universo (no solo Jornada) porque la "
        "dificultad es propiedad del curso, no del tipo de contrato de quien lo dicta. "
        "56% de las asignaturas las dicta un solo docente — para esos casos el % histórico "
        "es circular (es el % de ese mismo docente), se descartó por eso un z-score.")
    return sl


if __name__ == "__main__":
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(UcenSlideKit.SW_EMU), Emu(UcenSlideKit.SH_EMU)
    agregar(prs)
    prs.save(OUT_PPTX)
    print(f"\n✓ Guardado: {OUT_PPTX}")
