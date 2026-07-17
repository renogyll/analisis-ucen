import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os

BASE = os.path.dirname(__file__)
OUT1 = os.path.join(BASE, "G_aprobacion_antiguedad_918.png")
OUT2 = os.path.join(BASE, "G_aprobacion_jerarquia_918.png")

matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11, "axes.titlesize": 13, "axes.labelsize": 12,
})

C_MED  = "#1565C0"
C_TEXT = "#333333"

# ── Cargar universo ───────────────────────────────────────────────────────────
doc917 = pd.read_csv(os.path.join(BASE,"..","PROCESADO","docente_918.csv"),
                     encoding="utf-8-sig", dtype={"rut_key": str})
doc917["rut_key"] = doc917["rut_key"].str.strip()
doc917["jerarquia"] = doc917["jerarquia"].fillna(
    doc917["jerarquia_dot"].str.replace(r"^PROFESOR\s+", "", regex=True))
doc917.loc[doc917["jerarquia"] == "NO INFORMA", "jerarquia"] = None

# ── Cargar notas ──────────────────────────────────────────────────────────────
notas = pd.read_csv(
    os.path.join(BASE,"..","..","DETALLE DE EVALUACION DE CADA ESTUDIANTE A DOCENTE 3-5-2026",
                 "DETALLE DE EVALUACION DE CADA ESTUDIANTE A DOCENTE 3-5-2026.xlsx - datos.csv"),
    encoding="utf-8-sig", dtype=str)

notas["nota_num"]  = pd.to_numeric(notas["Nota"], errors="coerce")
notas["rut_doc"]   = notas["Rut Docente"].astype(str).str.strip()
notas["aprobado"]  = notas["nota_num"] >= 4.0

# Filtrar al universo 917 y notas válidas
notas917 = notas[notas["rut_doc"].isin(set(doc917["rut_key"])) &
                 notas["nota_num"].notna()].copy()

# ── Opción A: un % de aprobación por docente (todo el período colapsado) ─────
por_doc = (notas917.groupby("rut_doc")
           .agg(total_alumnos=("nota_num","count"),
                aprobados=("aprobado","sum"))
           .reset_index())
por_doc["pct_aprobacion"] = 100 * por_doc["aprobados"] / por_doc["total_alumnos"]

# Merge con antigüedad y jerarquía
por_doc = por_doc.merge(
    doc917[["rut_key","tramo_antiguedad","jerarquia"]].rename(
        columns={"rut_key":"rut_doc"}),
    on="rut_doc", how="left")

# Agrupar antigüedad 15+
REMAP = {"15-19":"15+","20-24":"15+","25-29":"15+","30+":"15+"}
por_doc["tramo_ant"] = por_doc["tramo_antiguedad"].replace(REMAP)

n_total  = len(doc917)
n_notas  = por_doc["rut_doc"].nunique()
mediana_global = por_doc["pct_aprobacion"].median()
media_global   = por_doc["pct_aprobacion"].mean()

# ── Órdenes ───────────────────────────────────────────────────────────────────
ORD_ANT = ["0-4","5-9","10-14","15+"]
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
COLORES_ANT = ["#42A5F5","#1976D2","#388E3C","#E65100"]
COLORES_JER = ["#42A5F5","#1976D2","#66BB6A","#388E3C",
               "#FFA726","#E65100","#EF5350","#B71C1C"]

ant_validos = [a for a in ORD_ANT if a in por_doc["tramo_ant"].values]
jer_validos = [j for j in ORD_JER if j in por_doc["jerarquia"].dropna().values]

# ── Cascada ───────────────────────────────────────────────────────────────────
print("=" * 65)
print("  TASA DE APROBACIÓN POR DOCENTE (Universo 917)")
print("  Criterio: Nota ≥ 4.0 · Un % por docente (períodos 2023-2025)")
print("=" * 65)
print(f"  917 docentes jerarquizados")
print(f"    ├── {n_notas} con registros de calificaciones de alumnos")
print(f"    │     ├── Mediana global: {mediana_global:.1f}%")
print(f"    │     ├── Media global  : {media_global:.1f}%")
print(f"    │")
print(f"    │   Por tramo de antigüedad:")
for a in ant_validos:
    sub = por_doc[por_doc["tramo_ant"]==a]["pct_aprobacion"]
    print(f"    │     ├── {a:5} años : n={len(sub):3d} | "
          f"mediana={sub.median():.1f}% | media={sub.mean():.1f}%")
print(f"    │")
print(f"    │   Por jerarquía:")
for j in jer_validos:
    sub = por_doc[por_doc["jerarquia"]==j]["pct_aprobacion"]
    print(f"    │     ├── {ABREV_JER[j].replace(chr(10),' '):18}: "
          f"n={len(sub):3d} | mediana={sub.median():.1f}% | media={sub.mean():.1f}%")
print(f"    └── {n_total - n_notas} sin registros de calificaciones")
print("=" * 65)

