"""
P1 — Caracterización del Cuerpo Académico de Planta
Evaluación Estudiantil, dimensión Metodologías y Evaluación (MET_01-05) — evolución
por semestre. Docentes de Jornada.

Mismo patrón que evaluacion_apr/ (ver ese script para el detalle metodológico completo:
CM-1 cobertura≥40%, CM-2 ponderado por alumnos, se descarta "indiferente", universo
acotado a los 624 Jornada). MET tiene 5 preguntas — se reparten 2 + 3 en dos
diapositivas, cada una en su propio .pptx (no un solo archivo con 2 diapos).

FUENTE: consolidados.evaluacion_respuesta + consolidados.evaluacion_periodo (Postgres, en vivo)
        + data/cascade/01_jornada/docentes_jornada.csv (universo de RUTs)
SALIDA: P1_evaluacion_met_1.pptx (MET_01-02), P1_evaluacion_met_2.pptx (MET_03-05)
        + evaluacion_met_1_chart.png, evaluacion_met_2_chart.png
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
OUT_DIR = Path(OUTPUTS) / "pptx"
OUT_DIR.mkdir(parents=True, exist_ok=True)

DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"
COBERTURA_MIN = 40

PREGUNTA_LABEL = {
    "MET_01": "MET_01: Diversidad y género",
    "MET_02": "MET_02: Eval. mostró aprendizaje",
    "MET_03": "MET_03: Logra aprendizajes",
    "MET_04": "MET_04: Orienta dudas",
    "MET_05": "MET_05: Comunica criterios",
}
# Reparto pedido: 2 en una diapo, 3 en otra — cada una en su propio pptx
GRUPOS = [
    ("evaluacion_met_1", ["MET_01", "MET_02"], "P1_evaluacion_met_1.pptx"),
    ("evaluacion_met_2", ["MET_03", "MET_04", "MET_05"], "P1_evaluacion_met_2.pptx"),
]
PERIODOS = ["2023-01", "2023-02", "2024-01", "2024-02", "2025-01", "2025-02"]
PERIODO_LABEL = {p: p[2:].replace("-", "-S") for p in PERIODOS}   # "2023-01" → "23-S01"

COL_ACUERDO = "#3E9E68"
COL_DESACUERDO = "#E4572E"

# ── Datos (una sola consulta para las 5 preguntas) ────────────────────────────
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
    raw = pd.read_sql(q, conn, params={"preguntas": tuple(PREGUNTA_LABEL), "ruts": ruts_jornada})

print(f"Universo: {N_DOCENTES} docentes Jornada  |  cobertura ≥ {COBERTURA_MIN}%  |  filas: {len(raw)}")
print(raw.sort_values(["pregunta_id", "periodo"]).to_string(index=False))

prim, ult = PERIODOS[0], PERIODOS[-1]


def hacer_grafico(preguntas):
    """1 figura con un subplot por pregunta (grupo de 2 o 3)."""
    kit = UcenSlideKit(out_dir=HERE)
    kit.ensure_bg()
    fig = kit.new_chart_fig()
    axs = fig.subplots(1, len(preguntas), gridspec_kw={"wspace": 0.30})
    fig.subplots_adjust(left=0.045, right=0.985, top=0.72, bottom=0.20)
    if len(preguntas) == 1:
        axs = [axs]

    x = np.arange(len(PERIODOS))
    w = 0.38
    stroke = [pe.withStroke(linewidth=1.8, foreground="#0A0F18")]

    for ax, preg in zip(axs, preguntas):
        d = raw[raw["pregunta_id"] == preg].set_index("periodo").reindex(PERIODOS)

        bars_a = ax.bar(x - w/2, d["pct_acuerdo"], width=w, color=COL_ACUERDO, alpha=0.92,
                         edgecolor="none", label="% Acuerdo")
        bars_d = ax.bar(x + w/2, d["pct_desacuerdo"], width=w, color=COL_DESACUERDO, alpha=0.92,
                         edgecolor="none", label="% Desacuerdo")

        for bars, color in [(bars_a, COL_ACUERDO), (bars_d, COL_DESACUERDO)]:
            for b in bars:
                hgt = b.get_height()
                if pd.notna(hgt):
                    ax.text(b.get_x() + b.get_width()/2, hgt + 1.3, f"{hgt:.0f}%",
                            ha="center", va="bottom", fontsize=6.8, fontweight="bold",
                            color=color, path_effects=stroke, zorder=6)
        # N° una sola vez por semestre (Acuerdo y Desacuerdo comparten el mismo N —
        # son las mismas evaluaciones), centrado sobre el par de barras.
        for xi, acu, n in zip(x, d["pct_acuerdo"], d["n_alumnos"]):
            if pd.notna(n):
                ax.text(xi, acu + 6.5, f"N°={n/1000:.0f}k", ha="center", va="bottom",
                        fontsize=5.0, color="#8A97A3", path_effects=stroke, zorder=6)

        ax.set_title(PREGUNTA_LABEL[preg], fontsize=8.5, color="white", pad=10, wrap=True)
        ax.set_xticks(x)
        ax.set_xticklabels([PERIODO_LABEL[p] for p in PERIODOS], fontsize=6.8, color="#AAAAAA")
        ax.set_ylim(0, 112)
        ax.set_yticks([0, 20, 40, 60, 80, 100])
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

    return kit, fig


def agregar_diapositiva(prs, nombre, preguntas):
    """Agrega a `prs` la diapositiva de un grupo de preguntas (2 o 3)."""
    kit, fig = hacer_grafico(preguntas)
    chart_path = kit.save_chart(fig, f"{nombre}_chart.png")

    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.pic_chart(sl, prs, chart_path)
    kit.title(sl, "Evaluación Estudiantil — Dimensión Metodologías y Evaluación (MET) "
                   "— Docentes de Planta (Jornada)")
    kit.subtitulo(sl,
        f"Universo: {N_DOCENTES} docentes Jornada  ·  6 semestres (2023-01 a 2025-02)  ·  "
        f"secciones con cobertura ≥ {COBERTURA_MIN}%  ·  % ponderado por alumnos evaluadores")

    d0 = raw[raw["pregunta_id"] == preguntas[0]].set_index("periodo")
    acu_prim, acu_ult = d0.loc[prim, "pct_acuerdo"], d0.loc[ult, "pct_acuerdo"]
    des_prim, des_ult = d0.loc[prim, "pct_desacuerdo"], d0.loc[ult, "pct_desacuerdo"]
    kit.punteo_numerado(sl, [
        f"{PREGUNTA_LABEL[preguntas[0]].split(' — ')[0]}: % de acuerdo pasó de {acu_prim:.0f}% "
        f"({prim}) a {acu_ult:.0f}% ({ult}); % de desacuerdo de {des_prim:.1f}% a {des_ult:.1f}%.",
        f"Preguntas incluidas en esta diapositiva: "
        f"{', '.join(p.split('_')[1] for p in preguntas)} de la dimensión Metodologías y Evaluación.",
    ])
    return sl


def agregar_todas(prs):
    """Agrega las 2 diapositivas de MET a `prs` (usado por el ensamblador
    products/p1_planta/generar_presentacion.py)."""
    for nombre, preguntas, _ in GRUPOS:
        agregar_diapositiva(prs, nombre, preguntas)


if __name__ == "__main__":
    # ── Un pptx separado por grupo (comportamiento standalone, sin cambios) ────
    for nombre, preguntas, out_name in GRUPOS:
        prs = Presentation()
        prs.slide_width, prs.slide_height = Emu(UcenSlideKit.SW_EMU), Emu(UcenSlideKit.SH_EMU)
        agregar_diapositiva(prs, nombre, preguntas)
        out_path = OUT_DIR / out_name
        prs.save(out_path)
        print(f"✓ Guardado: {out_path}")
