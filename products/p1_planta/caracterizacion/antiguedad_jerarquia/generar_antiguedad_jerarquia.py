"""
P1 — Caracterización del Cuerpo Académico de Planta
Años de trayectoria (antigüedad) promedio por Nivel de Jerarquía — docentes de Jornada.

Pedido de la contraparte (2026-09-25): cruzar las jerarquías de edad_jerarquia/ con los
años de trayectoria en la universidad. Mismo diseño que edad_jerarquia/ (barra horizontal
ordenada por magnitud, textura para N chicos) para que se lean como par.

Trayectoria = `antiguedad_anios` de docentes_jornada.csv (años desde fecha_ingreso a la
fecha de corte). Es antigüedad en UCEN, no trayectoria académica total.

FUENTE: data/cascade/01_jornada/docentes_jornada.csv (en vivo, sin copiar)
SALIDA: P1_antiguedad_jerarquia.pptx (1 diapositiva) + antiguedad_jerarquia_chart.png
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
OUT_PPTX = Path(OUTPUTS) / "pptx" / "P1_antiguedad_jerarquia.pptx"
OUT_PPTX.parent.mkdir(parents=True, exist_ok=True)

# Mismas 8 categorías, orden y colores que edad_jerarquia/ (D25)
CAT_ORD = ["INSTRUCTOR DOCENTE", "INSTRUCTOR REGULAR",
           "ASISTENTE DOCENTE",  "ASISTENTE REGULAR",
           "ASOCIADO DOCENTE",   "ASOCIADO REGULAR",
           "TITULAR DOCENTE",    "TITULAR REGULAR"]
CAT_LABEL = {c: c.title() for c in CAT_ORD}
NIVEL_COLORS = ["#AFCBE8", "#7FADD9", "#4E8FC9", "#1F5C99"]
CAT_COLORS = {cat: NIVEL_COLORS[i // 2] for i, cat in enumerate(CAT_ORD)}
CAT_COLORS["TITULAR REGULAR"] = "#5C8CB3"
N_MIN_CONFIABLE = 15

# ── Datos ───────────────────────────────────────────────────────────────────
doc = pd.read_csv(Path(CASCADE) / "01_jornada" / "docentes_jornada.csv", encoding="utf-8-sig")
N_TOTAL = len(doc)

con_datos = doc.dropna(subset=["jerarquia", "antiguedad_anios"]).copy()
con_datos = con_datos[con_datos["jerarquia"].isin(CAT_ORD)]
N_CON_DATOS = len(con_datos)
N_SIN_DATOS = N_TOTAL - N_CON_DATOS

tab = (con_datos.groupby("jerarquia")["antiguedad_anios"].agg(tray_prom="mean", n="count")
       .reindex(CAT_ORD))

print(f"Universo Jornada: {N_TOTAL}  |  con jerarquía+antigüedad: {N_CON_DATOS}  |  sin dato: {N_SIN_DATOS}")
print(tab.round(1))

tab = tab.sort_values("tray_prom", ascending=False)
CAT_DISPLAY = tab.index.tolist()

# Hallazgos para el punteo
cat_mayor = tab["tray_prom"].idxmax()
cat_menor = tab.drop(index=[c for c in tab.index if tab.loc[c, "n"] < N_MIN_CONFIABLE])["tray_prom"].idxmin()
cats_muestra_chica = tab.index[tab["n"] < N_MIN_CONFIABLE].tolist()
# Docente vs Regular dentro del mismo nivel: ¿quién llega con menos años en la universidad?
pares = [(nivel, tab.loc[f"{nivel} DOCENTE", "tray_prom"], tab.loc[f"{nivel} REGULAR", "tray_prom"])
         for nivel in ["ASISTENTE", "ASOCIADO", "TITULAR"]]
n_regular_menor = sum(r < d for _, d, r in pares)
tit_d, tit_r = tab.loc["TITULAR DOCENTE", "tray_prom"], tab.loc["TITULAR REGULAR", "tray_prom"]


def agregar(prs):
    """Construye el gráfico y agrega la diapositiva a `prs` (standalone o ensamblador)."""
    kit = UcenSlideKit(out_dir=HERE)
    kit.ensure_bg()

    fig = kit.new_chart_fig()
    ax = kit.chart_axes(fig, left=0.22)

    y = np.arange(len(CAT_DISPLAY))
    colors = [CAT_COLORS[c] for c in CAT_DISPLAY]
    n_vals = tab["n"].values
    alphas = np.clip(0.35 + 0.65 * np.sqrt(n_vals) / np.sqrt(n_vals.max()), 0.35, 0.97)
    hatches = ["///" if n < N_MIN_CONFIABLE else None for n in n_vals]

    for i, (v, color, alpha, hatch) in enumerate(zip(tab["tray_prom"], colors, alphas, hatches)):
        ax.barh(i, v, height=0.62, color=color, alpha=alpha, edgecolor="none",
                hatch=hatch, zorder=3)

    stroke = [pe.withStroke(linewidth=2, foreground="#0A0F18")]
    for i, (v, n) in enumerate(zip(tab["tray_prom"], n_vals)):
        marca = " ⚠" if n < N_MIN_CONFIABLE else ""
        ax.text(v + 0.25, i, f"{v:.1f} años   (N°={int(n)}{marca})",
                ha="left", va="center", fontsize=9.5, fontweight="bold",
                color="white", path_effects=stroke, zorder=6)

    ax.set_yticks(y)
    ax.set_yticklabels([CAT_LABEL[c] for c in CAT_DISPLAY], fontsize=10, color="white")
    ax.invert_yaxis()
    ax.set_xlabel("Años de trayectoria en la universidad (promedio)", color="#AAAAAA", fontsize=9)
    ax.set_xlim(0, tab["tray_prom"].max() * 1.40)
    ax.tick_params(axis="y", length=0, pad=8)
    ax.tick_params(axis="x", colors="#AAAAAA", labelsize=8.5)
    for sp in ax.spines.values():
        sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.7)
    ax.xaxis.grid(True, color="white", alpha=0.07, linewidth=0.5)
    ax.set_axisbelow(True)

    chart_path = kit.save_chart(fig, "antiguedad_jerarquia_chart.png")

    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.pic_chart(sl, prs, chart_path)
    kit.title(sl, "Años de trayectoria promedio según jerarquía — Docentes Jornada")
    # Decisiones del usuario 2026-09-26: trayectoria = años en UCEN, explícito en la bajada;
    # se quita el punteo interpretativo sobre Regulares que ingresan ya jerarquizados.
    kit.subtitulo(sl,
        f"Años en UCEN desde la fecha de ingreso (no incluye carrera previa)  ·  {N_CON_DATOS} de "
        f"{N_TOTAL} docentes Jornada con jerarquía y antigüedad ({N_SIN_DATOS} sin dato)")
    bullets = [
        f"La trayectoria crece con la jerarquía: {CAT_LABEL[cat_mayor]} promedia "
        f"{tab.loc[cat_mayor, 'tray_prom']:.1f} años en la universidad, frente a "
        f"{tab.loc[cat_menor, 'tray_prom']:.1f} en {CAT_LABEL[cat_menor]}.",
        f"En los 3 niveles comparables, el escalafón Regular tiene menos años en la universidad que el "
        f"Docente del mismo nivel (Titular: {tit_r:.1f} vs {tit_d:.1f} años)." if n_regular_menor == 3 else
        f"En {n_regular_menor} de 3 niveles, el escalafón Regular tiene menos años en la universidad que el "
        f"Docente del mismo nivel.",
    ]
    if cats_muestra_chica:
        nombres = ", ".join(CAT_LABEL[c] for c in cats_muestra_chica)
        bullets.append(
            f"⚠ {nombres} tiene{'n' if len(cats_muestra_chica) > 1 else ''} menos de "
            f"{N_MIN_CONFIABLE} casos — su promedio no es representativo, se marca con textura.")
    kit.punteo_numerado(sl, bullets, fs=12)
    kit.notas(sl,
        "Años de trayectoria = antiguedad_anios (desde fecha de ingreso a UCEN hasta la fecha de "
        "corte). Mide permanencia en la universidad, no trayectoria académica total. "
        f"{N_SIN_DATOS} docentes sin fecha de ingreso o sin jerarquía válida quedan fuera. "
        "Fuente: docentes_jornada.csv.")
    return sl


if __name__ == "__main__":
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(UcenSlideKit.SW_EMU), Emu(UcenSlideKit.SH_EMU)
    agregar(prs)
    prs.save(OUT_PPTX)
    print(f"\n✓ Guardado: {OUT_PPTX}")
