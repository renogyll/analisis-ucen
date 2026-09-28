"""
Standalone: genera DIAPO_perfil_electores.pptx (8 diapositivas) — perfil
demográfico de Electores/Elegibles para la elección de Asamblea General.

Pedido de la contraparte (vía el usuario, 2026-09-14): 6 análisis
descriptivos (edad+sexo, jerarquía, antigüedad, SAT, evaluación de
jefaturas/EDD, facultad) sobre el universo de 1.144 docentes, entendidos
como una caracterización de las poblaciones Electores/No electores y
Elegibles/No elegibles (D33/D34) — no un descriptivo aislado.

Regla de alcance confirmada con el usuario: donde el cruce con Honorario sea
viable se hace (Sexo, Jerarquía, Antigüedad, SAT, Facultad); donde no
(Edad, EDD — Honorario tiene 2-2.5% de cobertura) se hace Jornada-only y se
documenta la limitación en la diapositiva.

Estructura (8 diapositivas):
  0. Portada — universo y totales Elector/Elegible (confirmado+estimado+no+sin dato)
  1. SAT — nota promedio, Elector vs No / Elegible vs No (Welch t-test)
  2. Antigüedad — composición confirmado/estimado/no/sin dato por tipo de contrato
  3. Jerarquía — % Elector por las 8 categorías (D25); Elegible solo aplica a Titular
  4. Sexo — % Elector y % Elegible por sexo
  5. Facultad — % Elector y % Elegible por facultad (6 categorías, D32)
  6. Edad (Jornada-only) — % Elector y % Elegible por tramo de edad
  7. EDD / evaluación de jefaturas (Jornada-only) — promedio, Elector vs No / Elegible vs No

FUENTES: analisis.universo_electores (D33) + analisis.universo_base +
consolidados.evaluacion_periodo/evaluacion_respuesta (SAT_NOTA, CM-1) +
intel.evaluacion_jefes (EDD).
SALIDA: DIAPO_perfil_electores.pptx (8 diapositivas)
"""
import sys; sys.stdout.reconfigure(encoding="utf-8")
import os, zipfile, pathlib
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import pandas as pd
from scipy import stats
from PIL import Image as PILImage
from sqlalchemy import create_engine, text
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

# ── Rutas ───────────────────────────────────────────────────────────────────
BASE      = os.path.dirname(os.path.abspath(__file__))
REPO      = str(pathlib.Path(BASE).parents[2])
SCRATCH   = os.path.join(REPO, "outputs", "scratch")
OUT_DIR   = os.path.join(BASE, "dark_slides")
FONDOTIPO = os.path.join(REPO, "assets", "Fondotipop.pptx")

BG_PATH   = os.path.join(SCRATCH, "fondotipo_image1.jpg")
LOGO_PATH = os.path.join(SCRATCH, "fondotipo_image2.png")
SHARED_BG = os.path.join(OUT_DIR, "_background.png")
OUT_PPTX  = os.path.join(REPO, "outputs", "pptx", "DIAPO_perfil_electores.pptx")

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

# Colores — Elector reusa el azul ya establecido en el proyecto para
# binarios genéricos; Elegible reusa el morado del trío validado
# Taller/Diplomado/Proyecto (validate_palette.js, CVD ΔE 8.4 — distinto de
# azul/naranjo, ya pasó los checks en este mismo proyecto). "Sin dato" usa
# gris neutro (no es una categoría a distinguir por color, es ausencia de dato).
COL_ELECTOR = "#5C9BD6"
COL_ELEGIBLE = "#9085e9"
COL_NO = "#FFB74D"
COL_SINDATO = "#7A8699"
STROKE = [pe.withStroke(linewidth=1.6, foreground="#0A0F18")]

FAC_ORD_REALES = ["Medicina y C. Salud", "Ingeniería y Arq.", "Educación",
                   "Economía, Gob. y Com.", "Derecho y Humanidades"]
