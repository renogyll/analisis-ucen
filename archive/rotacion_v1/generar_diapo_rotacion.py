"""
Standalone: genera DIAPO_rotacion_docente.pptx (10 diapositivas) — rotación
de docentes entre el universo histórico consolidado y el snapshot vigente
de dotación 2026.

Pedido de la contraparte (vía el usuario, 2026-09-14): entender cuántos
docentes siguen en la planta vs. cuántos ya no, comparando punto inicial
(fecha_ingreso/fecha_jerarquizacion de universo_base) vs punto final
(archivo de planeación 2026). Ver D35 en docs/DECISIONES_METODOLOGICAS.md
para el detalle completo de supuestos y hallazgos de calidad de datos.

Universo: 1.144 docentes históricos (se excluyen 539 "altas nuevas" del
archivo 2026 — sin punto inicial, no se puede medir rotación para ellos,
decisión explícita del usuario). 290 "no encontrados en 2026" se asumen
baja confirmada.

Estructura (10 diapositivas) — apuntes de la contraparte, 2026-09-24:
  0. Universo / Índice / Hallazgos — mismo patrón que P1 (uih_bN en
     products/p1_planta/slides_estructura.py), reimplementado acá porque
     este script no usa UcenSlideKit. Índice y Hallazgos con placeholder,
     a pedido explícito ("no dejemos nada aún").
  1. Metodología — línea de tiempo (punto inicial -> corte 2026 -> Activo/Baja)
  2. Tabla de pruebas de significancia estadística — vacía, placeholder
  3. Portada — universo, Activo/Baja totales, tasa general y por contrato final
  4. Rotación por tipo de contrato (final) — Jornada/Honorario reclasificados
  5. Rotación por jerarquía — 8 categorías (D25)
  6. Rotación por facultad — 6 categorías (D32)
  7. Rotación por antigüedad al corte — confirmada/estimada (D33), tramos
  8. Transición de régimen — N° de docentes que cambiaron Jornada<->Honorario
  9. Perfil de los transicionados — sexo/escalafón/facultad de esos 73,
     descriptivo puro (sin prueba t, base insuficiente)

Estilo tipográfico (apuntes de la contraparte): Calibri en todo el deck —
13pt blanco para títulos de gráfico y punteos, 11pt gris (#A9B7C6) para
subtítulos. Punteos reescritos como frases breves que señalan/describen el
dato mostrado, no párrafos explicativos — el detalle largo vive en D35, no
en la diapositiva.

FUENTE: analisis.universo_rotacion (generado por
products/rotacion_docente/etl/generar_tag_rotacion.py).
SALIDA: DIAPO_rotacion_docente.pptx (10 diapositivas)
"""
import sys; sys.stdout.reconfigure(encoding="utf-8")
import os, zipfile, pathlib
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import pandas as pd
from PIL import Image as PILImage
from sqlalchemy import create_engine, text
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

FONT = "Calibri"

# ── Rutas ───────────────────────────────────────────────────────────────────
BASE      = os.path.dirname(os.path.abspath(__file__))
REPO      = str(pathlib.Path(BASE).parents[2])
SCRATCH   = os.path.join(REPO, "outputs", "scratch")
OUT_DIR   = os.path.join(BASE, "dark_slides")
FONDOTIPO = os.path.join(REPO, "assets", "Fondotipop.pptx")

BG_PATH   = os.path.join(SCRATCH, "fondotipo_image1.jpg")
LOGO_PATH = os.path.join(SCRATCH, "fondotipo_image2.png")
SHARED_BG = os.path.join(OUT_DIR, "_background.png")
OUT_PPTX  = os.path.join(REPO, "outputs", "pptx", "DIAPO_rotacion_docente.pptx")

os.makedirs(OUT_DIR, exist_ok=True)
for path, zname in [(BG_PATH, "ppt/media/image1.jpg"), (LOGO_PATH, "ppt/media/image2.png")]:
    if not os.path.exists(path):
        with zipfile.ZipFile(FONDOTIPO) as z:
            with open(path, "wb") as f:
                f.write(z.read(zname))

# ── Constantes de layout ────────────────────────────────────────────────────
SW, SH = 13.333, 7.5
SW_EMU = 12192000
SH_EMU = 6858000

PIC_L, PIC_T, PIC_W, PIC_H = 786581, 1125000, 10599174, 3720000
BUL_L, BUL_T, BUL_W, BUL_H = 786581, 4870000, 10599174, 1870000
LOGO_L, LOGO_T, LOGO_W, LOGO_H = 9813773, 656354, 1756626, 697725
TITLE_L, TITLE_T, TITLE_W, TITLE_H = PIC_L, 185000, PIC_W, 710000
POP_L, POP_T, POP_W, POP_H = PIC_L, 845000, 9000000, 255000


