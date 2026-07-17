import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import os

engine  = create_engine("postgresql://ucen_user:ucen2026@localhost:5432/ucen")
BASE    = os.path.dirname(__file__)

# ── Cargar universo 917 y aptos P3 ───────────────────────────────────────────
doc = pd.read_csv(os.path.join(BASE, "docente_918.csv"),
                  encoding="utf-8-sig", dtype={"rut_key": str})
doc["rut_key"] = doc["rut_key"].str.strip()

p3 = pd.read_csv(os.path.join(BASE, "p3_918.csv"),
                 encoding="utf-8-sig", dtype={"rut_key": str})
p3["rut_key"] = p3["rut_key"].str.strip()
aptos = p3[p3["apto_p3"] == True].copy()
print(f"Aptos P3: {len(aptos)} filas | {aptos['rut_key'].nunique()} RUTs únicos")

# ── pct_si ponderado por docente × período (CM-1 + CM-2) ─────────────────────
with engine.connect() as conn:
    bin_raw = pd.read_sql(text("""
        SELECT e.rut_docente   AS rut_key,
               e.periodo,
               e.n_alumnos_evaluaron,
               r.pct_si
        FROM consolidados.evaluacion_periodo e
        JOIN consolidados.evaluacion_respuesta r ON r.evaluacion_id = e.evaluacion_id
        WHERE r.pregunta_id = 'SAT_BIN'
          AND e.cobertura_pct >= 40
          AND r.pct_si IS NOT NULL
    """), conn)

bin_raw["rut_key"] = bin_raw["rut_key"].astype(str).str.strip()
bin_raw["peso_bin"] = bin_raw["pct_si"] * bin_raw["n_alumnos_evaluaron"]
bin_per = (bin_raw.groupby(["rut_key", "periodo"])
           .agg(bin_pond=("peso_bin", "sum"),
                n_alumnos=("n_alumnos_evaluaron", "sum"))
           .reset_index())
bin_per["bin"] = bin_per["bin_pond"] / bin_per["n_alumnos"]
print(f"pct_si ponderado: {len(bin_per)} filas (docente×período)")
print(f"Períodos disponibles: {sorted(bin_per['periodo'].unique())}")

# Pivot para lookups
bin_pivot = bin_per.pivot(index="rut_key", columns="periodo", values="bin")

def get_bin_periodo(rut, periodo_str, tipo):
    if rut not in bin_pivot.index:
        return np.nan
    if tipo == "TALLER":
        return bin_pivot.loc[rut, periodo_str] if periodo_str in bin_pivot.columns else np.nan
    else:
        year = str(int(float(periodo_str)))
        vals = [bin_pivot.loc[rut, f"{year}-{s}"]
                for s in ["01","02"] if f"{year}-{s}" in bin_pivot.columns
                and pd.notna(bin_pivot.loc[rut, f"{year}-{s}"])]
        return float(np.mean(vals)) if vals else np.nan

# Calcular pct_si crudo baseline y resultado
aptos["bin_baseline"]  = aptos.apply(
    lambda r: get_bin_periodo(r["rut_key"], str(r["periodo_baseline"]),  r["tipo_formacion"]), axis=1)
aptos["bin_resultado"] = aptos.apply(
    lambda r: get_bin_periodo(r["rut_key"], str(r["periodo_resultado"]), r["tipo_formacion"]), axis=1)
aptos["delta_bin"] = (aptos["bin_resultado"] - aptos["bin_baseline"]).round(4)

print(f"\npct_si calculado:")
print(f"  Con bin_baseline:  {aptos['bin_baseline'].notna().sum()}")
print(f"  Con bin_resultado: {aptos['bin_resultado'].notna().sum()}")
print(f"  Con ambos:         {(aptos['bin_baseline'].notna() & aptos['bin_resultado'].notna()).sum()}")

# ── Población de referencia para z-score ─────────────────────────────────────
ruts_917 = set(doc["rut_key"])
bin_pop = bin_per[bin_per["rut_key"].isin(ruts_917)].merge(
    doc[["rut_key", "unidad_facultad"]], on="rut_key", how="inner"
)
n_por_unidad = bin_pop.groupby("unidad_facultad")["rut_key"].nunique()
pequenas = n_por_unidad[n_por_unidad < 30].index.tolist()
bin_pop["uf_ref"] = bin_pop["unidad_facultad"].apply(
    lambda x: "Otras" if x in pequenas or pd.isna(x) else x
)

