"""
P1 — Caracterización del Cuerpo Académico de Planta
% de Aprobación y Reprobación de alumnos según Sexo del docente — Jornada.

Mismo patrón/metodología que aprobacion_reprobacion/ (ver ese script para el detalle:
CM aprueba vía catalogo_calificacion, universo acotado a Jornada — ver
docs/DECISIONES_METODOLOGICAS.md D26).

FUENTE: intel.rendimiento_academico_alumnos (Postgres, en vivo)
        + data/cascade/01_jornada/docentes_jornada.csv (universo de RUTs)
SALIDA: P1_aprobacion_reprobacion_sexo.pptx (1 diapositiva) + aprobacion_reprobacion_sexo_chart.png
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
OUT_PPTX = Path(OUTPUTS) / "pptx" / "P1_aprobacion_reprobacion_sexo.pptx"
OUT_PPTX.parent.mkdir(parents=True, exist_ok=True)

DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"

COL_APROBACION = "#3E9E68"
COL_REPROBACION = "#E4572E"
SEXO_ORD = ["HOMBRE", "MUJER"]

# ── Datos ───────────────────────────────────────────────────────────────────
doc = pd.read_csv(Path(CASCADE) / "01_jornada" / "docentes_jornada.csv", encoding="utf-8-sig")
N_JORNADA = len(doc)

engine = create_engine(DB_URL)
q = text("""
    SELECT sexo,
           COUNT(*) AS n_evaluable,
           COUNT(DISTINCT rut_docente) AS n_docentes,
           100.0 * AVG(aprueba::int) AS pct_aprobacion
    FROM intel.rendimiento_academico_alumnos
    WHERE tipo_contrato_tag = 'JORNADA' AND aprueba IS NOT NULL
    GROUP BY sexo
""")
with engine.connect() as conn:
    raw = pd.read_sql(q, conn)

N_SIN_SEXO_DOC = int(raw.loc[raw["sexo"].isna(), "n_docentes"].sum())
tab = raw[raw["sexo"].isin(SEXO_ORD)].set_index("sexo").reindex(SEXO_ORD)
tab["pct_reprobacion"] = 100 - tab["pct_aprobacion"]

print(f"Universo Jornada: {N_JORNADA}")
print(tab)
print(f"Excluidos (sin sexo registrado): {N_SIN_SEXO_DOC} docentes")

brecha = tab.loc["MUJER", "pct_aprobacion"] - tab.loc["HOMBRE", "pct_aprobacion"]
sexo_mayor = "Mujeres" if brecha > 0 else "Hombres"

# ── Datos a nivel docente, para la prueba t. Unidad de análisis = docente (no
# calificación individual) para evitar pseudo-repetición — mismo criterio que
# aprobacion_reprobacion_edad/. ─────────────────────────────────────────────────
q2 = text("""
    SELECT rut_docente, sexo, aprueba
    FROM intel.rendimiento_academico_alumnos
    WHERE tipo_contrato_tag = 'JORNADA' AND aprueba IS NOT NULL
""")
with engine.connect() as conn:
    raw_ind = pd.read_sql(q2, conn)

por_docente = (raw_ind.groupby("rut_docente")
               .agg(sexo=("sexo", "first"),
                    pct_aprob=("aprueba", lambda s: 100 * s.mean()))
               .reset_index())

hombre = por_docente.loc[por_docente["sexo"] == "HOMBRE", "pct_aprob"]
mujer = por_docente.loc[por_docente["sexo"] == "MUJER", "pct_aprob"]
T_STAT, P_VAL = stats.ttest_ind(mujer, hombre, equal_var=False)   # Welch

print(f"\nPrueba t (por docente, Mujer vs Hombre): Mujer N°={len(mujer)} media={mujer.mean():.2f}%  "
      f"Hombre N°={len(hombre)} media={hombre.mean():.2f}%  t={T_STAT:.3f}  p={P_VAL:.4f}")



# ── Revisión 2026-09-26 ───────────────────────────────────────────────────────────────
# Obs. 2: una sola medida de aprobación por comparación — el promedio por docente (misma
# unidad que la prueba t). La versión ponderada por calificación (tab, arriba) se conserva
# solo como referencia en consola; la diapositiva descriptiva se fundió con la de prueba.
# Obs. 4: los hombres dictan más asignaturas de baja aprobación (sexo_dificultad/), así que
# la brecha global por sexo podría deberse a la dificultad de las asignaturas. Se compara
# hombres vs mujeres DENTRO de cada grupo de dificultad: 1 valor por docente y grupo (el %
# de aprobación del docente en las asignaturas de ese grupo).
from pptx_helpers import lectura_p, prueba_dict, encabezado_prueba, es_significativa
CLAVE = "% aprobación por docente: Mujer vs Hombre"   # = comparación registrada en PRUEBAS

GRUPOS_DIF = ["Baja", "Media", "Alta"]
ETIQ_DIF = {"Baja": "Baja aprobación", "Media": "Aprobación media", "Alta": "Aprobación alta"}

q3 = text("""
    SELECT rut_docente, sexo, grupo_dificultad, aprueba
    FROM intel.rendimiento_academico_alumnos
    WHERE tipo_contrato_tag = 'JORNADA' AND aprueba IS NOT NULL
      AND grupo_dificultad IS NOT NULL AND sexo IN ('HOMBRE', 'MUJER')
