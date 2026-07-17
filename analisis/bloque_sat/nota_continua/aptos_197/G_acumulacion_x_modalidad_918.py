import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os

BASE = os.path.dirname(__file__)
OUT_TALLER    = os.path.join(BASE, "G_acumulacion_talleres_918.png")
OUT_DIPLOMADO = os.path.join(BASE, "G_acumulacion_diplomados_918.png")

matplotlib.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})

C_CTRL  = "#607D8B"
C_TALL  = "#1976D2"
C_DIPL  = "#388E3C"
C_LINE  = "#0D47A1"
C_LINE2 = "#1B5E20"

# ── Cargar datos ──────────────────────────────────────────────────────────────
part = pd.read_csv(os.path.join(BASE,"..","PROCESADO","participacion_p2_918.csv"),
                   encoding="utf-8-sig", dtype=str)
notas = pd.read_csv(os.path.join(BASE,"..","PROCESADO","scatter_sat_notas.csv"),
                    encoding="utf-8-sig")
doc917 = pd.read_csv(os.path.join(BASE,"..","PROCESADO","docente_918.csv"),
                     encoding="utf-8-sig", dtype={"rut_key": str})
doc917["rut_key"] = doc917["rut_key"].str.strip()

# Aprobación promedio por docente
notas["rut_docente"] = notas["rut_docente"].astype(str).str.strip()
aprob = (notas.groupby("rut_docente")["pct_aprobacion"]
         .mean().reset_index()
         .rename(columns={"rut_docente": "rut_key"}))

# Contar iniciativas por tipo y docente
n_por_tipo = (part.groupby(["rut_key","tipo_formacion"])
              .size().unstack(fill_value=0).reset_index())
n_por_tipo["rut_key"] = n_por_tipo["rut_key"].astype(str).str.strip()
for col in ["TALLER","DIPLOMADO","PROYECTO"]:
    if col not in n_por_tipo.columns:
        n_por_tipo[col] = 0

# ── GRÁFICO 1: Acumulativo por Talleres ───────────────────────────────────────
def tramo_taller(n):
    if n == 0:   return "Sin taller"
    if n == 1:   return "1"
    if n == 2:   return "2"
    if n == 3:   return "3"
    return "4+"

# Merge universo 917 con conteo de talleres
df_t = doc917[["rut_key"]].merge(
    n_por_tipo[["rut_key","TALLER"]], on="rut_key", how="left").fillna({"TALLER": 0})
df_t["tramo"] = df_t["TALLER"].apply(tramo_taller)
df_t = df_t.merge(aprob, on="rut_key", how="inner")

ORD_T = ["Sin taller","1","2","3","4+"]
LABELS_T = ["Sin\ntaller","1\ntaller","2\ntalleres","3\ntalleres","4+\ntalleres"]

stats_t = {}
for tr in ORD_T:
    sub = df_t[df_t["tramo"]==tr]["pct_aprobacion"].dropna()
    stats_t[tr] = {"n": len(sub), "mediana": sub.median()}

print("=== TALLERES ===")
for tr in ORD_T:
    s = stats_t[tr]
    print(f"  {tr:10}: n={s['n']:3d} | mediana={s['mediana']:.1f}%")

medianas_t = [stats_t[t]["mediana"] for t in ORD_T]
ns_t       = [stats_t[t]["n"]       for t in ORD_T]
colores_t  = [C_CTRL] + [C_TALL]*4

fig, ax = plt.subplots(figsize=(13, 7))
fig.suptitle(
    "¿Es Acumulativo el Efecto de los Talleres?\n"
    "Tasa de Aprobación de Alumnos según N° de Talleres Cursados — Universo 917",
    fontsize=14, fontweight="bold", y=0.98)

x = np.arange(len(ORD_T))
labels_n = [f"{lbl}\n(n={n})" for lbl, n in zip(LABELS_T, ns_t)]

ax.bar(x, medianas_t, color=colores_t, alpha=0.85, width=0.6,
       edgecolor="white", linewidth=1.5)

for i, (m, color) in enumerate(zip(medianas_t, colores_t)):
    ax.text(i, m + 0.25, f"{m:.1f}%", ha="center", fontsize=12,
            fontweight="bold", color=color)

ax.plot(x[1:], medianas_t[1:], color=C_LINE, linewidth=2.5,
        linestyle="--", marker="D", markersize=9, alpha=0.85,
        label="Tendencia con talleres", zorder=5)