def _ex(e): return e / SW_EMU
def _ey(e): return e / SH_EMU
def _fig_rect(l, t, w, h): return (l, 1 - t - h, w, h)


PIC_RECT = _fig_rect(_ex(PIC_L), _ey(PIC_T), _ex(PIC_W), _ey(PIC_H))
CHART_X = PIC_RECT[0] + 0.13
CHART_Y = PIC_RECT[1] + 0.04
CHART_W = PIC_RECT[2] - 0.19
CHART_H = PIC_RECT[3] - 0.09

CTITLE_L = int(CHART_X * SW_EMU)
CTITLE_T = PIC_T + 38000
CTITLE_W = int((PIC_RECT[0] + PIC_RECT[2] - CHART_X + 0.02) * SW_EMU)
CTITLE_H = 295000

COL_ACTIVO = "#5C9BD6"
COL_BAJA = "#FFB74D"
COL_TRANS = "#9085e9"
COL_SINDATO = "#7A8699"
STROKE = [pe.withStroke(linewidth=1.6, foreground="#0A0F18")]

FAC_ORD_REALES = ["Medicina y C. Salud", "Ingeniería y Arq.", "Educación",
                   "Economía, Gob. y Com.", "Derecho y Humanidades"]
FAC_OTRA = "Otra / Sin facultad"
CAT_ORD_JERARQUIA = ["INSTRUCTOR DOCENTE", "INSTRUCTOR REGULAR",
                      "ASISTENTE DOCENTE", "ASISTENTE REGULAR",
                      "ASOCIADO DOCENTE", "ASOCIADO REGULAR",
                      "TITULAR DOCENTE", "TITULAR REGULAR"]
TRAMO_ANT_ORD = ["0-4", "5-9", "10-14", "15-19", "20+"]

# ── Fondo compartido ────────────────────────────────────────────────────────
if not os.path.exists(SHARED_BG):
    print("Generando fondo...")
    with PILImage.open(BG_PATH) as im:
        rgb = im.convert("RGB"); iw, ih = rgb.size
        nh = int(iw / (16 / 9)); y0 = min(int(ih * 0.12), ih - nh)
        bg_arr = np.array(rgb.crop((0, y0, iw, y0 + nh)))
    with PILImage.open(LOGO_PATH) as lg:
        logo_arr = np.array(lg.convert("RGBA")).astype(np.float32) / 255.0
    H_GRAD = 600; grad = np.zeros((H_GRAD, 1, 4), dtype=np.float32)
    for r in range(H_GRAD):
        t = r / (H_GRAD - 1)
        stops = [(0.00, (0, 33, 71)), (0.54, (0, 70, 128)), (1.00, (144, 171, 196))]
        for i in range(len(stops) - 1):
            t0, c0 = stops[i]; t1, c1 = stops[i + 1]
            if t0 <= t <= t1:
                s = (t - t0) / (t1 - t0)
                grad[r, 0] = [(c0[j] + s * (c1[j] - c0[j])) / 255 for j in range(3)] + [0.82]; break
    fig_bg = plt.figure(figsize=(SW, SH)); ax_bg = fig_bg.add_axes([0, 0, 1, 1])
    ax_bg.imshow(bg_arr, aspect="auto", extent=[0, 1, 0, 1])
    ax_bg.imshow(np.tile(grad, (1, 1000, 1)), aspect="auto", extent=[0, 1, 0, 1])
    lx = _ex(LOGO_L); ly = 1 - _ey(LOGO_T) - _ey(LOGO_H)
    ax_bg.imshow(logo_arr, aspect="auto", extent=[lx, lx + _ex(LOGO_W), ly, ly + _ey(LOGO_H)])
    # Sin esto matplotlib reencuadra la vista al extent del último imshow (el
    # logo, chico) en vez del lienzo completo — ver D34.
    ax_bg.set_xlim(0, 1); ax_bg.set_ylim(0, 1)
    ax_bg.axis("off")
    plt.savefig(SHARED_BG, dpi=150, facecolor=fig_bg.get_facecolor())
    plt.close()
    print(f"  Fondo guardado: {SHARED_BG}")


