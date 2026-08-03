"""
P1 — Caracterización del Cuerpo Académico de Planta
Calificación EDD (Evaluación de Desempeño Docente) según Sexo del Docente — Jornada.

EDD = evaluación hecha por la jefatura/director (distinta de la evaluación
estudiantil de aprobacion_reprobacion*/evaluacion_apr|met|afo/). Fuente:
intel.evaluacion_jefes (D28, docs/DECISIONES_METODOLOGICAS.md), 1 fila por
docente×año de evaluación (2022-2025). El sexo es un atributo fijo del docente
(no varía entre años, confirmado: 0 casos con más de un valor) — la unidad de
análisis es 1 valor por docente: el promedio de `edd_total` entre los años con
evaluación registrada. Mismo criterio "promedio por docente, no por instancia"
que aprobacion_reprobacion_sexo/ (D26).

FUENTE: intel.evaluacion_jefes (Postgres, en vivo)
        + data/cascade/01_jornada/docentes_jornada.csv (universo de RUTs)
SALIDA: P1_edd_sexo.pptx (2 diapositivas) + edd_sexo_chart.png + edd_sexo_ttest_chart.png
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
OUT_PPTX = Path(OUTPUTS) / "pptx" / "P1_edd_sexo.pptx"
OUT_PPTX.parent.mkdir(parents=True, exist_ok=True)

DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"
SEXO_ORD = ["HOMBRE", "MUJER"]
COL_HOMBRE = "#5C9BD6"
COL_MUJER = "#FFB74D"

# ── Datos ───────────────────────────────────────────────────────────────────
doc = pd.read_csv(Path(CASCADE) / "01_jornada" / "docentes_jornada.csv", encoding="utf-8-sig")
N_JORNADA = len(doc)

engine = create_engine(DB_URL)
q = text("""
    SELECT rut_key, sexo, AVG(edd_total) AS edd_prom, COUNT(edd_total) AS n_años
    FROM intel.evaluacion_jefes
    WHERE tipo_contrato_tag = 'JORNADA' AND sexo IS NOT NULL AND edd_total IS NOT NULL
    GROUP BY rut_key, sexo
""")
with engine.connect() as conn:
    por_docente = pd.read_sql(q, conn)

N_TOTAL_EDD_DOC = int(pd.read_sql(text("""
    SELECT COUNT(DISTINCT rut_key) AS n FROM intel.evaluacion_jefes
    WHERE tipo_contrato_tag = 'JORNADA'
