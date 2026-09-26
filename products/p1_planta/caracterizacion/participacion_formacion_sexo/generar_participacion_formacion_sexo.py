"""
P1 — Caracterización del Cuerpo Académico de Planta
Participación en Instancias Formativas según Sexo del Docente — Jornada.

Participación = tasa de docentes con al menos 1 instancia formativa (Taller,
Diplomado o Proyecto) registrada, no el conteo de instancias (un docente que
participó 10 veces no debe pesar más que uno que participó 1 vez — mismo
criterio de "1 valor por docente" que el resto de P1).

FUENTE: analisis.universo_base (Postgres, en vivo) — universo Jornada
        + analisis.universo_formados_p3 (Postgres, en vivo) — instancias
        formativas ya unidas al perfil de universo_base (D31, ver
        docs/DECISIONES_METODOLOGICAS.md). A pesar del nombre, NO está
        filtrada a "aptos P3": trae toda la participación (apto_p3 es solo
        un flag por fila, no un filtro aplicado a la tabla).
SALIDA: P1_participacion_formacion_sexo.pptx (2 diapositivas)
        + participacion_formacion_sexo_chart.png
        + participacion_formacion_sexo_ttest_chart.png
"""
import sys; sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "shared"))
from config import OUTPUTS
from pptx_helpers import UcenSlideKit, lectura_p, prueba_dict

import numpy as np
import pandas as pd
import matplotlib.patheffects as pe
from scipy import stats
from sqlalchemy import create_engine, text
from pptx import Presentation
from pptx.util import Emu

HERE = Path(__file__).parent
OUT_PPTX = Path(OUTPUTS) / "pptx" / "P1_participacion_formacion_sexo.pptx"
OUT_PPTX.parent.mkdir(parents=True, exist_ok=True)

DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"
SEXO_ORD = ["HOMBRE", "MUJER"]
COL_HOMBRE = "#5C9BD6"
COL_MUJER = "#FFB74D"

# ── Datos ───────────────────────────────────────────────────────────────────
engine = create_engine(DB_URL)
base = pd.read_sql(text("""
    SELECT rut_key, sexo FROM analisis.universo_base WHERE tipo_contrato_tag='JORNADA'
"""), engine)
N_JORNADA = len(base)

participantes = set(pd.read_sql(text("""
    SELECT DISTINCT rut_key FROM analisis.universo_formados_p3 WHERE tipo_contrato_tag='JORNADA'
"""), engine)["rut_key"])

base["participo"] = base["rut_key"].isin(participantes).astype(int)

N_SIN_SEXO = int(base["sexo"].isna().sum())
con_sexo = base.dropna(subset=["sexo"]).copy()

tab = (con_sexo.groupby("sexo")["participo"].agg(tasa="mean", n="count")
       .reindex(SEXO_ORD))
tab["tasa"] *= 100

print(f"Universo Jornada: {N_JORNADA}  |  con sexo registrado: {len(con_sexo)}  |  "
      f"sin sexo: {N_SIN_SEXO}")
print(tab)

hombre = con_sexo.loc[con_sexo["sexo"] == "HOMBRE", "participo"]
mujer = con_sexo.loc[con_sexo["sexo"] == "MUJER", "participo"]
T_STAT, P_VAL = stats.ttest_ind(mujer, hombre, equal_var=False)   # Welch
PRUEBAS = [prueba_dict("II · Participación", "Participación: Mujer vs Hombre",
                       f"{100 * mujer.mean():.1f}% vs {100 * hombre.mean():.1f}%", len(mujer) + len(hombre), P_VAL)]

brecha = tab.loc["MUJER", "tasa"] - tab.loc["HOMBRE", "tasa"]
sexo_mayor = "Mujeres" if brecha > 0 else "Hombres"

print(f"\nPrueba t (por docente, Mujer vs Hombre, participó=1/no=0): "
      f"Mujer N°={len(mujer)} tasa={100*mujer.mean():.1f}%  "
      f"Hombre N°={len(hombre)} tasa={100*hombre.mean():.1f}%  t={T_STAT:.3f}  p={P_VAL:.4f}")


