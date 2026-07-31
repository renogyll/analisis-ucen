# -*- coding: utf-8 -*-
"""
generar_ficha_p1_p2.py
Genera FICHA_P1_P2_v2.pptx en formato dark v3.

P1 = Caracterización del Cuerpo Académico de PLANTA (Jornada, 2026-01)
P2 = Participación en Formación Docente (universo completo 1.144)

  Slide 1 - Portada
  Slide 2 - Cascada P1: 1.144 base -> 624 Jornada -> 534 con Dotación
  Slide 3 - Jornada sin Dotación: los 90 sin perfil completo
  Slide 4 - Sub-cascadas dentro de los 534 (brechas menores)
  Slide 5 - Cascada P2: 1.144 -> 726 formados -> 2.190 iniciativas
  Slide 6 - Solicitudes de datos para completar P1 y P2
"""
import sys; sys.stdout.reconfigure(encoding="utf-8")
import os, zipfile
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import pandas as pd
from PIL import Image as PILImage
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

# ─────────────────────────────────────────────────────────────────────────────
# Rutas
# ─────────────────────────────────────────────────────────────────────────────
BASE      = os.path.dirname(os.path.abspath(__file__))
REPO      = os.path.normpath(os.path.join(BASE, "..", "..", "..", ".."))  # analisis-ucen/
DOWNLOADS = os.path.dirname(REPO)                                   # Downloads/
CASCADE   = os.path.join(REPO, "data", "cascade")
FONDOTIPO = os.path.join(REPO, "assets", "Fondotipop.pptx")
OUT_DIR   = os.path.join(BASE, "dark_slides_v3")
OUT_PPTX  = os.path.join(DOWNLOADS, "FICHA_P1_P2_v2.pptx")
os.makedirs(OUT_DIR, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# Datos
# ─────────────────────────────────────────────────────────────────────────────
CORTE = datetime(2026, 1, 1)

# P1: Jornada (Planta)
doc = pd.read_csv(
    os.path.join(CASCADE, "01_jornada", "docentes_jornada.csv"),
    encoding="utf-8-sig"
)

# P2: Formados P3 (una fila por iniciativa)
p2 = pd.read_csv(
    os.path.join(CASCADE, "04_formados_p3", "docentes_formados.csv"),
    encoding="utf-8-sig"
)

# ── Universo base (contexto) ────────────────────────────────────────────────
N_BASE   = 1144     # universo total: Jornada + Honorario

# ── P1 cascade ──────────────────────────────────────────────────────────────
N_JORNADA  = len(doc)                                    # 624 Jornada (Planta)
N_DOTACION = int(doc["fecha_ingreso"].notna().sum())     # 534 con dotación
N_SIN_DOT  = N_JORNADA - N_DOTACION                     # 90 solo NOMINA

# Sub-cascadas dentro de los 534 con dotación
_con = doc[doc["fecha_ingreso"].notna()]
N_CON_SEXO     = int(_con["sexo"].notna().sum())              # 513
N_CON_EDAD     = int(_con["edad_anios"].notna().sum())        # 534
N_CON_FACULTAD = int(_con["unidad_facultad"].notna().sum())   # 534
N_CON_NIVELFORM= int(_con["nivel_formacion"].notna().sum())   # 534
N_CON_JRQDATE  = int(_con["fecha_jerarquizacion"].notna().sum())  # 485
N_CON_CARGA    = int(_con["jornada_dot"].notna().sum())       # 534
N_CON_JER      = int(doc["jerarquia"].notna().sum())          # 603 (todos)

SUBCASC = [
    (N_DOTACION, "Con dotación completa",        "Edad · Facultad · Nivel Formación · Jerarquía · Carga"),
    (N_CON_SEXO, "Con sexo registrado",          "Perfil Sociodemográfico — Distribución por Género"),
    (N_CON_JRQDATE, "Con fecha jerarquización",  "Trayectoria Académica — Años hasta Jerarquización"),
]

# ── P2 cascade ──────────────────────────────────────────────────────────────
N_FORMADOS    = p2["rut_key"].nunique()   # 726 docentes únicos
N_INICIATIVAS = len(p2)                   # 2190 filas = iniciativas
N_TALL  = int((p2["tipo_formacion"] == "TALLER").sum())     # 1906
N_DIP   = int((p2["tipo_formacion"] == "DIPLOMADO").sum())  # 242
N_PROY  = int((p2["tipo_formacion"] == "PROYECTO").sum())   # 42
N_SIN_FORM = N_BASE - N_FORMADOS          # 418 sin formación en el universo base

F_DOC = "Nomina_Dotacion_2026-01.xlsx"

print(f"P1 Jornada: {N_JORNADA} total | {N_DOTACION} con dotación | {N_SIN_DOT} solo NOMINA")
print(f"  Sub: sexo={N_CON_SEXO}  facultad={N_CON_FACULTAD}  nivelform={N_CON_NIVELFORM}  jer.date={N_CON_JRQDATE}")
print(f"P2: {N_FORMADOS} formados | {N_INICIATIVAS} iniciativas | Tall={N_TALL} Dip={N_DIP} Proy={N_PROY}")

# ─────────────────────────────────────────────────────────────────────────────
# Assets
# ─────────────────────────────────────────────────────────────────────────────
BG_PATH   = os.path.join(OUT_DIR, "_fondotipo_bg.jpg")
LOGO_PATH = os.path.join(OUT_DIR, "_fondotipo_logo.png")
for path, zname in [(BG_PATH, "ppt/media/image1.jpg"),
                    (LOGO_PATH, "ppt/media/image2.png")]:
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
    _stops = [(0.00, (0, 33, 71)), (0.54, (0, 70, 128)), (1.00, (144, 171, 196))]
    for _i in range(len(_stops) - 1):
        _t0, _c0 = _stops[_i]; _t1, _c1 = _stops[_i + 1]
        if _t0 <= _t <= _t1:
            _s = (_t - _t0) / (_t1 - _t0)
            grad[_r, 0] = [(_c0[0]+_s*(_c1[0]-_c0[0]))/255,
                           (_c0[1]+_s*(_c1[1]-_c0[1]))/255,
                           (_c0[2]+_s*(_c1[2]-_c0[2]))/255, 0.82]; break

# ─────────────────────────────────────────────────────────────────────────────
# Layout constants
# ─────────────────────────────────────────────────────────────────────────────
SW, SH         = 13.333, 7.5
SW_EMU, SH_EMU = 12192000, 6858000
PIC_L, PIC_T, PIC_W, PIC_H         = 786581, 1125000, 10599174, 3720000
BUL_L, BUL_T, BUL_W, BUL_H         = 786581, 4870000, 10599174, 1870000
LOGO_L, LOGO_T, LOGO_W, LOGO_H     = 9813773, 656354, 1756626, 697725
TITLE_L, TITLE_T, TITLE_W, TITLE_H = PIC_L, 185000, PIC_W, 710000
POP_L,   POP_T,   POP_W,   POP_H   = PIC_L, 845000, 9000000, 255000

def _ex(e): return e / SW_EMU
def _ey(e): return e / SH_EMU
def _fig_rect(l, t, w, h): return (l, 1-t-h, w, h)
PIC_RECT  = _fig_rect(_ex(PIC_L), _ey(PIC_T), _ex(PIC_W), _ey(PIC_H))
LOGO_RECT = _fig_rect(_ex(LOGO_L), _ey(LOGO_T), _ex(LOGO_W), _ey(LOGO_H))

# ─────────────────────────────────────────────────────────────────────────────
# Helpers matplotlib
# ─────────────────────────────────────────────────────────────────────────────
def _bg_fig():
    fig = plt.figure(figsize=(SW, SH), facecolor="#101820")
    fig.patch.set_facecolor("#101820")
    for z, arr in [(0, bg_arr), (1, grad)]:
        ax = fig.add_axes([0, 0, 1, 1], zorder=z)
        ax.imshow(arr, extent=[0, 1, 0, 1], aspect="auto", origin="upper")
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    al = fig.add_axes([LOGO_RECT[0], LOGO_RECT[1], LOGO_RECT[2], LOGO_RECT[3]],
                      zorder=10, facecolor="none")
    al.imshow(logo_arr, aspect="auto"); al.axis("off"); al.patch.set_visible(False)
    return fig

def _tr_fig():
    fig = plt.figure(figsize=(SW, SH), facecolor="none")
    fig.patch.set_facecolor("none"); return fig

SHARED_BG = os.path.join(OUT_DIR, "_background.png")

def _ensure_bg():
    if not os.path.exists(SHARED_BG):
        fig = _bg_fig()
        plt.savefig(SHARED_BG, dpi=150, facecolor=fig.get_facecolor()); plt.close()
        print("  bg generado")

def _save_ch(fig, name):
    path = os.path.join(OUT_DIR, name)
    plt.savefig(path, dpi=150, facecolor="none", transparent=True)
    plt.close(); return path

# ─────────────────────────────────────────────────────────────────────────────
# Helpers python-pptx
# ─────────────────────────────────────────────────────────────────────────────
def _new_sl(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])

