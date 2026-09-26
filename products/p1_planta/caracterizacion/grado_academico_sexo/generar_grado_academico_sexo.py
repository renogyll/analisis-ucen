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
# Punteos enriquecidos (2026-09-25, anotación de la contraparte: "más conclusivos, dando insight")
pct_postgrado = 100 * tab.loc[["Magíster o Master", "Doctor"]].values.sum() / N_CON_DATOS
pct_doc_h = 100 * tab.loc["Doctor", "HOMBRE"] / n_hombre
pct_doc_m = 100 * tab.loc["Doctor", "MUJER"] / n_mujer
pct_prof_h = 100 * tab.loc["Profesional/Técnico", "HOMBRE"] / n_hombre
pct_prof_m = 100 * tab.loc["Profesional/Técnico", "MUJER"] / n_mujer
pct_mujer_prof = 100 * tab.loc["Profesional/Técnico", "MUJER"] / tab.loc["Profesional/Técnico"].sum()
# Doctorado dentro del escalafón Regular (contexto para la implicancia de la brecha)
reg = con_datos[con_datos["jerarquia"].str.contains("REGULAR", na=False)]
pct_doc_regular = 100 * (reg["nivel"] == "Doctor").mean()
print(f"Postgrado: {pct_postgrado:.1f}%  |  Doctor H {pct_doc_h:.1f}% / M {pct_doc_m:.1f}%  |  "
      f"Prof/Téc H {pct_prof_h:.1f}% / M {pct_prof_m:.1f}%  |  Doctor en escalafón Regular: "
      f"{pct_doc_regular:.1f}% (N°={len(reg)})")

def agregar(prs):
    """Construye el gráfico y agrega la diapositiva de este sub-tema a `prs`
    (usado tanto en modo standalone como por el ensamblador products/p1_planta/generar_presentacion.py)."""
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

    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.pic_chart(sl, prs, chart_path)
    kit.title(sl, "Grado académico según sexo — Docentes Jornada")
    kit.subtitulo(sl,
        f"Universo: {N_TOTAL} docentes Jornada  ·  {N_CON_DATOS} con grado académico y sexo disponibles "
        f"({N_SIN_DATOS} sin dato)")
    kit.punteo_numerado(sl, [
        f"Cuerpo académico altamente posgraduado: {pct_postgrado:.0f}% tiene Magíster o Doctorado; "
        f"{nivel_top} es el grado predominante ({100*n_top/N_CON_DATOS:.0f}%).",
        f"Brecha de género en el Doctorado: {pct_doc_h:.0f}% de los hombres es Doctor vs "
        f"{pct_doc_m:.0f}% de las mujeres — ellas son el {pct_mujer_total:.0f}% del cuerpo, "
        f"pero solo el {pct_mujer_doctor:.0f}% de los Doctores.",
        f"En el otro extremo, {pct_mujer_prof:.0f}% de quienes no tienen posgrado son mujeres "
        f"({pct_prof_m:.0f}% de ellas vs {pct_prof_h:.0f}% de los hombres).",
        f"Implicancia: el Doctorado predomina en el escalafón Regular ({pct_doc_regular:.0f}% "
        f"lo tiene), por lo que esta brecha podría limitar la progresión académica de las mujeres.",
    ], fs=11)
    kit.notas(sl,
        "La implicancia del punto 4 es una hipótesis: asocia dos distribuciones "
        "(grado × sexo y grado × escalafón), no mide trayectorias individuales de ascenso.")
    return sl


if __name__ == "__main__":
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(UcenSlideKit.SW_EMU), Emu(UcenSlideKit.SH_EMU)
    agregar(prs)
    prs.save(OUT_PPTX)
    print(f"\n✓ Guardado: {OUT_PPTX}")
