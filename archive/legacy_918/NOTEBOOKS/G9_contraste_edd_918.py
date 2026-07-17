import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os

BASE = os.path.dirname(__file__)
OUT  = os.path.join(BASE, "G9_contraste_edd_918.png")

matplotlib.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})

edd = pd.read_csv(os.path.join(BASE, "..", "..", "PROCESADO",
                               "P1_consolidado_con_evaluacion_jefes.csv"),
                  encoding="utf-8-sig", dtype={"rut_key": str})
doc = pd.read_csv(os.path.join(BASE, "..", "PROCESADO", "docente_918.csv"),
                  encoding="utf-8-sig", dtype={"rut_key": str})
p3  = pd.read_csv(os.path.join(BASE, "..", "PROCESADO", "p3_sat_zscore_918.csv"),
                  encoding="utf-8-sig", dtype={"rut_key": str})

for d in [edd, doc, p3]: d["rut_key"] = d["rut_key"].str.strip()

# Clasificar tipo y pureza
def tipo_p(r):
    if r["n_diplomado"] > 0: return "DIPLOMADO"
    if r["n_proyecto"]  > 0: return "PROYECTO"
    return "TALLER"
p3["tipo"] = p3.apply(tipo_p, axis=1)

p3["es_puro"] = (
    ((p3["n_taller"]>0)   & (p3["n_diplomado"]==0) & (p3["n_proyecto"]==0)) |
    ((p3["n_diplomado"]>0) & (p3["n_taller"]==0)   & (p3["n_proyecto"]==0)) |
    ((p3["n_proyecto"]>0)  & (p3["n_taller"]==0)   & (p3["n_diplomado"]==0))
)

ruts_formados_all   = set(p3["rut_key"])
ruts_taller_all     = set(p3[p3["tipo"]=="TALLER"]["rut_key"])
ruts_diplomado_all  = set(p3[p3["tipo"]=="DIPLOMADO"]["rut_key"])
ruts_proyecto_all   = set(p3[p3["tipo"]=="PROYECTO"]["rut_key"])
ruts_taller_puro    = set(p3[(p3["tipo"]=="TALLER")   & p3["es_puro"]]["rut_key"])
ruts_diplomado_puro = set(p3[(p3["tipo"]=="DIPLOMADO") & p3["es_puro"]]["rut_key"])
ruts_proyecto_puro  = set(p3[(p3["tipo"]=="PROYECTO")  & p3["es_puro"]]["rut_key"])
ruts_917            = set(doc["rut_key"])

# Preparar EDD
en_917 = edd[edd["rut_key"].isin(ruts_917) & edd["edd_total"].notna()].copy()
en_917["edd_total"] = pd.to_numeric(en_917["edd_total"], errors="coerce")
en_917 = en_917.dropna(subset=["edd_total"])
en_917["anio"] = en_917["anio_evaluacion"].astype(str).str[:4]
en_917 = en_917.drop_duplicates(subset=["rut_key","anio"])

ANIOS = ["2022","2023","2024","2025"]

# ── Función de grupo ──────────────────────────────────────────────────────────
def asignar_grupo_normal(rut):
    if rut in ruts_diplomado_all: return "DIPLOMADO"
    if rut in ruts_proyecto_all:  return "PROYECTO"
    if rut in ruts_taller_all:    return "TALLER"
    return "Sin formación"

def asignar_grupo_puro(rut):
    if rut in ruts_diplomado_puro: return "DIPLOMADO puro"
    if rut in ruts_proyecto_puro:  return "PROYECTO puro"
    if rut in ruts_taller_puro:    return "TALLER puro"
    if rut in ruts_formados_all:   return None  # mixtos → excluir
    return "Sin formación"

en_normal = en_917.copy()
en_normal["grupo"] = en_normal["rut_key"].apply(asignar_grupo_normal)

en_puro = en_917.copy()
en_puro["grupo"] = en_puro["rut_key"].apply(asignar_grupo_puro)
en_puro = en_puro[en_puro["grupo"].notna()]

