import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib
import numpy as np
import os
from sqlalchemy import create_engine, text

BASE   = os.path.dirname(__file__)
OUT    = os.path.join(BASE, "G_dimensiones_niveles_918.png")
engine = create_engine("postgresql://ucen_user:ucen2026@localhost:5432/ucen")

matplotlib.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12})

doc917   = pd.read_csv(os.path.join(BASE,"..","PROCESADO","docente_918.csv"),
                       encoding="utf-8-sig", dtype={"rut_key": str})
ruts_917 = list(doc917["rut_key"].str.strip().astype(str))
n_univ   = len(doc917)

# ── Umbrales por dimensión ────────────────────────────────────────────────────
DIMS = {
    "APR": {
        "pregs":    ["APR_01","APR_02","APR_03"],
        "nombre":   "Aprendizajes",
        "alto":     80, "medio": 60,
        "lbl_alto": "≥80%", "lbl_medio": "60–79%", "lbl_bajo": "<60%",
        "desc_alto": "Docente Destacado / Sello",
        "desc_med":  "Docente Competente / En Desarrollo",
        "desc_bajo": "Alerta Institucional / Crítico",
        "color":    "#1565C0",
    },
    "MET": {
        "pregs":    ["MET_01","MET_02","MET_03","MET_04","MET_05"],
        "nombre":   "Metodologías\ny Evaluación",
        "alto":     80, "medio": 60,
        "lbl_alto": "≥80%", "lbl_medio": "60–79%", "lbl_bajo": "<60%",
        "desc_alto": "Docente Destacado / Sello",
        "desc_med":  "Docente Competente / En Desarrollo",
        "desc_bajo": "Alerta Institucional / Crítico",
        "color":    "#6A1B9A",
    },
    "AFO": {
        "pregs":    ["AFO_01","AFO_02","AFO_03","AFO_04","AFO_05",
                     "AFO_06","AFO_07","AFO_08","AFO_09"],
        "nombre":   "Aspectos\nFormales",
        "alto":     90, "medio": 75,
        "lbl_alto": "≥90%", "lbl_medio": "75–89%", "lbl_bajo": "<75%",
        "desc_alto": "Cumplimiento Óptimo",
        "desc_med":  "Cumplimiento Al Límite",
        "desc_bajo": "Alerta Grave / Incumplimiento",
        "color":    "#2E7D32",
    },
}

C_ALTO = "#2E7D32"
C_MED  = "#F57C00"
C_BAJO = "#C62828"

# ── Query: promedio por docente × dimensión ───────────────────────────────────
all_pregs = [p for d in DIMS.values() for p in d["pregs"]]

with engine.connect() as conn:
    df = pd.read_sql(text("""
        SELECT ep.rut_docente, er.pregunta_id, AVG(er.pct_acuerdo) AS pct_favorable
        FROM consolidados.evaluacion_respuesta er
        JOIN consolidados.evaluacion_periodo ep ON er.evaluacion_id = ep.evaluacion_id
        WHERE ep.rut_docente::text = ANY(:ruts)
          AND er.pregunta_id = ANY(:pregs)
        GROUP BY ep.rut_docente, er.pregunta_id
    """), conn, params={"ruts": ruts_917, "pregs": all_pregs})

# Agregar a nivel dimensión por docente
results = {}
for dim, cfg in DIMS.items():
    sub = df[df["pregunta_id"].isin(cfg["pregs"])]
    # Promedio de todas las preguntas de la dimensión por docente
    dim_doc = sub.groupby("rut_docente")["pct_favorable"].mean().reset_index()
    dim_doc.columns = ["rut_docente", "score"]

    def nivel(p, cfg=cfg):
        if p >= cfg["alto"]:  return "Alto"
        if p >= cfg["medio"]: return "Medio"
        return "Bajo"

    dim_doc["nivel"] = dim_doc["score"].apply(nivel)
    results[dim] = dim_doc

n_doc = df["rut_docente"].nunique()
n_sin = n_univ - n_doc

# ── Cascada ───────────────────────────────────────────────────────────────────
print("=" * 65)
print("  EVALUACIÓN DOCENTE — Resumen por dimensión (promedio)")
print("=" * 65)
print(f"  917 docentes jerarquizados (Universo 917)")
print(f"    ├── {n_doc} con evaluaciones registradas")
for dim, cfg in DIMS.items():
    d = results[dim]
    n = len(d)
    alto = (d["nivel"]=="Alto").sum()
    med  = (d["nivel"]=="Medio").sum()
    bajo = (d["nivel"]=="Bajo").sum()
    print(f"    │     ├── {cfg['nombre'].replace(chr(10),' ')}: Alto={alto} ({100*alto/n:.1f}%) | Medio={med} ({100*med/n:.1f}%) | Bajo={bajo} ({100*bajo/n:.1f}%)")
