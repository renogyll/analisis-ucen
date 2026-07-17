import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os

BASE = os.path.dirname(__file__)
OUT  = os.path.join(BASE, "G10_concepto_edd_918.png")

matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 13, "axes.titlesize": 16, "axes.labelsize": 14,
    "xtick.labelsize": 12, "ytick.labelsize": 12, "legend.fontsize": 12,
})

# ── Cargar desde CSVs ─────────────────────────────────────────────────────────
df  = pd.read_csv(os.path.join(BASE, "..", "..", "PROCESADO",
                               "P1_consolidado_con_evaluacion_jefes.csv"),
                  encoding="utf-8-sig", dtype={"rut_key": str})
doc = pd.read_csv(os.path.join(BASE, "..", "PROCESADO", "docente_918.csv"),
                  encoding="utf-8-sig", dtype={"rut_key": str})
p3  = pd.read_csv(os.path.join(BASE, "..", "PROCESADO", "p3_sat_zscore_918.csv"),
                  encoding="utf-8-sig", dtype={"rut_key": str})

for d in [df, doc, p3]:
    d["rut_key"] = d["rut_key"].str.strip()

en_917 = df[df["rut_key"].isin(set(doc["rut_key"]))].copy()
en_917["formado"] = en_917["rut_key"].isin(set(p3["rut_key"]))
en_917["grupo"]   = en_917["formado"].map({True: "Formados", False: "Sin formación"})

con_concepto = en_917[en_917["concepto"].notna()].copy()

ORDER_CONCEPTO = ["Muy Bueno", "Bueno", "Insuficiente", "Deficiente"]
COLORS = {
    "Muy Bueno":    "#4CAF50",
    "Bueno":        "#8BC34A",
    "Insuficiente": "#FF9800",
    "Deficiente":   "#F44336",
}

grupos   = ["Formados", "Sin formación"]
tbl      = con_concepto.groupby(["grupo", "concepto"]).size().unstack(fill_value=0)
tbl_pct  = tbl.div(tbl.sum(axis=1), axis=0) * 100
tbl_pct  = tbl_pct.reindex(columns=ORDER_CONCEPTO, fill_value=0).reindex(grupos)
ns_grupo = con_concepto.groupby("grupo").size().reindex(grupos)

print("Distribución % por grupo:")
print(tbl_pct.round(1).to_string())
print("\nn por grupo:", ns_grupo.to_dict())

mb_f = tbl_pct.loc["Formados",      "Muy Bueno"]
mb_c = tbl_pct.loc["Sin formación", "Muy Bueno"]

# ── Figura ────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 7))

x      = np.arange(len(grupos))
bottom = np.zeros(len(grupos))

for concepto in ORDER_CONCEPTO:
    vals = tbl_pct[concepto].values
    bars = ax.bar(x, vals, bottom=bottom, color=COLORS[concepto],
                  label=concepto, width=0.5, edgecolor="white", linewidth=0.8)
    for i, (v, b) in enumerate(zip(vals, bottom)):
        if v >= 3:
            ax.text(x[i], b + v / 2, f"{v:.1f}%",
                    ha="center", va="center", fontsize=12,
                    fontweight="bold", color="white")
    bottom += vals

ax.set_xticks(x)
ax.set_xticklabels([f"{g}\n(n={ns_grupo[g]})" for g in grupos], fontsize=13)
ax.set_ylabel("% de docentes evaluados")
ax.set_ylim(0, 108)
ax.set_title(
    "Distribución de Concepto EDD — Formados vs Sin Formación\n"
    "Evaluación de Jefes · Universo 917",
    pad=14, fontweight="bold"
)

# Leyenda dentro del gráfico (evita expansión del bbox)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.09),
          ncol=4, framealpha=0.9, fontsize=12)

# Anotación diferencia Muy Bueno
ax.text(0.5, 102,
        f"Muy Bueno: {mb_f:.1f}% vs {mb_c:.1f}%  (+{mb_f-mb_c:.1f} pp formados)",
        ha="center", fontsize=12, color="#2E7D32", fontweight="bold",
        transform=ax.get_xaxis_transform())

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout(rect=[0, 0.10, 1, 1])
plt.savefig(OUT, dpi=150, bbox_inches="tight", pad_inches=0.3)
plt.close()
print(f"\nGuardado: {OUT}")