FAC_OTRA = "Otra / Sin facultad"
CAT_ORD_JERARQUIA = ["INSTRUCTOR DOCENTE", "INSTRUCTOR REGULAR",
                      "ASISTENTE DOCENTE", "ASISTENTE REGULAR",
                      "ASOCIADO DOCENTE", "ASOCIADO REGULAR",
                      "TITULAR DOCENTE", "TITULAR REGULAR"]

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
    # Sin esto, matplotlib re-encuadra la vista al extent del último imshow (el
    # logo, chico) en vez de mantener el lienzo completo [0,1]x[0,1] — bug
    # encontrado 2026-09-14, el logo terminaba "gigante" tapando toda la diapo.
    ax_bg.set_xlim(0, 1); ax_bg.set_ylim(0, 1)
    ax_bg.axis("off")
    plt.savefig(SHARED_BG, dpi=150, facecolor=fig_bg.get_facecolor())
    plt.close()
    print(f"  Fondo guardado: {SHARED_BG}")


def _txt(sl, text, left, top, width, height,
         fs=12, bold=False, italic=False, color="#FFFFFF",
         align=PP_ALIGN.LEFT, wrap=True):
    txb = sl.shapes.add_textbox(Emu(left), Emu(top), Emu(width), Emu(height))
    tf = txb.text_frame; tf.word_wrap = wrap
    for i, line in enumerate(str(text).split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        run = p.add_run(); run.text = line
        run.font.size = Pt(fs); run.font.bold = bold; run.font.italic = italic
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


def _style_ax(ax, ylim=(-10, 112)):
    ax.set_ylim(*ylim)
    ax.tick_params(axis="x", length=0, pad=10)
    ax.tick_params(axis="y", colors="#AAAAAA", labelsize=8)
    for sp in ax.spines.values():
        sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.7)
    ax.yaxis.grid(True, color="white", alpha=0.07, linewidth=0.5)
    ax.set_axisbelow(True)


def _add_texts(sl, titulo, subtitulo, chart_title, bullets):
    _txt(sl, titulo, TITLE_L, TITLE_T, TITLE_W, TITLE_H, fs=18, bold=True,
         color="#FFFFFF", align=PP_ALIGN.CENTER)
    _txt(sl, subtitulo, POP_L, POP_T, POP_W, POP_H, fs=8, italic=True, color="#C8DCF0")
    _txt(sl, chart_title, CTITLE_L, CTITLE_T, CTITLE_W, CTITLE_H, fs=9, color="#FFFFFF")
    txb = sl.shapes.add_textbox(Emu(BUL_L), Emu(BUL_T), Emu(BUL_W), Emu(BUL_H))
    tf = txb.text_frame; tf.word_wrap = True
    for i, item in enumerate(bullets):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(5); p.alignment = PP_ALIGN.LEFT
        run = p.add_run(); run.text = f"•  {item}"
        run.font.size = Pt(11); run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)


# ── Datos ───────────────────────────────────────────────────────────────────
DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"
engine = create_engine(DB_URL)


def cargar_datos():
    elect = pd.read_sql(text("SELECT * FROM analisis.universo_electores"), engine)
    base = pd.read_sql(text("SELECT rut_key, sexo, edad_anios FROM analisis.universo_base"), engine)
    sat = pd.read_sql(text("""
        SELECT p.rut_docente AS rut_key, avg(r.nota_promedio) AS sat_promedio
        FROM consolidados.evaluacion_periodo p
        JOIN consolidados.evaluacion_respuesta r ON r.evaluacion_id = p.evaluacion_id
        WHERE r.pregunta_id = 'SAT_NOTA' AND p.cobertura_pct >= 40
        GROUP BY p.rut_docente
    """), engine)
    edd = pd.read_sql(text("""
        SELECT rut_key, avg(edd_total) AS edd_promedio
        FROM intel.evaluacion_jefes
        WHERE edd_total IS NOT NULL
        GROUP BY rut_key
    """), engine)
    df = elect.merge(base, on="rut_key", how="left").merge(sat, on="rut_key", how="left").merge(edd, on="rut_key", how="left")
    df["fac"] = df["unidad_facultad"].apply(fac_norm)
    df["elector_bin"] = df["es_elector"].isin(["Sí", "Sí (estimado)"])
    df["elegible_bin"] = df["es_elegible"].isin(["Sí", "Sí (estimado)"])
    return df


