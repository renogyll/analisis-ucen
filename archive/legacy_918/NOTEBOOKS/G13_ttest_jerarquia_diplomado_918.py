import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib
import numpy as np
from scipy.stats import ttest_ind, f_oneway
from itertools import combinations
import os

BASE = os.path.dirname(__file__)
matplotlib.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12})

# ── Cargar datos ──────────────────────────────────────────────────────────────
p3 = pd.read_csv(os.path.join(BASE, "..", "PROCESADO", "p3_sat_zscore_918.csv"),
                 encoding="utf-8-sig", dtype={"rut_key": str})
p3["rut_key"] = p3["rut_key"].str.strip()

# Derivar tipo_principal: DIPLOMADO > PROYECTO > TALLER
def tipo_principal(row):
    if row["n_diplomado"] > 0: return "DIPLOMADO"
    if row["n_proyecto"]  > 0: return "PROYECTO"
    return "TALLER"
p3["tipo_principal"] = p3.apply(tipo_principal, axis=1)

# jerarquia ya está en p3_sat_zscore_918.csv
# Filtrar DIPLOMADO únicamente
dip = p3[p3["tipo_principal"] == "DIPLOMADO"].copy()

print(f"Diplomados aptos P3: {len(dip)}")
print(dip.groupby("jerarquia")["rut_key"].count().to_string())

# ── Abreviar jerarquías ───────────────────────────────────────────────────────
jer_map = {
    "INSTRUCTOR DOCENTE": "Instructor Doc.",
    "ASISTENTE DOCENTE":  "Asist. Docente",
    "ASISTENTE REGULAR":  "Asist. Regular",
    "ASOCIADO DOCENTE":   "Asoc. Docente",
    "ASOCIADO REGULAR":   "Asoc. Regular",
    "TITULAR DOCENTE":    "Titular Docente",
    "TITULAR REGULAR":    "Titular Regular",
}
dip["jer"] = dip["jerarquia"].map(jer_map).fillna(dip["jerarquia"])

# ── Orden y filtro mínimo ─────────────────────────────────────────────────────
ORD_JER = ["Instructor Doc.", "Asist. Docente", "Asist. Regular",
           "Asoc. Docente", "Asoc. Regular", "Titular Docente", "Titular Regular"]
MIN_N = 3  # mínimo para incluir en comparación

grupos_validos = dip.groupby("jer")["delta_z"].count()
grupos_validos = grupos_validos[grupos_validos >= MIN_N]
jer_incl = [j for j in ORD_JER if j in grupos_validos.index]

print(f"\nJerarquías con n≥{MIN_N}: {jer_incl}")

def sig(p):
    if p < 0.001: return "***"
    if p < 0.01:  return "**"
    if p < 0.05:  return "*"
    return "ns"

# ── Tabla descriptiva por jerarquía ──────────────────────────────────────────
desc_rows = []
grupos_data = {}
for jer in jer_incl:
    vals = dip[dip["jer"] == jer]["delta_z"].dropna().values
    grupos_data[jer] = vals
    zb  = dip[dip["jer"] == jer]["z_baseline"].dropna().mean()
    zr  = dip[dip["jer"] == jer]["z_resultado"].dropna().mean()
    desc_rows.append([
        jer,
        f"{len(vals)}",
        f"{zb:+.3f}",
        f"{zr:+.3f}",
        f"{vals.mean():+.3f}",
        f"{vals.std():.3f}",
        f"{vals.min():+.3f}",
        f"{vals.max():+.3f}",
    ])

# ── ANOVA ─────────────────────────────────────────────────────────────────────
arrays = [grupos_data[j] for j in jer_incl]
F_val, p_anova = f_oneway(*arrays)

# Eta-cuadrado (η²)
grand_mean = np.concatenate(arrays).mean()
SS_between = sum(len(g) * (g.mean() - grand_mean)**2 for g in arrays)
SS_total   = sum(((v - grand_mean)**2).sum() for v in arrays)
eta2 = SS_between / SS_total if SS_total > 0 else 0.0

