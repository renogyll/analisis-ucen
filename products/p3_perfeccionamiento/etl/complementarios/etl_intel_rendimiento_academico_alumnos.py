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

Enriquecida 2026-08-01 con más tags de perfil docente (sexo, tramo_edad,
edad_anios, jerarquia — mismo LEFT JOIN, misma razón) y con `aprueba` (booleano,
desde consolidados.catalogo_calificacion) para poder calcular % de aprobación
directo con GROUP BY sin tener que mapear el código de calificación a mano
cada vez. `aprueba` viene NULL para estados administrativos no evaluables
(NP, P, SC, SD — ver consolidados.catalogo_calificacion).

Enriquecida 2026-08-02 con tramo_antiguedad y antiguedad_anios (mismo LEFT JOIN
contra universo_base). tramo_antiguedad viene en la granularidad fina de la fuente
(0-4, 5-9, 10-14, 15-19, 20-24, 25-29, 30+) — el regrupamiento a variantes de
reporte (ej. "15+" o "10+") se hace en cada script de gráfico, no acá, mismo
criterio que tramo_edad.
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

# ── Cargar fuente (+ tags de perfil docente desde universo_base + aprueba desde
#    catalogo_calificacion) ─────────────────────────────────────────────────────
ca = pd.read_sql("""
    SELECT ca.*,
           ub.tipo_contrato_tag,
           ub.sexo,
           ub.tramo_edad,
           ub.edad_anios,
           ub.jerarquia,
           ub.tramo_antiguedad,
           ub.antiguedad_anios,
           cc.aprueba
    FROM consolidados.calificacion_alumno ca
    LEFT JOIN analisis.universo_base ub ON ca.rut_docente = ub.rut_key
    LEFT JOIN consolidados.catalogo_calificacion cc ON ca.calificacion = cc.codigo
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
print(f"  sexo/tramo_edad/jerarquia nulos: {ca['sexo'].isna().sum()}/"
      f"{ca['tramo_edad'].isna().sum()}/{ca['jerarquia'].isna().sum()}")
print(f"  tramo_antiguedad nulos: {ca['tramo_antiguedad'].isna().sum()}")
print(f"  aprueba nulos (NP/P/SC/SD, no evaluable): {ca['aprueba'].isna().sum()}")
n_evaluable = ca["aprueba"].notna().sum()
pct_aprob = 100 * ca["aprueba"].sum() / n_evaluable
print(f"  % aprobación global (sobre {n_evaluable} filas evaluables): {pct_aprob:.1f}%")
print(f"\nPor periodo:")
print(ca.groupby("periodo").agg(
    filas     = ("calificacion_id", "count"),
    docentes  = ("rut_docente",     "nunique"),
    alumnos   = ("rut_alumno",      "nunique"),
    nota_avg  = ("nota",            "mean"),
    pct_aprob = ("aprueba",         "mean"),
).assign(pct_aprob=lambda d: (d["pct_aprob"] * 100).round(1)).round(2).to_string())

# ── Guardar CSV + cargar a DB ─────────────────────────────────────────────────
os.makedirs(OUT, exist_ok=True)
ca.to_csv(f"{OUT}/rendimiento_academico_alumnos.csv", index=False, encoding="utf-8-sig")
ca.to_sql("rendimiento_academico_alumnos", engine, schema="intel", if_exists="replace", index=False)
print("\nCargado: intel.rendimiento_academico_alumnos")
print("Listo.")
