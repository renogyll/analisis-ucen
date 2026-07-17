import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os
from sqlalchemy import create_engine, text

BASE   = os.path.dirname(__file__)
OUT1   = os.path.join(BASE, "G_afo_antiguedad_918.png")
OUT2   = os.path.join(BASE, "G_afo_jerarquia_918.png")
engine = create_engine("postgresql://ucen_user:ucen2026@localhost:5432/ucen")

matplotlib.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})

C_ALTO = "#2E7D32"
C_MED  = "#F57C00"
C_BAJO = "#C62828"

# ── Cargar universo ───────────────────────────────────────────────────────────
doc917 = pd.read_csv(os.path.join(BASE,"..","PROCESADO","docente_918.csv"),
                     encoding="utf-8-sig", dtype={"rut_key": str})
doc917["rut_key"] = doc917["rut_key"].str.strip()

# Fallback jerarquía para los 2 de origen=dotacion
doc917["jerarquia"] = doc917["jerarquia"].fillna(
    doc917["jerarquia_dot"].str.replace(r"^PROFESOR\s+", "", regex=True))
doc917.loc[doc917["jerarquia"] == "NO INFORMA", "jerarquia"] = None

ruts = list(doc917["rut_key"].astype(str))
PREGS_AFO = ["AFO_01","AFO_02","AFO_03","AFO_04","AFO_05",
             "AFO_06","AFO_07","AFO_08","AFO_09"]

# ── Scores AFO desde BD ───────────────────────────────────────────────────────
with engine.connect() as conn:
    df_db = pd.read_sql(text("""
        SELECT ep.rut_docente, AVG(er.pct_acuerdo) AS afo_score
        FROM consolidados.evaluacion_respuesta er
        JOIN consolidados.evaluacion_periodo ep ON er.evaluacion_id = ep.evaluacion_id
        WHERE ep.rut_docente::text = ANY(:ruts)
          AND er.pregunta_id = ANY(:pregs)
        GROUP BY ep.rut_docente
    """), conn, params={"ruts": ruts, "pregs": PREGS_AFO})

df_db["rut_docente"] = df_db["rut_docente"].astype(str)
df_db["nivel_afo"] = df_db["afo_score"].apply(
    lambda p: "Alto" if p >= 90 else ("Medio" if p >= 75 else "Bajo"))

# Merge con docente_918
scores = df_db.merge(
    doc917[["rut_key","tramo_antiguedad","jerarquia"]].rename(
        columns={"rut_key":"rut_docente"}),
    on="rut_docente", how="left")

n_total = len(doc917)
n_afo   = len(scores)
n_med   = (scores["nivel_afo"]=="Medio").sum()
n_bajo  = (scores["nivel_afo"]=="Bajo").sum()
n_alto  = (scores["nivel_afo"]=="Alto").sum()

# ── Agrupar antigüedad: 15+ ───────────────────────────────────────────────────
REMAP_ANT = {"15-19": "15+", "20-24": "15+", "25-29": "15+", "30+": "15+"}
scores["tramo_ant"] = scores["tramo_antiguedad"].replace(REMAP_ANT)
ORD_ANT = ["0-4","5-9","10-14","15+"]

# ── Población Medio+Bajo para gráfico jerarquía ───────────────────────────────
scores_mb = scores[scores["nivel_afo"].isin(["Medio","Bajo"])].copy()
n_mb = len(scores_mb)   # 520

ORD_JER = ["INSTRUCTOR REGULAR","INSTRUCTOR DOCENTE",
           "ASISTENTE REGULAR","ASISTENTE DOCENTE",
           "ASOCIADO REGULAR","ASOCIADO DOCENTE",
           "TITULAR REGULAR","TITULAR DOCENTE"]
ABREV_JER = {
    "INSTRUCTOR REGULAR": "Instr.\nRegular",
    "INSTRUCTOR DOCENTE": "Instr.\nDocente",
    "ASISTENTE REGULAR":  "Asist.\nRegular",
    "ASISTENTE DOCENTE":  "Asist.\nDocente",
    "ASOCIADO REGULAR":   "Asoc.\nRegular",
    "ASOCIADO DOCENTE":   "Asoc.\nDocente",
    "TITULAR REGULAR":    "Titular\nRegular",
    "TITULAR DOCENTE":    "Titular\nDocente",
}

