import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
from sqlalchemy import create_engine, text
import os

engine  = create_engine("postgresql://ucen_user:ucen2026@localhost:5432/ucen")
BASE    = os.path.dirname(__file__)
OUT_CSV = os.path.join(BASE, "p3_918.csv")

# ── Mapeo de periodos taller ──────────────────────────────────────────────────
TALLER_BASELINE  = {"2023-02": "2023-01", "2024-01": "2023-02", "2024-02": "2024-01"}
TALLER_RESULTADO = {"2023-02": "2024-01", "2024-01": "2024-02", "2024-02": "2025-01"}

def periodos_dip_proy(anio):
    a = int(anio)
    return [f"{a-1}-01", f"{a-1}-02"], [f"{a+1}-01", f"{a+1}-02"]

# ── Cargar universo 917 ───────────────────────────────────────────────────────
doc = pd.read_csv(
    os.path.join(BASE, "docente_918.csv"),
    encoding="utf-8-sig", dtype={"rut_key": str}
)
doc["rut_key"] = doc["rut_key"].str.strip()
ruts_917 = set(doc["rut_key"])
print(f"Universo 917: {len(ruts_917)} RUTs únicos")

# ── Formación ─────────────────────────────────────────────────────────────────
with engine.connect() as conn:
    pf = pd.read_sql(text("""
        SELECT rut_key, tipo_formacion, nombre_actividad, anio_evento, periodo_evento
        FROM consolidados.participacion_formacion
        ORDER BY rut_key, anio_evento, periodo_evento
    """), conn)

pf["rut_key"] = pf["rut_key"].astype(str).str.strip()
pf_917 = pf[pf["rut_key"].isin(ruts_917)].copy()
print(f"Eventos formación 917: {len(pf_917)} filas | {pf_917['rut_key'].nunique()} docentes")

# ── Períodos SAT válidos por docente (CM-1: cobertura ≥40%) ──────────────────
with engine.connect() as conn:
    ep = pd.read_sql(text("""
        SELECT e.rut_docente AS rut_key, e.periodo
        FROM consolidados.evaluacion_periodo e
        JOIN consolidados.evaluacion_respuesta r ON r.evaluacion_id = e.evaluacion_id
        WHERE r.pregunta_id = 'SAT_NOTA'
        AND e.cobertura_pct >= 40
    """), conn)

ep["rut_key"] = ep["rut_key"].astype(str).str.strip()
# Diccionario: rut_key → set de períodos con SAT válido
periodos_sat = ep.groupby("rut_key")["periodo"].apply(set).to_dict()

# ── Construir tabla tratamiento ───────────────────────────────────────────────
filas = []

for _, row in pf_917.iterrows():
    rut  = row["rut_key"]
    tipo = row["tipo_formacion"]
    anio = row["anio_evento"]
    per  = row["periodo_evento"] if pd.notna(row["periodo_evento"]) else None

    if tipo in ("DIPLOMADO", "PROYECTO"):
        periodos_base, periodos_res = periodos_dip_proy(anio)
        periodo_baseline  = f"{int(anio)-1}"
        periodo_resultado = f"{int(anio)+1}"
    elif tipo == "TALLER" and per in TALLER_BASELINE:
        periodos_base = [TALLER_BASELINE[per]]
        periodos_res  = [TALLER_RESULTADO[per]]
        periodo_baseline  = TALLER_BASELINE[per]
        periodo_resultado = TALLER_RESULTADO[per]
    else:
        continue  # taller sin periodo conocido

    sat_doc = periodos_sat.get(rut, set())
    tiene_base = any(p in sat_doc for p in periodos_base)
    tiene_res  = any(p in sat_doc for p in periodos_res)

    filas.append({
        "rut_key":            rut,
        "tipo_formacion":     tipo,
        "nombre_actividad":   row["nombre_actividad"],
        "anio_evento":        anio,
        "periodo_evento":     per,
        "periodo_baseline":   periodo_baseline,
        "periodo_resultado":  periodo_resultado,
        "tiene_sat_baseline":  tiene_base,
        "tiene_sat_resultado": tiene_res,
        "apto_p3":             tiene_base and tiene_res,
    })

