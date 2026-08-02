"""
P1 — Caracterización del Cuerpo Académico de Planta
% de Aprobación y Reprobación de alumnos según Antigüedad del docente — Jornada.
Variante A: 4 tramos (0-4, 5-9, 10-14, 15+).

Mismo patrón/metodología que aprobacion_reprobacion/ (ver ese script para el detalle:
CM aprueba vía catalogo_calificacion, universo acotado a Jornada — ver
docs/DECISIONES_METODOLOGICAS.md D26). `tramo_antiguedad` viene de DOTACION —
misma brecha de cobertura que tramo_edad (ver D22/D23), los docentes sin registro
en DOTACION quedan sin dato y se excluyen del gráfico (no se estiman).

Nota: se probó una prueba t (15+ vs resto) y no dio significativa (p=0.157) — se
descartó esa diapositiva a pedido de la contraparte, queda solo el gráfico descriptivo.

FUENTE: intel.rendimiento_academico_alumnos (Postgres, en vivo)
        + data/cascade/01_jornada/docentes_jornada.csv (universo de RUTs)
SALIDA: P1_aprobacion_reprobacion_antiguedad_4tramos.pptx (1 diapositiva)
        + aprobacion_reprobacion_antiguedad_4tramos_chart.png
"""
import sys; sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "shared"))
from config import CASCADE, OUTPUTS
from pptx_helpers import UcenSlideKit

import numpy as np
import pandas as pd
import matplotlib.patheffects as pe
from sqlalchemy import create_engine, text
from pptx import Presentation
from pptx.util import Emu

HERE = Path(__file__).parent
OUT_PPTX = Path(OUTPUTS) / "pptx" / "P1_aprobacion_reprobacion_antiguedad_4tramos.pptx"
OUT_PPTX.parent.mkdir(parents=True, exist_ok=True)

DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"

COL_APROBACION = "#3E9E68"
COL_REPROBACION = "#E4572E"

TRAMOS_ORD = ["0-4", "5-9", "10-14", "15+"]
TRAMO_MAP = {"15-19": "15+", "20-24": "15+", "25-29": "15+", "30+": "15+"}

# ── Datos ───────────────────────────────────────────────────────────────────
doc = pd.read_csv(Path(CASCADE) / "01_jornada" / "docentes_jornada.csv", encoding="utf-8-sig")
N_JORNADA = len(doc)

engine = create_engine(DB_URL)
q = text("""
    SELECT tramo_antiguedad, aprueba, rut_docente
    FROM intel.rendimiento_academico_alumnos
    WHERE tipo_contrato_tag = 'JORNADA' AND aprueba IS NOT NULL
""")
with engine.connect() as conn:
    raw = pd.read_sql(q, conn)

N_SIN_ANTIGUEDAD_DOC = raw.loc[raw["tramo_antiguedad"].isna(), "rut_docente"].nunique()
raw = raw.dropna(subset=["tramo_antiguedad"]).copy()
raw["tramo_antiguedad"] = raw["tramo_antiguedad"].replace(TRAMO_MAP)

tab = (raw.groupby("tramo_antiguedad")
       .agg(n_evaluable=("aprueba", "count"),
            n_docentes=("rut_docente", "nunique"),
            pct_aprobacion=("aprueba", lambda s: 100 * s.mean()))
       .reindex(TRAMOS_ORD))
tab["pct_reprobacion"] = 100 - tab["pct_aprobacion"]

print(f"Universo Jornada: {N_JORNADA}")
print(tab)
print(f"Excluidos (sin tramo de antigüedad): {N_SIN_ANTIGUEDAD_DOC} docentes")

tramo_mejor = tab["pct_aprobacion"].idxmax()
tramo_peor = tab["pct_aprobacion"].idxmin()


def agregar(prs):
    """Construye el gráfico y agrega la diapositiva a `prs`."""
    kit = UcenSlideKit(out_dir=HERE)
    kit.ensure_bg()

    fig = kit.new_chart_fig()
    ax = kit.chart_axes(fig, top=0.15)   # deja espacio arriba para la leyenda

    x = np.arange(len(TRAMOS_ORD))
    w = 0.34
    bars_a = ax.bar(x - w/2, tab["pct_aprobacion"], width=w, color=COL_APROBACION,
                     alpha=0.92, edgecolor="none", label="% Aprobación")
    bars_r = ax.bar(x + w/2, tab["pct_reprobacion"], width=w, color=COL_REPROBACION,
                     alpha=0.92, edgecolor="none", label="% Reprobación")

    stroke = [pe.withStroke(linewidth=1.8, foreground="#0A0F18")]
    for bars, color in [(bars_a, COL_APROBACION), (bars_r, COL_REPROBACION)]:
        for b in bars:
            h = b.get_height()
            if pd.notna(h):
                ax.text(b.get_x() + b.get_width()/2, h + 1.5, f"{h:.0f}%",
                         ha="center", va="bottom", fontsize=9, fontweight="bold",
                         color=color, path_effects=stroke, zorder=6)
    for xi, n in zip(x, tab["n_docentes"]):
        if pd.notna(n):
            ax.text(xi, 100, f"N°={int(n)}", ha="center", va="bottom",
                    fontsize=8, color="#8A97A3")

    ax.set_xticks(x)
    ax.set_xticklabels(TRAMOS_ORD, fontsize=11, color="white")
    ax.set_xlabel("Tramo de antigüedad en la institución (años)", color="#AAAAAA", fontsize=9)
    ax.set_ylabel("% de calificaciones", color="#AAAAAA", fontsize=9)
    ax.set_ylim(0, 112)
    ax.set_yticks([0, 20, 40, 60, 80, 100])
    ax.tick_params(axis="x", length=0, pad=8)
    ax.tick_params(axis="y", colors="#AAAAAA", labelsize=8.5)
    for sp in ax.spines.values():
        sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.7)
    ax.yaxis.grid(True, color="white", alpha=0.07, linewidth=0.5)
    ax.set_axisbelow(True)
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, fontsize=9, framealpha=0.22, labelcolor="white",
               facecolor="#101820", edgecolor="#444", loc="upper center",
               bbox_to_anchor=(0.5, 0.99), ncol=2)

    chart_path = kit.save_chart(fig, "aprobacion_reprobacion_antiguedad_4tramos_chart.png")

    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.pic_chart(sl, prs, chart_path)
    kit.title(sl, "% de Aprobación y Reprobación según Antigüedad del Docente (4 tramos) — Jornada")
    kit.subtitulo(sl,
        f"Universo: {N_JORNADA} docentes Jornada  ·  "
        f"N°={int(tab['n_docentes'].sum())} con calificaciones y antigüedad registrada "
        f"({N_SIN_ANTIGUEDAD_DOC} excluidos sin dato de antigüedad)")
    kit.punteo_numerado(sl, [
        f"El tramo {tramo_mejor} tiene el mayor % de aprobación "
        f"({tab.loc[tramo_mejor,'pct_aprobacion']:.1f}%, N°={int(tab.loc[tramo_mejor,'n_docentes'])} docentes).",
        f"El tramo {tramo_peor} tiene el menor % de aprobación "
        f"({tab.loc[tramo_peor,'pct_aprobacion']:.1f}%, N°={int(tab.loc[tramo_peor,'n_docentes'])} docentes).",
    ])
    return sl


if __name__ == "__main__":
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(UcenSlideKit.SW_EMU), Emu(UcenSlideKit.SH_EMU)
    agregar(prs)
    prs.save(OUT_PPTX)
    print(f"\n✓ Guardado: {OUT_PPTX}")
