"""
Genera UNA diapo: Correlación SAT vs Nota Promedio — Aptos P3 vs Sin Formación (3 paneles)
Grupo Tratamiento = 316 Aptos P3 (p3_sat_zscore.csv)
Grupo Control     = resto de docentes en scatter (sin formación)
Salida: outputs/pptx/DIAPO_scatter_aptos.pptx
"""
import sys; sys.stdout.reconfigure(encoding="utf-8")
import os, zipfile
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import pandas as pd
from scipy import stats as scipy_stats
from PIL import Image as PILImage
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
import pathlib

# ── Rutas ─────────────────────────────────────────────────────────────────────
BASE    = os.path.dirname(os.path.abspath(__file__))
REPO    = str(pathlib.Path(BASE).parents[3])
CASCADE = os.path.join(REPO, "data", "cascade")
COMP    = os.path.join(CASCADE, "complementarios")

APTOS_CSV = os.path.join(CASCADE, "05_aptos_p3", "p3_sat_zscore.csv")
SCAT_CSV  = os.path.join(COMP, "scatter_sat_notas.csv")
FONDOTIPO = os.path.join(REPO, "assets", "Fondotipop.pptx")
OUT_PPTX  = os.path.join(REPO, "outputs", "pptx", "DIAPO_scatter_aptos.pptx")
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

def _style(ax, xlabel=None, xgrid=False):
    ax.tick_params(axis="x", colors="white", labelsize=9, length=0)
    ax.tick_params(axis="y", colors="#AAAAAA", labelsize=9, length=0)
    for sp in ax.spines.values():
        sp.set_edgecolor("white"); sp.set_alpha(0.35); sp.set_linewidth(0.9)
    ax.yaxis.grid(True, color="white", alpha=0.07, linewidth=0.5)
    if xgrid: ax.xaxis.grid(True, color="white", alpha=0.07, linewidth=0.5)
    ax.set_axisbelow(True)
    if xlabel: ax.set_xlabel(xlabel, color="#AAAAAA", fontsize=9)

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
aptos["rut_key"] = aptos["rut_key"].astype(str).str.strip()
ruts_aptos = set(aptos["rut_key"])
N_APTOS = len(ruts_aptos)
print(f"Aptos P3 cargados: {N_APTOS} docentes")

scat = pd.read_csv(SCAT_CSV, encoding="utf-8-sig")
scat["sat"]           = pd.to_numeric(scat["sat"],           errors="coerce")
scat["nota_promedio"] = pd.to_numeric(scat["nota_promedio"], errors="coerce")
scat["rut_key"]       = scat["rut_docente"].astype(str).str.strip()
scat["anio"]          = scat["periodo"].str[:4]
scat = scat.dropna(subset=["sat", "nota_promedio"])

# Reemplazar la columna formado: Aptos P3 = formado, resto = sin formación
scat["es_apto"] = scat["rut_key"].isin(ruts_aptos)

# ── Figura 3 paneles ───────────────────────────────────────────────────────────
_ensure_bg()

COL_CTRL = "#FFB74D"   # naranja — sin formación
COL_FORM = "#5C9BD6"   # azul    — Aptos P3
ALPHA    = 0.38
MS       = 10
GAP      = 0.022
anios    = ["2023", "2024", "2025"]

stats_by_year = {}
for y in anios:
    s = scat[scat["anio"] == y]
    if len(s) < 2:
        stats_by_year[y] = dict(r=0, p=1, n_sec=0, n_f=0, n_c=0)
        continue
    r, p = scipy_stats.pearsonr(s["sat"], s["nota_promedio"])
    n_f  = int(s[s["es_apto"]]["rut_key"].nunique())
    n_c  = int(s[~s["es_apto"]]["rut_key"].nunique())
    stats_by_year[y] = dict(r=r, p=p, n_sec=len(s), n_f=n_f, n_c=n_c)
    print(f"  {y}: r={r:.3f}  n_sec={len(s)}  Aptos P3={n_f}  Sin form={n_c}")

fig = _tr_fig()
gx  = PIC_RECT[0] + 0.04
gy  = PIC_RECT[1] + 0.005
gw  = PIC_RECT[2] - 0.055
gh  = PIC_RECT[3] - 0.05
pw  = (gw - GAP*2) / 3

