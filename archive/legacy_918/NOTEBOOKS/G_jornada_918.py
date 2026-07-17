import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib
import numpy as np
import os

BASE = os.path.dirname(__file__)
OUT  = os.path.join(BASE, "G_jornada_918.png")

matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11, "axes.titlesize": 14, "axes.labelsize": 12,
})

# ── Cargar datos ──────────────────────────────────────────────────────────────
doc917 = pd.read_csv(os.path.join(BASE,"..","PROCESADO","docente_918.csv"),
                     encoding="utf-8-sig", dtype={"rut_key": str})
doc917["rut_key"] = doc917["rut_key"].str.strip()

dot = pd.read_csv(
    os.path.join(BASE,"..","..","CONSOLIDADO DOCENTES 3-05-2026",
                 "CONSOLIDADO DOCENTES 3-05-2026.xlsx - DOTACION.csv"),
    dtype=str, encoding="utf-8-sig")
dot.columns = dot.columns.str.strip()
dot["rut_key"] = (dot["RUT"].str.strip()
                  .str.replace(".", "", regex=False)
                  .str.split("-").str[0].str.strip())

dot917 = dot[dot["rut_key"].isin(set(doc917["rut_key"]))].copy()
dot917["JORNADA"] = dot917["JORNADA"].str.strip()

# ── Mapeo a 3 categorías ──────────────────────────────────────────────────────
MAPEO_JORNADA = {
    "44 Horas Semanales":            "Planta Activa",
    "33 Horas Semanales":            "Planta Activa",
    "40 Horas Semanales":            "Planta Activa",
    "39 Horas Semanales":            "Planta Activa",
    "36 Horas Semanales":            "Planta Activa",
    "22 Horas Semanales":            "Parcial de Planta",
    "32 Horas Semanales":            "Parcial de Planta",
    "Jornada indefinida Variable":   "Parcial de Planta",
    "11 Horas Semanales":            "Por Hora / Externos",
    "6 horas semanales":             "Por Hora / Externos",
}
dot917["categoria_jornada"] = dot917["JORNADA"].map(MAPEO_JORNADA)

df = dot917[dot917["categoria_jornada"].notna()].copy()

CATS   = ["Planta Activa", "Parcial de Planta", "Por Hora / Externos"]
COLORES = ["#1565C0", "#E65100", "#6A1B9A"]
LABELS  = ["Jornadas de\nPlanta Activa\n(44, 40, 39, 36, 33 h)",
           "Jornadas Parciales\nde Planta\n(22, 32 h + Indef. Variable)",
           "Docentes por Hora\n/ Externos\n(11, 6 h)"]

n_total  = len(doc917)
n_dot    = len(dot917)
n_clasif = len(df)
n_sin    = n_total - n_dot

conteo = df["categoria_jornada"].value_counts()
vals   = [int(conteo.get(c, 0)) for c in CATS]
pcts   = [100*v/n_clasif for v in vals]

# Desglose por jornada original
desglose = df.groupby(["categoria_jornada","JORNADA"])["rut_key"].count().reset_index()

# ── Cascada ───────────────────────────────────────────────────────────────────
print("=" * 65)
print("  DISTRIBUCIÓN DE TIPO DE JORNADA (Universo 917)")
print("=" * 65)
print(f"  917 docentes jerarquizados")
print(f"    ├── {n_dot} con jornada en dotación → {n_clasif} clasificados")
for cat, v, p, color in zip(CATS, vals, pcts, COLORES):
    print(f"    │     ├── {v:3d} ({p:.1f}%)  {cat}")
    sub = desglose[desglose["categoria_jornada"]==cat]
    for _, row in sub.iterrows():
        print(f"    │     │       └── {row['JORNADA']}: {row['rut_key']}")
print(f"    └── {n_sin} sin datos de dotación (solo nómina)")
print("=" * 65)

# ── Figura: dona + barras ─────────────────────────────────────────────────────
fig, (ax_dona, ax_bar) = plt.subplots(1, 2, figsize=(16, 7),
                                       gridspec_kw={"width_ratios": [1, 1.3]})
fig.suptitle(
    "Distribución por Tipo de Jornada — Cuerpo Docente Jerarquizado UCEN\n"
    f"Universo 917 · {n_clasif} docentes con jornada clasificada en dotación",
    fontsize=13, fontweight="bold")

