"""
P1 — Caracterización del Cuerpo Académico de Planta
Participación en Instancias Formativas según Jerarquía — Docentes de Jornada.

Participación = tasa de docentes con al menos 1 instancia formativa (Taller,
Diplomado o Proyecto) registrada. Descriptivo con las 8 categorías completas
de jerarquía (D25), mismo estilo que edad_jerarquia/edd_jerarquia/ (barra
horizontal ordenada por magnitud, con textura para N chicos). La prueba t usa
escalafón binario (Docente=0/Regular=1) — mismo colapso que el resto de P1,
porque jerarquía no es continua.

FUENTE: analisis.universo_base (Postgres, en vivo) — universo Jornada
        + analisis.universo_formados_p3 (Postgres, en vivo) — ver D31
SALIDA: P1_participacion_formacion_jerarquia.pptx (2 diapositivas)
        + participacion_formacion_jerarquia_chart.png
        + participacion_formacion_jerarquia_ttest_chart.png
"""
import sys; sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "shared"))
from config import OUTPUTS
from pptx_helpers import UcenSlideKit, lectura_p, prueba_dict, encabezado_prueba

import numpy as np
import pandas as pd
import matplotlib.patheffects as pe
from scipy import stats
from sqlalchemy import create_engine, text
from pptx import Presentation
from pptx.util import Emu

HERE = Path(__file__).parent
OUT_PPTX = Path(OUTPUTS) / "pptx" / "P1_participacion_formacion_jerarquia.pptx"
OUT_PPTX.parent.mkdir(parents=True, exist_ok=True)

DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"

CAT_ORD = ["INSTRUCTOR DOCENTE", "INSTRUCTOR REGULAR",
           "ASISTENTE DOCENTE",  "ASISTENTE REGULAR",
           "ASOCIADO DOCENTE",   "ASOCIADO REGULAR",
           "TITULAR DOCENTE",    "TITULAR REGULAR"]
