"""
POC: Slide 'Distribución por Unidad/Facultad'
Gráfico directo sobre fondo oscuro del template UCEN.
v2: fondo exacto (gradiente navy desde Fondotipop.pptx), logo UCEN,
    gráfico con borde blanco, bullets ancho completo.
"""
import sys; sys.stdout.reconfigure(encoding="utf-8")
import os, zipfile, textwrap
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib.patheffects as pe
import pandas as pd
from PIL import Image as PILImage

BASE       = os.path.dirname(__file__)
SCRATCH    = (r"C:\Users\RGONZA~1.LAP\AppData\Local\Temp\claude"
              r"\c--Users-r-gonzalez-fluxsolar-LAPTOP-FLUX-ECO-Downloads-Analisis-UCEN-v2"
              r"\19e6fc3f-6ca1-4150-9da7-8dfa38be71ca\scratchpad")
FONDOTIPO  = (r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO"
              r"\Downloads\Analisis_UCEN_v2\Fondotipop.pptx")
OUT_PDF    = os.path.join(BASE, "poc_slide_facultad_dark.pdf")
OUT_PNG    = os.path.join(BASE, "poc_slide_facultad_dark.png")

# ── 1. Extraer imágenes desde Fondotipop.pptx si aún no existen ──────────────
BG_PATH   = os.path.join(SCRATCH, "fondotipo_image1.jpg")   # foto edificio B&N
LOGO_PATH = os.path.join(SCRATCH, "fondotipo_image2.png")   # logo UCEN blanco

for path, zipname in [(BG_PATH,   "ppt/media/image1.jpg"),
                      (LOGO_PATH, "ppt/media/image2.png")]:
    if not os.path.exists(path):
        with zipfile.ZipFile(FONDOTIPO) as z:
            data = z.read(zipname)
        with open(path, "wb") as f:
            f.write(data)

# ── 2. Foto de fondo — sin modificar tonalidad ────────────────────────────────
with PILImage.open(BG_PATH) as _im:
    _im_rgb = _im.convert("RGB")
    _iw, _ih = _im_rgb.size
    # Crop 16:9 centrado en el edificio (12% desde arriba)
    _new_h = int(_iw / (16 / 9))
    _y0    = min(int(_ih * 0.12), _ih - _new_h)
    _im_rgb = _im_rgb.crop((0, _y0, _iw, _y0 + _new_h))
    bg_arr = np.array(_im_rgb)   # (H, W, 3) uint8

print(f"Fondo: {bg_arr.shape}")

# ── 3. Logo UCEN (blanco sobre canal alfa) ────────────────────────────────────
with PILImage.open(LOGO_PATH) as _logo:
    logo_arr = np.array(_logo.convert("RGBA")).astype(np.float32) / 255.0
print(f"Logo: {logo_arr.shape}  alpha max={logo_arr[:,:,3].max():.2f}")

# ── 4. Gradiente navy overlay — idéntico al slide master de Fondotipop.pptx ──
# Stops extraídos del XML del master: ang=90° (top → bottom), alpha=80 000 (80%)
#   pos  0%  → #002147
#   pos 54%  → #004680  (schemeClr tx2 = dk2)
#   pos 100% → #90ABC4  (schemeClr accent1)
H_GRAD = 600
grad   = np.zeros((H_GRAD, 1, 4), dtype=np.float32)
stops  = [
    (0.00, (0x00, 0x21, 0x47)),
    (0.54, (0x00, 0x46, 0x80)),
    (1.00, (0x90, 0xAB, 0xC4)),
]
for row in range(H_GRAD):
    t = row / (H_GRAD - 1)
    for i in range(len(stops) - 1):
        t0, c0 = stops[i]
        t1, c1 = stops[i + 1]
        if t0 <= t <= t1:
            s = (t - t0) / (t1 - t0)
            r = c0[0] + s * (c1[0] - c0[0])
            g = c0[1] + s * (c1[1] - c0[1])
            b = c0[2] + s * (c1[2] - c0[2])
            grad[row, 0] = [r / 255, g / 255, b / 255, 0.82]
            break

# ── 5. Datos del gráfico ──────────────────────────────────────────────────────
p3    = pd.read_csv(os.path.join(BASE, "..", "PROCESADO", "p3_918.csv"),
                    encoding="utf-8-sig", dtype={"rut_key": str})
aptos = p3[p3["apto_p3"] == True].drop_duplicates("rut_key").copy()

