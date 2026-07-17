import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os

BASE = os.path.dirname(__file__)
OUT  = os.path.join(BASE, "G3_contraste_antiguedad_918.png")

matplotlib.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})

df = pd.read_csv(os.path.join(BASE,"..","PROCESADO","p3_sat_zscore_918.csv"),
                 encoding="utf-8-sig")

df["es_puro"] = (
    ((df["n_taller"]>0)   & (df["n_diplomado"]==0) & (df["n_proyecto"]==0)) |
    ((df["n_diplomado"]>0) & (df["n_taller"]==0)   & (df["n_proyecto"]==0)) |
    ((df["n_proyecto"]>0)  & (df["n_taller"]==0)   & (df["n_diplomado"]==0))
)

def tipo_simple(row):
    if row["n_diplomado"]>0 and row["n_taller"]==0 and row["n_proyecto"]==0: return "DIPLOMADO"
    if row["n_taller"]>0 and row["n_diplomado"]==0 and row["n_proyecto"]==0: return "TALLER"
    if row["n_proyecto"]>0 and row["n_taller"]==0 and row["n_diplomado"]==0: return "PROYECTO"
    return "MIXTO"
df["tipo_puro"] = df.apply(tipo_simple, axis=1)

def tipo_normal(row):
    if row["n_diplomado"]>0: return "DIPLOMADO"
    if row["n_proyecto"]>0:  return "PROYECTO"
    return "TALLER"
df["tipo_normal"] = df.apply(tipo_normal, axis=1)

TIPOS   = ["TALLER","DIPLOMADO","PROYECTO"]
COLORES = {"TALLER":"#1976D2","DIPLOMADO":"#388E3C","PROYECTO":"#E65100"}
ORD_ANT = ["0-4","5-9","10-14","15+"]

REMAP = {"15-19":"15+","20-24":"15+","25-29":"15+","30+":"15+"}
df["tramo_ant"] = df["tramo_antiguedad"].replace(REMAP)

# Filtrar sin antigüedad
df_ant = df[df["tramo_ant"].isin(ORD_ANT)].copy()

n_total = len(df_ant)
n_puro  = df_ant["es_puro"].sum()
n_mixto = (~df_ant["es_puro"]).sum()

# ── Cascada ───────────────────────────────────────────────────────────────────
print("=" * 65)
print("  G3 CONTRASTE — Δ Z-score × Antigüedad: Normal vs Puro")
print("=" * 65)
for version, subset in [("Normal (todos)", df_ant), ("Puro", df_ant[df_ant["es_puro"]])]:
    print(f"\n  {version}:")
    for tipo in TIPOS:
        if version == "Puro":
            sub = subset[subset["tipo_puro"]==tipo]
        else:
            sub = subset[subset["tipo_normal"]==tipo]
        for a in ORD_ANT:
            s = sub[sub["tramo_ant"]==a]
            if len(s)>0:
                print(f"    {tipo:10} {a:5}: n={len(s):2d} | Δz={s['delta_z'].mean():+.3f}")
print("=" * 65)

# ── Figura: dos heatmaps lado a lado ─────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8), sharey=True)
fig.suptitle(
    "Δ Z-score SAT por Antigüedad y Tipo — Población Normal vs Pura\n"
    f"Universo 917 · {n_total} docentes con antigüedad · {n_puro} puros · {n_mixto} mixtos",
    fontsize=13, fontweight="bold")

def make_heatmap(ax, subset, tipo_col, titulo, tipos=TIPOS):
    matrix = np.full((len(tipos), len(ORD_ANT)), np.nan)
    n_matrix = np.full((len(tipos), len(ORD_ANT)), 0)
    for i, tipo in enumerate(tipos):
        for j, a in enumerate(ORD_ANT):
            sub = subset[(subset[tipo_col]==tipo) & (subset["tramo_ant"]==a)]
            if len(sub) >= 1:
                matrix[i,j] = sub["delta_z"].mean()
                n_matrix[i,j] = len(sub)

    vmax = max(0.4, np.nanmax(np.abs(matrix[np.isfinite(matrix)]))) if np.any(np.isfinite(matrix)) else 0.5
    im = ax.imshow(matrix, cmap="RdYlGn", aspect="auto", vmin=-vmax, vmax=vmax)

    for i in range(len(tipos)):
        for j in range(len(ORD_ANT)):
            n = int(n_matrix[i,j])
            v = matrix[i,j]
            if n > 0 and not np.isnan(v):
                color = "white" if abs(v) > vmax*0.6 else "black"
                ax.text(j, i, f"{v:+.3f}\n(n={n})", ha="center", va="center",
                        fontsize=9, fontweight="bold", color=color)
            else:
                ax.text(j, i, "—", ha="center", va="center",
                        fontsize=10, color="#BBBBBB")

    ax.set_xticks(range(len(ORD_ANT)))
    ax.set_xticklabels([f"{a} años" for a in ORD_ANT], fontsize=10)
    ax.set_yticks(range(len(tipos)))
    ax.set_yticklabels(tipos, fontsize=12, fontweight="bold")
    ax.set_xlabel("Tramo de antigüedad")
    ax.set_title(titulo, pad=12, fontsize=12, fontweight="bold")
    return im

im1 = make_heatmap(ax1, df_ant, "tipo_normal",
                   f"Población Normal\n(todos los formados, n={n_total})")
im2 = make_heatmap(ax2, df_ant[df_ant["es_puro"]], "tipo_puro",
                   f"Población Pura\n(una sola modalidad, n={n_puro})")

cbar = fig.colorbar(im2, ax=[ax1, ax2], label="Δ Z-score (verde=mejoró, rojo=empeoró)",
                    shrink=0.6, pad=0.03, aspect=25)

plt.subplots_adjust(top=0.87, bottom=0.10, left=0.08, right=0.88, wspace=0.15)
plt.savefig(OUT, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nGuardado: {OUT}")
