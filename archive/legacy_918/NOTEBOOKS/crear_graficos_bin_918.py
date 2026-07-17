import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os

CSV = os.path.join(os.path.dirname(__file__), "..", "PROCESADO", "p3_bin_zscore_918.csv")
OUT = os.path.dirname(__file__)

df = pd.read_csv(CSV, encoding="utf-8-sig")
df["sexo"] = df["sexo"].fillna("").str.strip().str.upper()

matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 14, "axes.titlesize": 18, "axes.labelsize": 15,
    "xtick.labelsize": 13, "ytick.labelsize": 13, "legend.fontsize": 13,
})

TIPOS   = ["TALLER", "DIPLOMADO", "PROYECTO"]
COLORES = {"TALLER": "#2196F3", "DIPLOMADO": "#FF9800", "PROYECTO": "#4CAF50"}
MARCAS  = {"TALLER": "o",       "DIPLOMADO": "s",       "PROYECTO": "^"}

print(f"CSV cargado: {len(df)} docentes aptos P3 (SAT_BIN)")
print(f"Tipo principal:\n{df['tipo_principal'].value_counts().to_string()}\n")

# ─────────────────────────────────────────────────────────────────────────────
# G1.2 — Línea z_bin_baseline → z_bin_resultado por tipo de formación
# ─────────────────────────────────────────────────────────────────────────────
agg1 = df.groupby("tipo_principal").agg(
    n              = ("rut_key",        "count"),
    z_baseline     = ("z_bin_baseline",  "mean"),
    z_resultado    = ("z_bin_resultado", "mean"),
).round(3)
print("G1.2 — Trayectoria z_bin por tipo:")
print(agg1.to_string())

fig, ax = plt.subplots(figsize=(10, 6))

for tipo in TIPOS:
    if tipo not in agg1.index:
        continue
    row = agg1.loc[tipo]
    n   = int(row["n"])
    xs  = ["Baseline\n(pre-formación)", "Resultado\n(post-formación)"]
    ys  = [row["z_baseline"], row["z_resultado"]]
    ax.plot(xs, ys, marker=MARCAS[tipo], color=COLORES[tipo],
            linewidth=2.5, markersize=11, label=f"{tipo} (n={n})")
    ax.annotate(f"{ys[-1]:+.3f}", xy=(xs[-1], ys[-1]),
                xytext=(10, 0), textcoords="offset points",
                fontsize=12, color=COLORES[tipo], fontweight="bold")

ax.axhline(0, color="gray", linewidth=1, linestyle="--", alpha=0.6,
           label="Promedio facultad (z=0)")
ax.set_title("Trayectoria Z-score ¿Recomendaría al docente?\nbaseline → resultado por tipo de formación",
             pad=14, fontweight="bold")
ax.set_ylabel("Z-score promedio\n(posición relativa en facultad)")
ax.set_xlabel("")
ax.legend(loc="upper left")
ax.set_ylim(-0.5, 0.7)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
plt.tight_layout()
out1 = os.path.join(OUT, "G1.2_linea_zbin_918.png")
plt.savefig(out1, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nGuardado: {out1}")

# ─────────────────────────────────────────────────────────────────────────────
# G2.2 — Barras: Δz_bin y % mejora por tipo de formación
# ─────────────────────────────────────────────────────────────────────────────
agg2 = df.groupby("tipo_principal").agg(
    n          = ("rut_key",      "count"),
    delta_z    = ("delta_z_bin",  "mean"),
    pct_mejora = ("mejoro_z_bin", "mean"),
).round(3).reindex(["DIPLOMADO", "PROYECTO", "TALLER"])
agg2["pct_100"] = (agg2["pct_mejora"] * 100).round(1)
print("\nG2.2 — Delta Z bin y % mejora:")
print(agg2.to_string())

tipos2   = [t for t in ["DIPLOMADO", "PROYECTO", "TALLER"] if t in agg2.index]
colores2 = [COLORES[t] for t in tipos2]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
fig.suptitle("Impacto de la formación por tipo — ¿Recomendaría al docente? (SAT_BIN)\nZ-score posición relativa dentro de la facultad",
             fontsize=16, fontweight="bold")

bars1 = ax1.barh(tipos2, agg2.loc[tipos2, "delta_z"], color=colores2, height=0.5)
ax1.axvline(0, color="gray", linewidth=1.2, linestyle="--")
ax1.set_xlabel("Δ Z-score promedio (baseline → resultado)")
ax1.set_title("Cambio en posición relativa")
for bar, tipo in zip(bars1, tipos2):
    val = agg2.loc[tipo, "delta_z"]
    n   = int(agg2.loc[tipo, "n"])
    sign = "+" if val >= 0 else ""
    ax1.text(val + (0.005 if val >= 0 else -0.005),
             bar.get_y() + bar.get_height()/2,
             f"{sign}{val:.3f}  (n={n})",
             va="center", ha="left" if val >= 0 else "right",
             fontsize=12, fontweight="bold")
ax1.set_xlim(-0.35, 0.35)
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)