CAT_LABEL = {c: c.title() for c in CAT_ORD}
NIVEL_COLORS = ["#AFCBE8", "#7FADD9", "#4E8FC9", "#1F5C99"]
CAT_COLORS = {cat: NIVEL_COLORS[i // 2] for i, cat in enumerate(CAT_ORD)}
CAT_COLORS["TITULAR REGULAR"] = "#5C8CB3"
N_MIN_CONFIABLE = 15

COL_DOCENTE = "#5C9BD6"
COL_REGULAR = "#FFB74D"

# ── Datos ───────────────────────────────────────────────────────────────────
engine = create_engine(DB_URL)
base = pd.read_sql(text("""
    SELECT rut_key, jerarquia FROM analisis.universo_base WHERE tipo_contrato_tag='JORNADA'
"""), engine)
N_JORNADA = len(base)

participantes = set(pd.read_sql(text("""
    SELECT DISTINCT rut_key FROM analisis.universo_formados_p3 WHERE tipo_contrato_tag='JORNADA'
"""), engine)["rut_key"])

base["participo"] = base["rut_key"].isin(participantes).astype(int)

con_jer = base[base["jerarquia"].isin(CAT_ORD)].copy()
N_SIN_JERARQUIA = N_JORNADA - len(con_jer)

tab = (con_jer.groupby("jerarquia")["participo"].agg(tasa="mean", n="count")
       .reindex(CAT_ORD))
tab["tasa"] *= 100

print(f"Universo Jornada: {N_JORNADA}  |  con jerarquía válida: {len(con_jer)}  |  "
      f"excluidos: {N_SIN_JERARQUIA}")
print(tab)

tab_display = tab.sort_values("tasa", ascending=False)
CAT_DISPLAY = tab_display.index.tolist()
cat_mayor = tab_display["tasa"].idxmax()
cat_menor = tab_display["tasa"].idxmin()
cats_muestra_chica = tab_display.index[tab_display["n"] < N_MIN_CONFIABLE].tolist()

# ── Prueba t: escalafón binario (Docente=0/Regular=1) ──────────────────────────
con_jer["es_regular"] = con_jer["jerarquia"].str.contains("REGULAR").astype(int)
docente_g = con_jer.loc[con_jer["es_regular"] == 0, "participo"]
regular_g = con_jer.loc[con_jer["es_regular"] == 1, "participo"]
T_STAT, P_VAL = stats.ttest_ind(regular_g, docente_g, equal_var=False)   # Welch
CLAVE = "Participación: escalafón Regular vs Docente"   # = comparación registrada en PRUEBAS (p corregido por Holm)
PRUEBAS = [prueba_dict("II · Participación", "Participación: escalafón Regular vs Docente",
                       f"{100 * regular_g.mean():.1f}% vs {100 * docente_g.mean():.1f}%",
                       len(regular_g) + len(docente_g), P_VAL)]

print(f"\nPrueba t (escalafón Regular vs Docente, participó=1/no=0): "
      f"Regular N°={len(regular_g)} tasa={100*regular_g.mean():.1f}%  "
      f"Docente N°={len(docente_g)} tasa={100*docente_g.mean():.1f}%  t={T_STAT:.3f}  p={P_VAL:.4f}")


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
            zip(tab_display["tasa"], n_vals, colors, alphas, hatches)):
        ax.barh(i, v, height=0.62, color=color, alpha=alpha, edgecolor="none",
                hatch=hatch, zorder=3)

    stroke = [pe.withStroke(linewidth=2, foreground="#0A0F18")]
    for i, (v, n) in enumerate(zip(tab_display["tasa"], n_vals)):
        marca = " ⚠" if n < N_MIN_CONFIABLE else ""
        ax.text(v + 1.5, i, f"{v:.1f}%   (N°={int(n)}{marca})",
                ha="left", va="center", fontsize=9.5, fontweight="bold",
                color="white", path_effects=stroke, zorder=6)

    ax.set_yticks(y)
    ax.set_yticklabels([CAT_LABEL[c] for c in CAT_DISPLAY], fontsize=10, color="white")
    ax.invert_yaxis()
    ax.set_xlabel("% con ≥1 instancia formativa", color="#AAAAAA", fontsize=9)
    ax.set_xlim(0, min(100, tab_display["tasa"].max() * 1.30))
    ax.tick_params(axis="y", length=0, pad=8)
    ax.tick_params(axis="x", colors="#AAAAAA", labelsize=8.5)
    for sp in ax.spines.values():
        sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.7)
    ax.xaxis.grid(True, color="white", alpha=0.07, linewidth=0.5)
    ax.set_axisbelow(True)

    chart_path = kit.save_chart(fig, "participacion_formacion_jerarquia_chart.png")

    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.pic_chart(sl, prs, chart_path)
    kit.title(sl, "Participación en instancias formativas según jerarquía — Docentes Jornada")
    kit.subtitulo(sl,
        f"Universo: {N_JORNADA} docentes Jornada  ·  "
        f"N°={len(con_jer)} con jerarquía válida")
    kit.notas(sl,
        f"{N_SIN_JERARQUIA} docentes sin jerarquía válida (SIN JERARQUÍA o sin dato), "
        f"excluidos. Participación = al menos 1 instancia formativa 2022-2025. "
        f"Fuente: analisis.universo_formados_p3 (D31).")
    bullets = [
        f"{CAT_LABEL[cat_mayor]} tiene la tasa de participación más alta "
        f"({tab_display.loc[cat_mayor,'tasa']:.1f}%, N°={int(tab_display.loc[cat_mayor,'n'])}), "
        f"y {CAT_LABEL[cat_menor]} la más baja "
        f"({tab_display.loc[cat_menor,'tasa']:.1f}%, N°={int(tab_display.loc[cat_menor,'n'])}).",
    ]
    if cats_muestra_chica:
        nombres = ", ".join(CAT_LABEL[c] for c in cats_muestra_chica)
        bullets.append(
            f"⚠ {nombres} tiene{'n' if len(cats_muestra_chica) > 1 else ''} menos de "
            f"{N_MIN_CONFIABLE} casos — su tasa no es representativa, se marca con textura "
            f"en el gráfico."
        )
    # Revisión 2026-09-26 (obs. 21): la prueba por escalafón va en esta misma diapositiva.
    bullets.insert(1, f"Por escalafón: Docente {100 * docente_g.mean():.1f}% vs Regular "
                      f"{100 * regular_g.mean():.1f}%. " + lectura_p(P_VAL, clave=CLAVE))
    kit.punteo_numerado(sl, bullets, fs=12)
    return sl


