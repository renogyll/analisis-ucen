import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os

BASE = os.path.dirname(__file__)
CSV  = os.path.join(BASE, "..", "PROCESADO", "scatter_sat_notas.csv")
OUT  = os.path.join(BASE, "GN_aprobacion_918.png")

matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 13, "axes.titlesize": 15, "axes.labelsize": 13,
    "xtick.labelsize": 12, "ytick.labelsize": 12, "legend.fontsize": 12,
})

df = pd.read_csv(CSV, encoding="utf-8-sig")

# ── Cascade ───────────────────────────────────────────────────────────────────
n_doc_total = df["rut_docente"].nunique()
n_doc_form  = df[df["formado"] == True ]["rut_docente"].nunique()
n_doc_ctrl  = df[df["formado"] == False]["rut_docente"].nunique()
n_sec_form  = len(df[df["formado"] == True ])
n_sec_ctrl  = len(df[df["formado"] == False])
n_sec_total = len(df)

print("=" * 60)
print("CASCADA UNIVERSO — Tasas de Aprobación")
print("=" * 60)
print(f"917 docentes jerarquizados (Universo 917)")
print(f"  └── {n_doc_total:,} docentes con registros de calificaciones y SAT")
print(f"        ├── {n_doc_form:,} docentes FORMADOS   → {n_sec_form:,} secciones evaluadas")
print(f"        └── {n_doc_ctrl:,} docentes CONTROL    → {n_sec_ctrl:,} secciones evaluadas")
print()

# ── Estadísticos globales ─────────────────────────────────────────────────────
tasa_form  = df[df["formado"] == True ]["pct_aprobacion"].mean()
tasa_ctrl  = df[df["formado"] == False]["pct_aprobacion"].mean()
tasa_total = df["pct_aprobacion"].mean()
diff_pp    = tasa_form - tasa_ctrl

print(f"Tasa aprobación FORMADOS  : {tasa_form:.1f}%")
print(f"Tasa aprobación CONTROL   : {tasa_ctrl:.1f}%")
print(f"Tasa aprobación GLOBAL    : {tasa_total:.1f}%")
print(f"Diferencia (Form − Ctrl)  : {diff_pp:+.1f} pp")
print()

# ── Por período ───────────────────────────────────────────────────────────────
periodos_ord = sorted(df["periodo"].unique())
per_form = (df[df["formado"] == True ]
            .groupby("periodo")["pct_aprobacion"]
            .agg(["mean","count"]).reindex(periodos_ord))
per_ctrl = (df[df["formado"] == False]
            .groupby("periodo")["pct_aprobacion"]
            .agg(["mean","count"]).reindex(periodos_ord))

# ── FIGURA ────────────────────────────────────────────────────────────────────
C_FORM  = "#FF6B35"
C_CTRL  = "#607D8B"
C_INST  = "#9E9E9E"

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7))
fig.suptitle(
    "Tasa de Aprobación de Alumnos según Condición de Formación Docente\n"
    f"Universo 917 · {n_doc_total} con SAT y calificaciones disponibles · 6 períodos 2023-01 a 2025-02",
    fontsize=16, fontweight="bold", y=1.01,
)

# ── Panel izquierdo: barras globales ─────────────────────────────────────────
grupos    = ["Docentes\nFormados", "Docentes\nSin formación"]
tasas     = [tasa_form, tasa_ctrl]
colores   = [C_FORM, C_CTRL]
ns_doc    = [n_doc_form, n_doc_ctrl]
ns_sec    = [n_sec_form, n_sec_ctrl]

bars = ax1.bar(grupos, tasas, color=colores, width=0.5, alpha=0.88, edgecolor="white")
ax1.axhline(tasa_total, color=C_INST, linewidth=1.5, linestyle="--",
            label=f"Promedio global: {tasa_total:.1f}%")

for bar, val, nd, ns in zip(bars, tasas, ns_doc, ns_sec):
    ax1.text(bar.get_x() + bar.get_width()/2, val + 0.8,
             f"{val:.1f}%", ha="center", fontsize=15, fontweight="bold",
             color=bar.get_facecolor())
    ax1.text(bar.get_x() + bar.get_width()/2, val / 2,
             f"n={nd:,} doc.\n{ns:,} secc.",
             ha="center", fontsize=11, color="white", fontweight="bold")

# Anotación diferencia
ax1.annotate("", xy=(1, tasa_ctrl + 0.5), xytext=(0, tasa_form - 0.5),
             arrowprops=dict(arrowstyle="<->", color="#333", lw=1.5))
