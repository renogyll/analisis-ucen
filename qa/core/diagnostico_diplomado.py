import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
from sqlalchemy import create_engine, text

engine = create_engine("postgresql://ucen_user:ucen2026@localhost:5432/ucen")

# ── Fuentes ───────────────────────────────────────────────────────────────────
# 1. CSV SPSS (los 29 con pre+post)
df_spss = pd.read_csv("30 diplomados - antes o despues .csv", encoding="utf-8-sig")
for col in ["Promedio_2023_01","Promedio_2023_02","Promedio_2025_01","Promedio_2025_02"]:
    df_spss[col] = pd.to_numeric(df_spss[col].astype(str).str.replace(",","."), errors="coerce")
tiene_pre  = df_spss["Promedio_2023_01"].notna() | df_spss["Promedio_2023_02"].notna()
tiene_post = df_spss["Promedio_2025_01"].notna() | df_spss["Promedio_2025_02"].notna()
spss_64   = set(df_spss["Rut"].astype(str).str.strip())
spss_29   = set(df_spss[tiene_pre & tiene_post]["Rut"].astype(str).str.strip())

# 2. CSV DIPLOMADO 2024 del consolidado
dipl_csv = pd.read_csv(
    r"CONSOLIDADO DOCENTES 3-05-2026\CONSOLIDADO DOCENTES 3-05-2026.xlsx - DIPLOMADO 2024.csv",
    encoding="utf-8-sig"
)
print("Columnas DIPLOMADO 2024 CSV:", dipl_csv.columns.tolist())
# buscar columna de rut
rut_col = [c for c in dipl_csv.columns if "rut" in c.lower() or "RUT" in c]
print("Columna RUT encontrada:", rut_col)
if rut_col:
    dipl_csv["rut_key"] = dipl_csv[rut_col[0]].astype(str).str.strip().str.replace(".0","",regex=False)
    dipl_csv_ruts = set(dipl_csv["rut_key"])
else:
    dipl_csv_ruts = set()

with engine.connect() as conn:
    # 3. consolidados.participacion_formacion DIPLOMADO 2024
    # columnas reales de participacion_formacion
    cols_pf = pd.read_sql(text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema='consolidados' AND table_name='participacion_formacion'
    """), conn)["column_name"].tolist()
    print("Columnas participacion_formacion:", cols_pf)

    pf = pd.read_sql(text("""
        SELECT rut_key, tipo_formacion, nombre_actividad, anio_evento, periodo_evento
        FROM consolidados.participacion_formacion
        WHERE tipo_formacion = 'DIPLOMADO'
        ORDER BY anio_evento, rut_key
    """), conn)

    # 4. p3_grupo_tratamiento DIPLOMADO
    cols_p3 = pd.read_sql(text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema='analisis' AND table_name='p3_grupo_tratamiento'
    """), conn)["column_name"].tolist()

    p3 = pd.read_sql(text("""
        SELECT rut_key, tipo_formacion, nombre_actividad,
               anio_evento, periodo_evento, periodo_baseline, periodo_resultado
        FROM analisis.p3_grupo_tratamiento
        WHERE tipo_formacion = 'DIPLOMADO'
    """), conn)

    # 5. docente_ambos (los 492 jerarquizados)
    ambos = pd.read_sql(text("""
        SELECT rut_key, jerarquia FROM analisis.docente_ambos
        WHERE jerarquia NOT IN ('SIN JERARQUIA')
        AND jerarquia NOT ILIKE '%sin jerarqu%'
    """), conn)

pf["rut_key"]    = pf["rut_key"].astype(str).str.strip()
p3["rut_key"]    = p3["rut_key"].astype(str).str.strip()
ambos["rut_key"] = ambos["rut_key"].astype(str).str.strip()

pf_2024_ruts  = set(pf[pf["anio_evento"]==2024]["rut_key"])
pf_todos_ruts = set(pf["rut_key"])
p3_ruts       = set(p3["rut_key"])
ambos_ruts    = set(ambos["rut_key"])

# ── DIAGNÓSTICO ───────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("DIAGNÓSTICO COMPLETO — DISCREPANCIA DIPLOMADO")
print("="*60)

print(f"\n1. FUENTES DISPONIBLES")
print(f"   SPSS (64 totales)               : {len(spss_64)}")
print(f"   SPSS estrictos (pre+post)        : {len(spss_29)}")
print(f"   CSV Consolidado DIPLOMADO 2024   : {len(dipl_csv_ruts)}")
print(f"   participacion_formacion DIPL 2024: {len(pf_2024_ruts)}")
print(f"   participacion_formacion DIPL ALL : {len(pf_todos_ruts)}")
print(f"   p3_grupo_tratamiento DIPLOMADO   : {len(p3_ruts)}")
print(f"   docente_ambos (492 jerarquizados): {len(ambos_ruts)}")

print(f"\n2. CRUCE: SPSS 29 vs nuestras fuentes")
print(f"   En SPSS-29 Y en p3             : {len(spss_29 & p3_ruts)}")
print(f"   En SPSS-29 Y en pf_2024        : {len(spss_29 & pf_2024_ruts)}")
print(f"   En SPSS-29 Y en CSV consolidado: {len(spss_29 & dipl_csv_ruts)}")
print(f"   En SPSS-29 Y en jerarquizados  : {len(spss_29 & ambos_ruts)}")

print(f"\n3. LOS 16 PERDIDOS — ¿DÓNDE ESTÁN?")
perdidos = spss_29 - p3_ruts
for rut in sorted(perdidos):
    nombre = df_spss[df_spss["Rut"].astype(str).str.strip()==rut]["NOMBREDOCENTE_2024"].values
    nombre = nombre[0] if len(nombre)>0 else "?"
    en_pf_2024 = "✓ pf_2024" if rut in pf_2024_ruts else "✗ pf_2024"
    en_pf_all  = "✓ pf_all"  if rut in pf_todos_ruts else "✗ pf_all"
    en_csv     = "✓ csv_cons" if rut in dipl_csv_ruts else "✗ csv_cons"
    en_jer     = "✓ jerarq"  if rut in ambos_ruts else "✗ jerarq"
    print(f"   {rut}  {nombre[:30]:<30}  {en_pf_2024}  {en_pf_all}  {en_csv}  {en_jer}")

print(f"\n4. RAÍZ DE LA DISCREPANCIA")
no_en_pf    = perdidos - pf_todos_ruts
no_en_jer   = perdidos - ambos_ruts
en_pf_no_p3 = (perdidos & pf_todos_ruts) - p3_ruts
print(f"   Perdidos no están en participacion_formacion: {len(no_en_pf)}")
print(f"   Perdidos no están en jerarquizados (492)    : {len(no_en_jer)}")
print(f"   Perdidos SI en pf pero NO llegaron a p3     : {len(en_pf_no_p3)}")

print(f"\n5. p3_grupo_tratamiento vs participacion_formacion DIPLOMADO 2024")
print(f"   En pf_2024 pero NO en p3        : {len(pf_2024_ruts - p3_ruts)}")
print(f"   En p3 pero NO en pf_2024        : {len(p3_ruts - pf_2024_ruts)}")
print(f"   En ambos                        : {len(p3_ruts & pf_2024_ruts)}")

if len(pf_2024_ruts - p3_ruts) > 0:
    print(f"\n   Detalle: en pf_2024 pero no en p3:")
    sub = pf[pf["rut_key"].isin(pf_2024_ruts - p3_ruts)]
    print(sub[["rut_key","nombre_actividad","anio_evento","periodo_evento"]].to_string(index=False))
