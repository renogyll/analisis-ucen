import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os

BASE = os.path.dirname(__file__)
OUT1 = os.path.join(BASE, "G_institucion_grado_918.png")
OUT2 = os.path.join(BASE, "G_pais_grado_918.png")

matplotlib.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})

doc917 = pd.read_csv(os.path.join(BASE,"..","PROCESADO","docente_918.csv"),
                     encoding="utf-8-sig", dtype={"rut_key": str})
doc917["rut_key"] = doc917["rut_key"].str.strip()

dot = pd.read_csv(
    os.path.join(BASE,"..","..","CONSOLIDADO DOCENTES 3-05-2026",
                 "CONSOLIDADO DOCENTES 3-05-2026.xlsx - DOTACION_CON_GRADOREC.csv"),
    dtype=str, encoding="utf-8-sig")
dot.columns = dot.columns.str.strip()
dot["rut_key"] = (dot["RUT"].str.strip()
                  .str.replace(".", "", regex=False)
                  .str.split("-").str[0].str.strip())

dot917 = dot[dot["rut_key"].isin(set(doc917["rut_key"]))].copy()

n_total = len(doc917)
n_dot   = len(dot917)

# ══════════════════════════════════════════════════════════════════════════════
# GRÁFICO 1 — Institución de Grado
# ══════════════════════════════════════════════════════════════════════════════
df_inst = dot917[dot917["INSTITUCIÓN GRADO TÍTULO"].notna() &
                 (dot917["INSTITUCIÓN GRADO TÍTULO"].str.strip() != "NO INFORMA")].copy()
df_inst["inst"] = df_inst["INSTITUCIÓN GRADO TÍTULO"].str.strip()
n_inst = len(df_inst)

conteo_inst = df_inst["inst"].value_counts()
TOP_N = 6
top_inst   = conteo_inst.head(TOP_N)
n_otros    = n_inst - top_inst.sum()

labels_inst = top_inst.index.tolist() + [f"Otras ({conteo_inst.shape[0] - TOP_N} instituciones)"]
vals_inst   = top_inst.values.tolist() + [n_otros]
pcts_inst   = [100*v/n_inst for v in vals_inst]

ABREV_INST = {
    "UNIVERSIDAD CENTRAL DE CHILE SANTIAGO": "U. Central Santiago",
    "UNIVERSIDAD DE CHILE": "U. de Chile",
    "PONTIFICIA UNIVERSIDAD CATÓLICA DE CHILE": "PUC Chile",
    "UNIVERSIDAD ANDRÉS BELLO": "U. Andrés Bello",
    "UNIVERSIDAD DE SANTIAGO DE CHILE": "USACH",
    "UNIVERSIDAD MAYOR": "U. Mayor",
}
labels_abrev = [ABREV_INST.get(l, l) for l in labels_inst]

COLORES_INST = ["#1565C0","#1976D2","#42A5F5","#66BB6A","#FFA726","#E65100","#CFD8DC"]

print("=" * 65)
print("  INSTITUCIÓN DE GRADO ACADÉMICO (Universo 917)")
print("=" * 65)
print(f"  917 docentes · {n_inst} con institución informada")
for l, v, p in zip(labels_abrev, vals_inst, pcts_inst):
    print(f"    ├── {v:3d} ({p:5.1f}%)  {l}")
print("=" * 65)

fig, ax = plt.subplots(figsize=(13, 7))
fig.suptitle(
    "Institución de Obtención del Grado Académico — Top 6\n"
    f"Universo 917 · {n_inst} docentes con dato informado",
    fontsize=13, fontweight="bold")

y = np.arange(len(labels_abrev))
bars = ax.barh(y[::-1], vals_inst, color=COLORES_INST[:len(labels_abrev)],
               alpha=0.88, height=0.62, edgecolor="white")

for i, (v, p, color) in enumerate(zip(vals_inst[::-1], pcts_inst[::-1],
                                       COLORES_INST[:len(labels_abrev)][::-1])):
    ax.text(v + 1.5, i, f"{v}  ({p:.1f}%)",
            va="center", fontsize=10.5, fontweight="bold", color=color)

ax.set_yticks(y)
ax.set_yticklabels(labels_abrev[::-1], fontsize=10.5, fontweight="bold")
ax.set_xlabel("N° de docentes")
ax.set_xlim(0, max(vals_inst) * 1.35)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig(OUT1, dpi=150, bbox_inches="tight")
plt.close()
print(f"Guardado: {OUT1}")

