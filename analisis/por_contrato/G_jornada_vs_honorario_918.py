import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os
from sqlalchemy import create_engine, text

BASE    = os.path.dirname(__file__)
OUT1    = os.path.join(BASE, "G_sat_jornada_honorario_918.png")
OUT2    = os.path.join(BASE, "G_recomendacion_jornada_honorario_918.png")
OUT3    = os.path.join(BASE, "G_edd_jornada_honorario_918.png")
engine  = create_engine("postgresql://ucen_user:ucen2026@localhost:5432/ucen")

matplotlib.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})

C_JORNADA   = "#1565C0"
C_HONORARIO = "#E65100"

# ── Cargar NOMINA ─────────────────────────────────────────────────────────────
nom = pd.read_csv(os.path.join(BASE,"..","..","CONSOLIDADO DOCENTES 3-05-2026",
                               "CONSOLIDADO DOCENTES 3-05-2026.xlsx - NOMINA .csv"),
                  dtype=str, encoding="utf-8-sig")
nom.columns = nom.columns.str.strip()
nom["rut_key"] = (nom["RUT"].str.strip()
                  .str.replace(".", "", regex=False)
                  .str.split("-").str[0].str.strip())
nom["tipo_contrato"] = nom["JORNADA/HONORARIO"].str.strip().str.upper()
nom.loc[nom["tipo_contrato"]=="JORNADA","tipo_contrato"] = "JORNADA"

tipo_map = nom.drop_duplicates("rut_key").set_index("rut_key")["tipo_contrato"].to_dict()
ruts = list(nom["rut_key"].unique())

n_jornada   = nom[nom["tipo_contrato"]=="JORNADA"]["rut_key"].nunique()
n_honorario = nom[nom["tipo_contrato"]=="HONORARIO"]["rut_key"].nunique()

PERIODOS = ["2023-01","2023-02","2024-01","2024-02","2025-01","2025-02"]

# ══════════════════════════════════════════════════════════════════════════════
# 1. SAT NOTA por período — Jornada vs Honorario
# ══════════════════════════════════════════════════════════════════════════════
with engine.connect() as conn:
    df_sat = pd.read_sql(text("""
        SELECT ep.rut_docente::text AS rut_key, ep.periodo,
               AVG(er.nota_promedio) AS sat_nota
        FROM consolidados.evaluacion_respuesta er
        JOIN consolidados.evaluacion_periodo ep ON er.evaluacion_id = ep.evaluacion_id
        WHERE er.pregunta_id = 'SAT_NOTA'
          AND ep.rut_docente::text = ANY(:ruts)
        GROUP BY ep.rut_docente, ep.periodo
    """), conn, params={"ruts": ruts})

df_sat["tipo"] = df_sat["rut_key"].map(tipo_map)
df_sat = df_sat[df_sat["tipo"].isin(["JORNADA","HONORARIO"])].copy()

n_sat_j = df_sat[df_sat["tipo"]=="JORNADA"]["rut_key"].nunique()
n_sat_h = df_sat[df_sat["tipo"]=="HONORARIO"]["rut_key"].nunique()

print("=" * 65)
print("  1. SAT NOTA — Jornada vs Honorario")
print("=" * 65)
print(f"  957 docentes NOMINA · {n_sat_j + n_sat_h} con SAT")
print(f"    ├── Jornada   : {n_sat_j} docentes")
print(f"    └── Honorario : {n_sat_h} docentes")
print()

sat_agg = df_sat.groupby(["periodo","tipo"]).agg(
    media=("sat_nota","mean"), n=("rut_key","nunique")).reset_index()

for p in PERIODOS:
    for t in ["JORNADA","HONORARIO"]:
        sub = sat_agg[(sat_agg["periodo"]==p)&(sat_agg["tipo"]==t)]
        if len(sub)>0:
            print(f"  {p} {t:10}: media={sub.iloc[0]['media']:.3f} | n={int(sub.iloc[0]['n'])}")
print("=" * 65)

# Gráfico 1
fig, ax = plt.subplots(figsize=(13, 7))
fig.suptitle(
    "SAT Nota Promedio por Período — Jornada vs Honorario\n"
    f"Universo NOMINA · {n_sat_j} Jornada · {n_sat_h} Honorario",
    fontsize=13, fontweight="bold")