def _txt(sl, text, left, top, width, height,
         fs=13, bold=False, italic=False, color="#FFFFFF",
         align=PP_ALIGN.LEFT, wrap=True):
    txb = sl.shapes.add_textbox(Emu(left), Emu(top), Emu(width), Emu(height))
    tf = txb.text_frame; tf.word_wrap = wrap
    for i, line in enumerate(str(text).split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        run = p.add_run(); run.text = line
        run.font.size = Pt(fs); run.font.bold = bold; run.font.italic = italic
        run.font.name = FONT
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        run.font.color.rgb = RGBColor(r, g, b)


def _bullets(sl, items, left, top, width, height, fs=13, color="#FFFFFF", space_after=6):
    txb = sl.shapes.add_textbox(Emu(left), Emu(top), Emu(width), Emu(height))
    tf = txb.text_frame; tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(space_after); p.alignment = PP_ALIGN.LEFT
        run = p.add_run(); run.text = f"•  {item}"
        run.font.size = Pt(fs); run.font.name = FONT
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        run.font.color.rgb = RGBColor(r, g, b)


def fac_norm(s):
    if not isinstance(s, str) or not s.strip():
        return FAC_OTRA
    u = s.upper()
    if "MEDICINA" in u and "SALUD" in u: return "Medicina y C. Salud"
    if "DERECHO" in u and "HUMANIDADES" in u: return "Derecho y Humanidades"
    if "INGENIER" in u: return "Ingeniería y Arq."
    if "EDUCACI" in u: return "Educación"
    if "ECONOM" in u and "GOBIERNO" in u: return "Economía, Gob. y Com."
    return FAC_OTRA


def _bg_slide(prs):
    sl = prs.slides.add_slide(prs.slide_layouts[6])
    sl.shapes.add_picture(SHARED_BG, Emu(0), Emu(0), Emu(SW_EMU), Emu(SH_EMU))
    return sl


def _save_chart(fig, name):
    path = os.path.join(OUT_DIR, name)
    fig.savefig(path, dpi=150, facecolor="none", transparent=True)
    plt.close(fig)
    return path


def _new_fig():
    fig = plt.figure(figsize=(SW, SH), facecolor="none")
    fig.patch.set_facecolor("none")
    return fig


SUBT_COLOR = "#A9B7C6"  # "algo más gris" que el texto blanco general


def _add_texts(sl, titulo, subtitulo, chart_title, bullets):
    _txt(sl, titulo, TITLE_L, TITLE_T, TITLE_W, TITLE_H, fs=18, bold=True,
         color="#FFFFFF", align=PP_ALIGN.CENTER)
    _txt(sl, subtitulo, POP_L, POP_T, POP_W, POP_H, fs=11, color=SUBT_COLOR)
    _txt(sl, chart_title, CTITLE_L, CTITLE_T, CTITLE_W, CTITLE_H, fs=13, color="#FFFFFF")
    _bullets(sl, bullets, BUL_L, BUL_T, BUL_W, BUL_H, fs=13, color="#FFFFFF")


# ── Datos ───────────────────────────────────────────────────────────────────
DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"
engine = create_engine(DB_URL)


def cargar_datos():
    df = pd.read_sql(text("SELECT * FROM analisis.universo_rotacion"), engine)
    df["fac"] = df["unidad_facultad"].apply(fac_norm)
    df["baja_bin"] = df["estado"] == "Baja"
    return df


def slide_portada(prs, df):
    sl = _bg_slide(prs)
    n = len(df)
    activo = (df["estado"] == "Activo").sum()
    baja = (df["estado"] == "Baja").sum()

    _txt(sl, "Rotación Docente — Punto Inicial vs. Planeación 2026",
         TITLE_L, TITLE_T, TITLE_W, TITLE_H, fs=20, bold=True, color="#FFFFFF",
         align=PP_ALIGN.CENTER)
    _txt(sl, f"Universo: {n} docentes históricos (Jornada + Honorario) — analisis.universo_rotacion (D35)",
         POP_L, POP_T, POP_W, POP_H, fs=11, color=SUBT_COLOR)

    def _caja(left, titulo, color, valor, sub):
        _txt(sl, titulo, left, 1650000, 5600000, 300000, fs=13, bold=True, color=color, align=PP_ALIGN.CENTER)
        _txt(sl, valor, left, 2000000, 5600000, 700000, fs=44, bold=True, color="#FFFFFF", align=PP_ALIGN.CENTER)
        _txt(sl, sub, left, 2680000, 5600000, 260000, fs=11, color=SUBT_COLOR, align=PP_ALIGN.CENTER)

    _caja(786581, "ACTIVOS (siguen en 2026)", COL_ACTIVO, f"{activo}", f"{activo/n*100:.0f}% del universo histórico")
    _caja(6392419, "BAJA (no aparecen en 2026)", COL_BAJA, f"{baja}", f"{baja/n*100:.0f}% del universo histórico")

    tab = pd.crosstab(df["tipo_contrato_rotacion"], df["estado"])
    tasa_j = tab.loc["JORNADA", "Baja"] / tab.loc["JORNADA"].sum() * 100
    tasa_h = tab.loc["HONORARIO", "Baja"] / tab.loc["HONORARIO"].sum() * 100
    n_trans = (df["transicion"] != "N/A (baja o sin cambio)").sum()

    _txt(sl, "En esta pasada", BUL_L, 3600000, BUL_W, 260000, fs=13, bold=True, color="#FFFFFF")
    bullets = [
        f"25% del universo histórico no aparece en el archivo 2026.",
        f"Tasa de baja: {tasa_j:.0f}% Jornada vs {tasa_h:.0f}% Honorario.",
        f"{n_trans} docentes cambiaron de régimen (Jornada↔Honorario) sin darse de baja.",
        "539 altas nuevas del archivo 2026 quedan fuera del análisis.",
    ]
    _bullets(sl, bullets, BUL_L, 3900000, BUL_W, 2600000, fs=13, color="#FFFFFF")
    return sl


def slide_tasa_por_categoria(prs, df, categorias, col_cat, titulo, subtitulo,
                              chart_title, bullets, fname, wrap_labels=False):
    tab = df.groupby(col_cat).agg(n=("rut_key", "size"), pct_baja=("baja_bin", "mean"))
    tab["pct_baja"] *= 100
    tab["pct_activo"] = 100 - tab["pct_baja"]
    tab = tab.reindex(categorias)

    fig = _new_fig()
    ax = fig.add_axes([CHART_X, CHART_Y, CHART_W, CHART_H], facecolor="none", zorder=5)
    x = np.arange(len(categorias))
    bw = 0.5

    ax.bar(x, tab["pct_activo"], width=bw, color=COL_ACTIVO, alpha=0.92, edgecolor="none", label="Activo")
    ax.bar(x, tab["pct_baja"], width=bw, bottom=tab["pct_activo"], color=COL_BAJA, alpha=0.92,
           edgecolor="none", label="Baja")

    for xi, a, b in zip(x, tab["pct_activo"], tab["pct_baja"]):
        ax.text(xi, a / 2, f"{a:.0f}%", ha="center", va="center", fontsize=10,
                 fontweight="bold", color="white", path_effects=STROKE, zorder=6)
        if b > 5:
            ax.text(xi, a + b / 2, f"{b:.0f}%", ha="center", va="center", fontsize=9.5,
                     fontweight="bold", color="#3A2A00", zorder=6)

    for xi, n in zip(x, tab["n"]):
        ax.text(xi, -6, f"N°={int(n)}", ha="center", va="top", fontsize=7.5, color="#AAAAAA")

    labels = categorias
    if wrap_labels:
        labels = [c.replace(", ", ",\n").replace(" y ", " y\n", 1) if len(c) > 16 else c for c in categorias]
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8.8, color="white",
                        rotation=(20 if len(categorias) > 6 else 0))
    ax.set_ylabel("%", color="#AAAAAA", fontsize=9)
    ax.set_ylim(-10, 112)
    ax.set_yticks([0, 20, 40, 60, 80, 100])
    ax.tick_params(axis="x", length=0, pad=10)
    ax.tick_params(axis="y", colors="#AAAAAA", labelsize=8)
    for sp in ax.spines.values():
        sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.7)
    ax.yaxis.grid(True, color="white", alpha=0.07, linewidth=0.5)
    ax.set_axisbelow(True)
    ax.legend(fontsize=9, framealpha=0.22, labelcolor="white", facecolor="#101820",
              edgecolor="#444", loc="upper center", bbox_to_anchor=(0.5, 1.10),
              ncol=2, borderaxespad=0.4, columnspacing=1.4, handlelength=1.6)

    chart_path = _save_chart(fig, fname)
    sl = _bg_slide(prs)
    sl.shapes.add_picture(chart_path, Emu(0), Emu(0), Emu(SW_EMU), Emu(SH_EMU))
    _add_texts(sl, titulo, subtitulo, chart_title, bullets)
    return sl, tab