df = pd.DataFrame(filas)

# ── Agregar perfil del docente ────────────────────────────────────────────────
PERFIL = ["rut_key","nombre","sexo","jerarquia","jerarquia_dot",
          "tipo_contrato","unidad_facultad","nivel_formacion",
          "antiguedad_anios","tramo_antiguedad","edad_anios","tramo_edad",
          "origen","tiene_perfil_completo"]
df = df.merge(doc[PERFIL], on="rut_key", how="left")

# Ordenar columnas: perfil + evento + flags
col_orden = PERFIL + [c for c in df.columns if c not in PERFIL]
df = df[col_orden]

# ── Resumen ───────────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"PASO 4 — GRUPO TRATAMIENTO 917")
print(f"{'='*60}")
print(f"\n1. TOTAL")
print(f"   Filas (docente × evento): {len(df)}")
print(f"   RUTs únicos con formación: {df['rut_key'].nunique()}")
print(f"   Aptos P3 (filas):          {df['apto_p3'].sum()}")
print(f"   Aptos P3 (RUTs únicos):    {df[df['apto_p3']]['rut_key'].nunique()}")

print(f"\n2. POR TIPO DE FORMACIÓN")
print(f"   {'Tipo':<12} {'Filas':>6} {'RUTs':>6} {'Aptos':>7} {'%Aptos':>8}")
print(f"   {'-'*44}")
for tipo in ["TALLER","DIPLOMADO","PROYECTO"]:
    sub = df[df["tipo_formacion"]==tipo]
    if len(sub) == 0:
        continue
    aptos = sub["apto_p3"].sum()
    ruts  = sub["rut_key"].nunique()
    print(f"   {tipo:<12} {len(sub):>6} {ruts:>6} {aptos:>7} {aptos/len(sub)*100:>7.1f}%")

print(f"\n3. APTOS P3 POR ORIGEN")
aptos_df = df[df["apto_p3"]]
for origen in ["ambos","nomina","dotacion"]:
    sub = aptos_df[aptos_df["origen"]==origen]["rut_key"].nunique()
    print(f"   {origen:<12}: {sub} RUTs aptos")

print(f"\n4. APTOS P3 POR TIPO Y PERFIL")
for tipo in ["TALLER","DIPLOMADO","PROYECTO"]:
    sub = df[(df["tipo_formacion"]==tipo) & df["apto_p3"]]
    if len(sub) == 0:
        continue
    con_pf    = sub[sub["tiene_perfil_completo"]==True]["rut_key"].nunique()
    sin_pf    = sub[sub["tiene_perfil_completo"]==False]["rut_key"].nunique()
    print(f"   {tipo}: {sub['rut_key'].nunique()} aptos → perfil completo: {con_pf} | solo nómina: {sin_pf}")

print(f"\n5. RAZÓN DE NO APTITUD (docentes con formación pero sin apto_p3)")
no_aptos = df[~df["apto_p3"]]
sin_base = (~df["tiene_sat_baseline"] & df["tiene_sat_resultado"]).sum()
sin_res  = (df["tiene_sat_baseline"] & ~df["tiene_sat_resultado"]).sum()
sin_amb  = (~df["tiene_sat_baseline"] & ~df["tiene_sat_resultado"]).sum()
print(f"   Sin SAT baseline únicamente:  {sin_base}")
print(f"   Sin SAT resultado únicamente: {sin_res}")
print(f"   Sin SAT en ambos períodos:    {sin_amb}")

# ── Guardar ───────────────────────────────────────────────────────────────────
df.to_csv(OUT_CSV, encoding="utf-8-sig", index=False)
print(f"\nGuardado: {OUT_CSV}")
print(f"Total filas: {len(df)}")
