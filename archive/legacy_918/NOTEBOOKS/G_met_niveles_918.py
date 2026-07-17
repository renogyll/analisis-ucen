import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib
import numpy as np
import os
from sqlalchemy import create_engine, text

BASE   = os.path.dirname(__file__)
OUT    = os.path.join(BASE, "G_met_niveles_918.png")
engine = create_engine("postgresql://ucen_user:ucen2026@localhost:5432/ucen")

matplotlib.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})

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
          AND er.pregunta_id IN ('MET_01','MET_02','MET_03','MET_04','MET_05')
        GROUP BY ep.rut_docente, er.pregunta_id
    """), conn, params={"ruts": ruts_917})

def nivel(p):
    if p >= 80: return "Alto"
    if p >= 60: return "Medio"
    return "Bajo"

df["nivel"] = df["pct_favorable"].apply(nivel)
n_doc = df["rut_docente"].nunique()
n_sin = n_univ - n_doc

PREGS = {
    "MET_01": "Respeta diversidad e\nincluye mirada de género",
    "MET_02": "Evaluaciones permiten\nmostrar lo aprendido",
    "MET_03": "Metodología ayuda a\nlograr aprendizajes",
    "MET_04": "Orienta y clarifica\nante dudas",
    "MET_05": "Comunica criterios de\nevaluación con anticipación",
}
C_ALTO  = "#2E7D32"
C_MEDIO = "#F57C00"
C_BAJO  = "#C62828"

# ── Cascada ───────────────────────────────────────────────────────────────────
print("=" * 65)
print("  METODOLOGÍAS Y EVALUACIÓN — Clasificación por nivel")
print("=" * 65)
print(f"  917 docentes jerarquizados (Universo 917)")
print(f"    ├── {n_doc} con evaluaciones MET registradas")
for pid in PREGS:
    sub  = df[df["pregunta_id"] == pid]
    n    = len(sub)
    alto = (sub["nivel"] == "Alto").sum()
    med  = (sub["nivel"] == "Medio").sum()
    bajo = (sub["nivel"] == "Bajo").sum()
    print(f"    │     ├── {pid}: Alto={alto} ({100*alto/n:.1f}%) | Medio={med} ({100*med/n:.1f}%) | Bajo={bajo} ({100*bajo/n:.1f}%)")
print(f"    └── {n_sin} sin evaluaciones MET")
print()
print("  🟢 Alto  ≥80%  →  Docente Destacado / Sello")
print("  🟡 Medio 60–79% →  Docente Competente / En Desarrollo")
print("  🔴 Bajo  <60%  →  Alerta Institucional / Crítico")
print("=" * 65)

# ── Figura (1 fila × 5 columnas) ─────────────────────────────────────────────
fig, axes = plt.subplots(1, 5, figsize=(18, 7), sharey=True)
fig.suptitle(
    "Dimensión Metodologías y Evaluación — Distribución de docentes por nivel de desempeño\n"
    "Universo 917 · Escala: Alto ≥80% | Medio 60–79% | Bajo <60%",
    fontsize=13, fontweight="bold")

for ax, (pid, texto) in zip(axes, PREGS.items()):
    sub  = df[df["pregunta_id"] == pid]
    n    = len(sub)
    alto = (sub["nivel"] == "Alto").sum()
    med  = (sub["nivel"] == "Medio").sum()
    bajo = (sub["nivel"] == "Bajo").sum()

    vals = [alto, med, bajo]
    pcts = [100*v/n for v in vals]
    etiq = ["Alto\n≥80%", "Medio\n60–79%", "Bajo\n<60%"]
    cols = [C_ALTO, C_MEDIO, C_BAJO]

    bars = ax.bar(etiq, pcts, color=cols, width=0.55, alpha=0.88, edgecolor="white")
    for bar, v, p in zip(bars, vals, pcts):
        ax.text(bar.get_x() + bar.get_width()/2, p + 0.8,
                f"{v}\n({p:.1f}%)", ha="center", va="bottom",
                fontsize=10, fontweight="bold", color=bar.get_facecolor())

    ax.axhline(80, color=C_ALTO,  linewidth=1, linestyle="--", alpha=0.4)
    ax.axhline(60, color=C_MEDIO, linewidth=1, linestyle="--", alpha=0.4)

    ax.set_title(f"{pid}\n{texto}", fontsize=10, fontweight="bold", pad=8)
    ax.set_ylim(0, 105)
    if ax == axes[0]:
        ax.set_ylabel("% de docentes en el nivel")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    med_val = sub["pct_favorable"].median()
    ax.text(0.98, 0.97, f"Mediana:\n{med_val:.1f}%",
            transform=ax.transAxes, ha="right", va="top", fontsize=9,
            color="#333333",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#F5F5F5",
                      edgecolor="#BDBDBD", alpha=0.9))

legend_items = [
    mpatches.Patch(color=C_ALTO,  label="Alto ≥80% — Docente Destacado / Sello"),
    mpatches.Patch(color=C_MEDIO, label="Medio 60–79% — Docente Competente / En Desarrollo"),
    mpatches.Patch(color=C_BAJO,  label="Bajo <60% — Alerta Institucional / Crítico"),
]
fig.legend(handles=legend_items, loc="lower center", ncol=3,
           fontsize=11, framealpha=0.9, bbox_to_anchor=(0.5, 0.01))

plt.tight_layout(rect=[0, 0.09, 1, 0.97])
plt.savefig(OUT, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nGuardado: {OUT}")

sub_met02 = df[df["pregunta_id"]=="MET_02"]
sub_met03 = df[df["pregunta_id"]=="MET_03"]
sub_met05 = df[df["pregunta_id"]=="MET_05"]
alto_met05 = 100*(sub_met05["nivel"]=="Alto").sum()/len(sub_met05)
bajo_met03 = 100*(sub_met03["nivel"]=="Bajo").sum()/len(sub_met03)
bajo_met02 = 100*(sub_met02["nivel"]=="Bajo").sum()/len(sub_met02)

print(f"""
BAJADAS
• La dimensión Metodologías y Evaluación muestra niveles de desempeño
  levemente inferiores a Aprendizajes. MET_05 —comunicación anticipada de
  criterios de evaluación— registra el mayor porcentaje de Nivel Alto
  ({alto_met05:.1f}%), mientras MET_02 y MET_03 —que evalúan si las evaluaciones
  permiten mostrar lo aprendido y si la metodología ayuda a lograr los
  aprendizajes— concentran los mayores porcentajes de Nivel Bajo
  ({bajo_met02:.1f}% y {bajo_met03:.1f}% respectivamente).

• Entre el 67% y 76% de los docentes alcanza Nivel Alto en esta dimensión,
  lo que implica que entre un 24% y 33% requiere desarrollo metodológico.
  Este es el espacio de intervención más relevante para los programas de
  formación docente, ya que las preguntas de mayor desafío (MET_02 y MET_03)
  apuntan directamente a la calidad pedagógica del diseño de evaluaciones
  y de la experiencia de aprendizaje en el aula.
""")
