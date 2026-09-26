"""
P1 — Caracterización del Cuerpo Académico de Planta
% de Aprobación y Reprobación de alumnos — docentes de Jornada (global).

METODOLOGÍA (ver docs/DECISIONES_METODOLOGICAS.md D26):
  - Fuente: intel.rendimiento_academico_alumnos (calificacion_alumno enriquecida con
    tags de perfil docente + `aprueba` desde consolidados.catalogo_calificacion).
  - "Aprueba" excluye estados administrativos no evaluables (NP, P, SC, SD).
  - Universo acotado a Jornada (624) — misma decisión que el resto de P1.
  - % calculado sobre calificaciones individuales (filas), no sobre docentes.

FUENTE: intel.rendimiento_academico_alumnos (Postgres, en vivo)
        + data/cascade/01_jornada/docentes_jornada.csv (universo de RUTs, solo para N° total)
SALIDA: P1_aprobacion_reprobacion.pptx (1 diapositiva) + aprobacion_reprobacion_chart.png
"""
import sys; sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "shared"))
from config import CASCADE, OUTPUTS
from pptx_helpers import UcenSlideKit

import pandas as pd
import matplotlib.patheffects as pe
from sqlalchemy import create_engine, text
from pptx import Presentation
from pptx.util import Emu

HERE = Path(__file__).parent
OUT_PPTX = Path(OUTPUTS) / "pptx" / "P1_aprobacion_reprobacion.pptx"
OUT_PPTX.parent.mkdir(parents=True, exist_ok=True)

DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"

COL_APROBACION = "#3E9E68"
COL_REPROBACION = "#E4572E"

# ── Datos ───────────────────────────────────────────────────────────────────
doc = pd.read_csv(Path(CASCADE) / "01_jornada" / "docentes_jornada.csv", encoding="utf-8-sig")
N_JORNADA = len(doc)

engine = create_engine(DB_URL)
q = text("""
    SELECT COUNT(*) AS n_evaluable,
           COUNT(DISTINCT rut_docente) AS n_docentes,
           100.0 * AVG(aprueba::int) AS pct_aprobacion
    FROM intel.rendimiento_academico_alumnos
    WHERE tipo_contrato_tag = 'JORNADA' AND aprueba IS NOT NULL
""")
with engine.connect() as conn:
    row = pd.read_sql(q, conn).iloc[0]

N_EVALUABLE = int(row["n_evaluable"])
N_DOCENTES = int(row["n_docentes"])
PCT_APROB = row["pct_aprobacion"]
PCT_REPROB = 100 - PCT_APROB

print(f"Universo Jornada: {N_JORNADA}  |  con calificaciones: {N_DOCENTES}  |  "
      f"calificaciones evaluables: {N_EVALUABLE}")
print(f"% Aprobación: {PCT_APROB:.1f}  |  % Reprobación: {PCT_REPROB:.1f}")


def agregar(prs):
    """Construye el gráfico y agrega la diapositiva a `prs`."""
    kit = UcenSlideKit(out_dir=HERE)
    kit.ensure_bg()

    fig = kit.new_chart_fig()
    ax = kit.chart_axes(fig, left=0.10)

    cats = ["Aprobación", "Reprobación"]
    vals = [PCT_APROB, PCT_REPROB]
    colors = [COL_APROBACION, COL_REPROBACION]
    bars = ax.bar(cats, vals, width=0.45, color=colors, alpha=0.92, edgecolor="none")

    stroke = [pe.withStroke(linewidth=2, foreground="#0A0F18")]
    for b, v, c in zip(bars, vals, colors):
        ax.text(b.get_x() + b.get_width()/2, v + 1.5, f"{v:.1f}%",
                 ha="center", va="bottom", fontsize=16, fontweight="bold",
                 color=c, path_effects=stroke, zorder=6)

    ax.set_ylabel("% de calificaciones", color="#AAAAAA", fontsize=9)
    ax.set_ylim(0, 100)
    ax.tick_params(axis="x", length=0, labelsize=12, colors="white")
    ax.tick_params(axis="y", colors="#AAAAAA", labelsize=8.5)
    for sp in ax.spines.values():
        sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.7)
    ax.yaxis.grid(True, color="white", alpha=0.07, linewidth=0.5)
    ax.set_axisbelow(True)

    chart_path = kit.save_chart(fig, "aprobacion_reprobacion_chart.png")

    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.pic_chart(sl, prs, chart_path)
    kit.title(sl, "Aprobación y reprobación de alumnos — Docentes Jornada")
    kit.subtitulo(sl,
        f"Universo: {N_JORNADA} docentes Jornada  ·  {N_DOCENTES} con calificaciones registradas "
        f"({100*N_DOCENTES/N_JORNADA:.0f}%)  ·  N°={N_EVALUABLE:,} evaluaciones de docentes Jornada evaluables")
    kit.punteo_numerado(sl, [
        f"El {PCT_APROB:.1f}% de las calificaciones de alumnos evaluados por docentes de Jornada "
        f"corresponde a aprobación; el {PCT_REPROB:.1f}% a reprobación.",
        f"Se excluyen del cálculo los estados administrativos no evaluables (No se Presentó, "
        f"Postergado, Sin Calificación, Sin Datos) — solo se cuentan calificaciones con resultado real.",
    ])
    return sl


if __name__ == "__main__":
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(UcenSlideKit.SW_EMU), Emu(UcenSlideKit.SH_EMU)
    agregar(prs)
    prs.save(OUT_PPTX)
    print(f"\n✓ Guardado: {OUT_PPTX}")
