"""
P1 — Caracterización del Cuerpo Académico de Planta
Jerarquía (Escalafón) de los Docentes según Grupo de Dificultad de Asignatura — Jornada.

Mismo patrón que antiguedad_dificultad/ (ver ese script y
docs/DECISIONES_METODOLOGICAS.md D27 para el detalle metodológico completo). Usa
escalafón (Docente vs Regular) en vez del cruce completo de 8 categorías D25 —
mismo criterio de colapso que aprobacion_reprobacion_jerarquia/, porque jerarquía
no es continua y el escalafón es la única partición binaria natural para una
prueba t. La jerarquía es un atributo fijo del docente (no varía por instancia),
así que la prueba t usa "grupo de dificultad predominante" por docente, codificando
escalafón como binario (Regular=1/Docente=0).

FUENTE: intel.rendimiento_academico_alumnos (Postgres, en vivo)
        + data/cascade/01_jornada/docentes_jornada.csv (universo de RUTs)
SALIDA: P1_jerarquia_dificultad.pptx (2 diapositivas) + jerarquia_dificultad_chart.png
        + jerarquia_dificultad_ttest_chart.png
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
OUT_PPTX = Path(OUTPUTS) / "pptx" / "P1_jerarquia_dificultad.pptx"
OUT_PPTX.parent.mkdir(parents=True, exist_ok=True)

DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"
GRUPOS_ORD = ["Baja", "Media", "Alta"]
COL_DOCENTE = "#5C9BD6"   # mismo par usado en el resto de P1 (aprobacion_reprobacion_jerarquia)
COL_REGULAR = "#FFB74D"
CAT_VALIDAS = ("INSTRUCTOR DOCENTE", "INSTRUCTOR REGULAR", "ASISTENTE DOCENTE",
               "ASISTENTE REGULAR", "ASOCIADO DOCENTE", "ASOCIADO REGULAR",
               "TITULAR DOCENTE", "TITULAR REGULAR")

# ── Datos ───────────────────────────────────────────────────────────────────
doc = pd.read_csv(Path(CASCADE) / "01_jornada" / "docentes_jornada.csv", encoding="utf-8-sig")
N_JORNADA = len(doc)

engine = create_engine(DB_URL)
q = text("""
    SELECT grupo_dificultad,
           COUNT(*) AS n_instancias,
           COUNT(DISTINCT rut_docente) AS n_docentes,
           100.0 * AVG((jerarquia LIKE '%REGULAR')::int) AS pct_regular
    FROM intel.rendimiento_academico_alumnos
    WHERE tipo_contrato_tag = 'JORNADA' AND grupo_dificultad IS NOT NULL
      AND jerarquia IN :cats
    GROUP BY grupo_dificultad
""")
with engine.connect() as conn:
    tab = pd.read_sql(q, conn, params={"cats": CAT_VALIDAS}).set_index("grupo_dificultad").reindex(GRUPOS_ORD)
tab["pct_docente"] = 100 - tab["pct_regular"]

N_SIN_JERARQUIA = int(pd.read_sql(text("""
    SELECT COUNT(*) AS n FROM intel.rendimiento_academico_alumnos
    WHERE tipo_contrato_tag='JORNADA' AND grupo_dificultad IS NOT NULL
      AND (jerarquia IS NULL OR jerarquia NOT IN :cats)
"""), engine, params={"cats": CAT_VALIDAS}).iloc[0, 0])

print(f"Universo Jornada: {N_JORNADA}")
print(tab)
print(f"Instancias sin jerarquía válida: {N_SIN_JERARQUIA}")

grupo_mayor = tab["pct_regular"].idxmax()
grupo_menor = tab["pct_regular"].idxmin()
diferencia = tab.loc[grupo_mayor, "pct_regular"] - tab.loc[grupo_menor, "pct_regular"]

# ── Datos para la prueba t: grupo de dificultad PREDOMINANTE por docente (la
# jerarquía es un atributo fijo, no varía por instancia — ver D27) ─────────────
q2 = text("""
    SELECT rut_docente, jerarquia, grupo_dificultad
    FROM intel.rendimiento_academico_alumnos
    WHERE tipo_contrato_tag = 'JORNADA' AND grupo_dificultad IS NOT NULL
      AND jerarquia IN :cats
