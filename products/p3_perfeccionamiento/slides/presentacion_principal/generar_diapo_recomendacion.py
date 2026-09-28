"""
Standalone: DIAPO_recomendacion.pptx — 1 slide
% de Recomendación SAT — Formados P3 vs No Formados, por año.
"""
import sys; sys.stdout.reconfigure(encoding="utf-8")
import os, pathlib
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import pandas as pd
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

BASE      = os.path.dirname(os.path.abspath(__file__))
REPO      = str(pathlib.Path(BASE).parents[3])
CASCADE   = os.path.join(REPO, "data", "cascade")
OUT_DIR   = os.path.join(BASE, "dark_slides_v3")
SHARED_BG = os.path.join(OUT_DIR, "_background.png")
OUT_PPTX  = os.path.join(REPO, "outputs", "pptx", "DIAPO_recomendacion_v3.pptx")
CHART_PNG = os.path.join(OUT_DIR, "recomendacion_chart.png")

SW_EMU = 12192000
SH_EMU = 6858000

# ── Layout (idéntico al resto de la presentación) ────────────────────────────
SW, SH = 13.333, 7.5
PIC_L, PIC_T, PIC_W, PIC_H = 786581, 1125000, 10599174, 3720000
BUL_L, BUL_T, BUL_W, BUL_H = 786581, 4870000, 10599174, 1870000
TITLE_L, TITLE_T, TITLE_W, TITLE_H = PIC_L, 185000, PIC_W, 710000
POP_L,   POP_T,   POP_W,   POP_H   = PIC_L, 845000, 9000000, 255000

def _ex(e): return e / SW_EMU
def _ey(e): return e / SH_EMU
def _fig_rect(l, t, w, h): return (l, 1 - t - h, w, h)

PIC_RECT = _fig_rect(_ex(PIC_L), _ey(PIC_T), _ex(PIC_W), _ey(PIC_H))
CHART_X  = PIC_RECT[0] + 0.06
CHART_Y  = PIC_RECT[1] + 0.04
CHART_W  = PIC_RECT[2] - 0.08
CHART_H  = PIC_RECT[3] - 0.08

PAL_TRAT = "#5C9BD6"   # azul — Formados P3
PAL_CTRL = "#FFB74D"   # naranja — No formados

# ── Datos ─────────────────────────────────────────────────────────────────────
sat  = pd.read_csv(os.path.join(CASCADE, "05_aptos_p3", "p3_sat_zscore.csv"),
                   encoding="utf-8-sig")
ctrl = pd.read_csv(os.path.join(CASCADE, "complementarios", "control_918.csv"),
                   encoding="utf-8-sig")
bin_ = pd.read_csv(os.path.join(CASCADE, "complementarios", "bin_recomendacion_completo.csv"),
                   encoding="utf-8-sig")

trat_ruts = set(sat["rut_key"])
ctrl_ruts = set(ctrl["rut_key"])

bin_trat = bin_[bin_["rut_key"].isin(trat_ruts)].copy()
bin_ctrl = bin_[bin_["rut_key"].isin(ctrl_ruts)].copy()

bin_trat["anio"] = bin_trat["periodo"].str[:4].astype(int)
bin_ctrl["anio"] = bin_ctrl["periodo"].str[:4].astype(int)

t_year = bin_trat.groupby("anio").agg(pct=("bin", "mean"), n=("rut_key", "nunique")).reset_index()
c_year = bin_ctrl.groupby("anio").agg(pct=("bin", "mean"), n=("rut_key", "nunique")).reset_index()

anios = sorted(set(t_year["anio"]) | set(c_year["anio"]))

t_pct = [t_year.loc[t_year["anio"]==a, "pct"].values[0] if a in t_year["anio"].values else np.nan for a in anios]
c_pct = [c_year.loc[c_year["anio"]==a, "pct"].values[0] if a in c_year["anio"].values else np.nan for a in anios]
t_n   = [int(t_year.loc[t_year["anio"]==a, "n"].values[0]) if a in t_year["anio"].values else 0 for a in anios]
c_n   = [int(c_year.loc[c_year["anio"]==a, "n"].values[0]) if a in c_year["anio"].values else 0 for a in anios]

n_trat_total = int(bin_trat["rut_key"].nunique())
n_ctrl_total = int(bin_ctrl["rut_key"].nunique())

print("Años:", anios)
for a, tp, cp in zip(anios, t_pct, c_pct):
    print(f"  {a}  Formados={tp:.2f}%  Control={cp:.2f}%")

# ── Gráfico ───────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(SW, SH), facecolor="none")
fig.patch.set_facecolor("none")

ax = fig.add_axes([CHART_X, CHART_Y, CHART_W, CHART_H], facecolor="none", zorder=5)

xs = np.arange(len(anios))

# Barras agrupadas
BW = 0.32
bars_t = ax.bar(xs - BW/2, t_pct, width=BW, color=PAL_TRAT,
                alpha=0.90, edgecolor="none",
                label=f"Formados P3  (nº {n_trat_total})")
bars_c = ax.bar(xs + BW/2, c_pct, width=BW, color=PAL_CTRL,
                alpha=0.90, edgecolor="none",
                label=f"No Formados — Control  (nº {n_ctrl_total})")

# Etiquetas sobre barras
stroke = [pe.withStroke(linewidth=2.5, foreground="#0A0F18")]
for i, (v, n) in enumerate(zip(t_pct, t_n)):
    ax.text(xs[i] - BW/2, v + 0.18, f"{v:.1f}%",
            ha="center", va="bottom", fontsize=11, fontweight="bold",
            color=PAL_TRAT, path_effects=stroke)

