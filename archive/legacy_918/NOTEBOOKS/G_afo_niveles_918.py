import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib
import numpy as np
import os
from sqlalchemy import create_engine, text

BASE   = os.path.dirname(__file__)
OUT    = os.path.join(BASE, "G_afo_niveles_918.png")
engine = create_engine("postgresql://ucen_user:ucen2026@localhost:5432/ucen")

matplotlib.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})

doc917   = pd.read_csv(os.path.join(BASE,"..","PROCESADO","docente_918.csv"),
                       encoding="utf-8-sig", dtype={"rut_key": str})
ruts_917 = list(doc917["rut_key"].str.strip().astype(str))
n_univ   = len(doc917)

with engine.connect() as conn:
    df = pd.read_sql(text("""
        SELECT ep.rut_docente, er.pregunta_id, AVG(er.pct_acuerdo) AS pct_favorable
        FROM consolidados.evaluacion_respuesta er
        JOIN consolidados.evaluacion_periodo ep ON er.evaluacion_id = ep.evaluacion_id
        WHERE ep.rut_docente::text = ANY(:ruts)
          AND er.pregunta_id LIKE 'AFO_%'
        GROUP BY ep.rut_docente, er.pregunta_id
    """), conn, params={"ruts": ruts_917})

def nivel(p):
    if p >= 90: return "Alto"
    if p >= 75: return "Medio"
    return "Bajo"

df["nivel"] = df["pct_favorable"].apply(nivel)
n_doc = df["rut_docente"].nunique()
n_sin = n_univ - n_doc

PREGS = {
    "AFO_01": "Usa lenguaje\ninclusivo",
    "AFO_02": "Comportamiento\nacorde a su rol",
    "AFO_03": "Revisa syllabus y\ncompetencias del perfil",
    "AFO_04": "Desarrolla todos los\ntemas del syllabus",
    "AFO_05": "Asiste regularmente\na clases",
    "AFO_06": "Respeta el horario\nde clases",
    "AFO_07": "Entrega resultados\nen tiempos establecidos",
    "AFO_08": "Demuestra interés\npor enseñar",
    "AFO_09": "Demuestra dominio\nde la materia",
}
C_ALTO  = "#2E7D32"
C_MEDIO = "#F57C00"
C_BAJO  = "#C62828"

# ── Cascada ───────────────────────────────────────────────────────────────────
print("=" * 65)
print("  ASPECTOS FORMALES — Clasificación por nivel de desempeño")
print("  (Umbrales: Alto ≥90% | Medio 75–89% | Bajo <75%)")
print("=" * 65)
print(f"  917 docentes jerarquizados (Universo 917)")
print(f"    ├── {n_doc} con evaluaciones AFO registradas")
for pid in PREGS:
    sub  = df[df["pregunta_id"] == pid]
    n    = len(sub)
    alto = (sub["nivel"] == "Alto").sum()
    med  = (sub["nivel"] == "Medio").sum()
    bajo = (sub["nivel"] == "Bajo").sum()
    print(f"    │     ├── {pid}: Alto={alto} ({100*alto/n:.1f}%) | Medio={med} ({100*med/n:.1f}%) | Bajo={bajo} ({100*bajo/n:.1f}%)")
print(f"    └── {n_sin} sin evaluaciones AFO")
print()
print("  🟢 Alto  ≥90%  →  Cumplimiento Óptimo")
print("  🟡 Medio 75–89% →  Cumplimiento Al Límite")
print("  🔴 Bajo  <75%  →  Alerta Grave / Incumplimiento")
print("=" * 65)

# ── Figura 2 filas × 5 cols (última celda vacía) ─────────────────────────────
pids = list(PREGS.keys())
fig, axes = plt.subplots(2, 5, figsize=(18, 10))
axes_flat = axes.flatten()

fig.suptitle(
    "Dimensión Aspectos Formales — Distribución de docentes por nivel de desempeño\n"
    "Universo 917 · Escala: Alto ≥90% | Medio 75–89% | Bajo <75%",
    fontsize=13, fontweight="bold")

