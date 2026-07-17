import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib
import numpy as np
import os

BASE = os.path.dirname(__file__)
OUT  = os.path.join(BASE, "G_delta_z_puro_vs_mixto_918.png")

matplotlib.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})

C_PURO  = "#1565C0"
C_MIXTO = "#E65100"

df = pd.read_csv(os.path.join(BASE,"..","PROCESADO","p3_sat_zscore_918.csv"),
                 encoding="utf-8-sig")

df["tipo_principal"] = df["tipos_formacion"]
df["es_puro"] = (
    ((df["n_taller"]>0)   & (df["n_diplomado"]==0) & (df["n_proyecto"]==0)) |
    ((df["n_diplomado"]>0) & (df["n_taller"]==0)   & (df["n_proyecto"]==0)) |
    ((df["n_proyecto"]>0)  & (df["n_taller"]==0)   & (df["n_diplomado"]==0))
)

TIPOS   = ["TALLER","DIPLOMADO","PROYECTO"]
COLORES = {"TALLER":"#1976D2","DIPLOMADO":"#388E3C","PROYECTO":"#E65100"}

n_puro  = df["es_puro"].sum()
n_mixto = (~df["es_puro"]).sum()

# ── Cascada ───────────────────────────────────────────────────────────────────
print("=" * 65)
print("  Δ Z-SCORE — Distribución: Población Pura vs Mixta")
print("=" * 65)
print(f"  197 docentes aptos P3")
print(f"    ├── {n_puro}  PUROS  (una sola modalidad)")
print(f"    └── {n_mixto}  MIXTOS (más de una modalidad)")
print()

puro_all  = df[df["es_puro"]]["delta_z"]
mixto_all = df[~df["es_puro"]]["delta_z"]
print(f"  Δ Z-score PURO  : media={puro_all.mean():+.3f} | mediana={puro_all.median():+.3f} | "
      f"mejoró={( df[df['es_puro']]['mejoro_z']).sum()} ({100*(df[df['es_puro']]['mejoro_z']).mean():.0f}%)")
print(f"  Δ Z-score MIXTO : media={mixto_all.mean():+.3f} | mediana={mixto_all.median():+.3f} | "
      f"mejoró={(~df['es_puro'] & df['mejoro_z']).sum()} ({100*(df[~df['es_puro']]['mejoro_z']).mean():.0f}%)")
print()
for tipo in TIPOS:
    sub_p = df[(df["tipo_principal"]==tipo) & df["es_puro"]]["delta_z"]
    if len(sub_p) == 0: continue
    pct_m = 100*(df[(df["tipo_principal"]==tipo) & df["es_puro"]]["mejoro_z"]).mean()
    print(f"  {tipo:10} PURO  (n={len(sub_p):3d}): media={sub_p.mean():+.3f} | mejora={pct_m:.0f}%")
print("=" * 65)

# ── Figura ────────────────────────────────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
fig.suptitle(
    "Distribución del Δ Z-score SAT — Población Pura vs Mixta\n"
    "Universo 917 · 197 docentes aptos P3 · Baseline → Resultado",
    fontsize=13, fontweight="bold")

# Panel A — Boxplot PURO vs MIXTO global
datos_a = [df[df["es_puro"]]["delta_z"].dropna().values,
           df[~df["es_puro"]]["delta_z"].dropna().values]
labels_a = [f"Puro\n(n={n_puro})", f"Mixto\n(n={n_mixto})"]
cols_a   = [C_PURO, C_MIXTO]

bp1 = ax1.boxplot(datos_a, patch_artist=True,
                  medianprops=dict(color="black", linewidth=2.5),
                  whiskerprops=dict(linewidth=1.5),
                  capprops=dict(linewidth=1.5),
                  flierprops=dict(marker="o", markersize=4, alpha=0.45))
for patch, color in zip(bp1["boxes"], cols_a):
    patch.set_facecolor(color); patch.set_alpha(0.75)

# Puntos individuales
for i, (d, color) in enumerate(zip(datos_a, cols_a)):
    jitter = np.random.normal(0, 0.06, size=len(d))
    ax1.scatter(np.full_like(d, i+1) + jitter, d,
                alpha=0.3, s=18, color=color, zorder=2)

for i, (d, color) in enumerate(zip(datos_a, cols_a)):
    med = np.median(d)
    ax1.text(i+1, med + 0.04, f"{med:+.3f}",
             ha="center", fontsize=11, fontweight="bold", color="black")
    pct = 100 * (d > 0).sum() / len(d)
    ax1.text(i+1, ax1.get_ylim()[0] if ax1.get_ylim()[0] < -0.5 else -0.85,
             f"{pct:.0f}% mejoró", ha="center", fontsize=9.5,
             color=color, fontweight="bold")