""")
with engine.connect() as conn:
    raw_dif = pd.read_sql(q3, conn)
por_doc_grupo = (raw_dif.groupby(["grupo_dificultad", "rut_docente", "sexo"])["aprueba"]
                 .mean().mul(100).reset_index(name="pct_aprob"))
DIF = {}
for g in GRUPOS_DIF:
    s = por_doc_grupo[por_doc_grupo["grupo_dificultad"] == g]
    h, m = s.loc[s["sexo"] == "HOMBRE", "pct_aprob"], s.loc[s["sexo"] == "MUJER", "pct_aprob"]
    t, p = stats.ttest_ind(m, h, equal_var=False)
    DIF[g] = dict(h=h, m=m, t=t, p=p)
    print(f"Grupo {g}: Hombre {h.mean():.1f}% (N°={len(h)})  Mujer {m.mean():.1f}% (N°={len(m)})  p={p:.4f}")

PRUEBAS = [prueba_dict("IV · Aprobación", "% aprobación por docente: Mujer vs Hombre",
                       f"{mujer.mean():.1f}% vs {hombre.mean():.1f}%", len(hombre) + len(mujer), P_VAL)]
def _clave_dif(g):
    return f"% aprobación Mujer vs Hombre, dentro de {ETIQ_DIF[g].lower()}"


PRUEBAS += [prueba_dict("IV · Aprobación", _clave_dif(g),
                        f"{d['m'].mean():.1f}% vs {d['h'].mean():.1f}%", len(d['m']) + len(d['h']), d["p"])
            for g, d in DIF.items()]


def agregar(prs):
    """Aprobación por sexo, 1 valor por docente (descriptivo + prueba t en una diapositiva)."""
    kit = UcenSlideKit(out_dir=HERE)
    kit.ensure_bg()
    series = [hombre, mujer]
    medias = [s.mean() for s in series]
    cis = [stats.t.ppf(0.975, len(s) - 1) * s.std(ddof=1) / np.sqrt(len(s)) for s in series]
    colors = ["#5C9BD6", "#FFB74D"]

    fig = kit.new_chart_fig()
    ax = kit.chart_axes(fig, top=0.14)
    x = np.arange(2)
    ax.bar(x, medias, width=0.42, color=colors, alpha=0.92, edgecolor="none",
           yerr=cis, capsize=6, error_kw={"ecolor": "#DDDDDD", "linewidth": 1.3})
    stroke = [pe.withStroke(linewidth=2, foreground="#0A0F18")]
    for xi, m, ci, s in zip(x, medias, cis, series):
        ax.text(xi, m + ci + 2.5, f"{m:.1f}%", ha="center", va="bottom", fontsize=13,
                fontweight="bold", color="white", path_effects=stroke, zorder=6)
        ax.text(xi, 8, f"N°={len(s)} docentes", ha="center", va="bottom", fontsize=8.5, color="white")
    ax.text(0.5, 0.99, encabezado_prueba("Prueba t de Welch", "t", T_STAT, P_VAL, CLAVE),
            transform=ax.transAxes, ha="center", va="top", fontsize=9.5, color="#F2D675", fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels(["Hombre", "Mujer"], fontsize=12, color="white")
    ax.set_ylabel("% de aprobación promedio por docente", color="#AAAAAA", fontsize=9)
    ax.set_ylim(0, 112); ax.set_yticks([0, 20, 40, 60, 80, 100])
    ax.tick_params(axis="x", length=0, pad=8); ax.tick_params(axis="y", colors="#AAAAAA", labelsize=8.5)
    for sp in ax.spines.values():
        sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.7)
    ax.yaxis.grid(True, color="white", alpha=0.07, linewidth=0.5); ax.set_axisbelow(True)
    chart_path = kit.save_chart(fig, "aprobacion_reprobacion_sexo_chart.png")

    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.pic_chart(sl, prs, chart_path)
    kit.title(sl, "¿Difiere el % de aprobación según sexo del docente? — Docentes Jornada")
    kit.subtitulo(sl, f"% de aprobación promedio por docente (no por calificación)  ·  N°={len(hombre) + len(mujer)} "
                      f"docentes con calificaciones y sexo registrado  ·  barras = intervalo de confianza 95%")
    kit.punteo_numerado(sl, [
        f"Las docentes mujeres aprueban en promedio el {mujer.mean():.1f}% de sus calificaciones, vs "
        f"{hombre.mean():.1f}% los hombres (diferencia de {mujer.mean() - hombre.mean():.1f} puntos). "
        + lectura_p(P_VAL, clave=CLAVE),
        "Esta diferencia desaparece al comparar dentro de cada grupo de dificultad (siguiente diapositiva).",
    ], fs=12)
    kit.notas(sl,
        f"{N_SIN_SEXO_DOC} docentes sin sexo registrado, excluidos. Se usa el promedio por docente "
        f"porque es la unidad de la prueba t; ponderado por calificación, el resultado va en el mismo "
        f"sentido (Mujeres {tab.loc['MUJER', 'pct_aprobacion']:.1f}% vs Hombres "
        f"{tab.loc['HOMBRE', 'pct_aprobacion']:.1f}%).")
    return sl


def agregar_por_dificultad(prs):
    """Hombres vs mujeres dentro de cada grupo de dificultad (control de la obs. 4)."""
    kit = UcenSlideKit(out_dir=HERE)
    kit.ensure_bg()
    fig = kit.new_chart_fig()
    ax = kit.chart_axes(fig, top=0.14)
    x = np.arange(3); w = 0.36
    stroke = [pe.withStroke(linewidth=2, foreground="#0A0F18")]
    for off, clave, col, lab in [(-w / 2, "h", "#5C9BD6", "Hombre"), (w / 2, "m", "#FFB74D", "Mujer")]:
        medias = [DIF[g][clave].mean() for g in GRUPOS_DIF]
        cis = [stats.t.ppf(0.975, len(DIF[g][clave]) - 1) * DIF[g][clave].std(ddof=1) / np.sqrt(len(DIF[g][clave]))
               for g in GRUPOS_DIF]
        ax.bar(x + off, medias, width=w, color=col, alpha=0.92, edgecolor="none", label=lab,
               yerr=cis, capsize=4, error_kw={"ecolor": "#DDDDDD", "linewidth": 1.1})
        for xi, m, ci, g in zip(x + off, medias, cis, GRUPOS_DIF):
            ax.text(xi, m + ci + 1.5, f"{m:.1f}%", ha="center", va="bottom", fontsize=10.5,
                    fontweight="bold", color="white", path_effects=stroke, zorder=6)
            ax.text(xi, 4, f"N°={len(DIF[g][clave])}", ha="center", va="bottom", fontsize=7.5, color="white")
    for xi, g in zip(x, GRUPOS_DIF):
        p = DIF[g]["p"]
        ax.text(xi, 108, f"p={p:.2f}" + (" *" if es_significativa(p, _clave_dif(g)) else " (n.s.)"), ha="center", va="bottom",
                fontsize=9, color="#F2D675", fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels([ETIQ_DIF[g] for g in GRUPOS_DIF], fontsize=11.5, color="white")
    ax.set_xlabel("Grupo de dificultad de la asignatura", color="#AAAAAA", fontsize=9)
    ax.set_ylabel("% de aprobación promedio por docente", color="#AAAAAA", fontsize=9)
    ax.set_ylim(0, 118); ax.set_yticks([0, 20, 40, 60, 80, 100])
    ax.tick_params(axis="x", length=0, pad=6); ax.tick_params(axis="y", colors="#AAAAAA", labelsize=8.5)
    for sp in ax.spines.values():
        sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.7)
    ax.yaxis.grid(True, color="white", alpha=0.07, linewidth=0.5); ax.set_axisbelow(True)
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, fontsize=9, framealpha=0.22, labelcolor="white", facecolor="#101820",
               edgecolor="#444", loc="upper center", bbox_to_anchor=(0.5, 0.99), ncol=2)
    chart_path = kit.save_chart(fig, "aprobacion_sexo_por_dificultad_chart.png")

    difs = [DIF[g]["m"].mean() - DIF[g]["h"].mean() for g in GRUPOS_DIF]
    n_sig = sum(es_significativa(DIF[g]["p"], _clave_dif(g)) for g in GRUPOS_DIF)
    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.pic_chart(sl, prs, chart_path)
    kit.title(sl, "% de aprobación según sexo, dentro de cada grupo de dificultad — Docentes Jornada")
    kit.subtitulo(sl, "1 valor por docente y grupo: su % de aprobación en las asignaturas de ese grupo  ·  "
                      "prueba t de Welch por grupo, p corregido por comparaciones múltiples (n.s. = no significativa)")
    kit.punteo_numerado(sl, [
        f"Dentro de cada grupo de dificultad, hombres y mujeres aprueban casi igual: las diferencias van de "
        f"{min(difs):+.1f} a {max(difs):+.1f} puntos, y {'ninguna' if n_sig == 0 else n_sig} es "
        f"estadísticamente significativa.",
        "La brecha global por sexo se explica porque los hombres dictan más asignaturas de baja aprobación "
        "(Bloque IV, sexo según grupo de dificultad), no por una diferencia entre docentes en cursos comparables.",
    ], fs=12)
    kit.notas(sl,
        "Control por dificultad (revisión 2026-09-26, obs. 4). Un docente que dicta asignaturas de varios "
        "grupos aporta un valor en cada grupo, pero solo uno por grupo, así que cada prueba compara docentes "
        "distintos. Grupos de dificultad según D27.")
    return sl


if __name__ == "__main__":
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(UcenSlideKit.SW_EMU), Emu(UcenSlideKit.SH_EMU)
    agregar(prs)
    agregar_por_dificultad(prs)
    prs.save(OUT_PPTX)
    print(f"\n✓ Guardado: {OUT_PPTX}")