for idx, (pid, texto) in enumerate(PREGS.items()):
    ax   = axes_flat[idx]
    sub  = df[df["pregunta_id"] == pid]
    n    = len(sub)
    alto = (sub["nivel"] == "Alto").sum()
    med  = (sub["nivel"] == "Medio").sum()
    bajo = (sub["nivel"] == "Bajo").sum()

    vals = [alto, med, bajo]
    pcts = [100*v/n for v in vals]
    etiq = ["Alto\n≥90%", "Medio\n75–89%", "Bajo\n<75%"]
    cols = [C_ALTO, C_MEDIO, C_BAJO]

    bars = ax.bar(etiq, pcts, color=cols, width=0.55, alpha=0.88, edgecolor="white")
    for bar, v, p in zip(bars, vals, pcts):
        ax.text(bar.get_x() + bar.get_width()/2, p + 0.8,
                f"{v}\n({p:.1f}%)", ha="center", va="bottom",
                fontsize=9, fontweight="bold", color=bar.get_facecolor())

    ax.axhline(90, color=C_ALTO,  linewidth=1, linestyle="--", alpha=0.35)
    ax.axhline(75, color=C_MEDIO, linewidth=1, linestyle="--", alpha=0.35)

    ax.set_title(f"{pid}\n{texto}", fontsize=9, fontweight="bold", pad=6)
    ax.set_ylim(0, 78)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    med_val = sub["pct_favorable"].median()
    ax.text(0.98, 0.97, f"Med: {med_val:.1f}%",
            transform=ax.transAxes, ha="right", va="top", fontsize=8,
            color="#333333",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="#F5F5F5",
                      edgecolor="#BDBDBD", alpha=0.9))

# Ocultar celda 10 (sobrante)
axes_flat[9].set_visible(False)

# Eje Y solo en columna izquierda
for idx, ax in enumerate(axes_flat[:9]):
    if idx % 5 != 0:
        ax.set_yticklabels([])
    else:
        ax.set_ylabel("% de docentes en el nivel")

legend_items = [
    mpatches.Patch(color=C_ALTO,  label="Alto ≥90% — Cumplimiento Óptimo"),
    mpatches.Patch(color=C_MEDIO, label="Medio 75–89% — Cumplimiento Al Límite"),
    mpatches.Patch(color=C_BAJO,  label="Bajo <75% — Alerta Grave / Incumplimiento"),
]
fig.legend(handles=legend_items, loc="lower center", ncol=3,
           fontsize=11, framealpha=0.9, bbox_to_anchor=(0.5, 0.01))

plt.tight_layout(rect=[0, 0.07, 1, 0.96])
plt.savefig(OUT, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nGuardado: {OUT}")

# Stats para bajadas
sub_09 = df[df["pregunta_id"]=="AFO_09"]
sub_07 = df[df["pregunta_id"]=="AFO_07"]
alto_09 = 100*(sub_09["nivel"]=="Alto").sum()/len(sub_09)
bajo_07 = 100*(sub_07["nivel"]=="Bajo").sum()/len(sub_07)
medio_total = 100*(df["nivel"]=="Medio").sum()/len(df)

print(f"""
BAJADAS
• Con el umbral exigente propio de los Aspectos Formales (≥90% para Nivel Alto),
  AFO_09 —dominio de la materia— es la única pregunta donde más de la mitad de
  los docentes alcanza Cumplimiento Óptimo ({alto_09:.1f}%). En el otro extremo,
  AFO_07 —entrega de resultados en los tiempos establecidos— concentra el mayor
  porcentaje de Alerta Grave ({bajo_07:.1f}%), siendo el aspecto formal
  más crítico del cuerpo docente jerarquizado.

• El Nivel Medio (Cumplimiento Al Límite) es el predominante en la dimensión,
  con entre el 41% y 51% de los docentes en ese rango según la pregunta.
  Esto indica que la mayor parte del cuerpo docente cumple los aspectos
  formales pero no alcanza la excelencia, lo que representa una oportunidad
  de mejora sistémica más que casos aislados de incumplimiento.
""")
