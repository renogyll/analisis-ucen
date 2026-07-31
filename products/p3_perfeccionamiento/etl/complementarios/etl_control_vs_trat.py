"""
ETL: Grupo Control vs Tratamiento — SAT z-score por período
Control = universo_base (1,144) MINUS formados (419) ≈ 725 docentes.
Tratamiento = aptos P3 (210).

SALIDAS:
  data/cascade/complementarios/control_918.csv      — SAT+z por docente×período (grupo control)
  data/cascade/complementarios/control_vs_trat_918.csv — promedios z por período (ambos grupos)
"""
import sys; sys.stdout.reconfigure(encoding="utf-8")
import os
from pathlib import Path
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).parents[2]))
from config import CASCADE

DB_URL  = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"
engine  = create_engine(DB_URL)
COMP    = os.path.join(CASCADE, "complementarios")
PERIODOS = ["2023-01","2023-02","2024-01","2024-02","2025-01","2025-02"]

os.makedirs(COMP, exist_ok=True)

# ── Cargar fuentes ────────────────────────────────────────────────────────────
with engine.connect() as conn:
    doc = pd.read_sql(text("SELECT rut_key, origen, unidad_facultad FROM analisis.universo_base"), conn)
    form = pd.read_sql(text("SELECT DISTINCT rut_key FROM analisis.universo_formados_p3"), conn)
    aptos = pd.read_sql(text("SELECT DISTINCT rut_key FROM analisis.universo_aptos_p3"), conn)
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

doc["rut_key"]    = doc["rut_key"].astype(str).str.strip()
form["rut_key"]   = form["rut_key"].astype(str).str.strip()
aptos["rut_key"]  = aptos["rut_key"].astype(str).str.strip()
sat_raw["rut_key"] = sat_raw["rut_key"].astype(str).str.strip()

ruts_base   = set(doc["rut_key"])
ruts_form   = set(form["rut_key"])
ruts_aptos  = set(aptos["rut_key"])
ruts_ctrl   = ruts_base - ruts_form

print(f"Universo base:        {len(ruts_base)}")
print(f"Formados:             {len(ruts_form)}")
print(f"Control (sin form.):  {len(ruts_ctrl)}")
print(f"Tratamiento (aptos):  {len(ruts_aptos)}")

# ── SAT ponderado por docente × período (CM-2) ───────────────────────────────
sat_raw["peso_nota"] = sat_raw["nota_promedio"] * sat_raw["n_alumnos_evaluaron"]
sat_per = (sat_raw.groupby(["rut_key","periodo"])
           .agg(sat_pond=("peso_nota","sum"), n_alumnos=("n_alumnos_evaluaron","sum"))
           .reset_index())
sat_per["sat"] = sat_per["sat_pond"] / sat_per["n_alumnos"]

# ── Referencia: universo_base completo (misma lógica que etl_aptos_p3.py) ────
sat_pop = sat_per[sat_per["rut_key"].isin(ruts_base)].merge(
    doc[["rut_key","unidad_facultad"]], on="rut_key", how="inner"
)
n_por_uf = sat_pop.groupby("unidad_facultad")["rut_key"].nunique()
pequenas = n_por_uf[n_por_uf < 30].index.tolist()
sat_pop["uf_ref"] = sat_pop["unidad_facultad"].apply(
    lambda x: "Otras" if x in pequenas or pd.isna(x) else x
)
stats_per = (sat_pop.groupby(["uf_ref","periodo"])["sat"]
             .agg(mu="mean", sigma="std").reset_index())
sigma_global = sat_pop["sat"].std()
mu_global    = sat_pop["sat"].mean()
stats_per["sigma"] = stats_per["sigma"].fillna(sigma_global)
stats_per.loc[stats_per["sigma"] < 0.01, "sigma"] = sigma_global

def add_z(df, uf_col):
    df = df.copy()
    df["uf_ref"] = df[uf_col].apply(lambda x: "Otras" if x in pequenas or pd.isna(x) else x)
    df = df.merge(stats_per.rename(columns={"mu":"ref_mu","sigma":"ref_sigma"}),
                  on=["uf_ref","periodo"], how="left")
    df["ref_mu"]    = df["ref_mu"].fillna(mu_global)
    df["ref_sigma"] = df["ref_sigma"].fillna(sigma_global)
    df["z"] = ((df["sat"] - df["ref_mu"]) / df["ref_sigma"]).round(4)
    return df

# ── Grupo control: SAT + z por docente × período ─────────────────────────────
sat_ctrl = sat_per[sat_per["rut_key"].isin(ruts_ctrl)].merge(
    doc[["rut_key","unidad_facultad","origen"]], on="rut_key", how="left"
)
sat_ctrl = add_z(sat_ctrl, "unidad_facultad")
sat_ctrl_out = sat_ctrl[["rut_key","periodo","sat","z","unidad_facultad","origen"]].copy()
print(f"\nControl con ≥1 SAT: {sat_ctrl_out['rut_key'].nunique()} docentes "
      f"({sat_ctrl_out['rut_key'].nunique()/len(ruts_ctrl)*100:.0f}%)")

# ── Grupo tratamiento: SAT + z por docente × período ─────────────────────────
sat_trat = sat_per[sat_per["rut_key"].isin(ruts_aptos)].merge(
    doc[["rut_key","unidad_facultad","origen"]], on="rut_key", how="left"
)
sat_trat = add_z(sat_trat, "unidad_facultad")

# ── Tabla resumen: z promedio por período ─────────────────────────────────────
resumen = []
print(f"\n{'Período':<10} {'Z_trat':>8} {'N_trat':>7} {'Z_ctrl':>8} {'N_ctrl':>7}")
print("-" * 46)
for p in PERIODOS:
    st = sat_trat[sat_trat["periodo"] == p]
    sc = sat_ctrl[sat_ctrl["periodo"] == p]
    zt = round(st["z"].mean(), 4) if len(st) > 0 else np.nan
    zc = round(sc["z"].mean(), 4) if len(sc) > 0 else np.nan
    nt = st["rut_key"].nunique()
    nc = sc["rut_key"].nunique()
    print(f"{p:<10} {zt:>+8.3f} {nt:>7} {zc:>+8.3f} {nc:>7}")
    resumen.append({"periodo": p, "z_trat": zt, "n_trat": nt, "z_ctrl": zc, "n_ctrl": nc})

resumen_df = pd.DataFrame(resumen)

# ── Guardar ───────────────────────────────────────────────────────────────────
sat_ctrl_out.to_csv(os.path.join(COMP, "control_918.csv"), index=False, encoding="utf-8-sig")
resumen_df.to_csv(os.path.join(COMP, "control_vs_trat_918.csv"), index=False, encoding="utf-8-sig")
print(f"\nGuardado: control_918.csv ({len(sat_ctrl_out)} filas)")
print(f"Guardado: control_vs_trat_918.csv ({len(resumen_df)} filas)")
