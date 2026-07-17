"""
ETL P3 — Grupo de Tratamiento
Una fila por docente × evento de formación con periodos pre/post calculados.

CAMBIO METODOLÓGICO 2026-07-16:
  Universo base: analisis.universo_base (985 RUTs), NO docente_ambos (520).
  Periodos taller 2025-01 y 2025-02 agregados por la contraparte.
  Fuentes de datos: DB (analisis + consolidados), NO CSVs del directorio PROCESADO.

Reglas de periodo:
  DIPLOMADO/PROYECTO: año X → baseline = X-1, resultado = X+1
  TALLER:
    2023-02 → baseline 2023-01, resultado 2024-01
    2024-01 → baseline 2023-02, resultado 2024-02
    2024-02 → baseline 2024-01, resultado 2025-01
    2025-01 → baseline 2024-02, resultado 2025-02
    2025-02 → baseline 2025-01, resultado 2026-01
"""
import sys; sys.stdout.reconfigure(encoding="utf-8")
import os
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).parents[2]))
from config import CASCADE

DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"
engine = create_engine(DB_URL)

OUT_DIR = os.path.join(CASCADE, "complementarios")

TALLER_BASELINE = {
    "2023-02": "2023-01",
    "2024-01": "2023-02",
    "2024-02": "2024-01",
    "2025-01": "2024-02",
    "2025-02": "2025-01",
}
TALLER_RESULTADO = {
    "2023-02": "2024-01",
    "2024-01": "2024-02",
    "2024-02": "2025-01",
    "2025-01": "2025-02",
    "2025-02": "2026-01",
}

def periodos_diplomado(anio):
    a = int(anio)
    return [f"{a-1}-01", f"{a-1}-02"], [f"{a+1}-01", f"{a+1}-02"]

# ── Cargar fuentes desde DB ───────────────────────────────────────────────────
with engine.connect() as conn:
    base = pd.read_sql(text("SELECT * FROM analisis.universo_base"), conn)

    pf = pd.read_sql(text("""
        SELECT rut_key, tipo_formacion, nombre_actividad, anio_evento, periodo_evento
        FROM consolidados.participacion_formacion
        ORDER BY rut_key, anio_evento, periodo_evento
    """), conn)

    ep = pd.read_sql(text("""
        SELECT rut_docente AS rut_key, periodo
        FROM consolidados.evaluacion_periodo
        WHERE cobertura_pct >= 40
    """), conn)

    cj = pd.read_sql(text("""
        SELECT DISTINCT rut_key
        FROM consolidados.evaluacion_jefes
        WHERE tiene_eval_jefe = 'SI'
    """), conn)

base["rut_key"] = base["rut_key"].astype(str).str.strip()
pf["rut_key"]   = pf["rut_key"].astype(str).str.strip()
ep["rut_key"]   = ep["rut_key"].astype(str).str.strip()

ruts_base = set(base["rut_key"])
pf_base   = pf[pf["rut_key"].isin(ruts_base)].copy()

eval_por_docente = ep.groupby("rut_key")["periodo"].apply(set).to_dict()
ruts_con_jefe    = set(cj["rut_key"].astype(str).str.strip())

print(f"universo_base:   {len(ruts_base)} RUTs")
print(f"Eventos P3 base: {len(pf_base)} | {pf_base['rut_key'].nunique()} docentes")

# ── Construir tabla ───────────────────────────────────────────────────────────
filas = []
for _, row in pf_base.iterrows():
    rut  = row["rut_key"]
    tipo = row["tipo_formacion"]
    anio = row["anio_evento"]
    per  = row["periodo_evento"] if pd.notna(row["periodo_evento"]) else None

    if tipo in ("DIPLOMADO", "PROYECTO"):
        periodos_base, periodos_res = periodos_diplomado(anio)
        periodo_baseline  = f"{int(anio)-1}"
        periodo_resultado = f"{int(anio)+1}"
    elif tipo == "TALLER" and per in TALLER_BASELINE:
        periodos_base     = [TALLER_BASELINE[per]]
        periodos_res      = [TALLER_RESULTADO[per]]
        periodo_baseline  = TALLER_BASELINE[per]
        periodo_resultado = TALLER_RESULTADO[per]
    else:
        continue

    evals_docente = eval_por_docente.get(rut, set())
    tiene_base    = any(p in evals_docente for p in periodos_base)
    tiene_res     = any(p in evals_docente for p in periodos_res)
    tiene_jefe    = rut in ruts_con_jefe

    filas.append({
        "rut_key":                      rut,
        "tipo_formacion":               tipo,
        "nombre_actividad":             row["nombre_actividad"],
        "anio_evento":                  anio,
        "periodo_evento":               per,
        "periodo_baseline":             periodo_baseline,
        "periodo_resultado":            periodo_resultado,
        "tiene_eval_alumnos_baseline":  tiene_base,
        "tiene_eval_alumnos_resultado": tiene_res,
        "tiene_eval_jefe":              tiene_jefe,
        "apto_p3":                      tiene_base and tiene_res,
    })

df = pd.DataFrame(filas)

# Agregar perfil del docente desde universo_base
PERFIL_COLS = ["rut_key","nombre","sexo","jerarquia","jerarquia_dot",
               "tipo_contrato_tag","departamento","area_carrera","unidad_facultad",
               "nivel_formacion","antiguedad_anios","tramo_antiguedad",
               "edad_anios","tramo_edad","origen"]
perf_disponibles = [c for c in PERFIL_COLS if c in base.columns]
df = df.merge(base[perf_disponibles], on="rut_key", how="left")

col_orden = perf_disponibles + [c for c in df.columns if c not in perf_disponibles]
df = df[col_orden]

# ── Resumen ───────────────────────────────────────────────────────────────────
print(f"\np3_grupo_tratamiento:")
print(f"  Total filas (docente × evento):   {len(df)}")
print(f"  RUTs únicos:                      {df['rut_key'].nunique()}")
print(f"  Aptos para análisis (apto_p3):    {df['apto_p3'].sum()} filas | {df[df['apto_p3']]['rut_key'].nunique()} docentes")
print(f"\nPor tipo de formación:")
print(df.groupby("tipo_formacion").agg(
    filas=("rut_key","count"),
    docentes=("rut_key","nunique"),
    aptos=("apto_p3","sum")
).to_string())
print(f"\nPor origen:")
print(df.groupby("origen").agg(
    docentes=("rut_key","nunique"),
    aptos=("apto_p3","sum")
).to_string())
print(f"\nCon eval jefe:              {df[df['tiene_eval_jefe']]['rut_key'].nunique()} docentes")
print(f"Con eval baseline:          {df[df['tiene_eval_alumnos_baseline']]['rut_key'].nunique()} docentes")
print(f"Con eval resultado:         {df[df['tiene_eval_alumnos_resultado']]['rut_key'].nunique()} docentes")

# ── Guardar ───────────────────────────────────────────────────────────────────
os.makedirs(OUT_DIR, exist_ok=True)
csv_path = os.path.join(OUT_DIR, "P3_grupo_tratamiento.csv")
df.to_csv(csv_path, index=False, encoding="utf-8-sig")

df_db = df.copy()
for col in ["tiene_eval_alumnos_baseline","tiene_eval_alumnos_resultado",
            "tiene_eval_jefe","apto_p3"]:
    df_db[col] = df_db[col].astype(bool)
df_db.to_sql("p3_grupo_tratamiento", engine, schema="analisis", if_exists="replace", index=False)
print(f"\nGuardado: {csv_path}")
print(f"DB: analisis.p3_grupo_tratamiento  ({len(df_db)} filas)")
