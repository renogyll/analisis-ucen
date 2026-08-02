"""
P1 — Caracterización del Cuerpo Académico de Planta
% de Aprobación y Reprobación de alumnos según Sexo del docente — Jornada.

Mismo patrón/metodología que aprobacion_reprobacion/ (ver ese script para el detalle:
CM aprueba vía catalogo_calificacion, universo acotado a Jornada — ver
docs/DECISIONES_METODOLOGICAS.md D26).

FUENTE: intel.rendimiento_academico_alumnos (Postgres, en vivo)
        + data/cascade/01_jornada/docentes_jornada.csv (universo de RUTs)
SALIDA: P1_aprobacion_reprobacion_sexo.pptx (1 diapositiva) + aprobacion_reprobacion_sexo_chart.png
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
OUT_PPTX = Path(OUTPUTS) / "pptx" / "P1_aprobacion_reprobacion_sexo.pptx"
OUT_PPTX.parent.mkdir(parents=True, exist_ok=True)

DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"

COL_APROBACION = "#3E9E68"
COL_REPROBACION = "#E4572E"
SEXO_ORD = ["HOMBRE", "MUJER"]

# ── Datos ───────────────────────────────────────────────────────────────────
doc = pd.read_csv(Path(CASCADE) / "01_jornada" / "docentes_jornada.csv", encoding="utf-8-sig")
N_JORNADA = len(doc)

engine = create_engine(DB_URL)
q = text("""
    SELECT sexo,
           COUNT(*) AS n_evaluable,
           COUNT(DISTINCT rut_docente) AS n_docentes,
           100.0 * AVG(aprueba::int) AS pct_aprobacion
    FROM intel.rendimiento_academico_alumnos
    WHERE tipo_contrato_tag = 'JORNADA' AND aprueba IS NOT NULL
    GROUP BY sexo
""")
with engine.connect() as conn:
    raw = pd.read_sql(q, conn)

N_SIN_SEXO_DOC = int(raw.loc[raw["sexo"].isna(), "n_docentes"].sum())
tab = raw[raw["sexo"].isin(SEXO_ORD)].set_index("sexo").reindex(SEXO_ORD)
tab["pct_reprobacion"] = 100 - tab["pct_aprobacion"]

print(f"Universo Jornada: {N_JORNADA}")
print(tab)
print(f"Excluidos (sin sexo registrado): {N_SIN_SEXO_DOC} docentes")

brecha = tab.loc["MUJER", "pct_aprobacion"] - tab.loc["HOMBRE", "pct_aprobacion"]
sexo_mayor = "Mujeres" if brecha > 0 else "Hombres"

# ── Datos a nivel docente, para la prueba t. Unidad de análisis = docente (no
# calificación individual) para evitar pseudo-repetición — mismo criterio que
# aprobacion_reprobacion_edad/. ─────────────────────────────────────────────────
q2 = text("""
    SELECT rut_docente, sexo, aprueba
    FROM intel.rendimiento_academico_alumnos
    WHERE tipo_contrato_tag = 'JORNADA' AND aprueba IS NOT NULL
