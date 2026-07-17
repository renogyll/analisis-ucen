import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os

BASE = os.path.dirname(__file__)
OUT  = os.path.join(BASE, "G9_puro_edd_918.png")

matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 13, "axes.titlesize": 16, "axes.labelsize": 14,
    "xtick.labelsize": 12, "ytick.labelsize": 12, "legend.fontsize": 12,
})

# ── Cargar ─────────────────────────────────────────────────────────────────────
edd = pd.read_csv(os.path.join(BASE, "..", "..", "PROCESADO",
                               "P1_consolidado_con_evaluacion_jefes.csv"),
                  encoding="utf-8-sig", dtype={"rut_key": str})
doc = pd.read_csv(os.path.join(BASE, "..", "PROCESADO", "docente_918.csv"),
                  encoding="utf-8-sig", dtype={"rut_key": str})
p3  = pd.read_csv(os.path.join(BASE, "..", "PROCESADO", "p3_sat_zscore_918.csv"),
                  encoding="utf-8-sig", dtype={"rut_key": str})

for d in [edd, doc, p3]: d["rut_key"] = d["rut_key"].str.strip()

def tipo_p(r):
    if r["n_diplomado"] > 0: return "DIPLOMADO"
    if r["n_proyecto"]  > 0: return "PROYECTO"
    return "TALLER"
p3["tipo"] = p3.apply(tipo_p, axis=1)

# Poblaciones puras en p3
p3_puro = p3[
    (p3["tipo"] == "TALLER")                                           |
    ((p3["tipo"] == "DIPLOMADO") & (p3["n_taller"] == 0))             |
    ((p3["tipo"] == "PROYECTO")  & (p3["n_taller"] == 0))
].copy()

ruts_taller_puro   = set(p3_puro[p3_puro["tipo"] == "TALLER"   ]["rut_key"])
ruts_diplomado_puro = set(p3_puro[p3_puro["tipo"] == "DIPLOMADO"]["rut_key"])

# Preparar EDD universo 917
en_917 = edd[edd["rut_key"].isin(set(doc["rut_key"])) & edd["edd_total"].notna()].copy()
en_917["edd_total"] = pd.to_numeric(en_917["edd_total"], errors="coerce")
en_917 = en_917.dropna(subset=["edd_total"])
en_917["anio"] = en_917["anio_evaluacion"].astype(str).str[:4]
en_917 = en_917.drop_duplicates(subset=["rut_key", "anio"])

# Asignar grupo
def grupo(rut):
    if rut in ruts_diplomado_puro: return "DIPLOMADO puro"
    if rut in ruts_taller_puro:    return "TALLER puro"
    if rut in set(p3["rut_key"]):  return None   # mixtos → excluir
    return "Sin formación"

en_917["grupo"] = en_917["rut_key"].apply(grupo)
df_viz = en_917[en_917["grupo"].notna()].copy()

ANIOS  = ["2022", "2023", "2024", "2025"]
GRUPOS = ["TALLER puro", "DIPLOMADO puro", "Sin formación"]
ESTILOS = {
    "TALLER puro":    ("#2196F3", "-",  "o"),
    "DIPLOMADO puro": ("#FF9800", "-",  "s"),
    "Sin formación":  ("#607D8B", "--", "^"),
}

agg = df_viz.groupby(["anio", "grupo"])["edd_total"].agg(
    mean="mean", n="count").reset_index()

print("=== EDD por año, grupo puro ===")
print(agg.to_string())
for g in GRUPOS:
    sub = df_viz[df_viz["grupo"] == g]
    print(f"  {g}: {sub['rut_key'].nunique()} docentes únicos")

# ── Figura ─────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 7))

for grupo_name in GRUPOS:
    color, ls, marker = ESTILOS[grupo_name]
    sub = agg[agg["grupo"] == grupo_name].set_index("anio")
    ys  = [sub["mean"].get(a, np.nan) for a in ANIOS]
    ns  = [int(sub["n"].get(a, 0))    for a in ANIOS]
    n_doc = df_viz[df_viz["grupo"] == grupo_name]["rut_key"].nunique()

    ax.plot(range(len(ANIOS)), ys, marker=marker, color=color,
            linewidth=2.5, markersize=9, linestyle=ls,
            label=f"{grupo_name} (n={n_doc} doc.)")

    for i, (y, n) in enumerate(zip(ys, ns)):
        if not np.isnan(y) and n > 0:
            offset = 14 if grupo_name == "TALLER puro" else (-22 if grupo_name == "Sin formación" else 14)
            if grupo_name == "DIPLOMADO puro":
                offset = -22
            ax.annotate(f"{y:.3f}\n(n={n})", xy=(i, y),
                        xytext=(0, offset), textcoords="offset points",
                        ha="center", fontsize=9, color=color, fontweight="bold")

ax.axhline(0.75, color="gray", linewidth=1, linestyle=":", alpha=0.6,
           label="Umbral referencia (0.75)")
ax.set_xticks(range(len(ANIOS)))
ax.set_xticklabels(ANIOS)
ax.set_ylabel("EDD Total promedio (escala 0–1)")
ax.set_xlabel("Año de evaluación")
ax.set_ylim(0.5, 1.05)
ax.set_title(
    "Evolución EDD — Poblaciones Puras: Taller / Diplomado / Sin Formación\n"
    "Universo 917 · Excluidos 13 docentes mixtos (diplomado+taller y proyecto+taller)",
    pad=14, fontweight="bold")
ax.legend(loc="lower left", framealpha=0.9)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nGuardado: {OUT}")

print("""
BAJADAS
• Al separar las poblaciones puras, el grupo DIPLOMADO (solo diplomado, sin talleres)
  muestra la EDD más alta en todos los años, seguido por TALLER puro y finalmente
  el grupo sin formación. Esto es coherente con el análisis SAT: quienes eligen
  diplomados parten desde una posición ya aventajada.

• El grupo TALLER puro mantiene una ventaja consistente sobre el control a lo largo
  de los 4 años, con la brecha ampliándose desde 2024. Los 13 docentes mixtos
  (que hicieron ambas modalidades) quedan excluidos para mantener la pureza
  de la comparación entre iniciativas independientes.
""")
