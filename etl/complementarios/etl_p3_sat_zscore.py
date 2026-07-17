"""
ETL: p3_sat_zscore.csv
Una fila por docente × instancia de capacitación (209 filas).
Combina:
  - intel.pre_post_sat          → SAT pre/post crudo
  - ped-001 - pd001 - jerarquizados.csv → perfil completo
  - consolidados.evaluacion_periodo × docente_ambos → z-score por unidad_facultad × período
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import numpy as np
from sqlalchemy import create_engine

DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"
OUT    = r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO\Downloads\Analisis_UCEN_v2\PROCESADO\p3_sat_zscore.csv"
CSV_JER = r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO\Downloads\Analisis_UCEN_v2\PROCESADO\ped-001 - pd001 - jerarquizados.csv"

engine = create_engine(DB_URL)

# ── 1. Base: pre_post_sat (209 filas) ─────────────────────────────────────────
sat = pd.read_sql("""
    SELECT rut_key, nombre, tipo_formacion, nombre_actividad,
           periodo_baseline, periodo_durante, periodo_resultado,
           nota_1          AS sat_pre_raw,
           nota_durante    AS sat_durante_raw,
           nota_2          AS sat_post_raw,
           delta_pre_post  AS delta_sat_raw,
           tiene_nota_durante
    FROM intel.pre_post_sat
""", engine)
sat["rut_key"] = sat["rut_key"].astype(str).str.strip()
print(f"pre_post_sat        : {len(sat)} filas, {sat['rut_key'].nunique()} RUTs únicos")

# ── 2. Perfil completo (jerarquizados CSV) ─────────────────────────────────────
jer = pd.read_csv(CSV_JER, encoding="utf-8-sig")
jer["rut_key"] = jer["rut_key"].astype(str).str.strip().str.replace(".0", "", regex=False)

cols_perfil = [
    "rut_key", "sexo", "tipo_contrato", "departamento", "jerarquia",
    "unidad_facultad", "fecha_ingreso", "antiguedad_anios",
    "fecha_nacimiento", "edad_anios", "nivel_formacion",
    "nombre_grado", "tramo_edad", "tramo_antiguedad",
]
jer = jer[[c for c in cols_perfil if c in jer.columns]]
print(f"jerarquizados CSV   : {len(jer)} filas")

df = sat.merge(jer, on="rut_key", how="left")
print(f"después del merge   : {len(df)} filas")

# ── 3. Distribución SAT de TODA la población por unidad_facultad × período ────
# CM-1: cobertura >= 40% | CM-2: ponderado por n_alumnos_evaluaron
pop_raw = pd.read_sql("""
    SELECT e.rut_docente AS rut_key,
           e.periodo,
           e.n_alumnos_evaluaron,
           r.nota_promedio,
           d.unidad_facultad
    FROM consolidados.evaluacion_respuesta r
    JOIN consolidados.evaluacion_periodo e ON r.evaluacion_id = e.evaluacion_id
    JOIN analisis.docente_ambos d ON e.rut_docente = d.rut_key
    WHERE r.pregunta_id = 'SAT_NOTA'
      AND r.nota_promedio IS NOT NULL
      AND e.cobertura_pct >= 40
      AND d.jerarquia NOT IN ('SIN JERARQUÍA', 'SIN JERARQUIA')