def slide_transicion(prs, df):
    trans = df[df["transicion"] != "N/A (baja o sin cambio)"].copy()
    n_jh = (trans["transicion"] == "Jornada -> Honorario").sum()
    n_hj = (trans["transicion"] == "Honorario -> Jornada").sum()

    fig = _new_fig()
    ax1 = fig.add_axes([CHART_X + CHART_W * 0.22, CHART_Y, CHART_W * 0.56, CHART_H], facecolor="none", zorder=5)

    ax1.bar([0, 1], [n_jh, n_hj], width=0.45, color=[COL_TRANS, "#c98500"], alpha=0.92)
    ax1.text(0, n_jh + 1.5, f"{n_jh}", ha="center", fontsize=20, fontweight="bold", color=COL_TRANS, path_effects=STROKE)
    ax1.text(1, n_hj + 1.5, f"{n_hj}", ha="center", fontsize=20, fontweight="bold", color="#c98500", path_effects=STROKE)
    ax1.set_xticks([0, 1])
    ax1.set_xticklabels(["Jornada →\nHonorario", "Honorario →\nJornada"], fontsize=12, color="white")
    ax1.set_ylim(0, max(n_jh, n_hj) * 1.35)
    ax1.tick_params(axis="y", colors="#AAAAAA", labelsize=8.5)
    ax1.tick_params(axis="x", length=0, pad=8)
    for sp in ax1.spines.values():
        sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.7)
    ax1.yaxis.grid(True, color="white", alpha=0.07, linewidth=0.5)
    ax1.set_axisbelow(True)

    chart_path = _save_chart(fig, "transicion_regimen.png")
    sl = _bg_slide(prs)
    sl.shapes.add_picture(chart_path, Emu(0), Emu(0), Emu(SW_EMU), Emu(SH_EMU))

    ant_trans = trans["antiguedad_minima_anios"].dropna().mean()
    ant_resto = df.loc[(df["estado"] == "Activo") & (df["transicion"] == "N/A (baja o sin cambio)"),
                        "antiguedad_minima_anios"].dropna().mean()
    bullets = [
        f"73 docentes activos, no bajas — cambiaron de tipo de contrato.",
        f"{n_jh} Jornada→Honorario, {n_hj} Honorario→Jornada ({n_jh/n_hj:.1f}x más frecuente).",
        f"Antigüedad mínima promedio: {ant_trans:.1f} años (transicionados) vs {ant_resto:.1f} años (resto activo).",
        "Perfil demográfico del grupo en la siguiente diapositiva.",
        "Lista con nombre y RUT exportada aparte: transiciones_jornada_honorario.csv.",
    ]
    _add_texts(sl, "Transición de Régimen — Jornada ↔ Honorario",
               "Universo: 73 docentes activos que cambiaron de tipo de contrato entre el universo histórico y 2026",
               "N° de docentes por dirección de transición",
               bullets)
    return sl


