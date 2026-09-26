"""
P1 — Caracterización del Cuerpo Académico de Planta
Distribución por Unidad/Facultad — docentes de Jornada.

Pedido de la contraparte (2026-09-25), con una diapositiva de P3 como referencia visual
(barras horizontales con N° y %). A diferencia de esa referencia, `unidad_facultad` se
normaliza antes de contar: la fuente trae la misma facultad escrita de 2 formas
("FAC. DE MEDICINA Y CIENCIAS DE LA SALUD" / "Facultad de Medicina y Ciencias de la Salud"),
que en la referencia aparecían como barras duplicadas.

Categorías: 5 facultades académicas + VR de Investigación (80 docentes, peso propio) +
VR Académica + "Otras unidades" (Junta Directiva, Sede La Serena, Dir. Aseguramiento de
la Calidad, Gabinete de Rectoría — 13 docentes, ninguna con N° suficiente para ir sola).

FUENTE: data/cascade/01_jornada/docentes_jornada.csv (en vivo, sin copiar)
SALIDA: P1_facultad.pptx (1 diapositiva) + facultad_chart.png
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
OUT_PPTX = Path(OUTPUTS) / "pptx" / "P1_facultad.pptx"
OUT_PPTX.parent.mkdir(parents=True, exist_ok=True)

FACULTADES = ["Medicina y C. Salud", "Ingeniería y Arq.", "Educación",
              "Economía, Gob. y Com.", "Derecho y Humanidades"]
OTRAS = ["VR Investigación y Postgrado", "VR Académica", "Otras unidades"]
COL_FACULTAD = "#5C9BD6"
COL_UNIDAD = "#9085E9"   # unidades no académicas: mismo violeta ya validado en P1


def fac_norm(s):
    """Normaliza unidad_facultad a una categoría (None = sin dato)."""
    if not isinstance(s, str) or not s.strip():
        return None
    u = s.upper()
    if "MEDICINA" in u: return "Medicina y C. Salud"
    if "INGENIER" in u: return "Ingeniería y Arq."
    if "EDUCACI" in u: return "Educación"
    if "ECONOM" in u: return "Economía, Gob. y Com."
    if "DERECHO" in u: return "Derecho y Humanidades"
    if "INVEST" in u: return "VR Investigación y Postgrado"
    if "VICERRECTOR" in u and "ACAD" in u: return "VR Académica"
    return "Otras unidades"


# ── Datos ───────────────────────────────────────────────────────────────────
doc = pd.read_csv(Path(CASCADE) / "01_jornada" / "docentes_jornada.csv", encoding="utf-8-sig")
N_TOTAL = len(doc)
doc["fac"] = doc["unidad_facultad"].apply(fac_norm)
con_dato = doc.dropna(subset=["fac"])
N_CON_DATO = len(con_dato)
N_SIN_DATO = N_TOTAL - N_CON_DATO

conteo = con_dato["fac"].value_counts()
# Facultades ordenadas por N°, luego las unidades no académicas (siempre al final)
orden = [f for f in conteo.index if f in FACULTADES] + [o for o in OTRAS if o in conteo.index]
conteo = conteo.reindex(orden)
pct = 100 * conteo / N_CON_DATO

print(f"Universo Jornada: {N_TOTAL}  |  con unidad/facultad: {N_CON_DATO}  |  sin dato: {N_SIN_DATO}")
print(pd.DataFrame({"n": conteo, "pct": pct.round(1)}))
print("Detalle 'Otras unidades':")
print(doc.loc[doc["fac"] == "Otras unidades", "unidad_facultad"].value_counts())

top1, top2, top3 = conteo.index[:3]
pct_5fac = 100 * conteo.reindex(FACULTADES).sum() / N_CON_DATO


def agregar(prs):
    kit = UcenSlideKit(out_dir=HERE)
    kit.ensure_bg()

    fig = kit.new_chart_fig()
    ax = kit.chart_axes(fig, left=0.24, bottom=0.16, top=0.04)

    y = np.arange(len(conteo))
    colors = [COL_FACULTAD if f in FACULTADES else COL_UNIDAD for f in conteo.index]
    ax.barh(y, conteo.values, height=0.62, color=colors, alpha=0.92, edgecolor="none", zorder=3)

    stroke = [pe.withStroke(linewidth=2, foreground="#0A0F18")]
    for i, (n, p, c) in enumerate(zip(conteo.values, pct.values, colors)):
        ax.text(n + conteo.max() * 0.012, i, f"{int(n)}  ({p:.1f}%)", ha="left", va="center",
                fontsize=10, fontweight="bold", color="white", path_effects=stroke, zorder=6)

    ax.set_yticks(y)
    ax.set_yticklabels(conteo.index, fontsize=10.5, color="white")
    ax.invert_yaxis()
    ax.set_xlim(0, conteo.max() * 1.22)
    ax.set_xlabel("N° de docentes", color="#AAAAAA", fontsize=9)
    ax.tick_params(axis="y", length=0, pad=8)
    ax.tick_params(axis="x", colors="#AAAAAA", labelsize=8.5)
    for sp in ax.spines.values():
        sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.7)
    ax.xaxis.grid(True, color="white", alpha=0.07, linewidth=0.5)
    ax.set_axisbelow(True)

    chart_path = kit.save_chart(fig, "facultad_chart.png")

    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.pic_chart(sl, prs, chart_path)
    kit.title(sl, "Distribución por unidad/facultad — Docentes Jornada")
    kit.subtitulo(sl,
        f"Universo: {N_TOTAL} docentes Jornada  ·  {N_CON_DATO} con unidad/facultad registrada "
        f"({N_SIN_DATO} sin dato)")
    kit.punteo_numerado(sl, [
        f"{top1} concentra el mayor número de docentes ({conteo[top1]}, {pct[top1]:.0f}%), "
        f"seguida por {top2} ({conteo[top2]}, {pct[top2]:.0f}%) y {top3} "
        f"({conteo[top3]}, {pct[top3]:.0f}%).",
        f"Las 5 facultades académicas agrupan el {pct_5fac:.0f}% de los docentes Jornada con dato; "
        f"el resto se adscribe a vicerrectorías y otras unidades (en violeta).",
    ], fs=12)
    kit.notas(sl,
        "Nombres de unidad normalizados: la fuente escribe algunas facultades de 2 formas "
        "(ej. 'FAC. DE MEDICINA...' y 'Facultad de Medicina...'), se suman en una sola barra. "
        "'Otras unidades' = Junta Directiva, Sede La Serena, Dir. de Aseguramiento de la Calidad "
        f"y Gabinete de Rectoría. {N_SIN_DATO} docentes sin unidad registrada en la fuente. "
        "Fuente: docentes_jornada.csv (campo unidad_facultad).")
    return sl


if __name__ == "__main__":
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(UcenSlideKit.SW_EMU), Emu(UcenSlideKit.SH_EMU)
    agregar(prs)
    prs.save(OUT_PPTX)
    print(f"\n✓ Guardado: {OUT_PPTX}")