bars2 = ax2.barh(tipos2, agg2.loc[tipos2, "pct_100"], color=colores2, height=0.5)
ax2.axvline(50, color="gray", linewidth=1.2, linestyle="--", alpha=0.7)
ax2.set_xlabel("% de docentes que mejoró su z-score")
ax2.set_title("% docentes que mejoraron")
ax2.set_xlim(0, 100)
for bar, tipo in zip(bars2, tipos2):
    val = agg2.loc[tipo, "pct_100"]
    ax2.text(val + 1.5, bar.get_y() + bar.get_height()/2,
             f"{val:.0f}%", va="center", fontsize=12, fontweight="bold")
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)

plt.tight_layout()
out2 = os.path.join(OUT, "G2.2_barras_tipo_bin_918.png")
plt.savefig(out2, dpi=150, bbox_inches="tight")
plt.close()
print(f"Guardado: {out2}")

# ─────────────────────────────────────────────────────────────────────────────
# G3.2 — Heatmap Δz_bin: antigüedad × tipo  (solo perfil completo)
# ─────────────────────────────────────────────────────────────────────────────
df3 = df[df["tiene_perfil_completo"] == True].copy()

def tramo3(t):
    if t == "0-4":             return "Noveles\n(0–4 años)"
    if t in ("5-9", "10-14"): return "Consolidados\n(5–14 años)"
    return                           "Senior\n(15+ años)"

df3["tramo_ant3"] = df3["tramo_antiguedad"].apply(tramo3)

ORD_ANT  = ["Noveles\n(0–4 años)", "Consolidados\n(5–14 años)", "Senior\n(15+ años)"]
ORD_TIPO = ["TALLER", "DIPLOMADO", "PROYECTO"]

piv_d3 = (df3.groupby(["tramo_ant3", "tipo_principal"])["delta_z_bin"]
            .mean().unstack().reindex(index=ORD_ANT, columns=ORD_TIPO))
piv_n3 = (df3.groupby(["tramo_ant3", "tipo_principal"])["delta_z_bin"]
            .count().unstack().reindex(index=ORD_ANT, columns=ORD_TIPO).fillna(0))

rows3 = [r for r in ORD_ANT  if r in piv_d3.index and piv_d3.loc[r].notna().any()]
cols3 = [c for c in ORD_TIPO if c in piv_d3.columns]
data3 = piv_d3.reindex(index=rows3, columns=cols3).values.astype(float)

print(f"\nG3.2 — Heatmap pct_si z-score por antigüedad (n={len(df3)}):")
print(piv_d3.round(3).to_string())

fig, ax = plt.subplots(figsize=(10, 7))
im = ax.imshow(data3, cmap="RdYlGn", vmin=-0.5, vmax=0.5, aspect="auto")
ax.set_xticks(range(len(cols3))); ax.set_xticklabels(cols3, fontsize=14, fontweight="bold")
ax.set_yticks(range(len(rows3))); ax.set_yticklabels(rows3, fontsize=13)
ax.set_xlabel("Tipo de formación", fontsize=14)
ax.set_ylabel("Tramo antigüedad", fontsize=14)
n_g3 = len(df3)
n_sin_ant = len(df) - n_g3
ax.set_title(f"Δ Z-score ¿Recomendaría? — Antigüedad × Tipo de formación\n"
             f"Universo 917 · 197 aptos P3 · {n_g3} con antigüedad disponible · {n_sin_ant} sin dato excluidos",
             pad=12, fontsize=14, fontweight="bold")

for i, row in enumerate(rows3):
    for j, col in enumerate(cols3):
        delta = piv_d3.loc[row, col] if (row in piv_d3.index and col in piv_d3.columns) else np.nan
        n     = int(piv_n3.loc[row, col]) if (row in piv_n3.index and col in piv_n3.columns) else 0
        if pd.isna(delta) or n == 0:
            ax.add_patch(plt.Rectangle((j-0.5, i-0.5), 1, 1, color="#EEEEEE", zorder=2))
            ax.text(j, i, "—", ha="center", va="center", fontsize=16, color="#BBBBBB")
        else:
            sign   = "+" if delta >= 0 else ""
            txt_c  = "white" if abs(delta) > 0.30 else "black"
            weight = "bold" if n >= 10 else "normal"
            nota   = " *" if n < 5 else ""
            ax.text(j, i, f"{sign}{delta:.2f}{nota}\nn={n}",
                    ha="center", va="center", fontsize=12, fontweight=weight, color=txt_c)

