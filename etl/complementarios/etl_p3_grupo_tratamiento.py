"""
ETL P3 — Grupo de Tratamiento
Una fila por docente x evento de formacion con periodos pre/post calculados.

Reglas de periodo (DECISIONES_METODOLOGICAS.md seccion 8):
  DIPLOMADO/PROYECTO: anio X -> baseline = X-1, resultado = X+1
  TALLER:            semestre S -> baseline = S-1, resultado = S+2
    2023-02 -> baseline 2023-01, resultado 2024-01
    2024-01 -> baseline 2023-02, resultado 2024-02
    2024-02 -> baseline 2024-01, resultado 2025-01

Flags calculados:
  tiene_eval_alumnos_baseline  : tiene >= 1 evaluacion estudiantil en periodo baseline
  tiene_eval_alumnos_resultado : tiene >= 1 evaluacion estudiantil en periodo resultado
  tiene_eval_jefe              : tiene >= 1 evaluacion de jefe en cualquier anio
  apto_p3                      : tiene_eval_alumnos_baseline AND tiene_eval_alumnos_resultado
"""

import pandas as pd
import os
from sqlalchemy import create_engine

BASE = r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO\Downloads\Analisis_UCEN_v2"
OUT  = os.path.join(BASE, "PROCESADO")
DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"

# ── Mapeo de periodos taller ──────────────────────────────────────────────────
TALLER_BASELINE = {
    "2023-02": "2023-01",
    "2024-01": "2023-02",
    "2024-02": "2024-01",
}
TALLER_RESULTADO = {
    "2023-02": "2024-01",
    "2024-01": "2024-02",
    "2024-02": "2025-01",
}

def periodos_diplomado(anio):
    a = int(anio)
    # baseline: cualquier semestre del año anterior
    baseline  = [f"{a-1}-01", f"{a-1}-02"]
    # resultado: cualquier semestre del año siguiente
    resultado = [f"{a+1}-01", f"{a+1}-02"]
    return baseline, resultado

# ── Cargar fuentes ────────────────────────────────────────────────────────────
ambos = pd.read_csv(os.path.join(OUT, "docente_ambos.csv"), dtype=str)
pf    = pd.read_csv(os.path.join(OUT, "P3_participacion_formacion_todos.csv"), dtype=str)
ep    = pd.read_csv(os.path.join(OUT, "evaluacion_periodo.csv"), dtype=str)
cj    = pd.read_csv(os.path.join(OUT, "P1_consolidado_con_evaluacion_jefes.csv"), dtype=str)

ruts_520 = set(ambos["rut_key"].unique())

# Participacion filtrada a 520
pf_520 = pf[pf["rut_key"].isin(ruts_520)].copy()
print(f"Eventos de formacion para los 520: {len(pf_520)} | {pf_520['rut_key'].nunique()} docentes")

# Lookup rapido: que periodos de evaluacion tiene cada docente
eval_por_docente = ep.groupby("rut_docente")["periodo"].apply(set).to_dict()

# RUTs con alguna eval de jefe
ruts_con_jefe = set(
    cj[cj["tiene_eval_jefe"] == "SI"]["rut_key"].unique()
)

# ── Construir tabla ───────────────────────────────────────────────────────────
filas = []

for _, row in pf_520.iterrows():
    rut  = row["rut_key"]
    tipo = row["tipo_formacion"]
    anio = row["anio_evento"]
    per  = row["periodo_evento"] if pd.notna(row["periodo_evento"]) else None

    # Calcular periodos baseline y resultado
    if tipo in ("DIPLOMADO", "PROYECTO"):
        periodos_base, periodos_res = periodos_diplomado(anio)
        periodo_baseline  = f"{int(anio)-1}"
        periodo_resultado = f"{int(anio)+1}"
    elif tipo == "TALLER" and per in TALLER_BASELINE:
        periodos_base = [TALLER_BASELINE[per]]
        periodos_res  = [TALLER_RESULTADO[per]]
        periodo_baseline  = TALLER_BASELINE[per]
        periodo_resultado = TALLER_RESULTADO[per]
    else:
        continue  # taller sin periodo conocido, saltar

    evals_docente = eval_por_docente.get(rut, set())

    tiene_base = any(p in evals_docente for p in periodos_base)
    tiene_res  = any(p in evals_docente for p in periodos_res)
    tiene_jefe = rut in ruts_con_jefe

    filas.append({
        "rut_key":                   rut,
        "tipo_formacion":            tipo,
        "nombre_actividad":          row["nombre_actividad"],
        "anio_evento":               anio,
        "periodo_evento":            per,
        "periodo_baseline":          periodo_baseline,
        "periodo_resultado":         periodo_resultado,
        "tiene_eval_alumnos_baseline":  tiene_base,
        "tiene_eval_alumnos_resultado": tiene_res,
        "tiene_eval_jefe":           tiene_jefe,
        "apto_p3":                   tiene_base and tiene_res,
    })

df = pd.DataFrame(filas)

# Agregar perfil del docente (columnas clave de ambos)
PERFIL_COLS = ["rut_key", "nombre", "departamento", "jerarquia", "nivel_formacion",
               "antiguedad_anios", "clasificacion", "area_carrera", "unidad_facultad",
               "sexo", "tipo_contrato", "fuente"]
df = df.merge(ambos[PERFIL_COLS], on="rut_key", how="left")

# Reordenar: perfil primero, luego evento, luego flags
col_orden = PERFIL_COLS + [c for c in df.columns if c not in PERFIL_COLS]
df = df[col_orden]

# ── Resumen ───────────────────────────────────────────────────────────────────
print(f"\np3_grupo_tratamiento:")
print(f"  Total filas (docente x evento):   {len(df)}")
print(f"  RUTs unicos:                      {df['rut_key'].nunique()}")
print(f"  Aptos para analisis (apto_p3):    {df['apto_p3'].sum()} filas | {df[df['apto_p3']]['rut_key'].nunique()} docentes")
print(f"\nPor tipo de formacion:")
print(df.groupby("tipo_formacion").agg(
    filas=("rut_key","count"),
    docentes=("rut_key","nunique"),
    aptos=("apto_p3","sum")
).to_string())
print(f"\nCon eval jefe:    {df[df['tiene_eval_jefe']]['rut_key'].nunique()} docentes")
print(f"Con eval alumnos baseline:   {df[df['tiene_eval_alumnos_baseline']]['rut_key'].nunique()} docentes")
print(f"Con eval alumnos resultado:  {df[df['tiene_eval_alumnos_resultado']]['rut_key'].nunique()} docentes")

# ── Guardar CSV ───────────────────────────────────────────────────────────────
out_path = os.path.join(OUT, "P3_grupo_tratamiento.csv")
df.to_csv(out_path, index=False, encoding="utf-8-sig")
print(f"\nGuardado: P3_grupo_tratamiento.csv")

# ── Cargar a DB ───────────────────────────────────────────────────────────────
engine = create_engine(DB_URL)
df_db = df.copy()
for col in ["tiene_eval_alumnos_baseline","tiene_eval_alumnos_resultado",
            "tiene_eval_jefe","apto_p3"]:
    df_db[col] = df_db[col].astype(bool)
df_db.to_sql("p3_grupo_tratamiento", engine, schema="analisis", if_exists="replace", index=False)
print("Cargado en DB: p3_grupo_tratamiento")
print("\nListo. Archivos madre no modificados.")