# ── Slide 0: Portada ────────────────────────────────────────────────────────
def slide_portada(prs, df):
    sl = _bg_slide(prs)
    n = len(df)
    e = df["es_elector"].value_counts()
    g = df["es_elegible"].value_counts()

    _txt(sl, "Perfil Demográfico — Electores y Elegibles, Asamblea General",
         TITLE_L, TITLE_T, TITLE_W, TITLE_H, fs=20, bold=True, color="#FFFFFF",
         align=PP_ALIGN.CENTER)
    _txt(sl, f"Universo: {n} docentes (Jornada + Honorario) — analisis.universo_electores (D33)",
         POP_L, POP_T, POP_W, POP_H, fs=9, italic=True, color="#C8DCF0")

    def _caja(left, titulo, color, si, si_est, no, sd):
        _txt(sl, titulo, left, 1650000, 5600000, 300000, fs=13, bold=True, color=color, align=PP_ALIGN.CENTER)
        _txt(sl, f"{si + si_est}", left, 2000000, 5600000, 700000, fs=44, bold=True, color="#FFFFFF", align=PP_ALIGN.CENTER)
        _txt(sl, f"({si} confirmado + {si_est} estimado)", left, 2680000, 5600000, 260000, fs=9, italic=True, color="#C8DCF0", align=PP_ALIGN.CENTER)
        _txt(sl, f"No: {no}   ·   Sin dato: {sd}", left, 3050000, 5600000, 260000, fs=10, color="#AAAAAA", align=PP_ALIGN.CENTER)

    _caja(786581, "ELECTORES (Art. 2°)", COL_ELECTOR,
          e.get("Sí", 0), e.get("Sí (estimado)", 0), e.get("No", 0), e.get("Sin dato", 0))
    _caja(6392419, "ELEGIBLES (Art. 4°)", COL_ELEGIBLE,
          g.get("Sí", 0), g.get("Sí (estimado)", 0), g.get("No", 0), g.get("Sin dato", 0))

    _txt(sl, "En esta pasada", BUL_L, 3600000, BUL_W, 260000, fs=12, bold=True, color="#FFFFFF")
    bullets = [
        "7 análisis: SAT, Antigüedad, Jerarquía, Sexo, Facultad, Edad, Evaluación de Jefaturas (EDD) — cada uno cruzado contra Elector/Elegible.",
        "Donde el cruce con Honorario es viable (cobertura de dato razonable), se muestra; donde no (Edad, EDD), se indica explícitamente 'Jornada' en el título.",
        "'Estimado' = cota inferior segura por fecha de jerarquización cuando falta fecha de ingreso (ver D33) — nunca sobreestima, solo promueve 'Sin dato' cuando ya hay certeza.",
    ]
    txb = sl.shapes.add_textbox(Emu(BUL_L), Emu(3900000), Emu(BUL_W), Emu(2600000))
    tf = txb.text_frame; tf.word_wrap = True
    for i, item in enumerate(bullets):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(6); p.alignment = PP_ALIGN.LEFT
        run = p.add_run(); run.text = f"•  {item}"
        run.font.size = Pt(11); run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    return sl


