import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os

BASE = os.path.dirname(__file__)
CSV  = os.path.join(BASE, "..", "PROCESADO", "control_vs_trat_918.csv")
OUT  = os.path.join(BASE, "G6_control_vs_tratamiento_918.png")

df = pd.read_csv(CSV, encoding="utf-8-sig")

matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 14, "axes.titlesize": 17, "axes.labelsize": 15,
    "xtick.labelsize": 13, "ytick.labelsize": 13, "legend.fontsize": 13,
})

fig, ax = plt.subplots(figsize=(12, 7))

# Tratamiento
ax.plot(df["periodo"], df["z_trat"], marker="o", color="#FF6B35",
        linewidth=2.5, markersize=9, label="Grupo Tratamiento (formados)")
for _, row in df.iterrows():
    ax.annotate(f"{row['z_trat']:+.3f}\n(n={int(row['n_trat'])})",
                xy=(row["periodo"], row["z_trat"]),
                xytext=(0, 12), textcoords="offset points",
                ha="center", fontsize=10, color="#FF6B35", fontweight="bold")

# Control
ax.plot(df["periodo"], df["z_ctrl"], marker="s", color="#607D8B",
        linewidth=2.5, markersize=9, linestyle="--",
        label="Grupo Control (sin formación)")
for _, row in df.iterrows():
    ax.annotate(f"{row['z_ctrl']:+.3f}\n(n={int(row['n_ctrl'])})",
                xy=(row["periodo"], row["z_ctrl"]),
                xytext=(0, -22), textcoords="offset points",
                ha="center", fontsize=10, color="#607D8B", fontweight="bold")

# Línea cero
ax.axhline(0, color="gray", linewidth=1, linestyle=":", alpha=0.7,
           label="Promedio facultad (z=0)")

# Sombreado diferencia
ax.fill_between(df["periodo"], df["z_trat"], df["z_ctrl"],
                alpha=0.08, color="#FF6B35", label="Brecha tratamiento − control")

n_doc_total = len(set(list(df["n_trat"].astype(int)) + list(df["n_ctrl"].astype(int))))
ax.set_title("Z-score SAT Nota por período — Grupo Tratamiento vs Grupo Control\n"
             "Universo 917 · 816 con SAT disponible · n fluctúa por período según carga académica",
             pad=14, fontweight="bold")
ax.set_ylabel("Z-score promedio\n(posición relativa en facultad)")
ax.set_xlabel("Período")
ax.set_ylim(-0.30, 0.35)
ax.legend(loc="upper left")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Calcular brecha promedio
brecha = (df["z_trat"] - df["z_ctrl"]).mean()
ax.text(0.98, 0.05,
        f"Brecha media: {brecha:+.3f} z\n(~{brecha*38:.0f} percentiles)",
        transform=ax.transAxes, ha="right", va="bottom",
        fontsize=12, color="#333333",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#FFF9C4", edgecolor="#FBC02D", alpha=0.9))

plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches="tight")
plt.close()
print(f"Guardado: {OUT}")
print(f"\nBrecha promedio tratamiento − control: {brecha:+.4f} z")
print(f"En percentiles aprox.: +{brecha*38:.0f} percentiles de ventaja del grupo tratado")
