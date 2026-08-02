"""
P1 — Caracterización del Cuerpo Académico de Planta
Antigüedad de los Docentes según Grupo de Dificultad de Asignatura — Jornada.

¿Los docentes con más antigüedad institucional dictan asignaturas más difíciles
(menor % de aprobación histórico)? Usa los grupos de dificultad definidos en
docs/DECISIONES_METODOLOGICAS.md D27 (terciles Baja/Media/Alta de % aprobación
histórico por asignatura). Unidad de análisis: instancia docente×asignatura×período
(una fila de intel.rendimiento_academico_alumnos) — un docente que dicta materias
de dos grupos distintos aporta a los dos, ponderado por su volumen de calificaciones
en cada uno (mismo criterio que el resto de los gráficos "por grupo" de este bloque).

FUENTE: intel.rendimiento_academico_alumnos (Postgres, en vivo)
        + data/cascade/01_jornada/docentes_jornada.csv (universo de RUTs)
SALIDA: P1_antiguedad_dificultad.pptx (1 diapositiva) + antiguedad_dificultad_chart.png
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
OUT_PPTX = Path(OUTPUTS) / "pptx" / "P1_antiguedad_dificultad.pptx"
OUT_PPTX.parent.mkdir(parents=True, exist_ok=True)

DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"
GRUPOS_ORD = ["Baja", "Media", "Alta"]
# Mismo criterio ordinal que edad_jerarquia/: claro→oscuro seguido el eje de la
# variable (acá % aprobación creciente Baja→Alta), no un juicio de "bueno/malo".
COLORS = ["#AFCBE8", "#4E8FC9", "#1F5C99"]

# ── Datos ───────────────────────────────────────────────────────────────────
doc = pd.read_csv(Path(CASCADE) / "01_jornada" / "docentes_jornada.csv", encoding="utf-8-sig")
N_JORNADA = len(doc)

engine = create_engine(DB_URL)
q = text("""
    SELECT grupo_dificultad,
           COUNT(*) AS n_instancias,
           COUNT(DISTINCT rut_docente) AS n_docentes,
           AVG(antiguedad_anios) AS antiguedad_prom
    FROM intel.rendimiento_academico_alumnos
    WHERE tipo_contrato_tag = 'JORNADA' AND grupo_dificultad IS NOT NULL
      AND antiguedad_anios IS NOT NULL
    GROUP BY grupo_dificultad
""")
with engine.connect() as conn:
    tab = pd.read_sql(q, conn).set_index("grupo_dificultad").reindex(GRUPOS_ORD)

N_SIN_ANTIGUEDAD = int(pd.read_sql(text("""
    SELECT COUNT(*) AS n FROM intel.rendimiento_academico_alumnos
    WHERE tipo_contrato_tag='JORNADA' AND grupo_dificultad IS NOT NULL AND antiguedad_anios IS NULL
"""), engine).iloc[0, 0])

print(f"Universo Jornada: {N_JORNADA}")
print(tab)
print(f"Instancias sin dato de antigüedad: {N_SIN_ANTIGUEDAD}")

grupo_mayor = tab["antiguedad_prom"].idxmax()
grupo_menor = tab["antiguedad_prom"].idxmin()
diferencia = tab.loc[grupo_mayor, "antiguedad_prom"] - tab.loc[grupo_menor, "antiguedad_prom"]

# ── Datos para la prueba t: grupo DIFICULTAD PREDOMINANTE por docente. La antigüedad
# es un atributo fijo del docente (no varía por instancia), así que a diferencia de
# las pruebas t de aprobación acá no se pondera por volumen — cada docente aporta
# un solo valor, asignado al grupo donde tiene más instancias (evita que un mismo
# docente cuente en dos muestras a la vez, lo que rompería la independencia del t-test).
q2 = text("""
    SELECT rut_docente, antiguedad_anios, grupo_dificultad
    FROM intel.rendimiento_academico_alumnos
    WHERE tipo_contrato_tag = 'JORNADA' AND grupo_dificultad IS NOT NULL
      AND antiguedad_anios IS NOT NULL
