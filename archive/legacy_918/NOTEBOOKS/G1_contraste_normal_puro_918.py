import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os

BASE = os.path.dirname(__file__)
OUT  = os.path.join(BASE, "G1_contraste_normal_puro_918.png")

matplotlib.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})

C_TALLER    = "#1976D2"
C_DIPLOMADO = "#388E3C"
C_PROYECTO  = "#E65100"
C_CTRL      = "#90A4AE"

df = pd.read_csv(os.path.join(BASE,"..","PROCESADO","p3_sat_zscore_918.csv"),
                 encoding="utf-8-sig")

# Tipo principal y flag puro
df["tipo_principal"] = df["tipos_formacion"]
df["es_puro"] = (
    ((df["n_taller"]>0)   & (df["n_diplomado"]==0) & (df["n_proyecto"]==0)) |
    ((df["n_diplomado"]>0) & (df["n_taller"]==0)   & (df["n_proyecto"]==0)) |
    ((df["n_proyecto"]>0)  & (df["n_taller"]==0)   & (df["n_diplomado"]==0))
)

# Simplificar tipo para los mixtos
def simplificar(row):
    if row["es_puro"]: return row["tipo_principal"]
    if row["n_taller"]>0 and row["n_diplomado"]>0: return "TALLER+DIPLOMADO"
    if row["n_taller"]>0 and row["n_proyecto"]>0:  return "TALLER+PROYECTO"
    return "MIXTO"
df["tipo_label"] = df.apply(simplificar, axis=1)

TIPOS  = ["TALLER","DIPLOMADO","PROYECTO"]
COLORES = {"TALLER": C_TALLER, "DIPLOMADO": C_DIPLOMADO, "PROYECTO": C_PROYECTO}
MARKERS = {"TALLER": "o", "DIPLOMADO": "s", "PROYECTO": "^"}

# ── Cascada ───────────────────────────────────────────────────────────────────
n_total = len(df)
n_puro  = df["es_puro"].sum()
n_mixto = (~df["es_puro"]).sum()

print("=" * 65)
print("  G1 CONTRASTE — Trayectoria SAT: Normal vs Población Pura")
print("=" * 65)
print(f"  197 docentes aptos P3")
print(f"    ├── {n_puro} población pura  (una sola modalidad)")
print(f"    │     ├── TALLER   : n={len(df[(df['tipo_principal']=='TALLER')   &  df['es_puro']])}")
print(f"    │     ├── DIPLOMADO: n={len(df[(df['tipo_principal']=='DIPLOMADO') &  df['es_puro']])}")
print(f"    │     └── PROYECTO : n={len(df[(df['tipo_principal']=='PROYECTO')  &  df['es_puro']])}")
print(f"    └── {n_mixto} mixtos (más de una modalidad)")
print()
for tipo in TIPOS:
    all_b = df[df["tipo_principal"].str.contains(tipo)]["z_baseline"].mean()
    all_r = df[df["tipo_principal"].str.contains(tipo)]["z_resultado"].mean()
    pur_b = df[(df["tipo_principal"]==tipo) & df["es_puro"]]["z_baseline"].mean()
    pur_r = df[(df["tipo_principal"]==tipo) & df["es_puro"]]["z_resultado"].mean()
    print(f"  {tipo:10}: Normal  baseline={all_b:+.3f} → resultado={all_r:+.3f} (Δ={all_r-all_b:+.3f})")
    print(f"            Puro    baseline={pur_b:+.3f} → resultado={pur_r:+.3f} (Δ={pur_r-pur_b:+.3f})")
    print()
print("=" * 65)

# ── Figura ────────────────────────────────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7), sharey=True)
fig.suptitle(
    "Trayectoria SAT (Z-score) — Población Normal vs Población Pura\n"
    "Universo 917 · 197 docentes aptos P3 · Baseline → Resultado",
    fontsize=13, fontweight="bold")

MOMENTOS = ["Baseline", "Resultado"]

def plot_trayectoria(ax, filtro_df, titulo, mostrar_mixtos=False):
    for tipo in TIPOS:
        sub = filtro_df[filtro_df["tipo_principal"].str.contains(tipo)]
        n   = len(sub)
        if n == 0: continue
        vals = [sub["z_baseline"].mean(), sub["z_resultado"].mean()]
        color = COLORES[tipo]
        ax.plot([0,1], vals, marker=MARKERS[tipo], color=color,
                linewidth=2.5, markersize=10, label=f"{tipo.capitalize()} (n={n})",
                zorder=4)
        for xi, v in enumerate(vals):
            offset = 0.025 if xi==0 else -0.025
            ha = "left" if xi==0 else "right"
            ax.text(xi + offset, v + 0.015, f"{v:+.3f}",
                    ha=ha, fontsize=9.5, fontweight="bold", color=color)
        # Flecha de dirección
        delta = vals[1] - vals[0]
        ax.annotate("", xy=(1, vals[1]), xytext=(0, vals[0]),
                    arrowprops=dict(arrowstyle="->", color=color,
                                    lw=1.5, alpha=0.4))

    if mostrar_mixtos:
        mixtos = filtro_df[~filtro_df["es_puro"]]
        if len(mixtos) > 0:
            vals_m = [mixtos["z_baseline"].mean(), mixtos["z_resultado"].mean()]
            ax.plot([0,1], vals_m, marker="x", color="#AAAAAA",
                    linewidth=1.5, markersize=9, linestyle=":",
                    label=f"Mixtos (n={len(mixtos)})", zorder=3)

    ax.axhline(0, color="#CCCCCC", linewidth=1, linestyle="--", alpha=0.6)
    ax.set_xticks([0,1])
    ax.set_xticklabels(MOMENTOS, fontsize=12, fontweight="bold")
    ax.set_ylabel("Z-score SAT (desviaciones estándar)", fontsize=11)
    ax.set_title(titulo, pad=12, fontsize=12, fontweight="bold")
    ax.legend(fontsize=10, loc="lower right")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_xlim(-0.3, 1.3)

# Panel izquierdo — Población normal (todos los 197)
plot_trayectoria(ax1, df, f"Población Normal\n(todos los formados, n={n_total})",
                 mostrar_mixtos=False)

# Panel derecho — Población pura
df_puro = df[df["es_puro"]].copy()
plot_trayectoria(ax2, df_puro, f"Población Pura\n(una sola modalidad, n={n_puro})",
                 mostrar_mixtos=False)

# Nota en panel normal con los mixtos
ax1.text(0.5, 0.03,
         f"Incluye {n_mixto} mixtos (múltiples modalidades)",
         transform=ax1.transAxes, ha="center", fontsize=8.5,
         color="#888888", fontstyle="italic")
ax2.text(0.5, 0.03,
         f"Excluye {n_mixto} mixtos",
         transform=ax2.transAxes, ha="center", fontsize=8.5,
         color="#888888", fontstyle="italic")

plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nGuardado: {OUT}")
