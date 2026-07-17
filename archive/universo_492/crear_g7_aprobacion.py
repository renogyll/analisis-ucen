"""G7 — Tasas de aprobación/reprobación"""
import nbformat as nbf

nb  = nbf.v4.new_notebook()
OUT = r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO\Downloads\Analisis_UCEN_v2\NOTEBOOKS\G7_aprobacion.png"

nb.cells = [nbf.v4.new_code_cell(f"""\
import matplotlib.pyplot as plt
import matplotlib
import numpy as np

OUT = r"{OUT}"

matplotlib.rcParams.update({{
    "font.size": 15, "axes.titlesize": 17, "axes.labelsize": 15,
    "xtick.labelsize": 13, "ytick.labelsize": 13,
}})

# Datos
grupos = [
    "Institucional\\n(327.276 alumnos)",
    "338 asig.\\ncomparables\\n(100.711 alumnos)",
    "Docente\\nCAPACITADO\\n(19.994 alumnos)",
    "Docente\\nNO CAPACITADO\\n(80.717 alumnos)",
]
aprob  = [88.3, 85.2, 86.5, 84.9]
reprob = [11.7, 14.8, 13.5, 15.1]

x      = np.arange(len(grupos))
width  = 0.38
COLOR_AP = "#4CAF50"
COLOR_RP = "#F44336"

fig, ax = plt.subplots(figsize=(13, 7))
fig.suptitle("Tasa de aprobación y reprobación de alumnos\\nbajo los mismos supuestos del análisis comparativo",
             fontsize=17, fontweight="bold")

bars_a = ax.bar(x - width/2, aprob,  width, label="Aprobados",   color=COLOR_AP, alpha=0.88)
bars_r = ax.bar(x + width/2, reprob, width, label="Reprobados",  color=COLOR_RP, alpha=0.88)

for bar, val in zip(bars_a, aprob):
    ax.text(bar.get_x() + bar.get_width()/2, val + 0.5,
            f"{{val:.1f}}%", ha="center", fontsize=14, fontweight="bold", color="#2E7D32")

for bar, val in zip(bars_r, reprob):
    ax.text(bar.get_x() + bar.get_width()/2, val + 0.5,
            f"{{val:.1f}}%", ha="center", fontsize=14, fontweight="bold", color="#C62828")

# Resaltar diferencia cap vs no-cap
ax.annotate("", xy=(x[3] - width/2, 84.9), xytext=(x[2] - width/2, 86.5),
            arrowprops=dict(arrowstyle="<->", color="#555", lw=1.5))
ax.text((x[2] + x[3]) / 2 - width/2, 85.9, "+1.6 pp",
        ha="center", fontsize=12, color="#555", fontstyle="italic")

# Separador visual entre institucional y comparable
ax.axvline(1.5, color="#BBBBBB", linewidth=1.2, linestyle="--")
ax.text(1.52, 92, "338 asig. comparables →", fontsize=11, color="#888")

ax.set_xticks(x)
ax.set_xticklabels(grupos, fontsize=13)
ax.set_ylabel("% alumnos")
ax.set_ylim(0, 100)
ax.legend(fontsize=13)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches="tight")
plt.show()
print(f"Guardado: {{OUT}}")
""")]

out = r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO\Downloads\Analisis_UCEN_v2\NOTEBOOKS\G7_aprobacion.ipynb"
with open(out, "w", encoding="utf-8") as f:
    nbf.write(nb, f)
print(f"Creado: {out}")