print(f"\nANOVA: F={F_val:.3f}, p={p_anova:.4f}, η²={eta2:.3f}, {sig(p_anova)}")

anova_row = [
    f"F = {F_val:.3f}",
    f"p = {p_anova:.4f}",
    f"η² = {eta2:.3f}",
    sig(p_anova),
    f"gl entre = {len(jer_incl)-1}",
    f"gl dentro = {sum(len(g) for g in arrays) - len(jer_incl)}",
]

# ── Pairwise t-tests (Bonferroni) ─────────────────────────────────────────────
pairs = list(combinations(jer_incl, 2))
n_tests = len(pairs)
pair_rows = []
print(f"\nPairwise t-tests (Bonferroni n={n_tests}):")
for j1, j2 in pairs:
    g1, g2 = grupos_data[j1], grupos_data[j2]
    t_val, p_raw = ttest_ind(g1, g2, equal_var=False)
    p_adj = min(p_raw * n_tests, 1.0)
    pool_sd = np.sqrt((g1.std()**2 + g2.std()**2) / 2)
    d = (g1.mean() - g2.mean()) / pool_sd if pool_sd > 0 else 0.0
    diff = g1.mean() - g2.mean()
    s_raw = sig(p_raw)
    s_adj = sig(p_adj)
    pair_rows.append([
        j1, j2,
        f"{int(len(g1))}", f"{int(len(g2))}",
        f"{diff:+.3f}",
        f"{t_val:+.3f}",
        f"{p_raw:.4f}",
        f"{p_adj:.4f}",
        f"{d:+.3f}",
        s_adj,
    ])
    print(f"  {j1} vs {j2}: Δ={diff:+.3f}, t={t_val:+.3f}, p={p_raw:.4f}, p_adj={p_adj:.4f}, d={d:+.3f} {s_adj}")

# ── FIGURA ─────────────────────────────────────────────────────────────────────
n_rows = 3  # desc / anova / pairwise
hr = [1.2, 0.4, max(1.2, len(pair_rows) * 0.28)]
fig, axes = plt.subplots(3, 1, figsize=(17, 13),
                          gridspec_kw={"height_ratios": hr})
fig.suptitle(
    "Prueba t por Jerarquía — Δ Z-score SAT Nota (Diplomados)\n"
    "Universo 917 · Solo aptos P3 tipo DIPLOMADO · Corrección Bonferroni",
    fontsize=17, fontweight="bold", y=0.99)

sig_colors_bg = {"***": "#C8E6C9", "**": "#DCEDC8", "*": "#F1F8E9", "ns": "#F5F5F5"}
sig_colors_fg = {"***": "#1B5E20", "**": "#388E3C", "*": "#66BB6A", "ns": "#9E9E9E"}

# ── Panel A: Descriptiva ──────────────────────────────────────────────────────
ax_a = axes[0]
ax_a.axis("off")
cols_a = ["Jerarquía", "n", "Z Baseline", "Z Resultado", "Δ Z promedio", "SD", "Δ Z mín.", "Δ Z máx."]
tbl_a = ax_a.table(cellText=desc_rows, colLabels=cols_a, loc="center", cellLoc="center")
tbl_a.auto_set_font_size(False)
tbl_a.set_fontsize(12)
tbl_a.scale(1, 1.75)
for j in range(len(cols_a)):
    tbl_a[0, j].set_facecolor("#37474F")
    tbl_a[0, j].set_text_props(color="white", fontweight="bold")
for i, row in enumerate(desc_rows, start=1):
    bg = "#FAFAFA" if i % 2 == 0 else "#FFFFFF"
    for j in range(len(cols_a)):
        tbl_a[i, j].set_facecolor(bg)
    # Colorear Δ Z promedio (col 4) según signo
    dz = float(row[4])
    tbl_a[i, 4].set_text_props(color="#1B5E20" if dz > 0 else "#C62828",
                                fontweight="bold")