def slide_perfil_transicionados(prs, df):
    trans = df[df["transicion"] != "N/A (baja o sin cambio)"].copy()
    n = len(trans)

    fig = _new_fig()
    panel_w = (CHART_W - 0.10) / 3
    ax1 = fig.add_axes([CHART_X, CHART_Y, panel_w, CHART_H], facecolor="none", zorder=5)
    ax2 = fig.add_axes([CHART_X + panel_w + 0.05, CHART_Y, panel_w, CHART_H], facecolor="none", zorder=5)
    ax3 = fig.add_axes([CHART_X + 2 * (panel_w + 0.05), CHART_Y, panel_w, CHART_H], facecolor="none", zorder=5)

    def _barras(ax, cats, vals, colors, titulo):
        ax.bar(range(len(cats)), vals, width=0.55, color=colors, alpha=0.92)
        for xi, v in zip(range(len(cats)), vals):
            ax.text(xi, v + max(vals) * 0.03, f"{v}", ha="center", fontsize=11,
                     fontweight="bold", color="white", path_effects=STROKE)
        ax.set_xticks(range(len(cats)))
        ax.set_xticklabels(cats, fontsize=8, color="white", rotation=(15 if len(cats) > 2 else 0))
        ax.set_ylim(0, max(vals) * 1.3)
        ax.set_title(titulo, fontsize=9, color="white", pad=8)
        ax.tick_params(axis="y", colors="#AAAAAA", labelsize=7)
        ax.tick_params(axis="x", length=0)
        for sp in ax.spines.values():
            sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.7)

    # Panel 1: sexo
    sexo_c = trans["sexo"].value_counts()
    cats_sexo = [c for c in ["MUJER", "HOMBRE"] if c in sexo_c.index]
    _barras(ax1, [c.title() for c in cats_sexo], [sexo_c[c] for c in cats_sexo],
            [COL_TRANS, COL_ACTIVO], "Sexo")

    # Panel 2: escalafón (Docente/Regular) — la granularidad correcta para N=73,
    # no las 8 categorías completas de jerarquía (celdas de 1-14, no informativas)
    trans["escalafon"] = np.where(trans["jerarquia"].str.contains("REGULAR", na=False), "Regular",
                          np.where(trans["jerarquia"].notna(), "Docente", "Sin dato"))
    esc = trans["escalafon"].value_counts()
    cats_esc = [c for c in ["Docente", "Regular", "Sin dato"] if c in esc.index]
    colors_esc = {"Docente": COL_ACTIVO, "Regular": COL_TRANS, "Sin dato": COL_SINDATO}
    _barras(ax2, cats_esc, [esc[c] for c in cats_esc], [colors_esc[c] for c in cats_esc], "Escalafón")

    # Panel 3: facultad
    trans["fac"] = trans["unidad_facultad"].apply(fac_norm)
    fac_c = trans["fac"].value_counts()
    fac_ord = [f for f in (FAC_ORD_REALES + [FAC_OTRA]) if f in fac_c.index]
    _barras(ax3, [f.split(" ")[0] for f in fac_ord], [fac_c[f] for f in fac_ord],
            [COL_ACTIVO] * len(fac_ord), "Facultad")

    chart_path = _save_chart(fig, "perfil_transicionados.png")
    sl = _bg_slide(prs)
    sl.shapes.add_picture(chart_path, Emu(0), Emu(0), Emu(SW_EMU), Emu(SH_EMU))

    bullets = [
        f"Descriptivo, sin prueba t — base insuficiente (N°={n}).",
        f"Sexo: {sexo_c.get('MUJER',0)} Mujeres, {sexo_c.get('HOMBRE',0)} Hombres.",
        f"Escalafón: mayoritariamente Docente ({esc.get('Docente',0)} de {n}).",
        f"Facultad: concentrado en 'Otra / Sin facultad' ({fac_c.get(FAC_OTRA,0)} de {n}).",
    ]
    _add_texts(sl, "Perfil de los Transicionados — Sexo, Escalafón y Facultad",
               f"Universo: {n} docentes que cambiaron de régimen — descriptivo, sin prueba t (base insuficiente)",
               "Composición del grupo de transicionados por sexo, escalafón y facultad",
               bullets)
    return sl