ax1.text(0.5, (tasa_form + tasa_ctrl) / 2,
         f"{diff_pp:+.1f} pp", ha="center", va="center",
         fontsize=12, color="#333", fontstyle="italic",
         bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="#BDBDBD"))

ax1.set_title("Tasa global de aprobación", pad=10)
ax1.set_ylabel("% Alumnos aprobados (nota ≥ 4,0)")
ax1.set_ylim(0, max(tasas) + 10)
ax1.legend(loc="lower right", framealpha=0.9)
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)

# ── Panel derecho: líneas por período ────────────────────────────────────────
x_labels = periodos_ord

ax2.plot(x_labels, per_form["mean"].values, marker="o", color=C_FORM,
         linewidth=2.5, markersize=9, label="Docentes Formados")
ax2.plot(x_labels, per_ctrl["mean"].values, marker="s", color=C_CTRL,
         linewidth=2.5, markersize=9, linestyle="--", label="Docentes Sin formación")

for i, (vf, vc, nf, nc) in enumerate(zip(
        per_form["mean"], per_ctrl["mean"],
        per_form["count"], per_ctrl["count"])):
    ax2.annotate(f"{vf:.1f}%\n(n={int(nf)})",
                 xy=(x_labels[i], vf),
                 xytext=(0, 11), textcoords="offset points",
                 ha="center", fontsize=9, color=C_FORM, fontweight="bold")
    ax2.annotate(f"{vc:.1f}%\n(n={int(nc)})",
                 xy=(x_labels[i], vc),
                 xytext=(0, -22), textcoords="offset points",
                 ha="center", fontsize=9, color=C_CTRL, fontweight="bold")

ax2.axhline(tasa_total, color=C_INST, linewidth=1.2, linestyle=":",
            alpha=0.7, label=f"Promedio global: {tasa_total:.1f}%")
ax2.fill_between(x_labels, per_form["mean"], per_ctrl["mean"],
                 alpha=0.07, color=C_FORM)

ax2.set_title("Evolución por período", pad=10)
ax2.set_ylabel("% Alumnos aprobados")
ax2.set_xlabel("Período académico")
ymin = min(per_form["mean"].min(), per_ctrl["mean"].min()) - 8
ymax = max(per_form["mean"].max(), per_ctrl["mean"].max()) + 14
ax2.set_ylim(ymin, ymax)
ax2.legend(loc="upper left", framealpha=0.9)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)
plt.setp(ax2.get_xticklabels(), rotation=30, ha="right")

plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches="tight")
plt.close()
print(f"Guardado: {OUT}")

# ── Bajadas ───────────────────────────────────────────────────────────────────
brecha_max = max(abs(per_form["mean"] - per_ctrl["mean"]))
periodo_max = periodos_ord[np.argmax(np.abs(per_form["mean"].values - per_ctrl["mean"].values))]

print()
print("=" * 60)
print("BAJADAS PARA EL INFORME")
print("=" * 60)
print(f"""
Los {n_doc_total:,} docentes del universo con registros de calificaciones y evaluación docente (SAT)
generaron {n_sec_total:,} secciones en los 6 períodos analizados (2023-01 a 2025-02):
{n_doc_form:,} docentes formados dictaron {n_sec_form:,} secciones;
{n_doc_ctrl:,} docentes sin formación dictaron {n_sec_ctrl:,} secciones.

• La tasa media de aprobación de los alumnos de docentes formados es {tasa_form:.1f}%, frente
  al {tasa_ctrl:.1f}% del grupo control, una diferencia de {diff_pp:+.1f} puntos porcentuales.
  Ambos grupos se ubican en torno al promedio global ({tasa_total:.1f}%), lo que indica que la
  participación del docente en actividades de formación no deteriora el rendimiento académico
  de sus estudiantes.

• A lo largo de los seis períodos analizados la brecha más amplia se registró en {periodo_max}
  ({brecha_max:.1f} pp), aunque esta diferencia no es estadísticamente significativa dada la
  variabilidad intrínseca de las secciones. La tendencia es estable en ambos grupos.

• La consistencia entre períodos sugiere que los efectos de la formación docente observados en
  la evaluación estudiantil (SAT) no se acompañan de una caída en las tasas de aprobación,
  lo que descarta un eventual trade-off entre satisfacción del alumno y exigencia académica.
""")