""", engine)
pop_raw["rut_key"] = pop_raw["rut_key"].astype(str).str.strip()

# SAT ponderado por docente x periodo (CM-2)
pop_raw["peso_nota"] = pop_raw["nota_promedio"] * pop_raw["n_alumnos_evaluaron"]
pop = (pop_raw.groupby(["rut_key", "periodo", "unidad_facultad"])
       .agg(sat_pond=("peso_nota","sum"), n_alumnos=("n_alumnos_evaluaron","sum"))
       .reset_index())
pop["sat_nota"] = pop["sat_pond"] / pop["n_alumnos"]
print(f"población SAT total : {len(pop)} filas, {pop['rut_key'].nunique()} RUTs")

# Colapsar unidades pequeñas (n < 50) en "Otras" para referencia estadística confiable
n_por_unidad = pop.groupby("unidad_facultad")["rut_key"].nunique()
unidades_pequenas = n_por_unidad[n_por_unidad < 50].index.tolist()
pop["unidad_facultad_ref"] = pop["unidad_facultad"].apply(
    lambda x: "Otras" if x in unidades_pequenas else x
)
print(f"Unidades colapsadas en 'Otras' (n<50 RUTs): {unidades_pequenas}")

# Estadísticas por unidad_facultad_ref × período
stats = (pop.groupby(["unidad_facultad_ref", "periodo"])["sat_nota"]
           .agg(media="mean", std="std")
           .reset_index()
           .rename(columns={"unidad_facultad_ref": "unidad_facultad"}))
# std = 0 no tiene sentido → reemplazar con std global
stats["std"] = stats["std"].fillna(1.0)
stats.loc[stats["std"] < 0.01, "std"] = stats["std"][stats["std"] >= 0.01].mean()

print(f"grupos facultad×período: {len(stats)}")

# ── 4. Función: z-score para un docente en un período dado ────────────────────
def z_score(df, col_nota, col_periodo, col_ufacultad, stats, suffix):
    """Agrega columna z_{suffix} al df."""
    tmp = df[[col_nota, col_periodo, col_ufacultad]].copy()
    tmp = tmp.merge(stats.rename(columns={"periodo": col_periodo,
                                           "unidad_facultad": col_ufacultad}),
                    on=[col_periodo, col_ufacultad], how="left")
    # Fallback: si no hay stats para esa facultad×período, usar media/std global
    media_global = pop["sat_nota"].mean()
    std_global   = pop["sat_nota"].std()
    tmp["media"] = tmp["media"].fillna(media_global)
    tmp["std"]   = tmp["std"].fillna(std_global)
    df[f"z_{suffix}"] = ((df[col_nota] - tmp["media"]) / tmp["std"]).round(4)
    df[f"z_{suffix}_ref_media"] = tmp["media"].round(3)
    df[f"z_{suffix}_ref_std"]   = tmp["std"].round(3)
    return df

# Aplicar mismo colapso de unidades pequeñas al df principal
df["unidad_facultad_ref"] = df["unidad_facultad"].apply(
    lambda x: "Otras" if x in unidades_pequenas else x
)

df = z_score(df, "sat_pre_raw",    "periodo_baseline",   "unidad_facultad_ref", stats, "pre")
df = z_score(df, "sat_post_raw",   "periodo_resultado",  "unidad_facultad_ref", stats, "post")

# Z durante (opcional, solo donde existe)
df_dur = df[df["sat_durante_raw"].notna()].copy()
df_dur = z_score(df_dur, "sat_durante_raw", "periodo_durante", "unidad_facultad_ref", stats, "durante")
df["z_durante"] = df_dur["z_durante"]

# Delta Z
df["delta_z"] = (df["z_post"] - df["z_pre"]).round(4)

# ── 5. Colapsar a una fila por RUT (promedio de instancias) ───────────────────
cols_perfil = [
    "rut_key", "nombre", "sexo", "jerarquia", "nivel_formacion", "nombre_grado",
    "unidad_facultad", "departamento", "antiguedad_anios", "tramo_antiguedad",
    "edad_anios", "tramo_edad", "tipo_contrato",
]
cols_num = ["sat_pre_raw", "sat_durante_raw", "sat_post_raw",
            "delta_sat_raw", "z_pre", "z_durante", "z_post", "delta_z"]

# Métricas de formación por docente
form_meta = df.groupby("rut_key").agg(
    n_instancias      = ("tipo_formacion", "count"),
    tipos_formacion   = ("tipo_formacion", lambda x: " | ".join(sorted(x.unique()))),
    n_taller          = ("tipo_formacion", lambda x: (x == "TALLER").sum()),
    n_diplomado       = ("tipo_formacion", lambda x: (x == "DIPLOMADO").sum()),
    n_proyecto        = ("tipo_formacion", lambda x: (x == "PROYECTO").sum()),
).reset_index()

# Promedio de SAT y Z por docente
num_agg = df.groupby("rut_key")[cols_num].mean().round(4).reset_index()

# Perfil (tomar primera fila — es el mismo para todas las instancias del docente)
perfil = df[cols_perfil].drop_duplicates("rut_key")

# Juntar todo
out = perfil.merge(form_meta, on="rut_key").merge(num_agg, on="rut_key")

# Mejora: booleano simple
out["mejoro_sat"]  = out["delta_sat_raw"] > 0
out["mejoro_z"]    = out["delta_z"] > 0

# Orden de columnas
cols_out = [
    "rut_key", "nombre",
    "sexo", "jerarquia", "nivel_formacion", "nombre_grado",
    "unidad_facultad", "departamento",
    "antiguedad_anios", "tramo_antiguedad", "edad_anios", "tramo_edad",
    "tipo_contrato",
    "n_instancias", "tipos_formacion", "n_taller", "n_diplomado", "n_proyecto",
    "sat_pre_raw", "sat_durante_raw", "sat_post_raw", "delta_sat_raw", "mejoro_sat",
    "z_pre", "z_durante", "z_post", "delta_z", "mejoro_z",
]
out = out[[c for c in cols_out if c in out.columns]]

# ── 6. Resumen ────────────────────────────────────────────────────────────────
print(f"\n=== RESULTADO (1 fila por RUT) ===")
print(f"Filas (RUTs únicos)    : {len(out)}")
print(f"Con múltiples instancias: {(out['n_instancias'] > 1).sum()}")
print(f"\nDelta SAT crudo (media): {out['delta_sat_raw'].mean():+.3f}")
print(f"Delta Z      (media)   : {out['delta_z'].mean():+.3f}")
print(f"% mejora SAT crudo     : {out['mejoro_sat'].mean()*100:.1f}%")
print(f"% mejora Z             : {out['mejoro_z'].mean()*100:.1f}%")
print()
print("Por tipos_formacion:")
print(out.groupby("tipos_formacion").agg(
    n=("rut_key","count"),
    delta_sat=("delta_sat_raw","mean"),
    delta_z=("delta_z","mean"),
    pct_mejora_z=("mejoro_z","mean"),
).round(3).to_string())

# ── 7. Guardar ────────────────────────────────────────────────────────────────
out.to_csv(OUT, index=False, encoding="utf-8-sig")
print(f"\nGuardado: {OUT}")
print(f"Columnas: {list(df.columns)}")