def slide_metodologia(prs):
    fig = _new_fig()
    ax = fig.add_axes([CHART_X, CHART_Y, CHART_W, CHART_H], facecolor="none", zorder=5)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis("off")

    y_mid = 0.55
    x_inicio, x_corte = 0.10, 0.50
    x_fin_activo, x_fin_baja = 0.92, 0.72

    # Línea histórica: inicio -> corte (un solo universo, sin distinguir todavía)
    ax.plot([x_inicio, x_corte], [y_mid, y_mid], color="white", lw=2.5, alpha=0.85, zorder=3)
    ax.scatter([x_inicio], [y_mid], s=200, color=COL_ACTIVO, zorder=5, edgecolor="white", linewidth=1.5)
    ax.annotate("PUNTO INICIAL", (x_inicio, y_mid), xytext=(x_inicio, y_mid + 0.17),
                ha="center", fontsize=12, fontweight="bold", color="white")
    ax.annotate("fecha_ingreso /\nfecha_jerarquización\n(analisis.universo_base — histórico)",
                (x_inicio, y_mid), xytext=(x_inicio, y_mid - 0.20),
                ha="center", fontsize=8.5, color="#C8DCF0")

    # Corte 2026 (vertical, punteado)
    ax.plot([x_corte, x_corte], [y_mid - 0.32, y_mid + 0.32], color="white", lw=1.3,
            linestyle="--", alpha=0.6, zorder=2)
    ax.annotate("PUNTO DE CORTE — 2026", (x_corte, y_mid), xytext=(x_corte, y_mid + 0.17),
                ha="center", fontsize=12, fontweight="bold", color="white")
    ax.annotate("Planeación docente 2026\n(archivo de dotación vigente)",
                (x_corte, y_mid), xytext=(x_corte, y_mid - 0.20),
                ha="center", fontsize=8.5, color="#C8DCF0")

    # Rama ACTIVO — continúa (el quiebre empieza bien pasado el corte, para no
    # cruzar el texto de "PUNTO DE CORTE" que queda centrado en x_corte)
    x_kink = x_corte + 0.16
    y_activo = y_mid + 0.20
    ax.plot([x_corte, x_kink, x_fin_activo], [y_mid, y_activo, y_activo],
            color=COL_ACTIVO, lw=2.8, zorder=3, solid_capstyle="round")
    ax.annotate("", xy=(x_fin_activo + 0.015, y_activo), xytext=(x_fin_activo, y_activo),
                arrowprops=dict(arrowstyle="-|>", color=COL_ACTIVO, lw=2.8))
    ax.text(x_fin_activo + 0.03, y_activo, "ACTIVO\nSigue en la planta 2026",
            fontsize=10.5, fontweight="bold", color=COL_ACTIVO, va="center")

    # Rama BAJA — se corta
    y_baja = y_mid - 0.20
    ax.plot([x_corte, x_kink, x_fin_baja], [y_mid, y_baja, y_baja],
            color=COL_BAJA, lw=2.8, zorder=3, solid_capstyle="round")
    ax.scatter([x_fin_baja], [y_baja], marker="x", s=160, color=COL_BAJA, linewidth=3.2, zorder=5)
    ax.text(x_fin_baja + 0.03, y_baja, "BAJA\nNo aparece en 2026",
            fontsize=10.5, fontweight="bold", color=COL_BAJA, va="center")

    chart_path = _save_chart(fig, "metodologia_timeline.png")
    sl = _bg_slide(prs)
    sl.shapes.add_picture(chart_path, Emu(0), Emu(0), Emu(SW_EMU), Emu(SH_EMU))

    bullets = [
        "Punto inicial: fecha de ingreso, o fecha de jerarquización cuando falta (D33).",
        "Punto de corte: archivo de Planeación Docente 2026 — snapshot vigente de dotación.",
        "Activo = aparece en el archivo 2026. Baja = no aparece.",
        "Sin fecha exacta de salida — se sabe SI se fue, no CUÁNDO.",
        "539 altas nuevas del archivo 2026 quedan fuera del análisis (sin punto inicial).",
    ]
    _add_texts(sl, "Metodología — Cómo se Mide la Rotación",
               "Dos archivos, un punto inicial y un punto de corte — así se construye cada dato de esta presentación",
               "Línea de tiempo: del punto inicial al corte 2026, y las dos rutas posibles desde ahí",
               bullets)
    return sl


