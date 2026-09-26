"""
P1 — Caracterización del Cuerpo Académico de Planta
Calificación EDD (Evaluación de Desempeño Docente) según Jerarquía — Jornada.

Descriptivo con las 8 categorías de jerarquía (D25), barra horizontal ordenada por magnitud,
textura para N° chicos. La prueba t usa escalafón binario (Docente vs Regular) — mismo colapso
que el resto de P1 — y su resultado va en el punteo de la misma diapositiva (revisión
2026-09-26, obs. 21: descriptivo + prueba en una sola diapositiva).

Revisión 2026-09-26 (D36): usa la EDD ajustada por año (edd_comun.py), porque la escala de
edd_total cambió entre 2023 y 2024.

FUENTE: intel.evaluacion_jefes (Postgres, en vivo) — vía edd_comun.cargar_edd
SALIDA: P1_edd_jerarquia.pptx (1 diapositiva) + edd_jerarquia_chart.png
"""
import sys; sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "shared"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import CASCADE, OUTPUTS
from pptx_helpers import UcenSlideKit, lectura_p, prueba_dict
from edd_comun import cargar_edd, NOTA_AJUSTE, ANIO_REF

import numpy as np
import pandas as pd
import matplotlib.patheffects as pe
from scipy import stats
from sqlalchemy import create_engine
from pptx import Presentation
from pptx.util import Emu

HERE = Path(__file__).parent
OUT_PPTX = Path(OUTPUTS) / "pptx" / "P1_edd_jerarquia.pptx"
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

# ── Datos ───────────────────────────────────────────────────────────────────
doc = pd.read_csv(Path(CASCADE) / "01_jornada" / "docentes_jornada.csv", encoding="utf-8-sig")
N_JORNADA = len(doc)

engine = create_engine(DB_URL)
edd = cargar_edd(engine)
N_EDD_DOC = edd["rut_key"].nunique()
por_docente = (edd[edd["jerarquia"].isin(CAT_ORD)]
               .groupby(["rut_key", "jerarquia"])["edd_aj"].mean().reset_index())
N_SIN_DATO = N_EDD_DOC - len(por_docente)

tab = (por_docente.groupby("jerarquia")["edd_aj"].agg(edd_prom="mean", n="count")
       .reindex(CAT_ORD).dropna(subset=["edd_prom"]).sort_values("edd_prom", ascending=False))
CAT_DISPLAY = tab.index.tolist()
cats_ok = tab[tab["n"] >= N_MIN_CONFIABLE]
cat_mayor, cat_menor = cats_ok["edd_prom"].idxmax(), cats_ok["edd_prom"].idxmin()
cats_muestra_chica = tab.index[tab["n"] < N_MIN_CONFIABLE].tolist()

por_docente["es_regular"] = por_docente["jerarquia"].str.contains("REGULAR")
docente_g = por_docente.loc[~por_docente["es_regular"], "edd_aj"]
regular_g = por_docente.loc[por_docente["es_regular"], "edd_aj"]
T_STAT, P_VAL = stats.ttest_ind(regular_g, docente_g, equal_var=False)   # Welch

PRUEBAS = [prueba_dict("III · EDD", "EDD ajustada por año: escalafón Regular vs Docente",
                       f"{regular_g.mean():.2f} vs {docente_g.mean():.2f}", len(por_docente), P_VAL)]

print(f"Universo Jornada: {N_JORNADA}  |  con EDD y jerarquía válida: {len(por_docente)}")
print(tab.round(3))
print(f"Escalafón: Regular {regular_g.mean():.3f} (N°={len(regular_g)})  Docente {docente_g.mean():.3f} "
      f"(N°={len(docente_g)})  t={T_STAT:.3f}  p={P_VAL:.4f}")


def agregar(prs):
    kit = UcenSlideKit(out_dir=HERE)
    kit.ensure_bg()
    fig = kit.new_chart_fig()
    ax = kit.chart_axes(fig, left=0.22)

    y = np.arange(len(CAT_DISPLAY))
    colors = [CAT_COLORS[c] for c in CAT_DISPLAY]
    n_vals = tab["n"].values
    alphas = np.clip(0.35 + 0.65 * np.sqrt(n_vals) / np.sqrt(n_vals.max()), 0.35, 0.97)
    for i, (v, n, color, alpha) in enumerate(zip(tab["edd_prom"], n_vals, colors, alphas)):
        ax.barh(i, v, height=0.62, color=color, alpha=alpha, edgecolor="none",
                hatch="///" if n < N_MIN_CONFIABLE else None, zorder=3)
    stroke = [pe.withStroke(linewidth=2, foreground="#0A0F18")]
    for i, (v, n) in enumerate(zip(tab["edd_prom"], n_vals)):
        marca = " ⚠" if n < N_MIN_CONFIABLE else ""
        ax.text(v + 0.012, i, f"{v:.2f}   (N°={int(n)}{marca})", ha="left", va="center",
                fontsize=9.5, fontweight="bold", color="white", path_effects=stroke, zorder=6)
    ax.set_yticks(y); ax.set_yticklabels([CAT_LABEL[c] for c in CAT_DISPLAY], fontsize=10, color="white")
    ax.invert_yaxis()
    ax.set_xlabel(f"EDD ajustada por año (escala {ANIO_REF})", color="#AAAAAA", fontsize=9)
    ax.set_xlim(0, tab["edd_prom"].max() * 1.35)
    ax.tick_params(axis="y", length=0, pad=8); ax.tick_params(axis="x", colors="#AAAAAA", labelsize=8.5)
    for sp in ax.spines.values():
        sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.7)
    ax.xaxis.grid(True, color="white", alpha=0.07, linewidth=0.5); ax.set_axisbelow(True)
    chart_path = kit.save_chart(fig, "edd_jerarquia_chart.png")

    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.pic_chart(sl, prs, chart_path)
    kit.title(sl, "Calificación EDD según jerarquía — Docentes Jornada")
    kit.subtitulo(sl, f"EDD ajustada por año, 1 valor por docente  ·  N°={len(por_docente)} docentes con "
                      f"EDD y jerarquía válida")
    bullets = [
        f"{CAT_LABEL[cat_mayor]} tiene la calificación más alta ({tab.loc[cat_mayor, 'edd_prom']:.2f}) y "
        f"{CAT_LABEL[cat_menor]} la más baja ({tab.loc[cat_menor, 'edd_prom']:.2f}), entre las "
        f"categorías con N° suficiente.",
        f"Por escalafón: Docente {docente_g.mean():.2f} vs Regular {regular_g.mean():.2f}. " + lectura_p(P_VAL),
    ]
    if cats_muestra_chica:
        nombres = ", ".join(CAT_LABEL[c] for c in cats_muestra_chica)
        bullets.append(f"⚠ {nombres}: menos de {N_MIN_CONFIABLE} casos, promedio no representativo (con textura).")
    kit.punteo_numerado(sl, bullets, fs=12)
    kit.notas(sl, f"{N_SIN_DATO} docentes con EDD sin jerarquía válida, excluidos. Jerarquía = 8 "
                  f"categorías; escalafón = Docente/Regular. " + NOTA_AJUSTE)
    return sl


if __name__ == "__main__":
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(UcenSlideKit.SW_EMU), Emu(UcenSlideKit.SH_EMU)
    agregar(prs)
    prs.save(OUT_PPTX)
    print(f"\n✓ Guardado: {OUT_PPTX}")