for i, (v, n) in enumerate(zip(c_pct, c_n)):
    ax.text(xs[i] + BW/2, v + 0.18, f"{v:.1f}%",
            ha="center", va="bottom", fontsize=11, fontweight="bold",
            color=PAL_CTRL, path_effects=stroke)

# Líneas de tendencia
ax.plot(xs - BW/2, t_pct, color=PAL_TRAT, linewidth=1.8,
        linestyle="--", alpha=0.55, zorder=3)
ax.plot(xs + BW/2, c_pct, color=PAL_CTRL, linewidth=1.8,
        linestyle="--", alpha=0.55, zorder=3)

# Ejes
y_min = min(min(t_pct), min(c_pct)) - 2
y_max = max(max(t_pct), max(c_pct)) + 3
ax.set_ylim(y_min, y_max)
ax.set_xticks(xs)
ax.set_xticklabels([str(a) for a in anios], fontsize=13, fontweight="bold",
                   color="white")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
ax.tick_params(axis="y", colors="#AAAAAA", labelsize=10)
ax.tick_params(axis="x", length=0, pad=10)

for sp in ax.spines.values():
    sp.set_edgecolor("white"); sp.set_alpha(0.30); sp.set_linewidth(0.8)
ax.xaxis.grid(False)
ax.yaxis.grid(True, color="white", alpha=0.07, linewidth=0.6)
ax.set_axisbelow(True)

# Leyenda — esquina superior izquierda, fuera del área de barras
leg = ax.legend(loc="upper left", bbox_to_anchor=(0.01, 0.99),
                fontsize=10.5, framealpha=0, labelcolor="white",
                handlelength=1.4, handletextpad=0.6, borderpad=0)
for t in leg.get_texts():
    t.set_fontweight("bold")

fig.savefig(CHART_PNG, dpi=150, facecolor="none", transparent=True)
plt.close()
print(f"Chart guardado: {CHART_PNG}")

# ── Armar slide ───────────────────────────────────────────────────────────────
prs = Presentation()
prs.slide_width  = Emu(SW_EMU)
prs.slide_height = Emu(SH_EMU)
sl = prs.slides.add_slide(prs.slide_layouts[6])

sl.shapes.add_picture(SHARED_BG,  Emu(0), Emu(0), Emu(SW_EMU), Emu(SH_EMU))
sl.shapes.add_picture(CHART_PNG,  Emu(0), Emu(0), Emu(SW_EMU), Emu(SH_EMU))

W   = RGBColor(0xFF, 0xFF, 0xFF)
CEL = RGBColor(0x7E, 0xBF, 0xF0)
GRI = RGBColor(0xCC, 0xDD, 0xEE)

def _txt(text, left, top, width, height, fs=12, bold=False, italic=False,
         color="#FFFFFF", align=PP_ALIGN.LEFT):
    txb = sl.shapes.add_textbox(Emu(left), Emu(top), Emu(width), Emu(height))
    tf  = txb.text_frame; tf.word_wrap = True
    for i, line in enumerate(str(text).split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        run = p.add_run(); run.text = line
        run.font.size = Pt(fs); run.font.bold = bold; run.font.italic = italic
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        run.font.color.rgb = RGBColor(r, g, b)

# Título
_txt("% de Recomendación Estudiantil — Formados P3 vs No Formados",
     TITLE_L, TITLE_T, TITLE_W, TITLE_H,
     fs=20, bold=True, color="#FFFFFF", align=PP_ALIGN.CENTER)

# POP subtitle
_txt(
    f"Pregunta 4526: «¿Recomendaría a este profesor/a a otro/a estudiante que quiera lograr un real aprendizaje?»  ·  "
    f"Tratamiento nº {n_trat_total}  ·  Control nº {n_ctrl_total}  ·  Períodos 2023–2025",
    POP_L, POP_T, POP_W, POP_H,
    fs=7.5, italic=True, color="#C8DCF0")

# Bullets
delta_2023 = t_pct[anios.index(2023)] - c_pct[anios.index(2023)]
delta_2025 = t_pct[anios.index(2025)] - c_pct[anios.index(2025)]
trend_t = t_pct[-1] - t_pct[0]
trend_c = c_pct[-1] - c_pct[0]

bul_items = [
    (f"Los docentes Formados P3 muestran un porcentaje de recomendación "
     f"consistentemente superior al grupo control en todos los años analizados "
     f"(diferencia {delta_2023:+.1f} pp en 2023 y {delta_2025:+.1f} pp en 2025)."),
    (f"Tendencia Formados P3: {t_pct[0]:.1f}% → {t_pct[-1]:.1f}% ({trend_t:+.1f} pp de 2023 a 2025). "
     f"Tendencia Control: {c_pct[0]:.1f}% → {c_pct[-1]:.1f}% ({trend_c:+.1f} pp)."),
]

txb = sl.shapes.add_textbox(Emu(BUL_L), Emu(BUL_T), Emu(BUL_W), Emu(BUL_H))
tf  = txb.text_frame; tf.word_wrap = True
for i, item in enumerate(bul_items):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    p.space_after = Pt(5); p.alignment = PP_ALIGN.LEFT
    run = p.add_run()
    run.text = f"•  {item}"
    run.font.size = Pt(11.5)
    run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

prs.save(OUT_PPTX)
print(f"\n✓ Guardado: {OUT_PPTX}")
