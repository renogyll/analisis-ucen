import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import os

engine  = create_engine("postgresql://ucen_user:ucen2026@localhost:5432/ucen")
BASE    = os.path.dirname(__file__)
OUT_CSV = os.path.join(BASE, "p3_sat_zscore_918.csv")

# ── Cargar universo 917 y aptos P3 ───────────────────────────────────────────
doc = pd.read_csv(os.path.join(BASE, "docente_918.csv"),
                  encoding="utf-8-sig", dtype={"rut_key": str})
doc["rut_key"] = doc["rut_key"].str.strip()

p3 = pd.read_csv(os.path.join(BASE, "p3_918.csv"),
                 encoding="utf-8-sig", dtype={"rut_key": str})
p3["rut_key"] = p3["rut_key"].str.strip()
aptos = p3[p3["apto_p3"] == True].copy()
print(f"Aptos P3: {len(aptos)} filas | {aptos['rut_key'].nunique()} RUTs únicos")

# ── SAT ponderado por docente × período (CM-1+CM-2) ──────────────────────────
# CM-1: cobertura_pct >= 40
# CM-2: SUM(nota * n_alumnos) / SUM(n_alumnos)
with engine.connect() as conn:
    sat_raw = pd.read_sql(text("""
        SELECT e.rut_docente   AS rut_key,
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

# SAT ponderado por (docente, periodo)
sat_raw["peso_nota"] = sat_raw["nota_promedio"] * sat_raw["n_alumnos_evaluaron"]
sat_per = (sat_raw.groupby(["rut_key", "periodo"])
           .agg(sat_pond=("peso_nota", "sum"),
                n_alumnos=("n_alumnos_evaluaron", "sum"))
           .reset_index())
sat_per["sat"] = sat_per["sat_pond"] / sat_per["n_alumnos"]
print(f"SAT ponderado: {len(sat_per)} filas (docente×período)")

# Pivot rápido para lookups
sat_pivot = sat_per.pivot(index="rut_key", columns="periodo", values="sat")
print(f"Períodos disponibles: {list(sat_pivot.columns)}")

# ── Función de lookup SAT ─────────────────────────────────────────────────────
PERIODOS_ALL = list(sat_pivot.columns)

def get_sat_periodo(rut, periodo_str, tipo):
    """
    TALLER: periodo_str = "2023-02" → lookup exacto
    DIPLOMADO/PROYECTO: periodo_str = "2023" → promedio de los semestres disponibles del año
    """
    if rut not in sat_pivot.index:
        return np.nan
    if tipo == "TALLER":
        if periodo_str in sat_pivot.columns:
            return sat_pivot.loc[rut, periodo_str]
        return np.nan
    else:
        year = str(int(float(periodo_str)))
        p1 = f"{year}-01"
        p2 = f"{year}-02"
        vals = []
        for p in [p1, p2]:
            if p in sat_pivot.columns:
                v = sat_pivot.loc[rut, p]
                if pd.notna(v):
                    vals.append(v)
        return float(np.mean(vals)) if vals else np.nan

# ── Calcular SAT crudo baseline y resultado por apto ─────────────────────────
aptos["sat_baseline"]  = aptos.apply(
    lambda r: get_sat_periodo(r["rut_key"], str(r["periodo_baseline"]),  r["tipo_formacion"]), axis=1)
aptos["sat_resultado"] = aptos.apply(
    lambda r: get_sat_periodo(r["rut_key"], str(r["periodo_resultado"]), r["tipo_formacion"]), axis=1)
aptos["delta_sat"] = (aptos["sat_resultado"] - aptos["sat_baseline"]).round(4)

print(f"\nSAT crudo calculado:")
print(f"  Con sat_baseline:  {aptos['sat_baseline'].notna().sum()}")
print(f"  Con sat_resultado: {aptos['sat_resultado'].notna().sum()}")
print(f"  Con ambos:         {(aptos['sat_baseline'].notna() & aptos['sat_resultado'].notna()).sum()}")

# ── Población de referencia para z-score (todos los 917 con SAT) ──────────────
# Unir SAT ponderado con unidad_facultad (solo docentes del universo 917)
ruts_917 = set(doc["rut_key"])
sat_pop = sat_per[sat_per["rut_key"].isin(ruts_917)].merge(
    doc[["rut_key", "unidad_facultad"]], on="rut_key", how="inner"
)

# Colapsar unidades pequeñas (< 30 RUTs) en "Otras"
n_por_unidad = sat_pop.groupby("unidad_facultad")["rut_key"].nunique()
pequenas = n_por_unidad[n_por_unidad < 30].index.tolist()
sat_pop["uf_ref"] = sat_pop["unidad_facultad"].apply(
    lambda x: "Otras" if x in pequenas or pd.isna(x) else x
)
print(f"\nUnidades colapsadas en 'Otras' (n<30): {pequenas}")

# Estadísticas de referencia por (uf_ref, periodo)
stats_per = (sat_pop.groupby(["uf_ref", "periodo"])["sat"]
             .agg(mu="mean", sigma="std")
             .reset_index())
stats_per["sigma"] = stats_per["sigma"].fillna(1.0)
# Evitar sigma ≈ 0
sigma_global = sat_pop["sat"].std()
stats_per.loc[stats_per["sigma"] < 0.01, "sigma"] = sigma_global
print(f"Grupos uf×período para referencia: {len(stats_per)}")

# Stats anuales para DIPLOMADO/PROYECTO (agregar sobre semestres)
sat_pop["anio"] = sat_pop["periodo"].str[:4]
stats_anio = (sat_pop.groupby(["uf_ref", "anio"])["sat"]
              .agg(mu="mean", sigma="std")
              .reset_index())
stats_anio["sigma"] = stats_anio["sigma"].fillna(1.0)
stats_anio.loc[stats_anio["sigma"] < 0.01, "sigma"] = sigma_global

# Media y sigma globales como fallback
mu_global = sat_pop["sat"].mean()

# ── Función z-score ───────────────────────────────────────────────────────────
def get_z(sat_val, rut, periodo_str, tipo, uf):
    if pd.isna(sat_val):
        return np.nan, np.nan, np.nan
    uf_ref = "Otras" if uf in pequenas or pd.isna(uf) else uf
    if tipo == "TALLER":
        row = stats_per[(stats_per["uf_ref"] == uf_ref) & (stats_per["periodo"] == periodo_str)]
        if len(row) == 0:
            mu, sigma = mu_global, sigma_global
        else:
            mu, sigma = row.iloc[0]["mu"], row.iloc[0]["sigma"]
    else:
        year = str(int(float(periodo_str)))
        row = stats_anio[(stats_anio["uf_ref"] == uf_ref) & (stats_anio["anio"] == year)]
        if len(row) == 0:
            mu, sigma = mu_global, sigma_global
        else:
            mu, sigma = row.iloc[0]["mu"], row.iloc[0]["sigma"]
    z = (sat_val - mu) / sigma
    return round(z, 4), round(mu, 3), round(sigma, 3)

# unidad_facultad ya viene de p3_918.csv (no necesita merge adicional)

# Aplicar z-scores
z_data = aptos.apply(lambda r: pd.Series(
    get_z(r["sat_baseline"],  r["rut_key"], str(r["periodo_baseline"]),  r["tipo_formacion"], r["unidad_facultad"])
), axis=1)
aptos[["z_baseline",  "z_base_mu",  "z_base_sigma"]]  = z_data

z_data2 = aptos.apply(lambda r: pd.Series(
    get_z(r["sat_resultado"], r["rut_key"], str(r["periodo_resultado"]), r["tipo_formacion"], r["unidad_facultad"])
), axis=1)
aptos[["z_resultado", "z_res_mu",   "z_res_sigma"]]   = z_data2

aptos["delta_z"]    = (aptos["z_resultado"] - aptos["z_baseline"]).round(4)
aptos["mejoro_sat"] = aptos["delta_sat"] > 0
aptos["mejoro_z"]   = aptos["delta_z"]   > 0

# ── Resumen por docente (colapsar múltiples instancias) ───────────────────────
# Si un docente tiene TALLER x2, promediar sus métricas
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

NUM_COLS = ["sat_baseline","sat_resultado","delta_sat","z_baseline","z_resultado","delta_z"]
num_agg  = aptos.groupby("rut_key")[NUM_COLS].mean().round(4).reset_index()

bool_agg = aptos.groupby("rut_key").agg(
    mejoro_sat = ("mejoro_sat", lambda x: (x.sum() / len(x)) >= 0.5),
    mejoro_z   = ("mejoro_z",   lambda x: (x.sum() / len(x)) >= 0.5),
).reset_index()

perfil = aptos[PERFIL_COLS].drop_duplicates("rut_key")

out = (perfil
       .merge(form_meta, on="rut_key")
       .merge(num_agg,   on="rut_key")
       .merge(bool_agg,  on="rut_key"))

# ── Resumen impreso ───────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"PASO 5 — Z-SCORES SAT UNIVERSO 917")
print(f"{'='*60}")
print(f"\n1. COBERTURA")
print(f"   Filas (aptos P3):             {len(aptos)}")
print(f"   RUTs únicos:                  {len(out)}")
print(f"   Con z_baseline y z_resultado: {(aptos['z_baseline'].notna() & aptos['z_resultado'].notna()).sum()}")

print(f"\n2. RESULTADOS GLOBALES")
print(f"   Delta SAT crudo (media):  {out['delta_sat'].mean():+.3f}")
print(f"   Delta Z         (media):  {out['delta_z'].mean():+.3f}")
print(f"   % mejora SAT:             {out['mejoro_sat'].mean()*100:.1f}%")
print(f"   % mejora Z:               {out['mejoro_z'].mean()*100:.1f}%")

print(f"\n3. POR TIPO DE FORMACIÓN")
print(f"   {'Tipo':<20} {'N':>5} {'ΔSat':>8} {'ΔZ':>8} {'%Mejora_Z':>10}")
print(f"   {'-'*55}")
for tipo in ["TALLER","DIPLOMADO","PROYECTO","TALLER | DIPLOMADO"]:
    sub = out[out["tipos_formacion"]==tipo] if tipo in out["tipos_formacion"].values else out[out["tipos_formacion"].str.contains(tipo, na=False)]
    if len(sub) == 0:
        continue
    print(f"   {tipo:<20} {len(sub):>5} {sub['delta_sat'].mean():>+8.3f} {sub['delta_z'].mean():>+8.3f} {sub['mejoro_z'].mean()*100:>9.1f}%")

print(f"\n4. POR JERARQUÍA (top)")
jer_res = out.groupby("jerarquia").agg(
    n=("rut_key","count"),
    delta_z=("delta_z","mean"),
    pct_mejora=("mejoro_z","mean")
).sort_values("n", ascending=False).head(6)
print(jer_res.round(3).to_string())

# ── Guardar ───────────────────────────────────────────────────────────────────
out.to_csv(OUT_CSV, encoding="utf-8-sig", index=False)
print(f"\nGuardado: {OUT_CSV}")
print(f"Columnas: {list(out.columns)}")