# ── Slide genérico: tasa (% Elector / % Elegible) por categoría ────────────
def slide_tasa_por_categoria(prs, df, categorias, col_cat, titulo, subtitulo,
                              chart_title, bullets, fname, wrap_labels=False,
                              mostrar_elegible=True, horizontal=False):
    tab = df.groupby(col_cat).agg(
        n=("rut_key", "size"),
        pct_elector=("elector_bin", "mean"),
        pct_elegible=("elegible_bin", "mean"),
    )
    tab[["pct_elector", "pct_elegible"]] *= 100
    tab = tab.reindex(categorias)

    fig = _new_fig()
    ax = fig.add_axes([CHART_X, CHART_Y, CHART_W, CHART_H], facecolor="none", zorder=5)
    x = np.arange(len(categorias))

    if mostrar_elegible:
        bw = 0.34
        offs = [-0.5 * bw, 0.5 * bw]
    else:
        bw = 0.5
        offs = [0.0]

    n_bajo = tab["n"] < 15
    hatch_e = ["///" if b else None for b in n_bajo]

    bars1 = ax.bar(x + offs[0], tab["pct_elector"], width=bw, color=COL_ELECTOR,
                    alpha=0.92, edgecolor="none", label="% Elector")
    for bar, h in zip(bars1, hatch_e):
        if h: bar.set_hatch(h); bar.set_edgecolor("#0A0F18")
    for xi, v in zip(x + offs[0], tab["pct_elector"]):
        ax.text(xi, v + 2, f"{v:.0f}%", ha="center", va="bottom", fontsize=8.5,
                 fontweight="bold", color=COL_ELECTOR, path_effects=STROKE, zorder=6)

    if mostrar_elegible:
        bars2 = ax.bar(x + offs[1], tab["pct_elegible"], width=bw, color=COL_ELEGIBLE,
                        alpha=0.92, edgecolor="none", label="% Elegible")
        for bar, h in zip(bars2, hatch_e):
            if h: bar.set_hatch(h); bar.set_edgecolor("#0A0F18")
        for xi, v in zip(x + offs[1], tab["pct_elegible"]):
            ax.text(xi, v + 2, f"{v:.0f}%", ha="center", va="bottom", fontsize=8.5,
                     fontweight="bold", color=COL_ELEGIBLE, path_effects=STROKE, zorder=6)

    for xi, n in zip(x, tab["n"]):
        ax.text(xi, -6, f"N°={int(n)}", ha="center", va="top", fontsize=7.5, color="#AAAAAA")

    labels = categorias
    if wrap_labels:
        labels = [c.replace(", ", ",\n").replace(" y ", " y\n", 1) if len(c) > 16 else c for c in categorias]
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8.8, color="white", rotation=(20 if len(categorias) > 6 else 0))
    ax.set_ylabel("%", color="#AAAAAA", fontsize=9)
    _style_ax(ax)
    ax.set_yticks([0, 20, 40, 60, 80, 100])
    if mostrar_elegible:
        ax.legend(fontsize=9, framealpha=0.22, labelcolor="white", facecolor="#101820",
                  edgecolor="#444", loc="upper center", bbox_to_anchor=(0.5, 1.10),
                  ncol=2, borderaxespad=0.4, columnspacing=1.4, handlelength=1.6)

    chart_path = _save_chart(fig, fname)
    sl = _bg_slide(prs)
    sl.shapes.add_picture(chart_path, Emu(0), Emu(0), Emu(SW_EMU), Emu(SH_EMU))
    _add_texts(sl, titulo, subtitulo, chart_title, bullets)
    return sl, tab


