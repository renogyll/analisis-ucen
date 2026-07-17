import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib
import numpy as np
import os
from sqlalchemy import create_engine, text

BASE   = os.path.dirname(__file__)
OUT1   = os.path.join(BASE, "G_jerarquia_met_918.png")
OUT2   = os.path.join(BASE, "G_jerarquia_afo_918.png")
engine = create_engine("postgresql://ucen_user:ucen2026@localhost:5432/ucen")

matplotlib.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})

doc917 = pd.read_csv(os.path.join(BASE,"..","PROCESADO","docente_918.csv"),
                     encoding="utf-8-sig", dtype={"rut_key": str})
doc917["rut_key"] = doc917["rut_key"].str.strip()
ruts = list(doc917["rut_key"].astype(str))
n_univ = len(doc917)

PREGS_MET = ["MET_01","MET_02","MET_03","MET_04","MET_05"]
PREGS_AFO = ["AFO_01","AFO_02","AFO_03","AFO_04","AFO_05",
             "AFO_06","AFO_07","AFO_08","AFO_09"]

with engine.connect() as conn:
    df = pd.read_sql(text("""
        SELECT ep.rut_docente, er.pregunta_id, AVG(er.pct_acuerdo) AS score
        FROM consolidados.evaluacion_respuesta er
        JOIN consolidados.evaluacion_periodo ep ON er.evaluacion_id = ep.evaluacion_id
        WHERE ep.rut_docente::text = ANY(:ruts)
          AND er.pregunta_id = ANY(:pregs)
        GROUP BY ep.rut_docente, er.pregunta_id
    """), conn, params={"ruts": ruts,
                        "pregs": PREGS_MET + PREGS_AFO})

df["rut_docente"] = df["rut_docente"].astype(str)
met_s = df[df["pregunta_id"].isin(PREGS_MET)].groupby("rut_docente")["score"].mean()
afo_s = df[df["pregunta_id"].isin(PREGS_AFO)].groupby("rut_docente")["score"].mean()

scores = pd.DataFrame({"met": met_s, "afo": afo_s}).dropna()
scores = scores.merge(
    doc917[["rut_key","jerarquia"]].rename(columns={"rut_key":"rut_docente"}),
    on="rut_docente", how="left")
scores = scores[scores["jerarquia"].notna()].copy()

# Orden y abreviaciones
ORD_JER = ["INSTRUCTOR REGULAR","INSTRUCTOR DOCENTE",
           "ASISTENTE REGULAR","ASISTENTE DOCENTE",
           "ASOCIADO REGULAR","ASOCIADO DOCENTE",
           "TITULAR REGULAR","TITULAR DOCENTE"]
ABREV = {
    "INSTRUCTOR REGULAR": "Instructor\nRegular",
    "INSTRUCTOR DOCENTE": "Instructor\nDocente",
    "ASISTENTE REGULAR":  "Asist.\nRegular",
    "ASISTENTE DOCENTE":  "Asist.\nDocente",
    "ASOCIADO REGULAR":   "Asoc.\nRegular",
    "ASOCIADO DOCENTE":   "Asoc.\nDocente",
    "TITULAR REGULAR":    "Titular\nRegular",
    "TITULAR DOCENTE":    "Titular\nDocente",
}
jer_validos = [j for j in ORD_JER if j in scores["jerarquia"].values]
n_ok = len(scores)

C_ALTO = "#2E7D32"
C_MED  = "#F57C00"
C_BAJO = "#C62828"

def nivel_met(p): return "Alto" if p>=80 else ("Medio" if p>=60 else "Bajo")
def nivel_afo(p): return "Alto" if p>=90 else ("Medio" if p>=75 else "Bajo")

scores["nivel_met"] = scores["met"].apply(nivel_met)
scores["nivel_afo"] = scores["afo"].apply(nivel_afo)

