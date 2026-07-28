"""
Genera UNA diapo: Perfil por Facultad — Aptos P3 vs Control (Bloque II)
Layout pareado: izquierda = Aptos P3 (316), derecha = Control
Salida: outputs/pptx/DIAPO_facultad_pareado.pptx
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
SCAT_CSV   = os.path.join(COMP, "scatter_sat_notas.csv")
NOMINA_CSV = os.path.join(CASCADE, "00_base", "nomina_x_dotacion.csv")
FONDOTIPO = (r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO"
             r"\Downloads\Analisis_UCEN_v2\Fondotipop.pptx")
OUT_PPTX  = os.path.join(REPO, "outputs", "pptx", "DIAPO_facultad_pareado.pptx")
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

CHART_X = PIC_RECT[0] + 0.15   # margen izq para etiquetas eje Y
CHART_Y = PIC_RECT[1] + 0.04
CHART_W = PIC_RECT[2] - 0.17   # ancho total de la zona de graficos
CHART_H = PIC_RECT[3] - 0.09

CTITLE_L = int((PIC_RECT[0] + 0.13) * SW_EMU)
CTITLE_T = PIC_T + 38000
CTITLE_W = int((PIC_RECT[0] + PIC_RECT[2] - (PIC_RECT[0] + 0.13) + 0.02) * SW_EMU)
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

# ── Normalizar facultad ────────────────────────────────────────────────────────
import unicodedata

def _strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")

def _fac(s):
    if not isinstance(s, str): return str(s)
    s = s.strip(); u = _strip_accents(s).upper()
    if "MEDICINA" in u and "SALUD" in u:        return "Medicina y C. Salud"
    if "DERECHO" in u and "HUMANIDADES" in u:   return "Derecho y Humanidades"
    if "INGENIER" in u:                         return "Ingenieria y Arq."
    if "EDUCACI" in u:                          return "Educacion"
    if "ECONOM" in u and "GOBIERNO" in u:       return "Economia, Gob. y Com."
    if "INVEST" in u and "INNOV" in u:          return "VR Investigacion"
    if "VICERRECTORIA" in u and "ACADEM" in u:  return "VR Academica"
    if "ASEGURAMIENTO" in u:                    return "Dir. Aseg. Calidad"
    if "JUNTA" in u:                            return "Junta Directiva"
    return s[:28].title()

# ── Carga de datos ─────────────────────────────────────────────────────────────
sat = pd.read_csv(APTOS_CSV, encoding="utf-8-sig")
sat["rut_key"] = sat["rut_key"].astype(str).str.strip()
N_APTOS = len(sat)

# Control B3: docentes con formado=False en scatter_sat_notas (= 300)
scat = pd.read_csv(SCAT_CSV, encoding="utf-8-sig")
ruts_ctrl = set(scat[~scat["formado"]]["rut_docente"].astype(str).str.strip().unique())

# Obtener unidad_facultad desde nomina (fuente actualizada)
nomina = pd.read_csv(NOMINA_CSV, encoding="utf-8-sig")
nomina["rut_key"] = nomina["rut_key"].astype(str).str.strip()
ctrl_uniq = nomina[nomina["rut_key"].isin(ruts_ctrl)][["rut_key","unidad_facultad"]].drop_duplicates("rut_key")
N_CTRL = len(ctrl_uniq)

# Facultad Aptos P3
sat_fac = sat[sat["unidad_facultad"].notna()].copy()
sat_fac["fac"] = sat_fac["unidad_facultad"].str.strip().apply(_fac)
cnt_ap  = sat_fac["fac"].value_counts()

# Facultad Control
ctrl_fac = ctrl_uniq[ctrl_uniq["unidad_facultad"].notna()].copy()
ctrl_fac["fac"] = ctrl_fac["unidad_facultad"].str.strip().apply(_fac)
cnt_ct   = ctrl_fac["fac"].value_counts()

# Unificar orden de facultades (union de ambas listas, ordenado por aptos)
all_facs = list(cnt_ap.index)
for f in cnt_ct.index:
    if f not in all_facs:
        all_facs.append(f)

val_ap = [int(cnt_ap.get(f, 0)) for f in all_facs]
val_ct = [int(cnt_ct.get(f, 0)) for f in all_facs]

# Denominadores = solo docentes con facultad asignada (para que sumen 100%)
n_ap_fac = sum(val_ap)
n_ct_fac = sum(val_ct)
pct_ap = [100*v/n_ap_fac if n_ap_fac else 0 for v in val_ap]
pct_ct = [100*v/n_ct_fac if n_ct_fac else 0 for v in val_ct]

print(f"Aptos P3: {N_APTOS} total  |  {n_ap_fac} con facultad asignada")
print(f"Control:  {N_CTRL} total  |  {n_ct_fac} con facultad asignada")
for f, va, vc in zip(all_facs, val_ap, val_ct):
    print(f"  {f:<32} Aptos={va:3d} ({100*va/n_ap_fac:.1f}%)  Ctrl={vc:3d} ({100*vc/n_ct_fac:.1f}%)")

# ── Figura pareada ─────────────────────────────────────────────────────────────
_ensure_bg()
fig = _tr_fig()

GAP    = 0.17           # ~2.3 pulgadas de separacion entre paneles
W_EACH = (CHART_W - GAP) / 2
n_fac  = len(all_facs)
ya     = np.arange(n_fac)

PAL_AP = ["#5C9BD6","#64B5F6","#80DEEA","#A5D6A7","#90CAF9","#4FC3F7","#4DD0E1","#80CBC4","#B39DDB"]
PAL_CT = ["#FFB74D","#FFA726","#FF8F00","#FFCA28","#FFD54F","#FFE082","#FF7043","#FF5722","#FFCCBC"]

def _hbar_panel(ax, labels, vals, pcts, n_total, title, col_title, palette, xlim_max=None):
    mv      = max(vals) if vals else 1
    x_limit = xlim_max if xlim_max else mv * 1.65
    ax.barh(ya[::-1], vals, height=0.58, color=palette[:n_fac], alpha=0.90, edgecolor="none")
    for i, (v, p) in enumerate(zip(vals[::-1], pcts[::-1])):
        if v > 0:
            lbl_x = v + x_limit * 0.018   # offset fijo relativo al limite del eje
            if lbl_x < x_limit * 0.97:    # solo dibujar si cabe dentro del panel
                ax.text(lbl_x, i, f"{v}  ({p:.1f}%)",
                        va="center", ha="left", fontsize=7.5, fontweight="bold", color="white",
                        clip_on=True,
                        path_effects=[pe.withStroke(linewidth=2, foreground="#0A0F18")])
    ax.set_yticks(ya)
    ax.set_yticklabels(labels[::-1], fontsize=8, fontweight="bold", color="white")
    ax.tick_params(axis="y", length=0, pad=6)
    ax.tick_params(axis="x", colors="#AAAAAA", labelsize=8, length=0)
    for sp in ax.spines.values():
        sp.set_edgecolor("white"); sp.set_alpha(0.25); sp.set_linewidth(0.8)
    ax.set_xlim(0, x_limit)
    ax.set_ylim(-0.5, n_fac - 0.5)
    ax.xaxis.grid(True, color="white", alpha=0.06, linewidth=0.5)
    ax.set_axisbelow(True)
    ax.set_title(title, color=col_title, fontsize=11, fontweight="bold", pad=8,
                 fontfamily="Calibri")

ax1 = fig.add_axes([CHART_X,            CHART_Y, W_EACH, CHART_H], facecolor="none", zorder=5)
ax2 = fig.add_axes([CHART_X+W_EACH+GAP, CHART_Y, W_EACH, CHART_H], facecolor="none", zorder=5)

_hbar_panel(ax1, all_facs, val_ap, pct_ap, n_ap_fac,
            f"Aptos P3  (nº {n_ap_fac})", "#7ABFE8", PAL_AP, xlim_max=120)
_hbar_panel(ax2, all_facs, val_ct, pct_ct, n_ct_fac,
            f"Control  (nº {n_ct_fac})",  "#F5C46A", PAL_CT)

# Separador vertical sutil centrado en el gap
sep_x = CHART_X + W_EACH + GAP/2 - 0.001
ax_sep = fig.add_axes([sep_x, CHART_Y, 0.002, CHART_H], facecolor="none", zorder=4)
ax_sep.set_facecolor("white"); ax_sep.patch.set_alpha(0.12); ax_sep.axis("off")

# ── Armar PPTX ─────────────────────────────────────────────────────────────────
prs = Presentation()
prs.slide_width  = Emu(SW_EMU)
prs.slide_height = Emu(SH_EMU)

sl = _new_sl(prs)
_pic(sl, SHARED_BG, prs)
_pic(sl, _save_ch(fig, "facultad_pareado.png"), prs)

_T(sl, "Perfil por Facultad — Aptos P3 vs Grupo Control")
_POP(sl, f"Aptos P3: {N_APTOS} docentes (nº {n_ap_fac} con facultad asignada)  ·  "
         f"Control: {N_CTRL} docentes (nº {n_ct_fac} con facultad asignada)  ·  % sobre evaluados con dato")
_CT(sl, f"Distribucion por unidad/facultad  ·  Izq: Aptos P3 (nº {N_APTOS})  ·  "
        f"Der: Control Bloque II (nº {N_CTRL})  ·  porcentajes sobre docentes con facultad registrada")

# Facultad mas representada en cada grupo
top_ap = all_facs[val_ap.index(max(val_ap))]
top_ct = all_facs[val_ct.index(max(val_ct))]
_BUL(sl, [
    f"En los Aptos P3, {top_ap} concentra la mayor representacion "
    f"({max(val_ap)} doc., {max(pct_ap):.0f}% de los {n_ap_fac} con facultad registrada). "
    "La composicion refleja el perfil de participacion en iniciativas de formacion.",
    f"En el grupo control, {top_ct} lidera "
    f"({max(val_ct)} doc., {max(pct_ct):.0f}% de los {n_ct_fac} con facultad registrada). "
    "La distribucion por facultad es comparable entre ambos grupos.",
    "El z-score SAT normaliza por facultad y periodo, controlando las diferencias "
    "sistematicas entre unidades academicas.",
])

prs.save(OUT_PPTX)
print(f"\n✓ Guardado: {OUT_PPTX}")
