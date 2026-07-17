import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os

BASE = os.path.dirname(__file__)
OUT  = os.path.join(BASE, "G_edad_918.png")

matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 12, "axes.titlesize": 15, "axes.labelsize": 13,
    "xtick.labelsize": 11, "ytick.labelsize": 11, "legend.fontsize": 11,
})

doc = pd.read_csv(os.path.join(BASE,"..","PROCESADO","docente_918.csv"),
                  encoding="utf-8-sig", dtype={"rut_key": str})
doc["rut_key"] = doc["rut_key"].str.strip()

con_edad = doc[doc["edad_anios"].notna()].copy()
con_edad["edad_anios"] = pd.to_numeric(con_edad["edad_anios"], errors="coerce")

ORD      = ["<30","30-34","35-39","40-44","45-49","50-54","55-59","60-64","65-69","70+"]
n_total  = len(con_edad)
n_sin    = len(doc) - n_total
edad_med = con_edad["edad_anios"].median()
edad_avg = con_edad["edad_anios"].mean()

tbl = (con_edad.groupby("tramo_edad")["rut_key"]
       .count().reindex(ORD).fillna(0).astype(int))

# ── Cascada consola ────────────────────────────────────────────────────────────
print("=" * 60)
print("  UNIVERSO — Caracterización Docente por Edad")
print("=" * 60)
print(f"  917 docentes jerarquizados (Universo 917)")
print(f"    ├── {n_total} CON datos de edad  ← perfil completo (dotación)")
print(f"    └── {n_sin} SIN datos de edad  ← solo nómina, sin dotación")
print()
print(f"  Edad promedio: {edad_avg:.1f} años")
print(f"  Mediana: {edad_med:.1f} años  |  Rango: {con_edad['edad_anios'].min():.0f}–{con_edad['edad_anios'].max():.0f} años")
print()
print("  Distribución por tramo:")
for tr in ORD:
    n = int(tbl.get(tr, 0))
    pct = 100*n/n_total if n_total > 0 else 0
    bar = "█" * (n // 3)
    print(f"    {tr:>5}  {bar}  n={n} ({pct:.1f}%)")
print("=" * 60)

# ── Figura ────────────────────────────────────────────────────────────────────
# Gradiente de colores por tramo (más joven → más azul, más mayor → más naranja)
PALETTE = ["#1565C0","#1976D2","#1E88E5","#42A5F5",
           "#78909C","#546E7A","#E65100","#EF6C00","#F57C00","#FF8F00"]

x    = np.arange(len(ORD))
vals = [int(tbl.get(t, 0)) for t in ORD]
pcts = [100*v/n_total for v in vals]

fig, ax = plt.subplots(figsize=(13, 7))

bars = ax.bar(x, vals, width=0.65, color=PALETTE, alpha=0.88, edgecolor="white")

for i, (v, p) in enumerate(zip(vals, pcts)):
    if v > 0:
        ax.text(i, v + 0.8, f"{v}\n({p:.1f}%)", ha="center",
                fontsize=10, color="#222222", fontweight="bold")

# Mediana
med_idx = next(i for i, t in enumerate(ORD) if t == "45-49")
ax.axvline(med_idx + 0.05, color="#333333", linewidth=1.8,
           linestyle="--", alpha=0.6)
ax.text(med_idx + 0.15, max(vals) * 0.93,
        f"Mediana\n{edad_med:.0f} años", fontsize=10,
        color="#333333", fontstyle="italic")

# Franja central (35–54)
ax.axvspan(ORD.index("35-39") - 0.35, ORD.index("50-54") + 0.35,
           alpha=0.06, color="#1565C0", zorder=0)
n_central = sum(vals[ORD.index(t)] for t in ["35-39","40-44","45-49","50-54"])
ax.text((ORD.index("35-39") + ORD.index("50-54"))/2, max(vals)*0.75,
        f"Núcleo 35–54 años\n{n_central} doc. ({100*n_central/n_total:.0f}%)",
        ha="center", fontsize=10, color="#1565C0", alpha=0.8,
        fontstyle="italic")

ax.set_xticks(x)
ax.set_xticklabels(ORD, fontsize=12)
ax.set_ylabel("N° docentes", fontsize=13)
ax.set_xlabel("Tramo de edad", fontsize=13)
ax.set_title(
    "Caracterización por Edad — Cuerpo Docente Jerarquizado UCEN\n"
    f"Universo 917 · {n_total} docentes con datos de edad · "
    f"Edad promedio {edad_avg:.1f} años · Mediana {edad_med:.0f} años",
    pad=14, fontweight="bold", fontsize=14)
ax.set_ylim(0, max(vals) * 1.18)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nGuardado: {OUT}")

n_central = sum(vals[ORD.index(t)] for t in ["35-39","40-44","45-49","50-54"])
n_senior  = sum(vals[ORD.index(t)] for t in ["55-59","60-64","65-69","70+"])
print(f"""
BAJADAS
• El cuerpo docente jerarquizado de UCEN con datos de edad disponibles (n={n_total})
  presenta una edad mediana de {edad_med:.0f} años y un promedio de {edad_avg:.1f} años,
  con el {100*n_central/n_total:.0f}% de los docentes concentrado en el tramo 35–54 años.
  Este perfil refleja un cuerpo académico en plena madurez profesional, con
  trayectoria consolidada en la disciplina y en la docencia universitaria.

• El {100*n_senior/n_total:.0f}% del cuerpo docente supera los 55 años (n={n_senior}),
  incluyendo {vals[ORD.index('70+')]} docentes de 70 años o más, lo que evidencia
  una base de experiencia significativa y plantea la necesidad de estrategias
  de renovación generacional y transferencia de conocimiento en el mediano plazo.
""")
