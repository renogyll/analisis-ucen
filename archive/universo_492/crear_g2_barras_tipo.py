"""G2 — Barras horizontales: Δ_z y % mejora por tipo de formación"""
import nbformat as nbf

nb  = nbf.v4.new_notebook()
CSV = r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO\Downloads\Analisis_UCEN_v2\PROCESADO\p3_sat_zscore.csv"
OUT = r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO\Downloads\Analisis_UCEN_v2\NOTEBOOKS\G2_barras_tipo.png"

nb.cells = [

nbf.v4.new_markdown_cell("""\
# G2 — Δ Z-score SAT por tipo de formación
Cambio promedio en posición relativa (z_post − z_pre) y porcentaje de docentes que mejoró.
"""),

nbf.v4.new_code_cell(f"""\
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np

CSV = r"{CSV}"
OUT = r"{OUT}"

df = pd.read_csv(CSV, encoding="utf-8-sig")

def tipo_principal(row):
    if row["n_diplomado"] > 0: return "DIPLOMADO"
    if row["n_proyecto"]  > 0: return "PROYECTO"
    return "TALLER"

df["tipo_principal"] = df.apply(tipo_principal, axis=1)

agg = df.groupby("tipo_principal").agg(
    n          = ("rut_key",  "count"),
    delta_z    = ("delta_z",  "mean"),
    pct_mejora = ("mejoro_z", "mean"),
).round(3).reindex(["DIPLOMADO","PROYECTO","TALLER"])
agg["pct_mejora_100"] = (agg["pct_mejora"] * 100).round(1)
print(agg)

matplotlib.rcParams.update({{
    "font.size": 15, "axes.titlesize": 20, "axes.labelsize": 16,
    "xtick.labelsize": 15, "ytick.labelsize": 15,
}})

COLORES = {{"TALLER": "#2196F3", "DIPLOMADO": "#FF9800", "PROYECTO": "#4CAF50"}}
tipos   = agg.index.tolist()
colores = [COLORES[t] for t in tipos]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle("Impacto de la capacitación por tipo de formación\\n(Z-score SAT: posición relativa dentro de la facultad)",
             fontsize=19, fontweight="bold")

# Panel 1: Δ z
bars1 = ax1.barh(tipos, agg["delta_z"], color=colores, edgecolor="white", height=0.5)
ax1.axvline(0, color="gray", linewidth=1.2, linestyle="--")
ax1.set_xlabel("Δ Z-score promedio (pre → post)")
ax1.set_title("Cambio en posición relativa")
for bar, val, n in zip(bars1, agg["delta_z"], agg["n"]):
    sign = "+" if val >= 0 else ""
    ax1.text(val + (0.005 if val >= 0 else -0.005),
             bar.get_y() + bar.get_height()/2,
             f"{{sign}}{{val:.3f}}  (n={{int(n)}})",
             va="center", ha="left" if val >= 0 else "right",
             fontsize=14, fontweight="bold")
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)
ax1.set_xlim(-0.25, 0.40)

# Panel 2: % mejora
bars2 = ax2.barh(tipos, agg["pct_mejora_100"], color=colores, edgecolor="white", height=0.5)
ax2.axvline(50, color="gray", linewidth=1.2, linestyle="--", alpha=0.7)
ax2.set_xlabel("% de docentes que mejoró su z-score")
ax2.set_title("% docentes que mejoraron")
ax2.set_xlim(0, 100)
for bar, val in zip(bars2, agg["pct_mejora_100"]):
    ax2.text(val + 1.5, bar.get_y() + bar.get_height()/2,
             f"{{val:.0f}}%", va="center", fontsize=14, fontweight="bold")
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches="tight")
plt.show()
print(f"Guardado: {{OUT}}")
"""),

]

out = r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO\Downloads\Analisis_UCEN_v2\NOTEBOOKS\G2_barras_tipo.ipynb"
with open(out, "w", encoding="utf-8") as f:
    nbf.write(nb, f)
print(f"Creado: {out}")
