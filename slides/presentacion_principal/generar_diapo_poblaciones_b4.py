"""
Genera UNA diapo: Derivación de Grupos B4 — Evaluación de Desempeño Docente
Embudo 316 -> 206 (Tratamiento B4, Aptos P3 con EDD) -> 130 (Control B4)
Barras horizontales Jornada/Honorario para cada grupo
Salida: outputs/pptx/DIAPO_poblaciones_b4.pptx
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

APTOS_CSV  = os.path.join(CASCADE, "05_aptos_p3", "p3_sat_zscore.csv")
P3EV_CSV   = os.path.join(CASCADE, "04_formados_p3", "p3_918.csv")
DOC918_CSV = os.path.join(CASCADE, "03_jerarquizados", "docente_918.csv")
BASE_CSV   = os.path.join(CASCADE, "00_base", "nomina_x_dotacion.csv")
EDD_CSV    = os.path.join(COMP, "evaluacion_jefes.csv")
FONDOTIPO  = (r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO"
              r"\Downloads\Analisis_UCEN_v2\Fondotipop.pptx")
OUT_PPTX   = os.path.join(REPO, "outputs", "pptx", "DIAPO_poblaciones_b4.pptx")
OUT_DIR    = os.path.join(BASE, "dark_slides_v3")
SCRATCH    = os.path.join(REPO, "outputs", "scratch")
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
ruts_aptos = set(aptos["rut_key"])
N_APTOS = len(ruts_aptos)

p3ev = pd.read_csv(P3EV_CSV, encoding="utf-8-sig")
p3ev["rut_key"] = p3ev["rut_key"].astype(str).str.strip()
ruts_todos_form = set(p3ev["rut_key"])

doc918 = pd.read_csv(DOC918_CSV, dtype={"rut_key": str}, encoding="utf-8-sig")
ruts_917 = set(doc918["rut_key"].str.strip())

base_df = pd.read_csv(BASE_CSV, encoding="utf-8-sig")
base_df["rut_key"] = base_df["rut_key"].astype(str).str.strip()

edd_df = pd.read_csv(EDD_CSV, dtype={"rut_key": str}, encoding="utf-8-sig")
edd_df["rut_key"]   = edd_df["rut_key"].str.strip()
edd_df["edd_total"] = pd.to_numeric(edd_df["edd_total"], errors="coerce")
edd_df["anio_eval"] = edd_df["anio_evaluacion"].apply(
    lambda x: str(int(float(x)))[:4] if pd.notna(x) else None)

edd_form = (edd_df[edd_df["rut_key"].isin(ruts_aptos)
                   & edd_df["edd_total"].notna()
                   & edd_df["anio_eval"].notna()]
            .drop_duplicates(subset=["rut_key", "anio_eval"]))
edd_ctrl = (edd_df[edd_df["rut_key"].isin(ruts_917)
                   & ~edd_df["rut_key"].isin(ruts_todos_form)
                   & edd_df["edd_total"].notna()
                   & edd_df["anio_eval"].notna()]
            .drop_duplicates(subset=["rut_key", "anio_eval"]))

ruts_form_edd = set(edd_form["rut_key"].unique())
ruts_ctrl_edd = set(edd_ctrl["rut_key"].unique())
N_TRAT = len(ruts_form_edd)   # 206
N_CTRL = len(ruts_ctrl_edd)   # 130

def _norm(s):
    s = str(s).strip().upper()
    if "HONOR" in s: return "Honorario"
    if "JORNA" in s: return "Jornada"
    return "Otro"

trat_df = aptos[aptos["rut_key"].isin(ruts_form_edd)].copy()
ctrl_df = base_df[base_df["rut_key"].isin(ruts_ctrl_edd)].drop_duplicates("rut_key").copy()
trat_df["contrato"] = trat_df["tipo_contrato_tag"].apply(_norm)
ctrl_df["contrato"] = ctrl_df["tipo_contrato_tag"].apply(_norm)

j_t = int(trat_df["contrato"].value_counts().get("Jornada",   0))
h_t = int(trat_df["contrato"].value_counts().get("Honorario", 0))
j_c = int(ctrl_df["contrato"].value_counts().get("Jornada",   0))
h_c = int(ctrl_df["contrato"].value_counts().get("Honorario", 0))

print(f"Tratamiento B4: {N_TRAT}  Jornada={j_t}  Honorario={h_t}")
print(f"Control B4:     {N_CTRL}  Jornada={j_c}  Honorario={h_c}")

# ── Colores ────────────────────────────────────────────────────────────────────
COL_APTOS      = "#3A8FD1"    # azul — Aptos P3 (contexto)
COL_APTOS_EDGE = "#7ABFE8"
COL_TRAT       = "#2A6FAA"    # azul oscuro — Tratamiento B4 (206)
COL_TRAT_EDGE  = "#5BAED6"
COL_CTRL       = "#D4922B"    # naranja — Control B4
COL_CTRL_EDGE  = "#F5C46A"
COL_JORNADA    = "#4A90C4"
COL_HONORARIO  = "#E8A84A"

# ── Figura ─────────────────────────────────────────────────────────────────────
_ensure_bg()
fig = _tr_fig()

px, py, pw, ph = PIC_RECT

# ── Embudo (izquierda, 3 etapas) ──────────────────────────────────────────────
FX = px + 0.03
FY = py + 0.03
FW = pw * 0.28
FH = ph * 0.94
ax_f = fig.add_axes([FX, FY, FW, FH], facecolor="none", zorder=5)
ax_f.set_xlim(0, 1)
ax_f.set_ylim(0, 1)
ax_f.axis("off")

def trap(ax, x_tl, x_tr, x_bl, x_br, y_top, y_bot, color, edge, alpha=0.82):
    poly = plt.Polygon(
        [(x_tl, y_top), (x_tr, y_top), (x_br, y_bot), (x_bl, y_bot)],
        closed=True, facecolor=color, edgecolor=edge,
        linewidth=1.2, alpha=alpha, zorder=5
    )
    ax.add_patch(poly)

# Etapa 1: 206 Tratamiento B4 (azul oscuro) — ocupa parte superior del embudo
trap(ax_f, 0.05, 0.95, 0.16, 0.84, 0.97, 0.58, COL_TRAT, COL_TRAT_EDGE, alpha=0.90)
ax_f.text(0.50, 0.80, str(N_TRAT),
          ha="center", va="center", fontsize=36, fontweight="bold", color="white", zorder=8,
          path_effects=[pe.withStroke(linewidth=3, foreground="#0A1830")])
ax_f.text(0.50, 0.62, "Tratamiento B4  ·  Aptos P3 con EDD disponible",
          ha="center", va="center", fontsize=8, color="#BEE0F5", zorder=8,
          path_effects=[pe.withStroke(linewidth=1.5, foreground="#0A1830")])

# Flecha entre tratamiento y control
ax_f.annotate("", xy=(0.50, 0.50), xytext=(0.50, 0.57),
              arrowprops=dict(arrowstyle="-|>", color="white", lw=1.8, mutation_scale=14), zorder=9)

# Etapa 2: 130 Control B4 (naranja, caja rectangular)
rect = plt.Polygon(
    [(0.04, 0.49), (0.96, 0.49), (0.96, 0.16), (0.04, 0.16)],
    closed=True, facecolor=COL_CTRL, edgecolor=COL_CTRL_EDGE,
    linewidth=1.4, alpha=0.88, zorder=5
)
ax_f.add_patch(rect)
ax_f.text(0.50, 0.37, str(N_CTRL),
          ha="center", va="center", fontsize=36, fontweight="bold", color="white", zorder=8,
          path_effects=[pe.withStroke(linewidth=3, foreground="#0A1830")])
ax_f.text(0.50, 0.20, "Grupo Control B4  ·  sin actividad P3, con EDD comparable",
          ha="center", va="center", fontsize=8, color="#F5D99A", zorder=8,
          path_effects=[pe.withStroke(linewidth=1.5, foreground="#0A1830")])

# ── Barras horizontales (derecha) ─────────────────────────────────────────────
GAP         = 0.10
BAR_Y       = py + FH * 0.08
BAR_H       = FH * 0.84
BAR_X_START = FX + FW + 0.10
BAR_W_EACH  = (pw - (BAR_X_START - px) - 0.03) / 2 - GAP / 2

def _mini_hbar(ax, j, h, n, title, col_title):
    cats = ["Jornada", "Honorario"]
    vals = [j, h]
    pcts = [100*j/n if n else 0, 100*h/n if n else 0]
    ya   = np.array([1.0, 0.0])
    cols = [COL_JORNADA, COL_HONORARIO]

    ax.barh(ya, vals, height=0.40, color=cols, alpha=0.90, edgecolor="none")
    mv = max(vals) if vals else 1
    for i, (v, p) in enumerate(zip(vals, pcts)):
        ax.text(v + mv * 0.04, ya[i], f"{v}  ({p:.0f}%)",
                va="center", ha="left", fontsize=9.5, fontweight="bold", color="white",
                path_effects=[pe.withStroke(linewidth=2, foreground="#0A0F18")])
    ax.set_yticks(ya)
    ax.set_yticklabels(cats, fontsize=10, fontweight="bold", color="white")
    ax.tick_params(axis="y", length=0, pad=6)
    ax.tick_params(axis="x", colors="#AAAAAA", labelsize=8, length=0)
    for sp in ax.spines.values():
        sp.set_edgecolor("white"); sp.set_alpha(0.25); sp.set_linewidth(0.8)
    ax.set_xlim(0, mv * 1.75)
    ax.set_ylim(-0.5, 1.5)
    ax.xaxis.grid(True, color="white", alpha=0.06, linewidth=0.5)
    ax.set_axisbelow(True)
    ax.set_title(title, color=col_title, fontsize=10.5, fontweight="bold", pad=8,
                 fontfamily="Calibri")

ax1 = fig.add_axes([BAR_X_START,                   BAR_Y, BAR_W_EACH, BAR_H],
                   facecolor="none", zorder=5)
ax2 = fig.add_axes([BAR_X_START + BAR_W_EACH + GAP, BAR_Y, BAR_W_EACH, BAR_H],
                   facecolor="none", zorder=5)

_mini_hbar(ax1, j_t, h_t, N_TRAT, f"Tratamiento B4  (nº {N_TRAT})", COL_TRAT_EDGE)
_mini_hbar(ax2, j_c, h_c, N_CTRL, f"Control B4  (nº {N_CTRL})",      COL_CTRL_EDGE)

# ── Armar PPTX ─────────────────────────────────────────────────────────────────
prs = Presentation()
prs.slide_width  = Emu(SW_EMU)
prs.slide_height = Emu(SH_EMU)

sl = _new_sl(prs)
_pic(sl, SHARED_BG, prs)
_pic(sl, _save_ch(fig, "poblaciones_b4.png"), prs)

_T(sl, "Bloque IV — Derivación de Grupos: Evaluación de Desempeño Docente")
_POP(sl, f"Tratamiento: {N_TRAT} Aptos P3 con EDD disponible  ·  "
         f"Control: {N_CTRL} docentes sin actividad P3, con EDD comparable")
_CT(sl, f"Izq.: embudo de derivacion desde 316 Aptos P3 hasta Tratamiento B4  ·  "
        f"Der.: composicion Jornada/Honorario Tratamiento vs Control")

pct_j_t = 100*j_t/N_TRAT; pct_h_t = 100*h_t/N_TRAT
pct_j_c = 100*j_c/N_CTRL; pct_h_c = 100*h_c/N_CTRL

_BUL(sl, [
    f"El Tratamiento B4 ({N_TRAT} Aptos P3 con EDD) se compone de {j_t} docentes Jornada "
    f"({pct_j_t:.0f}%) y {h_t} Honorarios ({pct_h_t:.0f}%). "
    f"({N_APTOS - N_TRAT} de los {N_APTOS} Aptos P3 no tienen EDD registrada.)",
    f"El Control B4 ({N_CTRL} docentes) incluye {j_c} Jornada ({pct_j_c:.0f}%) "
    f"y {h_c} Honorarios ({pct_h_c:.0f}%).",
    "El Tratamiento B4 esta compuesto mayoritariamente por docentes de Jornada, "
    "lo cual es consistente con que la EDD se aplica principalmente a planta regular.",
])

prs.save(OUT_PPTX)
print(f"\n✓ Guardado: {OUT_PPTX}")
