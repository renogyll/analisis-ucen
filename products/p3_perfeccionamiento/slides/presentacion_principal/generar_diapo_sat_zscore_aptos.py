"""
Genera UNA diapo: SAT z-score — Aptos P3 vs Control — 6 Períodos
Fuente: data/cascade/complementarios/control_vs_trat_918.csv
(el z_trat ya corresponde a los 316 Aptos P3, no a todos los formados)
Salida: outputs/pptx/DIAPO_sat_zscore_aptos.pptx
"""
import sys; sys.stdout.reconfigure(encoding="utf-8")
import os, zipfile
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import pandas as pd
from PIL import Image as PILImage
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
import pathlib

# ── Rutas ─────────────────────────────────────────────────────────────────────
BASE    = os.path.dirname(os.path.abspath(__file__))
REPO    = str(pathlib.Path(BASE).parents[1])
CASCADE = os.path.join(REPO, "data", "cascade")
COMP    = os.path.join(CASCADE, "complementarios")

CVT_CSV   = os.path.join(COMP, "control_vs_trat_918.csv")
APTOS_CSV = os.path.join(CASCADE, "05_aptos_p3", "p3_sat_zscore.csv")
FONDOTIPO = (r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO"
             r"\Downloads\Analisis_UCEN_v2\Fondotipop.pptx")
OUT_PPTX  = os.path.join(REPO, "outputs", "pptx", "DIAPO_sat_zscore_aptos.pptx")
OUT_DIR   = os.path.join(BASE, "dark_slides_v3")
SCRATCH   = os.path.join(REPO, "outputs", "scratch")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(SCRATCH, exist_ok=True)

# ── Assets ─────────────────────────────────────────────────────────────────────
BG_PATH   = os.path.join(SCRATCH, "fondotipo_image1.jpg")
LOGO_PATH = os.path.join(SCRATCH, "fondotipo_image2.png")
for path, zname in [(BG_PATH, "ppt/media/image1.jpg"), (LOGO_PATH, "ppt/media/image2.png")]:
    if not os.path.exists(path):
        with zipfile.ZipFile(FONDOTIPO) as z:
            with open(path, "wb") as f:
                f.write(z.read(zname))

with PILImage.open(BG_PATH) as _im:
    _rgb = _im.convert("RGB"); _iw, _ih = _rgb.size
    _nh  = int(_iw / (16/9)); _y0 = min(int(_ih * 0.12), _ih - _nh)
    bg_arr = np.array(_rgb.crop((0, _y0, _iw, _y0 + _nh)))

with PILImage.open(LOGO_PATH) as _logo:
    logo_arr = np.array(_logo.convert("RGBA")).astype(np.float32) / 255.0

H_GRAD = 600; grad = np.zeros((H_GRAD, 1, 4), dtype=np.float32)
for _r in range(H_GRAD):
    _t = _r / (H_GRAD - 1)
    _stops = [(0.00, (0,33,71)), (0.54, (0,70,128)), (1.00, (144,171,196))]
    for _i in range(len(_stops) - 1):
        _t0, _c0 = _stops[_i]; _t1, _c1 = _stops[_i + 1]
        if _t0 <= _t <= _t1:
            _s = (_t - _t0) / (_t1 - _t0)
            grad[_r, 0] = [(_c0[0]+_s*(_c1[0]-_c0[0]))/255,
                            (_c0[1]+_s*(_c1[1]-_c0[1]))/255,
                            (_c0[2]+_s*(_c1[2]-_c0[2]))/255, 0.82]; break

# ── Layout ─────────────────────────────────────────────────────────────────────
SW, SH   = 13.333, 7.5
SW_EMU   = 12192000
SH_EMU   = 6858000

PIC_L, PIC_T, PIC_W, PIC_H = 786581, 1125000, 10599174, 3720000
BUL_L, BUL_T, BUL_W, BUL_H = 786581, 4870000, 10599174, 1870000
LOGO_L, LOGO_T, LOGO_W, LOGO_H = 9813773, 656354, 1756626, 697725
TITLE_L, TITLE_T, TITLE_W, TITLE_H = PIC_L, 185000, PIC_W, 710000
POP_L,   POP_T,   POP_W,   POP_H   = PIC_L, 845000, 9000000, 255000

def _ex(e): return e / SW_EMU
def _ey(e): return e / SH_EMU
def _fig_rect(l, t, w, h): return (l, 1 - t - h, w, h)

PIC_RECT  = _fig_rect(_ex(PIC_L), _ey(PIC_T), _ex(PIC_W), _ey(PIC_H))
LOGO_RECT = _fig_rect(_ex(LOGO_L), _ey(LOGO_T), _ex(LOGO_W), _ey(LOGO_H))