stats_per = (bin_pop.groupby(["uf_ref", "periodo"])["bin"]
             .agg(mu="mean", sigma="std").reset_index())
stats_per["sigma"] = stats_per["sigma"].fillna(1.0)
sigma_global = bin_pop["bin"].std()
mu_global    = bin_pop["bin"].mean()
stats_per.loc[stats_per["sigma"] < 0.01, "sigma"] = sigma_global

bin_pop["anio"] = bin_pop["periodo"].str[:4]
stats_anio = (bin_pop.groupby(["uf_ref", "anio"])["bin"]
              .agg(mu="mean", sigma="std").reset_index())
stats_anio["sigma"] = stats_anio["sigma"].fillna(1.0)
stats_anio.loc[stats_anio["sigma"] < 0.01, "sigma"] = sigma_global

def get_z(bin_val, rut, periodo_str, tipo, uf):
    if pd.isna(bin_val):
        return np.nan, np.nan, np.nan
    uf_ref = "Otras" if uf in pequenas or pd.isna(uf) else uf
    if tipo == "TALLER":
        row = stats_per[(stats_per["uf_ref"] == uf_ref) & (stats_per["periodo"] == periodo_str)]
    else:
        year = str(int(float(periodo_str)))
        row = stats_anio[(stats_anio["uf_ref"] == uf_ref) & (stats_anio["anio"] == year)]
    if len(row) == 0:
        mu, sigma = mu_global, sigma_global
    else:
        mu, sigma = row.iloc[0]["mu"], row.iloc[0]["sigma"]
    return round((bin_val - mu) / sigma, 4), round(mu, 3), round(sigma, 3)

z_data = aptos.apply(lambda r: pd.Series(
    get_z(r["bin_baseline"],  r["rut_key"], str(r["periodo_baseline"]),  r["tipo_formacion"], r["unidad_facultad"])
), axis=1)
aptos[["z_bin_baseline",  "z_bin_base_mu",  "z_bin_base_sigma"]]  = z_data

z_data2 = aptos.apply(lambda r: pd.Series(
    get_z(r["bin_resultado"], r["rut_key"], str(r["periodo_resultado"]), r["tipo_formacion"], r["unidad_facultad"])
), axis=1)
aptos[["z_bin_resultado", "z_bin_res_mu",   "z_bin_res_sigma"]]   = z_data2

aptos["delta_z_bin"]  = (aptos["z_bin_resultado"] - aptos["z_bin_baseline"]).round(4)
aptos["mejoro_bin"]   = aptos["delta_bin"]   > 0
aptos["mejoro_z_bin"] = aptos["delta_z_bin"] > 0

# ── Agregar por docente ───────────────────────────────────────────────────────
PERFIL_COLS = ["rut_key","nombre","sexo","jerarquia","jerarquia_dot",
               "tipo_contrato","unidad_facultad","nivel_formacion",
               "antiguedad_anios","tramo_antiguedad","edad_anios","tramo_edad",
               "origen","tiene_perfil_completo"]

form_meta = aptos.groupby("rut_key").agg(
    n_instancias    = ("tipo_formacion", "count"),
    tipos_formacion = ("tipo_formacion", lambda x: " | ".join(sorted(x.unique()))),
    n_taller        = ("tipo_formacion", lambda x: (x == "TALLER").sum()),
    n_diplomado     = ("tipo_formacion", lambda x: (x == "DIPLOMADO").sum()),
    n_proyecto      = ("tipo_formacion", lambda x: (x == "PROYECTO").sum()),
).reset_index()

NUM_COLS = ["bin_baseline","bin_resultado","delta_bin","z_bin_baseline","z_bin_resultado","delta_z_bin"]
num_agg  = aptos.groupby("rut_key")[NUM_COLS].mean().round(4).reset_index()

bool_agg = aptos.groupby("rut_key").agg(
    mejoro_bin   = ("mejoro_bin",   lambda x: (x.sum() / len(x)) >= 0.5),
    mejoro_z_bin = ("mejoro_z_bin", lambda x: (x.sum() / len(x)) >= 0.5),
).reset_index()