ABREV = [
    ("MEDICINA",  "Medicina y C. Salud"),
    ("DERECHO",   "Derecho y Humanidades"),
    ("INGENIE",   "Ingenieria y Arq."),
    ("EDUCACI",   "Educacion"),
    ("ECONOM",    "Economia, Gob. y Com."),
    ("INVEST",    "VR Invest./Postgrado"),
    ("VICERRECT", "VR Academica"),
    ("ASEGURAM",  "Dir. Aseg. Calidad"),
]
def abrev_fac(key):
    ku = str(key).upper()
    for pat, label in ABREV:
        if pat in ku:
            return label
    return key[:30]

con_fac = aptos[aptos["unidad_facultad"].notna()].copy()
n_fac   = len(con_fac)
cnt_fac = con_fac["unidad_facultad"].str.strip().value_counts()
labels  = [abrev_fac(k) for k in cnt_fac.index]
vals    = cnt_fac.values.tolist()
pcts    = [100 * v / n_fac for v in vals]

PALETTE = ["#5C9BD6", "#64B5F6", "#80DEEA", "#A5D6A7",
           "#FFB74D", "#CE93D8", "#90A4AE", "#F48FB1"]

# ── 6. Constantes de layout (EMU → fracción de figura) ───────────────────────
SW, SH = 13.333, 7.5

def ex(e): return e / 12192000
def ey(e): return e / 6858000
def fig_rect(l, t, w, h): return (l, 1 - t - h, w, h)

TITLE_L, TITLE_T = ex(786582),  ey(250608)
TITLE_W, TITLE_H = ex(10599174), ey(553998)
POP_L,   POP_T   = ex(786582),  ey(820000)
POP_W,   POP_H   = ex(10599174), ey(290000)
PIC_L,   PIC_T   = ex(786581),  ey(1125000)
PIC_W,   PIC_H   = ex(10599174), ey(3720000)
BUL_L,   BUL_T   = ex(786581),  ey(4870000)
BUL_W,   BUL_H   = ex(10599174), ey(1870000)

# Logo (desde slide master XML de Fondotipop.pptx)
LOGO_L, LOGO_T = ex(9813773), ey(656354)
LOGO_W, LOGO_H = ex(1756626), ey(697725)

T_RECT    = fig_rect(TITLE_L, TITLE_T, TITLE_W, TITLE_H)
POP_Y     = 1 - POP_T - POP_H / 2
PIC_RECT  = fig_rect(PIC_L, PIC_T, PIC_W, PIC_H)
LOGO_RECT = fig_rect(LOGO_L, LOGO_T, LOGO_W, LOGO_H)

# Gráfico: ligeramente más pequeño que PIC_RECT
CHART_X = PIC_RECT[0] + 0.16
CHART_W = PIC_RECT[2] - 0.16 - 0.02
CHART_Y = PIC_RECT[1] + 0.04
CHART_H = PIC_RECT[3] - 0.09

# ── 7. Figura ─────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(SW, SH), facecolor="#101820")
fig.patch.set_facecolor("#101820")

# Capa 0: foto del edificio
ax_bg = fig.add_axes([0, 0, 1, 1], zorder=0)
ax_bg.imshow(bg_arr, extent=[0, 1, 0, 1], aspect="auto", origin="upper")
ax_bg.set_xlim(0, 1); ax_bg.set_ylim(0, 1)
ax_bg.axis("off")

# Capa 1: gradiente navy (replica el overlay del template)
ax_gd = fig.add_axes([0, 0, 1, 1], zorder=1)
ax_gd.imshow(grad, extent=[0, 1, 0, 1], aspect="auto", origin="upper")
ax_gd.set_xlim(0, 1); ax_gd.set_ylim(0, 1)
ax_gd.axis("off")

# ── 8. Título — centrado entre borde superior y zona del gráfico ─────────────
_title_y = (1.0 + CHART_Y + CHART_H + 0.020) / 2 + 0.018   # centrado en su espacio
fig.text(T_RECT[0] + T_RECT[2] / 2, _title_y,
         "Distribución por Unidad/Facultad",
         ha="center", va="center", fontsize=20, fontweight="bold",
         color="white", transform=fig.transFigure, zorder=4)

# ── 9. Logo UCEN — esquina superior derecha ───────────────────────────────────
ax_logo = fig.add_axes(
    [LOGO_RECT[0], LOGO_RECT[1], LOGO_RECT[2], LOGO_RECT[3]],
    zorder=10, facecolor="none")
ax_logo.imshow(logo_arr, aspect="auto")
ax_logo.axis("off")
ax_logo.patch.set_visible(False)

# ── 10. Etiqueta de población ─────────────────────────────────────────────────
fig.text(PIC_RECT[0], POP_Y,
         "Universo: 197 Aptos P3  ·  130 formados + 67 control"
         "  ·  SAT disponible baseline / durante / resultado",
         ha="left", va="center", fontsize=7.5, fontstyle="italic",
         color="#C8DCF0", transform=fig.transFigure, zorder=4)