# ══════════════════════════════════════════════════════════════════════════════
# GRÁFICO 2 — País de Grado
# ══════════════════════════════════════════════════════════════════════════════
df_pais = dot917[dot917["PAÍS GRADO TÍTULO"].notna() &
                 (dot917["PAÍS GRADO TÍTULO"].str.strip() != "NO INFORMA")].copy()
df_pais["pais"] = df_pais["PAÍS GRADO TÍTULO"].str.strip()
# Unificar REINO UNIDO + INGLATERRA
df_pais["pais"] = df_pais["pais"].replace({"INGLATERRA": "REINO UNIDO"})
n_pais = len(df_pais)

conteo_pais = df_pais["pais"].value_counts()
TOP_P = 6
top_pais   = conteo_pais.head(TOP_P)
n_otros_p  = n_pais - top_pais.sum()

labels_pais = top_pais.index.tolist() + [f"Otros ({conteo_pais.shape[0] - TOP_P} países)"]
vals_pais   = top_pais.values.tolist() + [n_otros_p]
pcts_pais   = [100*v/n_pais for v in vals_pais]

n_chile    = conteo_pais.get("CHILE", 0)
n_ext      = n_pais - n_chile
pct_chile  = 100*n_chile/n_pais
pct_ext    = 100*n_ext/n_pais

COLORES_PAIS = ["#1565C0","#E65100","#1B5E20","#6A1B9A","#F57C00","#388E3C","#CFD8DC"]

print()
print("=" * 65)
print("  PAÍS DE OBTENCIÓN DEL GRADO ACADÉMICO (Universo 917)")
print("=" * 65)
print(f"  917 docentes · {n_pais} con país informado")
print(f"    ├── Chile: {n_chile} ({pct_chile:.1f}%)")
print(f"    └── Internacional: {n_ext} ({pct_ext:.1f}%)")
print()
for l, v, p in zip(labels_pais, vals_pais, pcts_pais):
    print(f"    ├── {v:3d} ({p:5.1f}%)  {l}")
print("=" * 65)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7),
                                gridspec_kw={"width_ratios": [1, 1.3]})
fig.suptitle(
    "País de Obtención del Grado Académico\n"
    f"Universo 917 · {n_pais} docentes con dato informado",
    fontsize=13, fontweight="bold")

# Panel A — Dona Chile vs Internacional
vals_dona = [n_chile, n_ext]
wedges, _ = ax1.pie(vals_dona, colors=["#1565C0","#E65100"], startangle=90,
                    counterclock=False,
                    wedgeprops=dict(width=0.55, edgecolor="white", linewidth=2.5))
for wedge, lbl, v, p, color in zip(wedges,
    [f"Chile\n{n_chile} ({pct_chile:.1f}%)", f"Internacional\n{n_ext} ({pct_ext:.1f}%)"],
    vals_dona, [pct_chile, pct_ext], ["#1565C0","#E65100"]):
    ang = (wedge.theta2 + wedge.theta1)/2
    x2 = 1.25*np.cos(np.radians(ang))
    y2 = 1.25*np.sin(np.radians(ang))
    ha = "left" if x2>0 else "right"
    ax1.annotate(lbl, xy=(0.75*np.cos(np.radians(ang)), 0.75*np.sin(np.radians(ang))),
                 xytext=(x2,y2), arrowprops=dict(arrowstyle="-",color="#888",lw=1),
                 fontsize=11, ha=ha, va="center", fontweight="bold", color=color)
ax1.text(0, 0, f"{n_pais}\ndocentes", ha="center", va="center",
         fontsize=13, fontweight="bold", color="#333333")
ax1.set_xlim(-2, 2)
ax1.set_title("Chile vs Internacional", pad=10)

# Panel B — Top 6 barras
y = np.arange(len(labels_pais))
bars = ax2.barh(y[::-1], vals_pais, color=COLORES_PAIS[:len(labels_pais)],
                alpha=0.88, height=0.55, edgecolor="white")
for i, (v, p, color) in enumerate(zip(vals_pais[::-1], pcts_pais[::-1],
                                       COLORES_PAIS[:len(labels_pais)][::-1])):
    ax2.text(v + 1, i, f"{v}  ({p:.1f}%)",
             va="center", fontsize=10.5, fontweight="bold", color=color)
ax2.set_yticks(y)
ax2.set_yticklabels(labels_pais[::-1], fontsize=10.5, fontweight="bold")
ax2.set_xlabel("N° de docentes")
ax2.set_title("Top 6 países + otros", pad=10)
ax2.set_xlim(0, max(vals_pais) * 1.3)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig(OUT2, dpi=150, bbox_inches="tight")
plt.close()
print(f"Guardado: {OUT2}")