# ── Slide genérico: comparación de medias (SAT / EDD) con Welch t-test ─────
def slide_medias_ttest(prs, df, valor_col, titulo, subtitulo, chart_title,
                        fname, escala_label, decimales=2):
    fig = _new_fig()
    panel_w = (CHART_W - 0.06) / 2
    ax1 = fig.add_axes([CHART_X, CHART_Y, panel_w, CHART_H], facecolor="none", zorder=5)
    ax2 = fig.add_axes([CHART_X + panel_w + 0.06, CHART_Y, panel_w, CHART_H], facecolor="none", zorder=5)

    resultados = {}
    for ax, bin_col, color, nombre in [(ax1, "elector_bin", COL_ELECTOR, "Elector"),
                                        (ax2, "elegible_bin", COL_ELEGIBLE, "Elegible")]:
        tag_col = "es_elector" if bin_col == "elector_bin" else "es_elegible"
        sub = df[df[tag_col].isin(["Sí", "Sí (estimado)", "No"])].dropna(subset=[valor_col])
        g1 = sub.loc[sub[bin_col], valor_col]
        g0 = sub.loc[~sub[bin_col], valor_col]
        t, p = stats.ttest_ind(g1, g0, equal_var=False)
        resultados[nombre] = dict(n1=len(g1), n0=len(g0), m1=g1.mean(), m0=g0.mean(), t=t, p=p)

        vmax = max(g1.mean(), g0.mean()) * 1.35
        ax.bar([0], [g1.mean()], width=0.5, color=color, alpha=0.92)
        ax.bar([1], [g0.mean()], width=0.5, color=COL_NO, alpha=0.92)
        ax.text(0, g1.mean() + vmax * 0.03, f"{g1.mean():.{decimales}f}", ha="center",
                fontsize=11, fontweight="bold", color=color, path_effects=STROKE)
        ax.text(1, g0.mean() + vmax * 0.03, f"{g0.mean():.{decimales}f}", ha="center",
                fontsize=11, fontweight="bold", color=COL_NO, path_effects=STROKE)
        ax.set_xticks([0, 1])
        ax.set_xticklabels([f"{nombre}\n(N°={len(g1)})", f"No {nombre.lower()}\n(N°={len(g0)})"],
                            fontsize=9, color="white")
        sig = "significativa" if p < 0.05 else "no significativa"
        ax.set_title(f"{nombre} — p={p:.4f} ({sig})", fontsize=9.5, color="white", pad=10)
        ax.set_ylim(0, vmax)
        ax.set_ylabel(escala_label, color="#AAAAAA", fontsize=8.5)
        ax.tick_params(axis="y", colors="#AAAAAA", labelsize=7.5)
        ax.tick_params(axis="x", length=0)
        for sp in ax.spines.values():
            sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.7)
        ax.yaxis.grid(True, color="white", alpha=0.07, linewidth=0.5)
        ax.set_axisbelow(True)

    chart_path = _save_chart(fig, fname)
    sl = _bg_slide(prs)
    sl.shapes.add_picture(chart_path, Emu(0), Emu(0), Emu(SW_EMU), Emu(SH_EMU))

    r_e, r_g = resultados["Elector"], resultados["Elegible"]
    bullets = [
        f"Elector: {r_e['m1']:.{decimales}f} vs {r_e['m0']:.{decimales}f} (No elector) — "
        f"t={r_e['t']:.2f}, p={r_e['p']:.4f} — "
        f"{'diferencia significativa' if r_e['p'] < 0.05 else 'sin diferencia significativa'}.",
        f"Elegible: {r_g['m1']:.{decimales}f} vs {r_g['m0']:.{decimales}f} (No elegible) — "
        f"t={r_g['t']:.2f}, p={r_g['p']:.4f} — "
        f"{'diferencia significativa' if r_g['p'] < 0.05 else 'sin diferencia significativa'}.",
    ]
    _add_texts(sl, titulo, subtitulo, chart_title, bullets)
    return sl, resultados


