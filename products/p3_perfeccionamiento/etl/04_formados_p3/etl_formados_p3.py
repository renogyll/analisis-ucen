"""
ETL: Universo Formados P3
FILTRO: universo_base que participó en ≥1 actividad P3 (Taller/Diplomado/Proyecto)
FUENTE: analisis.universo_base (DB) + consolidados.participacion_formacion (DB)
SALIDAS: analisis.universo_formados_p3 (DB)
         data/cascade/04_formados_p3/docentes_formados.csv
         data/cascade/04_formados_p3/p3_918.csv  (alias por compatibilidad)

CAMBIO METODOLÓGICO 2026-07-16:
  Universo base es ahora NOMINA × DOTACION (985 RUTs), NO solo jerarquizados.
  Un docente honorario sin jerarquía que participó en P3 es incluido.

Periodos taller vigentes (incluye 2025-01 y 2025-02 agregados por la contraparte):
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
from config import C04_FORMADOS

DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"
engine = create_engine(DB_URL)

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

def periodos_dip_proy(anio):
    a = int(anio)
    return [f"{a-1}-01", f"{a-1}-02"], [f"{a+1}-01", f"{a+1}-02"]

# ── Cargar universo base ──────────────────────────────────────────────────────
with engine.connect() as conn:
    doc = pd.read_sql(text("SELECT * FROM analisis.universo_base"), conn)
    pf  = pd.read_sql(text("""
        SELECT rut_key, tipo_formacion, nombre_actividad, anio_evento, periodo_evento
        FROM consolidados.participacion_formacion
        ORDER BY rut_key, anio_evento, periodo_evento
    """), conn)
    ep = pd.read_sql(text("""
        SELECT e.rut_docente AS rut_key, e.periodo
        FROM consolidados.evaluacion_periodo e
        JOIN consolidados.evaluacion_respuesta r ON r.evaluacion_id = e.evaluacion_id
        WHERE r.pregunta_id = 'SAT_NOTA' AND e.cobertura_pct >= 40
    """), conn)

doc["rut_key"] = doc["rut_key"].astype(str).str.strip()
pf["rut_key"]  = pf["rut_key"].astype(str).str.strip()
ep["rut_key"]  = ep["rut_key"].astype(str).str.strip()

ruts_base = set(doc["rut_key"])
pf_base   = pf[pf["rut_key"].isin(ruts_base)].copy()
periodos_sat = ep.groupby("rut_key")["periodo"].apply(set).to_dict()

print(f"universo_base: {len(ruts_base)} RUTs")
print(f"Eventos formación en base: {len(pf_base)} filas | {pf_base['rut_key'].nunique()} docentes")

# ── Construir tabla formados ──────────────────────────────────────────────────
filas = []
for _, row in pf_base.iterrows():
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
        continue

    sat_doc    = periodos_sat.get(rut, set())
    tiene_base = any(p in sat_doc for p in periodos_base)
    tiene_res  = any(p in sat_doc for p in periodos_res)

    filas.append({
        "rut_key":             rut,
        "tipo_formacion":      tipo,
        "nombre_actividad":    row["nombre_actividad"],
        "anio_evento":         anio,
        "periodo_evento":      per,
        "periodo_baseline":    periodo_baseline,
        "periodo_resultado":   periodo_resultado,
        "tiene_sat_baseline":  tiene_base,
        "tiene_sat_resultado": tiene_res,
        "apto_p3":             tiene_base and tiene_res,
    })

df = pd.DataFrame(filas)

# Agregar perfil del universo base
PERFIL = ["rut_key","nombre","sexo","jerarquia","jerarquia_dot",
          "tipo_contrato","tipo_contrato_tag","unidad_facultad","departamento",
          "nivel_formacion","nombre_grado",
          "antiguedad_anios","tramo_antiguedad","edad_anios","tramo_edad",
          "origen"]
perfil_cols = [c for c in PERFIL if c in doc.columns]
df = df.merge(doc[perfil_cols], on="rut_key", how="left")

col_orden = perfil_cols + [c for c in df.columns if c not in perfil_cols]
df = df[col_orden]

# ── Resumen ───────────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"FORMADOS P3 — UNIVERSO BASE (sin filtro jerarquía)")
print(f"{'='*60}")
print(f"Filas (docente × evento): {len(df)}")
print(f"RUTs únicos con formación: {df['rut_key'].nunique()}")
print(f"Aptos P3 (filas):          {df['apto_p3'].sum()}")
print(f"Aptos P3 (RUTs únicos):    {df[df['apto_p3']]['rut_key'].nunique()}")
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

# ── Guardar ───────────────────────────────────────────────────────────────────
os.makedirs(C04_FORMADOS, exist_ok=True)
df.to_csv(os.path.join(C04_FORMADOS, "docentes_formados.csv"), index=False, encoding="utf-8-sig")
df.to_csv(os.path.join(C04_FORMADOS, "p3_918.csv"), index=False, encoding="utf-8-sig")  # alias compat.

df_db = df.copy()
for col in ["tiene_sat_baseline", "tiene_sat_resultado", "apto_p3"]:
    df_db[col] = df_db[col].astype(bool)
df_db.to_sql("universo_formados_p3", engine, schema="analisis", if_exists="replace", index=False)
print(f"\nGuardado: CSV + alias p3_918.csv + analisis.universo_formados_p3")
