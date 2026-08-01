"""
P1 — Caracterización del Cuerpo Académico de Planta
Edad promedio por Nivel de Jerarquía — docentes de Jornada.

FUENTE: data/cascade/01_jornada/docentes_jornada.csv (en vivo, sin copiar)
SALIDA: P1_edad_jerarquia.pptx (1 diapositiva) + edad_jerarquia_chart.png
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
from pptx import Presentation
from pptx.util import Emu

HERE = Path(__file__).parent
OUT_PPTX = Path(OUTPUTS) / "pptx" / "P1_edad_jerarquia.pptx"
OUT_PPTX.parent.mkdir(parents=True, exist_ok=True)

# Las 8 categorías reales de jerarquia (normalizadas en shared/etl/00_base/etl_universo_base.py,
# ver docs/DECISIONES_METODOLOGICAS.md D25). Orden: junior→senior, Docente antes que Regular en cada nivel.
CAT_ORD = ["INSTRUCTOR DOCENTE", "INSTRUCTOR REGULAR",
           "ASISTENTE DOCENTE",  "ASISTENTE REGULAR",
           "ASOCIADO DOCENTE",   "ASOCIADO REGULAR",
           "TITULAR DOCENTE",    "TITULAR REGULAR"]
CAT_LABEL = {c: c.title() for c in CAT_ORD}   # "INSTRUCTOR DOCENTE" → "Instructor Docente"
# Ramp secuencial azul claro→oscuro por nivel; Docente y Regular del mismo nivel comparten color
NIVEL_COLORS = ["#AFCBE8", "#7FADD9", "#4E8FC9", "#1F5C99"]
CAT_COLORS = {cat: NIVEL_COLORS[i // 2] for i, cat in enumerate(CAT_ORD)}
N_MIN_CONFIABLE = 15   # bajo este umbral el promedio no es representativo (ver punteo)

# ── Datos ───────────────────────────────────────────────────────────────────
doc = pd.read_csv(Path(CASCADE) / "01_jornada" / "docentes_jornada.csv", encoding="utf-8-sig")
N_TOTAL = len(doc)

con_datos = doc.dropna(subset=["jerarquia", "edad_anios"]).copy()
con_datos = con_datos[con_datos["jerarquia"].isin(CAT_ORD)]
N_CON_DATOS = len(con_datos)
N_SIN_DATOS = N_TOTAL - N_CON_DATOS

tab = (con_datos.groupby("jerarquia")["edad_anios"].agg(edad_prom="mean", n="count")
       .reindex(CAT_ORD))

print(f"Universo Jornada: {N_TOTAL}  |  con jerarquía+edad: {N_CON_DATOS}  |  sin dato: {N_SIN_DATOS}")
print(tab)

# Orden de despliegue: por edad promedio descendente (la historia del gráfico, no el escalafón)
tab = tab.sort_values("edad_prom", ascending=False)
CAT_DISPLAY = tab.index.tolist()

# Hallazgos para el punteo
cat_mas_grande = tab["n"].idxmax()
n_mas_grande = int(tab["n"].max())
cat_mayor_edad = tab["edad_prom"].idxmax()
edad_mayor = tab["edad_prom"].max()
cats_muestra_chica = tab.index[tab["n"] < N_MIN_CONFIABLE].tolist()

def agregar(prs):
    """Construye el gráfico y agrega la diapositiva de este sub-tema a `prs`
    (usado tanto en modo standalone como por el ensamblador products/p1_planta/generar_presentacion.py)."""
    kit = UcenSlideKit(out_dir=HERE)
    kit.ensure_bg()

    fig = kit.new_chart_fig()
    ax = kit.chart_axes(fig, left=0.22)   # más margen izq. para las etiquetas de 2 palabras

    y = np.arange(len(CAT_DISPLAY))
    colors = [CAT_COLORS[c] for c in CAT_DISPLAY]
    # El N pesa visualmente: muestras chicas se ven más tenues y con textura, para no leerse
    # con la misma fuerza que una categoría con 10x más casos.
    n_vals = tab["n"].values
    alphas = np.clip(0.35 + 0.65 * np.sqrt(n_vals) / np.sqrt(n_vals.max()), 0.35, 0.97)
    hatches = ["///" if n < N_MIN_CONFIABLE else None for n in n_vals]

    for i, (edad, n, color, alpha, hatch) in enumerate(
            zip(tab["edad_prom"], n_vals, colors, alphas, hatches)):
        ax.barh(i, edad, height=0.62, color=color, alpha=alpha, edgecolor="none",
                hatch=hatch, zorder=3)

    stroke = [pe.withStroke(linewidth=2, foreground="#0A0F18")]
    for i, (edad, n) in enumerate(zip(tab["edad_prom"], n_vals)):
        marca = " ⚠" if n < N_MIN_CONFIABLE else ""
        ax.text(edad + 0.8, i, f"{edad:.1f} años   (N°={int(n)}{marca})",
                ha="left", va="center", fontsize=9.5, fontweight="bold",
                color=colors[i], path_effects=stroke, zorder=6)

    ax.set_yticks(y)
    ax.set_yticklabels([CAT_LABEL[c] for c in CAT_DISPLAY], fontsize=10, color="white")
    ax.invert_yaxis()   # mayor edad promedio arriba, menor abajo
    ax.set_xlabel("Edad promedio (años)", color="#AAAAAA", fontsize=9)
    ax.set_xlim(0, tab["edad_prom"].max() * 1.30)
    ax.tick_params(axis="y", length=0, pad=8)
    ax.tick_params(axis="x", colors="#AAAAAA", labelsize=8.5)
    for sp in ax.spines.values():
        sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.7)
    ax.xaxis.grid(True, color="white", alpha=0.07, linewidth=0.5)
    ax.set_axisbelow(True)

    chart_path = kit.save_chart(fig, "edad_jerarquia_chart.png")

    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.pic_chart(sl, prs, chart_path)
    kit.title(sl, "Edad Promedio por Jerarquía — Docentes de Planta (Jornada)")
    kit.subtitulo(sl,
        f"Universo: {N_TOTAL} docentes Jornada  ·  {N_CON_DATOS} con jerarquía y edad disponibles "
        f"({N_SIN_DATOS} sin dato)")
    bullets = [
        f"{CAT_LABEL[cat_mas_grande]} concentra la mayor cantidad de docentes "
        f"(N°={n_mas_grande} de {N_CON_DATOS}, {100*n_mas_grande/N_CON_DATOS:.0f}%).",
        f"{CAT_LABEL[cat_mayor_edad]} tiene la edad promedio más alta de las 8 categorías "
        f"({edad_mayor:.1f} años, N°={int(tab.loc[cat_mayor_edad, 'n'])}).",
    ]
    if cats_muestra_chica:
        nombres = ", ".join(CAT_LABEL[c] for c in cats_muestra_chica)
        bullets.append(
            f"⚠ {nombres} tiene{'n' if len(cats_muestra_chica) > 1 else ''} menos de "
            f"{N_MIN_CONFIABLE} casos — su promedio no es representativo, se marca con textura en el gráfico."
        )
    kit.punteo_numerado(sl, bullets)
    return sl


if __name__ == "__main__":
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(UcenSlideKit.SW_EMU), Emu(UcenSlideKit.SH_EMU)
    agregar(prs)
    prs.save(OUT_PPTX)
    print(f"\n✓ Guardado: {OUT_PPTX}")
