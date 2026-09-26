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



# ── Revisión 2026-09-26 (obs. 2 y 7) ──────────────────────────────────────────────────
# Misma medida que sexo/escalafón: % de aprobación promedio POR DOCENTE (no por calificación),
# con intervalo de confianza, y una prueba que antes no se mostraba: ANOVA de un factor entre
# los 4 tramos (Kruskal-Wallis como verificación no paramétrica, en notas). Respalda la frase
# "por antigüedad no hay diferencias significativas" del Bloque IV.
from scipy import stats
from pptx_helpers import prueba_dict

por_docente = (raw.groupby(["rut_docente", "tramo_antiguedad"])["aprueba"].mean().mul(100)
               .reset_index(name="pct_aprob"))
series = {t: por_docente.loc[por_docente["tramo_antiguedad"] == t, "pct_aprob"] for t in TRAMOS_ORD}
F_STAT, P_VAL = stats.f_oneway(*series.values())
P_KRUSKAL = stats.kruskal(*series.values()).pvalue
PRUEBAS = [prueba_dict("IV · Aprobación", "% aprobación por docente según tramo de antigüedad (4 tramos)",
                       " / ".join(f"{t}: {s.mean():.1f}%" for t, s in series.items()),
                       len(por_docente), P_VAL, prueba="ANOVA de un factor")]
print({t: round(s.mean(), 1) for t, s in series.items()}, f"ANOVA p={P_VAL:.4f}  Kruskal p={P_KRUSKAL:.4f}")


def agregar(prs):
    kit = UcenSlideKit(out_dir=HERE)
    kit.ensure_bg()
    medias = [series[t].mean() for t in TRAMOS_ORD]
    cis = [stats.t.ppf(0.975, len(series[t]) - 1) * series[t].std(ddof=1) / np.sqrt(len(series[t]))
           for t in TRAMOS_ORD]

    fig = kit.new_chart_fig()
    ax = kit.chart_axes(fig, top=0.14)
    x = np.arange(len(TRAMOS_ORD))
    ax.bar(x, medias, width=0.5, color=COL_APROBACION, alpha=0.92, edgecolor="none",
           yerr=cis, capsize=6, error_kw={"ecolor": "#DDDDDD", "linewidth": 1.3})
    stroke = [pe.withStroke(linewidth=2, foreground="#0A0F18")]
    for xi, m, ci, t in zip(x, medias, cis, TRAMOS_ORD):
        ax.text(xi, m + ci + 2.5, f"{m:.1f}%", ha="center", va="bottom", fontsize=12,
                fontweight="bold", color="white", path_effects=stroke, zorder=6)
        ax.text(xi, 8, f"N°={len(series[t])} docentes", ha="center", va="bottom", fontsize=8.5, color="white")
    sig = "significativa" if P_VAL < 0.05 else "no significativa"
    ax.text(0.5, 0.99, f"ANOVA de un factor entre los 4 tramos:  F = {F_STAT:.2f}   ·   p = {P_VAL:.4f}   ·   "
            f"diferencia {sig} al 5%", transform=ax.transAxes, ha="center", va="top",
            fontsize=9.5, color="#F2D675", fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels(TRAMOS_ORD, fontsize=11, color="white")
    ax.set_xlabel("Tramo de antigüedad en la institución (años)", color="#AAAAAA", fontsize=9)
    ax.set_ylabel("% de aprobación promedio por docente", color="#AAAAAA", fontsize=9)
    ax.set_ylim(0, 112); ax.set_yticks([0, 20, 40, 60, 80, 100])
    ax.tick_params(axis="x", length=0, pad=8); ax.tick_params(axis="y", colors="#AAAAAA", labelsize=8.5)
    for sp in ax.spines.values():
        sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.7)
    ax.yaxis.grid(True, color="white", alpha=0.07, linewidth=0.5); ax.set_axisbelow(True)
    chart_path = kit.save_chart(fig, "aprobacion_reprobacion_antiguedad_4tramos_chart.png")

    mejor, peor = max(series, key=lambda t: series[t].mean()), min(series, key=lambda t: series[t].mean())
    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.pic_chart(sl, prs, chart_path)
    kit.title(sl, "% de aprobación según antigüedad del docente — Docentes Jornada")
    kit.subtitulo(sl, f"% de aprobación promedio por docente  ·  N°={len(por_docente)} docentes con calificaciones "
                      f"y antigüedad registrada ({N_SIN_ANTIGUEDAD_DOC} sin dato de antigüedad)  ·  "
                      f"barras = intervalo de confianza 95%")
    kit.punteo_numerado(sl, [
        f"El % de aprobación va de {series[peor].mean():.1f}% (tramo {peor}) a {series[mejor].mean():.1f}% "
        f"(tramo {mejor}).",
        f"El ANOVA entre los 4 tramos da p={P_VAL:.4f}: "
        + ("la diferencia es estadísticamente significativa al 5%."
           if P_VAL < 0.05 else "la antigüedad no se asocia de forma significativa con el % de aprobación."),
    ], fs=12)
    kit.notas(sl,
        f"Verificación no paramétrica (Kruskal-Wallis): p={P_KRUSKAL:.4f}. El tramo 15+ tiene pocos docentes "
        f"(N°={len(series['15+'])}) y un intervalo amplio. Tramos de antigüedad desde la fecha de ingreso (DOTACION).")
    return sl


if __name__ == "__main__":
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(UcenSlideKit.SW_EMU), Emu(UcenSlideKit.SH_EMU)
    agregar(prs)
    prs.save(OUT_PPTX)
    print(f"\n✓ Guardado: {OUT_PPTX}")