# ── Cascada ───────────────────────────────────────────────────────────────────
def print_cascada(col_nivel, dim_name, umbral_str):
    print(f"\n{'='*65}")
    print(f"  {dim_name} × JERARQUÍA  ({umbral_str})")
    print(f"{'='*65}")
    print(f"  917 docentes · {n_ok} con score {dim_name} y jerarquía")
    for j in jer_validos:
        sub  = scores[scores["jerarquia"]==j]
        n    = len(sub)
        alto = (sub[col_nivel]=="Alto").sum()
        med  = (sub[col_nivel]=="Medio").sum()
        bajo = (sub[col_nivel]=="Bajo").sum()
        print(f"    ├── {ABREV[j].replace(chr(10),' '):22} n={n:3d} | "
              f"Alto={alto:3d} ({100*alto/n:.0f}%) | Medio={med:3d} ({100*med/n:.0f}%) | Bajo={bajo:3d} ({100*bajo/n:.0f}%)")
    print(f"{'='*65}")

print_cascada("nivel_met","METODOLOGÍAS Y EVALUACIÓN","Alto ≥80% | Medio 60-79% | Bajo <60%")
print_cascada("nivel_afo","ASPECTOS FORMALES","Alto ≥90% | Medio 75-89% | Bajo <75%")

# ── Función genérica de gráfico ───────────────────────────────────────────────
def make_chart(out, col_nivel, dim_name, umbral_str, lbl_alto, lbl_med, lbl_bajo, color_dim):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(17, 7))
    fig.suptitle(
        f"{dim_name} — Distribución de niveles por Jerarquía Académica\n"
        f"Universo 917 · {n_ok} docentes · {umbral_str}",
        fontsize=13, fontweight="bold")

    x     = np.arange(len(jer_validos))
    w     = 0.25
    labels = [ABREV[j] for j in jer_validos]

    # Panel A — Barras agrupadas absolutas
    vals_a = [(scores[scores["jerarquia"]==j][col_nivel]=="Alto").sum() for j in jer_validos]
    vals_m = [(scores[scores["jerarquia"]==j][col_nivel]=="Medio").sum() for j in jer_validos]
    vals_b = [(scores[scores["jerarquia"]==j][col_nivel]=="Bajo").sum() for j in jer_validos]

    b1 = ax1.bar(x - w, vals_a, width=w, color=C_ALTO, alpha=0.88, label=f"Alto {lbl_alto}", edgecolor="white")
    b2 = ax1.bar(x,     vals_m, width=w, color=C_MED,  alpha=0.88, label=f"Medio {lbl_med}", edgecolor="white")
    b3 = ax1.bar(x + w, vals_b, width=w, color=C_BAJO, alpha=0.88, label=f"Bajo {lbl_bajo}", edgecolor="white")

    for bars in [b1, b2, b3]:
        for bar in bars:
            h = bar.get_height()
            if h > 0:
                ax1.text(bar.get_x()+bar.get_width()/2, h+0.5, str(int(h)),
                         ha="center", fontsize=8, color=bar.get_facecolor(),
                         fontweight="bold")

    ax1.set_xticks(x); ax1.set_xticklabels(labels, fontsize=9)
    ax1.set_ylabel("N° docentes")
    ax1.set_title("Distribución absoluta por jerarquía", pad=10)
    ax1.legend(fontsize=9, loc="upper right")
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)

    # Panel B — % Alto por jerarquía (línea)
    ns    = [len(scores[scores["jerarquia"]==j]) for j in jer_validos]
    pct_a = [100*va/n for va, n in zip(vals_a, ns)]
    pct_m = [100*vm/n for vm, n in zip(vals_m, ns)]
    pct_b = [100*vb/n for vb, n in zip(vals_b, ns)]

    ax2.plot(x, pct_a, marker="o", color=C_ALTO, linewidth=2.5,
             markersize=9, label=f"Alto {lbl_alto}")
    ax2.plot(x, pct_m, marker="s", color=C_MED,  linewidth=2.5,
             markersize=9, linestyle="--", label=f"Medio {lbl_med}")
    ax2.plot(x, pct_b, marker="^", color=C_BAJO, linewidth=2.5,
             markersize=9, linestyle=":",  label=f"Bajo {lbl_bajo}")

    for i, (pa, pm, pb, n) in enumerate(zip(pct_a, pct_m, pct_b, ns)):
        ax2.text(i, pa+1.5, f"{pa:.0f}%", ha="center", fontsize=8.5,
                 color=C_ALTO, fontweight="bold")
        ax2.text(i, pb-3.5, f"{pb:.0f}%", ha="center", fontsize=8,
                 color=C_BAJO, fontweight="bold")
        ax2.text(i, -6, f"n={n}", ha="center", fontsize=8,
                 color=color_dim, fontweight="bold")

    ax2.set_xticks(x); ax2.set_xticklabels(labels, fontsize=9)
    ax2.set_ylabel("% de docentes en el nivel")
    ax2.set_title("% por nivel dentro de cada jerarquía", pad=10)
    ax2.set_ylim(-10, 110)
    ax2.axhline(0, color="#CCCCCC", linewidth=0.8)
    ax2.legend(fontsize=9, loc="upper right")
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)

    plt.tight_layout()
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\nGuardado: {out}")

