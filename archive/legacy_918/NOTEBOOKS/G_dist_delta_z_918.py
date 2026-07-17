import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib
import numpy as np
import os

BASE = os.path.dirname(__file__)
OUT  = os.path.join(BASE, "G_dist_delta_z_918.png")

matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 13, "axes.titlesize": 15, "axes.labelsize": 13,
    "xtick.labelsize": 12, "ytick.labelsize": 12, "legend.fontsize": 11,
})

p3 = pd.read_csv(os.path.join(BASE, "..", "PROCESADO", "p3_sat_zscore_918.csv"),
                 encoding="utf-8-sig", dtype={"rut_key": str})
p3["rut_key"] = p3["rut_key"].str.strip()

def tipo_p(r):
    if r["n_diplomado"] > 0: return "DIPLOMADO"
    if r["n_proyecto"]  > 0: return "PROYECTO"
    return "TALLER"
p3["tipo"] = p3.apply(tipo_p, axis=1)

TIPOS   = ["TALLER", "DIPLOMADO", "PROYECTO"]
COLORES = {"TALLER": "#2196F3", "DIPLOMADO": "#FF9800", "PROYECTO": "#4CAF50"}

# Estadísticos por tipo
print("=== Distribución Δ Z-score por tipo ===")
for t in TIPOS:
    sub = p3[p3["tipo"] == t]["delta_z"].dropna()
    pct_pos = (sub > 0).mean() * 100
    print(f"  {t} (n={len(sub)}): mediana={sub.median():+.3f} "
          f"| Q1={sub.quantile(.25):+.3f} Q3={sub.quantile(.75):+.3f} "
          f"| % mejora={pct_pos:.1f}%")

# ── Figura ─────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 7))

positions = {t: i for i, t in enumerate(TIPOS)}
bp_data   = [p3[p3["tipo"] == t]["delta_z"].dropna().values for t in TIPOS]

# Boxplot
bp = ax.boxplot(bp_data,
                positions=range(len(TIPOS)),
                widths=0.45,
                patch_artist=True,
                medianprops=dict(color="black", linewidth=2),
                whiskerprops=dict(linewidth=1.5),
                capprops=dict(linewidth=1.5),
                flierprops=dict(marker="o", markersize=4, alpha=0.4))

for patch, tipo in zip(bp["boxes"], TIPOS):
    patch.set_facecolor(COLORES[tipo])
    patch.set_alpha(0.65)

# Stripplot — puntos individuales
np.random.seed(42)
for i, tipo in enumerate(TIPOS):
    vals = p3[p3["tipo"] == tipo]["delta_z"].dropna().values
    jitter = np.random.uniform(-0.18, 0.18, size=len(vals))
    ax.scatter(i + jitter, vals,
               color=COLORES[tipo], alpha=0.35, s=22, zorder=3)

# Línea en 0
ax.axhline(0, color="#333333", linewidth=1.5, linestyle="--",
           alpha=0.7, label="Sin cambio (Δz = 0)")

# Anotaciones: n, mediana, % que mejoró
for i, tipo in enumerate(TIPOS):
    vals = p3[p3["tipo"] == tipo]["delta_z"].dropna()
    med  = vals.median()
    pct  = (vals > 0).mean() * 100
    ax.text(i, ax.get_ylim()[0] if ax.get_ylim()[0] < -0.8 else -1.05,
            f"n={len(vals)}\nmediana {med:+.2f}\n{pct:.0f}% mejora",
            ha="center", va="top", fontsize=11,
            color=COLORES[tipo], fontweight="bold")

ax.set_xticks(range(len(TIPOS)))
ax.set_xticklabels(TIPOS, fontsize=13, fontweight="bold")
ax.set_ylabel("Δ Z-score SAT (resultado − baseline)")
ax.set_title(
    "Distribución del cambio individual en Z-score SAT por tipo de formación\n"
    "Universo 917 · 197 docentes aptos P3 · Cada punto = 1 docente",
    pad=12, fontweight="bold")
all_vals = p3["delta_z"].dropna()
ypad = 0.15
ymin = all_vals.min() - ypad
ymax = all_vals.max() + ypad
ax.set_ylim(ymin, ymax)
ax.legend(loc="upper right", framealpha=0.9)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Zonas de mejora / retroceso
ax.axhspan(0,    ymax, alpha=0.03, color="#4CAF50")
ax.axhspan(ymin, 0,    alpha=0.03, color="#F44336")
ax.text(2.48, ymax - 0.1, "Mejoró ▲", ha="right", fontsize=10,
        color="#2E7D32", alpha=0.7, fontstyle="italic")
ax.text(2.48, ymin + 0.1, "Retrocedió ▼", ha="right", fontsize=10,
        color="#C62828", alpha=0.7, fontstyle="italic")

plt.tight_layout(rect=[0, 0.12, 1, 1])
plt.savefig(OUT, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nGuardado: {OUT}")

print("""
BAJADAS
• El gráfico revela que el cambio promedio cercano a cero no es homogéneo:
  dentro de cada tipo hay docentes que mejoran sustancialmente (Δz > +0.3)
  y otros que retroceden (Δz < −0.3). La formación no produce el mismo efecto
  en todos — el promedio esconde una distribución amplia.

• En TALLER, el grupo más numeroso (n=154), alrededor del 46% de los docentes
  mejoró su posición relativa en la facultad tras la formación. En DIPLOMADO
  (n=36), la dispersión es mayor pero con medianas también cercanas a cero,
  coherente con las pruebas t no significativas.
""")
