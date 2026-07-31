"""
ETL intel.rendimiento_academico_alumnos
Copia limpia de consolidados.calificacion_alumno con RUTs válidos.
Excluye registros placeholder (Sin Docente, POR DESIGNAR, etc.) donde
rut_docente tiene menos de 7 dígitos.

330.578 filas — granularidad individual por alumno, sin agregación.
calificacion_id es la clave natural de cada fila.

Renombrada 2026-07-30 desde intel.notas_docente / etl_intel_notas_docente.py:
el nombre anterior era engañoso (son notas de ALUMNOS agrupadas por sección
de cada docente, no notas que le pusieron al docente).

Enriquecida 2026-07-30 con tipo_contrato_tag (JORNADA/HONORARIO) vía LEFT JOIN
contra analisis.universo_base, para poder filtrar/agrupar por modalidad de
contrato sin tener que hacer el join a mano cada vez.
"""

import sys, os
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from config import DATA_STAGING

OUT    = DATA_STAGING
DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"

engine = create_engine(DB_URL)

# ── Cargar fuente (+ tipo_contrato_tag desde universo_base) ────────────────────
ca = pd.read_sql("""
    SELECT ca.*, ub.tipo_contrato_tag
    FROM consolidados.calificacion_alumno ca
    LEFT JOIN analisis.universo_base ub ON ca.rut_docente = ub.rut_key
""", engine)
print(f"calificacion_alumno original: {len(ca)} filas | {ca['rut_docente'].nunique()} docentes")

# Excluir placeholders (Sin Docente, POR DESIGNAR, Acta Manual, etc.)
mask_invalido = ca["rut_docente"].str.len() < 7
print(f"  Excluidas (rut placeholder): {mask_invalido.sum()} filas")
ca = ca[~mask_invalido].copy()
print(f"  Válidas:                     {len(ca)} filas | {ca['rut_docente'].nunique()} docentes")

# ── Resumen ───────────────────────────────────────────────────────────────────
ca["nota"] = pd.to_numeric(ca["nota"], errors="coerce")

print(f"\nintel.rendimiento_academico_alumnos:")
print(f"  Filas:            {len(ca)}")
print(f"  Docentes únicos:  {ca['rut_docente'].nunique()}")
print(f"  Alumnos únicos:   {ca['rut_alumno'].nunique()}")
print(f"  Periodos:         {sorted(ca['periodo'].dropna().unique().tolist())}")
print(f"  tipo_contrato_tag nulos: {ca['tipo_contrato_tag'].isna().sum()}")
print(f"\nPor periodo:")
print(ca.groupby("periodo").agg(
    filas     = ("calificacion_id", "count"),
    docentes  = ("rut_docente",     "nunique"),
    alumnos   = ("rut_alumno",      "nunique"),
    nota_avg  = ("nota",            "mean"),
).round(2).to_string())

# ── Guardar CSV + cargar a DB ─────────────────────────────────────────────────
os.makedirs(OUT, exist_ok=True)
ca.to_csv(f"{OUT}/rendimiento_academico_alumnos.csv", index=False, encoding="utf-8-sig")
ca.to_sql("rendimiento_academico_alumnos", engine, schema="intel", if_exists="replace", index=False)
print("\nCargado: intel.rendimiento_academico_alumnos")
print("Listo.")