""")
with engine.connect() as conn:
    raw_doc = pd.read_sql(q2, conn, params={"cats": CAT_VALIDAS})

conteo = raw_doc.groupby(["rut_docente", "grupo_dificultad"]).size().reset_index(name="n")
idx_predominante = conteo.groupby("rut_docente")["n"].idxmax()
predominante = conteo.loc[idx_predominante, ["rut_docente", "grupo_dificultad"]] \
    .rename(columns={"grupo_dificultad": "grupo_predominante"})
jer_doc = raw_doc.drop_duplicates("rut_docente")[["rut_docente", "jerarquia"]].copy()
jer_doc["es_regular"] = jer_doc["jerarquia"].str.contains("REGULAR").astype(int)
por_docente = predominante.merge(jer_doc, on="rut_docente")

grupo_baja = por_docente.loc[por_docente["grupo_predominante"] == "Baja", "es_regular"]
grupo_resto = por_docente.loc[por_docente["grupo_predominante"] != "Baja", "es_regular"]
T_STAT, P_VAL = stats.ttest_ind(grupo_baja, grupo_resto, equal_var=False)   # Welch
# Revisión 2026-09-26 (obs. 6): no va como diapositiva (no significativa), pero sí en la tabla
# resumen de pruebas del anexo, para no ocultar resultados no significativos.
from pptx_helpers import prueba_dict
PRUEBAS = [prueba_dict("IV · Aprobación", "% escalafón Regular: grupo predominante Baja vs Media+Alta",
                       f"{100 * grupo_baja.mean():.1f}% vs {100 * grupo_resto.mean():.1f}%",
                       len(grupo_baja) + len(grupo_resto), P_VAL)]

print(f"\nPrueba t (por docente, grupo predominante Baja vs Media+Alta, %Regular): "
      f"Baja N°={len(grupo_baja)} %regular={100*grupo_baja.mean():.1f}  "
      f"Resto N°={len(grupo_resto)} %regular={100*grupo_resto.mean():.1f}  t={T_STAT:.3f}  p={P_VAL:.4f}")


def agregar(prs):
    """Construye el gráfico descriptivo (barra 100% apilada Docente/Regular) y
    agrega la diapositiva a `prs`."""
    kit = UcenSlideKit(out_dir=HERE)
    kit.ensure_bg()

    fig = kit.new_chart_fig()
    ax = kit.chart_axes(fig, top=0.15)   # deja espacio arriba para la leyenda

    x = np.arange(len(GRUPOS_ORD))
    w = 0.45
    ax.bar(x, tab["pct_docente"], width=w, color=COL_DOCENTE, alpha=0.92,
           edgecolor="none", label="Docente")
    ax.bar(x, tab["pct_regular"], width=w, bottom=tab["pct_docente"],
           color=COL_REGULAR, alpha=0.92, edgecolor="none", label="Regular")

    stroke = [pe.withStroke(linewidth=1.8, foreground="#0A0F18")]
    for xi, d, r in zip(x, tab["pct_docente"], tab["pct_regular"]):
        ax.text(xi, d / 2, f"{d:.0f}%", ha="center", va="center",
                 fontsize=11, fontweight="bold", color="white", path_effects=stroke, zorder=6)
        # El segmento Regular es angosto (7-11%) — la etiqueta va arriba de la barra,
        # no centrada adentro, para que no se corte ni se superponga.
        ax.text(xi, 101.5, f"Regular {r:.0f}%", ha="center", va="bottom",
                 fontsize=9.5, fontweight="bold", color=COL_REGULAR,
                 path_effects=stroke, zorder=6)
    for xi, n in zip(x, tab["n_docentes"]):
        ax.text(xi, 4, f"N°={int(n)} docentes", ha="center", va="bottom",
                 fontsize=8, color="white", alpha=0.85)

    ax.set_xticks(x)
    ax.set_xticklabels([f"{g} aprobación" for g in GRUPOS_ORD], fontsize=12, color="white")
    ax.set_xlabel("Grupo de dificultad de la asignatura", color="#AAAAAA", fontsize=9)
    ax.set_ylabel("% de docentes (Docente / Regular)", color="#AAAAAA", fontsize=9)
    ax.set_ylim(0, 112)
    ax.set_yticks([0, 20, 40, 60, 80, 100])
    ax.tick_params(axis="x", length=0, pad=8)
    ax.tick_params(axis="y", colors="#AAAAAA", labelsize=8.5)
    for sp in ax.spines.values():
        sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.7)
    ax.yaxis.grid(True, color="white", alpha=0.07, linewidth=0.5)
    ax.set_axisbelow(True)
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, fontsize=9, framealpha=0.22, labelcolor="white",
               facecolor="#101820", edgecolor="#444", loc="upper center",
               bbox_to_anchor=(0.5, 0.99), ncol=2)

    chart_path = kit.save_chart(fig, "jerarquia_dificultad_chart.png")

    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.pic_chart(sl, prs, chart_path)
    kit.title(sl, "Jerarquía (Escalafón) de los Docentes según Grupo de Dificultad — Jornada")
    kit.subtitulo(sl,
        f"Universo: {N_JORNADA} docentes Jornada  ·  "
        f"N°={int(tab['n_instancias'].sum()):,} instancias con jerarquía válida")
    kit.notas(sl,
        f"{N_SIN_JERARQUIA} instancias sin jerarquía válida (SIN JERARQUÍA o sin dato, ver D4/D25). "
        f"Grupos de dificultad definidos en D27. Escalafón Docente/Regular, mismo colapso que "
        f"aprobacion_reprobacion_jerarquia/ — no el cruce completo de 8 categorías.")
    kit.punteo_numerado(sl, [
        f"El % de docentes de escalafón Regular es más alto en el grupo {grupo_mayor} "
        f"aprobación ({tab.loc[grupo_mayor,'pct_regular']:.1f}%) que en {grupo_menor} "
        f"({tab.loc[grupo_menor,'pct_regular']:.1f}%) — diferencia de {diferencia:.1f} puntos.",
        f"El escalafón Regular tiende a concentrarse algo más en asignaturas de baja "
        f"aprobación histórica (ver prueba de significancia en la siguiente diapositiva).",
    ])
    return sl


def agregar_ttest(prs):
    """Construye el gráfico de la prueba t (grupo predominante Baja vs Media+Alta)
    y agrega la diapositiva a `prs`."""
    kit = UcenSlideKit(out_dir=HERE)
    kit.ensure_bg()

    grupos = ["Baja (predominante)", "Media + Alta (predominante)"]
    medias = [100 * grupo_baja.mean(), 100 * grupo_resto.mean()]
    ns = [len(grupo_baja), len(grupo_resto)]
    cis = [100 * stats.t.ppf(0.975, n - 1) * s.std(ddof=1) / np.sqrt(n)
           for s, n in [(grupo_baja, len(grupo_baja)), (grupo_resto, len(grupo_resto))]]
    colors = ["#1F5C99", "#7FADD9"]

    fig = kit.new_chart_fig()
    ax = kit.chart_axes(fig, top=0.14)

    x = np.arange(2)
    ax.bar(x, medias, width=0.42, color=colors, alpha=0.92, edgecolor="none",
           yerr=cis, capsize=6, error_kw={"ecolor": "#DDDDDD", "linewidth": 1.3})

    stroke = [pe.withStroke(linewidth=2, foreground="#0A0F18")]
    for xi, media, ci, n, color in zip(x, medias, cis, ns, colors):
        ax.text(xi, media + ci + 0.6, f"{media:.1f}%", ha="center", va="bottom",
                 fontsize=13, fontweight="bold", color=color, path_effects=stroke, zorder=6)
        ax.text(xi, 0.6, f"N°={n} docentes", ha="center", va="bottom",
                 fontsize=8.5, color="white")

    sig = "significativa" if P_VAL < 0.05 else "no significativa"
    ax.text(0.5, 0.99, f"Prueba t de Welch:  t = {T_STAT:.2f}   ·   p = {P_VAL:.4f}   ·   "
            f"diferencia {sig} al 5%", transform=ax.transAxes, ha="center", va="top",
            fontsize=9.5, color="#F2D675", fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(grupos, fontsize=12, color="white")
    ax.set_ylabel("% de docentes escalafón Regular", color="#AAAAAA", fontsize=9)
    ax.set_ylim(0, max(medias) * 1.6)
    ax.tick_params(axis="x", length=0, pad=8)
    ax.tick_params(axis="y", colors="#AAAAAA", labelsize=8.5)
    for sp in ax.spines.values():
        sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.7)
    ax.yaxis.grid(True, color="white", alpha=0.07, linewidth=0.5)
    ax.set_axisbelow(True)

    chart_path = kit.save_chart(fig, "jerarquia_dificultad_ttest_chart.png")

    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.pic_chart(sl, prs, chart_path)
    kit.title(sl, "¿El escalafón se asocia al grupo de dificultad? — Prueba t, Jornada")
    kit.subtitulo(sl,
        f"Unidad de análisis: 1 valor por docente (Regular=1/Docente=0), asignado a su grupo "
        f"de dificultad predominante  ·  N°={len(grupo_baja)+len(grupo_resto)} docentes  ·  "
        f"Barras = intervalo de confianza 95%")
    kit.notas(sl,
        "Grupo predominante = el grupo de dificultad (Baja/Media/Alta) donde el docente "
        "tiene más instancias docente×asignatura×período — ver D27.")
    kit.punteo_numerado(sl, [
        f"Entre los docentes cuyo grupo predominante es Baja aprobación, el "
        f"{100*grupo_baja.mean():.1f}% son escalafón Regular, vs {100*grupo_resto.mean():.1f}% "
        f"en quienes predominan en Media o Alta (diferencia de "
        f"{100*(grupo_baja.mean()-grupo_resto.mean()):.1f} puntos).",
        f"La prueba t de Welch da p={P_VAL:.4f} — la diferencia {'sí' if P_VAL<0.05 else 'no'} es "
        f"estadísticamente significativa al 5% (con estos N°, {'se puede' if P_VAL<0.05 else 'no se puede'} "
        f"descartar que la diferencia observada se deba al azar).",
    ])
    return sl


if __name__ == "__main__":
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(UcenSlideKit.SW_EMU), Emu(UcenSlideKit.SH_EMU)
    agregar(prs)
    agregar_ttest(prs)
    prs.save(OUT_PPTX)
    print(f"\n✓ Guardado: {OUT_PPTX}")
