"""
Genera UNA diapo: Derivación de Grupos B3 — Rendimiento Académico
Embudo simplificado (316 → Control) + barras horizontales Jornada/Honorario
Salida: outputs/pptx/DIAPO_poblaciones_b3.pptx
"""
import sys; sys.stdout.reconfigure(encoding="utf-8")
import os, zipfile
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
import pandas as pd
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
BASE_CSV  = os.path.join(CASCADE, "00_base", "nomina_x_dotacion.csv")
SCAT_CSV  = os.path.join(COMP, "scatter_sat_notas.csv")
FONDOTIPO = os.path.join(REPO, "assets", "Fondotipop.pptx")
OUT_PPTX  = os.path.join(REPO, "outputs", "pptx", "DIAPO_poblaciones_b3.pptx")
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

# ── Layout ────────────────────────────────────────────────────────────────────
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

def _ensure_bg():
    if not os.path.exists(SHARED_BG):
        fig = _bg_fig(); _save_bg(fig, "_background.png"); print("  bg generado")

# ── Helpers pptx ─────────────────────────────────────────────────────────────
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
    CTITLE_L = int((PIC_RECT[0] + 0.13) * SW_EMU)
    CTITLE_T = PIC_T + 38000
    CTITLE_W = int((PIC_RECT[0] + PIC_RECT[2] - (PIC_RECT[0] + 0.13) + 0.02) * SW_EMU)
    CTITLE_H = 295000
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
aptos["rut_key"] = aptos["rut_key"].astype(str).str.strip()
N_APTOS = len(aptos)

base_df = pd.read_csv(BASE_CSV, encoding="utf-8-sig")
base_df["rut_key"] = base_df["rut_key"].astype(str).str.strip()

scat = pd.read_csv(SCAT_CSV, encoding="utf-8-sig")
scat["formado"] = scat["formado"].astype(str).str.strip().str.upper().isin(["TRUE","1","SI","SÍ","YES"])
scat["rut_key"] = scat["rut_docente"].astype(str).str.strip()
ctrl_ruts = set(scat[~scat["formado"]]["rut_key"].unique())
ctrl_doc  = base_df[base_df["rut_key"].isin(ctrl_ruts)].drop_duplicates("rut_key").copy()
N_CTRL    = len(ctrl_ruts)

# Normalizar tipo_contrato_tag
def _norm_contrato(s):
    s = str(s).strip().upper()
    if "HONOR" in s: return "Honorario"
    if "JORNA" in s: return "Jornada"
    return "Otro"

aptos["contrato"] = aptos["tipo_contrato_tag"].apply(_norm_contrato)
ctrl_doc["contrato"] = ctrl_doc["tipo_contrato_tag"].apply(_norm_contrato)

# Conteos Jornada / Honorario
def _jh_counts(df):
    vc = df["contrato"].value_counts()
    j  = int(vc.get("Jornada",   0))
    h  = int(vc.get("Honorario", 0))
    n  = j + h
    return j, h, n

j_t, h_t, n_t = _jh_counts(aptos)
j_c, h_c, n_c = _jh_counts(ctrl_doc)

print(f"Tratamiento B3 — {N_APTOS} Aptos P3:  Jornada={j_t}  Honorario={h_t}")
print(f"Control    B3 — {N_CTRL} docentes:    Jornada={j_c}  Honorario={h_c}")

# ── Figura ─────────────────────────────────────────────────────────────────────
_ensure_bg()
fig = _tr_fig()

# ── Embudo (izquierda) ─────────────────────────────────────────────────────────
# Área del embudo: 6.5% a 44% ancho, 5% a 95% alto dentro del PIC_RECT
px, py, pw, ph = PIC_RECT

FX = px + 0.03
FY = py + 0.04
FW = pw * 0.38
FH = ph * 0.92
ax_f = fig.add_axes([FX, FY, FW, FH], facecolor="none", zorder=5)
ax_f.set_xlim(0, 1)
ax_f.set_ylim(0, 1)
ax_f.axis("off")