def agregar(prs):
    """Construye el gráfico descriptivo y agrega la diapositiva a `prs`."""
    kit = UcenSlideKit(out_dir=HERE)
    kit.ensure_bg()

    fig = kit.new_chart_fig()
    ax = kit.chart_axes(fig, top=0.10)

    x = np.arange(len(SEXO_ORD))
    colors = [COL_HOMBRE, COL_MUJER]
    ax.bar(x, tab["tasa"], width=0.45, color=colors, alpha=0.92, edgecolor="none")

    stroke = [pe.withStroke(linewidth=2, foreground="#0A0F18")]
    for xi, v, n, color in zip(x, tab["tasa"], tab["n"], colors):
        ax.text(xi, v + 1.5, f"{v:.1f}%", ha="center", va="bottom",
                 fontsize=14, fontweight="bold", color=color, path_effects=stroke, zorder=6)
        ax.text(xi, 2, f"N°={int(n)} docentes", ha="center", va="bottom",
                 fontsize=8.5, color="white")

    ax.set_xticks(x)
    ax.set_xticklabels(["Hombre", "Mujer"], fontsize=12, color="white")
    ax.set_ylabel("% con ≥1 instancia formativa", color="#AAAAAA", fontsize=9)
    ax.set_ylim(0, 100)
    ax.tick_params(axis="x", length=0, pad=8)
    ax.tick_params(axis="y", colors="#AAAAAA", labelsize=8.5)
    for sp in ax.spines.values():
        sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.7)
    ax.yaxis.grid(True, color="white", alpha=0.07, linewidth=0.5)
    ax.set_axisbelow(True)

    chart_path = kit.save_chart(fig, "participacion_formacion_sexo_chart.png")

    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.pic_chart(sl, prs, chart_path)
    kit.title(sl, "Participación en Instancias Formativas según Sexo — Jornada")
    kit.subtitulo(sl,
        f"Universo: {N_JORNADA} docentes Jornada  ·  "
        f"N°={len(con_sexo)} con sexo registrado")
    kit.notas(sl,
        f"{N_SIN_SEXO} docentes sin sexo registrado, excluidos. Participación = al "
        f"menos 1 instancia formativa (Taller/Diplomado/Proyecto) 2022-2025, tasa por "
        f"docente (no conteo de instancias). Fuente: analisis.universo_formados_p3 "
        f"(D31) — a pesar del nombre, no está filtrada a apto_p3.")
    kit.punteo_numerado(sl, [
        f"{sexo_mayor} participan en instancias formativas con más frecuencia: "
        f"Mujeres {tab.loc['MUJER','tasa']:.1f}% vs Hombres {tab.loc['HOMBRE','tasa']:.1f}% "
        f"(diferencia de {abs(brecha):.1f} puntos).",
        "Ver prueba de significancia en la siguiente diapositiva.",
    ])
    return sl


def agregar_ttest(prs):
    """Construye el gráfico de la prueba t (Hombre vs Mujer) y agrega la diapositiva a `prs`."""
    kit = UcenSlideKit(out_dir=HERE)
    kit.ensure_bg()

    grupos = ["Hombre", "Mujer"]
    medias = [100 * hombre.mean(), 100 * mujer.mean()]
    ns = [len(hombre), len(mujer)]
    cis = [100 * stats.t.ppf(0.975, n - 1) * s.std(ddof=1) / np.sqrt(n)
           for s, n in [(hombre, len(hombre)), (mujer, len(mujer))]]
    colors = [COL_HOMBRE, COL_MUJER]

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

    sig = "significativa" if P_VAL < 0.05 else "no significativa"
    ax.text(0.5, 0.99, f"Prueba t de Welch:  t = {T_STAT:.2f}   ·   p = {P_VAL:.4f}   ·   "
            f"diferencia {sig} al 5%", transform=ax.transAxes, ha="center", va="top",
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

    chart_path = kit.save_chart(fig, "participacion_formacion_sexo_ttest_chart.png")

    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.pic_chart(sl, prs, chart_path)
    # Revisión 2026-09-26 (obs. 5 y 21): única diapositiva del tema en el consolidado
    # (descriptivo + prueba), título sin lenguaje causal.
    kit.title(sl, "¿Difiere la participación en instancias formativas según sexo? — Docentes Jornada")
    kit.subtitulo(sl,
        f"1 valor por docente (participó=1/no participó=0)  ·  N°={len(hombre)+len(mujer)} docentes "
        f"con sexo registrado  ·  barras = intervalo de confianza 95%")
    kit.punteo_numerado(sl, [
        f"Las docentes mujeres participan en instancias formativas en el "
        f"{mujer.mean()*100:.1f}% de los casos, vs {hombre.mean()*100:.1f}% en hombres "
        f"(diferencia de {(mujer.mean()-hombre.mean())*100:.1f} puntos).",
        lectura_p(P_VAL),
    ], fs=12)
    kit.notas(sl,
        f"{N_SIN_SEXO} docentes sin sexo registrado, excluidos. Participación = al menos 1 instancia "
        f"formativa (Taller/Diplomado/Proyecto) 2022-2025 (D31).")
    return sl


if __name__ == "__main__":
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(UcenSlideKit.SW_EMU), Emu(UcenSlideKit.SH_EMU)
    agregar(prs)
    agregar_ttest(prs)
    prs.save(OUT_PPTX)
    print(f"\n✓ Guardado: {OUT_PPTX}")