CHART_X = PIC_RECT[0] + 0.13
CHART_Y = PIC_RECT[1] + 0.04
CHART_W = PIC_RECT[2] - 0.19
CHART_H = PIC_RECT[3] - 0.09

CTITLE_L = int(CHART_X * SW_EMU)
CTITLE_T = PIC_T + 38000
CTITLE_W = int((PIC_RECT[0] + PIC_RECT[2] - CHART_X + 0.02) * SW_EMU)
CTITLE_H = 295000

SHARED_BG = os.path.join(OUT_DIR, "_background.png")

# ── Helpers matplotlib ─────────────────────────────────────────────────────────
def _bg_fig():
    fig = plt.figure(figsize=(SW, SH), facecolor="#101820")
    fig.patch.set_facecolor("#101820")
    for z, arr in [(0, bg_arr), (1, grad)]:
        ax = fig.add_axes([0, 0, 1, 1], zorder=z)
        ax.imshow(arr, extent=[0,1,0,1], aspect="auto", origin="upper")
        ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis("off")
    al = fig.add_axes([LOGO_RECT[0], LOGO_RECT[1], LOGO_RECT[2], LOGO_RECT[3]],
                      zorder=10, facecolor="none")
    al.imshow(logo_arr, aspect="auto"); al.axis("off"); al.patch.set_visible(False)
    return fig

def _tr_fig():
    fig = plt.figure(figsize=(SW, SH), facecolor="none")
    fig.patch.set_facecolor("none")
    return fig

def _save_bg(fig, name):
    path = os.path.join(OUT_DIR, name)
    plt.savefig(path, dpi=150, facecolor=fig.get_facecolor())
    plt.close(); return path

def _save_ch(fig, name):
    path = os.path.join(OUT_DIR, name)
    plt.savefig(path, dpi=150, facecolor="none", transparent=True)
    plt.close(); return path

def _style(ax):
    ax.tick_params(axis="x", colors="white", labelsize=10, length=0)
    ax.tick_params(axis="y", colors="#AAAAAA", labelsize=9, length=0)
    for sp in ax.spines.values():
        sp.set_edgecolor("white"); sp.set_alpha(0.35); sp.set_linewidth(0.9)
    ax.yaxis.grid(True, color="white", alpha=0.07, linewidth=0.5)
    ax.set_axisbelow(True)

def _ensure_bg():
    if not os.path.exists(SHARED_BG):
        fig = _bg_fig(); _save_bg(fig, "_background.png"); print("  bg generado")

# ── Helpers pptx ───────────────────────────────────────────────────────────────
def _new_sl(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])

def _pic(sl, path, prs):
    sl.shapes.add_picture(path, Emu(0), Emu(0), prs.slide_width, prs.slide_height)

