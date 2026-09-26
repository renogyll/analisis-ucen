"""
P1 — Caracterización del Cuerpo Académico de Planta
% de Aprobación y Reprobación de alumnos según Jerarquía del docente — Jornada.

Mismo patrón/metodología que aprobacion_reprobacion/ (ver ese script para el detalle:
CM aprueba vía catalogo_calificacion, universo acotado a Jornada — ver
docs/DECISIONES_METODOLOGICAS.md D26).

REPLANTEADO 2026-08-01 a pedido de la contraparte: en vez de las 8 categorías cruzadas
(nivel × escalafón, ver D25), acá solo se separa por ESCALAFÓN — Docente vs Regular —
colapsando los 4 niveles (Instructor/Asistente/Asociado/Titular) dentro de cada uno.
Se excluye "Sin Jerarquía"/sin dato, igual que en el resto de P1.

FUENTE: intel.rendimiento_academico_alumnos (Postgres, en vivo)
        + data/cascade/01_jornada/docentes_jornada.csv (universo de RUTs)
SALIDA: P1_aprobacion_reprobacion_jerarquia.pptx (1 diapositiva)
        + aprobacion_reprobacion_jerarquia_chart.png
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
from scipy import stats
from sqlalchemy import create_engine, text
from pptx import Presentation
from pptx.util import Emu

HERE = Path(__file__).parent
OUT_PPTX = Path(OUTPUTS) / "pptx" / "P1_aprobacion_reprobacion_jerarquia.pptx"
OUT_PPTX.parent.mkdir(parents=True, exist_ok=True)

DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"

COL_APROBACION = "#3E9E68"
COL_REPROBACION = "#E4572E"

CAT_ORD = ["INSTRUCTOR DOCENTE", "INSTRUCTOR REGULAR",
           "ASISTENTE DOCENTE",  "ASISTENTE REGULAR",
           "ASOCIADO DOCENTE",   "ASOCIADO REGULAR",
           "TITULAR DOCENTE",    "TITULAR REGULAR"]
ESCALAFON_ORD = ["Docente", "Regular"]

# ── Datos ───────────────────────────────────────────────────────────────────
doc = pd.read_csv(Path(CASCADE) / "01_jornada" / "docentes_jornada.csv", encoding="utf-8-sig")
N_JORNADA = len(doc)

engine = create_engine(DB_URL)
q = text("""
    SELECT jerarquia, aprueba, rut_docente
    FROM intel.rendimiento_academico_alumnos
    WHERE tipo_contrato_tag = 'JORNADA' AND aprueba IS NOT NULL
