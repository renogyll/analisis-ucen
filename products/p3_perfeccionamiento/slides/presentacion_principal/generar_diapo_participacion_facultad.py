"""
Standalone: genera DIAPO_participacion_facultad.pptx (2 diapositivas) —
Participación en instancias formativas, Formados vs No formados, 100% apilado.

Pedido de la contraparte (2026-08-14): la versión anterior (4 barras por
facultad, desagregada por tipo de formación — Taller/Diplomado/Proyecto) fue
rechazada. Nueva versión, 2 diapositivas, cada una con una sola barra 100%
apilada Formados/No formados por categoría de eje X:
  - Diapo 1: eje X = año del evento (2023, 2024, 2025).
  - Diapo 2: eje X = Facultad.

"Formados" = docente con ≥1 instancia de formación registrada en
analisis.universo_formados_p3 (cualquier tipo: Taller/Diplomado/Proyecto) —
no se filtra por apto_p3, mismo criterio que la versión anterior y que D31
de P1. Universo: TODOS los docentes de analisis.universo_base — Jornada +
Honorario combinados (a diferencia de la versión anterior, que separaba en
2 diapos por tipo de contrato; la contraparte pidió solo 2 diapos en total,
ya no 2 por tipo de contrato).

En la diapo por año, el universo (denominador) es el mismo total fijo de
docentes en las 3 barras — lo que cambia es si tuvieron una instancia de
formación CON anio_evento igual a ese año (independiente entre años, un
docente puede contar en más de un año).

Normalización de facultad: misma función fac_norm() ya usada en la versión
anterior (5 facultades académicas reales + "Otra / Sin facultad" para el
resto — incluye NaN y unidades centrales como Vicerrectorías, Junta
Directiva, Sede La Serena, etc. — a pedido explícito de la contraparte,
para no perder esos docentes del todo).

FUENTE: analisis.universo_base + analisis.universo_formados_p3 (Postgres, en vivo)
SALIDA: DIAPO_participacion_facultad.pptx (2 diapositivas)
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

# ── Rutas (mismo patrón que generar_diapo_combinaciones.py) ───────────────────
BASE      = os.path.dirname(os.path.abspath(__file__))
REPO      = str(pathlib.Path(BASE).parents[3])
SCRATCH   = os.path.join(REPO, "outputs", "scratch")
OUT_DIR   = os.path.join(BASE, "dark_slides_v3")
FONDOTIPO = os.path.join(REPO, "assets", "Fondotipop.pptx")

BG_PATH   = os.path.join(SCRATCH, "fondotipo_image1.jpg")
LOGO_PATH = os.path.join(SCRATCH, "fondotipo_image2.png")
SHARED_BG = os.path.join(OUT_DIR, "_background.png")
OUT_PPTX  = r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO\Downloads\DIAPO_participacion_facultad.pptx"

os.makedirs(OUT_DIR, exist_ok=True)
for path, zname in [(BG_PATH, "ppt/media/image1.jpg"), (LOGO_PATH, "ppt/media/image2.png")]:
    if not os.path.exists(path):
        with zipfile.ZipFile(FONDOTIPO) as z:
            with open(path, "wb") as f:
                f.write(z.read(zname))

# ── Constantes de layout (idénticas a generar_diapo_combinaciones.py) ─────────
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

# Par binario ya reservado en todo el proyecto para Participó/No participó
COL_FORMADO = "#5C9BD6"
COL_NO_FORMADO = "#FFB74D"

FAC_ORD_REALES = ["Medicina y C. Salud", "Ingeniería y Arq.", "Educación",
                   "Economía, Gob. y Com.", "Derecho y Humanidades"]
FAC_OTRA = "Otra / Sin facultad"

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
    lh, lw = logo_arr.shape[:2]
    lx = _ex(LOGO_L); ly = 1 - _ey(LOGO_T) - _ey(LOGO_H)
    ax_bg.imshow(logo_arr, aspect="auto", extent=[lx, lx + _ex(LOGO_W), ly, ly + _ey(LOGO_H)])
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


# ── Datos ───────────────────────────────────────────────────────────────────
DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"
engine = create_engine(DB_URL)


def cargar_base():
    base = pd.read_sql(text("SELECT rut_key, unidad_facultad FROM analisis.universo_base"), engine)
    base["fac"] = base["unidad_facultad"].apply(fac_norm)
    form = pd.read_sql(text("SELECT rut_key, anio_evento FROM analisis.universo_formados_p3"), engine)
    return base, form


def tabla_por_anio(base, form, anios=("2023", "2024", "2025")):
    n_total = len(base)
    rows = []
    for a in anios:
        ruts_anio = set(form.loc[form["anio_evento"] == a, "rut_key"])
        n_formado = int(base["rut_key"].isin(ruts_anio).sum())
        rows.append({"cat": a, "n": n_total, "n_formado": n_formado,
                      "n_no_formado": n_total - n_formado})
    tab = pd.DataFrame(rows).set_index("cat")
    tab["pct_formado"] = tab["n_formado"] / tab["n"] * 100
    tab["pct_no_formado"] = 100 - tab["pct_formado"]
    return tab


def tabla_por_facultad(base, form):
    ruts_formados = set(form["rut_key"])
    b = base.copy()
    b["formado"] = b["rut_key"].isin(ruts_formados)
    tab = b.groupby("fac").agg(n=("rut_key", "size"), n_formado=("formado", "sum"))
    tab["n_no_formado"] = tab["n"] - tab["n_formado"]
    tab["pct_formado"] = tab["n_formado"] / tab["n"] * 100
    tab["pct_no_formado"] = 100 - tab["pct_formado"]

    orden = [f for f in FAC_ORD_REALES if f in tab.index]
    orden = sorted(orden, key=lambda f: -tab.loc[f, "n"])
    if FAC_OTRA in tab.index:
        orden.append(FAC_OTRA)
    tab = tab.reindex(orden)
    tab.index.name = "cat"
    return tab


def construir_slide(prs, tab, titulo, subtitulo, chart_title, bullets,
                     fname_suffix, wrap_labels=False):
    fig = plt.figure(figsize=(SW, SH), facecolor="none")
    fig.patch.set_facecolor("none")
    ax = fig.add_axes([CHART_X, CHART_Y, CHART_W, CHART_H], facecolor="none", zorder=5)

    cats = tab.index.tolist()
    x = np.arange(len(cats))
    bw = 0.46
    stroke = [pe.withStroke(linewidth=1.6, foreground="#0A0F18")]

    pf, pnf, ns = tab["pct_formado"], tab["pct_no_formado"], tab["n"]

    ax.bar(x, pf, width=bw, color=COL_FORMADO, alpha=0.92, edgecolor="none", label="Formados")
    ax.bar(x, pnf, width=bw, bottom=pf, color=COL_NO_FORMADO, alpha=0.92,
           edgecolor="none", label="No formados")

    for xi, p, n in zip(x, pf, pnf):
        ax.text(xi, p / 2, f"{p:.0f}%", ha="center", va="center", fontsize=11,
                 fontweight="bold", color="white", path_effects=stroke, zorder=6)
        if n > 4:
            ax.text(xi, p + n / 2, f"{n:.0f}%", ha="center", va="center", fontsize=10,
                     fontweight="bold", color="#3A2A00", zorder=6)

    for xi, nn in zip(x, ns):
        ax.text(xi, -6, f"N°={int(nn)}", ha="center", va="top", fontsize=8.5, color="#AAAAAA")

    labels = cats
    if wrap_labels:
        labels = [c.replace(", ", ",\n").replace(" y ", " y\n", 1) if len(c) > 16 else c
                  for c in cats]
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10.5, color="white")
    ax.set_ylabel("% de docentes", color="#AAAAAA", fontsize=9)
    ax.set_ylim(-10, 112)
    ax.set_yticks([0, 20, 40, 60, 80, 100])
    ax.tick_params(axis="x", length=0, pad=10)
    ax.tick_params(axis="y", colors="#AAAAAA", labelsize=8)
    for sp in ax.spines.values():
        sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.7)
    ax.yaxis.grid(True, color="white", alpha=0.07, linewidth=0.5)
    ax.set_axisbelow(True)
    ax.legend(fontsize=9, framealpha=0.22, labelcolor="white", facecolor="#101820",
              edgecolor="#444", loc="upper center", bbox_to_anchor=(0.5, 1.11),
              ncol=2, borderaxespad=0.4, columnspacing=1.4, handlelength=1.6)

    chart_path = os.path.join(OUT_DIR, f"participacion_facultad_{fname_suffix}_chart.png")
    fig.savefig(chart_path, dpi=150, facecolor="none", transparent=True)
    plt.close(fig)

    sl = prs.slides.add_slide(prs.slide_layouts[6])
    sl.shapes.add_picture(SHARED_BG, Emu(0), Emu(0), Emu(SW_EMU), Emu(SH_EMU))
    sl.shapes.add_picture(chart_path, Emu(0), Emu(0), Emu(SW_EMU), Emu(SH_EMU))

    _txt(sl, titulo, TITLE_L, TITLE_T, TITLE_W, TITLE_H, fs=18, bold=True,
         color="#FFFFFF", align=PP_ALIGN.CENTER)
    _txt(sl, subtitulo, POP_L, POP_T, POP_W, POP_H, fs=8, italic=True, color="#C8DCF0")
    _txt(sl, chart_title, CTITLE_L, CTITLE_T, CTITLE_W, CTITLE_H, fs=9, color="#FFFFFF")

    txb = sl.shapes.add_textbox(Emu(BUL_L), Emu(BUL_T), Emu(BUL_W), Emu(BUL_H))
    tf = txb.text_frame; tf.word_wrap = True
    for i, item in enumerate(bullets):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(5); p.alignment = PP_ALIGN.LEFT
        run = p.add_run()
        run.text = f"•  {item}"
        run.font.size = Pt(11)
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    return sl


if __name__ == "__main__":
    prs = Presentation()
    prs.slide_width = Emu(SW_EMU)
    prs.slide_height = Emu(SH_EMU)

    base, form = cargar_base()
    n_total = len(base)

    # ── Diapo 1 — por año ──────────────────────────────────────────────────
    tab_anio = tabla_por_anio(base, form)
    print("\n--- Por año ---"); print(tab_anio.round(1))

    p0, p1 = tab_anio["pct_formado"].iloc[0], tab_anio["pct_formado"].iloc[-1]
    a0, a1 = tab_anio.index[0], tab_anio.index[-1]
    verbo = "aumentó" if p1 > p0 else "disminuyó"
    bullets_anio = [
        f"La participación en instancias formativas {verbo} de {p0:.0f}% en {a0} a "
        f"{p1:.0f}% en {a1}, sobre un universo fijo de {n_total} docentes.",
        f"{a1} concentra la mayor proporción de docentes formados en un solo año "
        f"({tab_anio['pct_formado'].max():.0f}%, N°={int(tab_anio.loc[a1,'n_formado'])}).",
    ]
    construir_slide(
        prs, tab_anio,
        titulo="Participación en Instancias Formativas por Año",
        subtitulo=f"Universo: {n_total} docentes (Jornada + Honorario)  ·  "
                  f"Formados = con ≥1 instancia registrada ese año  ·  todos los formados (no solo Aptos P3)",
        chart_title="% de docentes con ≥1 instancia de formación registrada en el año, sobre el universo total",
        bullets=bullets_anio,
        fname_suffix="anio",
    )

    # ── Diapo 2 — por facultad ─────────────────────────────────────────────
    tab_fac = tabla_por_facultad(base, form)
    print("\n--- Por facultad ---"); print(tab_fac.round(1))

    fac_mayor = tab_fac["pct_formado"].idxmax()
    fac_menor = tab_fac["pct_formado"].idxmin()
    bullets_fac = [
        f"{fac_mayor} tiene la mayor tasa de participación "
        f"({tab_fac.loc[fac_mayor,'pct_formado']:.0f}%, N°={int(tab_fac.loc[fac_mayor,'n'])}), y "
        f"{fac_menor} la más baja ({tab_fac.loc[fac_menor,'pct_formado']:.0f}%, "
        f"N°={int(tab_fac.loc[fac_menor,'n'])}).",
        f"Universo total: {n_total} docentes, consolidado 2022-2025 sin distinguir por año.",
    ]
    construir_slide(
        prs, tab_fac,
        titulo="Participación en Instancias Formativas por Facultad",
        subtitulo=f"Universo: {n_total} docentes (Jornada + Honorario)  ·  "
                  f"Formados = con ≥1 instancia registrada  ·  todos los formados (no solo Aptos P3)",
        chart_title="% de docentes con ≥1 instancia de formación registrada, por facultad, sobre el universo de esa facultad",
        bullets=bullets_fac,
        fname_suffix="facultad",
        wrap_labels=True,
    )

    prs.save(OUT_PPTX)
    print(f"\n✓ Guardado: {OUT_PPTX}")