ax.axhline(medianas_t[0], color=C_CTRL, linewidth=1.8, linestyle=":",
           alpha=0.8, label=f"Mediana sin taller ({medianas_t[0]:.1f}%)")

ax.set_xticks(x)
ax.set_xticklabels(labels_n, fontsize=11)
ax.set_ylabel("% alumnos aprobados (mediana por docente)", fontsize=12)
ax.set_ylim(89, max(medianas_t) + 2)
ax.legend(fontsize=11, loc="lower right")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

fig.text(0.5, 0.01,
         "Nota: tasa de aprobación = % alumnos con nota ≥ 4.0 · Mediana por docente · Períodos 2023-2025.",
         ha="center", fontsize=9, color="#666666", fontstyle="italic")

plt.tight_layout(rect=[0, 0.04, 1, 0.95])
plt.savefig(OUT_TALLER, dpi=150, bbox_inches="tight")
plt.close()
print(f"Guardado: {OUT_TALLER}")

# ── GRÁFICO 2: Diplomados (comparación binaria) ───────────────────────────────
# Todos los que hicieron diplomado hicieron exactamente 1 — sin variación de intensidad
df_d = doc917[["rut_key"]].merge(
    n_por_tipo[["rut_key","DIPLOMADO"]], on="rut_key", how="left").fillna({"DIPLOMADO": 0})
df_d["grupo"] = df_d["DIPLOMADO"].apply(lambda n: "1 diplomado" if n >= 1 else "Sin diplomado")
df_d = df_d.merge(aprob, on="rut_key", how="inner")

stats_d = {}
for g in ["Sin diplomado","1 diplomado"]:
    sub = df_d[df_d["grupo"]==g]["pct_aprobacion"].dropna()
    stats_d[g] = {"n": len(sub), "mediana": sub.median()}

print("\n=== DIPLOMADOS ===")
for g, s in stats_d.items():
    print(f"  {g:20}: n={s['n']:3d} | mediana={s['mediana']:.1f}%")

ORD_D = ["Sin diplomado","1 diplomado"]
LABELS_D = ["Sin\ndiplomado","1\ndiplomado"]
medianas_d = [stats_d[g]["mediana"] for g in ORD_D]
ns_d       = [stats_d[g]["n"]       for g in ORD_D]
colores_d  = [C_CTRL, C_DIPL]
diff = medianas_d[1] - medianas_d[0]

fig, ax = plt.subplots(figsize=(9, 7))
fig.suptitle(
    "Efecto del Diplomado en Tasa de Aprobación\n"
    "Universo 917 · Todos los docentes con Diplomado cursaron exactamente 1",
    fontsize=14, fontweight="bold", y=0.98)

x = np.arange(2)
labels_n_d = [f"{lbl}\n(n={n})" for lbl, n in zip(LABELS_D, ns_d)]
bars = ax.bar(x, medianas_d, color=colores_d, alpha=0.85, width=0.5,
              edgecolor="white", linewidth=1.5)

for i, (m, color) in enumerate(zip(medianas_d, colores_d)):
    ax.text(i, m + 0.2, f"{m:.1f}%", ha="center", fontsize=14,
            fontweight="bold", color=color)

# Anotación de diferencia
ax.annotate("", xy=(1, medianas_d[1]), xytext=(0, medianas_d[0]),
            arrowprops=dict(arrowstyle="<->", color="#555", lw=2))
ax.text(0.5, (medianas_d[0]+medianas_d[1])/2, f"{diff:+.1f} pp",
        ha="center", va="center", fontsize=13, fontweight="bold",
        color=C_DIPL if diff >= 0 else "#C62828",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="#ccc"))

ax.set_xticks(x)
ax.set_xticklabels(labels_n_d, fontsize=13)
ax.set_ylabel("% alumnos aprobados (mediana por docente)", fontsize=12)
ymin = min(medianas_d) - 2
ax.set_ylim(ymin, max(medianas_d) + 3)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

nota_bin = ("Nota: No hay variación de intensidad en Diplomados — el 100% de los docentes\n"
            "que realizó un Diplomado cursó exactamente 1. Se muestra la comparación binaria.")
fig.text(0.5, 0.01, nota_bin, ha="center", fontsize=9,
         color="#666666", fontstyle="italic")

plt.tight_layout(rect=[0, 0.06, 1, 0.95])
plt.savefig(OUT_DIPLOMADO, dpi=150, bbox_inches="tight")
plt.close()
print(f"Guardado: {OUT_DIPLOMADO}")
