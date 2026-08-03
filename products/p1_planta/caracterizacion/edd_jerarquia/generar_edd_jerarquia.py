"""
P1 — Caracterización del Cuerpo Académico de Planta
Calificación EDD (Evaluación de Desempeño Docente) según Jerarquía — Jornada.

EDD = evaluación hecha por la jefatura/director (D28), distinta de la evaluación
estudiantil. Descriptivo con las 8 categorías completas de jerarquía (D25), mismo
estilo que edad_jerarquia/ (barra horizontal ordenada por magnitud, con textura
para N chicos). La prueba t usa escalafón binario (Docente=0/Regular=1) — mismo
colapso que jerarquia_dificultad/, porque jerarquía no es continua y el escalafón
es la única partición binaria natural. La jerarquía es un atributo fijo del
docente (no varía entre años, confirmado: 0 casos con más de un valor), así que
la unidad de análisis es 1 valor por docente: el promedio de `edd_total` entre
los años con evaluación registrada.

FUENTE: intel.evaluacion_jefes (Postgres, en vivo)
        + data/cascade/01_jornada/docentes_jornada.csv (universo de RUTs)
SALIDA: P1_edd_jerarquia.pptx (2 diapositivas) + edd_jerarquia_chart.png
        + edd_jerarquia_ttest_chart.png
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
OUT_PPTX = Path(OUTPUTS) / "pptx" / "P1_edd_jerarquia.pptx"
OUT_PPTX.parent.mkdir(parents=True, exist_ok=True)

DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"

CAT_ORD = ["INSTRUCTOR DOCENTE", "INSTRUCTOR REGULAR",
           "ASISTENTE DOCENTE",  "ASISTENTE REGULAR",
           "ASOCIADO DOCENTE",   "ASOCIADO REGULAR",
           "TITULAR DOCENTE",    "TITULAR REGULAR"]
CAT_LABEL = {c: c.title() for c in CAT_ORD}
NIVEL_COLORS = ["#AFCBE8", "#7FADD9", "#4E8FC9", "#1F5C99"]
CAT_COLORS = {cat: NIVEL_COLORS[i // 2] for i, cat in enumerate(CAT_ORD)}
CAT_COLORS["TITULAR REGULAR"] = "#5C8CB3"   # mismo matiz distintivo que edad_jerarquia/
N_MIN_CONFIABLE = 15

COL_DOCENTE = "#5C9BD6"
COL_REGULAR = "#FFB74D"

# ── Datos: promedio de edd_total por docente, 1 fila por docente ──────────────
doc = pd.read_csv(Path(CASCADE) / "01_jornada" / "docentes_jornada.csv", encoding="utf-8-sig")
N_JORNADA = len(doc)

engine = create_engine(DB_URL)
q = text("""
    SELECT rut_key, jerarquia, AVG(edd_total) AS edd_prom, COUNT(edd_total) AS n_años
    FROM intel.evaluacion_jefes
    WHERE tipo_contrato_tag = 'JORNADA' AND jerarquia IS NOT NULL AND edd_total IS NOT NULL
    GROUP BY rut_key, jerarquia
""")
with engine.connect() as conn:
    por_docente = pd.read_sql(q, conn)
por_docente = por_docente[por_docente["jerarquia"].isin(CAT_ORD)].copy()

N_TOTAL_EDD_DOC = int(pd.read_sql(text("""
    SELECT COUNT(DISTINCT rut_key) AS n FROM intel.evaluacion_jefes
    WHERE tipo_contrato_tag = 'JORNADA'
