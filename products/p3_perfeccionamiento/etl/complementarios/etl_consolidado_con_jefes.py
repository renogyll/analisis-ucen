"""
ETL: consolidados.evaluacion_jefes
Carga el CSV de Evaluación de Jefes a Docentes a la DB.
Una fila por docente × año de evaluación.

FUENTE: EVALUACION DE JEFES A DOCENTES .csv
SALIDA: consolidados.evaluacion_jefes (DB)
        data/cascade/complementarios/evaluacion_jefes.csv

CAMBIO 2026-07-18: reescrito para poblar DB desde CSV fuente.
Anterior versión: solo generaba CSV en PROCESADO/ desde tabla_docente.csv (legacy).
"""
import sys; sys.stdout.reconfigure(encoding="utf-8")
import os
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).parents[2]))
from config import CASCADE

RAW    = Path(r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO\Downloads\Analisis_UCEN_v2\CONSOLIDADO DOCENTES 3-05-2026")
OUT    = os.path.join(CASCADE, "complementarios")
DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"
engine = create_engine(DB_URL)

def strip_dv(serie):
    return (serie.astype(str).str.strip()
            .str.replace(".", "", regex=False)
            .str.upper()
            .str.split("-").str[0]
            .str.rstrip("Kk")
            .str.strip())

# ── Cargar CSV fuente ─────────────────────────────────────────────────────────
csv_path = RAW / "CONSOLIDADO DOCENTES 3-05-2026.xlsx - EVALUACION DE JEFES A DOCENTES .csv"
df = pd.read_csv(csv_path, dtype=str, encoding="latin-1")
df.columns = df.columns.str.strip()

print(f"CSV cargado: {len(df)} filas | columnas: {list(df.columns)}")

# ── Normalizar ────────────────────────────────────────────────────────────────
df["rut_key"]        = strip_dv(df["RUT ACADEMICO"])
df["anio_evaluacion"] = df["PERIODO"].str.strip()
df["nombre_docente"] = df["DOCENTE"].str.strip() if "DOCENTE" in df.columns else None
df["concepto"]       = df["CONCEPTO"].str.strip() if "CONCEPTO" in df.columns else None
df["tiene_eval_jefe"] = "SI"

# Mapeo de columnas numéricas
col_map = {
    "PORCENTAJE CONCEPTO": "porcentaje_concepto",
    "CUMPLIMIENTO CD":     "cumplimiento_cd",
    "EDD":                 "edd_total",
    "EDD Director":        "edd_director",
    "EDD Docente":         "edd_docente",
    "ACTIVO EN UCEN":      "activo_ucen",
    "FACULTAD":            "facultad_jefe",
    "CARRERA":             "carrera_jefe",
    "SEDE":                "sede_jefe",
    "COD_OBSERVACION":     "cod_observacion",
}
for src, dst in col_map.items():
    if src in df.columns:
        df[dst] = df[src].str.strip() if df[src].dtype == object else df[src]

# Columnas finales
cols = ["rut_key", "anio_evaluacion", "nombre_docente", "tiene_eval_jefe",
        "concepto", "porcentaje_concepto", "cumplimiento_cd",
        "edd_total", "edd_director", "edd_docente",
        "activo_ucen", "facultad_jefe", "carrera_jefe", "sede_jefe", "cod_observacion"]
cols_disp = [c for c in cols if c in df.columns]
out = df[cols_disp].copy()

# Excluir ESPINOZA
out = out[out["rut_key"] != "16322128"]

# Dedup rut × año (en caso de duplicados, keep first)
out = out.drop_duplicates(subset=["rut_key", "anio_evaluacion"], keep="first")

print(f"\nevaluacion_jefes: {len(out)} filas | {out['rut_key'].nunique()} docentes únicos")
print(f"Años: {sorted(out['anio_evaluacion'].dropna().unique())}")
print(f"Conceptos:\n{out['concepto'].value_counts(dropna=False).to_string()}")

# ── Guardar ───────────────────────────────────────────────────────────────────
os.makedirs(OUT, exist_ok=True)
out.to_sql("evaluacion_jefes", engine, schema="consolidados", if_exists="replace", index=False)
out.to_csv(os.path.join(OUT, "evaluacion_jefes.csv"), index=False, encoding="utf-8-sig")
print(f"\nDB : consolidados.evaluacion_jefes  ({len(out)} filas)")
print(f"CSV: {OUT}/evaluacion_jefes.csv")