for i, y in enumerate(anios):
    s   = scat[scat["anio"] == y]
    sf  = s[s["es_apto"]]      # Aptos P3
    sc2 = s[~s["es_apto"]]     # Sin formación
    st  = stats_by_year[y]
    ax  = fig.add_axes([gx + i*(pw+GAP), gy, pw, gh], facecolor="none", zorder=5)

    # Primero el control (detrás), luego Aptos P3 (encima)
    ax.scatter(sc2["sat"], sc2["nota_promedio"],
               c=COL_CTRL, alpha=ALPHA, s=MS, linewidths=0, zorder=2,
               label=f"Sin formación  (nº {st['n_c']})")
    ax.scatter(sf["sat"], sf["nota_promedio"],
               c=COL_FORM, alpha=ALPHA+0.14, s=MS, linewidths=0, zorder=3,
               label=f"Aptos P3  (nº {st['n_f']})")

    if len(s) >= 2:
        x_all = s["sat"].values; y_all = s["nota_promedio"].values
        m, b  = np.polyfit(x_all, y_all, 1)
        xr    = np.array([x_all.min(), x_all.max()])
        ax.plot(xr, m*xr+b, "--", color="white", linewidth=1.5, alpha=0.60, zorder=4,
                label=f"Tendencia  (r={round(st['r'], 2)})")

    _style(ax, xlabel="SAT docente (sobre 7)", xgrid=True)
    ax.set_xlim(1, 7); ax.set_ylim(1, 7)
    ax.set_xticks([1,2,3,4,5,6,7]); ax.set_yticks([1,2,3,4,5,6,7])
    if i == 0:
        ax.set_ylabel("Nota promedio alumnos (sobre 7)", color="#AAAAAA", fontsize=8.5)
    else:
        ax.set_yticklabels([])
    ax.set_title(f"Año {y}", color="white", fontsize=10.5, fontweight="bold", pad=6)

    leg = ax.legend(fontsize=7.2, framealpha=0.35, facecolor="#101820",
                    edgecolor="#444444", loc="upper left", markerscale=1.5,
                    handlelength=0.8, borderpad=0.5, labelspacing=0.35)
    for txt in leg.get_texts(): txt.set_color("white")

    p_str = "< 0.001" if st["p"] < 0.001 else f"= {round(st['p'], 3)}"
    ax.text(0.97, 0.05,
            f"r = {round(st['r'], 2)}\np {p_str}\n{st['n_sec']} secciones",
            transform=ax.transAxes, fontsize=8, va="bottom", ha="right",
            color="white",
            bbox=dict(boxstyle="round,pad=0.45", facecolor="#1A2E10",
                      edgecolor="#6AAA40", alpha=0.88))

# ── Armar PPTX ─────────────────────────────────────────────────────────────────
prs = Presentation()
prs.slide_width  = Emu(SW_EMU)
prs.slide_height = Emu(SH_EMU)

sl = _new_sl(prs)
_pic(sl, SHARED_BG, prs)
_pic(sl, _save_ch(fig, "scatter_sat_nota_aptos.png"), prs)

r23 = round(stats_by_year["2023"]["r"], 2)
r24 = round(stats_by_year["2024"]["r"], 2)
r25 = round(stats_by_year["2025"]["r"], 2)

_T(sl, "Correlación Satisfacción Docente y Desempeño Académico Estudiantes según Nota Promedio de Año", fs=13)
_POP(sl, f"Universo con evaluaciones de satisfacción y calificaciones disponibles  |  "
         f"2023-01 a 2025-02  |  Cada punto = 1 sección  |  Aptos P3: nº {N_APTOS}")
_BUL(sl, [
    f"Correlación positiva y estadísticamente significativa entre SAT docente y nota promedio "
    f"de alumnos en los tres años (r≈{r23} en 2023, r≈{r24} en 2024, r≈{r25} en 2025; "
    f"p<0.001 en todos los cortes).",
    "Los Aptos P3 (azul) se concentran en la región SAT mayor a 5 con notas promedio superiores; "
    "los sin formación (naranja) presentan mayor dispersión hacia valores bajos en ambas dimensiones.",
    "La correlación se fortalece en 2024–2025, coincidiendo con el mayor volumen de formación, "
    "consistente con un efecto acumulativo sobre el rendimiento estudiantil.",
])

prs.save(OUT_PPTX)
print(f"\n✓ Guardado: {OUT_PPTX}")
