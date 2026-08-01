"""
P1 — Caracterización del Cuerpo Académico de Planta
Evaluación Estudiantil, dimensión Aprendizajes (APR_01/02/03) — evolución por semestre.
Docentes de Jornada.

Prototipo de la serie "evaluación por dimensión" (APR ahora, MET/AFO después con el
mismo patrón: una carpeta por dimensión, mismo script adaptado).

METODOLOGÍA (ver docs/DECISIONES_METODOLOGICAS.md):
  - CM-1 (D10): se excluye toda sección con cobertura_pct < 40.
  - CM-2 (D11): el % de cada semestre se promedia ponderado por n_alumnos_evaluaron
    (no es un promedio simple de secciones — una sección de 5 alumnos no pesa igual
    que una de 50).
  - Se descarta "indiferente": solo se muestra % acuerdo (Muy de acuerdo + De acuerdo)
    y % desacuerdo (Muy en desacuerdo + En desacuerdo), tal como vienen ya calculados
    en consolidados.evaluacion_respuesta (pct_acuerdo/pct_desacuerdo).
  - Universo: acotado a los 624 docentes de Jornada (rut_docente IN docentes_jornada.csv),
    para que esto viva junto a la caracterización de P1 en vez de mezclar con Honorarios.

FUENTE: consolidados.evaluacion_respuesta + consolidados.evaluacion_periodo (Postgres, en vivo)
        + data/cascade/01_jornada/docentes_jornada.csv (universo de RUTs)
SALIDA: P1_evaluacion_apr.pptx (1 diapositiva, 3 gráficos) + evaluacion_apr_chart.png
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
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from sqlalchemy import create_engine, text
from pptx import Presentation
from pptx.util import Emu

HERE = Path(__file__).parent
OUT_PPTX = Path(OUTPUTS) / "pptx" / "P1_evaluacion_apr.pptx"
OUT_PPTX.parent.mkdir(parents=True, exist_ok=True)

DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"
COBERTURA_MIN = 40

PREGUNTAS = ["APR_01", "APR_02", "APR_03"]
PREGUNTA_LABEL = {
    "APR_01": "APR_01: Vínculo profesional",
    "APR_02": "APR_02: Aplica lo aprendido",
    "APR_03": "APR_03: Conoc. previos",
}
PERIODOS = ["2023-01", "2023-02", "2024-01", "2024-02", "2025-01", "2025-02"]
PERIODO_LABEL = {p: p[2:].replace("-", "-S") for p in PERIODOS}   # "2023-01" → "23-S01"

COL_ACUERDO = "#3E9E68"
COL_DESACUERDO = "#E4572E"

# ── Datos ───────────────────────────────────────────────────────────────────
doc = pd.read_csv(Path(CASCADE) / "01_jornada" / "docentes_jornada.csv", encoding="utf-8-sig")
ruts_jornada = tuple(doc["rut_key"].astype(str).str.strip().unique())
N_DOCENTES = len(ruts_jornada)

engine = create_engine(DB_URL)
q = text(f"""
    SELECT r.pregunta_id, ep.periodo,
           SUM(r.pct_acuerdo * ep.n_alumnos_evaluaron) / SUM(ep.n_alumnos_evaluaron) AS pct_acuerdo,
           SUM(r.pct_desacuerdo * ep.n_alumnos_evaluaron) / SUM(ep.n_alumnos_evaluaron) AS pct_desacuerdo,
           SUM(ep.n_alumnos_evaluaron) AS n_alumnos
    FROM consolidados.evaluacion_respuesta r
    JOIN consolidados.evaluacion_periodo ep ON r.evaluacion_id = ep.evaluacion_id
    WHERE r.pregunta_id IN :preguntas
      AND ep.cobertura_pct >= {COBERTURA_MIN}
      AND ep.rut_docente IN :ruts
    GROUP BY r.pregunta_id, ep.periodo
