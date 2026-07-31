"""
ETL: scatter_sat_notas.csv
Una fila por docente × período × sección (asignatura).
Combina SAT docente con nota promedio y % aprobación de sus alumnos.

Universo: analisis.universo_base (1,144 RUTs).
  formado = True  → en analisis.universo_formados_p3 (419 RUTs)
  formado = False → resto del universo_base sin formación (~725)

SALIDA: data/cascade/complementarios/scatter_sat_notas.csv
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
COMP   = os.path.join(CASCADE, "complementarios")
os.makedirs(COMP, exist_ok=True)

# ── Cargar fuentes ────────────────────────────────────────────────────────────
with engine.connect() as conn:
    # RUTs universo_base
    base = pd.read_sql(text("SELECT rut_key FROM analisis.universo_base"), conn)

    # Formados (tratamiento)
    form = pd.read_sql(text("SELECT DISTINCT rut_key FROM analisis.universo_formados_p3"), conn)

    # Notas de alumnos por docente × período × asignatura
    notas = pd.read_sql(text("""
        SELECT rut_docente,
               periodo,
               cod_asignatura,
               nombre_asignatura,
               facultad,
               ROUND(AVG(nota)::numeric, 3)                    AS nota_promedio,
               COUNT(*)                                         AS n_alumnos,
               ROUND(AVG(CASE WHEN nota >= 4 THEN 1 ELSE 0 END)::numeric * 100, 1) AS pct_aprobacion
        FROM intel.notas_docente
        WHERE nota IS NOT NULL
        GROUP BY rut_docente, periodo, cod_asignatura, nombre_asignatura, facultad
    """), conn)

    # SAT ponderado por docente × período (CM-1: cob>=40%, CM-2: pond. por n_alumnos)
    sat_raw = pd.read_sql(text("""
        SELECT e.rut_docente,
               e.periodo,
               SUM(r.nota_promedio * e.n_alumnos_evaluaron) AS sat_pond,
               SUM(e.n_alumnos_evaluaron)                   AS n_alumnos_sat
        FROM consolidados.evaluacion_periodo e
        JOIN consolidados.evaluacion_respuesta r ON r.evaluacion_id = e.evaluacion_id
        WHERE r.pregunta_id = 'SAT_NOTA'
          AND e.cobertura_pct >= 40
          AND r.nota_promedio IS NOT NULL
        GROUP BY e.rut_docente, e.periodo
    """), conn)

ruts_base   = set(base["rut_key"].astype(str).str.strip())
ruts_form   = set(form["rut_key"].astype(str).str.strip())
notas["rut_docente"] = notas["rut_docente"].astype(str).str.strip()
sat_raw["rut_docente"] = sat_raw["rut_docente"].astype(str).str.strip()

print(f"universo_base:  {len(ruts_base)}")
print(f"Formados:       {len(ruts_form)}")
print(f"notas filas:    {len(notas):,}  | RUTs: {notas['rut_docente'].nunique()}")
print(f"SAT filas:      {len(sat_raw):,} | RUTs: {sat_raw['rut_docente'].nunique()}")

# ── SAT ponderado ──────────────────────────────────────────────────────────────
sat_raw["sat"] = (sat_raw["sat_pond"] / sat_raw["n_alumnos_sat"]).round(3)
sat_per = sat_raw[["rut_docente","periodo","sat"]]

# ── Filtrar notas al universo_base y unir con SAT ─────────────────────────────
notas_base = notas[notas["rut_docente"].isin(ruts_base)].copy()

# Excluir secciones subjetivas o sin sentido comparativo
EXCLUIR = ["PRACTICA","PRÁCTICA","PROYECTO DE TIT","SEMINARIO",
           "CICLO FORMATIVO","INTEGRACION PROFESIONAL","INTEGRACIÓN PROFESIONAL"]
mask = notas_base["nombre_asignatura"].apply(
    lambda n: any(p in str(n).upper() for p in EXCLUIR) if pd.notna(n) else True
)
notas_base = notas_base[~mask]
notas_base = notas_base[notas_base["n_alumnos"] >= 7]  # mínimo 7 alumnos por sección

notas_sat = notas_base.merge(sat_per, on=["rut_docente","periodo"], how="inner")

# Marcar si es formado
notas_sat["formado"] = notas_sat["rut_docente"].isin(ruts_form)

# ── Seleccionar columnas de salida ────────────────────────────────────────────
out = notas_sat[["rut_docente","periodo","nota_promedio","pct_aprobacion","sat","formado"]].copy()
out = out.dropna(subset=["nota_promedio","sat"])

# ── Resumen ───────────────────────────────────────────────────────────────────
print(f"\n{'='*55}")
print(f"SCATTER SAT × NOTAS ALUMNOS — RESUMEN")
print(f"{'='*55}")
print(f"Filas totales:            {len(out):,}")
print(f"RUTs únicos:              {out['rut_docente'].nunique()}")
print(f"  - formado=True:         {out[out['formado']]['rut_docente'].nunique()}")
print(f"  - formado=False:        {out[~out['formado']]['rut_docente'].nunique()}")
print(f"\nPor período:")
print(out.groupby("periodo").agg(
    filas=("rut_docente","count"),
    ruts=("rut_docente","nunique"),
    form_pct=("formado","mean"),
    nota_prom=("nota_promedio","mean"),
    aprobacion=("pct_aprobacion","mean")
).round(2).to_string())
print(f"\nNota promedio formados:   {out[out['formado']]['nota_promedio'].mean():.3f}")
print(f"Nota promedio control:    {out[~out['formado']]['nota_promedio'].mean():.3f}")
print(f"Aprobación formados (%):  {out[out['formado']]['pct_aprobacion'].mean():.1f}%")
print(f"Aprobación control (%):   {out[~out['formado']]['pct_aprobacion'].mean():.1f}%")

# ── Guardar ───────────────────────────────────────────────────────────────────
out_path = os.path.join(COMP, "scatter_sat_notas.csv")
out.to_csv(out_path, index=False, encoding="utf-8-sig")
print(f"\nGuardado: {out_path}  ({len(out):,} filas)")
