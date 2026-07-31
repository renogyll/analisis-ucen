import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
from sqlalchemy import create_engine, text

engine = create_engine("postgresql://ucen_user:ucen2026@localhost:5432/ucen")

# SPSS estrictos (pre+post)
df_spss = pd.read_csv("30 diplomados - antes o despues .csv", encoding="utf-8-sig")
for col in ["Promedio_2023_01","Promedio_2023_02","Promedio_2025_01","Promedio_2025_02"]:
    df_spss[col] = pd.to_numeric(df_spss[col].astype(str).str.replace(",","."), errors="coerce")
tiene_pre  = df_spss["Promedio_2023_01"].notna() | df_spss["Promedio_2023_02"].notna()
tiene_post = df_spss["Promedio_2025_01"].notna() | df_spss["Promedio_2025_02"].notna()
df_spss["Rut"] = df_spss["Rut"].astype(str).str.strip()
spss_29 = df_spss[tiene_pre & tiene_post][["Rut","NOMBREDOCENTE_2024","Facultad_2024"]].copy()

# Nuestra base: intel.pre_post_sat DIPLOMADO
sat = pd.read_csv("PROCESADO/intel_pre_post_sat.csv", encoding="utf-8-sig")
sat_dipl = sat[sat["tipo_formacion"]=="DIPLOMADO"][["rut_key","nombre","nota_1","nota_2","delta_pre_post"]].copy()
sat_dipl["rut_key"] = sat_dipl["rut_key"].astype(str).str.strip()

# Jerarquizados
with engine.connect() as conn:
    ambos = pd.read_sql(text("""
        SELECT rut_key, jerarquia, unidad_facultad
        FROM analisis.docente_ambos
        WHERE jerarquia NOT IN ('SIN JERARQUIA')
        AND jerarquia NOT ILIKE '%sin jerarqu%'
    """), conn)
    p3_dipl = pd.read_sql(text("""
        SELECT rut_key, nombre_actividad, anio_evento, periodo_baseline, periodo_resultado
        FROM analisis.p3_grupo_tratamiento
        WHERE tipo_formacion = 'DIPLOMADO'
    """), conn)

ambos["rut_key"]    = ambos["rut_key"].astype(str).str.strip()
p3_dipl["rut_key"]  = p3_dipl["rut_key"].astype(str).str.strip()

spss_ruts   = set(spss_29["Rut"])
nuestros_ruts = set(sat_dipl["rut_key"])

solo_spss    = spss_ruts - nuestros_ruts      # 16
solo_nuestros = nuestros_ruts - spss_ruts     # 7
en_ambos     = spss_ruts & nuestros_ruts      # 13

print("="*65)
print(f"GRUPO A — Solo en SPSS, no en nuestro análisis ({len(solo_spss)})")
print("="*65)
print("Razón: no son parte de los 492 jerarquizados (nómina+dotación)\n")
for rut in sorted(solo_spss):
    row   = spss_29[spss_29["Rut"]==rut].iloc[0]
    jer   = ambos[ambos["rut_key"]==rut]
    en_jer = "NO jerarquizado" if len(jer)==0 else jer.iloc[0]["jerarquia"]
    print(f"  {rut}  {row['NOMBREDOCENTE_2024'][:35]:<35}  {en_jer}")

print()
print("="*65)
print(f"GRUPO B — Solo en nuestro análisis, no en SPSS ({len(solo_nuestros)})")
print("="*65)
print("Razón: hicieron diplomado en año distinto a 2024\n")
for rut in sorted(solo_nuestros):
    row_sat = sat_dipl[sat_dipl["rut_key"]==rut].iloc[0]
    row_p3  = p3_dipl[p3_dipl["rut_key"]==rut]
    anio    = row_p3["anio_evento"].values[0] if len(row_p3)>0 else "?"
    activ   = row_p3["nombre_actividad"].values[0] if len(row_p3)>0 else "?"
    print(f"  {rut}  {row_sat['nombre'][:35]:<35}  año={anio}  {activ[:30]}")

print()
print("="*65)
print(f"GRUPO C — En ambos (coincidencia perfecta): {len(en_ambos)}")
print("="*65)
for rut in sorted(en_ambos):
    row_spss = spss_29[spss_29["Rut"]==rut].iloc[0]
    row_sat  = sat_dipl[sat_dipl["rut_key"]==rut].iloc[0]
    print(f"  {rut}  {row_spss['NOMBREDOCENTE_2024'][:35]:<35}  Δ={row_sat['delta_pre_post']:+.2f}")
