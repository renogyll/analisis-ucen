"""
P1 — Caracterización del Cuerpo Académico de Planta
Calificación EDD (Evaluación de Desempeño Docente) según Facultad — Jornada.

EDD = evaluación hecha por la jefatura/director (D28), distinta de la evaluación
estudiantil. A diferencia de sexo/jerarquía, `facultad_jefe` SÍ puede variar entre
años para un mismo docente (confirmado: 61/491 docentes Jornada con más de un
valor distinto entre 2022-2025 — el docente cambió de unidad, o distintas
evaluaciones fueron hechas por distintas jefaturas). Por eso, para agrupar por
facultad se usa la "facultad predominante" por docente (la que más veces aparece
en sus años evaluados) — misma extensión del criterio "grupo predominante" que
D27 usa para atributos que pueden variar por instancia.

Facultad tiene 6 categorías (no es binaria), así que la prueba t no puede ser una
sola comparación de 2 grupos como en sexo/jerarquía: se hacen 6 pruebas t de
Welch, una por facultad, cada una comparando esa facultad contra el resto
combinado (mismo criterio "grupo vs. resto" que sexo_dificultad/ usa para Baja
vs. Media+Alta). Cada barra del gráfico de prueba t se colorea según si su
diferencia es significativa al 5% o no.

FUENTE: intel.evaluacion_jefes (Postgres, en vivo)
        + data/cascade/01_jornada/docentes_jornada.csv (universo de RUTs)
SALIDA: P1_edd_facultad.pptx (2 diapositivas) + edd_facultad_chart.png
        + edd_facultad_ttest_chart.png
"""
import sys; sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "shared"))
from config import CASCADE, OUTPUTS
from pptx_helpers import UcenSlideKit

import numpy as np
import pandas as pd
import matplotlib.patheffects as pe
from scipy import stats
from sqlalchemy import create_engine, text
from pptx import Presentation
from pptx.util import Emu

HERE = Path(__file__).parent
OUT_PPTX = Path(OUTPUTS) / "pptx" / "P1_edd_facultad.pptx"
OUT_PPTX.parent.mkdir(parents=True, exist_ok=True)

DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"

# Ramp secuencial azul claro→oscuro, 6 pasos, interpolada entre los extremos ya
# usados en el resto de P1 (#AFCBE8 → #1F5C99) — mismo criterio de "magnitud
# ordenada" que edad_jerarquia/edd_jerarquia, no identidad categórica (facultad
# no tiene un orden intrínseco, así que el color codifica el ranking del gráfico).
def _blue_ramp(n):
    lo = np.array([0xAF, 0xCB, 0xE8])
    hi = np.array([0x1F, 0x5C, 0x99])
    steps = [lo + (hi - lo) * i / (n - 1) for i in range(n)]
    return [f"#{int(r):02X}{int(g):02X}{int(b):02X}" for r, g, b in steps]

COL_SIGNIF = "#F2D675"     # mismo dorado usado para resaltar significancia en el resto de P1
COL_NO_SIGNIF = "#4E8FC9"

# ── Datos: facultad predominante por docente + promedio de edd_total ──────────
doc = pd.read_csv(Path(CASCADE) / "01_jornada" / "docentes_jornada.csv", encoding="utf-8-sig")
N_JORNADA = len(doc)

engine = create_engine(DB_URL)
q = text("""
    SELECT rut_key, facultad_jefe, edd_total
    FROM intel.evaluacion_jefes
    WHERE tipo_contrato_tag = 'JORNADA' AND facultad_jefe IS NOT NULL AND edd_total IS NOT NULL
""")
with engine.connect() as conn:
    raw = pd.read_sql(q, conn)

N_TOTAL_EDD_DOC = int(pd.read_sql(text("""
    SELECT COUNT(DISTINCT rut_key) AS n FROM intel.evaluacion_jefes
    WHERE tipo_contrato_tag = 'JORNADA'
"""), engine).iloc[0, 0])

# Facultad predominante = la que más veces aparece entre los años evaluados del docente
conteo = raw.groupby(["rut_key", "facultad_jefe"]).size().reset_index(name="n_registros")
idx_predominante = conteo.groupby("rut_key")["n_registros"].idxmax()
predominante = conteo.loc[idx_predominante, ["rut_key", "facultad_jefe"]] \
    .rename(columns={"facultad_jefe": "facultad_predominante"})
edd_doc = raw.groupby("rut_key")["edd_total"].mean().reset_index(name="edd_prom")
por_docente = predominante.merge(edd_doc, on="rut_key")

N_SIN_DATO = N_TOTAL_EDD_DOC - len(por_docente)
N_FACULTAD_CAMBIO = int((conteo.groupby("rut_key")["facultad_jefe"].nunique() > 1).sum())