def _pic(sl, path, prs):
    sl.shapes.add_picture(path, Emu(0), Emu(0), prs.slide_width, prs.slide_height)

def _txt(sl, text, left, top, width, height,
         fs=12, bold=False, italic=False, color="#FFFFFF",
         align=PP_ALIGN.LEFT, wrap=True, lspc=0):
    txb = sl.shapes.add_textbox(Emu(left), Emu(top), Emu(width), Emu(height))
    tf  = txb.text_frame; tf.word_wrap = wrap
    for i, line in enumerate(str(text).split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        if lspc > 0 and i > 0: p.space_before = Pt(lspc)
        run = p.add_run(); run.text = line
        run.font.size = Pt(fs); run.font.bold = bold; run.font.italic = italic
        r, g, b = int(color[1:3],16), int(color[3:5],16), int(color[5:7],16)
        run.font.color.rgb = RGBColor(r, g, b)

def _T(sl, text, fs=20):
    _txt(sl, text, TITLE_L, TITLE_T, TITLE_W, TITLE_H,
         fs=fs, bold=True, color="#FFFFFF", align=PP_ALIGN.CENTER)

def _POP(sl, text):
    _txt(sl, text, POP_L, POP_T, POP_W, POP_H,
         fs=7.5, italic=True, color="#C8DCF0")

def _BUL(sl, items, fs=11.5):
    txb = sl.shapes.add_textbox(Emu(BUL_L), Emu(BUL_T), Emu(BUL_W), Emu(BUL_H))
    tf  = txb.text_frame; tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(4); p.alignment = PP_ALIGN.LEFT
        run = p.add_run(); run.text = "•  " + item
        run.font.size = Pt(fs)
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)


# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 1 — Portada
# ─────────────────────────────────────────────────────────────────────────────
def slide_portada(prs):
    sl = _new_sl(prs)
    _pic(sl, SHARED_BG, prs)
    _txt(sl, "Ficha Técnica", TITLE_L, 1_700_000, TITLE_W, 600_000,
         fs=30, bold=True, color="#FFFFFF", align=PP_ALIGN.CENTER)
    _txt(sl, "P1 — Cuerpo Académico de Planta  ·  P2 — Formación Docente",
         TITLE_L, 2_350_000, TITLE_W, 700_000,
         fs=22, bold=True, color="#7EC8E3", align=PP_ALIGN.CENTER)
    _txt(sl, "Cascadas de datos · cobertura del perfil · brechas menores · solicitudes de completitud",
         TITLE_L, 3_150_000, TITLE_W, 500_000,
         fs=12, italic=True, color="#C8DCF0", align=PP_ALIGN.CENTER)
    _txt(sl,
         f"P1 — Planta 2026-01: {N_JORNADA} docentes Jornada  →  {N_DOTACION} con perfil completo"
         f"  |  {N_SIN_DOT} sin dotación",
         TITLE_L, 3_850_000, TITLE_W, 380_000,
         fs=11.5, color="#FFD580", align=PP_ALIGN.CENTER)
    _txt(sl,
         f"P2 — Formación: {N_FORMADOS} formados de {N_BASE} universo base"
         f"  ({N_INICIATIVAS} iniciativas: {N_TALL} Talleres · {N_DIP} Diplomados · {N_PROY} Proyectos)",
         TITLE_L, 4_300_000, TITLE_W, 380_000,
         fs=11.5, color="#A8E8A0", align=PP_ALIGN.CENTER)
    _txt(sl,
         f"Universo base: {N_BASE} docentes UCEN (Jornada + Honorario)  |  Corte: 2026-01",
         TITLE_L, 4_800_000, TITLE_W, 350_000,
         fs=9.5, italic=True, color="#A0B8D0", align=PP_ALIGN.CENTER)
    print("  slide 1 - Portada OK")


# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 2 — Cascada P1: 1.144 -> 624 Jornada -> 534 con Dotación
# ─────────────────────────────────────────────────────────────────────────────
def slide_cascada_p1(prs):
    fig = _tr_fig()
    gx = PIC_RECT[0] + 0.01
    gy = PIC_RECT[1] + 0.00
    gw = PIC_RECT[2] - 0.02
    gh = PIC_RECT[3] - 0.01
    ax = fig.add_axes([gx, gy, gw, gh], facecolor="none", zorder=5)
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")

    def _box(ax, x0, y0, w, h, n, label, sub, col, fs_n=22):
        rect = mpatches.FancyBboxPatch((x0, y0), w, h,
                                        boxstyle="round,pad=0.10",
                                        facecolor=col, edgecolor="white",
                                        linewidth=0.8, alpha=0.90, zorder=3)
        ax.add_patch(rect)
        ax.text(x0 + 0.60, y0 + h*0.62, str(n),
                ha="center", va="center", fontsize=fs_n, fontweight="bold",
                color="white", zorder=5,
                path_effects=[pe.withStroke(linewidth=3, foreground="#050D1A")])
        ax.text(x0 + 1.35, y0 + h*0.67, label,
                ha="left", va="center", fontsize=9.5, fontweight="bold",
                color="white", zorder=5)
        ax.text(x0 + 1.35, y0 + h*0.28, sub,
                ha="left", va="center", fontsize=7.8, color="#B8D0E8", zorder=5)

    def _arrow(ax, x, y_from, y_to, lbl, col="#FFD580"):
        mid = (y_from + y_to) / 2
        ax.annotate("", xy=(x, y_to + 0.05), xytext=(x, y_from - 0.05),
                    arrowprops=dict(arrowstyle="->", color=col, lw=1.4,
                                   mutation_scale=16), zorder=6)
        ax.text(x - 0.10, mid, lbl, ha="right", va="center",
                fontsize=7.5, color=col, fontstyle="italic", zorder=5)

    BW, BH = 3.70, 1.35
    BX = 0.20

    # Nodo 1: universo base
    _box(ax, BX, 8.40, BW, BH, f"{N_BASE:,}".replace(",", "."),
         "docentes UCEN (universo base)",
         "Jornada + Honorario  |  Corte: 2026-01", "#1B4E8F")

    # Nodo 2: Jornada (P1 = Planta)
    _box(ax, BX, 6.60, BW, BH, str(N_JORNADA),
         "docentes de Jornada (Planta)",
         f"P1 — Cuerpo Académico de Planta  |  {N_BASE - N_JORNADA} Honorarios excluidos", "#2E6AAD")

    # Nodo 3: con Dotación
    _box(ax, BX, 4.50, BW, BH, str(N_DOTACION),
         "con perfil completo (Dotación)",
         "Edad · Facultad · Nivel Formación · Carga · Jerarquía", "#1B7A4A", fs_n=22)

    _arrow(ax, BX + BW/2 - 0.2, 8.40, 6.60 + BH,
           f"{N_JORNADA} de {N_BASE}")
    _arrow(ax, BX + BW/2 - 0.2, 6.60, 4.50 + BH,
           f"−{N_SIN_DOT} sin dotación", col="#E05A3A")

    # Etiqueta del drop
    ax.text(BX + BW/2 - 0.2 - 0.15, 5.85,
            f"  {N_SIN_DOT} SOLO EN NÓMINA  ",
            ha="right", va="center", fontsize=8.0, fontweight="bold",
            color="#E05A3A", zorder=5,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#2A0808",
                      edgecolor="#E05A3A", alpha=0.85))

    # Sub-cascadas (columna derecha) — rama de los 534
    midbox = 4.50 + BH / 2
    ax.plot([BX + BW, BX + BW + 0.45], [midbox, midbox],
            "-", color="white", linewidth=0.7, alpha=0.45, zorder=4)
    ax.plot([BX + BW + 0.45, BX + BW + 0.45], [midbox, 7.40],
            "-", color="white", linewidth=0.7, alpha=0.45, zorder=4)

    sx0 = BX + BW + 0.55
    sub_ys = [7.40, 5.90, 4.40]
    sub_colors = ["#1B7A4A", "#27824A", "#348A52"]

    for (n, lbl, analisis), y, col in zip(SUBCASC, sub_ys, sub_colors):
        sh = 1.05
        srect = mpatches.FancyBboxPatch(
            (sx0, y - sh/2), 5.85, sh,
            boxstyle="round,pad=0.07",
            facecolor=col, edgecolor="white",
            linewidth=0.5, alpha=0.82, zorder=3)
        ax.add_patch(srect)
        ax.text(sx0 + 0.55, y + 0.08, str(n),
                ha="center", va="center", fontsize=16, fontweight="bold",
                color="white", zorder=5,
                path_effects=[pe.withStroke(linewidth=2.5, foreground="#050D1A")])
        ax.text(sx0 + 1.10, y + 0.20, lbl,
                ha="left", va="center", fontsize=8.5, fontweight="bold",
                color="white", zorder=5)
        ax.text(sx0 + 1.10, y - 0.22, f"→ {analisis}",
                ha="left", va="center", fontsize=7.5,
                color="#C8E8C8", zorder=5)
        ax.plot([BX + BW + 0.45, sx0 - 0.02], [y, y],
                "-", color="white", linewidth=0.5, alpha=0.35, zorder=4)

    path = _save_ch(fig, "ficha_p1_cascada.png")

    sl = _new_sl(prs)
    _pic(sl, SHARED_BG, prs)
    _pic(sl, path, prs)
    _T(sl, f"P1 — Cascada de Datos: de {N_BASE:,} a {N_JORNADA} Jornada y {N_DOTACION} con Perfil Completo".replace(",", "."), fs=13)
    _POP(sl, f"P1 = Cuerpo Académico de Planta (Jornada 2026-01)  |  "
             f"Universo base: {N_BASE} (Jornada + Honorario)  |  "
             f"Sub-cascadas dentro de los {N_DOTACION} con Dotación")
    _BUL(sl, [
        f"P1 se acota a los {N_JORNADA} docentes de Jornada (Planta), según TdR. "
        f"Los {N_BASE - N_JORNADA} Honorarios no forman parte del universo de análisis de P1.",
        f"El salto crítico dentro de los {N_JORNADA} Jornada es a {N_DOTACION}: "
        f"los {N_SIN_DOT} sin dotación están en NÓMINA pero no en la hoja DOTACIÓN, "
        f"por lo que carecen de edad, antigüedad, facultad, nivel de formación y carga horaria.",
    ])
    print("  slide 2 - Cascada P1 OK")


# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 3 — Jornada sin Dotación: los 90 sin perfil completo
# ─────────────────────────────────────────────────────────────────────────────
def slide_jornada_sin_dotacion(prs):
    fig = _tr_fig()
    gx = PIC_RECT[0] + 0.01
    gy = PIC_RECT[1] + 0.00
    gw = PIC_RECT[2] - 0.02
    gh = PIC_RECT[3] - 0.01
    ax = fig.add_axes([gx, gy, gw, gh], facecolor="none", zorder=5)
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")

    def _panel(ax, x0, y0, w, h, n, title, col, items_ok, items_no=None):
        rect = mpatches.FancyBboxPatch((x0, y0), w, h,
                                        boxstyle="round,pad=0.12",
                                        facecolor=col, edgecolor="white",
                                        linewidth=0.8, alpha=0.28, zorder=2)
        ax.add_patch(rect)
        bar = mpatches.FancyBboxPatch(
            (x0, y0 + h - 0.62), w, 0.62,
            boxstyle="round,pad=0.05",
            facecolor=col, edgecolor="none", alpha=0.88, zorder=3)
        ax.add_patch(bar)
        ax.text(x0 + w/2, y0 + h - 0.31, f"{n}  {title}",
                ha="center", va="center", fontsize=11, fontweight="bold",
                color="white", zorder=5)
        y_item = y0 + h - 0.90
        for it in items_ok:
            ax.text(x0 + 0.25, y_item, it,
                    ha="left", va="top", fontsize=8.0, color="white",
                    zorder=5, linespacing=1.35)
            y_item -= 0.60
        if items_no:
            ax.text(x0 + 0.25, y_item - 0.10, "NO disponible:",
                    ha="left", va="top", fontsize=8.0, color="#E08080",
                    fontweight="bold", zorder=5)
            y_item -= 0.52
            for it in items_no:
                ax.text(x0 + 0.25, y_item, it,
                        ha="left", va="top", fontsize=8.0, color="#E08080",
                        zorder=5)
                y_item -= 0.55

    ok_vars_dot = [
        "[OK]  Sexo (de NÓMINA)",
        "[OK]  Jerarquía académica",
        "[OK]  Tipo contrato = Jornada",
        "[OK]  Edad / fecha nacimiento",
        "[OK]  Antigüedad / fecha ingreso",
        "[OK]  Unidad / Facultad",
        "[OK]  Nivel formación (grado)",
        "[OK]  Institución y país del grado",
        "[OK]  Carga horaria (jornada hrs)",
        "[OK]  Cargo específico",
    ]
    ok_vars_nom = [
        "[OK]  Tipo contrato = Jornada",
        "[OK]  Jerarquía académica (aprox.)",
        "[OK]  Función principal académica",
        "[OK]  Fecha jerarquización (parcial)",
    ]
    no_vars_nom = [
        "[---]  Edad / fecha nacimiento",
        "[---]  Antigüedad / fecha ingreso",
        "[---]  Unidad / Facultad detallada",
        "[---]  Nivel de formación",
        "[---]  Nombre y país del grado",
        "[---]  Carga horaria (horas semanales)",
        "[---]  Cargo específico",
    ]

    _panel(ax, 0.10, 0.30, 4.15, 9.35,
           N_DOTACION, "docentes Jornada con DOTACIÓN",
           "#1B7A4A", ok_vars_dot)

    ax.axvline(4.60, ymin=0.03, ymax=0.97,
               color="white", linewidth=0.6, alpha=0.30, zorder=4)

    _panel(ax, 4.80, 0.30, 4.85, 9.35,
           N_SIN_DOT, "docentes Jornada SOLO en NÓMINA",
           "#8B2020", ok_vars_nom, no_vars_nom)

    ax.text(4.83, 0.12,
            f"Jornada sin cruce en DOTACIÓN — posible causa: ingreso posterior al corte del archivo",
            ha="left", va="center", fontsize=8.0, color="#E08080",
            fontstyle="italic", zorder=5)

    path = _save_ch(fig, "ficha_p1_sin_dotacion.png")

    sl = _new_sl(prs)
    _pic(sl, SHARED_BG, prs)
    _pic(sl, path, prs)
    _T(sl, f"Jornada sin Dotación — {N_SIN_DOT} Docentes de Planta sin Perfil Completo", fs=14)
    _POP(sl,
         f"NÓMINA 2026-01: {N_JORNADA} Jornada  |  "
         f"DOTACIÓN: {N_DOTACION} con perfil completo  |  "
         f"Gap: {N_SIN_DOT} Jornada sin cruce en DOTACIÓN")
    _BUL(sl, [
        f"Los {N_SIN_DOT} docentes de Jornada sin dotación tienen contrato de planta "
        f"y jerarquía académica asignada, pero carecen de los datos de perfil "
        f"(edad, antigüedad, facultad, grado, carga horaria). "
        f"La causa más probable es ingreso posterior al corte del archivo DOTACIÓN.",
        f"Para P1 se trabaja con los {N_DOTACION} que sí tienen perfil completo, "
        f"que representan el {100*N_DOTACION/N_JORNADA:.0f}% del cuerpo de planta. "
        f"Solicitar dotación actualizada recuperaría estos {N_SIN_DOT} casos.",
    ])
    print("  slide 3 - Jornada sin Dotación OK")


# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 4 — Sub-cascadas dentro de los 534
# ─────────────────────────────────────────────────────────────────────────────
def slide_subcascadas(prs):
    fig = _tr_fig()
    gx = PIC_RECT[0] + 0.04
    gy = PIC_RECT[1] + 0.02
    gw = PIC_RECT[2] * 0.72
    gh = PIC_RECT[3] - 0.04
    ax = fig.add_axes([gx, gy, gw, gh], facecolor="none", zorder=5)

    ns     = [sc[0] for sc in SUBCASC]
    labels = [sc[1] for sc in SUBCASC]
    anals  = [sc[2] for sc in SUBCASC]
    cols   = ["#1B7A4A", "#27924A", "#348A52"]

    bars = ax.barh(range(len(ns)), ns, color=cols, alpha=0.88,
                   edgecolor="white", linewidth=0.6, height=0.50, zorder=3)

    x_min = min(ns) - 30
    x_max = max(ns) + 40
    ax.set_xlim(x_min, x_max)

    for bar, n, lbl, ana, col in zip(bars, ns, labels, anals, cols):
        ax.text(n + 3, bar.get_y() + bar.get_height()/2,
                str(n), va="center", ha="left", fontsize=16, fontweight="bold",
                color="white",
                path_effects=[pe.withStroke(linewidth=2, foreground="#050D1A")])
        diff = N_DOTACION - n
        if diff > 0:
            ax.text(n - 5, bar.get_y() + bar.get_height()/2,
                    f"−{diff}", va="center", ha="right", fontsize=9,
                    color="#FFD580", fontweight="bold",
                    path_effects=[pe.withStroke(linewidth=1.5, foreground="#050D1A")])

    ax.set_xlabel(f"Nº docentes disponibles (base: {N_DOTACION} con dotación)", color="#AAAAAA", fontsize=9)
    ax.set_yticks(range(len(ns)))
    ax.set_yticklabels(labels, fontsize=9.5, color="white")
    ax.tick_params(axis="x", colors="#AAAAAA", labelsize=8.5)
    for sp in ax.spines.values():
        sp.set_edgecolor("white"); sp.set_alpha(0.25); sp.set_linewidth(0.7)
    ax.xaxis.grid(True, color="white", alpha=0.08, linewidth=0.5)
    ax.set_axisbelow(True)

    ax2 = fig.add_axes([gx + gw + 0.018, gy + gh*0.04, 0.20, gh*0.93],
                       facecolor="none", zorder=5)
    ax2.axis("off")
    ax2.text(0.0, 1.0, "ANÁLISIS HABILITADO",
             transform=ax2.transAxes, va="top", ha="left",
             fontsize=9.5, fontweight="bold", color="#FFD580", zorder=5)
    ax2.text(0.0, 0.92, "(por sub-nivel de completitud)",
             transform=ax2.transAxes, va="top", ha="left",
             fontsize=7.5, color="#A0B8D0", fontstyle="italic", zorder=5)

    y_pos = 0.75
    for n, lbl, ana, col in zip(ns, labels, anals, cols):
        circ = mpatches.Circle((0.05, y_pos), 0.04,
                                facecolor=col, edgecolor="white",
                                linewidth=0.5, alpha=0.85,
                                transform=ax2.transAxes, zorder=3)
        ax2.add_patch(circ)
        ax2.text(0.14, y_pos, ana,
                 transform=ax2.transAxes, va="center", ha="left",
                 fontsize=7.8, color="white", zorder=5)
        y_pos -= 0.22

    ax2.text(0.0, 0.10,
             "Causas de los drops:\n"
             f"- {N_DOTACION - N_CON_SEXO} sin sexo registrado en NÓMINA\n"
             f"- {N_DOTACION - N_CON_JRQDATE} sin fecha de jerarquización\n"
             "  (necesaria para años hasta jerarquización)\n"
             "- Resto: perfil 100% completo",
             transform=ax2.transAxes, va="bottom", ha="left",
             fontsize=7.5, color="#E8A080", zorder=5, linespacing=1.4)

    path = _save_ch(fig, "ficha_p1_subcascadas.png")

    sl = _new_sl(prs)
    _pic(sl, SHARED_BG, prs)
    _pic(sl, path, prs)
    _T(sl, f"P1 — Sub-Cascadas Dentro de los {N_DOTACION} con Dotación Completa", fs=15)
    _POP(sl, f"Base: {N_DOTACION} docentes Jornada con dotación completa  |  "
             f"Brechas menores dentro del grupo — {N_DOTACION - N_CON_SEXO} sin sexo, "
             f"{N_DOTACION - N_CON_JRQDATE} sin fecha jerarquización")
    _BUL(sl, [
        f"La mayoría de los {N_DOTACION} con dotación tiene perfil completo. "
        f"La mayor sub-caída es de {N_DOTACION} a {N_CON_JRQDATE} (−{N_DOTACION - N_CON_JRQDATE} sin "
        f"fecha de jerarquización), imprescindible para calcular 'Años hasta jerarquización' "
        f"y analizar trayectoria académica.",
        f"Los {N_DOTACION - N_CON_SEXO} sin sexo registrado corresponden a docentes en la "
        f"hoja NÓMINA sin ese campo completado. Para perfil sociodemográfico, se trabaja "
        f"con los {N_CON_SEXO} que sí tienen el dato ({100*N_CON_SEXO/N_DOTACION:.0f}% de cobertura).",
    ])
    print("  slide 4 - Sub-cascadas OK")


# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 5 — Cascada P2: 1.144 -> 726 formados -> 2.190 iniciativas
# ─────────────────────────────────────────────────────────────────────────────
def slide_cascada_p2(prs):
    fig = _tr_fig()
    gx = PIC_RECT[0] + 0.02
    gy = PIC_RECT[1] + 0.00
    gw = PIC_RECT[2] - 0.04
    gh = PIC_RECT[3] - 0.01
    ax = fig.add_axes([gx, gy, gw, gh], facecolor="none", zorder=5)
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")

    BW, BH, BX = 3.70, 1.45, 0.20

    def _box(ax, x0, y0, n, label, sub, col, fs_n=22):
        rect = mpatches.FancyBboxPatch((x0, y0), BW, BH,
                                        boxstyle="round,pad=0.10",
                                        facecolor=col, edgecolor="white",
                                        linewidth=0.8, alpha=0.90, zorder=3)
        ax.add_patch(rect)
        ax.text(x0 + 0.60, y0 + BH*0.62, str(n),
                ha="center", va="center", fontsize=fs_n, fontweight="bold",
                color="white", zorder=5,
                path_effects=[pe.withStroke(linewidth=3, foreground="#050D1A")])
        ax.text(x0 + 1.35, y0 + BH*0.68, label,
                ha="left", va="center", fontsize=9.5, fontweight="bold",
                color="white", zorder=5)
        ax.text(x0 + 1.35, y0 + BH*0.22, sub,
                ha="left", va="center", fontsize=7.8, color="#B8D0E8", zorder=5)

    def _arrow(ax, x, y_from, y_to, lbl, col="#FFD580"):
        mid = (y_from + y_to) / 2
        ax.annotate("", xy=(x, y_to + 0.05), xytext=(x, y_from - 0.05),
                    arrowprops=dict(arrowstyle="->", color=col, lw=1.4,
                                   mutation_scale=16), zorder=6)
        ax.text(x - 0.10, mid, lbl, ha="right", va="center",
                fontsize=7.5, color=col, fontstyle="italic", zorder=5)

    _box(ax, BX, 8.20, f"{N_BASE:,}".replace(",", "."),
         "docentes UCEN (universo base)",
         "Jornada + Honorario  |  Corte: 2026-01", "#1B4E8F", fs_n=18)

    # 418 sin formación (burbuja a la derecha)
    bub_x, bub_y = BX + BW + 0.60, 7.90
    bub = mpatches.FancyBboxPatch((bub_x, bub_y), 5.10, 1.30,
                                   boxstyle="round,pad=0.10",
                                   facecolor="#5A2020", edgecolor="#E05A3A",
                                   linewidth=0.8, alpha=0.75, zorder=3)
    ax.add_patch(bub)
    ax.text(bub_x + 0.55, bub_y + 0.65, str(N_SIN_FORM),
            ha="center", va="center", fontsize=20, fontweight="bold",
            color="white", zorder=5,
            path_effects=[pe.withStroke(linewidth=2.5, foreground="#050D1A")])
    ax.text(bub_x + 1.25, bub_y + 0.82, "sin formación registrada",
            ha="left", va="center", fontsize=9, fontweight="bold",
            color="white", zorder=5)
    ax.text(bub_x + 1.25, bub_y + 0.40, "Brecha de cobertura, no de datos",
            ha="left", va="center", fontsize=7.8,
            color="#E08080", fontstyle="italic", zorder=5)
    ax.text(bub_x + 1.25, bub_y + 0.10,
            f"({100*N_SIN_FORM/N_BASE:.0f}% del universo base no ha participado en P3)",
            ha="left", va="center", fontsize=7.5, color="#B8D0E8", zorder=5)
    ax.annotate("", xy=(bub_x - 0.02, bub_y + 0.65),
                xytext=(BX + BW + 0.05, 8.20 + BH*0.44),
                arrowprops=dict(arrowstyle="->", color="#E05A3A", lw=1.2,
                                connectionstyle="arc3,rad=0.0"), zorder=6)

    _box(ax, BX, 5.95, str(N_FORMADOS),
         "docentes formados (≥1 iniciativa P3)",
         "Talleres · Diplomados · Proyectos  |  2022–2025", "#2E6AAD")

    _arrow(ax, BX + BW/2 - 0.2, 8.20, 5.95 + BH,
           f"{N_FORMADOS} de {N_BASE}  ({100*N_FORMADOS/N_BASE:.0f}%)")

    _box(ax, BX, 3.65, str(N_INICIATIVAS),
         "iniciativas de formación (filas totales)",
         f"{N_FORMADOS} docentes únicos (un docente puede tener varias iniciativas)", "#3A8BC4")

    _arrow(ax, BX + BW/2 - 0.2, 5.95, 3.65 + BH, f"{N_INICIATIVAS} registros")

    tipos = [
        (N_TALL, "Talleres",   "#4B9CD3"),
        (N_DIP,  "Diplomados", "#3A7ABF"),
        (N_PROY, "Proyectos",  "#2A5EA0"),
    ]
    ty0 = 3.65
    for n_t, lbl_t, col_t in tipos:
        bx_t = BX + BW + 0.40
        bar_w = (n_t / N_TALL) * 5.0
        brect = mpatches.FancyBboxPatch(
            (bx_t, ty0 + 0.12), bar_w, 0.75,
            boxstyle="round,pad=0.05",
            facecolor=col_t, edgecolor="white",
            linewidth=0.4, alpha=0.85, zorder=3)
        ax.add_patch(brect)
        ax.text(bx_t + bar_w + 0.12, ty0 + 0.50,
                f"{n_t}  {lbl_t}", ha="left", va="center",
                fontsize=9, fontweight="bold", color="white", zorder=5)
        ty0 += 1.00

    path = _save_ch(fig, "ficha_p2_cascada.png")

    sl = _new_sl(prs)
    _pic(sl, SHARED_BG, prs)
    _pic(sl, path, prs)
    _T(sl, f"P2 — Cascada de Formación: {N_BASE} Base → {N_FORMADOS} Formados → {N_INICIATIVAS} Iniciativas", fs=13)
    _POP(sl, f"Fuente: base consolidada 2026-01  |  "
             f"Talleres (2022–2025) · Diplomados · Proyectos  |  "
             f"{N_FORMADOS} docentes únicos en {N_INICIATIVAS} iniciativas P3")
    _BUL(sl, [
        f"De los {N_BASE} docentes del universo base (Jornada + Honorario), "
        f"{N_SIN_FORM} ({100*N_SIN_FORM/N_BASE:.0f}%) no tienen ninguna iniciativa de formación P3. "
        f"Esto es una brecha de cobertura de la política formativa, no un problema de datos.",
        f"Los {N_FORMADOS} formados generan {N_INICIATIVAS} iniciativas en total: "
        f"Talleres ({N_TALL}), Diplomados ({N_DIP}) y Proyectos ({N_PROY}). "
        f"Un mismo docente puede haber participado en varias iniciativas de distinto tipo.",
    ])
    print("  slide 5 - Cascada P2 OK")


# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 6 — Solicitudes de datos para completar P1 y P2
# ─────────────────────────────────────────────────────────────────────────────
def slide_solicitudes(prs):
    fig = _tr_fig()
    gx = PIC_RECT[0] + 0.01
    gy = PIC_RECT[1] + 0.01
    gw = PIC_RECT[2] - 0.02
    gh = PIC_RECT[3] - 0.03
    ax = fig.add_axes([gx, gy, gw, gh], facecolor="none", zorder=5)
    ax.set_xlim(0, 10); ax.set_ylim(0, 10.5); ax.axis("off")

    BOX_H = 2.35
    solicitudes = [
        {
            "num": "1", "col": "#1B6A40",
            "title": f"P1  —  Dotación actualizada para los {N_SIN_DOT} Jornada sin perfil",
            "lines": [
                f"Los {N_SIN_DOT} docentes de Jornada están en NÓMINA pero no en la hoja DOTACIÓN.",
                "Por tanto carecen de:",
                "  edad / fecha nacimiento  |  antigüedad / fecha ingreso  |  unidad / facultad",
                "  nivel de formación  |  nombre y país del grado  |  carga horaria",
                "Solicitar: DOTACIÓN actualizada al corte 2026-01 que los incluya.",
            ],
            "impacto": f"Sube el universo P1 de {N_DOTACION} a {N_JORNADA} docentes ({100*N_SIN_DOT/N_JORNADA:.0f}% de recuperación)",
            "yc": 9.45,
        },
        {
            "num": "2", "col": "#1B4E8F",
            "title": f"P1  —  Sexo faltante para {N_DOTACION - N_CON_SEXO} docentes",
            "lines": [
                f"{N_DOTACION - N_CON_SEXO} docentes dentro de los {N_DOTACION} con dotación no tienen sexo registrado.",
                "Campo presente en la hoja NÓMINA pero vacío para estos casos.",
                "Necesario para: distribución por género (perfil sociodemográfico).",
                "Solicitar: completar campo SEXO en hoja NÓMINA para esos registros.",
            ],
            "impacto": f"Sube de {N_CON_SEXO} a {N_DOTACION} los disponibles para análisis de género",
            "yc": 6.75,
        },
        {
            "num": "3", "col": "#3A5080",
            "title": f"P1  —  Fecha de jerarquización faltante para {N_DOTACION - N_CON_JRQDATE} docentes",
            "lines": [
                f"{N_DOTACION - N_CON_JRQDATE} docentes dentro de los {N_DOTACION} con dotación no tienen fecha de jerarquización.",
                "Necesario para: calcular 'Años hasta jerarquización' y analizar trayectoria académica.",
                "Solicitar: completar FECHA_JERARQUIZACION en hoja NÓMINA.",
            ],
            "impacto": f"Sube de {N_CON_JRQDATE} a {N_DOTACION} los disponibles para análisis de trayectoria",
            "yc": 4.05,
        },
        {
            "num": "4", "col": "#4A7030",
            "title": "P2  —  Confirmar completitud de iniciativas de formación 2025",
            "lines": [
                f"La base P2 contiene {N_INICIATIVAS} iniciativas ({N_FORMADOS} docentes únicos).",
                "Verificar que estén incluidos todos los talleres del período 2025.",
                "Confirmar si hay iniciativas de otros tipos no contemplados (ej. cursos, diplomados 2025).",
                "Solicitar: listado oficial de iniciativas P3 cerradas al corte 2026-01.",
            ],
            "impacto": f"Amplía el universo desde los {N_FORMADOS} formados actuales",
            "yc": 1.55,
        },
    ]

    for s in solicitudes:
        yc = s["yc"]; y0 = yc - BOX_H/2
        ax.add_patch(mpatches.FancyBboxPatch(
            (-0.05, y0), 10.1, BOX_H,
            boxstyle="round,pad=0.10", facecolor=s["col"],
            edgecolor="white", linewidth=0.6, alpha=0.32, zorder=2))
        circ = mpatches.Circle((0.42, yc + 0.65), 0.35,
                                facecolor=s["col"], edgecolor="white",
                                linewidth=0.8, alpha=0.95, zorder=3)
        ax.add_patch(circ)
        ax.text(0.42, yc + 0.65, s["num"],
                ha="center", va="center", fontsize=15, fontweight="bold",
                color="white", zorder=4)
        ax.text(1.00, yc + 0.83, s["title"],
                ha="left", va="center", fontsize=10, fontweight="bold",
                color="#FFD580", zorder=4)
        y_txt = yc + 0.40
        for line in s["lines"]:
            ax.text(1.00, y_txt, line,
                    ha="left", va="top", fontsize=7.8, color="#D0E8FF", zorder=4)
            y_txt -= 0.37
        ax.text(0.42, y0 + 0.18, "→ " + s["impacto"],
                ha="left", va="center", fontsize=7.8,
                color="#A8E8A0", zorder=4, fontstyle="italic")

    path = _save_ch(fig, "ficha_p1p2_solicitudes.png")

    sl = _new_sl(prs)
    _pic(sl, SHARED_BG, prs)
    _pic(sl, path, prs)
    _T(sl, "Datos Adicionales — Solicitudes para Completar P1 y P2", fs=15)
    _POP(sl, f"P1 trabaja con {N_DOTACION} docentes Jornada con perfil completo ({100*N_DOTACION/N_JORNADA:.0f}% del total Jornada)  |  "
             f"Solicitudes ordenadas por impacto")
    _BUL(sl, [
        f"La solicitud más impactante (N°1) es actualizar la hoja DOTACIÓN al corte 2026-01 "
        f"para incluir los {N_SIN_DOT} Jornada sin cruce: ampliaría P1 de {N_DOTACION} "
        f"a los {N_JORNADA} docentes de planta completos.",
        f"Las solicitudes N°2 y N°3 son correcciones menores de campos "
        f"(sexo y fecha de jerarquización) que elevan la completitud interna de los "
        f"{N_DOTACION} ya cubiertos.",
    ])
    print("  slide 6 - Solicitudes OK")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Generando FICHA_P1_P2_v2.pptx ...")
    _ensure_bg()
    prs = Presentation()
    prs.slide_width  = Emu(SW_EMU)
    prs.slide_height = Emu(SH_EMU)
    slide_portada(prs)
    slide_cascada_p1(prs)
    slide_jornada_sin_dotacion(prs)
    slide_subcascadas(prs)
    slide_cascada_p2(prs)
    slide_solicitudes(prs)
    prs.save(OUT_PPTX)
    print(f"\n  Guardado: {OUT_PPTX}")
    print("  6 slides: [1] Portada, [2] Cascada P1, [3] Jornada sin Dotación, "
          "[4] Sub-cascadas, [5] Cascada P2, [6] Solicitudes")