""")
with engine.connect() as conn:
    raw_doc = pd.read_sql(q2, conn)

conteo = raw_doc.groupby(["rut_docente", "grupo_dificultad"]).size().reset_index(name="n")
idx_predominante = conteo.groupby("rut_docente")["n"].idxmax()
predominante = conteo.loc[idx_predominante, ["rut_docente", "grupo_dificultad"]] \
    .rename(columns={"grupo_dificultad": "grupo_predominante"})
antig_doc = raw_doc.drop_duplicates("rut_docente")[["rut_docente", "antiguedad_anios"]]
por_docente = predominante.merge(antig_doc, on="rut_docente")

grupo_baja = por_docente.loc[por_docente["grupo_predominante"] == "Baja", "antiguedad_anios"]
grupo_resto = por_docente.loc[por_docente["grupo_predominante"] != "Baja", "antiguedad_anios"]
T_STAT, P_VAL = stats.ttest_ind(grupo_baja, grupo_resto, equal_var=False)   # Welch

print(f"\nPrueba t (por docente, grupo predominante Baja vs Media+Alta): "
      f"Baja N°={len(grupo_baja)} media={grupo_baja.mean():.2f}  "
      f"Resto N°={len(grupo_resto)} media={grupo_resto.mean():.2f}  t={T_STAT:.3f}  p={P_VAL:.4f}")


def agregar(prs):
    """Construye el gráfico y agrega la diapositiva a `prs`."""
    kit = UcenSlideKit(out_dir=HERE)
    kit.ensure_bg()

    fig = kit.new_chart_fig()
    ax = kit.chart_axes(fig, top=0.10)

    x = np.arange(len(GRUPOS_ORD))
    bars = ax.bar(x, tab["antiguedad_prom"], width=0.45, color=COLORS, alpha=0.92, edgecolor="none")

    stroke = [pe.withStroke(linewidth=2, foreground="#0A0F18")]
    for xi, v, n, color in zip(x, tab["antiguedad_prom"], tab["n_docentes"], COLORS):
        ax.text(xi, v + 0.3, f"{v:.1f} años", ha="center", va="bottom",
                 fontsize=14, fontweight="bold", color=color, path_effects=stroke, zorder=6)
        ax.text(xi, 0.3, f"N°={int(n)} docentes", ha="center", va="bottom",
                 fontsize=8.5, color="white")

    ax.set_xticks(x)
    ax.set_xticklabels([f"{g} aprobación" for g in GRUPOS_ORD], fontsize=12, color="white")
    ax.set_xlabel("Grupo de dificultad de la asignatura", color="#AAAAAA", fontsize=9)
    ax.set_ylabel("Antigüedad promedio (años)", color="#AAAAAA", fontsize=9)
    ax.set_ylim(0, tab["antiguedad_prom"].max() * 1.30)
    ax.tick_params(axis="x", length=0, pad=8)
    ax.tick_params(axis="y", colors="#AAAAAA", labelsize=8.5)
    for sp in ax.spines.values():
        sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.7)
    ax.yaxis.grid(True, color="white", alpha=0.07, linewidth=0.5)
    ax.set_axisbelow(True)

    chart_path = kit.save_chart(fig, "antiguedad_dificultad_chart.png")

    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.pic_chart(sl, prs, chart_path)
    kit.title(sl, "Antigüedad de los Docentes según Grupo de Dificultad de Asignatura — Jornada")
    kit.subtitulo(sl,
        f"Universo: {N_JORNADA} docentes Jornada  ·  "
        f"N°={int(tab['n_instancias'].sum()):,} instancias con antigüedad registrada")
    kit.notas(sl,
        f"{N_SIN_ANTIGUEDAD} instancias sin dato de antigüedad (brecha NOMINA→DOTACION, "
        f"ver D22/D23). Grupos de dificultad definidos en D27 — terciles de % de aprobación "
        f"histórico por asignatura, calculados sobre todo el universo (no solo Jornada).")
    kit.punteo_numerado(sl, [
        f"Los docentes que dictan asignaturas de {grupo_mayor.lower()} aprobación histórica "
        f"tienen en promedio {diferencia:.1f} años más de antigüedad que quienes dictan las de "
        f"{grupo_menor.lower()} aprobación ({tab.loc[grupo_mayor,'antiguedad_prom']:.1f} vs "
        f"{tab.loc[grupo_menor,'antiguedad_prom']:.1f} años).",
        f"La diferencia entre grupos es de {diferencia:.1f} años — un indicio de que las "
        f"asignaturas más exigentes tienden a quedar en manos de docentes más senior "
        f"(ver prueba de significancia en la siguiente diapositiva).",
    ])
    return sl


def agregar_ttest(prs):
    """Construye el gráfico de la prueba t (grupo predominante Baja vs Media+Alta)
    y agrega la diapositiva a `prs`."""
    kit = UcenSlideKit(out_dir=HERE)
    kit.ensure_bg()

    grupos = ["Baja (predominante)", "Media + Alta (predominante)"]
    medias = [grupo_baja.mean(), grupo_resto.mean()]
    ns = [len(grupo_baja), len(grupo_resto)]
    cis = [stats.t.ppf(0.975, n - 1) * s.std(ddof=1) / np.sqrt(n)
           for s, n in [(grupo_baja, len(grupo_baja)), (grupo_resto, len(grupo_resto))]]
    colors = ["#1F5C99", "#7FADD9"]

    fig = kit.new_chart_fig()
    ax = kit.chart_axes(fig, top=0.14)

    x = np.arange(2)
    ax.bar(x, medias, width=0.42, color=colors, alpha=0.92, edgecolor="none",
           yerr=cis, capsize=6, error_kw={"ecolor": "#DDDDDD", "linewidth": 1.3})

    stroke = [pe.withStroke(linewidth=2, foreground="#0A0F18")]
    for xi, media, ci, n, color in zip(x, medias, cis, ns, colors):
        ax.text(xi, media + ci + 0.3, f"{media:.1f} años", ha="center", va="bottom",
                 fontsize=13, fontweight="bold", color=color, path_effects=stroke, zorder=6)
        ax.text(xi, 0.3, f"N°={n} docentes", ha="center", va="bottom",
                 fontsize=8.5, color="white")

    sig = "significativa" if P_VAL < 0.05 else "no significativa"
    ax.text(0.5, 0.99, f"Prueba t de Welch:  t = {T_STAT:.2f}   ·   p = {P_VAL:.4f}   ·   "
            f"diferencia {sig} al 5%", transform=ax.transAxes, ha="center", va="top",
            fontsize=9.5, color="#F2D675", fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(grupos, fontsize=12, color="white")
    ax.set_ylabel("Antigüedad promedio (años)", color="#AAAAAA", fontsize=9)
    ax.set_ylim(0, max(medias) * 1.6)
    ax.tick_params(axis="x", length=0, pad=8)
    ax.tick_params(axis="y", colors="#AAAAAA", labelsize=8.5)
    for sp in ax.spines.values():
        sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.7)
    ax.yaxis.grid(True, color="white", alpha=0.07, linewidth=0.5)
    ax.set_axisbelow(True)

    chart_path = kit.save_chart(fig, "antiguedad_dificultad_ttest_chart.png")

    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.pic_chart(sl, prs, chart_path)
    kit.title(sl, "¿La antigüedad se asocia al grupo de dificultad? — Prueba t, Jornada")
    kit.subtitulo(sl,
        f"Unidad de análisis: 1 valor por docente, asignado a su grupo de dificultad "
        f"predominante  ·  N°={len(grupo_baja)+len(grupo_resto)} docentes  ·  "
        f"Barras = intervalo de confianza 95%")
    kit.notas(sl,
        "Grupo predominante = el grupo de dificultad (Baja/Media/Alta) donde el docente "
        "tiene más instancias docente×asignatura×período — evita que un mismo docente "
        "cuente en dos muestras del t-test a la vez. Ver D27 para la limitación del 56% "
        "de asignaturas de un solo docente (afecta la asignación del grupo, no esta prueba).")
    kit.punteo_numerado(sl, [
        f"Los docentes cuyo grupo predominante es Baja aprobación tienen en promedio "
        f"{grupo_baja.mean():.1f} años de antigüedad, vs {grupo_resto.mean():.1f} años "
        f"en quienes predominan en Media o Alta (diferencia de "
        f"{grupo_baja.mean()-grupo_resto.mean():.1f} años).",
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
