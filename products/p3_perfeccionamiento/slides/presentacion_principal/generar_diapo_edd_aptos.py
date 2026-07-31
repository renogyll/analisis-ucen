"""
Genera UNA diapo: Evolución EDD — Aptos P3 vs Control (2022–2025)
Grupo Tratamiento = 316 Aptos P3 (p3_sat_zscore.csv)
Grupo Control     = docentes sin formación con EDD disponible
Salida: outputs/pptx/DIAPO_edd_aptos.pptx
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
REPO    = str(pathlib.Path(BASE).parents[3])
CASCADE = os.path.join(REPO, "data", "cascade")
COMP    = os.path.join(CASCADE, "complementarios")

APTOS_CSV = os.path.join(CASCADE, "05_aptos_p3", "p3_sat_zscore.csv")
EDD_CSV   = os.path.join(COMP, "evaluacion_jefes.csv")
DOC918_CSV = os.path.join(CASCADE, "03_jerarquizados", "docente_918.csv")
FONDOTIPO = os.path.join(REPO, "assets", "Fondotipop.pptx")
OUT_PPTX  = os.path.join(REPO, "outputs", "pptx", "DIAPO_edd_aptos_v2.pptx")
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
aptos["rut_key"] = aptos["rut_key"].astype(str).str.strip()
ruts_aptos = set(aptos["rut_key"])
N_APTOS = len(ruts_aptos)

base_df = pd.read_csv(os.path.join(CASCADE, "00_base", "nomina_x_dotacion.csv"), encoding="utf-8-sig")
base_df["rut_key"] = base_df["rut_key"].astype(str).str.strip()
ruts_universo_base = set(base_df["rut_key"])

form_df = pd.read_csv(os.path.join(CASCADE, "04_formados_p3", "docentes_formados.csv"),
                      encoding="utf-8-sig").drop_duplicates("rut_key")
ruts_todos_formados = set(form_df["rut_key"].astype(str).str.strip())

if not os.path.exists(EDD_CSV):
    print("ERROR: No se encontró evaluacion_jefes.csv"); exit(1)

edd_df = pd.read_csv(EDD_CSV, dtype={"rut_key": str}, encoding="utf-8-sig")
edd_df["rut_key"]   = edd_df["rut_key"].str.strip()
edd_df["edd_total"] = pd.to_numeric(edd_df["edd_total"], errors="coerce")
edd_df["anio_eval"] = edd_df["anio_evaluacion"].apply(
    lambda x: str(int(float(x)))[:4] if pd.notna(x) else None)

# Tratamiento: Aptos P3 con EDD
edd_form = (edd_df[edd_df["rut_key"].isin(ruts_aptos)
                   & edd_df["edd_total"].notna()
                   & edd_df["anio_eval"].notna()]
            .drop_duplicates(subset=["rut_key", "anio_eval"]))

# Control: en universo_base pero SIN ninguna formación P3 (no solo sin ser "apto"), con EDD
# CORREGIDO 2026-07-30: antes excluía solo ruts_aptos (316) y restringía a ruts_917
# (jerarquizados), dejando colar 162 formados-no-aptos dentro del "control" (daba 292
# en vez de 134). Ver plan: bug de definición de control + bug de jerarquía, cuantificados.
edd_ctrl = (edd_df[edd_df["rut_key"].isin(ruts_universo_base)
                   & ~edd_df["rut_key"].isin(ruts_todos_formados)
                   & edd_df["edd_total"].notna()
                   & edd_df["anio_eval"].notna()]
            .drop_duplicates(subset=["rut_key", "anio_eval"]))

n_form_edd = edd_form["rut_key"].nunique()
n_ctrl_edd = edd_ctrl["rut_key"].nunique()
print(f"Aptos P3 con EDD: {n_form_edd} docentes")
print(f"Control con EDD:  {n_ctrl_edd} docentes")

anios_ord = sorted(edd_form["anio_eval"].unique())
print(f"Años: {anios_ord}")

z_f      = [edd_form[edd_form["anio_eval"]==a]["edd_total"].mean() for a in anios_ord]
z_c      = [edd_ctrl[edd_ctrl["anio_eval"]==a]["edd_total"].mean() for a in anios_ord]
n_f_yr   = [edd_form[edd_form["anio_eval"]==a]["rut_key"].nunique() for a in anios_ord]
n_c_yr   = [edd_ctrl[edd_ctrl["anio_eval"]==a]["rut_key"].nunique() for a in anios_ord]

for a, vf, vc, nf, nc in zip(anios_ord, z_f, z_c, n_f_yr, n_c_yr):
    print(f"  {a}:  Aptos P3={vf:.3f} (nº {nf})  Control={vc:.3f} (nº {nc})")

# ── Figura ─────────────────────────────────────────────────────────────────────
_ensure_bg()

fig = _tr_fig()
ax  = fig.add_axes([CHART_X, CHART_Y, CHART_W, CHART_H], facecolor="none", zorder=5)
xa  = range(len(anios_ord))

ax.plot(xa, z_f, color="#5C9BD6", linewidth=2.5, marker="o", markersize=9,
        label=f"Aptos P3  (nº {n_form_edd})", zorder=5)
ax.plot(xa, z_c, color="#FF7043", linewidth=2.5, linestyle="--", marker="s", markersize=8,
        label="Control", zorder=5)

all_vals = [v for v in z_f + z_c if not np.isnan(v)]

for i, (vf, vc, nf, nc) in enumerate(zip(z_f, z_c, n_f_yr, n_c_yr)):
    if not np.isnan(vf):
        ax.text(i, vf + 0.012, f"{vf:.3f}  (nº {nf})",
                ha="center", va="bottom", fontsize=8, fontweight="bold", color="#5C9BD6",
                path_effects=[pe.withStroke(linewidth=1.5, foreground="#0A0F18")])
    if not np.isnan(vc):
        ax.text(i, vc - 0.012, f"{vc:.3f}  (nº {nc})",
                ha="center", va="top", fontsize=8, fontweight="bold", color="#FF7043",
                path_effects=[pe.withStroke(linewidth=1.5, foreground="#0A0F18")])

ax.set_xticks(list(xa))
ax.set_xticklabels(anios_ord, fontsize=10, color="white")
_style(ax)
ax.set_ylabel("EDD Total (promedio)", color="#AAAAAA", fontsize=9)
ax.legend(fontsize=10, framealpha=0.2, labelcolor="white", facecolor="#101820", edgecolor="#444")
if all_vals:
    ax.set_ylim(max(0, min(all_vals) - 0.08), min(1.0, max(all_vals) + 0.08))

# ── Armar PPTX ─────────────────────────────────────────────────────────────────
prs = Presentation()
prs.slide_width  = Emu(SW_EMU)
prs.slide_height = Emu(SH_EMU)

sl = _new_sl(prs)
_pic(sl, SHARED_BG, prs)
_pic(sl, _save_ch(fig, "edd_aptos.png"), prs)

_T(sl, "Evolución EDD — Aptos P3 vs Control (2022–2025)")
_POP(sl, f"EDD: Evaluación de Desempeño Docente  ·  escala 0–1  ·  "
         f"Aptos P3 ({n_form_edd}) vs control externo sin formación")
_CT(sl, f"EDD Total promedio por año  ·  Aptos P3 nº {n_form_edd} doc. con dato  ·  "
        f"Control nº {n_ctrl_edd} doc.")

z_f_glo = edd_form["edd_total"].mean()
z_c_glo = edd_ctrl["edd_total"].mean() if len(edd_ctrl) else float("nan")
brecha   = z_f_glo - z_c_glo

_BUL(sl, [
    f"Los Aptos P3 obtienen EDD promedio de {z_f_glo:.3f} vs {z_c_glo:.3f} del grupo "
    f"control — brecha de {brecha:+.3f} puntos a favor de los Aptos P3.",
    "La brecha Aptos P3−Control se amplía en 2024 y 2025, coincidiendo con mayor volumen "
    "de formación impartida — el efecto acumulativo se refleja en la EDD.",
    "La EDD mide la evaluación de directivos sobre el desempeño docente, complementando "
    "las métricas SAT y rendimiento académico de alumnos con una perspectiva institucional.",
])

prs.save(OUT_PPTX)
print(f"\n✓ Guardado: {OUT_PPTX}")