"""), engine).iloc[0, 0])
N_SIN_DATO = N_TOTAL_EDD_DOC - len(por_docente)

tab = (por_docente.groupby("jerarquia")["edd_prom"].agg(edd_prom="mean", n="count")
       .reindex(CAT_ORD))

print(f"Universo Jornada: {N_JORNADA}  |  docentes con EDD+jerarquía válidas: {len(por_docente)}  |  "
      f"excluidos: {N_SIN_DATO}")
print(tab)

tab_display = tab.dropna(subset=["edd_prom"]).sort_values("edd_prom", ascending=False)
CAT_DISPLAY = tab_display.index.tolist()

cat_mayor = tab_display["edd_prom"].idxmax()
cat_menor = tab_display["edd_prom"].idxmin()
cats_muestra_chica = tab_display.index[tab_display["n"] < N_MIN_CONFIABLE].tolist()

# ── Prueba t: escalafón binario (Docente=0/Regular=1), 1 valor por docente ────
por_docente["es_regular"] = por_docente["jerarquia"].str.contains("REGULAR").astype(int)

docente_g = por_docente.loc[por_docente["es_regular"] == 0, "edd_prom"]
regular_g = por_docente.loc[por_docente["es_regular"] == 1, "edd_prom"]
T_STAT, P_VAL = stats.ttest_ind(regular_g, docente_g, equal_var=False)   # Welch

print(f"\nPrueba t (por docente, escalafón Regular vs Docente): "
      f"Regular N°={len(regular_g)} media={regular_g.mean():.3f}  "
      f"Docente N°={len(docente_g)} media={docente_g.mean():.3f}  t={T_STAT:.3f}  p={P_VAL:.4f}")


def agregar(prs):
    """Construye el gráfico descriptivo (8 categorías) y agrega la diapositiva a `prs`."""
    kit = UcenSlideKit(out_dir=HERE)
    kit.ensure_bg()

    fig = kit.new_chart_fig()
    ax = kit.chart_axes(fig, left=0.22)

    y = np.arange(len(CAT_DISPLAY))
    colors = [CAT_COLORS[c] for c in CAT_DISPLAY]
    n_vals = tab_display["n"].values
    alphas = np.clip(0.35 + 0.65 * np.sqrt(n_vals) / np.sqrt(n_vals.max()), 0.35, 0.97)
    hatches = ["///" if n < N_MIN_CONFIABLE else None for n in n_vals]

    for i, (v, n, color, alpha, hatch) in enumerate(
            zip(tab_display["edd_prom"], n_vals, colors, alphas, hatches)):
        ax.barh(i, v, height=0.62, color=color, alpha=alpha, edgecolor="none",
                hatch=hatch, zorder=3)

    stroke = [pe.withStroke(linewidth=2, foreground="#0A0F18")]
    for i, (v, n) in enumerate(zip(tab_display["edd_prom"], n_vals)):
        marca = " ⚠" if n < N_MIN_CONFIABLE else ""
        ax.text(v + 0.015, i, f"{v:.2f}   (N°={int(n)}{marca})",
                ha="left", va="center", fontsize=9.5, fontweight="bold",
                color=colors[i], path_effects=stroke, zorder=6)

    ax.set_yticks(y)
    ax.set_yticklabels([CAT_LABEL[c] for c in CAT_DISPLAY], fontsize=10, color="white")
    ax.invert_yaxis()
    ax.set_xlabel("Calificación EDD promedio (escala 0-1)", color="#AAAAAA", fontsize=9)
    ax.set_xlim(0, tab_display["edd_prom"].max() * 1.30)
    ax.tick_params(axis="y", length=0, pad=8)
    ax.tick_params(axis="x", colors="#AAAAAA", labelsize=8.5)
    for sp in ax.spines.values():
        sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.7)
    ax.xaxis.grid(True, color="white", alpha=0.07, linewidth=0.5)
    ax.set_axisbelow(True)

    chart_path = kit.save_chart(fig, "edd_jerarquia_chart.png")

    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.pic_chart(sl, prs, chart_path)
    kit.title(sl, "Calificación EDD según Jerarquía — Docentes de Jornada")
    kit.subtitulo(sl,
        f"Universo: {N_JORNADA} docentes Jornada  ·  "
        f"N°={len(por_docente)} con evaluación de desempeño (EDD) y jerarquía registradas")
    kit.notas(sl,
        f"{N_SIN_DATO} docentes con registro EDD excluidos por falta de jerarquía válida o "
        f"edd_total. EDD = Evaluación de Desempeño Docente, hecha por la jefatura/director "
        f"(D28). Unidad de análisis: promedio de edd_total por docente entre los años con "
        f"evaluación registrada, ya que la jerarquía no varía entre años. "
        f"Fuente: intel.evaluacion_jefes.")
    bullets = [
        f"{CAT_LABEL[cat_mayor]} tiene la calificación EDD promedio más alta "
        f"({tab_display.loc[cat_mayor,'edd_prom']:.2f}, N°={int(tab_display.loc[cat_mayor,'n'])}), "
        f"y {CAT_LABEL[cat_menor]} la más baja "
        f"({tab_display.loc[cat_menor,'edd_prom']:.2f}, N°={int(tab_display.loc[cat_menor,'n'])}).",
    ]
    if cats_muestra_chica:
        nombres = ", ".join(CAT_LABEL[c] for c in cats_muestra_chica)
        bullets.append(
            f"⚠ {nombres} tiene{'n' if len(cats_muestra_chica) > 1 else ''} menos de "
            f"{N_MIN_CONFIABLE} casos — su promedio no es representativo, se marca con textura "
            f"en el gráfico."
        )
    bullets.append("Ver prueba de significancia por escalafón (Docente/Regular) en la siguiente diapositiva.")
    kit.punteo_numerado(sl, bullets)
    return sl


def agregar_ttest(prs):
    """Construye el gráfico de la prueba t (escalafón Docente vs Regular) y agrega
    la diapositiva a `prs`."""
    kit = UcenSlideKit(out_dir=HERE)
    kit.ensure_bg()

    grupos = ["Docente", "Regular"]
    medias = [docente_g.mean(), regular_g.mean()]
    ns = [len(docente_g), len(regular_g)]
    cis = [stats.t.ppf(0.975, n - 1) * s.std(ddof=1) / np.sqrt(n)
           for s, n in [(docente_g, len(docente_g)), (regular_g, len(regular_g))]]
    colors = [COL_DOCENTE, COL_REGULAR]

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

    chart_path = kit.save_chart(fig, "edd_jerarquia_ttest_chart.png")

    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.pic_chart(sl, prs, chart_path)
    kit.title(sl, "¿El escalafón influye en la calificación EDD? — Prueba t, Jornada")
    kit.subtitulo(sl,
        f"Unidad de análisis: 1 valor por docente (promedio de edd_total entre años) "
        f"·  N°={len(docente_g)+len(regular_g)} docentes con jerarquía y EDD registradas  ·  "
        f"Barras = intervalo de confianza 95%")
    kit.notas(sl,
        "Escalafón Docente/Regular, mismo colapso que jerarquia_dificultad/ y "
        "aprobacion_reprobacion_jerarquia/ — no el cruce completo de 8 categorías.")
    kit.punteo_numerado(sl, [
        f"Los docentes de escalafón Regular tienen una calificación EDD promedio de "
        f"{regular_g.mean():.2f}, vs {docente_g.mean():.2f} en escalafón Docente "
        f"(diferencia de {regular_g.mean()-docente_g.mean():.2f}).",
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