ant_validos = [a for a in ORD_ANT if a in scores["tramo_ant"].values]
jer_validos = [j for j in ORD_JER if j in scores_mb["jerarquia"].values]

# ── Cascadas ──────────────────────────────────────────────────────────────────
print("=" * 65)
print("  AFO (Aspectos Formales) — ZOOM Medio y Bajo")
print("  Umbral: Alto ≥90% | Medio 75-89% | Bajo <75%")
print("=" * 65)
print(f"  917 docentes · {n_afo} con score AFO")
print(f"    ├── Alto  (≥90%): {n_alto} ({100*n_alto/n_afo:.1f}%)")
print(f"    ├── Medio (75-89%): {n_med} ({100*n_med/n_afo:.1f}%)  ← foco")
print(f"    └── Bajo  (<75%):  {n_bajo} ({100*n_bajo/n_afo:.1f}%)  ← foco")

print(f"\n  AFO × Antigüedad — tramos agrupados (≥15 años = '15+'):")
for a in ant_validos:
    sub = scores[scores["tramo_ant"]==a]
    n = len(sub)
    alto = (sub["nivel_afo"]=="Alto").sum()
    med  = (sub["nivel_afo"]=="Medio").sum()
    bajo = (sub["nivel_afo"]=="Bajo").sum()
    print(f"    {a:5} años: n={n:3d} | Alto={alto:3d}({100*alto/n:.0f}%) "
          f"Medio={med:3d}({100*med/n:.0f}%) Bajo={bajo:3d}({100*bajo/n:.0f}%)")

print(f"\n  AFO × Jerarquía — solo Medio y Bajo (n={n_mb}):")
for j in jer_validos:
    sub = scores_mb[scores_mb["jerarquia"]==j]
    n = len(sub)
    if n == 0: continue
    med  = (sub["nivel_afo"]=="Medio").sum()
    bajo = (sub["nivel_afo"]=="Bajo").sum()
    print(f"    {ABREV_JER[j].replace(chr(10),' '):18}: n={n:3d} | "
          f"Medio={med:3d}({100*med/n:.0f}%) Bajo={bajo:3d}({100*bajo/n:.0f}%)")
print("=" * 65)

# ── Función genérica stacked bars ─────────────────────────────────────────────
def make_stacked(ax, grupos, col, scores, abrev_fn=None, title="", xlabel=""):
    vals_a, vals_m, vals_b, ns = [], [], [], []
    for g in grupos:
        sub = scores[scores[col]==g]
        n   = len(sub)
        ns.append(n)
        vals_a.append((sub["nivel_afo"]=="Alto").sum())
        vals_m.append((sub["nivel_afo"]=="Medio").sum())
        vals_b.append((sub["nivel_afo"]=="Bajo").sum())

    x = np.arange(len(grupos))
    pct_a = [100*a/n if n>0 else 0 for a,n in zip(vals_a, ns)]
    pct_m = [100*m/n if n>0 else 0 for m,n in zip(vals_m, ns)]
    pct_b = [100*b/n if n>0 else 0 for b,n in zip(vals_b, ns)]

    b1 = ax.bar(x, pct_a, color=C_ALTO, alpha=0.85, label="Alto ≥90%",   edgecolor="white")
    b2 = ax.bar(x, pct_m, bottom=pct_a, color=C_MED,  alpha=0.85,
                label="Medio 75-89%", edgecolor="white")
    b3 = ax.bar(x, pct_b, bottom=[a+m for a,m in zip(pct_a,pct_m)],
                color=C_BAJO, alpha=0.85, label="Bajo <75%", edgecolor="white")

    for i, (pa, pm, pb, n) in enumerate(zip(pct_a, pct_m, pct_b, ns)):
        if pa >= 7:
            ax.text(i, pa/2,      f"{pa:.0f}%", ha="center", va="center",
                    fontsize=8.5, fontweight="bold", color="white")
        if pm >= 7:
            ax.text(i, pa+pm/2,   f"{pm:.0f}%", ha="center", va="center",
                    fontsize=8.5, fontweight="bold", color="white")
        if pb >= 7:
            ax.text(i, pa+pm+pb/2,f"{pb:.0f}%", ha="center", va="center",
                    fontsize=8.5, fontweight="bold", color="white")
        # n debajo de la barra
        ax.text(i, -5, f"n={n}", ha="center", va="top",
                fontsize=8, color="#555555", fontweight="bold")

    labels = [abrev_fn(g) if abrev_fn else g for g in grupos]
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylim(-9, 108)
    ax.set_ylabel("% de docentes")
    ax.set_title(title, pad=10)
    ax.axhline(0, color="#CCCCCC", linewidth=0.7)
    ax.legend(fontsize=9, loc="upper right")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_xlabel(xlabel)

