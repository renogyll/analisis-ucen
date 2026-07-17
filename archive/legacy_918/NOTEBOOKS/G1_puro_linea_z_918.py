import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os

BASE = os.path.dirname(__file__)
OUT  = os.path.join(BASE, "G1_puro_linea_z_918.png")

matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 14, "axes.titlesize": 18, "axes.labelsize": 15,
    "xtick.labelsize": 13, "ytick.labelsize": 13, "legend.fontsize": 13,
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

# ── Pobaciones PURAS ──────────────────────────────────────────────────────────
mask_puro = (
    (p3["tipo_principal"] == "TALLER")                                          |
    ((p3["tipo_principal"] == "DIPLOMADO") & (p3["n_taller"] == 0))             |
    ((p3["tipo_principal"] == "PROYECTO")  & (p3["n_taller"] == 0))
)
df = p3[mask_puro].copy()

TIPOS   = ["TALLER", "DIPLOMADO", "PROYECTO"]
COLORES = {"TALLER": "#2196F3", "DIPLOMADO": "#FF9800", "PROYECTO": "#4CAF50"}
MARCAS  = {"TALLER": "o",       "DIPLOMADO": "s",       "PROYECTO": "^"}

agg = df.groupby("tipo_principal").agg(
    n           = ("rut_key",     "count"),
    z_baseline  = ("z_baseline",  "mean"),
    z_resultado = ("z_resultado", "mean"),
    delta_z     = ("delta_z",     "mean"),
).round(3)

print("Población pura — agregado por tipo:")
print(agg.to_string())

# ── Figura ────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 6))

xs = ["Baseline\n(pre-formación)", "Resultado\n(post-formación)"]

for tipo in TIPOS:
    if tipo not in agg.index:
        continue
    row = agg.loc[tipo]
    n   = int(row["n"])
    ys  = [row["z_baseline"], row["z_resultado"]]
    ax.plot(xs, ys, marker=MARCAS[tipo], color=COLORES[tipo],
            linewidth=2.5, markersize=11,
            label=f"{tipo} (n={n})")
    ax.annotate(f"{ys[-1]:+.3f}",
                xy=(xs[-1], ys[-1]),
                xytext=(10, 0), textcoords="offset points",
                fontsize=12, color=COLORES[tipo], fontweight="bold")

ax.axhline(0, color="gray", linewidth=1, linestyle="--", alpha=0.6,
           label="Promedio facultad (z=0)")

ax.set_title(
    "Trayectoria Z-score SAT\nbaseline → resultado por tipo de formación\n"
    "(Poblaciones puras: TALLER=154, DIPLOMADO=27, PROYECTO=3)",
    pad=14, fontweight="bold", fontsize=15)
ax.set_ylabel("Z-score promedio\n(posición relativa en facultad)")
ax.set_xlabel("")
ax.legend(loc="upper left")
ax.set_ylim(-0.5, 0.7)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nGuardado: {OUT}")

# ── Bajadas ───────────────────────────────────────────────────────────────────
for tipo in TIPOS:
    if tipo in agg.index:
        r = agg.loc[tipo]
        print(f"  {tipo}: baseline={r['z_baseline']:+.3f} → resultado={r['z_resultado']:+.3f} "
              f"(Δ={r['delta_z']:+.3f}, n={int(r['n'])})")

print("""
BAJADAS PARA EL INFORME
───────────────────────""")
dip = agg.loc["DIPLOMADO"] if "DIPLOMADO" in agg.index else None
tal = agg.loc["TALLER"]    if "TALLER"    in agg.index else None

print(f"""
• Con poblaciones puras, el grupo DIPLOMADO (n=27, solo diplomado sin talleres) \
parte desde un z-score baseline de {dip['z_baseline']:+.3f} y alcanza {dip['z_resultado']:+.3f} \
en el período resultado (Δ={dip['delta_z']:+.3f}), mostrando la trayectoria \
más favorable de los tres grupos.

• El grupo TALLER puro (n=154) parte de {tal['z_baseline']:+.3f} y llega a \
{tal['z_resultado']:+.3f} (Δ={tal['delta_z']:+.3f}). El PROYECTO puro queda con \
n=3, insuficiente para extraer conclusiones; sus resultados deben interpretarse \
con cautela.
""")