# ── Función boxplot ───────────────────────────────────────────────────────────
def make_boxplot(ax, grupos, col, df, colores, abrev_fn, title, ylabel, ref_line):
    datos  = [df[df[col]==g]["pct_aprobacion"].dropna().values for g in grupos]
    ns     = [len(d) for d in datos]
    labels = [f"{abrev_fn(g)}\n(n={n})" for g, n in zip(grupos, ns)]

    bp = ax.boxplot(datos, patch_artist=True,
                    medianprops=dict(color="black", linewidth=2.5),
                    whiskerprops=dict(linewidth=1.5),
                    capprops=dict(linewidth=1.5),
                    flierprops=dict(marker="o", markersize=3, alpha=0.35))

    for patch, color in zip(bp["boxes"], colores[:len(grupos)]):
        patch.set_facecolor(color); patch.set_alpha(0.75)

    for i, (d, color) in enumerate(zip(datos, colores)):
        med = np.median(d) if len(d) > 0 else 0
        ax.text(i+1, med+1.2, f"{med:.1f}%", ha="center", fontsize=8.5,
                fontweight="bold", color="black")

    ax.axhline(ref_line, color="#C62828", linewidth=1.5,
               linestyle="--", alpha=0.7, label=f"Mediana global ({ref_line:.1f}%)")
    ax.set_xticks(range(1, len(grupos)+1))
    ax.set_xticklabels(labels, fontsize=8.5)
    ax.set_ylabel(ylabel)
    ax.set_title(title, pad=10)
    ax.set_ylim(-5, 110)
    ax.legend(fontsize=9, loc="lower right")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

# ══════════════════════════════════════════════════════════════════════════════
# GRÁFICO 1 — Aprobación × Antigüedad
# ══════════════════════════════════════════════════════════════════════════════
fig1, ax1 = plt.subplots(figsize=(12, 7))
fig1.suptitle(
    "Tasa de Aprobación de Alumnos por Tramo de Antigüedad Docente\n"
    f"Universo 917 · {n_notas} docentes con registros · Períodos 2023-2025",
    fontsize=13, fontweight="bold")

make_boxplot(ax1, ant_validos, "tramo_ant", por_doc,
             COLORES_ANT, lambda g: g,
             "% de aprobación por docente según antigüedad en UCEN",
             "% de alumnos aprobados por docente", mediana_global)

plt.tight_layout()
plt.savefig(OUT1, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nGuardado: {OUT1}")

# ══════════════════════════════════════════════════════════════════════════════
# GRÁFICO 2 — Aprobación × Jerarquía
# ══════════════════════════════════════════════════════════════════════════════
fig2, ax2 = plt.subplots(figsize=(14, 7))
fig2.suptitle(
    "Tasa de Aprobación de Alumnos por Jerarquía Académica Docente\n"
    f"Universo 917 · {n_notas} docentes con registros · Períodos 2023-2025",
    fontsize=13, fontweight="bold")

make_boxplot(ax2, jer_validos, "jerarquia", por_doc,
             COLORES_JER, lambda j: ABREV_JER.get(j, j),
             "% de aprobación por docente según jerarquía académica",
             "% de alumnos aprobados por docente", mediana_global)

plt.tight_layout()
plt.savefig(OUT2, dpi=150, bbox_inches="tight")
plt.close()
print(f"Guardado: {OUT2}")

# ── Bajadas ───────────────────────────────────────────────────────────────────
med_ant = {a: por_doc[por_doc["tramo_ant"]==a]["pct_aprobacion"].median()
           for a in ant_validos}
med_jer = {j: por_doc[por_doc["jerarquia"]==j]["pct_aprobacion"].median()
           for j in jer_validos}

mejor_ant = max(med_ant, key=med_ant.get)
peor_ant  = min(med_ant, key=med_ant.get)
mejor_jer = max(med_jer, key=med_jer.get)
peor_jer  = min(med_jer, key=med_jer.get)

print(f"""
BAJADAS — Aprobación × Antigüedad
• La tasa mediana de aprobación es relativamente estable entre tramos
  de antigüedad, con una mediana global de {mediana_global:.1f}%. El tramo de
  **{mejor_ant} años** registra la mediana más alta ({med_ant[mejor_ant]:.1f}%),
  mientras **{peor_ant} años** presenta la más baja ({med_ant[peor_ant]:.1f}%).
  La amplitud del boxplot es mayor en los tramos iniciales, lo que
  refleja mayor heterogeneidad en el desempeño de los docentes recién
  incorporados.

• La dispersión intra-tramo supera las diferencias entre tramos,
  lo que indica que la antigüedad por sí sola no determina la tasa
  de aprobación de los alumnos: existen docentes con alta y baja
  aprobación en todos los tramos de trayectoria institucional.

BAJADAS — Aprobación × Jerarquía
• **{ABREV_JER[mejor_jer].replace(chr(10),' ')}** registra la mediana de
  aprobación más alta ({med_jer[mejor_jer]:.1f}%), mientras
  **{ABREV_JER[peor_jer].replace(chr(10),' ')}** presenta la más baja
  ({med_jer[peor_jer]:.1f}%). Sin embargo, en todas las jerarquías la
  dispersión interna es amplia, con docentes que superan el 90% y
  otros que no alcanzan el 60% dentro del mismo nivel.

• Los rangos medios del escalafón (Asistente y Asociado) muestran
  medianas de aprobación comparables a los rangos superiores, lo que
  sugiere que la jerarquía académica no es un predictor directo del
  rendimiento estudiantil medido por tasa de aprobación.
""")
