"""
ETL intel.notas_docente
Copia limpia de consolidados.calificacion_alumno con RUTs válidos.
Excluye registros placeholder (Sin Docente, POR DESIGNAR, etc.) donde
rut_docente tiene menos de 7 dígitos.

330.578 filas — granularidad individual por alumno, sin agregación.
calificacion_id es la clave natural de cada fila.
"""

import pandas as pd
from sqlalchemy import create_engine

OUT    = r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO\Downloads\Analisis_UCEN_v2\PROCESADO"
DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"

engine = create_engine(DB_URL)

# ── Cargar fuente ─────────────────────────────────────────────────────────────
ca = pd.read_sql("SELECT * FROM consolidados.calificacion_alumno", engine)
print(f"calificacion_alumno original: {len(ca)} filas | {ca['rut_docente'].nunique()} docentes")

# Excluir placeholders (Sin Docente, POR DESIGNAR, Acta Manual, etc.)
mask_invalido = ca["rut_docente"].str.len() < 7
print(f"  Excluidas (rut placeholder): {mask_invalido.sum()} filas")
ca = ca[~mask_invalido].copy()
print(f"  Válidas:                     {len(ca)} filas | {ca['rut_docente'].nunique()} docentes")

# ── Resumen ───────────────────────────────────────────────────────────────────
ca["nota"] = pd.to_numeric(ca["nota"], errors="coerce")

print(f"\nintel.notas_docente:")
print(f"  Filas:            {len(ca)}")
print(f"  Docentes únicos:  {ca['rut_docente'].nunique()}")
print(f"  Alumnos únicos:   {ca['rut_alumno'].nunique()}")
print(f"  Periodos:         {sorted(ca['periodo'].dropna().unique().tolist())}")
print(f"\nPor periodo:")
print(ca.groupby("periodo").agg(
    filas     = ("calificacion_id", "count"),
    docentes  = ("rut_docente",     "nunique"),
    alumnos   = ("rut_alumno",      "nunique"),
    nota_avg  = ("nota",            "mean"),
).round(2).to_string())

# ── Guardar CSV + cargar a DB ─────────────────────────────────────────────────
ca.to_csv(f"{OUT}/intel_notas_docente.csv", index=False, encoding="utf-8-sig")
ca.to_sql("notas_docente", engine, schema="intel", if_exists="replace", index=False)
print("\nCargado: intel.notas_docente")
print("Listo.")
