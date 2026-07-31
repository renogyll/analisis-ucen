"""
ETL calificacion_alumno
Fuente: DETALLE DE EVALUACION DE CADA ESTUDIANTE A DOCENTE 3-5-2026 / datos.csv
333,067 filas, 24 columnas originales

Tabla resultante (una fila por registro de nota):
  calificacion_id, periodo, rut_alumno, cod_plan, plan, sede, facultad, cohorte,
  cod_asignatura, nombre_asignatura, seccion, convocatoria,
  calificacion, nota, rut_docente, nombre_docente
"""

import pandas as pd
import os

BASE  = r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO\Downloads\Analisis_UCEN_v2"
SRC   = os.path.join(BASE, "DETALLE DE EVALUACION DE CADA ESTUDIANTE A DOCENTE 3-5-2026",
                     "DETALLE DE EVALUACION DE CADA ESTUDIANTE A DOCENTE 3-5-2026.xlsx - datos.csv")
OUT   = os.path.join(BASE, "PROCESADO")

def strip_dv(serie):
    return (serie.astype(str).str.strip()
            .str.replace(".", "", regex=False)
            .str.split("-").str[0].str.strip())

# ── Cargar fuente ─────────────────────────────────────────────────────────────
df = pd.read_csv(SRC, dtype=str, encoding="latin-1")
df.columns = df.columns.str.strip()
print(f"Fuente cargada: {len(df)} filas")

# ── Normalizar RUTs ───────────────────────────────────────────────────────────
# rut_alumno: columna Rut (sin DV) — aplicamos strip_dv por consistencia
df["rut_alumno"]  = strip_dv(df["Rut"])
# rut_docente: columna 'Rut Docente' (numeros sin DV en la fuente)
df["rut_docente"] = strip_dv(df["Rut Docente"])

# ── Nota numerica ─────────────────────────────────────────────────────────────
df["nota"] = (df["Nota"].astype(str).str.strip()
              .str.replace(",", ".", regex=False)
              .replace("nan", None)
              .pipe(pd.to_numeric, errors="coerce"))

# ── Mapeo por indice posicional (evita conflictos de encoding en nombres acentuados)
# Col 0:Sede 1:Facultad 2:CodPlan 3:Plan 4:Cohorte 5:Rut 6:DV
# 10:Periodo 11:CodAsig 12:Asignatura 13:Seccion 14:Convocatoria
# 15:Calificacion 23:NOMBRE_DOCENTE
C = df.columns.tolist()

out = pd.DataFrame({
    "periodo":           df[C[10]].str.strip(),
    "rut_alumno":        df["rut_alumno"],
    "cod_plan":          df[C[2]].str.strip(),
    "plan":              df[C[3]].str.strip(),
    "sede":              df[C[0]].str.strip(),
    "facultad":          df[C[1]].str.strip(),
    "cohorte":           df[C[4]].str.strip(),
    "cod_asignatura":    df[C[11]].str.strip(),
    "nombre_asignatura": df[C[12]].str.strip(),
    "seccion":           df[C[13]].str.strip(),
    "convocatoria":      df[C[14]].str.strip(),
    "calificacion":      df[C[15]].str.strip(),
    "nota":              df["nota"],
    "rut_docente":       df["rut_docente"],
    "nombre_docente":    df[C[23]].str.strip(),
})

out.insert(0, "calificacion_id", range(1, len(out) + 1))

# ── Guardar ───────────────────────────────────────────────────────────────────
out_path = os.path.join(OUT, "calificacion_alumno.csv")
out.to_csv(out_path, index=False, encoding="utf-8-sig")

print(f"\ncalificacion_alumno.csv generada")
print(f"  Total filas:         {len(out)}")
print(f"  RUTs docente unicos: {out['rut_docente'].nunique()}")
print(f"  RUTs alumno unicos:  {out['rut_alumno'].nunique()}")
print(f"  Nota nulls:          {out['nota'].isna().sum()}")
print(f"\nDistribucion por periodo:")
print(out["periodo"].value_counts().sort_index().to_string())
print(f"\nDistribucion por calificacion:")
print(out["calificacion"].value_counts().to_string())
print(f"\nDistribucion por convocatoria:")
print(out["convocatoria"].value_counts().to_string())
print(f"\nNota promedio global: {out['nota'].mean():.2f}")
print("\nListo. Archivos madre no modificados.")