# ── Cascada ───────────────────────────────────────────────────────────────────
print("=" * 65)
print("  G9 CONTRASTE — EDD: Población Normal vs Pura")
print("=" * 65)
for label, df_viz, grupos in [
    ("Normal", en_normal, ["TALLER","DIPLOMADO","PROYECTO","Sin formación"]),
    ("Puro",   en_puro,   ["TALLER puro","DIPLOMADO puro","PROYECTO puro","Sin formación"])]:
    print(f"\n  {label}:")
    for g in grupos:
        sub = df_viz[df_viz["grupo"]==g]
        n_doc = sub["rut_key"].nunique()
        media = sub["edd_total"].mean()
        print(f"    {g:20}: {n_doc:3d} docentes únicos | EDD media global={media:.3f}")
        for a in ANIOS:
            s = sub[sub["anio"]==a]
            if len(s)>0:
                print(f"      {a}: n={len(s):3d} | media={s['edd_total'].mean():.3f}")
print("=" * 65)

# ── Figura ────────────────────────────────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7), sharey=True)
fig.suptitle(
    "Evolución EDD — Población Normal vs Población Pura\n"
    "Universo 917 · Evaluación de Desempeño Docente 2022–2025",
    fontsize=13, fontweight="bold")

def plot_edd(ax, df_viz, grupos, estilos, titulo):
    for grupo_name in grupos:
        color, ls, marker = estilos[grupo_name]
        sub = df_viz[df_viz["grupo"]==grupo_name]
        agg = sub.groupby("anio")["edd_total"].agg(mean="mean", n="count").reset_index()
        agg = agg.set_index("anio")
        ys = [agg["mean"].get(a, np.nan) for a in ANIOS]
        ns = [int(agg["n"].get(a, 0)) for a in ANIOS]
        n_doc = sub["rut_key"].nunique()

        ax.plot(range(len(ANIOS)), ys, marker=marker, color=color,
                linewidth=2.5, markersize=9, linestyle=ls,
                label=f"{grupo_name} (n={n_doc})")

        offsets = {"TALLER": 16, "TALLER puro": 16,
                   "DIPLOMADO": -22, "DIPLOMADO puro": -22,
                   "PROYECTO": 20, "PROYECTO puro": 20,
                   "Sin formación": -22, "Formados": 16}
        off = offsets.get(grupo_name, 14)
        for i, (y, n) in enumerate(zip(ys, ns)):
            if not np.isnan(y) and n > 0:
                ax.annotate(f"{y:.3f}\n(n={n})", xy=(i, y),
                            xytext=(0, off), textcoords="offset points",
                            ha="center", fontsize=7.5, color=color, fontweight="bold")

    ax.set_xticks(range(len(ANIOS)))
    ax.set_xticklabels(ANIOS, fontsize=11)
    ax.set_ylabel("EDD Total promedio (escala 0–1)")
    ax.set_xlabel("Año")
    ax.set_ylim(0.55, 1.02)
    ax.set_title(titulo, pad=12, fontsize=12, fontweight="bold")
    ax.legend(fontsize=9.5, loc="lower left")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

ESTILOS_NORMAL = {
    "TALLER":         ("#2196F3", "-",  "o"),
    "DIPLOMADO":      ("#FF9800", "-",  "s"),
    "PROYECTO":       ("#E65100", "-",  "D"),
    "Sin formación":  ("#607D8B", "--", "^"),
}
ESTILOS_PURO = {
    "TALLER puro":    ("#2196F3", "-",  "o"),
    "DIPLOMADO puro": ("#FF9800", "-",  "s"),
    "PROYECTO puro":  ("#E65100", "-",  "D"),
    "Sin formación":  ("#607D8B", "--", "^"),
}

n_mixto_excl = en_917[en_917["rut_key"].isin(
    ruts_formados_all - ruts_taller_puro - ruts_diplomado_puro - ruts_proyecto_puro
)]["rut_key"].nunique()

plot_edd(ax1, en_normal,
         ["TALLER","DIPLOMADO","PROYECTO","Sin formación"],
         ESTILOS_NORMAL,
         f"Población Normal\n(incluye mixtos en cada tipo)")
plot_edd(ax2, en_puro,
         ["TALLER puro","DIPLOMADO puro","PROYECTO puro","Sin formación"],
         ESTILOS_PURO,
         f"Población Pura\n(excluye {n_mixto_excl} mixtos)")

plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nGuardado: {OUT}")
