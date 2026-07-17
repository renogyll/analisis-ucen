import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import os

engine  = create_engine("postgresql://ucen_user:ucen2026@localhost:5432/ucen")
BASE    = os.path.dirname(__file__)
OUT_CSV = os.path.join(BASE, "control_918.csv")

PERIODOS = ["2023-01","2023-02","2024-01","2024-02","2025-01","2025-02"]

# ── Universo 917 ──────────────────────────────────────────────────────────────
doc = pd.read_csv(os.path.join(BASE, "docente_918.csv"),
                  encoding="utf-8-sig", dtype={"rut_key": str})
doc["rut_key"] = doc["rut_key"].str.strip()
ruts_917 = set(doc["rut_key"])

# ── Docentes con formación registrada ────────────────────────────────────────
with engine.connect() as conn:
    pf = pd.read_sql(text(
        "SELECT DISTINCT rut_key FROM consolidados.participacion_formacion"
    ), conn)
pf["rut_key"] = pf["rut_key"].astype(str).str.strip()
ruts_con_formacion = set(pf["rut_key"])

# Control = en 917 y SIN formación
ruts_control = ruts_917 - ruts_con_formacion
print(f"Universo 917:            {len(ruts_917)}")
print(f"Con formación:           {len(ruts_con_formacion & ruts_917)}")
print(f"Sin formación (control): {len(ruts_control)}")

# ── SAT ponderado por docente × período (CM-1 + CM-2) ────────────────────────
with engine.connect() as conn:
    sat_raw = pd.read_sql(text("""
        SELECT e.rut_docente AS rut_key,
               e.periodo,
               e.n_alumnos_evaluaron,
               r.nota_promedio
        FROM consolidados.evaluacion_periodo e
        JOIN consolidados.evaluacion_respuesta r ON r.evaluacion_id = e.evaluacion_id
        WHERE r.pregunta_id = 'SAT_NOTA'
          AND e.cobertura_pct >= 40
          AND r.nota_promedio IS NOT NULL
    """), conn)

sat_raw["rut_key"] = sat_raw["rut_key"].astype(str).str.strip()
sat_raw["peso_nota"] = sat_raw["nota_promedio"] * sat_raw["n_alumnos_evaluaron"]
sat_per = (sat_raw.groupby(["rut_key","periodo"])
           .agg(sat_pond=("peso_nota","sum"), n_alumnos=("n_alumnos_evaluaron","sum"))
           .reset_index())
sat_per["sat"] = sat_per["sat_pond"] / sat_per["n_alumnos"]

# Filtrar control y merger con perfil
sat_ctrl = sat_per[sat_per["rut_key"].isin(ruts_control)].copy()
sat_ctrl = sat_ctrl.merge(doc[["rut_key","unidad_facultad","origen","tiene_perfil_completo"]],
                           on="rut_key", how="left")

ruts_ctrl_con_sat = set(sat_ctrl["rut_key"].unique())
print(f"Control con ≥1 SAT:      {len(ruts_ctrl_con_sat)} ({len(ruts_ctrl_con_sat)/len(ruts_control)*100:.0f}%)")

# ── Estadísticas de referencia (mismas que para tratamiento) ─────────────────
sat_pop = sat_per[sat_per["rut_key"].isin(ruts_917)].merge(
    doc[["rut_key","unidad_facultad"]], on="rut_key", how="inner"
)
n_por_uf  = sat_pop.groupby("unidad_facultad")["rut_key"].nunique()
pequenas  = n_por_uf[n_por_uf < 30].index.tolist()
sat_pop["uf_ref"] = sat_pop["unidad_facultad"].apply(
    lambda x: "Otras" if x in pequenas or pd.isna(x) else x
)
stats_per = (sat_pop.groupby(["uf_ref","periodo"])["sat"]
             .agg(mu="mean", sigma="std").reset_index())
stats_per["sigma"] = stats_per["sigma"].fillna(1.0)
sigma_global = sat_pop["sat"].std()
mu_global    = sat_pop["sat"].mean()
stats_per.loc[stats_per["sigma"] < 0.01, "sigma"] = sigma_global

# ── Z-score del grupo control ─────────────────────────────────────────────────
sat_ctrl["uf_ref"] = sat_ctrl["unidad_facultad"].apply(
    lambda x: "Otras" if x in pequenas or pd.isna(x) else x
)
sat_ctrl = sat_ctrl.merge(
    stats_per.rename(columns={"mu":"ref_mu","sigma":"ref_sigma"}),
    on=["uf_ref","periodo"], how="left"
)
sat_ctrl["ref_mu"]    = sat_ctrl["ref_mu"].fillna(mu_global)
sat_ctrl["ref_sigma"] = sat_ctrl["ref_sigma"].fillna(sigma_global)
sat_ctrl["z"] = ((sat_ctrl["sat"] - sat_ctrl["ref_mu"]) / sat_ctrl["ref_sigma"]).round(4)