perfil = aptos[PERFIL_COLS].drop_duplicates("rut_key")
out = (perfil.merge(form_meta, on="rut_key")
             .merge(num_agg,   on="rut_key")
             .merge(bool_agg,  on="rut_key"))

# Derivar tipo_principal
def tipo_principal(row):
    if row["n_diplomado"] > 0: return "DIPLOMADO"
    if row["n_proyecto"]  > 0: return "PROYECTO"
    return "TALLER"
out["tipo_principal"] = out.apply(tipo_principal, axis=1)

# ── Control vs tratamiento por período (para G6.2 y G11.2) ───────────────────
with engine.connect() as conn:
    pf = pd.read_sql(text("SELECT DISTINCT rut_key FROM consolidados.participacion_formacion"), conn)
pf["rut_key"] = pf["rut_key"].astype(str).str.strip()
ruts_con_formacion = set(pf["rut_key"])
ruts_control   = ruts_917 - ruts_con_formacion
ruts_treatment = set(aptos["rut_key"].unique())

# Calcular z-score de pct_si para toda la población 917
bin_all = bin_per[bin_per["rut_key"].isin(ruts_917)].copy()
bin_all = bin_all.merge(doc[["rut_key","unidad_facultad"]], on="rut_key", how="left")
bin_all["uf_ref"] = bin_all["unidad_facultad"].apply(
    lambda x: "Otras" if x in pequenas or pd.isna(x) else x
)
bin_all = bin_all.merge(stats_per.rename(columns={"mu":"ref_mu","sigma":"ref_sigma"}),
                         on=["uf_ref","periodo"], how="left")
bin_all["ref_mu"]    = bin_all["ref_mu"].fillna(mu_global)
bin_all["ref_sigma"] = bin_all["ref_sigma"].fillna(sigma_global)
bin_all["z"] = ((bin_all["bin"] - bin_all["ref_mu"]) / bin_all["ref_sigma"]).round(4)

PERIODOS = ["2023-01","2023-02","2024-01","2024-02","2025-01","2025-02"]
rows_ctrl = []
for p in PERIODOS:
    sub_p  = bin_all[bin_all["periodo"] == p]
    trat_p = sub_p[sub_p["rut_key"].isin(ruts_treatment)]
    ctrl_p = sub_p[sub_p["rut_key"].isin(ruts_control)]
    rows_ctrl.append({
        "periodo": p,
        "z_trat": round(trat_p["z"].mean(), 4),
        "n_trat": len(trat_p),
        "z_ctrl": round(ctrl_p["z"].mean(), 4),
        "n_ctrl": len(ctrl_p),
    })
ctrl_trat_df = pd.DataFrame(rows_ctrl)
ctrl_trat_df.to_csv(os.path.join(BASE, "control_vs_trat_bin_918.csv"),
                    encoding="utf-8-sig", index=False)

# Guardar también el z individual completo para t-tests
bin_all.to_csv(os.path.join(BASE, "bin_zscore_all_918.csv"),
               encoding="utf-8-sig", index=False)

# ── Resumen ───────────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"PASO — Z-SCORES pct_si (SAT_BIN) UNIVERSO 917")
print(f"{'='*60}")
print(f"RUTs únicos en output: {len(out)}")
print(f"Delta pct_si crudo (media): {out['delta_bin'].mean():+.2f}%")
print(f"Delta Z bin (media):        {out['delta_z_bin'].mean():+.3f}")
print(f"\nPor tipo de formación:")
for tipo in ["TALLER", "DIPLOMADO", "PROYECTO"]:
    sub = out[out["tipo_principal"] == tipo]
    if len(sub) == 0: continue
    print(f"  {tipo:<15} n={len(sub):>3}  Δbin={sub['delta_bin'].mean():+.2f}%  Δz={sub['delta_z_bin'].mean():+.3f}  %mejora={sub['mejoro_z_bin'].mean()*100:.0f}%")

print(f"\nControl vs tratamiento pct_si z-score:")
print(ctrl_trat_df.to_string(index=False))

out.to_csv(os.path.join(BASE, "p3_bin_zscore_918.csv"), encoding="utf-8-sig", index=False)
print(f"\nGuardado: p3_bin_zscore_918.csv")
print(f"Guardado: control_vs_trat_bin_918.csv")
print(f"Guardado: bin_zscore_all_918.csv")
print(f"Columnas: {list(out.columns)}")
