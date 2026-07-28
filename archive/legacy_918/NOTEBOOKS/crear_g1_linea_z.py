"""G1 — Línea z_pre → z_durante → z_post por tipo de formación"""
import nbformat as nbf, os

nb  = nbf.v4.new_notebook()
CSV = r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO\Downloads\Analisis_UCEN_v2\PROCESADO\p3_sat_zscore.csv"
OUT = r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO\Downloads\Analisis_UCEN_v2\NOTEBOOKS\G1_linea_z.png"

nb.cells = [

nbf.v4.new_markdown_cell("""\
# G1 — Trayectoria Z-score SAT: pre → durante → post
Evolución de la posición relativa del docente dentro de su facultad,
antes, durante y después de la capacitación. Por tipo de formación.
"""),

nbf.v4.new_code_cell(f"""\
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np

CSV = r"{CSV}"
OUT = r"{OUT}"

df = pd.read_csv(CSV, encoding="utf-8-sig")

# Tipo principal: si participó en diplomado → DIPLOMADO, proyecto → PROYECTO, si no → TALLER
def tipo_principal(row):
    if row["n_diplomado"] > 0: return "DIPLOMADO"
    if row["n_proyecto"]  > 0: return "PROYECTO"
    return "TALLER"

df["tipo_principal"] = df.apply(tipo_principal, axis=1)

# Agregado por tipo
agg = df.groupby("tipo_principal").agg(
    n        = ("rut_key",    "count"),
    z_pre    = ("z_pre",      "mean"),
    z_durante= ("z_durante",  "mean"),
    z_post   = ("z_post",     "mean"),
).round(3)
print(agg)

# Paleta y orden
TIPOS  = ["TALLER", "DIPLOMADO", "PROYECTO"]
COLORES= {{"TALLER": "#2196F3", "DIPLOMADO": "#FF9800", "PROYECTO": "#4CAF50"}}
MARCAS = {{"TALLER": "o",        "DIPLOMADO": "s",       "PROYECTO": "^"}}

matplotlib.rcParams.update({{
    "font.size": 15, "axes.titlesize": 20, "axes.labelsize": 16,
    "xtick.labelsize": 15, "ytick.labelsize": 15, "legend.fontsize": 14,
}})

fig, ax = plt.subplots(figsize=(11, 7))

for tipo in TIPOS:
    if tipo not in agg.index:
        continue
    row = agg.loc[tipo]
    n   = int(row["n"])
    # Puntos disponibles
    pts = {{"pre": row["z_pre"], "durante": row["z_durante"], "post": row["z_post"]}}
    xs, ys = [], []
    for lbl, val in pts.items():
        if pd.notna(val):
            xs.append(lbl)
            ys.append(val)
    ax.plot(xs, ys, marker=MARCAS[tipo], color=COLORES[tipo],
            linewidth=2.5, markersize=10, label=f"{{tipo}} (n={{n}})")
    # Anotar último punto
    ax.annotate(f"{{ys[-1]:+.3f}}", xy=(xs[-1], ys[-1]),
                xytext=(8, 0), textcoords="offset points",
                fontsize=13, color=COLORES[tipo], fontweight="bold")

ax.axhline(0, color="gray", linewidth=1, linestyle="--", alpha=0.6)
ax.set_title("Trayectoria Z-score SAT\\npre → durante → post capacitación", pad=16)
ax.set_xlabel("Momento de evaluación")
ax.set_ylabel("Z-score promedio\\n(posición relativa en facultad)")
ax.legend(loc="upper left")
ax.set_ylim(-0.6, 0.8)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches="tight")
plt.show()
print(f"Guardado: {{OUT}}")
"""),

]

out = r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO\Downloads\Analisis_UCEN_v2\NOTEBOOKS\G1_linea_z.ipynb"
with open(out, "w", encoding="utf-8") as f:
    nbf.write(nb, f)
print(f"Creado: {out}")