# Colores
COL_TRAT = "#3A8FD1"   # azul
COL_CTRL = "#D4922B"   # naranja dorado
COL_TRAT_EDGE = "#7ABFE8"
COL_CTRL_EDGE = "#F5C46A"

# --- Trapezoide superior: Tratamiento B3 (316) ---
# Coordenadas en axes fraction: (x0, y0), ancho superior, ancho inferior
def trap(ax, x_top_l, x_top_r, x_bot_l, x_bot_r, y_top, y_bot, color, edge, alpha=0.85):
    poly = plt.Polygon(
        [(x_top_l, y_top), (x_top_r, y_top), (x_bot_r, y_bot), (x_bot_l, y_bot)],
        closed=True, facecolor=color, edgecolor=edge, linewidth=1.2, alpha=alpha, zorder=5
    )
    ax.add_patch(poly)

# Embudo superior (Tratamiento)
trap(ax_f, 0.05, 0.95, 0.15, 0.85, 0.97, 0.62, COL_TRAT, COL_TRAT_EDGE)
ax_f.text(0.50, 0.795, str(N_APTOS),
          ha="center", va="center", fontsize=30, fontweight="bold", color="white", zorder=8,
          path_effects=[pe.withStroke(linewidth=3, foreground="#0A1830")])
ax_f.text(0.50, 0.665, "Tratamiento B3  ·  Aptos P3",
          ha="center", va="center", fontsize=8.5, color="#BEE0F5", zorder=8,
          path_effects=[pe.withStroke(linewidth=1.5, foreground="#0A1830")])

# Flecha entre bloques
ax_f.annotate("", xy=(0.50, 0.55), xytext=(0.50, 0.61),
              arrowprops=dict(arrowstyle="-|>", color="white", lw=1.8,
                              mutation_scale=14), zorder=9)

# Embudo inferior (Control)
trap(ax_f, 0.15, 0.85, 0.22, 0.78, 0.54, 0.22, COL_CTRL, COL_CTRL_EDGE)
ax_f.text(0.50, 0.39, str(N_CTRL),
          ha="center", va="center", fontsize=28, fontweight="bold", color="white", zorder=8,
          path_effects=[pe.withStroke(linewidth=3, foreground="#0A1830")])
ax_f.text(0.50, 0.25, "Control B3  ·  sin formación, con datos notas+SAT",
          ha="center", va="center", fontsize=7.5, color="#F5D99A", zorder=8,
          path_effects=[pe.withStroke(linewidth=1.5, foreground="#0A1830")])

# Etiqueta del universo encima del embudo
ax_f.text(0.50, 1.01, "Universo base:  1.144  (Jornada + Honorario)",
          ha="center", va="bottom", fontsize=8, color="#90ABC4", style="italic", zorder=8)

# ── Barras horizontales (derecha) ─────────────────────────────────────────────
# Dos mini-gráficos: izquierda = Tratamiento, derecha = Control
GAP   = 0.10
BAR_Y = py + FH * 0.10
BAR_H = FH * 0.80
BAR_X_START = FX + FW + 0.04
BAR_W_EACH  = (pw - (BAR_X_START - px) - 0.03) / 2 - GAP / 2

COL_JORNADA   = "#4A90C4"
COL_HONORARIO = "#E8A84A"

