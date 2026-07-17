import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib
import numpy as np
import os
from sqlalchemy import create_engine, text

BASE   = os.path.dirname(__file__)
OUT    = os.path.join(BASE, "G_apr_niveles_918.png")
engine = create_engine("postgresql://ucen_user:ucen2026@localhost:5432/ucen")

matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 12, "axes.titlesize": 15, "axes.labelsize": 13,
})

doc917 = pd.read_csv(os.path.join(BASE,"..","PROCESADO","docente_918.csv"),
                     encoding="utf-8-sig", dtype={"rut_key": str})
ruts_917 = list(doc917["rut_key"].str.strip().astype(str))
n_univ   = len(doc917)

with engine.connect() as conn:
    df = pd.read_sql(text("""
        SELECT
            ep.rut_docente,
            er.pregunta_id,
            AVG(er.pct_acuerdo) AS pct_favorable
        FROM consolidados.evaluacion_respuesta er
        JOIN consolidados.evaluacion_periodo ep
             ON er.evaluacion_id = ep.evaluacion_id
        WHERE ep.rut_docente::text = ANY(:ruts)
          AND er.pregunta_id IN ('APR_01','APR_02','APR_03')
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
    "APR_01": "Vincula enseñanza con\nejercicio profesional",
    "APR_02": "Promueve aplicación de\naprendizajes",
    "APR_03": "Relaciona conocimientos\nprevios / otras asignaturas",
}
C_ALTO  = "#2E7D32"
C_MEDIO = "#F57C00"
C_BAJO  = "#C62828"

# ── Cascada ───────────────────────────────────────────────────────────────────
print("=" * 65)
print("  APRENDIZAJES — Clasificación por nivel de desempeño docente")
print("=" * 65)
print(f"  917 docentes jerarquizados (Universo 917)")
print(f"    ├── {n_doc} con evaluaciones APR registradas")
for pid, texto in PREGS.items():
    sub  = df[df["pregunta_id"] == pid]
    n    = len(sub)
    alto = (sub["nivel"] == "Alto").sum()
    med  = (sub["nivel"] == "Medio").sum()
    bajo = (sub["nivel"] == "Bajo").sum()
    print(f"    │     ├── {pid}: Alto={alto} ({100*alto/n:.1f}%) | Medio={med} ({100*med/n:.1f}%) | Bajo={bajo} ({100*bajo/n:.1f}%)")
print(f"    └── {n_sin} sin evaluaciones APR")
print()
print("  Niveles:")
print("    🟢 Alto  ≥ 80%  →  Docente Destacado / Sello")
print("    🟡 Medio 60–79% →  Docente Competente / En Desarrollo")
print("    🔴 Bajo  < 60%  →  Alerta Institucional / Crítico")
print("=" * 65)

# ── Figura ────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(15, 7), sharey=False)
fig.suptitle(
    "Dimensión Aprendizajes — Distribución de docentes por nivel de desempeño\n"
    "Universo 917 · Escala: Alto ≥80% | Medio 60–79% | Bajo <60%",
    fontsize=14, fontweight="bold")

for ax, (pid, texto) in zip(axes, PREGS.items()):
    sub  = df[df["pregunta_id"] == pid]
    n    = len(sub)
    alto = (sub["nivel"] == "Alto").sum()
    med  = (sub["nivel"] == "Medio").sum()
    bajo = (sub["nivel"] == "Bajo").sum()

    vals  = [alto, med, bajo]
    pcts  = [100*v/n for v in vals]
    etiq  = ["Alto\n≥80%", "Medio\n60–79%", "Bajo\n<60%"]
    cols  = [C_ALTO, C_MEDIO, C_BAJO]

    bars = ax.bar(etiq, pcts, color=cols, width=0.55, alpha=0.88, edgecolor="white")

    for bar, v, p in zip(bars, vals, pcts):
        ax.text(bar.get_x() + bar.get_width()/2, p + 0.8,
                f"{v}\n({p:.1f}%)", ha="center", va="bottom",
                fontsize=12, fontweight="bold",
                color=bar.get_facecolor())

    # Líneas de referencia
    ax.axhline(80, color=C_ALTO,  linewidth=1, linestyle="--", alpha=0.4)
    ax.axhline(60, color=C_MEDIO, linewidth=1, linestyle="--", alpha=0.4)

    ax.set_title(f"{pid}\n{texto}", fontsize=11, fontweight="bold", pad=10)
    ax.set_ylabel("% de docentes en el nivel" if ax == axes[0] else "")
    ax.set_ylim(0, 105)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Mediana del pct_favorable
    med_val = sub["pct_favorable"].median()
    ax.text(0.98, 0.97, f"Mediana: {med_val:.1f}%",
            transform=ax.transAxes, ha="right", va="top",
            fontsize=10, color="#333333",
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

# Stats para bajadas
sub1 = df[df["pregunta_id"]=="APR_01"]
sub3 = df[df["pregunta_id"]=="APR_03"]
alto1 = 100*(sub1["nivel"]=="Alto").sum()/len(sub1)
alto3 = 100*(sub3["nivel"]=="Alto").sum()/len(sub3)
bajo_total = df[df["nivel"]=="Bajo"]["rut_docente"].nunique()

print(f"""
BAJADAS
• El {alto1:.1f}% de los docentes jerarquizados alcanza el Nivel Alto (≥80%) en APR_01
  —vinculación de la enseñanza con el ejercicio profesional—, lo que refleja
  un cuerpo académico que en su mayoría conecta los contenidos con el perfil
  de egreso. La pregunta APR_03 (relación con conocimientos previos) registra
  el menor porcentaje de Nivel Alto ({alto3:.1f}%), siendo el aspecto de
  aprendizajes con mayor margen de desarrollo.

• Entre el 17% y 20% de los docentes se ubica en Nivel Medio por pregunta,
  indicando que hay una masa crítica que aún no consolida la didáctica
  de aprendizaje contextualizado. El Nivel Bajo (Alerta Institucional)
  afecta a menos del 3.1% por pregunta, pero identifica focos prioritarios
  de acompañamiento formativo inmediato.
""")
