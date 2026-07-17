import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
from sqlalchemy import create_engine, text

engine = create_engine("postgresql://ucen_user:ucen2026@localhost:5432/ucen")

df = pd.read_csv("30 diplomados - antes o despues .csv", encoding="utf-8-sig")
for col in ["Promedio_2023_01","Promedio_2023_02","Promedio_2025_01","Promedio_2025_02"]:
    df[col] = pd.to_numeric(df[col].astype(str).str.replace(",","."), errors="coerce")

tiene_pre  = df["Promedio_2023_01"].notna() | df["Promedio_2023_02"].notna()
tiene_post = df["Promedio_2025_01"].notna() | df["Promedio_2025_02"].notna()
spss_30 = df[tiene_pre & tiene_post].copy()
spss_30["Rut"] = spss_30["Rut"].astype(str).str.strip()

sat = pd.read_csv("PROCESADO/intel_pre_post_sat.csv", encoding="utf-8-sig")
sat_dipl_ruts = set(sat[sat["tipo_formacion"]=="DIPLOMADO"]["rut_key"].astype(str).str.strip())

perdidos_ruts = set(spss_30["Rut"]) - sat_dipl_ruts
perdidos_df   = spss_30[spss_30["Rut"].isin(perdidos_ruts)]

with engine.connect() as conn:
    p3 = pd.read_sql(text("""
        SELECT rut_key, nombre, tipo_formacion, nombre_actividad,
               anio_evento, periodo_evento, periodo_baseline, periodo_resultado
        FROM analisis.p3_grupo_tratamiento
        WHERE tipo_formacion = 'DIPLOMADO'
    """), conn)

    sat_eval = pd.read_sql(text("""
        SELECT e.rut_docente AS rut_key, e.periodo, r.nota_promedio
        FROM consolidados.evaluacion_respuesta r
        JOIN consolidados.evaluacion_periodo e ON r.evaluacion_id = e.evaluacion_id
        WHERE r.pregunta_id = 'SAT_NOTA' AND r.nota_promedio IS NOT NULL
        ORDER BY e.rut_docente, e.periodo
    """), conn)

p3["rut_key"]       = p3["rut_key"].astype(str).str.strip()
sat_eval["rut_key"] = sat_eval["rut_key"].astype(str).str.strip()

print(f"Total en SPSS (pre+post): {len(spss_30)}")
print(f"Perdidos (en SPSS no en nuestra base): {len(perdidos_ruts)}")

print("\n=== ESTADO EN p3_grupo_tratamiento ===")
p3_perd = p3[p3["rut_key"].isin(perdidos_ruts)]
no_en_p3 = perdidos_ruts - set(p3["rut_key"])
print(f"Aparecen en p3_grupo_tratamiento : {len(p3_perd)}")
print(f"NO aparecen en p3_grupo_tratamiento: {len(no_en_p3)}")
if len(no_en_p3) > 0:
    print("  RUTs ausentes:", no_en_p3)

if len(p3_perd) > 0:
    print("\nDetalle p3_grupo_tratamiento:")
    print(p3_perd[["rut_key","nombre","anio_evento","periodo_evento",
                    "periodo_baseline","periodo_resultado"]].to_string(index=False))

print("\n=== SUS PERIODOS SAT ===")
for _, row in perdidos_df.iterrows():
    rut    = row["Rut"]
    nombre = row["NOMBREDOCENTE_2024"]
    evals  = sat_eval[sat_eval["rut_key"] == rut]["periodo"].tolist()
    p3_row = p3[p3["rut_key"] == rut]
    baseline   = p3_row["periodo_baseline"].values[0]   if len(p3_row) > 0 else "—"
    resultado  = p3_row["periodo_resultado"].values[0]  if len(p3_row) > 0 else "—"
    print(f"  {nombre}")
    print(f"    SAT períodos: {evals}")
    print(f"    baseline={baseline}  resultado={resultado}")