""")
with engine.connect() as conn:
    raw_ind = pd.read_sql(q2, conn)

por_docente = (raw_ind.groupby("rut_docente")
               .agg(sexo=("sexo", "first"),
                    pct_aprob=("aprueba", lambda s: 100 * s.mean()))
               .reset_index())

hombre = por_docente.loc[por_docente["sexo"] == "HOMBRE", "pct_aprob"]
mujer = por_docente.loc[por_docente["sexo"] == "MUJER", "pct_aprob"]
T_STAT, P_VAL = stats.ttest_ind(mujer, hombre, equal_var=False)   # Welch

print(f"\nPrueba t (por docente, Mujer vs Hombre): Mujer N°={len(mujer)} media={mujer.mean():.2f}%  "
      f"Hombre N°={len(hombre)} media={hombre.mean():.2f}%  t={T_STAT:.3f}  p={P_VAL:.4f}")


def agregar(prs):
    """Construye el gráfico y agrega la diapositiva a `prs`."""
    kit = UcenSlideKit(out_dir=HERE)
    kit.ensure_bg()

    fig = kit.new_chart_fig()
    ax = kit.chart_axes(fig, top=0.15)   # deja espacio arriba para la leyenda

    x = np.arange(len(SEXO_ORD))
    w = 0.34
    bars_a = ax.bar(x - w/2, tab["pct_aprobacion"], width=w, color=COL_APROBACION,
                     alpha=0.92, edgecolor="none", label="% Aprobación")
    bars_r = ax.bar(x + w/2, tab["pct_reprobacion"], width=w, color=COL_REPROBACION,
                     alpha=0.92, edgecolor="none", label="% Reprobación")

    stroke = [pe.withStroke(linewidth=2, foreground="#0A0F18")]
    for bars, color in [(bars_a, COL_APROBACION), (bars_r, COL_REPROBACION)]:
        for b in bars:
            h = b.get_height()
            ax.text(b.get_x() + b.get_width()/2, h + 1.5, f"{h:.1f}%",
                     ha="center", va="bottom", fontsize=10, fontweight="bold",
                     color=color, path_effects=stroke, zorder=6)
    # N° de docentes con calificaciones, una vez por sexo
    for xi, n in zip(x, tab["n_docentes"]):
        ax.text(xi, 100, f"N°={int(n)} docentes", ha="center", va="bottom",
                fontsize=8, color="#8A97A3")

    ax.set_xticks(x)
    ax.set_xticklabels(["Hombre", "Mujer"], fontsize=12, color="white")
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

    chart_path = kit.save_chart(fig, "aprobacion_reprobacion_sexo_chart.png")

    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.pic_chart(sl, prs, chart_path)
    kit.title(sl, "% de Aprobación y Reprobación según Sexo del Docente — Jornada")
    kit.subtitulo(sl,
        f"Universo: {N_JORNADA} docentes Jornada  ·  "
        f"N°={int(tab['n_docentes'].sum())} con calificaciones y sexo registrados "
        f"({N_SIN_SEXO_DOC} excluidos sin sexo)")
    kit.punteo_numerado(sl, [
        f"{sexo_mayor} tienen mayor % de aprobación: Mujeres {tab.loc['MUJER','pct_aprobacion']:.1f}% "
        f"vs Hombres {tab.loc['HOMBRE','pct_aprobacion']:.1f}% (diferencia de {abs(brecha):.1f} puntos).",
        f"El % de reprobación es mayor entre docentes hombres "
        f"({tab.loc['HOMBRE','pct_reprobacion']:.1f}% vs {tab.loc['MUJER','pct_reprobacion']:.1f}% en mujeres).",
    ])
    return sl


def agregar_ttest(prs):
    """Construye el gráfico de la prueba t (Hombre vs Mujer) y agrega la diapositiva a `prs`."""
    kit = UcenSlideKit(out_dir=HERE)
    kit.ensure_bg()

    grupos = ["Hombre", "Mujer"]
    medias = [hombre.mean(), mujer.mean()]
    ns = [len(hombre), len(mujer)]
    cis = [stats.t.ppf(0.975, n - 1) * s.std(ddof=1) / np.sqrt(n)
           for s, n in [(hombre, len(hombre)), (mujer, len(mujer))]]
    colors = ["#5C9BD6", "#FFB74D"]   # mismo par que edad_sexo/ (Hombre azul, Mujer naranjo)

    fig = kit.new_chart_fig()
    ax = kit.chart_axes(fig, top=0.14)

    x = np.arange(2)
    ax.bar(x, medias, width=0.42, color=colors, alpha=0.92, edgecolor="none",
           yerr=cis, capsize=6, error_kw={"ecolor": "#DDDDDD", "linewidth": 1.3})

    stroke = [pe.withStroke(linewidth=2, foreground="#0A0F18")]
    for xi, media, ci, n, color in zip(x, medias, cis, ns, colors):
        ax.text(xi, media + ci + 2.5, f"{media:.1f}%", ha="center", va="bottom",
                 fontsize=13, fontweight="bold", color=color, path_effects=stroke, zorder=6)
        ax.text(xi, 8, f"N°={n} docentes", ha="center", va="bottom",
                 fontsize=8.5, color="white")

    sig = "significativa" if P_VAL < 0.05 else "no significativa"
    ax.text(0.5, 0.99, f"Prueba t de Welch:  t = {T_STAT:.2f}   ·   p = {P_VAL:.4f}   ·   "
            f"diferencia {sig} al 5%", transform=ax.transAxes, ha="center", va="top",
            fontsize=9.5, color="#F2D675", fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(grupos, fontsize=12, color="white")
    ax.set_ylabel("% de aprobación promedio por docente", color="#AAAAAA", fontsize=9)
    ax.set_ylim(0, 112)
    ax.set_yticks([0, 20, 40, 60, 80, 100])
    ax.tick_params(axis="x", length=0, pad=8)
    ax.tick_params(axis="y", colors="#AAAAAA", labelsize=8.5)
    for sp in ax.spines.values():
        sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.7)
    ax.yaxis.grid(True, color="white", alpha=0.07, linewidth=0.5)
    ax.set_axisbelow(True)

    chart_path = kit.save_chart(fig, "aprobacion_reprobacion_sexo_ttest_chart.png")

    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.pic_chart(sl, prs, chart_path)
    kit.title(sl, "¿El sexo del docente influye en el % de Aprobación? — Prueba t, Jornada")
    kit.subtitulo(sl,
        f"Unidad de análisis: % de aprobación promedio por docente (no por calificación individual) "
        f"·  N°={len(hombre)+len(mujer)} docentes con sexo registrado  ·  Barras = intervalo de confianza 95%")
    kit.punteo_numerado(sl, [
        f"Las docentes mujeres aprueban en promedio {mujer.mean():.1f}% de sus calificaciones, vs "
        f"{hombre.mean():.1f}% en hombres (diferencia de {mujer.mean()-hombre.mean():.1f} puntos).",
        f"La prueba t de Welch da p={P_VAL:.4f} — la diferencia {'sí' if P_VAL<0.05 else 'no'} es "
        f"estadísticamente significativa al 5% (con estos N°, {'se puede' if P_VAL<0.05 else 'no se puede'} "
        f"descartar que la diferencia observada se deba al azar).",
    ])
    return sl


if __name__ == "__main__":
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(UcenSlideKit.SW_EMU), Emu(UcenSlideKit.SH_EMU)
    agregar(prs)
    agregar_ttest(prs)
    prs.save(OUT_PPTX)
    print(f"\n✓ Guardado: {OUT_PPTX}")