# ── Slide: Antigüedad — composición confirmado/estimado/no/sin dato ────────
def slide_antiguedad(prs, df):
    fig = _new_fig()
    panel_w = (CHART_W - 0.06) / 2
    ax1 = fig.add_axes([CHART_X, CHART_Y, panel_w, CHART_H], facecolor="none", zorder=5)
    ax2 = fig.add_axes([CHART_X + panel_w + 0.06, CHART_Y, panel_w, CHART_H], facecolor="none", zorder=5)

    orden_estado = ["Sí", "Sí (estimado)", "No", "Sin dato"]
    colores = {"Sí": COL_ELECTOR, "Sí (estimado)": "#A8CBEA", "No": COL_NO, "Sin dato": COL_SINDATO}

    for ax, col, titulo_panel in [(ax1, "es_elector", "Elector (Art. 2° — 3 años)"),
                                   (ax2, "es_elegible", "Elegible (Art. 4° — 8 años)")]:
        cats = ["JORNADA", "HONORARIO"]
        tab = pd.crosstab(df["tipo_contrato_tag"], df[col])
        tab = tab.reindex(index=cats, columns=orden_estado, fill_value=0)
        pct = tab.div(tab.sum(axis=1), axis=0) * 100
        x = np.arange(len(cats))
        bottom = np.zeros(len(cats))
        for estado in orden_estado:
            vals = pct[estado].values
            ax.bar(x, vals, width=0.5, bottom=bottom, color=colores[estado],
                   alpha=0.92, edgecolor="#0A0F18", linewidth=0.5, label=estado)
            for xi, v, b in zip(x, vals, bottom):
                if v > 6:
                    ax.text(xi, b + v / 2, f"{v:.0f}%", ha="center", va="center",
                             fontsize=8, fontweight="bold", color="white", path_effects=STROKE)
            bottom += vals
        ax.set_xticks(x)
        ax.set_xticklabels([f"Jornada\n(N°={int(tab.loc['JORNADA'].sum())})",
                             f"Honorario\n(N°={int(tab.loc['HONORARIO'].sum())})"],
                            fontsize=9.5, color="white")
        ax.set_title(titulo_panel, fontsize=10, color="white", pad=8)
        ax.set_ylim(0, 100)
        ax.tick_params(axis="y", colors="#AAAAAA", labelsize=7.5)
        ax.tick_params(axis="x", length=0)
        for sp in ax.spines.values():
            sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.7)

    handles, labels = ax1.get_legend_handles_labels()
    # bbox_to_anchor en coords de FIGURA completa (0-1 de toda la diapo, no del
    # chart) — hay que anclarlo justo arriba de los paneles (CHART_Y+CHART_H),
    # si no queda pegado al título de la diapo (bug encontrado 2026-09-14).
    fig.legend(handles, labels, loc="lower center",
               bbox_to_anchor=(0.5, CHART_Y + CHART_H + 0.015),
               ncol=4, fontsize=8.5, framealpha=0.22, labelcolor="white",
               facecolor="#101820", edgecolor="#444")

    chart_path = _save_chart(fig, "antiguedad_composicion.png")
    sl = _bg_slide(prs)
    sl.shapes.add_picture(chart_path, Emu(0), Emu(0), Emu(SW_EMU), Emu(SH_EMU))
    bullets = [
        "'Sí' = confirmado por fecha de ingreso exacta. 'Sí (estimado)' = cota inferior segura por fecha de jerarquización cuando falta la fecha de ingreso (ver D33) — nunca degrada a 'No'.",
        "Honorario concentra la mayor parte del 'Sin dato' — no es un problema de la regla, es que la fuente de dotación (con fecha de ingreso) cubre solo 2.5% de Honorario directamente.",
    ]
    _add_texts(sl, "Antigüedad — Composición del Dato por Tipo de Contrato",
               "Universo: 1.144 docentes (Jornada + Honorario) — analisis.universo_electores (D33)",
               "% de docentes por estado de verificación (confirmado/estimado/no/sin dato), Elector y Elegible",
               bullets)
    return sl