ax1.axhline(0, color="#C62828", linewidth=1.5, linestyle="--",
            alpha=0.7, label="Sin cambio (Δ=0)")
ax1.set_xticks([1,2]); ax1.set_xticklabels(labels_a, fontsize=12)
ax1.set_ylabel("Δ Z-score (resultado − baseline)")
ax1.set_title("Global: Puro vs Mixto", pad=10)
ax1.legend(fontsize=10)
ax1.spines["top"].set_visible(False); ax1.spines["right"].set_visible(False)

# Panel B — Boxplot por tipo (solo puros, con n del total para contexto)
TIPOS_VALIDOS = [t for t in TIPOS
                 if len(df[(df["tipo_principal"]==t) & df["es_puro"]]) >= 3]
datos_b  = [df[(df["tipo_principal"]==t) & df["es_puro"]]["delta_z"].dropna().values
            for t in TIPOS_VALIDOS]
datos_b2 = [df[df["tipo_principal"].str.contains(t)]["delta_z"].dropna().values
            for t in TIPOS_VALIDOS]
cols_b   = [{"TALLER":"#1976D2","DIPLOMADO":"#388E3C","PROYECTO":"#E65100"}[t]
            for t in TIPOS_VALIDOS]

x_pos = np.arange(len(TIPOS_VALIDOS)) * 1.8
w = 0.55

for i, (d_p, d_n, tipo, color) in enumerate(zip(datos_b, datos_b2, TIPOS_VALIDOS, cols_b)):
    xi = x_pos[i]
    # Boxplot normal (todos)
    bp_n = ax2.boxplot(d_n, positions=[xi - w/2], widths=w*0.85,
                       patch_artist=True,
                       medianprops=dict(color="black", linewidth=2),
                       whiskerprops=dict(linewidth=1.2),
                       capprops=dict(linewidth=1.2),
                       flierprops=dict(marker="o", markersize=3, alpha=0.3))
    bp_n["boxes"][0].set_facecolor(color); bp_n["boxes"][0].set_alpha(0.4)

    # Boxplot puro
    bp_p = ax2.boxplot(d_p, positions=[xi + w/2], widths=w*0.85,
                       patch_artist=True,
                       medianprops=dict(color="black", linewidth=2.5),
                       whiskerprops=dict(linewidth=1.5),
                       capprops=dict(linewidth=1.5),
                       flierprops=dict(marker="o", markersize=3.5, alpha=0.4))
    bp_p["boxes"][0].set_facecolor(color); bp_p["boxes"][0].set_alpha(0.85)

    # Etiquetas
    med_n = np.median(d_n); med_p = np.median(d_p)
    ax2.text(xi-w/2, med_n+0.04, f"{med_n:+.3f}", ha="center", fontsize=8.5,
             color=color, alpha=0.7)
    ax2.text(xi+w/2, med_p+0.04, f"{med_p:+.3f}", ha="center", fontsize=9,
             fontweight="bold", color=color)
    ax2.text(xi-w/2, -0.92, f"n={len(d_n)}", ha="center", fontsize=8.5,
             color=color, alpha=0.6)
    ax2.text(xi+w/2, -0.92, f"n={len(d_p)}", ha="center", fontsize=8.5,
             fontweight="bold", color=color)
    ax2.text(xi, ax2.get_ylim()[1] if ax2.get_ylim()[1]>0.5 else 0.75,
             tipo.capitalize(), ha="center", fontsize=11,
             fontweight="bold", color=color)

ax2.axhline(0, color="#C62828", linewidth=1.5, linestyle="--", alpha=0.7)
ax2.set_xticks(x_pos)
ax2.set_xticklabels([t.capitalize() for t in TIPOS_VALIDOS], fontsize=11)
ax2.set_ylabel("Δ Z-score (resultado − baseline)")
ax2.set_title("Por tipo: Normal (transparente) vs Puro (sólido)", pad=10)

patch_n = mpatches.Patch(facecolor="#AAAAAA", alpha=0.4, label="Normal (todos)")
patch_p = mpatches.Patch(facecolor="#444444", alpha=0.85, label="Puro (una modalidad)")
ax2.legend(handles=[patch_n, patch_p], fontsize=10, loc="lower right")
ax2.spines["top"].set_visible(False); ax2.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nGuardado: {OUT}")

# Bajadas rápidas
print(f"""
DATOS CLAVE PARA PUNTEOS
Puro  mediana Δz: {puro_all.median():+.3f} | mejoró: {100*df[df['es_puro']]['mejoro_z'].mean():.0f}%
Mixto mediana Δz: {mixto_all.median():+.3f} | mejoró: {100*df[~df['es_puro']]['mejoro_z'].mean():.0f}%
""")