# ── Resumen ───────────────────────────────────────────────────────────────────
print(f"\n{'='*55}")
print(f"GRUPO CONTROL — UNIVERSO 917")
print(f"{'='*55}")
print(f"\n1. COMPOSICIÓN")
for origen in ["ambos","nomina","dotacion"]:
    n = doc[doc["rut_key"].isin(ruts_control) & (doc["origen"]==origen)].shape[0]
    print(f"   {origen:<12}: {n}")

print(f"\n2. COBERTURA SAT POR PERÍODO")
print(f"   {'Período':<10} {'N docentes':>10} {'Z prom':>8}")
for p in PERIODOS:
    sub = sat_ctrl[sat_ctrl["periodo"]==p]
    n   = sub["rut_key"].nunique()
    z   = sub["z"].mean()
    print(f"   {p:<10} {n:>10} {z:>+8.3f}")

print(f"\n3. Z-SCORE PROMEDIO POR PERÍODO (control vs tratamiento)")
# Cargar tratamiento para comparar
p3_zscore = pd.read_csv(os.path.join(BASE, "p3_sat_zscore_918.csv"),
                         encoding="utf-8-sig", dtype={"rut_key": str})
pivot_trat = pd.read_csv(os.path.join(BASE, "p3_sat_zscore_918.csv"),
                          encoding="utf-8-sig", dtype={"rut_key": str})

# z promedio por período del grupo tratamiento (desde p3_918.csv aptos)
p3_all = pd.read_csv(os.path.join(BASE, "p3_918.csv"),
                      encoding="utf-8-sig", dtype={"rut_key": str})
aptos = p3_all[p3_all["apto_p3"]==True][["rut_key"]].drop_duplicates()
sat_trat = sat_per[sat_per["rut_key"].isin(set(aptos["rut_key"].str.strip()))].copy()
sat_trat = sat_trat.merge(doc[["rut_key","unidad_facultad"]], on="rut_key", how="left")
sat_trat["uf_ref"] = sat_trat["unidad_facultad"].apply(
    lambda x: "Otras" if x in pequenas or pd.isna(x) else x
)
sat_trat = sat_trat.merge(
    stats_per.rename(columns={"mu":"ref_mu","sigma":"ref_sigma"}),
    on=["uf_ref","periodo"], how="left"
)
sat_trat["ref_mu"]    = sat_trat["ref_mu"].fillna(mu_global)
sat_trat["ref_sigma"] = sat_trat["ref_sigma"].fillna(sigma_global)
sat_trat["z"] = ((sat_trat["sat"] - sat_trat["ref_mu"]) / sat_trat["ref_sigma"]).round(4)

print(f"\n   {'Período':<10} {'Z_trat':>8} {'N_trat':>7} {'Z_ctrl':>8} {'N_ctrl':>7}")
print(f"   {'-'*46}")
resumen = []
for p in PERIODOS:
    st = sat_trat[sat_trat["periodo"]==p]
    sc = sat_ctrl[sat_ctrl["periodo"]==p]
    zt = st["z"].mean() if len(st) > 0 else np.nan
    zc = sc["z"].mean() if len(sc) > 0 else np.nan
    nt = st["rut_key"].nunique()
    nc = sc["rut_key"].nunique()
    print(f"   {p:<10} {zt:>+8.3f} {nt:>7} {zc:>+8.3f} {nc:>7}")
    resumen.append({"periodo":p,"z_trat":round(zt,4),"n_trat":nt,"z_ctrl":round(zc,4),"n_ctrl":nc})

resumen_df = pd.DataFrame(resumen)

# ── Guardar ───────────────────────────────────────────────────────────────────
sat_ctrl_out = sat_ctrl[["rut_key","periodo","sat","z","unidad_facultad","origen","tiene_perfil_completo"]].copy()
sat_ctrl_out.to_csv(OUT_CSV, encoding="utf-8-sig", index=False)
resumen_df.to_csv(os.path.join(BASE, "control_vs_trat_918.csv"), encoding="utf-8-sig", index=False)
print(f"\nGuardado: {OUT_CSV}")
print(f"Guardado: control_vs_trat_918.csv")