print(f"    └── {n_sin} sin evaluaciones registradas")
print("=" * 65)

# ── Figura ────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(14, 7))
fig.suptitle(
    "Evaluación Docente — Distribución de docentes por nivel de desempeño\n"
    "Promedio por dimensión · Universo 917 docentes jerarquizados",
    fontsize=14, fontweight="bold")

for ax, (dim, cfg) in zip(axes, DIMS.items()):
    d = results[dim]
    n = len(d)
    alto = (d["nivel"]=="Alto").sum()
    med  = (d["nivel"]=="Medio").sum()
    bajo = (d["nivel"]=="Bajo").sum()

    vals  = [alto, med, bajo]
    pcts  = [100*v/n for v in vals]
    etiq  = [f"Alto\n{cfg['lbl_alto']}", f"Medio\n{cfg['lbl_medio']}", f"Bajo\n{cfg['lbl_bajo']}"]
    cols  = [C_ALTO, C_MED, C_BAJO]

    bars = ax.bar(etiq, pcts, color=cols, width=0.55, alpha=0.88, edgecolor="white")

    for bar, v, p in zip(bars, vals, pcts):
        ax.text(bar.get_x() + bar.get_width()/2, p + 0.8,
                f"{v} doc.\n({p:.1f}%)", ha="center", va="bottom",
                fontsize=12, fontweight="bold", color=bar.get_facecolor())

    # Líneas de umbral
    ax.axhline(cfg["alto"], color=C_ALTO, linewidth=1, linestyle="--", alpha=0.35)
    ax.axhline(cfg["medio"], color=C_MED,  linewidth=1, linestyle="--", alpha=0.35)

    med_score = d["score"].median()
    ax.text(0.98, 0.97, f"Mediana: {med_score:.1f}%",
            transform=ax.transAxes, ha="right", va="top", fontsize=10,
            color="#333333",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#F5F5F5",
                      edgecolor="#BDBDBD", alpha=0.9))

    ax.set_title(f"{cfg['nombre']}\n({len(cfg['pregs'])} preguntas)",
                 fontsize=12, fontweight="bold", color=cfg["color"], pad=10)
    ax.set_ylim(0, 105)
    if ax == axes[0]:
        ax.set_ylabel("% de docentes en el nivel")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Descripción niveles dentro de cada panel
    descs = [cfg["desc_alto"], cfg["desc_med"], cfg["desc_bajo"]]
    for bar, desc in zip(bars, descs):
        ax.text(bar.get_x() + bar.get_width()/2, -6,
                desc, ha="center", va="top", fontsize=7.5,
                color="#555555", fontstyle="italic",
                wrap=True)

legend_items = [
    mpatches.Patch(color=C_ALTO, label="Alto — Nivel óptimo de desempeño"),
    mpatches.Patch(color=C_MED,  label="Medio — En desarrollo / Al límite"),
    mpatches.Patch(color=C_BAJO, label="Bajo — Alerta / Requiere intervención"),
]
fig.legend(handles=legend_items, loc="lower center", ncol=3,
           fontsize=11, framealpha=0.9, bbox_to_anchor=(0.5, 0.01))

plt.tight_layout(rect=[0, 0.08, 1, 0.97])
plt.savefig(OUT, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nGuardado: {OUT}")

# Bajadas
apr = results["APR"]; met = results["MET"]; afo = results["AFO"]
alto_apr = 100*(apr["nivel"]=="Alto").sum()/len(apr)
alto_met = 100*(met["nivel"]=="Alto").sum()/len(met)
alto_afo = 100*(afo["nivel"]=="Alto").sum()/len(afo)
bajo_afo = 100*(afo["nivel"]=="Bajo").sum()/len(afo)
bajo_met = 100*(met["nivel"]=="Bajo").sum()/len(met)

print(f"""
BAJADAS
• Aprendizajes lidera con {alto_apr:.1f}% de docentes en Nivel Alto, seguida
  de Metodologías y Evaluación ({alto_met:.1f}%). Aspectos Formales, con su
  umbral más exigente (≥90%), registra solo el {alto_afo:.1f}% en Nivel Óptimo,
  siendo la dimensión con mayor masa crítica en el rango medio (Al Límite).

• El Nivel Bajo afecta principalmente a Aspectos Formales ({bajo_afo:.1f}%) y
  Metodologías ({bajo_met:.1f}%), dimensiones que representan los focos
  prioritarios de acompañamiento formativo. La brecha entre los umbrales
  refleja la mayor exigencia institucional en el cumplimiento formal
  respecto a la calidad pedagógica.
""")