tab = (por_docente.groupby("facultad_predominante")["edd_prom"].agg(edd_prom="mean", n="count")
       .sort_values("edd_prom", ascending=False))
FAC_DISPLAY = tab.index.tolist()
COLORS = dict(zip(FAC_DISPLAY, _blue_ramp(len(FAC_DISPLAY))))

print(f"Universo Jornada: {N_JORNADA}  |  docentes con EDD+facultad válidas: {len(por_docente)}  |  "
      f"excluidos: {N_SIN_DATO}  |  con facultad predominante ambigua (cambió de facultad): "
      f"{N_FACULTAD_CAMBIO}")
print(tab)

fac_mayor = tab["edd_prom"].idxmax()
fac_menor = tab["edd_prom"].idxmin()

# ── Prueba t: cada facultad vs. el resto combinado (Welch, 6 comparaciones) ───
resultados = []
for fac in FAC_DISPLAY:
    grupo = por_docente.loc[por_docente["facultad_predominante"] == fac, "edd_prom"]
    resto = por_docente.loc[por_docente["facultad_predominante"] != fac, "edd_prom"]
    t_stat, p_val = stats.ttest_ind(grupo, resto, equal_var=False)
    resultados.append({
        "facultad": fac, "media_grupo": grupo.mean(), "media_resto": resto.mean(),
        "diferencia": grupo.mean() - resto.mean(), "n_grupo": len(grupo),
        "t": t_stat, "p": p_val, "signif": p_val < 0.05,
    })
res = pd.DataFrame(resultados).set_index("facultad").reindex(FAC_DISPLAY)

print("\nPrueba t por facultad (vs. resto combinado):")
print(res[["media_grupo", "media_resto", "diferencia", "n_grupo", "t", "p", "signif"]])

facs_signif = res.index[res["signif"]].tolist()


def agregar(prs):
    """Construye el gráfico descriptivo (6 facultades) y agrega la diapositiva a `prs`."""
    kit = UcenSlideKit(out_dir=HERE)
    kit.ensure_bg()

    fig = kit.new_chart_fig()
    ax = kit.chart_axes(fig, left=0.20)

    y = np.arange(len(FAC_DISPLAY))
    colors = [COLORS[f] for f in FAC_DISPLAY]

    ax.barh(y, tab["edd_prom"], height=0.6, color=colors, alpha=0.92, edgecolor="none", zorder=3)

    stroke = [pe.withStroke(linewidth=2, foreground="#0A0F18")]
    for i, (v, n) in enumerate(zip(tab["edd_prom"], tab["n"])):
        ax.text(v + 0.015, i, f"{v:.2f}   (N°={int(n)} docentes)",
                 ha="left", va="center", fontsize=9.5, fontweight="bold",
                 color=colors[i], path_effects=stroke, zorder=6)

    ax.set_yticks(y)
    ax.set_yticklabels(FAC_DISPLAY, fontsize=11, color="white")
    ax.invert_yaxis()
    ax.set_xlabel("Calificación EDD promedio (escala 0-1)", color="#AAAAAA", fontsize=9)
    ax.set_xlim(0, tab["edd_prom"].max() * 1.30)
    ax.tick_params(axis="y", length=0, pad=8)
    ax.tick_params(axis="x", colors="#AAAAAA", labelsize=8.5)
    for sp in ax.spines.values():
        sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.7)
    ax.xaxis.grid(True, color="white", alpha=0.07, linewidth=0.5)
    ax.set_axisbelow(True)

    chart_path = kit.save_chart(fig, "edd_facultad_chart.png")

    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.pic_chart(sl, prs, chart_path)
    kit.title(sl, "Calificación EDD según Facultad — Docentes de Jornada")
    kit.subtitulo(sl,
        f"Universo: {N_JORNADA} docentes Jornada  ·  "
        f"N°={len(por_docente)} con evaluación de desempeño (EDD) y facultad registradas")
    kit.notas(sl,
        f"{N_SIN_DATO} docentes con registro EDD excluidos por falta de facultad_jefe o "
        f"edd_total válido. {N_FACULTAD_CAMBIO} docentes cambiaron de facultad_jefe entre años "
        f"(2022-2025) — se les asigna su facultad predominante (la más frecuente entre sus años "
        f"evaluados). EDD = Evaluación de Desempeño Docente, hecha por la jefatura/director "
        f"(D28). Unidad de análisis: promedio de edd_total por docente entre los años con "
        f"evaluación registrada. Fuente: intel.evaluacion_jefes.")
    kit.punteo_numerado(sl, [
        f"{fac_mayor} tiene la calificación EDD promedio más alta "
        f"({tab.loc[fac_mayor,'edd_prom']:.2f}, N°={int(tab.loc[fac_mayor,'n'])}), y {fac_menor} "
        f"la más baja ({tab.loc[fac_menor,'edd_prom']:.2f}, N°={int(tab.loc[fac_menor,'n'])}).",
        "Ver pruebas de significancia (cada facultad vs. el resto) en la siguiente diapositiva.",
    ])
    return sl