""")
with engine.connect() as conn:
    raw = pd.read_sql(q, conn, params={"preguntas": tuple(PREGUNTAS), "ruts": ruts_jornada})

print(f"Universo: {N_DOCENTES} docentes Jornada  |  cobertura ≥ {COBERTURA_MIN}%  |  filas: {len(raw)}")
print(raw.sort_values(["pregunta_id", "periodo"]).to_string(index=False))

# Tendencia global (para el punteo): comparar 1er vs último semestre, promediando las 3 preguntas
prim, ult = PERIODOS[0], PERIODOS[-1]
acu_prim = raw.loc[raw["periodo"] == prim, "pct_acuerdo"].mean()
acu_ult = raw.loc[raw["periodo"] == ult, "pct_acuerdo"].mean()
des_prim = raw.loc[raw["periodo"] == prim, "pct_desacuerdo"].mean()
des_ult = raw.loc[raw["periodo"] == ult, "pct_desacuerdo"].mean()
n_prim = int(raw.loc[raw["periodo"] == prim, "n_alumnos"].iloc[0])
n_ult = int(raw.loc[raw["periodo"] == ult, "n_alumnos"].iloc[0])

# ── Gráfico: 1 figura, 3 subplots (uno por pregunta) ──────────────────────────
kit = UcenSlideKit(out_dir=HERE)
kit.ensure_bg()

fig = kit.new_chart_fig()
axs = fig.subplots(1, 3, gridspec_kw={"wspace": 0.32})
fig.subplots_adjust(left=0.045, right=0.985, top=0.72, bottom=0.20)

x = np.arange(len(PERIODOS))
w = 0.38
stroke = [pe.withStroke(linewidth=1.8, foreground="#0A0F18")]

for ax, preg in zip(axs, PREGUNTAS):
    d = raw[raw["pregunta_id"] == preg].set_index("periodo").reindex(PERIODOS)

    bars_a = ax.bar(x - w/2, d["pct_acuerdo"], width=w, color=COL_ACUERDO, alpha=0.92,
                     edgecolor="none", label="% Acuerdo")
    bars_d = ax.bar(x + w/2, d["pct_desacuerdo"], width=w, color=COL_DESACUERDO, alpha=0.92,
                     edgecolor="none", label="% Desacuerdo")

    for bars, color in [(bars_a, COL_ACUERDO), (bars_d, COL_DESACUERDO)]:
        for b in bars:
            hgt = b.get_height()
            if pd.notna(hgt):
                ax.text(b.get_x() + b.get_width()/2, hgt + 1.5, f"{hgt:.0f}",
                        ha="center", va="bottom", fontsize=6.8, fontweight="bold",
                        color=color, path_effects=stroke, zorder=6)

    ax.set_title(PREGUNTA_LABEL[preg], fontsize=8.5, color="white", pad=10, wrap=True)
    ax.set_xticks(x)
    ax.set_xticklabels([PERIODO_LABEL[p] for p in PERIODOS], fontsize=6.8, color="#AAAAAA",
                        rotation=0)
    ax.set_ylim(0, 100)
    ax.tick_params(axis="x", length=0, pad=5)
    ax.tick_params(axis="y", colors="#AAAAAA", labelsize=7)
    for sp in ax.spines.values():
        sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.7)
    ax.yaxis.grid(True, color="white", alpha=0.07, linewidth=0.5)
    ax.set_axisbelow(True)

axs[0].set_ylabel("% de respuestas", color="#AAAAAA", fontsize=7.5)
handles, labels = axs[0].get_legend_handles_labels()
fig.legend(handles, labels, fontsize=8.5, framealpha=0.22, labelcolor="white",
           facecolor="#101820", edgecolor="#444", loc="upper center",
           bbox_to_anchor=(0.5, 0.99), ncol=2)

chart_path = kit.save_chart(fig, "evaluacion_apr_chart.png")

# ── Diapositiva ────────────────────────────────────────────────────────────────
prs = Presentation()
prs.slide_width, prs.slide_height = Emu(kit.SW_EMU), Emu(kit.SH_EMU)

sl = kit.new_slide(prs)
kit.pic(sl, prs, kit.SHARED_BG)
kit.pic_chart(sl, prs, chart_path)
kit.title(sl, "Evaluación Estudiantil — Dimensión Aprendizajes (APR) — Docentes de Planta (Jornada)")
kit.subtitulo(sl,
    f"Universo: {N_DOCENTES} docentes Jornada  ·  6 semestres (2023-01 a 2025-02)  ·  "
    f"secciones con cobertura ≥ {COBERTURA_MIN}%  ·  % ponderado por alumnos evaluadores")
kit.punteo_numerado(sl, [
    f"El % de acuerdo se mantiene estable y alto en las 3 preguntas: {acu_prim:.0f}% en "
    f"{prim} → {acu_ult:.0f}% en {ult}.",
    f"El % de desacuerdo bajó de {des_prim:.1f}% ({prim}, N°={n_prim:,} alumnos evaluadores) a "
    f"{des_ult:.1f}% ({ult}, N°={n_ult:,}) — señal de mejora sostenida en esta dimensión.",
])

prs.save(OUT_PPTX)
print(f"\n✓ Guardado: {OUT_PPTX}")
