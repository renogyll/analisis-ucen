"""G6 — Delta nota y % cap mejor por tipo de formación"""
import nbformat as nbf

nb  = nbf.v4.new_notebook()
OUT = r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO\Downloads\Analisis_UCEN_v2\NOTEBOOKS\G6_delta_notas_tipo.png"
CSV = r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO\Downloads\Analisis_UCEN_v2\PROCESADO\notas_comparables.csv"

nb.cells = [nbf.v4.new_code_cell(f"""\
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np

OUT = r"{OUT}"
CSV = r"{CSV}"

df = pd.read_csv(CSV, encoding="utf-8-sig")

data = {{
    "tipo":        ["DIPLOMADO", "PROYECTO", "TALLER"],
    "n":           [196, 33, 104],
    "delta_nota":  [0.017, -0.011, -0.036],
    "pct_mejor":   [55.6, 48.5, 41.3],
}}
d = pd.DataFrame(data)

COLORES = {{"DIPLOMADO": "#FF9800", "PROYECTO": "#4CAF50", "TALLER": "#2196F3"}}
colores = [COLORES[t] for t in d["tipo"]]

matplotlib.rcParams.update({{
    "font.size": 15, "axes.titlesize": 18, "axes.labelsize": 15,
    "xtick.labelsize": 14, "ytick.labelsize": 14,
}})

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle("Notas de alumnos: docente capacitado vs no capacitado\\n338 asignaturas comparables · por tipo de formación",
             fontsize=17, fontweight="bold")

# Panel 1: Delta nota
bars1 = ax1.bar(d["tipo"], d["delta_nota"], color=colores, width=0.5, edgecolor="white")
ax1.axhline(0, color="gray", linewidth=1.2, linestyle="--")
ax1.set_title("Δ nota promedio\\n(cap − no cap)", pad=10)
ax1.set_ylabel("Δ nota (escala 1–7)")
ax1.set_ylim(-0.10, 0.08)
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)
for bar, val, n in zip(bars1, d["delta_nota"], d["n"]):
    sign = "+" if val >= 0 else ""
    ax1.text(bar.get_x() + bar.get_width()/2,
             val + (0.003 if val >= 0 else -0.005),
             f"{{sign}}{{val:.3f}}\\n(n={{n}} asig.)",
             ha="center", va="bottom" if val >= 0 else "top",
             fontsize=13, fontweight="bold")

# Panel 2: % cap mejor
bars2 = ax2.bar(d["tipo"], d["pct_mejor"], color=colores, width=0.5, edgecolor="white")
ax2.axhline(50, color="gray", linewidth=1.2, linestyle="--", alpha=0.7)
ax2.set_title("% asignaturas donde\\ncapacitado > no capacitado", pad=10)
ax2.set_ylabel("% asignaturas")
ax2.set_ylim(0, 80)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)
for bar, val in zip(bars2, d["pct_mejor"]):
    ax2.text(bar.get_x() + bar.get_width()/2, val + 1.5,
             f"{{val:.1f}}%", ha="center", fontsize=14, fontweight="bold")

fig.text(0.5, -0.03,
         "La línea punteada marca el umbral de neutralidad (Δ=0 y 50%)",
         ha="center", fontsize=12, color="gray")

plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches="tight")
plt.show()
print(f"Guardado: {{OUT}}")
""")]

out = r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO\Downloads\Analisis_UCEN_v2\NOTEBOOKS\G6_delta_notas_tipo.ipynb"
with open(out, "w", encoding="utf-8") as f:
    nbf.write(nb, f)
print(f"Creado: {out}")