def agregar_ttest(prs):
    """Construye el gráfico de las 6 pruebas t (cada facultad vs. el resto combinado)
    y agrega la diapositiva a `prs`."""
    kit = UcenSlideKit(out_dir=HERE)
    kit.ensure_bg()

    fig = kit.new_chart_fig()
    ax = kit.chart_axes(fig, top=0.14, bottom=0.14)

    x = np.arange(len(FAC_DISPLAY))
    colors = [COL_SIGNIF if s else COL_NO_SIGNIF for s in res["signif"]]
    ax.bar(x, res["diferencia"], width=0.55, color=colors, alpha=0.92, edgecolor="none", zorder=3)
    ax.axhline(0, color="white", alpha=0.35, linewidth=0.8)

    ymax = max(abs(res["diferencia"].min()), abs(res["diferencia"].max())) * 1.9

    stroke = [pe.withStroke(linewidth=2, foreground="#0A0F18")]
    for xi, d, p, n, color in zip(x, res["diferencia"], res["p"], res["n_grupo"], colors):
        va = "bottom" if d >= 0 else "top"
        offset = 0.012 if d >= 0 else -0.012
        marca = "*" if p < 0.05 else ""
        ax.text(xi, d + offset, f"{d:+.2f}{marca}", ha="center", va=va,
                 fontsize=10.5, fontweight="bold", color=color, path_effects=stroke, zorder=6)
        # N° siempre en una franja fija cerca del piso del gráfico (no pegado a la barra) —
        # con barras casi nulas (ej. FED, diferencia≈0), pegarlo a la barra choca con la
        # etiqueta de valor.
        ax.text(xi, -ymax * 0.85, f"N°={int(n)}", ha="center", va="center",
                 fontsize=7.5, color="white", alpha=0.85)

    ax.text(0.5, 0.99, "Prueba t de Welch por facultad, cada una vs. el resto combinado  ·  "
            "* = diferencia significativa al 5%", transform=ax.transAxes, ha="center", va="top",
            fontsize=9, color="#F2D675", fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(FAC_DISPLAY, fontsize=10, color="white")
    ax.set_ylabel("Diferencia EDD vs. resto (puntos, escala 0-1)", color="#AAAAAA", fontsize=9)
    ax.set_ylim(-ymax, ymax)
    ax.tick_params(axis="x", length=0, pad=8)
    ax.tick_params(axis="y", colors="#AAAAAA", labelsize=8.5)
    for sp in ax.spines.values():
        sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.7)
    ax.yaxis.grid(True, color="white", alpha=0.07, linewidth=0.5)
    ax.set_axisbelow(True)

    chart_path = kit.save_chart(fig, "edd_facultad_ttest_chart.png")

    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.pic_chart(sl, prs, chart_path)
    kit.title(sl, "¿La facultad influye en la calificación EDD? — Prueba t, Jornada")
    kit.subtitulo(sl,
        f"Unidad de análisis: 1 valor por docente (promedio de edd_total entre años), agrupado "
        f"por facultad predominante  ·  N°={len(por_docente)} docentes  ·  "
        f"6 pruebas t de Welch, cada facultad vs. el resto")
    kit.notas(sl,
        "Facultad predominante = la que más veces aparece entre los años evaluados del "
        "docente (puede variar entre años, a diferencia de sexo/jerarquía). Cada barra compara "
        "esa facultad contra el resto combinado, no contra las otras 5 por separado.")
    if facs_signif:
        nombres = ", ".join(facs_signif)
        bullets = [
            f"{nombres} muestra{'n' if len(facs_signif) > 1 else ''} una diferencia "
            f"estadísticamente significativa al 5% frente al resto de las facultades.",
        ]
        for fac in facs_signif:
            r = res.loc[fac]
            direccion = "más alta" if r["diferencia"] > 0 else "más baja"
            bullets.append(
                f"{fac}: calificación EDD promedio {r['media_grupo']:.2f} vs "
                f"{r['media_resto']:.2f} en el resto ({direccion}, diferencia de "
                f"{r['diferencia']:+.2f}, p={r['p']:.4f})."
            )
    else:
        bullets = ["Ninguna facultad muestra una diferencia estadísticamente significativa "
                   "al 5% frente al resto — las diferencias descriptivas de la diapositiva "
                   "anterior no se sostienen como hallazgo robusto."]
    kit.punteo_numerado(sl, bullets)
    return sl


if __name__ == "__main__":
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(UcenSlideKit.SW_EMU), Emu(UcenSlideKit.SH_EMU)
    agregar(prs)
    agregar_ttest(prs)
    prs.save(OUT_PPTX)
    print(f"\n✓ Guardado: {OUT_PPTX}")