# ── 11. Gráfico ───────────────────────────────────────────────────────────────
ax = fig.add_axes([CHART_X, CHART_Y, CHART_W, CHART_H],
                  facecolor="none", zorder=5)
ax.set_facecolor("none")

y = np.arange(len(labels))
ax.barh(y[::-1], vals, color=PALETTE[:len(labels)],
        height=0.58, edgecolor="none", alpha=0.90)

for i, (v, p, c) in enumerate(zip(vals[::-1], pcts[::-1],
                                    PALETTE[:len(labels)][::-1])):
    ax.text(v + max(vals) * 0.015, i, f"{v}  ({p:.1f}%)",
            va="center", ha="left", fontsize=10.5, fontweight="bold", color=c,
            path_effects=[pe.withStroke(linewidth=2.5, foreground="#0A0F18")])

ax.set_yticks(y)
ax.set_yticklabels(labels[::-1], fontsize=10.5, fontweight="bold", color="white")
ax.tick_params(axis="y", length=0, pad=8)
ax.tick_params(axis="x", colors="#AAAAAA", labelsize=9)

# Borde blanco sutil (contorno del área del gráfico)
for sp_name, sp in ax.spines.items():
    sp.set_visible(True)
    sp.set_edgecolor("white")
    sp.set_alpha(0.35)
    sp.set_linewidth(0.9)

ax.set_xlim(0, max(vals) * 1.35)
ax.set_ylim(-0.5, len(labels) - 0.5)
ax.xaxis.grid(True, color="white", alpha=0.07, linewidth=0.5, zorder=0)
ax.set_axisbelow(True)

# Título del gráfico — una línea en blanco, encima del chart
fig.text(CHART_X - 0.005, CHART_Y + CHART_H + 0.008,
         f"Distribucion por Unidad/Facultad  —  197 Aptos P3  (n={n_fac} con dato)",
         ha="left", va="bottom", fontsize=10, color="white",
         transform=fig.transFigure, zorder=7)

# ── 12. Bullets — ancho completo (de BUL_L hasta el borde derecho del área) ──
bul_right = BUL_L + BUL_W   # ~ 0.935 (mismo borde derecho que la imagen)

bullet_lines = [
    "1.  La Facultad de Medicina y Ciencias de la Salud concentra el mayor numero de Aptos P3 (47 doc., 36%), seguida por Derecho y Humanidades (22, 17%) e Ingenieria y Arq. (21, 16%).",
    "2.  Las cinco facultades principales agrupan el 90% de los docentes Aptos P3. La distribucion refleja la mayor concentracion de actividad SAT en salud y derecho.",
    "3.  Vicerrectoria de Investigacion e Innovacion aporta 11 docentes (8%), con un perfil mas orientado a investigacion que a docencia de pregrado.",
]

# Axes acotado exactamente entre PIC_L (izq) y CHART_X+CHART_W (der)
# clip_on=True recorta el texto en el borde derecho del gráfico
BUL_BOTTOM  = 1 - BUL_T - BUL_H
BUL_AX_W    = CHART_X + CHART_W - PIC_L
ax_bul = fig.add_axes([PIC_L, BUL_BOTTOM, BUL_AX_W, BUL_H],
                      facecolor="none", zorder=6)
ax_bul.set_xlim(0, 1); ax_bul.set_ylim(0, 1)
ax_bul.axis("off"); ax_bul.patch.set_visible(False)

# wrap_w calibrado: ~155 chars llena ~95% del ancho sin cortar palabras
WRAP_W    = 130
line_h_ax = 0.023 / BUL_H   # altura de línea a 11.5pt en coords del axes
gap_ax    = 0.012 / BUL_H   # espacio extra entre bullets
cur_y_ax  = 1.0 - (0.040 / BUL_H)

for text in bullet_lines:
    # primera línea incluye el número; continuaciones van con indent
    wrapped = textwrap.wrap(text, width=WRAP_W,
                            subsequent_indent="    ")
    for line in wrapped:
        ax_bul.text(0.0, cur_y_ax, line,
                    ha="left", va="top",
                    fontsize=11.5, color="white",
                    transform=ax_bul.transAxes,
                    clip_on=True)
        cur_y_ax -= line_h_ax
    cur_y_ax -= gap_ax

# ── 13. Exportar ──────────────────────────────────────────────────────────────
plt.savefig(OUT_PDF, format="pdf", dpi=150, facecolor=fig.get_facecolor())
plt.savefig(OUT_PNG, format="png", dpi=150, facecolor=fig.get_facecolor())
plt.close()
print(f"\n✓ PDF: {OUT_PDF}")
print(f"✓ PNG: {OUT_PNG}")
