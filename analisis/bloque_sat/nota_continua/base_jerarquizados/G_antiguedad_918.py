import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os

BASE = os.path.dirname(__file__)
OUT  = os.path.join(BASE, "G_antiguedad_918.png")

matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 12, "axes.titlesize": 15, "axes.labelsize": 13,
    "xtick.labelsize": 11, "ytick.labelsize": 11, "legend.fontsize": 11,
})

doc = pd.read_csv(os.path.join(BASE,"..","PROCESADO","docente_918.csv"),
                  encoding="utf-8-sig", dtype={"rut_key": str})
doc["rut_key"]         = doc["rut_key"].str.strip()
doc["antiguedad_anios"] = pd.to_numeric(doc["antiguedad_anios"], errors="coerce")

con_ant = doc[doc["antiguedad_anios"].notna()].copy()
n_total = len(doc)
n_con   = len(con_ant)
n_sin   = n_total - n_con

ORD     = ["0-4","5-9","10-14","15-19","20-24","25-29","30+"]
COLORES = ["#1565C0","#1976D2","#1E88E5","#78909C","#E65100","#EF6C00","#C62828"]

tbl  = con_ant.groupby("tramo_antiguedad")["rut_key"].count().reindex(ORD).fillna(0).astype(int)
vals = [int(tbl.get(t, 0)) for t in ORD]
pcts = [100*v/n_con for v in vals]

ant_med  = con_ant["antiguedad_anios"].median()
ant_avg  = con_ant["antiguedad_anios"].mean()
n_noveles = int(tbl.get("0-4", 0))

# ── Cascada consola ────────────────────────────────────────────────────────────
print("=" * 60)
print("  UNIVERSO — Caracterización Docente por Antigüedad")
print("=" * 60)
print(f"  917 docentes jerarquizados (Universo 917)")
print(f"    ├── {n_con} CON datos de antigüedad  ← perfil completo (dotación)")
for tr, v in zip(ORD, vals):
    p = 100*v/n_con
    bar = "█" * (v // 8)
    print(f"    │     ├── {v:3d}  {tr} años  ({p:.1f}%)  {bar}")
print(f"    └── {n_sin} SIN datos de antigüedad  ← solo nómina")
print()
print(f"  Antigüedad promedio: {ant_avg:.1f} años  |  Mediana: {ant_med:.1f} años")
print(f"  Rango: {con_ant['antiguedad_anios'].min():.1f} – {con_ant['antiguedad_anios'].max():.1f} años")
print("=" * 60)

# ── Figura ────────────────────────────────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7))
fig.suptitle(
    "Caracterización por Antigüedad en la Institución — Cuerpo Docente Jerarquizado UCEN\n"
    f"Universo 917 · {n_con} docentes con dato de antigüedad · "
    f"Promedio {ant_avg:.1f} años · Mediana {ant_med:.1f} años",
    fontsize=13, fontweight="bold")

x = np.arange(len(ORD))

# Panel A — Barras
bars = ax1.bar(x, vals, width=0.65, color=COLORES, alpha=0.88, edgecolor="white")
for i, (v, p) in enumerate(zip(vals, pcts)):
    if v > 0:
        ax1.text(i, v + 2, f"{v}\n({p:.1f}%)", ha="center",
                 fontsize=10, fontweight="bold", color="#222222")

# Franja 0-9 años
ax1.axvspan(-0.4, 1.4, alpha=0.06, color="#1565C0", zorder=0)
n_recientes = vals[0] + vals[1]
ax1.text(0.5, max(vals)*0.78,
         f"Ingreso reciente\n0–9 años\n{n_recientes} doc. ({100*n_recientes/n_con:.0f}%)",
         ha="center", fontsize=9, color="#1565C0", alpha=0.85, fontstyle="italic")

ax1.axvline(0.8, color="#333333", linewidth=1.5, linestyle="--", alpha=0.5)
ax1.text(0.88, max(vals)*0.92, f"Mediana\n{ant_med:.1f} años",
         fontsize=9, color="#333333", fontstyle="italic")

ax1.set_xticks(x)
ax1.set_xticklabels([t+" años" for t in ORD], rotation=30, ha="right", fontsize=10)
ax1.set_ylabel("N° docentes")
ax1.set_title("Distribución por tramo de antigüedad", pad=10)
ax1.set_ylim(0, max(vals)*1.2)
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)

# Panel B — Acumulado
acum  = np.cumsum(vals)
acum_pct = [100*a/n_con for a in acum]

ax2.fill_between(range(len(ORD)), acum_pct, alpha=0.18, color="#1565C0")
ax2.plot(range(len(ORD)), acum_pct, marker="o", color="#1565C0",
         linewidth=2.5, markersize=9)

for i, (a, v) in enumerate(zip(acum_pct, vals)):
    ax2.annotate(f"{a:.0f}%", xy=(i, a), xytext=(0, 10),
                 textcoords="offset points", ha="center",
                 fontsize=10, fontweight="bold", color="#1565C0")

ax2.axhline(50, color="gray", linewidth=1, linestyle=":", alpha=0.6)
ax2.axhline(80, color="gray", linewidth=1, linestyle=":", alpha=0.6)
ax2.text(len(ORD)-0.5, 51, "50%", fontsize=9, color="gray", ha="right")
ax2.text(len(ORD)-0.5, 81, "80%", fontsize=9, color="gray", ha="right")

ax2.set_xticks(range(len(ORD)))
ax2.set_xticklabels([t+" años" for t in ORD], rotation=30, ha="right", fontsize=10)
ax2.set_ylabel("% acumulado de docentes")
ax2.set_title("Curva acumulada de antigüedad", pad=10)
ax2.set_ylim(0, 108)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nGuardado: {OUT}")

n_recientes = vals[0] + vals[1]
n_veteranos = sum(vals[4:])
print(f"""
BAJADAS
• El cuerpo docente jerarquizado de UCEN presenta una antigüedad mediana de
  {ant_med:.1f} años, con el {100*n_recientes/n_con:.0f}% de los docentes con menos de 10 años
  en la institución (n={n_recientes}). Este perfil de ingreso reciente convive con
  una edad promedio de 48 años, lo que sugiere que una parte importante del
  cuerpo académico llegó a UCEN en etapas avanzadas de su carrera profesional.

• El {100*n_noveles/n_con:.0f}% de los docentes con datos (n={n_noveles}) tiene entre 0 y 4 años
  de antigüedad, configurando el tramo más numeroso con diferencia. Solo
  {n_veteranos} docentes ({100*n_veteranos/n_con:.1f}%) superan los 20 años en la institución,
  lo que evidencia una dotación académica en proceso de consolidación
  institucional más que de larga data.
""")
