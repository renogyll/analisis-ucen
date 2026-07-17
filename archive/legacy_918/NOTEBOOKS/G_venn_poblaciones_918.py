import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os
from matplotlib_venn import venn3, venn3_circles

BASE = os.path.dirname(__file__)
OUT  = os.path.join(BASE, "G_venn_poblaciones_918.png")

matplotlib.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})

df = pd.read_csv(os.path.join(BASE,"..","PROCESADO","p3_sat_zscore_918.csv"),
                 encoding="utf-8-sig")

# Sets por modalidad
set_taller    = set(df[df["n_taller"]>0]["rut_key"])
set_diplomado = set(df[df["n_diplomado"]>0]["rut_key"])
set_proyecto  = set(df[df["n_proyecto"]>0]["rut_key"])

# Calcular cada región del Venn
solo_T = set_taller - set_diplomado - set_proyecto
solo_D = set_diplomado - set_taller - set_proyecto
solo_P = set_proyecto - set_taller - set_diplomado
T_D    = (set_taller & set_diplomado) - set_proyecto
T_P    = (set_taller & set_proyecto) - set_diplomado
D_P    = (set_diplomado & set_proyecto) - set_taller
T_D_P  = set_taller & set_diplomado & set_proyecto

n_total = len(df)
n_puro  = len(solo_T) + len(solo_D) + len(solo_P)
n_mixto = len(T_D) + len(T_P) + len(D_P) + len(T_D_P)

# ── Cascada ───────────────────────────────────────────────────────────────────
print("=" * 65)
print("  DISTRIBUCIÓN DE POBLACIONES — Normal vs Pura")
print("=" * 65)
print(f"  197 docentes aptos P3")
print(f"  │")
print(f"  ├── POBLACIONES PURAS (una sola modalidad): {n_puro}")
print(f"  │     ├── TALLER puro    : {len(solo_T):3d}  (solo talleres)")
print(f"  │     ├── DIPLOMADO puro : {len(solo_D):3d}  (solo diplomado)")
print(f"  │     └── PROYECTO puro  : {len(solo_P):3d}  (solo proyecto)")
print(f"  │")
print(f"  └── MIXTOS (más de una modalidad): {n_mixto}")
print(f"        ├── TALLER + DIPLOMADO : {len(T_D)}")
print(f"        ├── TALLER + PROYECTO  : {len(T_P)}")
print(f"        ├── DIPLOMADO+PROYECTO : {len(D_P)}")
print(f"        └── LAS 3 MODALIDADES : {len(T_D_P)}")
print("=" * 65)

# ── Figura — solo el Venn, más grande ──────────────────────────────────────────
fig, ax_venn = plt.subplots(figsize=(11, 9))
fig.suptitle(
    "Distribución de Poblaciones: Normal vs Pura\n"
    f"197 docentes aptos P3 · {n_puro} puros · {n_mixto} mixtos",
    fontsize=16, fontweight="bold")

# Panel A — Venn
plt.sca(ax_venn)
v = venn3(
    subsets=(len(solo_T), len(solo_D), len(T_D),
             len(solo_P), len(T_P), len(D_P), len(T_D_P)),
    set_labels=("", "", ""),
    ax=ax_venn
)

# Colores
colors = {"100":"#1976D2", "010":"#FF9800", "001":"#388E3C",
          "110":"#FFA726", "101":"#26A69A", "011":"#66BB6A", "111":"#BDBDBD"}
for region_id, color in colors.items():
    patch = v.get_patch_by_id(region_id)
    if patch:
        patch.set_color(color)
        patch.set_alpha(0.7)
        patch.set_edgecolor("white")
        patch.set_linewidth(2)

# Etiquetas con n
labels_map = {
    "100": f"TALLER\npuro\nn={len(solo_T)}",
    "010": f"DIPLOMADO\npuro\nn={len(solo_D)}",
    "001": f"PROYECTO\npuro\nn={len(solo_P)}",
    "110": f"T+D\nn={len(T_D)}",
    "101": f"T+P\nn={len(T_P)}",
    "011": f"D+P\nn={len(D_P)}",
    "111": f"T+D+P\nn={len(T_D_P)}",
}
for region_id, label_text in labels_map.items():
    lbl = v.get_label_by_id(region_id)
    if lbl:
        n_val = int(label_text.split("n=")[1])
        if n_val > 0:
            lbl.set_text(label_text)
            lbl.set_fontsize(13)
            lbl.set_fontweight("bold")
        else:
            lbl.set_text("")

# Circles
circles = venn3_circles(
    subsets=(len(solo_T), len(solo_D), len(T_D),
             len(solo_P), len(T_P), len(D_P), len(T_D_P)),
    ax=ax_venn,
    linewidth=2.5)
circle_colors = ["#1976D2", "#FF9800", "#388E3C"]
for circle, color in zip(circles, circle_colors):
    circle.set_edgecolor(color)
    circle.set_alpha(0.8)

# Etiquetas de sets fuera del círculo
ax_venn.text(-0.78, 0.48, f"TALLER\n(n={len(set_taller)})",
             fontsize=15, fontweight="bold", color="#1976D2", ha="center")
ax_venn.text(0.78, 0.48, f"DIPLOMADO\n(n={len(set_diplomado)})",
             fontsize=15, fontweight="bold", color="#FF9800", ha="center")
ax_venn.text(0, -0.75, f"PROYECTO\n(n={len(set_proyecto)})",
             fontsize=15, fontweight="bold", color="#388E3C", ha="center")

ax_venn.set_title("Diagrama de Venn — Intersecciones entre modalidades", pad=15, fontsize=13)

plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nGuardado: {OUT}")