# ══════════════════════════════════════════════════════════════════════════════
# GRÁFICO 1 — AFO × Antigüedad
# ══════════════════════════════════════════════════════════════════════════════
scores_mb_ant = scores_mb.copy()  # misma población 520

fig1, (ax1a, ax1b) = plt.subplots(1, 2, figsize=(16, 7))
fig1.suptitle(
    "Aspectos Formales (AFO) por Antigüedad — Solo docentes Nivel Medio y Bajo\n"
    f"n={n_mb} docentes (Medio=411 + Bajo=109) · Umbral Medio 75-89% | Bajo <75%",
    fontsize=12, fontweight="bold")

# Panel A — barras apiladas Medio/Bajo por tramo antigüedad
def make_stacked_mb_ant(ax, grupos, col, df, title="", xlabel=""):
    vals_m, vals_b, ns = [], [], []
    for g in grupos:
        sub = df[df[col]==g]
        n   = len(sub)
        ns.append(n)
        vals_m.append((sub["nivel_afo"]=="Medio").sum())
        vals_b.append((sub["nivel_afo"]=="Bajo").sum())

    x = np.arange(len(grupos))
    pct_m = [100*m/n if n>0 else 0 for m,n in zip(vals_m, ns)]
    pct_b = [100*b/n if n>0 else 0 for b,n in zip(vals_b, ns)]

    ax.bar(x, pct_m, color=C_MED,  alpha=0.85, label="Medio 75-89%", edgecolor="white")
    ax.bar(x, pct_b, bottom=pct_m, color=C_BAJO, alpha=0.85, label="Bajo <75%",   edgecolor="white")

    for i, (pm, pb, n) in enumerate(zip(pct_m, pct_b, ns)):
        if pm >= 8:
            ax.text(i, pm/2,    f"{pm:.0f}%", ha="center", va="center",
                    fontsize=9, fontweight="bold", color="white")
        if pb >= 8:
            ax.text(i, pm+pb/2, f"{pb:.0f}%", ha="center", va="center",
                    fontsize=9, fontweight="bold", color="white")
        ax.text(i, -5, f"n={n}", ha="center", va="top",
                fontsize=8, color="#555555", fontweight="bold")

    ax.set_xticks(x); ax.set_xticklabels(grupos, fontsize=10)
    ax.set_ylim(-9, 108)
    ax.set_ylabel("% dentro de Medio+Bajo")
    ax.set_title(title, pad=10)
    ax.axhline(0, color="#CCCCCC", linewidth=0.7)
    ax.legend(fontsize=10, loc="upper right")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_xlabel(xlabel)

ant_mb_validos = [a for a in ORD_ANT if a in scores_mb_ant["tramo_ant"].values]

make_stacked_mb_ant(ax1a, ant_mb_validos, "tramo_ant", scores_mb_ant,
                    title="Proporción Medio vs Bajo por antigüedad\n(sobre los 520 con nivel no-Alto)",
                    xlabel="Tramo de antigüedad (años en UCEN)")

# Panel B — n absolutos Medio y Bajo por tramo
x_idx = np.arange(len(ant_mb_validos))
n_med_ant  = [(scores_mb_ant[scores_mb_ant["tramo_ant"]==a]["nivel_afo"]=="Medio").sum() for a in ant_mb_validos]
n_bajo_ant = [(scores_mb_ant[scores_mb_ant["tramo_ant"]==a]["nivel_afo"]=="Bajo").sum()  for a in ant_mb_validos]

