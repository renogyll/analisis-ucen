"""
ETL: P1_docente_consolidado + EVALUACION DE JEFES (formato largo)
Output: P1_consolidado_con_evaluacion_jefes.csv
  - Una fila por docente x año_evaluacion
  - Perfil completo (nomina + dotacion) repetido en cada fila
  - Columnas de evaluacion de jefe al lado derecho: anio_evaluacion, concepto, ratios
  - Docentes sin ninguna evaluacion aparecen con 1 fila y campos jefe vacios
"""

import pandas as pd
import os

BASE  = r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO\Downloads\Analisis_UCEN_v2"
DOCS  = os.path.join(BASE, "CONSOLIDADO DOCENTES 3-05-2026")
OUT   = os.path.join(BASE, "PROCESADO")

def strip_dv(serie):
    return (serie.astype(str).str.strip()
            .str.replace(".", "", regex=False)
            .str.split("-").str[0].str.strip())

# ── Cargar base maestra (tabla_docente — fuentes NOMINA y NOMINA_DOTACION) ────
td = pd.read_csv(os.path.join(OUT, "tabla_docente.csv"), dtype=str)
td.columns = td.columns.str.strip()
base = td[td["fuente"].isin(["NOMINA_DOTACION", "NOMINA"])].copy()
print(f"Base tabla_docente (NOMINA+NOMINA_DOTACION): {len(base)} filas | {base['rut_key'].nunique()} RUTs unicos")

# ── Cargar EVALUACION JEFES ───────────────────────────────────────────────────
jefes = pd.read_csv(
    os.path.join(DOCS, "CONSOLIDADO DOCENTES 3-05-2026.xlsx - EVALUACION DE JEFES A DOCENTES .csv"),
    dtype=str
)
jefes.columns = jefes.columns.str.strip()
jefes["rut_key"] = strip_dv(jefes["RUT ACADEMICO"])
jefes["PERIODO"] = jefes["PERIODO"].str.strip()

print(f"Evaluacion jefes:   {len(jefes)} filas | {jefes['rut_key'].nunique()} RUTs unicos")
print(f"Periodos: {sorted(jefes['PERIODO'].unique())}")
print(f"Conceptos: {jefes['CONCEPTO'].value_counts().to_dict()}")

# ── Columnas clave a pivotar ──────────────────────────────────────────────────
COLS_JEFE = {
    "CONCEPTO":            "concepto",
    "PORCENTAJE CONCEPTO": "porcentaje_concepto",
    "CUMPLIMIENTO CD":     "cumplimiento_cd",
    "EDD":                 "edd_total",
    "EDD Director":        "edd_director",
    "EDD Docente":         "edd_docente",
    "ACTIVO EN UCEN":      "activo_ucen",
    "FACULTAD":            "facultad_jefe",
    "CARRERA":             "carrera_jefe",
    "SEDE":                "sede_jefe",
    "OBSERVACIÓN":    "observacion_jefe",
    "COD_OBSERVACION":     "cod_observacion",
}

jefes_slim = jefes[["rut_key", "PERIODO"] + list(COLS_JEFE.keys())].copy()
jefes_slim = jefes_slim.rename(columns={**COLS_JEFE, "PERIODO": "anio_evaluacion"})
# si hay duplicados rut+año (raro), quedarse con el primero
jefes_slim = jefes_slim.drop_duplicates(subset=["rut_key", "anio_evaluacion"], keep="first")

print(f"\nJefes formato largo: {len(jefes_slim)} filas | {jefes_slim['rut_key'].nunique()} RUTs unicos")

# ── JOIN largo: base LEFT con jefes ──────────────────────────────────────────
# Docentes sin evaluacion quedan con 1 fila y campos jefe vacios
resultado = base.merge(jefes_slim, on="rut_key", how="left")

# Flag legible
resultado["tiene_eval_jefe"] = resultado["anio_evaluacion"].notna().map({True: "SI", False: "NO"})

# Ordenar: perfil primero, luego año, luego ratios
cols_perfil = [c for c in base.columns]
cols_jefe   = ["anio_evaluacion", "tiene_eval_jefe", "concepto", "porcentaje_concepto",
               "cumplimiento_cd", "edd_total", "edd_director", "edd_docente",
               "activo_ucen", "facultad_jefe", "carrera_jefe", "sede_jefe",
               "observacion_jefe", "cod_observacion"]
resultado = resultado[cols_perfil + cols_jefe]

ruts_con = resultado[resultado["tiene_eval_jefe"] == "SI"]["rut_key"].nunique()
ruts_sin = resultado[resultado["tiene_eval_jefe"] == "NO"]["rut_key"].nunique()
print(f"\nResultado final: {len(resultado)} filas | {len(resultado.columns)} columnas")
print(f"  Docentes con al menos 1 evaluacion jefe: {ruts_con}")
print(f"  Docentes sin ninguna evaluacion jefe:    {ruts_sin}")
print("\nDistribucion por concepto:")
print(resultado["concepto"].value_counts(dropna=False).to_string())

# ── Guardar ───────────────────────────────────────────────────────────────────
out_path = os.path.join(OUT, "P1_consolidado_con_evaluacion_jefes.csv")
resultado.to_csv(out_path, index=False, encoding="utf-8-sig")
print(f"\nGuardado: P1_consolidado_con_evaluacion_jefes.csv")
print("Listo. Archivos madre no modificados.")
