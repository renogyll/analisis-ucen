"""G4 — Heatmap Δ_z: jerarquía × tipo de formación"""
import nbformat as nbf

nb  = nbf.v4.new_notebook()
CSV = r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO\Downloads\Analisis_UCEN_v2\PROCESADO\p3_sat_zscore.csv"
OUT = r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO\Downloads\Analisis_UCEN_v2\NOTEBOOKS\G4_heatmap_jerarquia.png"

nb.cells = [

nbf.v4.new_markdown_cell("""\
# G4 — Heatmap Δ Z-score: Jerarquía × Tipo de formación
¿Instructores vs Titulares — quién responde mejor a cada tipo de capacitación?
Negrita = n ≥ 10. Asterisco = n < 5 (referencial).
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

jer_map = {{
    "INSTRUCTOR DOCENTE": "Instructor Doc.",
    "ASISTENTE DOCENTE":  "Asist. Docente",
    "ASISTENTE REGULAR":  "Asist. Regular",
    "ASOCIADO DOCENTE":   "Asoc. Docente",
    "ASOCIADO REGULAR":   "Asoc. Regular",
    "TITULAR DOCENTE":    "Titular Docente",
    "TITULAR REGULAR":    "Titular Regular",
}}
df["jer_short"] = df["jerarquia"].map(jer_map).fillna(df["jerarquia"])

# Orden Jr → Senior según jerarquía académica UCEN
ORD_JER  = ["Instructor Doc.","Asist. Docente","Asist. Regular",
            "Asoc. Docente","Asoc. Regular","Titular Docente","Titular Regular"]
ORD_TIPO = ["TALLER","DIPLOMADO","PROYECTO"]

piv_d = (df.groupby(["jer_short","tipo_principal"])["delta_z"]
           .mean().unstack().reindex(index=ORD_JER, columns=ORD_TIPO))
piv_n = (df.groupby(["jer_short","tipo_principal"])["delta_z"]
           .count().unstack().reindex(index=ORD_JER, columns=ORD_TIPO).fillna(0))

print("Delta Z por jerarquía × tipo:")
print(piv_d.round(3).to_string())

matplotlib.rcParams.update({{
    "font.size": 14, "axes.titlesize": 19, "axes.labelsize": 15,
    "xtick.labelsize": 14, "ytick.labelsize": 14,
}})

rows = [r for r in ORD_JER  if r in piv_d.index and piv_d.loc[r].notna().any()]
cols = [c for c in ORD_TIPO if c in piv_d.columns]
data = piv_d.reindex(index=rows, columns=cols).values.astype(float)

fig, ax = plt.subplots(figsize=(10, 7))
im = ax.imshow(data, cmap="RdYlGn", vmin=-0.5, vmax=0.5, aspect="auto")

ax.set_xticks(range(len(cols))); ax.set_xticklabels(cols, fontsize=14, fontweight="bold")
ax.set_yticks(range(len(rows))); ax.set_yticklabels(rows, fontsize=14)
ax.set_xlabel("Tipo de formación", fontsize=15)
ax.set_ylabel("Jerarquía académica", fontsize=15)
ax.set_title("Δ Z-score SAT\\nJerarquía × Tipo de formación", pad=14, fontsize=19, fontweight="bold")

for i, row in enumerate(rows):
    for j, col in enumerate(cols):
        delta = piv_d.loc[row, col] if (row in piv_d.index and col in piv_d.columns) else np.nan
        n     = int(piv_n.loc[row, col]) if (row in piv_n.index and col in piv_n.columns) else 0
        if pd.isna(delta) or n == 0:
            ax.add_patch(plt.Rectangle((j-0.5, i-0.5), 1, 1, color="#EEEEEE", zorder=2))
            ax.text(j, i, "—", ha="center", va="center", fontsize=16, color="#BBBBBB")
        else:
            sign   = "+" if delta >= 0 else ""
            txt_c  = "white" if abs(delta) > 0.30 else "black"
            weight = "bold" if n >= 10 else "normal"
            nota   = " *" if n < 5 else ""
            ax.text(j, i, f"{{sign}}{{delta:.2f}}{{nota}}\\nn={{n}}",
                    ha="center", va="center", fontsize=13,
                    fontweight=weight, color=txt_c)

cbar = plt.colorbar(im, ax=ax, label="Δ Z-score promedio", shrink=0.85)
cbar.ax.tick_params(labelsize=12)
cbar.set_label("Δ Z-score promedio", fontsize=13)
ax.spines[:].set_visible(False)

fig.text(0.5, -0.02,
         "Negrita = n ≥ 10  ·  * = n < 5 (baja confianza)  ·  — = sin datos",
         ha="center", fontsize=12, color="gray")

plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches="tight")
plt.show()
print(f"Guardado: {{OUT}}")
"""),

]

out = r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO\Downloads\Analisis_UCEN_v2\NOTEBOOKS\G4_heatmap_jerarquia.ipynb"
with open(out, "w", encoding="utf-8") as f:
    nbf.write(nb, f)
print(f"Creado: {out}")