ax_a.set_title("Panel A — Estadísticos descriptivos Δ Z-score por jerarquía",
               fontsize=13, fontweight="bold", loc="left", pad=8)

# ── Panel B: ANOVA ────────────────────────────────────────────────────────────
ax_b = axes[1]
ax_b.axis("off")
anova_bg = sig_colors_bg[sig(p_anova)]
anova_fg = sig_colors_fg[sig(p_anova)]
anova_label = [
    f"ANOVA  F({len(jer_incl)-1}, {sum(len(g) for g in arrays)-len(jer_incl)}) = {F_val:.3f}",
    f"p = {p_anova:.4f}",
    f"η² = {eta2:.3f}",
    sig(p_anova),
]
tbl_b = ax_b.table(
    cellText=[anova_label],
    colLabels=["Estadístico", "p-valor", "Tamaño efecto (η²)", "Sig."],
    loc="center", cellLoc="center")
tbl_b.auto_set_font_size(False)
tbl_b.set_fontsize(13)
tbl_b.scale(1, 1.6)
for j in range(4):
    tbl_b[0, j].set_facecolor("#37474F")
    tbl_b[0, j].set_text_props(color="white", fontweight="bold")
for j in range(4):
    tbl_b[1, j].set_facecolor(anova_bg)
tbl_b[1, 3].set_text_props(color=anova_fg, fontweight="bold")
ax_b.set_title("Panel B — ANOVA de un factor (Δ Z-score ~ Jerarquía)",
               fontsize=13, fontweight="bold", loc="left", pad=8)

# ── Panel C: Pairwise ─────────────────────────────────────────────────────────
ax_c = axes[2]
ax_c.axis("off")
if pair_rows:
    cols_c = ["Jerarquía A", "Jerarquía B",
              "n A", "n B", "Diferencia Δ", "t", "p crudo", "p Bonferroni", "Cohen d", "Sig."]
    tbl_c = ax_c.table(cellText=pair_rows, colLabels=cols_c, loc="center", cellLoc="center")
    tbl_c.auto_set_font_size(False)
    tbl_c.set_fontsize(11)
    tbl_c.scale(1, 1.8)
    for j in range(len(cols_c)):
        tbl_c[0, j].set_facecolor("#37474F")
        tbl_c[0, j].set_text_props(color="white", fontweight="bold")
    for i, row in enumerate(pair_rows, start=1):
        s = row[-1]
        for j in range(len(cols_c)):
            tbl_c[i, j].set_facecolor(sig_colors_bg[s])
        tbl_c[i, 9].set_text_props(color=sig_colors_fg[s],
                                   fontweight="bold" if s != "ns" else "normal")
else:
    ax_c.text(0.5, 0.5, "Datos insuficientes para comparaciones por pares.",
              ha="center", va="center", fontsize=13)

ax_c.set_title("Panel C — Comparaciones por pares (t independiente, corrección Bonferroni)",
               fontsize=13, fontweight="bold", loc="left", pad=8)

# ── Leyenda ───────────────────────────────────────────────────────────────────
legend_items = [
    mpatches.Patch(color="#1B5E20", label="*** p < 0.001"),
    mpatches.Patch(color="#388E3C", label="**  p < 0.01"),
    mpatches.Patch(color="#66BB6A", label="*   p < 0.05"),
    mpatches.Patch(color="#9E9E9E", label="ns  no significativo"),
]
fig.legend(handles=legend_items, loc="lower center", ncol=4,
           fontsize=12, framealpha=0.9, bbox_to_anchor=(0.5, 0.005))

plt.tight_layout(rect=[0, 0.04, 1, 0.97])
out = os.path.join(BASE, "G13_ttest_jerarquia_diplomado_918.png")
plt.savefig(out, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nGuardado: {out}")
