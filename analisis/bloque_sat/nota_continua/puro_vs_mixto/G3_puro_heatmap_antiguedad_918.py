import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os

BASE = os.path.dirname(__file__)
OUT  = os.path.join(BASE, "G3_puro_heatmap_antiguedad_918.png")

matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 12,
})

# ── Cargar ─────────────────────────────────────────────────────────────────────
p3 = pd.read_csv(os.path.join(BASE, "..", "PROCESADO", "p3_sat_zscore_918.csv"),
                 encoding="utf-8-sig", dtype={"rut_key": str})
p3["rut_key"] = p3["rut_key"].str.strip()

def tipo_principal(r):
    if r["n_diplomado"] > 0: return "DIPLOMADO"
    if r["n_proyecto"]  > 0: return "PROYECTO"
    return "TALLER"
p3["tipo_principal"] = p3.apply(tipo_principal, axis=1)

# ── Pobaciones PURAS (sin mezcla de tipos) ────────────────────────────────────
# TALLER puro   : ya implica n_diplomado=0, n_proyecto=0
# DIPLOMADO puro: clasificado como DIPLOMADO y además n_taller=0
# PROYECTO puro : clasificado como PROYECTO  y además n_taller=0

mask_puro = (
    ((p3["tipo_principal"] == "TALLER")   )                        |
    ((p3["tipo_principal"] == "DIPLOMADO") & (p3["n_taller"] == 0))|
    ((p3["tipo_principal"] == "PROYECTO")  & (p3["n_taller"] == 0))
)
df_puro = p3[mask_puro].copy()

print("=== Población pura por tipo ===")
for t in ["TALLER", "DIPLOMADO", "PROYECTO"]:
    sub = df_puro[df_puro["tipo_principal"] == t]
    print(f"  {t}: {len(sub)} total  |  con perfil completo: {sub['tiene_perfil_completo'].sum()}")

# ── Solo perfil completo (tienen antigüedad) ───────────────────────────────────
df3 = df_puro[df_puro["tiene_perfil_completo"] == True].copy()
print(f"\nCon perfil completo (tienen antigüedad): {len(df3)}")

# Reagrupar en 3 tramos
def tramo3(t):
    if t == "0-4":            return "Noveles\n(0–4 años)"
    if t in ("5-9", "10-14"): return "Consolidados\n(5–14 años)"
    return                           "Senior\n(15+ años)"

df3["tramo_ant3"] = df3["tramo_antiguedad"].apply(tramo3)

ORD_ANT  = ["Noveles\n(0–4 años)", "Consolidados\n(5–14 años)", "Senior\n(15+ años)"]
ORD_TIPO = ["TALLER", "DIPLOMADO", "PROYECTO"]

piv_dz = (df3.groupby(["tramo_ant3", "tipo_principal"])["delta_z"]
             .mean().unstack()
             .reindex(index=ORD_ANT, columns=ORD_TIPO))
piv_n  = (df3.groupby(["tramo_ant3", "tipo_principal"])["delta_z"]
             .count().unstack()
             .reindex(index=ORD_ANT, columns=ORD_TIPO).fillna(0))

print("\nΔ Z-score promedio:")
print(piv_dz.round(3).to_string())
print("\nn por celda:")
print(piv_n.astype(int).to_string())

rows = [r for r in ORD_ANT  if r in piv_dz.index and piv_dz.loc[r].notna().any()]
cols = [c for c in ORD_TIPO if c in piv_dz.columns]
data = piv_dz.reindex(index=rows, columns=cols).values.astype(float)

# ── Figura ─────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 7))

im = ax.imshow(data, cmap="RdYlGn", vmin=-0.5, vmax=0.5, aspect="auto")

ax.set_xticks(range(len(cols)))
ax.set_xticklabels(cols, fontsize=14, fontweight="bold")
ax.set_yticks(range(len(rows)))
ax.set_yticklabels(rows, fontsize=13)
ax.set_xlabel("Tipo de formación (población pura — sin mezcla)", fontsize=13)
ax.set_ylabel("Tramo de antigüedad", fontsize=13)
ax.set_title(
    "Δ Z-score SAT — Antigüedad × Tipo de formación\n"
    "Universo 917 · Poblaciones puras: TALLER=154, DIPLOMADO=27, PROYECTO=3",
    pad=12, fontsize=15, fontweight="bold"
)

for i, row in enumerate(rows):
    for j, col in enumerate(cols):
        dz = piv_dz.loc[row, col] if (row in piv_dz.index and col in piv_dz.columns) else np.nan
        n  = int(piv_n.loc[row, col]) if (row in piv_n.index and col in piv_n.columns) else 0
        if pd.isna(dz) or n == 0:
            ax.add_patch(plt.Rectangle((j-0.5, i-0.5), 1, 1, color="#EEEEEE", zorder=2))
            ax.text(j, i, "—", ha="center", va="center", fontsize=16, color="#BBBBBB")
        else:
            sign   = "+" if dz >= 0 else ""
            txt_c  = "white" if abs(dz) > 0.30 else "black"
            weight = "bold" if n >= 10 else "normal"
            nota   = " *" if n < 5 else ""
            ax.text(j, i, f"{sign}{dz:.2f}{nota}\nn={n}",
                    ha="center", va="center", fontsize=12,
                    fontweight=weight, color=txt_c)

plt.colorbar(im, ax=ax, label="Δ Z-score promedio", shrink=0.85).ax.tick_params(labelsize=11)
ax.spines[:].set_visible(False)
fig.text(0.5, -0.02,
         "Negrita = n ≥ 10  ·  * = n < 5 (baja confianza)  ·  — = sin datos  ·  "
         "Excluidos: 9 doc. diplomado+taller y 4 doc. proyecto+taller",
         ha="center", fontsize=10, color="gray")

plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nGuardado: {OUT}")

# ── Bajadas ────────────────────────────────────────────────────────────────────
print("""
BAJADAS PARA EL INFORME
───────────────────────
• Al analizar exclusivamente las poblaciones puras —docentes que realizaron un
  único tipo de formación— el patrón del grupo TALLER (n=154) se mantiene estable
  a lo largo de los tres tramos de antigüedad, sin diferencias relevantes entre
  noveles, consolidados y senior, lo que sugiere que el taller genera un efecto
  homogéneo independiente de la trayectoria del docente.

• El grupo DIPLOMADO puro (n=27) concentra sus efectivos principalmente en el
  tramo consolidado y senior; el PROYECTO puro queda con n=3 lo que impide
  extraer conclusiones confiables. Los celdas marcadas con * deben interpretarse
  con cautela por el bajo n muestral.
""")