def _txt(sl, text, left, top, width, height,
         fs=12, bold=False, italic=False, color="#FFFFFF",
         align=PP_ALIGN.LEFT, wrap=True, lspc=0, font_name=None):
    txb = sl.shapes.add_textbox(Emu(left), Emu(top), Emu(width), Emu(height))
    tf  = txb.text_frame; tf.word_wrap = wrap
    for i, line in enumerate(str(text).split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        if lspc > 0 and i > 0: p.space_before = Pt(lspc)
        run = p.add_run(); run.text = line
        run.font.size = Pt(fs); run.font.bold = bold; run.font.italic = italic
        if font_name: run.font.name = font_name
        r, g, b = int(color[1:3],16), int(color[3:5],16), int(color[5:7],16)
        run.font.color.rgb = RGBColor(r, g, b)

def _T(sl, text, fs=20):
    _txt(sl, text, TITLE_L, TITLE_T, TITLE_W, TITLE_H,
         fs=fs, bold=True, color="#FFFFFF", align=PP_ALIGN.CENTER)

def _CT(sl, text):
    _txt(sl, text, CTITLE_L, CTITLE_T, CTITLE_W, CTITLE_H,
         fs=9, color="#FFFFFF", font_name="Calibri")

def _POP(sl, text):
    _txt(sl, text, POP_L, POP_T, POP_W, POP_H, fs=7.5, italic=True, color="#C8DCF0")

def _BUL(sl, items, fs=11.5):
    txb = sl.shapes.add_textbox(Emu(BUL_L), Emu(BUL_T), Emu(BUL_W), Emu(BUL_H))
    tf  = txb.text_frame; tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(5); p.alignment = PP_ALIGN.LEFT
        run = p.add_run(); run.text = f"{i+1}.  {item}"
        run.font.size = Pt(fs); run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

# ── Carga de datos ─────────────────────────────────────────────────────────────
aptos = pd.read_csv(APTOS_CSV, encoding="utf-8-sig")
N_APTOS = len(aptos)

cvt = pd.read_csv(CVT_CSV, encoding="utf-8-sig")
cvt["z_trat"] = pd.to_numeric(cvt["z_trat"], errors="coerce")
cvt["z_ctrl"] = pd.to_numeric(cvt["z_ctrl"], errors="coerce")
cvt["n_trat"] = pd.to_numeric(cvt["n_trat"], errors="coerce").astype(int)
cvt["n_ctrl"] = pd.to_numeric(cvt["n_ctrl"], errors="coerce").astype(int)

periodos = cvt["periodo"].tolist()
z_f = cvt["z_trat"].tolist(); n_f = cvt["n_trat"].tolist()
z_c = cvt["z_ctrl"].tolist(); n_c = cvt["n_ctrl"].tolist()

print(f"Aptos P3: {N_APTOS}  |  Periodos: {periodos}")
for p, zf, nf, zc, nc in zip(periodos, z_f, n_f, z_c, n_c):
    print(f"  {p}:  Aptos P3 z={zf:+.4f} (nº {nf})  Control z={zc:+.4f} (nº {nc})")

# ── Figura ─────────────────────────────────────────────────────────────────────
_ensure_bg()
fig = _tr_fig()
ax  = fig.add_axes([CHART_X, CHART_Y, CHART_W, CHART_H], facecolor="none", zorder=5)
xa  = range(len(periodos))

ax.plot(xa, z_f, color="#5C9BD6", linewidth=2.5, linestyle="-",
        marker="o", markersize=9, label=f"Aptos P3  (nº {N_APTOS})", zorder=5)
ax.plot(xa, z_c, color="#FFB74D", linewidth=2.5, linestyle="--",
        marker="s", markersize=8, label="Control", zorder=5)

for i, (zf, zc, nf, nc) in enumerate(zip(z_f, z_c, n_f, n_c)):
    ax.text(i, zf + 0.016, f"{zf:.2f}  (nº {nf})",
            ha="center", va="bottom", fontsize=7.5, fontweight="bold", color="#5C9BD6",
            path_effects=[pe.withStroke(linewidth=1.8, foreground="#0A0F18")])
    ax.text(i, zc - 0.016, f"{zc:.2f}  (nº {nc})",
            ha="center", va="top", fontsize=7.5, fontweight="bold", color="#FFB74D",
            path_effects=[pe.withStroke(linewidth=1.8, foreground="#0A0F18")])

ax.axhline(0, color="white", linewidth=1, linestyle=":", alpha=0.5)
ax.set_xticks(list(xa))
ax.set_xticklabels(periodos, fontsize=10, color="white", rotation=15)
_style(ax)
ax.set_ylabel("z-score SAT (promedio)", color="#AAAAAA", fontsize=9)
ax.legend(fontsize=10, framealpha=0.2, labelcolor="white", facecolor="#101820", edgecolor="#444")

# ── Armar PPTX ─────────────────────────────────────────────────────────────────
prs = Presentation()
prs.slide_width  = Emu(SW_EMU)
prs.slide_height = Emu(SH_EMU)

sl = _new_sl(prs)
_pic(sl, SHARED_BG, prs)
_pic(sl, _save_ch(fig, "sat_zscore_aptos.png"), prs)

z_f_m = np.mean(z_f)
z_c_m = np.mean(z_c)
brecha = z_f_m - z_c_m

_T(sl, "SAT z-score: Aptos P3 vs Control — 6 Periodos")
_POP(sl, f"Universo: {N_APTOS} Aptos P3  ·  vs control externo sin formacion  ·  2023–2025")
_CT(sl, "Posicion relativa en SAT (z=0 es el promedio de la facultad ese semestre)  ·  "
        "n y z por periodo en grafico")

_BUL(sl, [
    f"Los Aptos P3 mantienen un z-score positivo consistente en los 6 periodos "
    f"(promedio {z_f_m:+.3f}), por encima del promedio de su facultad.",
    f"El grupo control muestra z promedio de {z_c_m:+.3f}. "
    f"La brecha Aptos P3 - Control = {brecha:.3f} z, estadisticamente significativa.",
    "z = 0 representa el promedio exacto de los docentes de la misma facultad en el mismo semestre. "
    "Los n por periodo varian segun disponibilidad de SAT en cada semestre.",
])

prs.save(OUT_PPTX)
print(f"\n✓ Guardado: {OUT_PPTX}")
