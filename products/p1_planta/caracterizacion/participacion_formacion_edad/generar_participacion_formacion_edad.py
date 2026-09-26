"""
P1 — Caracterización del Cuerpo Académico de Planta
Participación en Instancias Formativas según Edad — Docentes de Jornada.

Descriptivo: tasa de participación por tramo de edad (barras verticales, mismo
estilo que edad_sexo/). La prueba t compara la variable continua (edad_anios)
entre 2 grupos naturales — Participó vs No participó — mismo patrón que las
pruebas t de *_dificultad/ (ahí el grupo fijo era Baja/Media+Alta y la variable
comparada era edad; acá se invierten los roles: el grupo es participación y la
variable comparada sigue siendo edad).

FUENTE: analisis.universo_base (Postgres, en vivo) — universo Jornada
        + analisis.universo_formados_p3 (Postgres, en vivo) — ver D31
SALIDA: P1_participacion_formacion_edad.pptx (2 diapositivas)
        + participacion_formacion_edad_chart.png
        + participacion_formacion_edad_ttest_chart.png
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
OUT_PPTX = Path(OUTPUTS) / "pptx" / "P1_participacion_formacion_edad.pptx"
OUT_PPTX.parent.mkdir(parents=True, exist_ok=True)

DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"
TRAMO_ORD = ["<30", "30-34", "35-39", "40-44", "45-49", "50-54", "55-59", "60-64", "65-69", "70+"]
COL_BASE = "#4E8FC9"
N_MIN_CONFIABLE = 15

# ── Datos ───────────────────────────────────────────────────────────────────
engine = create_engine(DB_URL)
base = pd.read_sql(text("""
    SELECT rut_key, tramo_edad, edad_anios FROM analisis.universo_base
    WHERE tipo_contrato_tag='JORNADA'
"""), engine)
N_JORNADA = len(base)

participantes = set(pd.read_sql(text("""
    SELECT DISTINCT rut_key FROM analisis.universo_formados_p3 WHERE tipo_contrato_tag='JORNADA'