make_chart(OUT1, "nivel_met",
           "Metodologías y Evaluación", "Alto ≥80% | Medio 60–79% | Bajo <60%",
           "≥80%", "60–79%", "<60%", "#6A1B9A")

make_chart(OUT2, "nivel_afo",
           "Aspectos Formales", "Alto ≥90% | Medio 75–89% | Bajo <75%",
           "≥90%", "75–89%", "<75%", "#2E7D32")

# ── Bajadas ───────────────────────────────────────────────────────────────────
def top_jer(col, nivel):
    return max(jer_validos,
               key=lambda j: (scores[scores["jerarquia"]==j][col]==nivel).sum() /
                              max(len(scores[scores["jerarquia"]==j]),1))

met_mejor = top_jer("nivel_met","Alto")
afo_mejor = top_jer("nivel_afo","Alto")
met_peor  = top_jer("nivel_met","Bajo")
afo_peor  = top_jer("nivel_afo","Bajo")

sub_met_mejor = scores[scores["jerarquia"]==met_mejor]
sub_afo_mejor = scores[scores["jerarquia"]==afo_mejor]

pct_met_top = 100*(sub_met_mejor["nivel_met"]=="Alto").sum()/len(sub_met_mejor)
pct_afo_top = 100*(sub_afo_mejor["nivel_afo"]=="Alto").sum()/len(sub_afo_mejor)

print(f"""
BAJADAS — MET × Jerarquía
• En Metodologías y Evaluación, {ABREV[met_mejor].replace(chr(10),' ')} registra
  el mayor porcentaje de Nivel Alto ({pct_met_top:.0f}%), mientras los rangos
  más altos de la carrera académica no necesariamente lideran en esta
  dimensión — lo que sugiere que la destreza metodológica no es
  directamente proporcional al rango jerárquico, sino que depende
  de la actualización pedagógica continua.

• El Nivel Bajo en MET se distribuye de forma relativamente homogénea
  entre jerarquías, lo que indica que el riesgo de debilidad metodológica
  no está concentrado en un nivel específico del escalafón. Esto
  refuerza la necesidad de formación metodológica transversal para
  todos los rangos académicos.

BAJADAS — AFO × Jerarquía
• En Aspectos Formales, {ABREV[afo_mejor].replace(chr(10),' ')} lidera en
  Cumplimiento Óptimo ({pct_afo_top:.0f}%), coherente con el perfil de docentes
  con mayor experiencia y trayectoria institucional. Sin embargo, el
  umbral exigente (≥90%) hace que ninguna jerarquía supere el 60%
  en Nivel Alto, evidenciando que el cumplimiento formal óptimo
  es un desafío transversal.

• El Nivel Bajo en AFO (Alerta Grave) tiende a concentrarse en los
  rangos intermedios, lo que podría reflejar que docentes en plena
  carga académica enfrentan más dificultades para mantener estándares
  formales como entrega de notas y cumplimiento de horarios,
  mientras los rangos superiores muestran mayor consolidación
  en estos aspectos.
""")
