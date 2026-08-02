"""
ETL intel.evaluacion_jefes
Copia de consolidados.evaluacion_jefes (evaluación de desempeño docente — EDD —
hecha por la jefatura/director) enriquecida con tags de perfil docente, mismo
patrón que intel.rendimiento_academico_alumnos (ver
products/p3_perfeccionamiento/etl/complementarios/etl_intel_rendimiento_academico_alumnos.py
y docs/DECISIONES_METODOLOGICAS.md D26).

Granularidad: 1 fila por docente × año de evaluación (rut_key + anio_evaluacion).
1.646 filas, 604 docentes únicos, años 2022-2025.

Tags agregados vía LEFT JOIN contra analisis.universo_base por rut_key:
  - tipo_contrato_tag (JORNADA/HONORARIO)
  - sexo
  - jerarquia (normalizada, ver D25)

NO se agrega facultad por join — consolidados.evaluacion_jefes YA trae
`facultad_jefe` con 100% de cobertura (6 códigos: FAMEDSA, FINARQ, FED, FEGOC,
FACDEH, VRIIP), mejor cobertura que la de universo_base (1.374/1.646, 83.5%).
Usar esa columna directo, no inventar una nueva.

Cobertura de los tags nuevos (sobre 1.646 filas): tipo_contrato_tag 1.456 (88.5%),
sexo 1.446 (87.8%), jerarquia 1.449 (88.0%). El resto son docentes fuera del
universo_base actual (retirados u otros casos no cubiertos).

Columnas numéricas vienen como texto en la fuente (edd_total, edd_director,
edd_docente, cumplimiento_cd, porcentaje_concepto) — se castean acá a numérico
(errors="coerce") para no repetir esa conversión en cada script consumidor,
mismo criterio que `nota` en etl_intel_rendimiento_academico_alumnos.py.
"""

import sys, os
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from config import DATA_STAGING

OUT    = DATA_STAGING
DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"

engine = create_engine(DB_URL)

# ── Cargar fuente + tags de perfil docente desde universo_base ────────────────
ej = pd.read_sql("""
    SELECT ej.*,
           ub.tipo_contrato_tag,
           ub.sexo,
           ub.jerarquia
    FROM consolidados.evaluacion_jefes ej
    LEFT JOIN analisis.universo_base ub ON ej.rut_key = ub.rut_key
""", engine)
print(f"evaluacion_jefes original: {len(ej)} filas | {ej['rut_key'].nunique()} docentes")

# ── Castear columnas numéricas (vienen como texto en la fuente) ───────────────
for col in ["edd_total", "edd_director", "edd_docente", "cumplimiento_cd", "porcentaje_concepto"]:
    ej[col] = pd.to_numeric(ej[col], errors="coerce")

# ── Resumen ───────────────────────────────────────────────────────────────────
print(f"\nintel.evaluacion_jefes:")
print(f"  Filas:            {len(ej)}")
print(f"  Docentes únicos:  {ej['rut_key'].nunique()}")
print(f"  Años:             {sorted(ej['anio_evaluacion'].dropna().unique().tolist())}")
print(f"  tipo_contrato_tag/sexo/jerarquia nulos: "
      f"{ej['tipo_contrato_tag'].isna().sum()}/{ej['sexo'].isna().sum()}/{ej['jerarquia'].isna().sum()}")
print(f"  facultad_jefe nulos: {ej['facultad_jefe'].isna().sum()}")
print(f"\nPor año:")
print(ej.groupby("anio_evaluacion").agg(
    filas    = ("rut_key",     "count"),
    docentes = ("rut_key",     "nunique"),
    edd_total_avg = ("edd_total", "mean"),
).round(2).to_string())

# ── Guardar CSV + cargar a DB ─────────────────────────────────────────────────
os.makedirs(OUT, exist_ok=True)
ej.to_csv(f"{OUT}/evaluacion_jefes.csv", index=False, encoding="utf-8-sig")
ej.to_sql("evaluacion_jefes", engine, schema="intel", if_exists="replace", index=False)
print("\nCargado: intel.evaluacion_jefes")
print("Listo.")