def _caja_uih(sl, universo_txt, indice_items, hallazgos_items):
    """1 caja navy de ancho completo, 3 columnas: Universo | Índice | Hallazgos —
    mismo patrón visual que UcenSlideKit.caja_universo_indice_hallazgos (P1),
    reimplementado acá porque este script usa su propio andamiaje standalone,
    no UcenSlideKit."""
    box_l, box_t = PIC_L, PIC_T
    box_w = PIC_W
    box_h = (BUL_T + BUL_H) - PIC_T
    sh = sl.shapes.add_shape(MSO_SHAPE.RECTANGLE, Emu(box_l), Emu(box_t), Emu(box_w), Emu(box_h))
    sh.fill.solid(); sh.fill.fore_color.rgb = RGBColor(0, 33, 71)
    sh.line.fill.background()

    col_w = box_w // 3
    for i, h in enumerate(["Universo", "Índice", "Hallazgos"]):
        cx = box_l + i * col_w
        _txt(sl, h, cx + 50000, box_t + 45000, col_w - 100000, 260000,
             fs=13, bold=True, color="#FFFFFF", align=PP_ALIGN.CENTER)
        div = sl.shapes.add_shape(MSO_SHAPE.RECTANGLE, Emu(cx + 50000), Emu(box_t + 330000),
                                   Emu(col_w - 100000), Emu(9000))
        div.fill.solid(); div.fill.fore_color.rgb = RGBColor(90, 140, 190)
        div.line.fill.background()

    _txt(sl, universo_txt, box_l + 50000, box_t + 410000, col_w - 100000, box_h - 470000,
         fs=13, color="#FFFFFF")
    idx_txt = "\n".join(f"{i + 1}. {it}" for i, it in enumerate(indice_items))
    _txt(sl, idx_txt, box_l + col_w + 50000, box_t + 410000, col_w - 100000, box_h - 470000,
         fs=13, color="#FFFFFF")
    hal_txt = "\n".join(f"{i + 1}. {it}" for i, it in enumerate(hallazgos_items))
    _txt(sl, hal_txt, box_l + 2 * col_w + 50000, box_t + 410000, col_w - 100000, box_h - 470000,
         fs=13, color="#FFFFFF")


def slide_uih(prs):
    sl = _bg_slide(prs)
    _txt(sl, "Rotación Docente — Universo, Índice y Hallazgos",
         TITLE_L, TITLE_T, TITLE_W, TITLE_H, fs=18, bold=True, color="#FFFFFF",
         align=PP_ALIGN.CENTER)
    _caja_uih(sl,
        universo_txt=(
            "Universo histórico: 1.144 docentes de analisis.universo_base "
            "(Jornada + Honorario). Se cruza contra el archivo de Planeación "
            "Docente 2026 (dotación vigente) para construir "
            "analisis.universo_rotacion (D35): 854 activos (siguen en 2026) "
            "y 290 de baja (no aparecen). Se excluyen 539 altas nuevas del "
            "archivo 2026 sin punto inicial conocido. Dentro de los 854 "
            "activos, 73 además cambiaron de tipo de contrato "
            "(Jornada↔Honorario) — sub-universo analizado aparte al final."
        ),
        indice_items=["Pendiente"],
        hallazgos_items=["Pendiente"])
    return sl