plt.colorbar(im, ax=ax, label="Δ Z-score promedio", shrink=0.85).ax.tick_params(labelsize=11)
ax.spines[:].set_visible(False)
fig.text(0.5, -0.02, "Negrita = n ≥ 10  ·  * = n < 5 (baja confianza)  ·  — = sin datos",
         ha="center", fontsize=11, color="gray")
plt.tight_layout()
out3 = os.path.join(OUT, "G3.2_heatmap_antiguedad_bin_918.png")
plt.savefig(out3, dpi=150, bbox_inches="tight")
plt.close()
print(f"Guardado: {out3}")

# ─────────────────────────────────────────────────────────────────────────────
# G4.2 — Heatmap Δz_bin: jerarquía × tipo
# ─────────────────────────────────────────────────────────────────────────────
jer_map = {
    "INSTRUCTOR DOCENTE": "Instructor Doc.",
    "ASISTENTE DOCENTE":  "Asist. Docente",
    "ASISTENTE REGULAR":  "Asist. Regular",
    "ASOCIADO DOCENTE":   "Asoc. Docente",
    "ASOCIADO REGULAR":   "Asoc. Regular",
    "TITULAR DOCENTE":    "Titular Docente",
    "TITULAR REGULAR":    "Titular Regular",
}
df["jer_short"] = df["jerarquia"].map(jer_map).fillna(df["jerarquia"])

ORD_JER = ["Instructor Doc.", "Asist. Docente", "Asist. Regular",
           "Asoc. Docente",   "Asoc. Regular",  "Titular Docente", "Titular Regular"]

piv_d4 = (df.groupby(["jer_short", "tipo_principal"])["delta_z_bin"]
           .mean().unstack().reindex(index=ORD_JER, columns=ORD_TIPO))
piv_n4 = (df.groupby(["jer_short", "tipo_principal"])["delta_z_bin"]
           .count().unstack().reindex(index=ORD_JER, columns=ORD_TIPO).fillna(0))

rows4 = [r for r in ORD_JER if r in piv_d4.index and piv_d4.loc[r].notna().any()]
cols4 = [c for c in ORD_TIPO if c in piv_d4.columns]
data4 = piv_d4.reindex(index=rows4, columns=cols4).values.astype(float)

print(f"\nG4.2 — Heatmap pct_si z-score por jerarquía:")
print(piv_d4.round(3).to_string())

fig, ax = plt.subplots(figsize=(10, 7))
im = ax.imshow(data4, cmap="RdYlGn", vmin=-0.5, vmax=0.5, aspect="auto")
ax.set_xticks(range(len(cols4))); ax.set_xticklabels(cols4, fontsize=14, fontweight="bold")
ax.set_yticks(range(len(rows4))); ax.set_yticklabels(rows4, fontsize=13)
ax.set_xlabel("Tipo de formación", fontsize=14)
ax.set_ylabel("Jerarquía académica", fontsize=14)
ax.set_title("Δ Z-score ¿Recomendaría? — Jerarquía × Tipo de formación\n(Universo 917, Jr → Senior)",
             pad=12, fontsize=16, fontweight="bold")

for i, row in enumerate(rows4):
    for j, col in enumerate(cols4):
        delta = piv_d4.loc[row, col] if (row in piv_d4.index and col in piv_d4.columns) else np.nan
        n     = int(piv_n4.loc[row, col]) if (row in piv_n4.index and col in piv_n4.columns) else 0
        if pd.isna(delta) or n == 0:
            ax.add_patch(plt.Rectangle((j-0.5, i-0.5), 1, 1, color="#EEEEEE", zorder=2))
            ax.text(j, i, "—", ha="center", va="center", fontsize=16, color="#BBBBBB")
        else:
            sign   = "+" if delta >= 0 else ""
            txt_c  = "white" if abs(delta) > 0.30 else "black"
            weight = "bold" if n >= 10 else "normal"
            nota   = " *" if n < 5 else ""
            ax.text(j, i, f"{sign}{delta:.2f}{nota}\nn={n}",
                    ha="center", va="center", fontsize=12, fontweight=weight, color=txt_c)

