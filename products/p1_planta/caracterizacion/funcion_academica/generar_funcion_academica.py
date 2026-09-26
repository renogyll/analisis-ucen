"""
P1 — Caracterización del Cuerpo Académico de Planta
Distribución de la Carga Académica (función académica según cargo) — docentes de Jornada.

Pedido de la contraparte (2026-09-25), con un gráfico de P2 como referencia visual (dona +
barras por función académica, detalle del cargo original en cursiva). Fuente nueva
entregada por la contraparte: "CONSOLIDADO DOCENTES 3-05-2026.xlsx - dotacion_con_clasificacion"
(547 docentes con cargo en dotación), que agrega la columna CLASIFICACION sobre el CARGO.

Clasificación usada tal como viene de la contraparte (CLASIFICACION), con un solo ajuste:
"DOCENTE" (1 caso en Jornada, cargo "Profesor") se suma a "DOCENCIA" — mismo cargo que otros
casos clasificados como DOCENCIA. Universo: docentes Jornada presentes en el archivo
(cruce por rut_key contra docentes_jornada.csv).

FUENTE: data/raw/dotacion_clasificacion/dotacion_con_clasificacion_2026-05-03.csv
        (gitignored — trae nombre y RUT) + data/cascade/01_jornada/docentes_jornada.csv
SALIDA: P1_funcion_academica.pptx (1 diapositiva) + funcion_academica_chart.png
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
OUT_PPTX = Path(OUTPUTS) / "pptx" / "P1_funcion_academica.pptx"
OUT_PPTX.parent.mkdir(parents=True, exist_ok=True)
FUENTE = ROOT / "data" / "raw" / "dotacion_clasificacion" / "dotacion_con_clasificacion_2026-05-03.csv"

CLASIF_MAP = {
    "DOCENCIA": "Docencia", "DOCENTE": "Docencia",
    "DOCENTE/GESTOR": "Docente/Gestor",
    "GESTIÓN ACADÉMICA": "Gestión Académica",
    "INVESTIGACIÓN/INNOVACIÓN": "Investigación e Innovación",
    "VCM": "Vinculación con el Medio",
}
COLORES = {
    "Docencia": "#5C9BD6",
    "Docente/Gestor": "#9085E9",
    "Investigación e Innovación": "#3E9E68",
    "Gestión Académica": "#4DB6AC",
    "Vinculación con el Medio": "#FFB74D",
}

# ── Datos ───────────────────────────────────────────────────────────────────
doc = pd.read_csv(Path(CASCADE) / "01_jornada" / "docentes_jornada.csv", encoding="utf-8-sig")
N_JORNADA = len(doc)
clas = pd.read_csv(FUENTE, encoding="utf-8-sig")
N_ARCHIVO = len(clas)
clas = clas[clas["rut_key"].astype(str).isin(doc["rut_key"].astype(str))].copy()
clas["funcion"] = clas["CLASIFICACION"].str.strip().map(CLASIF_MAP)
assert clas["funcion"].notna().all(), f"Clasificación sin mapear: {clas.loc[clas['funcion'].isna(), 'CLASIFICACION'].unique()}"
N = len(clas)

conteo = clas["funcion"].value_counts()
pct = 100 * conteo / N
# Detalle de cargo por función (los 2 cargos más frecuentes), para la cursiva bajo cada barra
detalle = {f: ", ".join(f"{c} {n}" for c, n in g["CARGO"].str.strip().value_counts().head(2).items())
           for f, g in clas.groupby("funcion")}

print(f"Archivo: {N_ARCHIVO} docentes  |  en universo Jornada: {N} de {N_JORNADA}")
print(pd.DataFrame({"n": conteo, "pct": pct.round(1)}))
for f in conteo.index:
    print(f"  {f}: {detalle[f]}")

top = conteo.index[0]
no_docencia = 100 - pct.get("Docencia", 0)
pct_gestion = pct.get("Docente/Gestor", 0) + pct.get("Gestión Académica", 0)


def agregar(prs):
    kit = UcenSlideKit(out_dir=HERE)
    kit.ensure_bg()

    fig = kit.new_chart_fig()
    stroke = [pe.withStroke(linewidth=2, foreground="#0A0F18")]

    # Dona (izq.)
    ax1 = fig.add_axes([0.02, 0.04, 0.34, 0.92])
    colors = [COLORES[f] for f in conteo.index]
    wedges, _ = ax1.pie(conteo.values, colors=colors, startangle=90, counterclock=False,
                        wedgeprops=dict(width=0.38, edgecolor="#0A0F18", linewidth=1.2))
    ax1.text(0, 0, f"{N}\ndocentes", ha="center", va="center", fontsize=12,
             fontweight="bold", color="white")
    for w, n, p in zip(wedges, conteo.values, pct.values):
        ang = np.deg2rad((w.theta1 + w.theta2) / 2)
        ax1.text(0.81 * np.cos(ang), 0.81 * np.sin(ang), f"{p:.0f}%", ha="center", va="center",
                 fontsize=9, fontweight="bold", color="white", path_effects=stroke)
    ax1.set_aspect("equal")

    # Barras (der.) con detalle de cargo en cursiva
    ax2 = fig.add_axes([0.58, 0.08, 0.34, 0.86], facecolor="none")
    y = np.arange(len(conteo))
    ax2.barh(y, conteo.values, height=0.5, color=colors, alpha=0.92, edgecolor="none", zorder=3)
    for i, (f, n, p) in enumerate(zip(conteo.index, conteo.values, pct.values)):
        ax2.text(n + conteo.max() * 0.015, i, f"{int(n)} ({p:.1f}%)", ha="left", va="center",
                 fontsize=9.5, fontweight="bold", color="white", path_effects=stroke, zorder=6)
        ax2.text(0, i + 0.40, detalle[f], ha="left", va="center", fontsize=6.8,
                 style="italic", color="#C8DCF0", zorder=6)
    ax2.set_yticks(y)
    ax2.set_yticklabels(conteo.index, fontsize=9.5, color="white", fontweight="bold")
    ax2.invert_yaxis()
    ax2.set_xlim(0, conteo.max() * 1.30)
    ax2.set_xlabel("N° de docentes", color="#AAAAAA", fontsize=8.5)
    ax2.tick_params(axis="y", length=0, pad=6)
    ax2.tick_params(axis="x", colors="#AAAAAA", labelsize=8)
    for sp in ax2.spines.values():
        sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.7)
    ax2.xaxis.grid(True, color="white", alpha=0.07, linewidth=0.5)
    ax2.set_axisbelow(True)

    chart_path = kit.save_chart(fig, "funcion_academica_chart.png")

    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.pic_chart(sl, prs, chart_path)
    kit.title(sl, "Distribución de la carga académica — Docentes Jornada")
    kit.subtitulo(sl,
        f"Universo: {N_JORNADA} docentes Jornada  ·  {N} con cargo asignado en dotación, clasificados "
        f"por función académica ({N_JORNADA - N} sin cargo registrado)")
    kit.punteo_numerado(sl, [
        f"{top} es la función predominante: {conteo[top]} docentes ({pct[top]:.0f}%), casi todos con "
        f"cargo de Profesor en sus distintas jornadas.",
        f"El {no_docencia:.0f}% restante tiene un cargo con otra función principal: la gestión "
        f"(Docente/Gestor + Gestión Académica) suma el {pct_gestion:.0f}% y la investigación el "
        f"{pct.get('Investigación e Innovación', 0):.0f}%.",
    ], fs=12)
    kit.notas(sl,
        "Fuente: archivo de la contraparte 'CONSOLIDADO DOCENTES 3-05-2026 — dotacion_con_clasificacion' "
        f"({N_ARCHIVO} docentes), cruzado por RUT con el universo Jornada. Clasificación tal como viene "
        "en la columna CLASIFICACION; 'DOCENTE' (1 caso, cargo Profesor) se sumó a Docencia. Cada "
        "docente tiene un solo cargo principal en dotación. Bajo cada barra, los 2 cargos más "
        "frecuentes de esa función.")
    return sl


if __name__ == "__main__":
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(UcenSlideKit.SW_EMU), Emu(UcenSlideKit.SH_EMU)
    agregar(prs)
    prs.save(OUT_PPTX)
    print(f"\n✓ Guardado: {OUT_PPTX}")
