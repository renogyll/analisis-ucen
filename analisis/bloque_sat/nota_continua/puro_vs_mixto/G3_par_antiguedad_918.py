import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os

BASE = os.path.dirname(__file__)
OUT  = os.path.join(BASE, "G3_par_antiguedad_918.png")

matplotlib.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})

# ── Cargar datos ──────────────────────────────────────────────────────────────
df_sat = pd.read_csv(os.path.join(BASE,"..","PROCESADO","p3_sat_zscore_918.csv"),
                     encoding="utf-8-sig")
df_bin = pd.read_csv(os.path.join(BASE,"..","PROCESADO","p3_bin_zscore_918.csv"),
                     encoding="utf-8-sig")

def tramo3(t):
    if t == "0-4":             return "Noveles\n(0–4 años)"
    if t in ("5-9", "10-14"): return "Consolidados\n(5–14 años)"
    return                           "Senior\n(15+ años)"

ORD_ANT  = ["Noveles\n(0–4 años)", "Consolidados\n(5–14 años)", "Senior\n(15+ años)"]
ORD_TIPO = ["TALLER", "DIPLOMADO", "PROYECTO"]

def tipo_p(r):
    if r["n_diplomado"] > 0: return "DIPLOMADO"
    if r["n_proyecto"]  > 0: return "PROYECTO"
    return "TALLER"

for d in [df_sat, df_bin]:
    d["tramo_ant3"]    = d["tramo_antiguedad"].apply(tramo3)
    d["tipo_principal"] = d.apply(tipo_p, axis=1)

df_sat3 = df_sat[df_sat["tiene_perfil_completo"] == True].copy()
df_bin3 = df_bin[df_bin["tiene_perfil_completo"] == True].copy()

n_ok      = len(df_sat3)
n_total   = len(df_sat)
n_sin_ant = n_total - n_ok

def build_pivots(df, col_delta):
    piv_d = (df.groupby(["tramo_ant3","tipo_principal"])[col_delta]
               .mean().unstack().reindex(index=ORD_ANT, columns=ORD_TIPO))
    piv_n = (df.groupby(["tramo_ant3","tipo_principal"])[col_delta]
               .count().unstack().reindex(index=ORD_ANT, columns=ORD_TIPO).fillna(0))
    rows = [r for r in ORD_ANT  if r in piv_d.index and piv_d.loc[r].notna().any()]
    cols = [c for c in ORD_TIPO if c in piv_d.columns]
    return piv_d, piv_n, rows, cols

piv_d_sat, piv_n_sat, rows_sat, cols_sat = build_pivots(df_sat3, "delta_z")
piv_d_bin, piv_n_bin, rows_bin, cols_bin = build_pivots(df_bin3, "delta_z_bin")

# ── Figura: dos heatmaps pareados ─────────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))

# Títulos de panel en color naranja arriba
fig.text(0.27, 0.99, "SAT Nota", ha="center", fontsize=14,
         fontweight="bold", color="#E65100")
fig.text(0.73, 0.99, "SAT % Recomendación", ha="center", fontsize=14,
         fontweight="bold", color="#E65100")

# Subtítulo general más abajo, sin solapar
fig.text(0.5, 0.94,
         f"Universo 917 · 197 aptos P3 · {n_ok} con antigüedad disponible · {n_sin_ant} sin dato excluidos",
         ha="center", fontsize=12, fontweight="bold", color="#1A1A1A")

def make_heatmap(ax, piv_d, piv_n, rows, cols, title):
    data = piv_d.reindex(index=rows, columns=cols).values.astype(float)
    im = ax.imshow(data, cmap="RdYlGn", vmin=-0.5, vmax=0.5, aspect="auto")

    ax.set_xticks(range(len(cols))); ax.set_xticklabels(cols, fontsize=13, fontweight="bold")
    ax.set_yticks(range(len(rows))); ax.set_yticklabels(rows, fontsize=12)
    ax.set_xlabel("Tipo de formación", fontsize=13)
    ax.set_ylabel("Tramo antigüedad", fontsize=13)
    ax.set_title(title, pad=12, fontsize=13, fontweight="bold")

    for i, row in enumerate(rows):
        for j, col in enumerate(cols):
            delta = piv_d.loc[row, col] if (row in piv_d.index and col in piv_d.columns) else np.nan
            n     = int(piv_n.loc[row, col]) if (row in piv_n.index and col in piv_n.columns) else 0
            if np.isnan(delta) or n == 0:
                ax.text(j, i, "—", ha="center", va="center", fontsize=13, color="#999999")
            else:
                bold = n >= 10
                star = "*" if n < 5 else ""
                txt  = f"{delta:+.2f}{star}\nn={n}"
                ax.text(j, i, txt, ha="center", va="center",
                        fontsize=12, fontweight="bold" if bold else "normal",
                        color="white" if abs(delta) > 0.25 else "black")

    plt.colorbar(im, ax=ax, label="Δ Z-score promedio", shrink=0.8)

    ax.text(0.5, -0.12,
            "Negrita = n ≥ 10  ·  * = n < 5 (baja confianza)  ·  — = sin datos",
            ha="center", transform=ax.transAxes, fontsize=9, color="#666666")

    return im

make_heatmap(ax1, piv_d_sat, piv_n_sat, rows_sat, cols_sat,
             "Δ Z-score SAT — Antigüedad × Tipo de formación")
make_heatmap(ax2, piv_d_bin, piv_n_bin, rows_bin, cols_bin,
             "Δ Z-score ¿Recomendaría? — Antigüedad × Tipo de formación")

plt.tight_layout(rect=[0, 0, 1, 0.91])
plt.savefig(OUT, dpi=150, bbox_inches="tight")
plt.close()
print(f"Guardado: {OUT}")