"""), engine).iloc[0, 0])
N_SIN_DATO = N_TOTAL_EDD_DOC - len(por_docente)

tab = (por_docente.groupby("sexo")["edd_prom"].agg(edd_prom="mean", n="count")
       .reindex(SEXO_ORD))

print(f"Universo Jornada: {N_JORNADA}  |  docentes con EDD válida: {len(por_docente)}  |  "
      f"sin sexo/edd_total: {N_SIN_DATO}")
print(tab)

hombre = por_docente.loc[por_docente["sexo"] == "HOMBRE", "edd_prom"]
mujer = por_docente.loc[por_docente["sexo"] == "MUJER", "edd_prom"]
T_STAT, P_VAL = stats.ttest_ind(mujer, hombre, equal_var=False)   # Welch

brecha = tab.loc["MUJER", "edd_prom"] - tab.loc["HOMBRE", "edd_prom"]
sexo_mayor = "Mujeres" if brecha > 0 else "Hombres"

print(f"\nPrueba t (por docente, Mujer vs Hombre): Mujer N°={len(mujer)} media={mujer.mean():.3f}  "
      f"Hombre N°={len(hombre)} media={hombre.mean():.3f}  t={T_STAT:.3f}  p={P_VAL:.4f}")


def agregar(prs):
    """Construye el gráfico descriptivo y agrega la diapositiva a `prs`."""
    kit = UcenSlideKit(out_dir=HERE)
    kit.ensure_bg()

    fig = kit.new_chart_fig()
    ax = kit.chart_axes(fig, top=0.10)

    x = np.arange(len(SEXO_ORD))
    colors = [COL_HOMBRE, COL_MUJER]
    ax.bar(x, tab["edd_prom"], width=0.45, color=colors, alpha=0.92, edgecolor="none")

    stroke = [pe.withStroke(linewidth=2, foreground="#0A0F18")]
    for xi, v, n, color in zip(x, tab["edd_prom"], tab["n"], colors):
        ax.text(xi, v + 0.015, f"{v:.2f}", ha="center", va="bottom",
                 fontsize=14, fontweight="bold", color=color, path_effects=stroke, zorder=6)
        ax.text(xi, 0.015, f"N°={int(n)} docentes", ha="center", va="bottom",
                 fontsize=8.5, color="white")

    ax.set_xticks(x)
    ax.set_xticklabels(["Hombre", "Mujer"], fontsize=12, color="white")
    ax.set_ylabel("Calificación EDD promedio (escala 0-1)", color="#AAAAAA", fontsize=9)
    ax.set_ylim(0, 1.15)
    ax.tick_params(axis="x", length=0, pad=8)
    ax.tick_params(axis="y", colors="#AAAAAA", labelsize=8.5)
    for sp in ax.spines.values():
        sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.7)
    ax.yaxis.grid(True, color="white", alpha=0.07, linewidth=0.5)
    ax.set_axisbelow(True)

    chart_path = kit.save_chart(fig, "edd_sexo_chart.png")

    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.pic_chart(sl, prs, chart_path)
    kit.title(sl, "Calificación EDD según Sexo del Docente — Jornada")
    kit.subtitulo(sl,
        f"Universo: {N_JORNADA} docentes Jornada  ·  "
        f"N°={len(por_docente)} con evaluación de desempeño (EDD) y sexo registrados")
    kit.notas(sl,
        f"{N_SIN_DATO} docentes con registro EDD excluidos por falta de sexo o de edd_total "
        f"válido. EDD = Evaluación de Desempeño Docente, hecha por la jefatura/director (D28) "
        f"— distinta de la evaluación estudiantil. Unidad de análisis: promedio de edd_total "
        f"por docente entre los años con evaluación registrada (2022-2025), ya que el sexo "
        f"no varía entre años. Fuente: intel.evaluacion_jefes.")
    kit.punteo_numerado(sl, [
        f"{sexo_mayor} tienen una calificación EDD promedio más alta: Mujeres "
        f"{tab.loc['MUJER','edd_prom']:.2f} vs Hombres {tab.loc['HOMBRE','edd_prom']:.2f} "
        f"(diferencia de {abs(brecha):.2f}).",
        "Ver prueba de significancia en la siguiente diapositiva.",
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
    colors = [COL_HOMBRE, COL_MUJER]

    fig = kit.new_chart_fig()
    ax = kit.chart_axes(fig, top=0.14)

    x = np.arange(2)
    ax.bar(x, medias, width=0.42, color=colors, alpha=0.92, edgecolor="none",
           yerr=cis, capsize=6, error_kw={"ecolor": "#DDDDDD", "linewidth": 1.3})

    stroke = [pe.withStroke(linewidth=2, foreground="#0A0F18")]
    for xi, media, ci, n, color in zip(x, medias, cis, ns, colors):
        ax.text(xi, media + ci + 0.015, f"{media:.2f}", ha="center", va="bottom",
                 fontsize=13, fontweight="bold", color=color, path_effects=stroke, zorder=6)
        ax.text(xi, 0.02, f"N°={n} docentes", ha="center", va="bottom",
                 fontsize=8.5, color="white")

    sig = "significativa" if P_VAL < 0.05 else "no significativa"
    ax.text(0.5, 0.99, f"Prueba t de Welch:  t = {T_STAT:.2f}   ·   p = {P_VAL:.4f}   ·   "
            f"diferencia {sig} al 5%", transform=ax.transAxes, ha="center", va="top",
            fontsize=9.5, color="#F2D675", fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(grupos, fontsize=12, color="white")
    ax.set_ylabel("Calificación EDD promedio (escala 0-1)", color="#AAAAAA", fontsize=9)
    ax.set_ylim(0, max(medias) * 1.5)
    ax.tick_params(axis="x", length=0, pad=8)
    ax.tick_params(axis="y", colors="#AAAAAA", labelsize=8.5)
    for sp in ax.spines.values():
        sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.7)
    ax.yaxis.grid(True, color="white", alpha=0.07, linewidth=0.5)
    ax.set_axisbelow(True)

    chart_path = kit.save_chart(fig, "edd_sexo_ttest_chart.png")

    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.pic_chart(sl, prs, chart_path)
    kit.title(sl, "¿El sexo del docente influye en la calificación EDD? — Prueba t, Jornada")
    kit.subtitulo(sl,
        f"Unidad de análisis: 1 valor por docente (promedio de edd_total entre años) "
        f"·  N°={len(hombre)+len(mujer)} docentes con sexo y EDD registrados  ·  "
        f"Barras = intervalo de confianza 95%")
    kit.punteo_numerado(sl, [
        f"Las docentes mujeres tienen una calificación EDD promedio de {mujer.mean():.2f}, vs "
        f"{hombre.mean():.2f} en hombres (diferencia de {mujer.mean()-hombre.mean():.2f}).",
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