for tipo, color, marker, ls in [("JORNADA",C_JORNADA,"o","-"),
                                  ("HONORARIO",C_HONORARIO,"s","--")]:
    sub = sat_agg[sat_agg["tipo"]==tipo].set_index("periodo")
    ys = [sub["media"].get(p, np.nan) for p in PERIODOS]
    ns = [int(sub["n"].get(p, 0)) for p in PERIODOS]
    ax.plot(range(len(PERIODOS)), ys, marker=marker, color=color,
            linewidth=2.5, markersize=10, linestyle=ls,
            label=f"{tipo.capitalize()} (n={df_sat[df_sat['tipo']==tipo]['rut_key'].nunique()})")
    for i, (y, n) in enumerate(zip(ys, ns)):
        if not np.isnan(y):
            off = 12 if tipo=="JORNADA" else -18
            ax.annotate(f"{y:.2f}\n(n={n})", xy=(i,y),
                        xytext=(0,off), textcoords="offset points",
                        ha="center", fontsize=8.5, color=color, fontweight="bold")

ax.set_xticks(range(len(PERIODOS)))
ax.set_xticklabels(PERIODOS, fontsize=11)
ax.set_ylabel("SAT Nota Promedio (escala 1-7)")
ax.set_xlabel("Período académico")
ax.legend(fontsize=11, loc="lower right")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
plt.tight_layout()
plt.savefig(OUT1, dpi=150, bbox_inches="tight"); plt.close()
print(f"\nGuardado: {OUT1}")

# ══════════════════════════════════════════════════════════════════════════════
# 2. SAT BIN (% Recomendación) por período — Jornada vs Honorario
# ══════════════════════════════════════════════════════════════════════════════
with engine.connect() as conn:
    df_bin = pd.read_sql(text("""
        SELECT ep.rut_docente::text AS rut_key, ep.periodo,
               AVG(er.pct_si) AS pct_recomendacion
        FROM consolidados.evaluacion_respuesta er
        JOIN consolidados.evaluacion_periodo ep ON er.evaluacion_id = ep.evaluacion_id
        WHERE er.pregunta_id = 'SAT_BIN'
          AND ep.rut_docente::text = ANY(:ruts)
        GROUP BY ep.rut_docente, ep.periodo
    """), conn, params={"ruts": ruts})

df_bin["tipo"] = df_bin["rut_key"].map(tipo_map)
df_bin = df_bin[df_bin["tipo"].isin(["JORNADA","HONORARIO"])].copy()

n_bin_j = df_bin[df_bin["tipo"]=="JORNADA"]["rut_key"].nunique()
n_bin_h = df_bin[df_bin["tipo"]=="HONORARIO"]["rut_key"].nunique()

print()
print("=" * 65)
print("  2. % RECOMENDACIÓN — Jornada vs Honorario")
print("=" * 65)
print(f"  {n_bin_j + n_bin_h} docentes con dato")
print(f"    ├── Jornada   : {n_bin_j}")
print(f"    └── Honorario : {n_bin_h}")
print()

bin_agg = df_bin.groupby(["periodo","tipo"]).agg(
    media=("pct_recomendacion","mean"), n=("rut_key","nunique")).reset_index()

for p in PERIODOS:
    for t in ["JORNADA","HONORARIO"]:
        sub = bin_agg[(bin_agg["periodo"]==p)&(bin_agg["tipo"]==t)]
        if len(sub)>0:
            print(f"  {p} {t:10}: media={sub.iloc[0]['media']:.1f}% | n={int(sub.iloc[0]['n'])}")
print("=" * 65)

# Gráfico 2
fig, ax = plt.subplots(figsize=(13, 7))
fig.suptitle(
    "% Recomendación por Período — Jornada vs Honorario\n"
    f"Universo NOMINA · {n_bin_j} Jornada · {n_bin_h} Honorario",
    fontsize=13, fontweight="bold")

for tipo, color, marker, ls in [("JORNADA",C_JORNADA,"o","-"),
                                  ("HONORARIO",C_HONORARIO,"s","--")]:
    sub = bin_agg[bin_agg["tipo"]==tipo].set_index("periodo")
    ys = [sub["media"].get(p, np.nan) for p in PERIODOS]
    ns = [int(sub["n"].get(p, 0)) for p in PERIODOS]
    ax.plot(range(len(PERIODOS)), ys, marker=marker, color=color,
            linewidth=2.5, markersize=10, linestyle=ls,
            label=f"{tipo.capitalize()} (n={df_bin[df_bin['tipo']==tipo]['rut_key'].nunique()})")
    for i, (y, n) in enumerate(zip(ys, ns)):
        if not np.isnan(y):
            off = 12 if tipo=="JORNADA" else -18
            ax.annotate(f"{y:.1f}%\n(n={n})", xy=(i,y),
                        xytext=(0,off), textcoords="offset points",
                        ha="center", fontsize=8.5, color=color, fontweight="bold")