""")
with engine.connect() as conn:
    raw = pd.read_sql(q, conn)

N_SIN_JERARQUIA_DOC = raw.loc[~raw["jerarquia"].isin(CAT_ORD), "rut_docente"].nunique()
raw = raw[raw["jerarquia"].isin(CAT_ORD)].copy()
raw["escalafon"] = np.where(raw["jerarquia"].str.contains("REGULAR"), "Regular", "Docente")

tab = (raw.groupby("escalafon")
       .agg(n_evaluable=("aprueba", "count"),
            n_docentes=("rut_docente", "nunique"),
            pct_aprobacion=("aprueba", lambda s: 100 * s.mean()))
       .reindex(ESCALAFON_ORD))
tab["pct_reprobacion"] = 100 - tab["pct_aprobacion"]

print(f"Universo Jornada: {N_JORNADA}")
print(tab)
print(f"Excluidos (sin jerarquía válida): {N_SIN_JERARQUIA_DOC} docentes")

brecha = tab.loc["Docente", "pct_aprobacion"] - tab.loc["Regular", "pct_aprobacion"]
escalafon_mayor = "Docente" if brecha > 0 else "Regular"

# ── Datos a nivel docente, para la prueba t. Unidad de análisis = docente (no
# calificación individual) para evitar pseudo-repetición — mismo criterio que
# aprobacion_reprobacion_sexo/. ─────────────────────────────────────────────────
por_docente = (raw.groupby("rut_docente")
               .agg(escalafon=("escalafon", "first"),
                    pct_aprob=("aprueba", lambda s: 100 * s.mean()))
               .reset_index())

grupo_docente = por_docente.loc[por_docente["escalafon"] == "Docente", "pct_aprob"]
grupo_regular = por_docente.loc[por_docente["escalafon"] == "Regular", "pct_aprob"]
T_STAT, P_VAL = stats.ttest_ind(grupo_docente, grupo_regular, equal_var=False)   # Welch

print(f"\nPrueba t (por docente, Docente vs Regular): Docente N°={len(grupo_docente)} "
      f"media={grupo_docente.mean():.2f}%  Regular N°={len(grupo_regular)} "
      f"media={grupo_regular.mean():.2f}%  t={T_STAT:.3f}  p={P_VAL:.4f}")



# ── Revisión 2026-09-26 (obs. 2 y 21): una sola medida (promedio por docente, la unidad de la
# prueba t) y descriptivo + prueba en una sola diapositiva. La versión ponderada por
# calificación (tab) queda solo como referencia en notas. ────────────────────────────────
from pptx_helpers import lectura_p, prueba_dict

PRUEBAS = [prueba_dict("IV · Aprobación", "% aprobación por docente: escalafón Docente vs Regular",
                       f"{grupo_docente.mean():.1f}% vs {grupo_regular.mean():.1f}%",
                       len(grupo_docente) + len(grupo_regular), P_VAL)]


def agregar(prs):
    kit = UcenSlideKit(out_dir=HERE)
    kit.ensure_bg()
    series = [grupo_docente, grupo_regular]
    medias = [s.mean() for s in series]
    cis = [stats.t.ppf(0.975, len(s) - 1) * s.std(ddof=1) / np.sqrt(len(s)) for s in series]
    colors = ["#5C9BD6", "#FFB74D"]

    fig = kit.new_chart_fig()
    ax = kit.chart_axes(fig, top=0.14)
    x = np.arange(2)
    ax.bar(x, medias, width=0.42, color=colors, alpha=0.92, edgecolor="none",
           yerr=cis, capsize=6, error_kw={"ecolor": "#DDDDDD", "linewidth": 1.3})
    stroke = [pe.withStroke(linewidth=2, foreground="#0A0F18")]
    for xi, m, ci, s in zip(x, medias, cis, series):
        ax.text(xi, m + ci + 2.5, f"{m:.1f}%", ha="center", va="bottom", fontsize=13,
                fontweight="bold", color="white", path_effects=stroke, zorder=6)
        ax.text(xi, 8, f"N°={len(s)} docentes", ha="center", va="bottom", fontsize=8.5, color="white")
    sig = "significativa" if P_VAL < 0.05 else "no significativa"
    ax.text(0.5, 0.99, f"Prueba t de Welch:  t = {T_STAT:.2f}   ·   p = {P_VAL:.4f}   ·   diferencia {sig} al 5%",
            transform=ax.transAxes, ha="center", va="top", fontsize=9.5, color="#F2D675", fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels(ESCALAFON_ORD, fontsize=12, color="white")
    ax.set_ylabel("% de aprobación promedio por docente", color="#AAAAAA", fontsize=9)
    ax.set_ylim(0, 112); ax.set_yticks([0, 20, 40, 60, 80, 100])
    ax.tick_params(axis="x", length=0, pad=8); ax.tick_params(axis="y", colors="#AAAAAA", labelsize=8.5)
    for sp in ax.spines.values():
        sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.7)
    ax.yaxis.grid(True, color="white", alpha=0.07, linewidth=0.5); ax.set_axisbelow(True)
    chart_path = kit.save_chart(fig, "aprobacion_reprobacion_jerarquia_chart.png")

    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.pic_chart(sl, prs, chart_path)
    kit.title(sl, "¿Difiere el % de aprobación según escalafón? — Docentes Jornada")
    kit.subtitulo(sl, f"% de aprobación promedio por docente (no por calificación)  ·  "
                      f"N°={len(grupo_docente) + len(grupo_regular)} docentes con calificaciones y jerarquía "
                      f"válida  ·  barras = intervalo de confianza 95%")
    kit.punteo_numerado(sl, [
        f"Los docentes de escalafón Docente aprueban en promedio el {grupo_docente.mean():.1f}% de sus "
        f"calificaciones, vs {grupo_regular.mean():.1f}% en el escalafón Regular (diferencia de "
        f"{grupo_docente.mean() - grupo_regular.mean():.1f} puntos). " + lectura_p(P_VAL),
        f"El escalafón Regular tiene muchos menos docentes con calificaciones (N°={len(grupo_regular)} vs "
        f"N°={len(grupo_docente)}).",
    ], fs=12)
    kit.notas(sl,
        f"{N_SIN_JERARQUIA_DOC} docentes sin jerarquía válida, excluidos. Escalafón = Docente/Regular "
        f"(colapso de las 8 jerarquías). Se usa el promedio por docente porque es la unidad de la prueba t; "
        f"ponderado por calificación, el resultado va en el mismo sentido (Docente "
        f"{tab.loc['Docente', 'pct_aprobacion']:.1f}% vs Regular {tab.loc['Regular', 'pct_aprobacion']:.1f}%).")
    return sl


if __name__ == "__main__":
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(UcenSlideKit.SW_EMU), Emu(UcenSlideKit.SH_EMU)
    agregar(prs)
    prs.save(OUT_PPTX)
    print(f"\n✓ Guardado: {OUT_PPTX}")
