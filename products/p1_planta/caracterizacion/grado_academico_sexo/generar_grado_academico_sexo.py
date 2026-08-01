"""
P1 — Caracterización del Cuerpo Académico de Planta
Grado Académico por Sexo — docentes de Jornada.

FUENTE: data/cascade/01_jornada/docentes_jornada.csv (en vivo, sin copiar)
SALIDA: P1_grado_academico_sexo.pptx (1 diapositiva) + grado_academico_sexo_chart.png
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
OUT_PPTX = Path(OUTPUTS) / "pptx" / "P1_grado_academico_sexo.pptx"
OUT_PPTX.parent.mkdir(parents=True, exist_ok=True)

COL_HOMBRE = "#5C9BD6"   # mismo par usado en edad_sexo / P3
COL_MUJER  = "#FFB74D"

# TÉCNICO (N°=2) se funde con PROFESIONAL — muestra insuficiente para categoría propia
# (decisión 2026-08-01, mismo criterio que jerarquía: N chico no se oculta, se agrupa).
# "NO INFORMA" se trata como sin dato (ver docs/DECISIONES_METODOLOGICAS.md D21).
NIVEL_MAP = {
    "PROFESIONAL": "Profesional/Técnico", "TÉCNICO": "Profesional/Técnico",
    "MAGÍSTER O MASTER": "Magíster o Master",
    "DOCTOR": "Doctor",
}
NIVEL_ORD = ["Profesional/Técnico", "Magíster o Master", "Doctor"]   # orden ascendente de grado

# ── Datos ───────────────────────────────────────────────────────────────────
doc = pd.read_csv(Path(CASCADE) / "01_jornada" / "docentes_jornada.csv", encoding="utf-8-sig")
N_TOTAL = len(doc)

con_datos = doc.dropna(subset=["nivel_formacion", "sexo"]).copy()
con_datos["sexo"] = con_datos["sexo"].str.strip().str.upper()
con_datos["nivel"] = con_datos["nivel_formacion"].map(NIVEL_MAP)
con_datos = con_datos.dropna(subset=["nivel"])   # descarta "NO INFORMA"
N_CON_DATOS = len(con_datos)
N_SIN_DATOS = N_TOTAL - N_CON_DATOS

n_hombre = int((con_datos["sexo"] == "HOMBRE").sum())
n_mujer  = int((con_datos["sexo"] == "MUJER").sum())

tab = (con_datos.groupby(["nivel", "sexo"]).size()
       .unstack(fill_value=0)
       .reindex(index=NIVEL_ORD, fill_value=0)
       .reindex(columns=["HOMBRE", "MUJER"], fill_value=0))

print(f"Universo Jornada: {N_TOTAL}  |  con nivel_formación+sexo: {N_CON_DATOS}  |  sin dato: {N_SIN_DATOS}")
print(f"Hombre: {n_hombre}  |  Mujer: {n_mujer}")
print(tab)

# Hallazgos para el punteo
nivel_top = tab.sum(axis=1).idxmax()
n_top = int(tab.sum(axis=1).max())
pct_mujer_doctor = 100 * tab.loc["Doctor", "MUJER"] / tab.loc["Doctor"].sum()
pct_mujer_total = 100 * n_mujer / N_CON_DATOS

# ── Gráfico ───────────────────────────────────────────────────────────────────
kit = UcenSlideKit(out_dir=HERE)
kit.ensure_bg()

fig = kit.new_chart_fig()
ax = kit.chart_axes(fig)

x = np.arange(len(NIVEL_ORD))
w = 0.34
bars_h = ax.bar(x - w/2, tab["HOMBRE"], width=w, color=COL_HOMBRE, alpha=0.90,
                 edgecolor="none", label=f"Hombre  (N°={n_hombre})")
bars_m = ax.bar(x + w/2, tab["MUJER"], width=w, color=COL_MUJER, alpha=0.90,
                 edgecolor="none", label=f"Mujer  (N°={n_mujer})")

stroke = [pe.withStroke(linewidth=2, foreground="#0A0F18")]
for bars, color in [(bars_h, COL_HOMBRE), (bars_m, COL_MUJER)]:
    for b in bars:
        h = b.get_height()
        if h > 0:
            ax.text(b.get_x() + b.get_width()/2, h + 1.5, str(int(h)),
                    ha="center", va="bottom", fontsize=10, fontweight="bold",
                    color=color, path_effects=stroke, zorder=6)

ax.set_xticks(x)
ax.set_xticklabels(NIVEL_ORD, fontsize=11, color="white")
ax.set_ylabel("Nº de docentes", color="#AAAAAA", fontsize=9)
ax.tick_params(axis="x", length=0, pad=8)
ax.tick_params(axis="y", colors="#AAAAAA", labelsize=8.5)
for sp in ax.spines.values():
    sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.7)
ax.yaxis.grid(True, color="white", alpha=0.07, linewidth=0.5)
ax.set_axisbelow(True)
ax.legend(fontsize=10, framealpha=0.22, labelcolor="white",
          facecolor="#101820", edgecolor="#444", loc="upper right")

chart_path = kit.save_chart(fig, "grado_academico_sexo_chart.png")

# ── Diapositiva ────────────────────────────────────────────────────────────────
prs = Presentation()
prs.slide_width, prs.slide_height = Emu(kit.SW_EMU), Emu(kit.SH_EMU)

sl = kit.new_slide(prs)
kit.pic(sl, prs, kit.SHARED_BG)
kit.pic_chart(sl, prs, chart_path)
kit.title(sl, "Grado Académico por Sexo — Docentes de Planta (Jornada)")
kit.subtitulo(sl,
    f"Universo: {N_TOTAL} docentes Jornada  ·  {N_CON_DATOS} con grado académico y sexo disponibles "
    f"({N_SIN_DATOS} sin dato)")
kit.punteo_numerado(sl, [
    f"{nivel_top} es el grado más común (N°={n_top} de {N_CON_DATOS}, "
    f"{100*n_top/N_CON_DATOS:.0f}%).",
    f"Las mujeres son el {pct_mujer_total:.0f}% del universo con dato, pero solo el "
    f"{pct_mujer_doctor:.0f}% de quienes tienen Doctorado — la representación femenina "
    f"cae en el grado más alto.",
])

prs.save(OUT_PPTX)
print(f"\n✓ Guardado: {OUT_PPTX}")