def agregar_ttest(prs):
    """Construye el gráfico de la prueba t (escalafón Docente vs Regular) y agrega
    la diapositiva a `prs`."""
    kit = UcenSlideKit(out_dir=HERE)
    kit.ensure_bg()

    grupos = ["Docente", "Regular"]
    medias = [100 * docente_g.mean(), 100 * regular_g.mean()]
    ns = [len(docente_g), len(regular_g)]
    cis = [100 * stats.t.ppf(0.975, n - 1) * s.std(ddof=1) / np.sqrt(n)
           for s, n in [(docente_g, len(docente_g)), (regular_g, len(regular_g))]]
    colors = [COL_DOCENTE, COL_REGULAR]

    fig = kit.new_chart_fig()
    ax = kit.chart_axes(fig, top=0.14)

    x = np.arange(2)
    ax.bar(x, medias, width=0.42, color=colors, alpha=0.92, edgecolor="none",
           yerr=cis, capsize=6, error_kw={"ecolor": "#DDDDDD", "linewidth": 1.3})

    stroke = [pe.withStroke(linewidth=2, foreground="#0A0F18")]
    for xi, media, ci, n, color in zip(x, medias, cis, ns, colors):
        ax.text(xi, media + ci + 1.5, f"{media:.1f}%", ha="center", va="bottom",
                 fontsize=13, fontweight="bold", color=color, path_effects=stroke, zorder=6)
        ax.text(xi, 2, f"N°={n} docentes", ha="center", va="bottom",
                 fontsize=8.5, color="white")

    ax.text(0.5, 0.99, encabezado_prueba("Prueba t de Welch", "t", T_STAT, P_VAL, CLAVE),
            transform=ax.transAxes, ha="center", va="top",
            fontsize=9.5, color="#F2D675", fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(grupos, fontsize=12, color="white")
    ax.set_ylabel("% con ≥1 instancia formativa", color="#AAAAAA", fontsize=9)
    ax.set_ylim(0, 100)
    ax.tick_params(axis="x", length=0, pad=8)
    ax.tick_params(axis="y", colors="#AAAAAA", labelsize=8.5)
    for sp in ax.spines.values():
        sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.7)
    ax.yaxis.grid(True, color="white", alpha=0.07, linewidth=0.5)
    ax.set_axisbelow(True)

    chart_path = kit.save_chart(fig, "participacion_formacion_jerarquia_ttest_chart.png")

    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.pic_chart(sl, prs, chart_path)
    kit.title(sl, "¿El escalafón influye en la participación formativa? — Prueba t, Jornada")
    kit.subtitulo(sl,
        f"Unidad de análisis: 1 valor por docente (participó=1/no participó=0) "
        f"·  N°={len(docente_g)+len(regular_g)} docentes con jerarquía válida  ·  "
        f"Barras = intervalo de confianza 95%")
    kit.notas(sl,
        "Escalafón Docente/Regular, mismo colapso que el resto de P1 — no el cruce "
        "completo de 8 categorías.")
    kit.punteo_numerado(sl, [
        f"Los docentes de escalafón Docente participan en instancias formativas en el "
        f"{docente_g.mean()*100:.1f}% de los casos, vs {regular_g.mean()*100:.1f}% en "
        f"escalafón Regular (diferencia de {(docente_g.mean()-regular_g.mean())*100:.1f} puntos).",
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