"""), engine)["rut_key"])

base["participo"] = base["rut_key"].isin(participantes).astype(int)

con_tramo = base[base["tramo_edad"].isin(TRAMO_ORD)].copy()
N_SIN_EDAD = N_JORNADA - len(con_tramo)

tab = (con_tramo.groupby("tramo_edad")["participo"].agg(tasa="mean", n="count")
       .reindex(TRAMO_ORD))
tab["tasa"] *= 100

print(f"Universo Jornada: {N_JORNADA}  |  con tramo_edad válido: {len(con_tramo)}  |  "
      f"excluidos: {N_SIN_EDAD}")
print(tab)

tramo_mayor = tab["tasa"].idxmax()
tramo_menor = tab["tasa"].idxmin()
tramos_muestra_chica = tab.index[tab["n"] < N_MIN_CONFIABLE].tolist()

# ── Prueba t: edad_anios continua, Participó vs No participó ──────────────────
con_edad = base.dropna(subset=["edad_anios"]).copy()
N_SIN_EDAD_ANIOS = N_JORNADA - len(con_edad)
participo_g = con_edad.loc[con_edad["participo"] == 1, "edad_anios"]
no_participo_g = con_edad.loc[con_edad["participo"] == 0, "edad_anios"]
T_STAT, P_VAL = stats.ttest_ind(participo_g, no_participo_g, equal_var=False)   # Welch
PRUEBAS = [prueba_dict("II · Participación", "Edad: participó vs no participó",
                       f"{participo_g.mean():.1f} vs {no_participo_g.mean():.1f} años",
                       len(participo_g) + len(no_participo_g), P_VAL)]

print(f"\nPrueba t (edad_anios, Participó vs No participó): "
      f"Participó N°={len(participo_g)} media={participo_g.mean():.1f}  "
      f"No participó N°={len(no_participo_g)} media={no_participo_g.mean():.1f}  "
      f"t={T_STAT:.3f}  p={P_VAL:.4f}")


def agregar(prs):
    """Construye el gráfico descriptivo (tasa por tramo de edad) y agrega la
    diapositiva a `prs`."""
    kit = UcenSlideKit(out_dir=HERE)
    kit.ensure_bg()

    fig = kit.new_chart_fig()
    ax = kit.chart_axes(fig, top=0.10, bottom=0.14)

    x = np.arange(len(TRAMO_ORD))
    n_vals = tab["n"].values
    alphas = np.clip(0.35 + 0.65 * np.sqrt(n_vals) / np.sqrt(np.nanmax(n_vals)), 0.35, 0.97)
    hatches = ["///" if n < N_MIN_CONFIABLE else None for n in n_vals]

    for xi, v, alpha, hatch in zip(x, tab["tasa"], alphas, hatches):
        ax.bar(xi, v, width=0.6, color=COL_BASE, alpha=alpha, edgecolor="none",
               hatch=hatch, zorder=3)

    stroke = [pe.withStroke(linewidth=1.8, foreground="#0A0F18")]
    for xi, v, n in zip(x, tab["tasa"], n_vals):
        marca = "⚠" if n < N_MIN_CONFIABLE else ""
        ax.text(xi, v + 2, f"{v:.0f}%{marca}", ha="center", va="bottom", fontsize=9,
                 fontweight="bold", color=COL_BASE, path_effects=stroke, zorder=6)
        ax.text(xi, 2, f"N°={int(n)}", ha="center", va="bottom", fontsize=6.8,
                 color="white", alpha=0.85, rotation=90)

    ax.set_xticks(x)
    ax.set_xticklabels(TRAMO_ORD, fontsize=9.5, color="white")
    ax.set_xlabel("Tramo de edad", color="#AAAAAA", fontsize=9)
    ax.set_ylabel("% con ≥1 instancia formativa", color="#AAAAAA", fontsize=9)
    ax.set_ylim(0, 100)
    ax.tick_params(axis="x", length=0, pad=6)
    ax.tick_params(axis="y", colors="#AAAAAA", labelsize=8.5)
    for sp in ax.spines.values():
        sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.7)
    ax.yaxis.grid(True, color="white", alpha=0.07, linewidth=0.5)
    ax.set_axisbelow(True)

    chart_path = kit.save_chart(fig, "participacion_formacion_edad_chart.png")

    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.pic_chart(sl, prs, chart_path)
    kit.title(sl, "Participación en instancias formativas según tramo de edad — Docentes Jornada")
    kit.subtitulo(sl,
        f"Universo: {N_JORNADA} docentes Jornada  ·  "
        f"N°={len(con_tramo)} con tramo de edad válido")
    kit.notas(sl,
        f"{N_SIN_EDAD} docentes sin tramo de edad válido, excluidos. Participación = al "
        f"menos 1 instancia formativa 2022-2025. Fuente: analisis.universo_formados_p3 (D31).")
    bullets = [
        f"El tramo {tramo_mayor} tiene la tasa de participación más alta "
        f"({tab.loc[tramo_mayor,'tasa']:.1f}%, N°={int(tab.loc[tramo_mayor,'n'])}), y "
        f"{tramo_menor} la más baja ({tab.loc[tramo_menor,'tasa']:.1f}%, "
        f"N°={int(tab.loc[tramo_menor,'n'])}).",
        # Revisión 2026-09-26 (obs. 6): la prueba no significativa se muestra, no se oculta.
        f"No hay un patrón lineal claro por edad. Edad promedio: participó {participo_g.mean():.1f} vs "
        f"no participó {no_participo_g.mean():.1f} años. " + lectura_p(P_VAL),
    ]
    if tramos_muestra_chica:
        nombres = ", ".join(tramos_muestra_chica)
        bullets.append(
            f"⚠ Tramo{'s' if len(tramos_muestra_chica) > 1 else ''} {nombres} con menos de "
            f"{N_MIN_CONFIABLE} casos — su tasa no es representativa, se marca con textura "
            f"en el gráfico."
        )
    kit.punteo_numerado(sl, bullets, fs=12)
    return sl


def agregar_ttest(prs):
    """Construye el gráfico de la prueba t (Participó vs No participó, edad
    continua) y agrega la diapositiva a `prs`."""
    kit = UcenSlideKit(out_dir=HERE)
    kit.ensure_bg()

    grupos = ["Participó", "No participó"]
    medias = [participo_g.mean(), no_participo_g.mean()]
    ns = [len(participo_g), len(no_participo_g)]
    cis = [stats.t.ppf(0.975, n - 1) * s.std(ddof=1) / np.sqrt(n)
           for s, n in [(participo_g, len(participo_g)), (no_participo_g, len(no_participo_g))]]
    colors = ["#1F5C99", "#7FADD9"]

    fig = kit.new_chart_fig()
    ax = kit.chart_axes(fig, top=0.14)

    x = np.arange(2)
    ax.bar(x, medias, width=0.42, color=colors, alpha=0.92, edgecolor="none",
           yerr=cis, capsize=6, error_kw={"ecolor": "#DDDDDD", "linewidth": 1.3})

    stroke = [pe.withStroke(linewidth=2, foreground="#0A0F18")]
    for xi, media, ci, n, color in zip(x, medias, cis, ns, colors):
        ax.text(xi, media + ci + 0.3, f"{media:.1f} años", ha="center", va="bottom",
                 fontsize=13, fontweight="bold", color=color, path_effects=stroke, zorder=6)
        ax.text(xi, 0.3, f"N°={n} docentes", ha="center", va="bottom",
                 fontsize=8.5, color="white")

    sig = "significativa" if P_VAL < 0.05 else "no significativa"
    ax.text(0.5, 0.99, f"Prueba t de Welch:  t = {T_STAT:.2f}   ·   p = {P_VAL:.4f}   ·   "
            f"diferencia {sig} al 5%", transform=ax.transAxes, ha="center", va="top",
            fontsize=9.5, color="#F2D675", fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(grupos, fontsize=12, color="white")
    ax.set_ylabel("Edad promedio (años)", color="#AAAAAA", fontsize=9)
    ax.set_ylim(0, max(medias) * 1.4)
    ax.tick_params(axis="x", length=0, pad=8)
    ax.tick_params(axis="y", colors="#AAAAAA", labelsize=8.5)
    for sp in ax.spines.values():
        sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.7)
    ax.yaxis.grid(True, color="white", alpha=0.07, linewidth=0.5)
    ax.set_axisbelow(True)

    chart_path = kit.save_chart(fig, "participacion_formacion_edad_ttest_chart.png")

    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.pic_chart(sl, prs, chart_path)
    kit.title(sl, "¿La edad influye en la participación formativa? — Prueba t, Jornada")
    kit.subtitulo(sl,
        f"Unidad de análisis: 1 valor por docente (edad_anios)  ·  "
        f"N°={len(participo_g)+len(no_participo_g)} docentes con edad registrada  ·  "
        f"Barras = intervalo de confianza 95%")
    kit.notas(sl,
        f"{N_SIN_EDAD_ANIOS} docentes sin edad_anios registrada, excluidos de esta prueba "
        f"(distinto del descriptivo por tramo, que excluye por tramo_edad inválido).")
    kit.punteo_numerado(sl, [
        f"Los docentes que participaron en instancias formativas tienen en promedio "
        f"{participo_g.mean():.1f} años, vs {no_participo_g.mean():.1f} años en quienes no "
        f"participaron (diferencia de {participo_g.mean()-no_participo_g.mean():.1f} años).",
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