plt.colorbar(im, ax=ax, label="Δ Z-score promedio", shrink=0.85).ax.tick_params(labelsize=11)
ax.spines[:].set_visible(False)
fig.text(0.5, -0.02, "Negrita = n ≥ 10  ·  * = n < 5 (baja confianza)  ·  — = sin datos",
         ha="center", fontsize=11, color="gray")
plt.tight_layout()
out4 = os.path.join(OUT, "G4.2_heatmap_jerarquia_bin_918.png")
plt.savefig(out4, dpi=150, bbox_inches="tight")
plt.close()
print(f"Guardado: {out4}")

# ─────────────────────────────────────────────────────────────────────────────
# G5.2 — Barras Δz_bin por sexo × tipo
# ─────────────────────────────────────────────────────────────────────────────
df["sexo_norm"] = df["sexo"].map(
    {"MUJER":"F","FEMENINO":"F","HOMBRE":"M","MASCULINO":"M","F":"F","M":"M"}
)
df5 = df[df["sexo_norm"].isin(["M","F"])].copy()

agg5 = df5.groupby(["sexo_norm", "tipo_principal"]).agg(
    n          = ("rut_key",      "count"),
    delta_z    = ("delta_z_bin",  "mean"),
    pct_mejora = ("mejoro_z_bin", "mean"),
).round(3)
print(f"\nG5.2 — Delta Z bin por sexo × tipo (n={len(df5)}):")
print(agg5.to_string())

SEXOS     = ["F", "M"]
SEX_LABEL = {"F": "Mujer", "M": "Hombre"}
SEX_COLOR = {"F": "#E91E63", "M": "#4CAF50"}
x         = np.arange(len(TIPOS))
width     = 0.35

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle("Δ Z-score ¿Recomendaría? por Sexo × Tipo de formación — Universo 917",
             fontsize=15, fontweight="bold")

for i, sexo in enumerate(SEXOS):
    if sexo not in agg5.index.get_level_values("sexo_norm"):
        continue
    sub      = agg5.loc[sexo].reindex(TIPOS)
    vals_dz  = sub["delta_z"].values
    vals_pct = (sub["pct_mejora"] * 100).values
    ns       = sub["n"].fillna(0).values
    offset   = (i - len(SEXOS)/2 + 0.5) * width
    color    = SEX_COLOR[sexo]
    label    = SEX_LABEL[sexo]

    bars1 = ax1.bar(x + offset, np.nan_to_num(vals_dz),  width, label=label, color=color, alpha=0.85)
    bars2 = ax2.bar(x + offset, np.nan_to_num(vals_pct), width, label=label, color=color, alpha=0.85)

    for bar, val, n in zip(bars1, vals_dz, ns):
        if pd.notna(val) and n > 0:
            sign = "+" if val >= 0 else ""
            ax1.text(bar.get_x() + bar.get_width()/2,
                     val + (0.010 if val >= 0 else -0.015),
                     f"{sign}{val:.2f}\n(n={int(n)})",
                     ha="center", va="bottom" if val >= 0 else "top",
                     fontsize=10, fontweight="bold", color=color)
    for bar, val, n in zip(bars2, vals_pct, ns):
        if pd.notna(val) and n > 0:
            ax2.text(bar.get_x() + bar.get_width()/2, val + 1.5,
                     f"{val:.0f}%", ha="center", va="bottom",
                     fontsize=10, fontweight="bold", color=color)

ax1.axhline(0, color="gray", linewidth=1, linestyle="--")
ax1.set_xticks(x); ax1.set_xticklabels(TIPOS)
ax1.set_ylabel("Δ Z-score promedio (% recomendación)")
ax1.set_title("Cambio en posición relativa")
ax1.set_ylim(-0.4, 0.4)
ax1.legend(); ax1.spines["top"].set_visible(False); ax1.spines["right"].set_visible(False)

ax2.axhline(50, color="gray", linewidth=1, linestyle="--", alpha=0.7)
ax2.set_xticks(x); ax2.set_xticklabels(TIPOS)
ax2.set_ylabel("% de docentes que mejoró")
ax2.set_title("% docentes que mejoraron")
ax2.set_ylim(0, 105)
ax2.legend(); ax2.spines["top"].set_visible(False); ax2.spines["right"].set_visible(False)

plt.tight_layout()
out5 = os.path.join(OUT, "G5.2_barras_sexo_bin_918.png")
plt.savefig(out5, dpi=150, bbox_inches="tight")
plt.close()
print(f"Guardado: {out5}")

print("\n" + "="*55)
print("COMPLETO — G1.2 a G5.2 generados")
print("="*55)
for f in [out1, out2, out3, out4, out5]:
    print(f"  {os.path.basename(f)}")
