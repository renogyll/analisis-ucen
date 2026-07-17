import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os

BASE = os.path.dirname(__file__)
OUT  = os.path.join(BASE, "G1_puro_nota_recom_918.png")

matplotlib.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})

C_TALLER    = "#1976D2"
C_DIPLOMADO = "#FF9800"
C_PROYECTO  = "#388E3C"
COLORES = {"TALLER": C_TALLER, "DIPLOMADO": C_DIPLOMADO, "PROYECTO": C_PROYECTO}
MARKERS = {"TALLER": "o", "DIPLOMADO": "s", "PROYECTO": "^"}

# Cargar datos
df_sat = pd.read_csv(os.path.join(BASE,"..","PROCESADO","p3_sat_zscore_918.csv"),
                     encoding="utf-8-sig")
df_bin = pd.read_csv(os.path.join(BASE,"..","PROCESADO","p3_bin_zscore_918.csv"),
                     encoding="utf-8-sig")

def tipo_puro(r):
    if r["n_taller"]>0 and r["n_diplomado"]==0 and r["n_proyecto"]==0: return "TALLER"
    if r["n_diplomado"]>0 and r["n_taller"]==0 and r["n_proyecto"]==0: return "DIPLOMADO"
    if r["n_proyecto"]>0 and r["n_taller"]==0 and r["n_diplomado"]==0: return "PROYECTO"
    return "MIXTO"

for d in [df_sat, df_bin]:
    d["tipo_puro"] = d.apply(tipo_puro, axis=1)

puro_sat = df_sat[df_sat["tipo_puro"] != "MIXTO"].copy()
puro_bin = df_bin[df_bin["tipo_puro"] != "MIXTO"].copy()

TIPOS = ["TALLER", "DIPLOMADO", "PROYECTO"]
MOMENTOS = ["Baseline\n(pre-formación)", "Resultado\n(post-formación)"]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7), sharey=True)

# Títulos de panel en color, arriba del gráfico
fig.text(0.27, 0.96, "SAT Nota", ha="center", fontsize=13,
         fontweight="bold", color="#E65100")
fig.text(0.75, 0.96, "SAT % Recomendación", ha="center", fontsize=13,
         fontweight="bold", color="#E65100")

# Panel A — SAT Nota (puros)
ax1.set_title("Trayectoria Z-score SAT\nbaseline → resultado — Población Pura",
              fontsize=12, fontweight="bold")
for tipo in TIPOS:
    sub = puro_sat[puro_sat["tipo_puro"]==tipo]
    n = len(sub)
    vals = [sub["z_baseline"].mean(), sub["z_resultado"].mean()]
    color = COLORES[tipo]
    marker = MARKERS[tipo]
    ax1.plot([0,1], vals, marker=marker, color=color, linewidth=2.5,
             markersize=10, label=f"{tipo} (n={n})")
    ax1.text(1.02, vals[1], f"{vals[1]:+.3f}", va="center", fontsize=10,
             fontweight="bold", color=color)

ax1.axhline(0, color="#CCCCCC", linewidth=1, linestyle="--", alpha=0.7,
            label="Promedio facultad (z=0)")
ax1.set_xticks([0,1])
ax1.set_xticklabels(MOMENTOS, fontsize=11)
ax1.set_ylabel("Z-score promedio\n(posición relativa en facultad)", fontsize=11)
ax1.set_xlim(-0.15, 1.25)
ax1.legend(fontsize=10, loc="upper left")
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)

# Panel B — SAT % Recomendación (puros)
ax2.set_title("Trayectoria Z-score ¿Recomendaría al docente?\nbaseline → resultado — Población Pura",
              fontsize=12, fontweight="bold")
for tipo in TIPOS:
    sub = puro_bin[puro_bin["tipo_puro"]==tipo]
    n = len(sub)
    vals = [sub["z_bin_baseline"].mean(), sub["z_bin_resultado"].mean()]
    color = COLORES[tipo]
    marker = MARKERS[tipo]
    ax2.plot([0,1], vals, marker=marker, color=color, linewidth=2.5,
             markersize=10, label=f"{tipo} (n={n})")
    ax2.text(1.02, vals[1], f"{vals[1]:+.3f}", va="center", fontsize=10,
             fontweight="bold", color=color)

ax2.axhline(0, color="#CCCCCC", linewidth=1, linestyle="--", alpha=0.7,
            label="Promedio facultad (z=0)")
ax2.set_xticks([0,1])
ax2.set_xticklabels(MOMENTOS, fontsize=11)
ax2.set_xlim(-0.15, 1.25)
ax2.legend(fontsize=10, loc="upper left")
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)

plt.tight_layout(rect=[0, 0, 1, 0.94])
plt.savefig(OUT, dpi=150, bbox_inches="tight")
plt.close()
print(f"Guardado: {OUT}")

# Cascada
print()
print("POBLACIÓN PURA — SAT Nota + % Recomendación")
print(f"{'':10} {'SAT Nota':>30}    {'SAT % Recomendación':>30}")
print(f"{'':10} {'Base → Result    Δ':>30}    {'Base → Result    Δ':>30}")
for tipo in TIPOS:
    s = puro_sat[puro_sat["tipo_puro"]==tipo]
    b = puro_bin[puro_bin["tipo_puro"]==tipo]
    sn_b, sn_r = s["z_baseline"].mean(), s["z_resultado"].mean()
    bn_b, bn_r = b["z_bin_baseline"].mean(), b["z_bin_resultado"].mean()
    print(f"{tipo:10} (n={len(s):3d})  {sn_b:+.3f} → {sn_r:+.3f}  Δ={sn_r-sn_b:+.3f}"
          f"    {bn_b:+.3f} → {bn_r:+.3f}  Δ={bn_r-bn_b:+.3f}")
