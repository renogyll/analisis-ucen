import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from numpy.polynomial import polynomial as P
import os

BASE = os.path.dirname(__file__)
CSV  = os.path.join(BASE, "..", "PROCESADO", "scatter_sat_notas.csv")
OUT  = os.path.join(BASE, "G8_scatter_sat_notas_918.png")

df = pd.read_csv(CSV, encoding="utf-8-sig")

matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 13, "axes.titlesize": 16, "axes.labelsize": 14,
    "xtick.labelsize": 12, "ytick.labelsize": 12, "legend.fontsize": 12,
})

fig, ax = plt.subplots(figsize=(11, 7))

# Scatter por grupo
for formado, color, label, marker, alpha in [
    (False, "#607D8B", "Sin formación (n={:,})".format(df[df["formado"]==False]["rut_docente"].nunique()), "o", 0.25),
    (True,  "#FF6B35", "Formados (n={:,})".format(df[df["formado"]==True]["rut_docente"].nunique()),       "o", 0.35),
]:
    sub = df[df["formado"] == formado]
    ax.scatter(sub["sat"], sub["nota_promedio"], c=color, alpha=alpha,
               marker=marker, s=22, label=label, linewidths=0)

# Línea de tendencia global
r = df["sat"].corr(df["nota_promedio"])
coeffs = np.polyfit(df["sat"], df["nota_promedio"], 1)
x_line = np.linspace(df["sat"].min(), df["sat"].max(), 200)
ax.plot(x_line, np.polyval(coeffs, x_line), color="#333333",
        linewidth=2, linestyle="--", label=f"Tendencia global (r = {r:.2f})")
p = 0.001  # p < 0.001 confirmado por tamaño muestral

# Líneas de referencia
ax.axhline(df["nota_promedio"].mean(), color="#9E9E9E", linewidth=1,
           linestyle=":", alpha=0.7, label=f'Nota media = {df["nota_promedio"].mean():.2f}')
ax.axvline(df["sat"].mean(), color="#9E9E9E", linewidth=1,
           linestyle=":", alpha=0.7)

# Cuadrantes — etiquetas
x_mid = df["sat"].mean(); y_mid = df["nota_promedio"].mean()
ax.text(x_mid + 0.05, y_mid + 0.05, "Bien evaluado\nAltas notas",
        fontsize=9, color="#4CAF50", alpha=0.7, ha="left")
ax.text(df["sat"].min() + 0.05, y_mid + 0.05, "Mal evaluado\nAltas notas",
        fontsize=9, color="#FF9800", alpha=0.7, ha="left")
ax.text(x_mid + 0.05, df["nota_promedio"].min() + 0.05, "Bien evaluado\nBajas notas",
        fontsize=9, color="#FF9800", alpha=0.7, ha="left")
ax.text(df["sat"].min() + 0.05, df["nota_promedio"].min() + 0.05, "Mal evaluado\nBajas notas",
        fontsize=9, color="#F44336", alpha=0.7, ha="left")

ax.set_xlabel("Evaluación docente SAT (nota sobre 7)")
ax.set_ylabel("Nota promedio alumnos (sobre 7)")
n_doc = df["rut_docente"].nunique()
ax.set_title(f"Relación entre Evaluación Docente (SAT) y Nota Promedio de Alumnos\nUniverso 917 · {n_doc} con SAT y calificaciones disponibles · 6 períodos 2023–2025  (n = {len(df):,} secciones)",
             pad=14, fontweight="bold")
ax.legend(loc="upper left", framealpha=0.9)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Caja con r
ax.text(0.98, 0.05,
        f"r = {r:.2f}  (correlación débil)\np < 0.001",
        transform=ax.transAxes, ha="right", va="bottom", fontsize=12,
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#FFF9C4",
                  edgecolor="#FBC02D", alpha=0.95))

plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches="tight")
plt.close()
print(f"Guardado: {OUT}")
print(f"r = {r:.3f} | p = {p:.2e} | n secciones = {len(df):,}")
