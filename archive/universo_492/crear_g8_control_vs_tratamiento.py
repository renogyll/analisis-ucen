"""G8 — Z-score longitudinal: grupo tratamiento vs grupo control"""
import nbformat as nbf

nb  = nbf.v4.new_notebook()
OUT = r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO\Downloads\Analisis_UCEN_v2\NOTEBOOKS\G8_control_vs_tratamiento.png"

nb.cells = [nbf.v4.new_code_cell(f"""\
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np

OUT = r"{OUT}"

# Datos calculados
data = {{
    "periodo":  ["2023-01","2023-02","2024-01","2024-02","2025-01","2025-02"],
    "z_trat":   [ 0.032,    0.098,    0.173,    0.153,    0.130,    0.132],
    "n_trat":   [  112,      113,      129,      124,      128,      105],
    "z_ctrl":   [-0.056,   -0.044,   -0.169,   -0.125,   -0.092,   -0.080],
    "n_ctrl":   [  135,      141,      162,      163,      187,      176],
}}
df = pd.DataFrame(data)

matplotlib.rcParams.update({{
    "font.size": 15, "axes.titlesize": 18, "axes.labelsize": 15,
    "xtick.labelsize": 13, "ytick.labelsize": 13, "legend.fontsize": 14,
}})

fig, ax = plt.subplots(figsize=(12, 7))

ax.plot(df["periodo"], df["z_trat"], marker="o", color="#FF9800",
        linewidth=2.5, markersize=10, label="Grupo tratamiento (130 docentes capacitados)")
ax.plot(df["periodo"], df["z_ctrl"], marker="s", color="#2196F3",
        linewidth=2.5, markersize=10, label="Grupo control (227 docentes sin formación)")

# Anotaciones finales
for i, row in df.iterrows():
    ax.annotate(f"{{row['z_trat']:+.3f}}",
                xy=(row["periodo"], row["z_trat"]),
                xytext=(0, 10), textcoords="offset points",
                ha="center", fontsize=12, color="#E65100", fontweight="bold")
    ax.annotate(f"{{row['z_ctrl']:+.3f}}",
                xy=(row["periodo"], row["z_ctrl"]),
                xytext=(0, -18), textcoords="offset points",
                ha="center", fontsize=12, color="#1565C0", fontweight="bold")

ax.axhline(0, color="gray", linewidth=1, linestyle="--", alpha=0.6)

# Sombreado brecha
ax.fill_between(df["periodo"], df["z_trat"], df["z_ctrl"],
                alpha=0.08, color="#FF9800", label="Brecha entre grupos")

ax.set_title("Evolución Z-score SAT: grupo tratamiento vs grupo control\\n"
             "Posición relativa dentro de la facultad (2023–2025)",
             pad=14, fontweight="bold")
ax.set_xlabel("Período")
ax.set_ylabel("Z-score promedio\\n(0 = promedio facultad)")
ax.legend(loc="upper left")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.set_ylim(-0.35, 0.35)

fig.text(0.5, -0.03,
         "El grupo de tratamiento se mantiene consistentemente sobre el promedio de su facultad.\\n"
         "El grupo control se mantiene bajo el promedio. La brecha se amplía en 2024.",
         ha="center", fontsize=12, color="gray")

plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches="tight")
plt.show()
print(f"Guardado: {{OUT}}")
""")]

out = r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO\Downloads\Analisis_UCEN_v2\NOTEBOOKS\G8_control_vs_tratamiento.ipynb"
with open(out, "w", encoding="utf-8") as f:
    nbf.write(nb, f)
print(f"Creado: {out}")