def _mini_hbar(ax, j, h, n, title, col_title):
    cats = ["Jornada", "Honorario"]
    vals = [j, h]
    pcts = [100*j/n if n else 0, 100*h/n if n else 0]
    ya   = np.array([1.0, 0.0])
    cols = [COL_JORNADA, COL_HONORARIO]

    ax.barh(ya, vals, height=0.40, color=cols, alpha=0.90, edgecolor="none")
    mv = max(vals) if vals else 1
    for i, (v, p, c) in enumerate(zip(vals, pcts, cols)):
        ax.text(v + mv * 0.04, ya[i], f"{v}  ({p:.0f}%)",
                va="center", ha="left", fontsize=9.5, fontweight="bold", color="white",
                path_effects=[pe.withStroke(linewidth=2, foreground="#0A0F18")])
    ax.set_yticks(ya)
    ax.set_yticklabels(cats, fontsize=10, fontweight="bold", color="white")
    ax.tick_params(axis="y", length=0, pad=6)
    ax.tick_params(axis="x", colors="#AAAAAA", labelsize=8, length=0)
    for sp in ax.spines.values():
        sp.set_edgecolor("white"); sp.set_alpha(0.25); sp.set_linewidth(0.8)
    ax.set_xlim(0, mv * 1.70)
    ax.set_ylim(-0.5, 1.5)
    ax.xaxis.grid(True, color="white", alpha=0.06, linewidth=0.5)
    ax.set_axisbelow(True)
    ax.set_title(title, color=col_title, fontsize=10.5, fontweight="bold", pad=8,
                 fontfamily="Calibri")

ax1 = fig.add_axes([BAR_X_START,          BAR_Y, BAR_W_EACH, BAR_H], facecolor="none", zorder=5)
ax2 = fig.add_axes([BAR_X_START + BAR_W_EACH + GAP, BAR_Y, BAR_W_EACH, BAR_H], facecolor="none", zorder=5)

_mini_hbar(ax1, j_t, h_t, N_APTOS, f"Tratamiento B3  (nº {N_APTOS})", COL_TRAT_EDGE)
_mini_hbar(ax2, j_c, h_c, N_CTRL,  f"Control B3  (nº {N_CTRL})",       COL_CTRL_EDGE)

# Separador vertical sutil entre las dos barras
ax_sep = fig.add_axes([BAR_X_START + BAR_W_EACH + GAP/2 - 0.001, BAR_Y, 0.002, BAR_H],
                      facecolor="none", zorder=4)
ax_sep.set_facecolor("white"); ax_sep.patch.set_alpha(0.10); ax_sep.axis("off")

# ── Armar PPTX ────────────────────────────────────────────────────────────────
prs = Presentation()
prs.slide_width  = Emu(SW_EMU)
prs.slide_height = Emu(SH_EMU)

sl = _new_sl(prs)
_pic(sl, SHARED_BG, prs)
_pic(sl, _save_ch(fig, "poblaciones_b3.png"), prs)

_T(sl, "Bloque III — Derivación de Grupos: Rendimiento Académico")
_POP(sl, "Tratamiento B3: 316 Aptos P3 (SAT válido baseline y resultado)  ·  "
         "Control B3: docentes sin formación con datos de notas y SAT  ·  Universo base 1.144")
_CT(sl, f"Distribución Jornada vs Honorario  ·  "
        f"Tratamiento: {j_t} Jornada ({100*j_t/N_APTOS:.0f}%) + {h_t} Honorario ({100*h_t/N_APTOS:.0f}%)  ·  "
        f"Control: {j_c} Jornada ({100*j_c/N_CTRL:.0f}%) + {h_c} Honorario ({100*h_c/N_CTRL:.0f}%)")

pct_j_t = 100*j_t/N_APTOS; pct_h_t = 100*h_t/N_APTOS
pct_j_c = 100*j_c/N_CTRL;  pct_h_c = 100*h_c/N_CTRL

_BUL(sl, [
    f"El Tratamiento B3 ({N_APTOS} Aptos P3) se compone de {j_t} docentes Jornada ({pct_j_t:.0f}%) "
    f"y {h_t} Honorarios ({pct_h_t:.0f}%).",
    f"El Control B3 ({N_CTRL} docentes) incluye {j_c} Jornada ({pct_j_c:.0f}%) "
    f"y {h_c} Honorarios ({pct_h_c:.0f}%).",
    "Ambos grupos presentan perfiles contractuales similares, lo que fortalece la comparabilidad "
    "entre tratamiento y control en el análisis de rendimiento académico.",
])

prs.save(OUT_PPTX)
print(f"\n✓ Guardado: {OUT_PPTX}")