if __name__ == "__main__":
    df = cargar_datos()
    print(f"Universo cargado: {len(df)} docentes")

    prs = Presentation()
    prs.slide_width = Emu(SW_EMU)
    prs.slide_height = Emu(SH_EMU)

    slide_portada(prs, df)

    slide_medias_ttest(
        prs, df, "sat_promedio",
        titulo="SAT — Nota de Satisfacción Estudiantil",
        subtitulo="Universo con SAT válido: 967/1.144 (84.5%, CM-1 cobertura≥40%) — analisis.universo_electores + consolidados.evaluacion_periodo/respuesta",
        chart_title="Nota SAT promedio por docente (escala 1-7), Elector vs No elector y Elegible vs No elegible",
        fname="sat_ttest.png", escala_label="Nota SAT (1-7)", decimales=2,
    )

    slide_antiguedad(prs, df)

    df_jer = df[df["jerarquia"].notna()]
    slide_tasa_por_categoria(
        prs, df_jer, CAT_ORD_JERARQUIA, "jerarquia",
        titulo="Jerarquía — % Elector por Categoría",
        subtitulo="Universo: 1.117/1.144 con jerarquía conocida (D25) — 8 categorías, Docente y Regular",
        chart_title="% de docentes Elector por jerarquía (Elegible solo aplica a categorías Titular, ver D33)",
        bullets=[
            "La tasa de Elector sube con el rango — coherente, jerarquizarse toma tiempo y el requisito de Elector es antigüedad.",
            "'SIN JERARQUÍA' (177 docentes, no graficada) no tiene ningún caso confirmado ni estimado como Elector — no es una exclusión por regla, es que ese grupo tampoco tiene fecha de jerarquización que sirva de cota inferior.",
        ],
        fname="jerarquia_tasa.png", mostrar_elegible=True,
    )

    slide_tasa_por_categoria(
        prs, df, ["HOMBRE", "MUJER"], "sexo",
        titulo="Sexo — % Elector y % Elegible",
        subtitulo="Universo: 1.114/1.144 con sexo registrado (97%) — Jornada + Honorario",
        chart_title="% de docentes Elector y Elegible por sexo",
        bullets=[
            "Hombres muestran una tasa de Elector algo mayor que Mujeres — a confirmar si se sostiene al desagregar por jerarquía/antigüedad (posible variable de confusión).",
        ],
        fname="sexo_tasa.png", mostrar_elegible=True,
    )

    slide_tasa_por_categoria(
        prs, df, FAC_ORD_REALES + [FAC_OTRA], "fac",
        titulo="Facultad — % Elector y % Elegible",
        subtitulo="Universo: 1.144 docentes, 6 categorías (5 facultades reales + Otra/Sin facultad, D32)",
        chart_title="% de docentes Elector y Elegible por facultad",
        bullets=[
            "'Otra / Sin facultad' agrupa 549 docentes (48% del universo) sin una de las 5 facultades académicas reales — mismo criterio D32.",
        ],
        fname="facultad_tasa.png", wrap_labels=True, mostrar_elegible=True,
    )

    df_jornada = df[df["tipo_contrato_tag"] == "JORNADA"].copy()
    bins = [0, 35, 45, 55, 65, 120]
    labels_edad = ["<35", "35-44", "45-54", "55-64", "65+"]
    df_jornada["tramo_edad2"] = pd.cut(df_jornada["edad_anios"], bins=bins, labels=labels_edad)
    df_edad = df_jornada[df_jornada["tramo_edad2"].notna()]
    slide_tasa_por_categoria(
        prs, df_edad, labels_edad, "tramo_edad2",
        titulo="Edad — % Elector y % Elegible (Jornada)",
        subtitulo="Alcance Jornada — Honorario tiene 2.5% de cobertura de edad, no se puede graficar de forma confiable (ver D34)",
        chart_title="% de docentes Elector y Elegible por tramo de edad, universo Jornada (534/624 con edad conocida)",
        bullets=[
            "La tasa de Elector sube consistentemente con la edad — mismo patrón que jerarquía, coherente con que ambos correlacionan con antigüedad.",
        ],
        fname="edad_tasa.png", mostrar_elegible=True,
    )

    slide_medias_ttest(
        prs, df_jornada, "edd_promedio",
        titulo="Evaluación de Jefaturas (EDD) — Jornada",
        subtitulo="Alcance Jornada — Honorario tiene 2.3% de cobertura de EDD (no tiene jefe evaluador asignado), no aplica (ver D34)",
        chart_title="EDD total promedio por docente, Elector vs No elector y Elegible vs No elegible (universo Jornada)",
        fname="edd_ttest.png", escala_label="EDD total (escala D28)", decimales=3,
    )

    prs.save(OUT_PPTX)
    print(f"\n✓ Guardado: {OUT_PPTX} ({len(prs.slides)} diapositivas)")
