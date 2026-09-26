"""
P1 — Caracterización del Cuerpo Académico de Planta
Evolución de la Tasa de Aprobación de Alumnos por Sexo del Docente — Jornada.

Gráfico combinado: eje x = año (agregando los 2 semestres de cada año), una barra
Hombre y una Mujer por año, con la tasa de aprobación de alumnos de esos docentes.

Mismo patrón/metodología que aprobacion_reprobacion_sexo/ (ver ese script para el
detalle: CM aprueba vía catalogo_calificacion, universo acotado a Jornada — ver
docs/DECISIONES_METODOLOGICAS.md D26). A diferencia de ese gráfico (1 corte, sin
tiempo), acá se agrega la evolución por año — mismo espíritu que evaluacion_apr/
pero con sexo como serie en vez de acuerdo/desacuerdo, y año en vez de semestre.

FUENTE: intel.rendimiento_academico_alumnos (Postgres, en vivo)
        + data/cascade/01_jornada/docentes_jornada.csv (universo de RUTs)
SALIDA: P1_evolucion_aprobacion_sexo.pptx (1 diapositiva) + evolucion_aprobacion_sexo_chart.png
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
from sqlalchemy import create_engine, text
from pptx import Presentation
from pptx.util import Emu

HERE = Path(__file__).parent
OUT_PPTX = Path(OUTPUTS) / "pptx" / "P1_evolucion_aprobacion_sexo.pptx"
OUT_PPTX.parent.mkdir(parents=True, exist_ok=True)

DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"

COL_HOMBRE = "#5C9BD6"   # mismo par usado en el resto de P1 (edad_sexo, grado_academico_sexo)
COL_MUJER = "#FFB74D"
ANIOS_ORD = ["2023", "2024", "2025"]

# ── Datos ───────────────────────────────────────────────────────────────────
doc = pd.read_csv(Path(CASCADE) / "01_jornada" / "docentes_jornada.csv", encoding="utf-8-sig")
N_JORNADA = len(doc)

engine = create_engine(DB_URL)
q = text("""
    SELECT LEFT(periodo, 4) AS anio, sexo,
           COUNT(*) AS n_evaluable,
           COUNT(DISTINCT rut_docente) AS n_docentes,
           100.0 * AVG(aprueba::int) AS pct_aprobacion
    FROM intel.rendimiento_academico_alumnos
    WHERE tipo_contrato_tag = 'JORNADA' AND aprueba IS NOT NULL AND sexo IS NOT NULL
    GROUP BY LEFT(periodo, 4), sexo
""")
with engine.connect() as conn:
    raw = pd.read_sql(q, conn)

tab = (raw.pivot(index="anio", columns="sexo", values="pct_aprobacion")
       .reindex(ANIOS_ORD)[["HOMBRE", "MUJER"]])
tab_n = (raw.pivot(index="anio", columns="sexo", values="n_docentes")
         .reindex(ANIOS_ORD)[["HOMBRE", "MUJER"]])

print(f"Universo Jornada: {N_JORNADA}")
print(tab)
print(tab_n)

brecha_2023 = tab.loc["2023", "MUJER"] - tab.loc["2023", "HOMBRE"]
brecha_2025 = tab.loc["2025", "MUJER"] - tab.loc["2025", "HOMBRE"]
tendencia = "se redujo" if brecha_2025 < brecha_2023 else "se amplió"


def agregar(prs):
    """Construye el gráfico y agrega la diapositiva a `prs`."""
    kit = UcenSlideKit(out_dir=HERE)
    kit.ensure_bg()

    fig = kit.new_chart_fig()
    ax = kit.chart_axes(fig, top=0.15)   # deja espacio arriba para la leyenda

    x = np.arange(len(ANIOS_ORD))
    w = 0.34
    bars_h = ax.bar(x - w/2, tab["HOMBRE"], width=w, color=COL_HOMBRE, alpha=0.90,
                     edgecolor="none", label="Hombre")
    bars_m = ax.bar(x + w/2, tab["MUJER"], width=w, color=COL_MUJER, alpha=0.90,
                     edgecolor="none", label="Mujer")

    stroke = [pe.withStroke(linewidth=2, foreground="#0A0F18")]
    for bars, color, sexo_col in [(bars_h, COL_HOMBRE, "HOMBRE"), (bars_m, COL_MUJER, "MUJER")]:
        for b, anio in zip(bars, ANIOS_ORD):
            h = b.get_height()
            n = int(tab_n.loc[anio, sexo_col])
            ax.text(b.get_x() + b.get_width()/2, h + 1.2, f"{h:.1f}%",
                     ha="center", va="bottom", fontsize=10, fontweight="bold",
                     color=color, path_effects=stroke, zorder=6)
            ax.text(b.get_x() + b.get_width()/2, 4, f"N°={n}",
                     ha="center", va="bottom", fontsize=7, color="white", zorder=6)

    ax.set_xticks(x)
    ax.set_xticklabels(ANIOS_ORD, fontsize=12, color="white")
    ax.set_xlabel("Año", color="#AAAAAA", fontsize=9)
    ax.set_ylabel("% de aprobación de alumnos", color="#AAAAAA", fontsize=9)
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

    chart_path = kit.save_chart(fig, "evolucion_aprobacion_sexo_chart.png")

    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.pic_chart(sl, prs, chart_path)
    kit.title(sl, "Evolución de la tasa de aprobación según sexo del docente — Docentes Jornada")
    kit.subtitulo(sl,
        f"Universo: {N_JORNADA} docentes Jornada  ·  2023 a 2025  ·  "
        f"% ponderado sobre calificaciones evaluables por año")
    kit.punteo_numerado(sl, [
        f"La tasa de aprobación sube en ambos sexos entre 2023 y 2025: Hombre "
        f"{tab.loc['2023','HOMBRE']:.1f}%→{tab.loc['2025','HOMBRE']:.1f}%, Mujer "
        f"{tab.loc['2023','MUJER']:.1f}%→{tab.loc['2025','MUJER']:.1f}%.",
        f"La brecha entre sexos {tendencia}: de {brecha_2023:.1f} puntos en 2023 a "
        f"{brecha_2025:.1f} puntos en 2025 (Mujer siempre por sobre Hombre en los 3 años).",
    ])
    return sl


if __name__ == "__main__":
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(UcenSlideKit.SW_EMU), Emu(UcenSlideKit.SH_EMU)
    agregar(prs)
    prs.save(OUT_PPTX)
    print(f"\n✓ Guardado: {OUT_PPTX}")
