"""
P1 — Caracterización del Cuerpo Académico de Planta
Distribución por Sexo y Tramo de Edad — docentes de Jornada.

FUENTE: data/cascade/01_jornada/docentes_jornada.csv (en vivo, sin copiar)
SALIDA: edad_sexo.pptx (1 diapositiva) + edad_sexo_chart.png
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
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from pptx import Presentation
from pptx.util import Emu

HERE = Path(__file__).parent
OUT_PPTX = Path(OUTPUTS) / "pptx" / "P1_edad_sexo.pptx"
OUT_PPTX.parent.mkdir(parents=True, exist_ok=True)

COL_HOMBRE = "#5C9BD6"   # mismo azul usado en P3 para "grupo 1"
COL_MUJER  = "#FFB74D"   # mismo naranjo usado en P3 para "grupo 2"

TRAMOS_ORD = ["<30", "30-34", "35-39", "40-44", "45-49",
              "50-54", "55-59", "60-64", "65-69", "70+"]

# ── Datos ───────────────────────────────────────────────────────────────────
doc = pd.read_csv(Path(CASCADE) / "01_jornada" / "docentes_jornada.csv", encoding="utf-8-sig")
N_TOTAL = len(doc)

con_datos = doc.dropna(subset=["sexo", "tramo_edad"]).copy()
con_datos["sexo"] = con_datos["sexo"].str.strip().str.upper()
N_CON_DATOS = len(con_datos)
N_SIN_DATOS = N_TOTAL - N_CON_DATOS

n_hombre = int((con_datos["sexo"] == "HOMBRE").sum())
n_mujer  = int((con_datos["sexo"] == "MUJER").sum())

tab = (con_datos.groupby(["tramo_edad", "sexo"]).size()
       .unstack(fill_value=0)
       .reindex(index=TRAMOS_ORD, fill_value=0)
       .reindex(columns=["HOMBRE", "MUJER"], fill_value=0))

print(f"Universo Jornada: {N_TOTAL}  |  con sexo+edad: {N_CON_DATOS}  |  sin dato: {N_SIN_DATOS}")
print(f"Hombre: {n_hombre}  |  Mujer: {n_mujer}")
print(tab)

# Hallazgos para el punteo
tramo_top = tab.sum(axis=1).idxmax()
n_top = int(tab.sum(axis=1).max())
tramo_mayor_brecha = (tab["MUJER"] - tab["HOMBRE"]).abs().idxmax()
brecha_val = int((tab["MUJER"] - tab["HOMBRE"]).abs().max())
sexo_mayor_en_brecha = "Mujeres" if tab.loc[tramo_mayor_brecha, "MUJER"] > tab.loc[tramo_mayor_brecha, "HOMBRE"] else "Hombres"

# ── Gráfico ───────────────────────────────────────────────────────────────────
kit = UcenSlideKit(out_dir=HERE)
kit.ensure_bg()

fig = kit.new_fig()
ax = fig.add_axes(kit.chart_rect(pad=0.02), facecolor="none", zorder=5)

x = np.arange(len(TRAMOS_ORD))
w = 0.38
bars_h = ax.bar(x - w/2, tab["HOMBRE"], width=w, color=COL_HOMBRE, alpha=0.90,
                 edgecolor="none", label=f"Hombre  (n={n_hombre})")
bars_m = ax.bar(x + w/2, tab["MUJER"], width=w, color=COL_MUJER, alpha=0.90,
                 edgecolor="none", label=f"Mujer  (n={n_mujer})")

stroke = [pe.withStroke(linewidth=2, foreground="#0A0F18")]
for bars, color in [(bars_h, COL_HOMBRE), (bars_m, COL_MUJER)]:
    for b in bars:
        h = b.get_height()
        if h > 0:
            ax.text(b.get_x() + b.get_width()/2, h + 0.6, str(int(h)),
                    ha="center", va="bottom", fontsize=9, fontweight="bold",
                    color=color, path_effects=stroke, zorder=6)

ax.set_xticks(x)
ax.set_xticklabels(TRAMOS_ORD, fontsize=10, color="white")
ax.set_xlabel("Tramo de edad", color="#AAAAAA", fontsize=9)
ax.set_ylabel("Nº de docentes", color="#AAAAAA", fontsize=9)
ax.tick_params(axis="x", length=0, pad=8)
ax.tick_params(axis="y", colors="#AAAAAA", labelsize=8.5)
for sp in ax.spines.values():
    sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.7)
ax.yaxis.grid(True, color="white", alpha=0.07, linewidth=0.5)
ax.set_axisbelow(True)
ax.legend(fontsize=10, framealpha=0.22, labelcolor="white",
          facecolor="#101820", edgecolor="#444", loc="upper right")

chart_path = kit.save_chart(fig, "edad_sexo_chart.png")

# ── Diapositiva ────────────────────────────────────────────────────────────────
prs = Presentation()
prs.slide_width, prs.slide_height = Emu(kit.SW_EMU), Emu(kit.SH_EMU)

sl = kit.new_slide(prs)
kit.pic(sl, prs, kit.SHARED_BG)
kit.pic(sl, prs, chart_path)
kit.title(sl, "Distribución por Sexo y Tramo de Edad — Docentes de Planta (Jornada)")
kit.subtitulo(sl,
    f"Universo: {N_TOTAL} docentes Jornada  ·  {N_CON_DATOS} con sexo y edad disponibles "
    f"({N_SIN_DATOS} sin dato, principalmente sin dotación)  ·  Fuente: docentes_jornada.csv")
kit.punteo_numerado(sl, [
    f"El tramo {tramo_top} concentra la mayor cantidad de docentes ({n_top} de {N_CON_DATOS}, "
    f"{100*n_top/N_CON_DATOS:.0f}%).",
    f"La mayor brecha entre sexos se da en el tramo {tramo_mayor_brecha}, con "
    f"{brecha_val} docentes más {sexo_mayor_en_brecha.lower()} que del otro sexo en ese tramo.",
])

prs.save(OUT_PPTX)
print(f"\n✓ Guardado: {OUT_PPTX}")
