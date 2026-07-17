"""G5 — Barras Δ_z por sexo × tipo de formación"""
import nbformat as nbf

nb  = nbf.v4.new_notebook()
CSV = r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO\Downloads\Analisis_UCEN_v2\PROCESADO\p3_sat_zscore.csv"
OUT = r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO\Downloads\Analisis_UCEN_v2\NOTEBOOKS\G5_barras_sexo.png"

nb.cells = [

nbf.v4.new_markdown_cell("""\
# G5 — Δ Z-score SAT por sexo × tipo de formación
¿Existe diferencia en la respuesta a la capacitación entre hombres y mujeres?
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
df["sexo"] = df["sexo"].str.strip().str.upper()

agg = df.groupby(["sexo","tipo_principal"]).agg(
    n          = ("rut_key",  "count"),
    delta_z    = ("delta_z",  "mean"),
    pct_mejora = ("mejoro_z", "mean"),
).round(3)
print(agg.to_string())

matplotlib.rcParams.update({{
    "font.size": 15, "axes.titlesize": 20, "axes.labelsize": 16,
    "xtick.labelsize": 14, "ytick.labelsize": 14, "legend.fontsize": 14,
}})

TIPOS   = ["TALLER","DIPLOMADO","PROYECTO"]
SEXOS   = sorted(df["sexo"].dropna().unique())
COLORES = {{"F": "#E91E63", "M": "#2196F3", "FEMENINO": "#E91E63", "MASCULINO": "#2196F3"}}

x      = np.arange(len(TIPOS))
width  = 0.35
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
fig.suptitle("Δ Z-score SAT por Sexo × Tipo de formación", fontsize=20, fontweight="bold")

for i, sexo in enumerate(SEXOS):
    if sexo not in agg.index.get_level_values("sexo"):
        continue
    sub = agg.loc[sexo].reindex(TIPOS)
    vals_dz  = sub["delta_z"].values
    vals_pct = (sub["pct_mejora"] * 100).values
    ns       = sub["n"].values
    offset   = (i - len(SEXOS)/2 + 0.5) * width
    color    = COLORES.get(sexo, f"C{{i}}")

    bars1 = ax1.bar(x + offset, vals_dz,  width, label=sexo, color=color, alpha=0.85)
    bars2 = ax2.bar(x + offset, vals_pct, width, label=sexo, color=color, alpha=0.85)

    for bar, val, n in zip(bars1, vals_dz, ns):
        if pd.notna(val):
            sign = "+" if val >= 0 else ""
            ax1.text(bar.get_x() + bar.get_width()/2, val + (0.008 if val >= 0 else -0.012),
                     f"{{sign}}{{val:.2f}}\\n(n={{int(n)}})",
                     ha="center", va="bottom" if val >= 0 else "top",
                     fontsize=11, fontweight="bold", color=color)
    for bar, val in zip(bars2, vals_pct):
        if pd.notna(val):
            ax2.text(bar.get_x() + bar.get_width()/2, val + 1,
                     f"{{val:.0f}}%", ha="center", va="bottom",
                     fontsize=11, fontweight="bold", color=color)

ax1.axhline(0, color="gray", linewidth=1, linestyle="--")
ax1.set_xticks(x); ax1.set_xticklabels(TIPOS)
ax1.set_ylabel("Δ Z-score promedio"); ax1.set_title("Cambio en posición relativa")
ax1.legend(); ax1.spines["top"].set_visible(False); ax1.spines["right"].set_visible(False)

ax2.axhline(50, color="gray", linewidth=1, linestyle="--", alpha=0.7)
ax2.set_xticks(x); ax2.set_xticklabels(TIPOS)
ax2.set_ylabel("% de docentes que mejoró"); ax2.set_title("% docentes que mejoraron")
ax2.set_ylim(0, 105); ax2.legend()
ax2.spines["top"].set_visible(False); ax2.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches="tight")
plt.show()
print(f"Guardado: {{OUT}}")
"""),

]

out = r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO\Downloads\Analisis_UCEN_v2\NOTEBOOKS\G5_barras_sexo.ipynb"
with open(out, "w", encoding="utf-8") as f:
    nbf.write(nb, f)
print(f"Creado: {out}")