ax.set_xticks(range(len(PERIODOS)))
ax.set_xticklabels(PERIODOS, fontsize=11)
ax.set_ylabel("% de Recomendación")
ax.set_xlabel("Período académico")
ax.legend(fontsize=11, loc="lower right")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
plt.tight_layout()
plt.savefig(OUT2, dpi=150, bbox_inches="tight"); plt.close()
print(f"\nGuardado: {OUT2}")

# ══════════════════════════════════════════════════════════════════════════════
# 3. EDD por año — Jornada vs Honorario
# ══════════════════════════════════════════════════════════════════════════════
edd = pd.read_csv(os.path.join(BASE,"..","..","PROCESADO",
                               "P1_consolidado_con_evaluacion_jefes.csv"),
                  encoding="utf-8-sig", dtype={"rut_key": str})
edd["rut_key"]   = edd["rut_key"].str.strip()
edd["edd_total"] = pd.to_numeric(edd["edd_total"], errors="coerce")
edd = edd.dropna(subset=["edd_total"])
edd["anio"] = edd["anio_evaluacion"].astype(str).str[:4]
edd = edd.drop_duplicates(subset=["rut_key","anio"])

edd["tipo"] = edd["rut_key"].map(tipo_map)
edd = edd[edd["tipo"].isin(["JORNADA","HONORARIO"])].copy()

n_edd_j = edd[edd["tipo"]=="JORNADA"]["rut_key"].nunique()
n_edd_h = edd[edd["tipo"]=="HONORARIO"]["rut_key"].nunique()

ANIOS = ["2022","2023","2024","2025"]

print()
print("=" * 65)
print("  3. EDD — Jornada vs Honorario")
print("=" * 65)
print(f"  {n_edd_j + n_edd_h} docentes con EDD")
print(f"    ├── Jornada   : {n_edd_j}")
print(f"    └── Honorario : {n_edd_h}")
print()

edd_agg = edd.groupby(["anio","tipo"]).agg(
    media=("edd_total","mean"), n=("rut_key","nunique")).reset_index()

for a in ANIOS:
    for t in ["JORNADA","HONORARIO"]:
        sub = edd_agg[(edd_agg["anio"]==a)&(edd_agg["tipo"]==t)]
        if len(sub)>0:
            print(f"  {a} {t:10}: media={sub.iloc[0]['media']:.3f} | n={int(sub.iloc[0]['n'])}")
print("=" * 65)

# Gráfico 3
fig, ax = plt.subplots(figsize=(13, 7))
fig.suptitle(
    "Evolución EDD (Evaluación de Jefes) — Jornada vs Honorario\n"
    f"Universo NOMINA · {n_edd_j} Jornada · {n_edd_h} Honorario",
    fontsize=13, fontweight="bold")

for tipo, color, marker, ls in [("JORNADA",C_JORNADA,"o","-"),
                                  ("HONORARIO",C_HONORARIO,"s","--")]:
    sub = edd_agg[edd_agg["tipo"]==tipo].set_index("anio")
    ys = [sub["media"].get(a, np.nan) for a in ANIOS]
    ns = [int(sub["n"].get(a, 0)) for a in ANIOS]
    ax.plot(range(len(ANIOS)), ys, marker=marker, color=color,
            linewidth=2.5, markersize=10, linestyle=ls,
            label=f"{tipo.capitalize()} (n={edd[edd['tipo']==tipo]['rut_key'].nunique()})")
    for i, (y, n) in enumerate(zip(ys, ns)):
        if not np.isnan(y):
            off = 14 if tipo=="JORNADA" else -20
            ax.annotate(f"{y:.3f}\n(n={n})", xy=(i,y),
                        xytext=(0,off), textcoords="offset points",
                        ha="center", fontsize=9, color=color, fontweight="bold")

ax.set_xticks(range(len(ANIOS)))
ax.set_xticklabels(ANIOS, fontsize=12)
ax.set_ylabel("EDD Total promedio (escala 0-1)")
ax.set_xlabel("Año")
ax.legend(fontsize=11, loc="lower left")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
plt.tight_layout()
plt.savefig(OUT3, dpi=150, bbox_inches="tight"); plt.close()
print(f"\nGuardado: {OUT3}")
