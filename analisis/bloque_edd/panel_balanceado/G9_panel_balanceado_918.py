import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os

BASE = os.path.dirname(__file__)
OUT  = os.path.join(BASE, "G9_panel_balanceado_918.png")

matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 13, "axes.titlesize": 16, "axes.labelsize": 14,
    "xtick.labelsize": 12, "ytick.labelsize": 12, "legend.fontsize": 12,
})

# ── Cargar ─────────────────────────────────────────────────────────────────────
edd = pd.read_csv(os.path.join(BASE, "..", "..", "PROCESADO",
                               "P1_consolidado_con_evaluacion_jefes.csv"),
                  encoding="utf-8-sig", dtype={"rut_key": str})
doc = pd.read_csv(os.path.join(BASE, "..", "PROCESADO", "docente_918.csv"),
                  encoding="utf-8-sig", dtype={"rut_key": str})
p3  = pd.read_csv(os.path.join(BASE, "..", "PROCESADO", "p3_sat_zscore_918.csv"),
                  encoding="utf-8-sig", dtype={"rut_key": str})

for d in [edd, doc, p3]: d["rut_key"] = d["rut_key"].str.strip()

# Filtrar universo 917, con EDD numérica, deduplicar Stippel
en_917 = edd[edd["rut_key"].isin(set(doc["rut_key"])) & edd["edd_total"].notna()].copy()
en_917["edd_total"] = pd.to_numeric(en_917["edd_total"], errors="coerce")
en_917 = en_917.dropna(subset=["edd_total"])
en_917["anio"] = en_917["anio_evaluacion"].astype(str).str[:4]
en_917 = en_917.drop_duplicates(subset=["rut_key", "anio"])
en_917["formado"] = en_917["rut_key"].isin(set(p3["rut_key"]))

ANIOS = ["2022", "2023", "2024", "2025"]

# ── Panel balanceado: solo docentes con EDD en los 4 años ─────────────────────
anios_por_doc = en_917.groupby("rut_key")["anio"].nunique()
ruts_4anios   = anios_por_doc[anios_por_doc == 4].index
panel         = en_917[en_917["rut_key"].isin(ruts_4anios)].copy()

n_total = panel["rut_key"].nunique()
n_form  = panel[panel["formado"] == True ]["rut_key"].nunique()
n_ctrl  = panel[panel["formado"] == False]["rut_key"].nunique()

print(f"Panel balanceado (4 años): {n_total} docentes — Formados: {n_form} | Control: {n_ctrl}")

agg = panel.groupby(["anio", "formado"])["edd_total"].agg(
    mean="mean", n="count").reset_index()

print("\nMedias EDD por año y grupo:")
print(agg.to_string())

# ── Figura ────────────────────────────────────────────────────────────────────
C_FORM = "#FF6B35"
C_CTRL = "#607D8B"

fig, ax = plt.subplots(figsize=(11, 7))

for formado, color, label, ls, marker in [
    (True,  C_FORM, f"Formados (n={n_form})",        "-",  "o"),
    (False, C_CTRL, f"Sin formación (n={n_ctrl})", "--", "s"),
]:
    sub = agg[agg["formado"] == formado].set_index("anio")
    ys  = [sub["mean"].get(a, np.nan) for a in ANIOS]
    ns  = [int(sub["n"].get(a, 0))    for a in ANIOS]

    ax.plot(range(len(ANIOS)), ys, marker=marker, color=color,
            linewidth=2.5, markersize=9, linestyle=ls, label=label)

    for i, (y, n) in enumerate(zip(ys, ns)):
        if not np.isnan(y):
            offset = 12 if formado else -22
            ax.annotate(f"{y:.3f}\n(n={n})", xy=(i, y),
                        xytext=(0, offset), textcoords="offset points",
                        ha="center", fontsize=10, color=color, fontweight="bold")

# Brecha 2025
y_f = agg[(agg["anio"] == "2025") & (agg["formado"] == True )]["mean"].values[0]
y_c = agg[(agg["anio"] == "2025") & (agg["formado"] == False)]["mean"].values[0]
brecha = y_f - y_c
ax.annotate("", xy=(3, y_c), xytext=(3, y_f),
            arrowprops=dict(arrowstyle="<->", color="#E53935", lw=1.8))
ax.text(3.08, (y_f + y_c) / 2, f"Brecha\n+{brecha:.3f}",
        color="#E53935", fontsize=11, fontweight="bold", va="center")

ax.fill_between(range(len(ANIOS)),
                [agg[(agg["anio"]==a)&(agg["formado"]==True )]["mean"].values[0] for a in ANIOS],
                [agg[(agg["anio"]==a)&(agg["formado"]==False)]["mean"].values[0] for a in ANIOS],
                alpha=0.07, color=C_FORM)

ax.axhline(0.75, color="gray", linewidth=1, linestyle=":", alpha=0.6,
           label="Umbral referencia (0.75)")
ax.set_xticks(range(len(ANIOS)))
ax.set_xticklabels(ANIOS)
ax.set_ylabel("EDD Total promedio (escala 0–1)")
ax.set_xlabel("Año de evaluación")
ax.set_ylim(0.5, 1.05)
ax.set_title(
    f"Evolución EDD — Panel Balanceado: Formados vs Sin Formación\n"
    f"Solo {n_total} docentes evaluados los 4 años consecutivos (2022–2025) · Universo 917",
    pad=14, fontweight="bold")
ax.legend(loc="lower left", framealpha=0.9)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

ax.text(0.98, 0.05,
        f"Panel balanceado: n={n_total}\n"
        f"Excluye {485-n_total} docentes con EDD\nen menos de 4 años",
        transform=ax.transAxes, ha="right", va="bottom", fontsize=10,
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#FFF9C4",
                  edgecolor="#FBC02D", alpha=0.9))

plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nGuardado: {OUT}")

# ── Bajadas ───────────────────────────────────────────────────────────────────
print(f"""
BAJADAS
• Al restringir el análisis a los {n_total} docentes evaluados en los 4 años consecutivos
  (panel balanceado), la brecha EDD entre formados y control en 2025 es de +{brecha:.3f} puntos,
  confirmando el hallazgo del análisis completo. El panel elimina el ruido de docentes
  que entran o salen del sistema, dejando visible la progresión real de los mismos individuos.

• La tendencia muestra que los docentes formados mantienen una EDD consistentemente
  superior a lo largo de todo el período 2022–2025, con la brecha ampliándose
  progresivamente desde 2023. Esto refuerza la hipótesis de un efecto acumulativo
  de la formación sobre la evaluación de jefes directos.
""")