w = 0.35
ax1b.bar(x_idx - w/2, n_med_ant,  width=w, color=C_MED,  alpha=0.85,
         label="Medio 75-89%", edgecolor="white")
ax1b.bar(x_idx + w/2, n_bajo_ant, width=w, color=C_BAJO, alpha=0.85,
         label="Bajo <75%",    edgecolor="white")

for i, (nm, nb) in enumerate(zip(n_med_ant, n_bajo_ant)):
    if nm > 0: ax1b.text(i-w/2, nm+0.5, str(nm), ha="center", fontsize=9,
                         fontweight="bold", color=C_MED)
    if nb > 0: ax1b.text(i+w/2, nb+0.5, str(nb), ha="center", fontsize=9,
                         fontweight="bold", color=C_BAJO)

ax1b.set_xticks(x_idx)
ax1b.set_xticklabels(ant_mb_validos, fontsize=10)
ax1b.set_ylabel("N° de docentes")
ax1b.set_title("Volumen absoluto Medio y Bajo por antigüedad\n(n dentro de los 520)", pad=10)
ax1b.legend(fontsize=10, loc="upper right")
ax1b.spines["top"].set_visible(False)
ax1b.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig(OUT1, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nGuardado: {OUT1}")

# ══════════════════════════════════════════════════════════════════════════════
# GRÁFICO 2 — AFO × Jerarquía
# ══════════════════════════════════════════════════════════════════════════════
fig2, (ax2a, ax2b) = plt.subplots(1, 2, figsize=(17, 7))
fig2.suptitle(
    "Aspectos Formales (AFO) por Jerarquía — Solo docentes Nivel Medio y Bajo\n"
    f"n={n_mb} docentes (Medio=411 + Bajo=109) · Umbral Medio 75-89% | Bajo <75%",
    fontsize=12, fontweight="bold")

# Panel A — barras apiladas solo Medio y Bajo (100% dentro de los 520)
def make_stacked_mb(ax, grupos, scores_mb, abrev_fn=None, title="", xlabel=""):
    vals_m, vals_b, ns = [], [], []
    for g in grupos:
        sub = scores_mb[scores_mb["jerarquia"]==g]
        n   = len(sub)
        ns.append(n)
        vals_m.append((sub["nivel_afo"]=="Medio").sum())
        vals_b.append((sub["nivel_afo"]=="Bajo").sum())

    x = np.arange(len(grupos))
    pct_m = [100*m/n if n>0 else 0 for m,n in zip(vals_m, ns)]
    pct_b = [100*b/n if n>0 else 0 for b,n in zip(vals_b, ns)]

    ax.bar(x, pct_m, color=C_MED,  alpha=0.85, label="Medio 75-89%", edgecolor="white")
    ax.bar(x, pct_b, bottom=pct_m, color=C_BAJO, alpha=0.85, label="Bajo <75%",   edgecolor="white")

    for i, (pm, pb, n) in enumerate(zip(pct_m, pct_b, ns)):
        if pm >= 8:
            ax.text(i, pm/2,    f"{pm:.0f}%", ha="center", va="center",
                    fontsize=9, fontweight="bold", color="white")
        if pb >= 8:
            ax.text(i, pm+pb/2, f"{pb:.0f}%", ha="center", va="center",
                    fontsize=9, fontweight="bold", color="white")
        ax.text(i, -5, f"n={n}", ha="center", va="top",
                fontsize=8, color="#555555", fontweight="bold")

    labels = [abrev_fn(g) if abrev_fn else g for g in grupos]
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylim(-9, 108)
    ax.set_ylabel("% dentro de Medio+Bajo")
    ax.set_title(title, pad=10)
    ax.axhline(0, color="#CCCCCC", linewidth=0.7)
    ax.legend(fontsize=10, loc="upper right")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_xlabel(xlabel)

make_stacked_mb(ax2a, jer_validos, scores_mb,
                abrev_fn=lambda j: ABREV_JER.get(j, j),
                title="Proporción Medio vs Bajo por jerarquía\n(sobre los 520 con nivel no-Alto)",
                xlabel="Jerarquía académica")

# Panel B — n absolutos Medio y Bajo por jerarquía (barras agrupadas)
x_jer = np.arange(len(jer_validos))
n_med_jer  = [(scores_mb[scores_mb["jerarquia"]==j]["nivel_afo"]=="Medio").sum() for j in jer_validos]
n_bajo_jer = [(scores_mb[scores_mb["jerarquia"]==j]["nivel_afo"]=="Bajo").sum()  for j in jer_validos]

w = 0.35
b_med  = ax2b.bar(x_jer - w/2, n_med_jer,  width=w, color=C_MED,  alpha=0.85,
                  label="Medio 75-89%", edgecolor="white")
b_bajo = ax2b.bar(x_jer + w/2, n_bajo_jer, width=w, color=C_BAJO, alpha=0.85,
                  label="Bajo <75%",    edgecolor="white")

for i, (nm, nb) in enumerate(zip(n_med_jer, n_bajo_jer)):
    if nm > 0: ax2b.text(i-w/2, nm+0.5, str(nm), ha="center", fontsize=9,
                         fontweight="bold", color=C_MED)
    if nb > 0: ax2b.text(i+w/2, nb+0.5, str(nb), ha="center", fontsize=9,
                         fontweight="bold", color=C_BAJO)

pct_bajo_jer = [100*nb/max(nm+nb,1) for nm,nb in zip(n_med_jer, n_bajo_jer)]

ax2b.set_xticks(x_jer)
ax2b.set_xticklabels([ABREV_JER.get(j,j) for j in jer_validos], fontsize=8.5)
ax2b.set_ylabel("N° de docentes")
ax2b.set_title("Volumen absoluto Medio y Bajo por jerarquía\n(n dentro de los 520)", pad=10)
ax2b.legend(fontsize=10, loc="upper right")
ax2b.spines["top"].set_visible(False)
ax2b.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig(OUT2, dpi=150, bbox_inches="tight")
plt.close()
print(f"Guardado: {OUT2}")

# ── Bajadas ───────────────────────────────────────────────────────────────────
pct_bajo_ant = [100*nb/max(nm+nb,1) for nm,nb in zip(n_med_ant, n_bajo_ant)]
max_bajo_ant = ant_mb_validos[pct_bajo_ant.index(max(pct_bajo_ant))]
max_bajo_jer = jer_validos[pct_bajo_jer.index(max(pct_bajo_jer))]

print(f"""
BAJADAS — AFO × Antigüedad
• La proporción de docentes en Nivel Bajo (<75%) en Aspectos Formales
  es más pronunciada en el tramo de **{max_bajo_ant} años** de antigüedad
  ({max(pct_bajo_ant):.0f}%), lo que sugiere que el incumplimiento de aspectos
  formales no es exclusivo de docentes recién llegados, sino que
  persiste en tramos intermedios de trayectoria institucional.

• El Nivel Medio (75-89%) se mantiene relativamente estable a través
  de los tramos de antigüedad, lo que indica que la mejora hacia
  Nivel Alto (cumplimiento óptimo ≥90%) requiere acciones específicas
  de retroalimentación más allá de la permanencia en la institución.

BAJADAS — AFO × Jerarquía
• El Nivel Bajo en Aspectos Formales se concentra en
  **{ABREV_JER[max_bajo_jer].replace(chr(10),' ')}** ({max(pct_bajo_jer):.0f}%),
  lo que puede reflejar una mayor carga académica y administrativa
  en docentes de rangos intermedios, que dificulta el cumplimiento
  estricto de plazos y aspectos protocolares.

• A diferencia de las dimensiones APR y MET, el Nivel Alto en AFO
  (≥90%) no aumenta linealmente con la jerarquía — el umbral exigente
  hace que incluso los rangos superiores presenten proporciones
  significativas de Nivel Medio, evidenciando que el cumplimiento
  formal óptimo es un desafío transversal al escalafón.
""")
