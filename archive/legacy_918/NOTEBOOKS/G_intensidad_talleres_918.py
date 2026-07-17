import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os

BASE = os.path.dirname(__file__)
OUT  = os.path.join(BASE, "G_intensidad_talleres_918.png")
SRC  = os.path.join(BASE, "..", "..", "CONSOLIDADO DOCENTES 3-05-2026")

matplotlib.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})

def limpiar_rut(s):
    return str(s).strip().replace(".", "").split("-")[0].strip()

doc917 = pd.read_csv(os.path.join(BASE,"..","PROCESADO","docente_918.csv"),
                     encoding="utf-8-sig", dtype={"rut_key": str})
doc917["rut_key"] = doc917["rut_key"].str.strip()
ruts_917 = set(doc917["rut_key"])

# Contar talleres por docente
conteo = {}
for f in ["TALLERES 2023_2","TALLERES 2024_1","TALLERES 2024_2"]:
    df = pd.read_csv(os.path.join(SRC, f"CONSOLIDADO DOCENTES 3-05-2026.xlsx - {f}.csv"),
                     encoding="utf-8-sig", dtype=str)
    df.columns = df.columns.str.strip()
    df["rut_key"] = df["RUT"].apply(limpiar_rut)
    for rut in df["rut_key"]:
        if rut in ruts_917:
            conteo[rut] = conteo.get(rut, 0) + 1

# Distribución
from collections import Counter
dist = Counter(conteo.values())
max_t = max(dist.keys())

labels = []
vals   = []
for n in range(1, max_t + 1):
    count = dist.get(n, 0)
    if count > 0 or n <= 5:
        labels.append(f"{n}" if n > 1 else "1")
        vals.append(count)
n_total_doc = sum(vals)
pcts   = [100*v/n_total_doc for v in vals]
acum   = np.cumsum(pcts)

import matplotlib.cm as cm
n_bars = len(vals)
cmap = cm.get_cmap("Blues", n_bars + 2)
COLORES = [cmap(i + 2) for i in range(n_bars)]

# ── Cascada ───────────────────────────────────────────────────────────────────
print("=" * 65)
print("  INTENSIDAD DE TALLERES (Universo 917)")
print("=" * 65)
print(f"  215 docentes con al menos 1 taller · 376 iniciativas de formación totales")
print(f"  Promedio: {376/215:.2f} talleres por docente")
print(f"  Máximo: {max_t} talleres")
print()
for l, v, p in zip(labels, vals, pcts):
    print(f"    ├── {v:3d} docentes ({p:.1f}%)  {l}")
print()
print(f"  Detalle completo:")
for n in sorted(dist.keys()):
    print(f"    {n:2d} talleres: {dist[n]} docentes")
print("=" * 65)

# ── Figura ────────────────────────────────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7),
                                gridspec_kw={"width_ratios": [1.3, 1]})
fig.suptitle(
    "Intensidad de Participación en Talleres — Universo 917\n"
    f"215 docentes · 376 iniciativas de formación · Promedio {376/215:.1f} talleres por docente",
    fontsize=13, fontweight="bold")

# Panel A — Barras
x = np.arange(len(labels))
bars = ax1.bar(x, vals, color=COLORES, alpha=0.88, width=0.6, edgecolor="white")

for i, (v, p, color) in enumerate(zip(vals, pcts, COLORES)):
    ax1.text(i, v + 1, f"{v}\n({p:.0f}%)", ha="center", fontsize=11,
             fontweight="bold", color=color)

ax1.set_xticks(x)
ax1.set_xticklabels(labels, fontsize=10)
ax1.set_xlabel("N° de talleres")
ax1.set_ylabel("N° de docentes")
ax1.set_title("¿Cuántos talleres tomó cada docente?", pad=10)
ax1.set_ylim(0, max(vals) * 1.25)
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)

# Panel B — Curva acumulada
ax2.plot(x, acum, marker="o", color="#1565C0", linewidth=2.5, markersize=10)
ax2.fill_between(x, acum, alpha=0.15, color="#1565C0")
for i, a in enumerate(acum):
    ax2.text(i, a + 2, f"{a:.0f}%", ha="center", fontsize=11,
             fontweight="bold", color="#1565C0")

ax2.set_xticks(x)
ax2.set_xticklabels(labels, fontsize=10)
ax2.set_xlabel("N° de talleres")
ax2.set_ylabel("% acumulado de docentes")
ax2.set_title("Curva acumulada", pad=10)
ax2.set_ylim(0, 110)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nGuardado: {OUT}")