def slide_tabla_significancia(prs):
    sl = _bg_slide(prs)
    _txt(sl, "Pruebas de Significancia Estadística",
         TITLE_L, TITLE_T, TITLE_W, TITLE_H, fs=18, bold=True, color="#FFFFFF",
         align=PP_ALIGN.CENTER)
    _txt(sl, "Pendiente de definir — se completa al correr las pruebas por corte",
         POP_L, POP_T, POP_W, POP_H, fs=11, color=SUBT_COLOR)

    rows, cols = 5, 5
    box_t = PIC_T
    box_h = (BUL_T + BUL_H) - PIC_T
    tbl_shape = sl.shapes.add_table(rows, cols, Emu(PIC_L), Emu(box_t), Emu(PIC_W), Emu(box_h))
    tbl = tbl_shape.table

    headers = ["Corte / Variable", "N", "Estadístico", "p-valor", "¿Significativa?"]
    for j, h in enumerate(headers):
        cell = tbl.cell(0, j)
        cell.text = h
        cell.fill.solid(); cell.fill.fore_color.rgb = RGBColor(0, 33, 71)
        for p in cell.text_frame.paragraphs:
            p.alignment = PP_ALIGN.CENTER
            for run in p.runs:
                run.font.size = Pt(13); run.font.bold = True; run.font.name = FONT
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    for i in range(1, rows):
        for j in range(cols):
            cell = tbl.cell(i, j)
            cell.text = "—"
            cell.fill.solid(); cell.fill.fore_color.rgb = RGBColor(9, 26, 48)
            for p in cell.text_frame.paragraphs:
                p.alignment = PP_ALIGN.CENTER
                for run in p.runs:
                    run.font.size = Pt(13); run.font.name = FONT
                    r, g, b = (int(SUBT_COLOR[1:3], 16), int(SUBT_COLOR[3:5], 16), int(SUBT_COLOR[5:7], 16))
                    run.font.color.rgb = RGBColor(r, g, b)

    return sl


if __name__ == "__main__":
    df = cargar_datos()
    print(f"Universo cargado: {len(df)} docentes")

    prs = Presentation()
    prs.slide_width = Emu(SW_EMU)
    prs.slide_height = Emu(SH_EMU)

    slide_uih(prs)
    slide_metodologia(prs)
    slide_tabla_significancia(prs)
    slide_portada(prs, df)

    tab_contrato = df.groupby("tipo_contrato_rotacion").agg(n=("rut_key", "size"), pct_baja=("baja_bin", "mean"))
    slide_tasa_por_categoria(
        prs, df, ["JORNADA", "HONORARIO"], "tipo_contrato_rotacion",
        titulo="Rotación por Tipo de Contrato (final)",
        subtitulo="Activos reclasificados por su contrato 2026; bajas mantienen su contrato de origen (único dato disponible) — ver D35",
        chart_title="% de docentes Activo/Baja por tipo de contrato",
        bullets=[
            f"Honorario: {tab_contrato.loc['HONORARIO','pct_baja']*100:.0f}% de baja vs "
            f"{tab_contrato.loc['JORNADA','pct_baja']*100:.0f}% en Jornada — casi el doble.",
            "Contrato final (2026) para activos; contrato de origen para bajas.",
        ],
        fname="rotacion_contrato.png",
    )

    df_jer = df[df["jerarquia"].notna()]
    slide_tasa_por_categoria(
        prs, df_jer, CAT_ORD_JERARQUIA, "jerarquia",
        titulo="Rotación por Jerarquía",
        subtitulo="Universo: docentes con jerarquía conocida (D25) — 8 categorías, Docente y Regular",
        chart_title="% de docentes Activo/Baja por jerarquía",
        bullets=[
            "Línea Regular: baja consistentemente baja (8-10%).",
            "Titular Docente es la excepción: 28% de baja, la 2da tasa más alta.",
            "Instructor Regular: 36% de baja, pero N°=14 — base chica.",
        ],
        fname="rotacion_jerarquia.png",
    )

    slide_tasa_por_categoria(
        prs, df, FAC_ORD_REALES + [FAC_OTRA], "fac",
        titulo="Rotación por Facultad",
        subtitulo="Universo: 1.144 docentes, 6 categorías (5 facultades reales + Otra/Sin facultad, D32)",
        chart_title="% de docentes Activo/Baja por facultad",
        bullets=[
            "'Otra / Sin facultad' tiene la mayor baja: 32%.",
            "Entre las 5 reales: Educación más alta (26%), Economía/Gob./Com. más baja (14%).",
        ],
        fname="rotacion_facultad.png", wrap_labels=True,
    )

    df_ant = df[df["tramo_antiguedad_corte"].notna()]
    slide_tasa_por_categoria(
        prs, df_ant, TRAMO_ANT_ORD, "tramo_antiguedad_corte",
        titulo="Rotación por Antigüedad al Corte",
        subtitulo="Antigüedad mínima conocida (confirmada por fecha_ingreso o estimada por fecha_jerarquizacion, D33) — para quienes se fueron, cota inferior, no duración real",
        chart_title="% de docentes Activo/Baja por tramo de antigüedad mínima conocida",
        bullets=[
            "La baja baja con la antigüedad: 22% (0-4 años) a 14% (20+ años).",
            "Antigüedad mínima conocida, no duración real (sin fecha de salida).",
        ],
        fname="rotacion_antiguedad.png",
    )

    slide_transicion(prs, df)
    slide_perfil_transicionados(prs, df)

    prs.save(OUT_PPTX)
    print(f"\n✓ Guardado: {OUT_PPTX} ({len(prs.slides)} diapositivas)")
