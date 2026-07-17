import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os

BASE = os.path.dirname(__file__)
CSV  = os.path.join(BASE, "..", "PROCESADO", "scatter_sat_notas.csv")
OUT  = os.path.join(BASE, "G8_scatter_sat_notas_x_anio_918.png")

df = pd.read_csv(CSV, encoding="utf-8-sig")
df["anio"] = df["periodo"].str[:4].astype(int)

matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11, "axes.titlesize": 13, "axes.labelsize": 12,
    "xtick.labelsize": 10, "ytick.labelsize": 10, "legend.fontsize": 10,
})

C_CTRL  = "#607D8B"
C_FORM  = "#FF6B35"
C_TREND = "#333333"
AÑOS    = [2023, 2024, 2025]

fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=True)
fig.suptitle(
    "Relación entre Evaluación Docente (SAT) y Nota Promedio de Alumnos · Por Año\n"
    "Universo 816 con SAT y calificaciones disponibles · Períodos 2023–2025",
    fontsize=14, fontweight="bold", y=1.01
)

for ax, año in zip(axes, AÑOS):
    sub = df[df["anio"] == año].copy()
    n_sec = len(sub)

    # Scatter formados / control
    for formado, color, marker in [(False, C_CTRL, "o"), (True, C_FORM, "o")]:
        s = sub[sub["formado"] == formado]
        n_doc = s["rut_docente"].nunique()
        lbl = f"{'Formados' if formado else 'Sin formación'} (n={n_doc})"
        ax.scatter(s["sat"], s["nota_promedio"],
                   c=color, alpha=0.30, s=18, label=lbl,
                   linewidths=0, marker=marker)

    # Tendencia global del año
    r = sub["sat"].corr(sub["nota_promedio"])
    coeffs = np.polyfit(sub["sat"], sub["nota_promedio"], 1)
    x_line = np.linspace(sub["sat"].min(), sub["sat"].max(), 200)
    ax.plot(x_line, np.polyval(coeffs, x_line), color=C_TREND,
            linewidth=2, linestyle="--", label=f"Tendencia (r = {r:.2f})")

    # Referencias cruzadas (medias del año)
    x_mid = sub["sat"].mean()
    y_mid = sub["nota_promedio"].mean()
    ax.axhline(y_mid, color="#9E9E9E", linewidth=0.9, linestyle=":", alpha=0.6)
    ax.axvline(x_mid, color="#9E9E9E", linewidth=0.9, linestyle=":", alpha=0.6)

    # Caja r
    ax.text(0.97, 0.05, f"r = {r:.2f}\np < 0.001\n{n_sec:,} secciones",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=9,
            bbox=dict(boxstyle="round,pad=0.35", facecolor="#FFF9C4",
                      edgecolor="#FBC02D", alpha=0.95))

    ax.set_title(f"Año {año}", fontweight="bold", pad=8)
    ax.set_xlabel("SAT docente (sobre 7)")
    if ax == axes[0]:
        ax.set_ylabel("Nota promedio alumnos (sobre 7)")
    ax.legend(loc="upper left", fontsize=9, framealpha=0.85)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

# Cascada comparativa
print("=" * 65)
print("  SCATTER SAT × NOTAS — Por Año")
print("=" * 65)
for año in AÑOS:
    s = df[df["anio"] == año]
    r = s["sat"].corr(s["nota_promedio"])
    n_doc = s["rut_docente"].nunique()
    n_sec = len(s)
    n_form = s[s["formado"]]["rut_docente"].nunique()
    n_ctrl = s[~s["formado"]]["rut_docente"].nunique()
    print(f"  {año}: r={r:.3f} | {n_doc} docentes ({n_form} form / {n_ctrl} ctrl) | {n_sec:,} secciones")
print("=" * 65)

plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nGuardado: {OUT}")