# Panel A — Dona
wedges, _ = ax_dona.pie(
    vals, colors=COLORES, startangle=90, counterclock=False,
    wedgeprops=dict(width=0.55, edgecolor="white", linewidth=2.5))

for wedge, cat, lbl, v, p, color in zip(wedges, CATS, LABELS, vals, pcts, COLORES):
    ang = (wedge.theta2 + wedge.theta1) / 2
    x   = 0.75 * np.cos(np.radians(ang))
    y   = 0.75 * np.sin(np.radians(ang))
    x2  = 1.25 * np.cos(np.radians(ang))
    y2  = 1.25 * np.sin(np.radians(ang))
    ha  = "left" if x2 > 0 else "right"
    ax_dona.annotate(
        f"{lbl}\n{v} doc. ({p:.1f}%)",
        xy=(x, y), xytext=(x2, y2),
        arrowprops=dict(arrowstyle="-", color="#888888", lw=1),
        fontsize=8.5, ha=ha, va="center",
        color=color, fontweight="bold")

ax_dona.text(0, 0, f"{n_clasif}\ndocentes", ha="center", va="center",
             fontsize=13, fontweight="bold", color="#333333")
ax_dona.set_xlim(-2.1, 2.1)

# Panel B — Barras horizontales con desglose
y_pos = np.arange(len(CATS))
for i, (cat, v, p, color) in enumerate(zip(CATS[::-1], vals[::-1],
                                            pcts[::-1], COLORES[::-1])):
    ax_bar.barh(i, v, color=color, alpha=0.85, height=0.55, edgecolor="white")
    ax_bar.text(v + 3, i, f"{v}  ({p:.1f}%)",
                va="center", fontsize=11, fontweight="bold", color=color)
    # Desglose
    sub = desglose[desglose["categoria_jornada"]==cat].sort_values(
        "rut_key", ascending=False)
    detalle = "  /  ".join([f"{row['JORNADA'].replace(' Semanales','').replace(' horas semanales','h')}: {row['rut_key']}"
                            for _, row in sub.iterrows()])
    ax_bar.text(3, i - 0.28, detalle, va="center", fontsize=7.5,
                color="#666666", fontstyle="italic")

ax_bar.set_yticks(y_pos)
ax_bar.set_yticklabels(["Por Hora /\nExternos",
                         "Parcial\nde Planta",
                         "Planta\nActiva"], fontsize=11, fontweight="bold")
ax_bar.set_xlabel("N° de docentes")
ax_bar.set_title("Distribución por categoría de jornada\n(desglose de horas en cursiva)", pad=10)
ax_bar.set_xlim(0, max(vals) * 1.4)
ax_bar.spines["top"].set_visible(False)
ax_bar.spines["right"].set_visible(False)

fig.text(0.5, 0.01,
         f"Nota: {n_sin} docentes sin datos de dotación quedan fuera de esta distribución.",
         ha="center", fontsize=8.5, color="#666666", fontstyle="italic")

plt.tight_layout(rect=[0, 0.04, 1, 0.97])
plt.savefig(OUT, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nGuardado: {OUT}")

# ── Bajadas ───────────────────────────────────────────────────────────────────
n_pa  = vals[0]; p_pa  = pcts[0]
n_pp  = vals[1]; p_pp  = pcts[1]
n_ext = vals[2]; p_ext = pcts[2]

print(f"""
INTRO
La distribución por tipo de jornada del cuerpo docente jerarquizado
de UCEN revela que casi 8 de cada 10 docentes con dato de jornada
pertenecen a la Planta Activa, lo que refleja una dotación académica
predominantemente de dedicación completa — aunque un segmento
relevante ejerce en modalidades parciales o por hora.

BAJADAS
• La **Planta Activa** (jornadas de 33 a 44 horas semanales) concentra
  el {p_pa:.1f}% del cuerpo con jornada clasificada (n={n_pa}), siendo la
  categoría ampliamente dominante. Las **Jornadas Parciales de Planta**
  agrupan al {p_pp:.1f}% (n={n_pp}), conformadas principalmente por
  docentes de 22 horas más los de jornada indefinida variable.

• Los **Docentes por Hora / Externos** representan el {p_ext:.1f}% (n={n_ext}),
  el segmento de menor peso relativo dentro de los docentes con dato
  de jornada. Cabe señalar que los {n_sin} docentes sin datos de dotación
  (solo nómina) no pudieron clasificarse, por lo que la distribución
  efectiva podría variar si se dispusiera de la información completa
  de contratación para el universo total.
""")
