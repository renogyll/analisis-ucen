import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from sqlalchemy import create_engine, text
import os

engine = create_engine("postgresql://ucen_user:ucen2026@localhost:5432/ucen")
BASE = os.path.dirname(__file__)

matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 13, "axes.titlesize": 16, "axes.labelsize": 14,
    "xtick.labelsize": 12, "ytick.labelsize": 12, "legend.fontsize": 12,
})

# ── Cargar datos ──────────────────────────────────────────────────────────────
with engine.connect() as conn:
    df = pd.read_sql(text("SELECT * FROM consolidados.consolidado_jefes"), conn)
df["rut_key"] = df["rut_key"].astype(str).str.strip()

doc = pd.read_csv(os.path.join(BASE, "..", "PROCESADO", "docente_918.csv"),
                  encoding="utf-8-sig", dtype={"rut_key": str})
doc["rut_key"] = doc["rut_key"].str.strip()

p3 = pd.read_csv(os.path.join(BASE, "..", "PROCESADO", "p3_sat_zscore_918.csv"),
                 encoding="utf-8-sig", dtype={"rut_key": str})
p3["rut_key"] = p3["rut_key"].str.strip()

en_917 = df[df["rut_key"].isin(set(doc["rut_key"]))].copy()
en_917["formado"] = en_917["rut_key"].isin(set(p3["rut_key"]))
en_917["grupo"] = en_917["formado"].map({True: "Formados", False: "Sin formación"})

ANIOS = ["2022", "2023", "2024", "2025"]

# ── G9 — Evolución EDD total por año: formados vs sin formación ───────────────
edd = en_917[en_917["edd_total"].notna() & en_917["anio_evaluacion"].isin(ANIOS)]
agg = edd.groupby(["anio_evaluacion", "grupo"])["edd_total"].agg(
    mean="mean", n="count").reset_index()

fig, ax = plt.subplots(figsize=(11, 7))

for grupo, color, ls, marker in [
    ("Formados",       "#FF6B35", "-",  "o"),
    ("Sin formación",  "#607D8B", "--", "s"),
]:
    sub = agg[agg["grupo"] == grupo].set_index("anio_evaluacion")
    ys  = [sub["mean"].get(a, np.nan) for a in ANIOS]
    ns  = [int(sub["n"].get(a, 0))    for a in ANIOS]
    ax.plot(range(len(ANIOS)), ys, marker=marker, color=color,
            linewidth=2.5, markersize=9, linestyle=ls, label=grupo)
    for i, (y, n) in enumerate(zip(ys, ns)):
        if not np.isnan(y):
            offset = 12 if grupo == "Formados" else -20
            ax.annotate(f"{y:.3f}\n(n={n})", xy=(i, y),
                        xytext=(0, offset), textcoords="offset points",
                        ha="center", fontsize=10, color=color, fontweight="bold")

# Brecha 2025
y_f = agg[(agg["anio_evaluacion"]=="2025") & (agg["grupo"]=="Formados")]["mean"].values[0]
y_c = agg[(agg["anio_evaluacion"]=="2025") & (agg["grupo"]=="Sin formación")]["mean"].values[0]
ax.annotate("", xy=(3, y_c), xytext=(3, y_f),
            arrowprops=dict(arrowstyle="<->", color="#E53935", lw=1.8))
ax.text(3.08, (y_f + y_c) / 2, f"Brecha\n+{y_f-y_c:.3f}", color="#E53935",
        fontsize=11, fontweight="bold", va="center")

ax.fill_between(range(len(ANIOS)),
                [agg[(agg["anio_evaluacion"]==a)&(agg["grupo"]=="Formados")]["mean"].values[0]
                 if len(agg[(agg["anio_evaluacion"]==a)&(agg["grupo"]=="Formados")]) else np.nan
                 for a in ANIOS],
                [agg[(agg["anio_evaluacion"]==a)&(agg["grupo"]=="Sin formación")]["mean"].values[0]
                 if len(agg[(agg["anio_evaluacion"]==a)&(agg["grupo"]=="Sin formación")]) else np.nan
                 for a in ANIOS],
                alpha=0.07, color="#FF6B35")

ax.axhline(0.75, color="gray", linewidth=1, linestyle=":", alpha=0.6,
           label="Umbral referencia (0.75)")
ax.set_xticks(range(len(ANIOS))); ax.set_xticklabels(ANIOS)
ax.set_ylabel("EDD Total promedio (escala 0–1)")
ax.set_xlabel("Año de evaluación")
ax.set_ylim(0.5, 1.02)
n_edd_doc = edd["rut_key"].nunique()
n_edd_form = edd[edd["formado"]]["rut_key"].nunique()
n_edd_ctrl = edd[~edd["formado"]]["rut_key"].nunique()
ax.set_title(f"Evolución EDD Total — Formados vs Sin Formación\n"
             f"Universo 917 · {n_edd_doc} con EDD disponible ({n_edd_form} formados + {n_edd_ctrl} sin formación) · 2022–2025",
             pad=14, fontweight="bold")
ax.legend(loc="lower left", framealpha=0.9)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
plt.tight_layout()
out9 = os.path.join(BASE, "G9_edd_evolucion_918.png")
plt.savefig(out9, dpi=150, bbox_inches="tight")
plt.close()
print(f"Guardado: {out9}")

# ── G10 — Barras apiladas % concepto: formados vs sin formación ───────────────
con_concepto = en_917[en_917["concepto"].notna()].copy()
ORDER_CONCEPTO = ["Muy Bueno", "Bueno", "Insuficiente", "Deficiente"]
COLORS = {"Muy Bueno": "#4CAF50", "Bueno": "#8BC34A",
          "Insuficiente": "#FF9800", "Deficiente": "#F44336"}

tbl = con_concepto.groupby(["grupo", "concepto"]).size().unstack(fill_value=0)
tbl_pct = tbl.div(tbl.sum(axis=1), axis=0) * 100
tbl_pct = tbl_pct.reindex(columns=ORDER_CONCEPTO, fill_value=0)

grupos = ["Formados", "Sin formación"]
tbl_pct = tbl_pct.reindex(grupos)
ns_grupo = con_concepto.groupby("grupo").size().reindex(grupos)

fig, ax = plt.subplots(figsize=(10, 7))
x = np.arange(len(grupos))
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
ax.set_title(f"Distribución de Concepto EDD — Formados vs Sin Formación\n"
             f"Universo 917 · {n_edd_doc} con EDD disponible",
             pad=14, fontweight="bold")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.13),
          ncol=4, framealpha=0.9, fontsize=12)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.set_xlabel("")

# Anotar diferencia Muy Bueno
mb_f = tbl_pct.loc["Formados", "Muy Bueno"]
mb_c = tbl_pct.loc["Sin formación", "Muy Bueno"]
ax.text(0.5, 103, f"Muy Bueno: {mb_f:.1f}% vs {mb_c:.1f}%  (+{mb_f-mb_c:.1f}pp formados)",
        ha="center", fontsize=12, color="#2E7D32", fontweight="bold",
        transform=ax.get_xaxis_transform())

fig.subplots_adjust(bottom=0.18)
out10 = os.path.join(BASE, "G10_concepto_edd_918.png")
plt.savefig(out10, dpi=150, bbox_inches="tight")
plt.close()
print(f"Guardado: {out10}")
print("\nListo — G9 y G10 generados.")
