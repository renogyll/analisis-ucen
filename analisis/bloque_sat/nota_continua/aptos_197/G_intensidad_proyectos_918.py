import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os
from collections import Counter

BASE = os.path.dirname(__file__)
OUT  = os.path.join(BASE, "G_intensidad_proyectos_918.png")
SRC  = os.path.join(BASE, "..", "..", "CONSOLIDADO DOCENTES 3-05-2026")

matplotlib.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})

def limpiar_rut(s):
    return str(s).strip().replace(".", "").split("-")[0].strip()

doc917 = pd.read_csv(os.path.join(BASE,"..","PROCESADO","docente_918.csv"),
                     encoding="utf-8-sig", dtype={"rut_key": str})
doc917["rut_key"] = doc917["rut_key"].str.strip()
ruts_917 = set(doc917["rut_key"])

df = pd.read_csv(os.path.join(SRC, "CONSOLIDADO DOCENTES 3-05-2026.xlsx - PROYECTOS DE INVESTIGACION.csv"),
                 encoding="utf-8-sig", dtype=str)
df.columns = df.columns.str.strip()
df["rut_key"] = df["RUT"].apply(limpiar_rut)
df917 = df[df["rut_key"].isin(ruts_917)].copy()

conteo = df917.groupby("rut_key").size()
dist = Counter(conteo.values)
n_doc = len(conteo)
n_inst = len(df917)

labels = [str(n) for n in sorted(dist.keys())]
vals   = [dist[int(l)] for l in labels]
pcts   = [100*v/n_doc for v in vals]
acum   = np.cumsum(pcts)

COLORES = ["#66BB6A","#388E3C","#1B5E20","#0D3B0D"]

# ── Cascada ───────────────────────────────────────────────────────────────────
print("=" * 65)
print("  INTENSIDAD DE PROYECTOS (Universo 917)")
print("=" * 65)
print(f"  {n_doc} docentes con al menos 1 proyecto · {n_inst} instancias totales")
print(f"  Promedio: {n_inst/n_doc:.2f} proyectos por docente")
print()
for l, v, p in zip(labels, vals, pcts):
    print(f"    ├── {v:2d} docentes ({p:.0f}%)  {l} proyecto{'s' if int(l)>1 else ''}")

# Detalle de los que tienen más de 1
print()
print("  Docentes con más de 1 proyecto:")
for rut in conteo[conteo > 1].index:
    info = doc917[doc917["rut_key"]==rut]
    nombre = info.iloc[0]["nombre"] if len(info)>0 else "?"
    jer    = info.iloc[0]["jerarquia"] if len(info)>0 else "?"
    n_p    = conteo[rut]
    proyectos = df917[df917["rut_key"]==rut]["Nombre proyecto"].tolist()
    lineas    = df917[df917["rut_key"]==rut]["Linea"].tolist()
    print(f"    {nombre} ({jer}) — {n_p} proyectos:")
    for proy, linea in zip(proyectos, lineas):
        print(f"      · [{linea}] {proy}")
print("=" * 65)

# ── Figura ────────────────────────────────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7),
                                gridspec_kw={"width_ratios": [1.3, 1]})
fig.suptitle(
    "Intensidad de Participación en Proyectos — Universo 917\n"
    f"{n_doc} docentes · {n_inst} instancias · Promedio {n_inst/n_doc:.1f} proyectos por docente",
    fontsize=13, fontweight="bold")

# Panel A — Barras
x = np.arange(len(labels))
bars = ax1.bar(x, vals, color=COLORES[:len(labels)], alpha=0.88,
               width=0.5, edgecolor="white")

for i, (v, p, color) in enumerate(zip(vals, pcts, COLORES)):
    ax1.text(i, v + 0.3, f"{v}\n({p:.0f}%)", ha="center", fontsize=12,
             fontweight="bold", color=color)

ax1.set_xticks(x)
xlabels = [f"{l} proyecto{'s' if int(l)>1 else ''}" for l in labels]
ax1.set_xticklabels(xlabels, fontsize=11)
ax1.set_ylabel("N° de docentes")
ax1.set_xlabel("N° de proyectos")
ax1.set_title("¿Cuántos proyectos realizó cada docente?", pad=10)
ax1.set_ylim(0, max(vals) * 1.25)
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)

# Panel B — Curva acumulada
ax2.plot(x, acum, marker="o", color="#388E3C", linewidth=2.5, markersize=10)
ax2.fill_between(x, acum, alpha=0.15, color="#388E3C")
for i, a in enumerate(acum):
    ax2.text(i, a + 2, f"{a:.0f}%", ha="center", fontsize=11,
             fontweight="bold", color="#388E3C")

ax2.set_xticks(x)
ax2.set_xticklabels(xlabels, fontsize=10)
ax2.set_ylabel("% acumulado de docentes")
ax2.set_xlabel("N° de proyectos")
ax2.set_title("Curva acumulada", pad=10)
ax2.set_ylim(0, 110)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nGuardado: {OUT}")
