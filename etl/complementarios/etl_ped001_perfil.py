"""
PED-001 — Variables derivadas sobre los 520 (docente_ambos)

Nuevas columnas agregadas a analisis.docente_ambos:
  tramo_edad           : edad_anios en tramos de 5 años
  tramo_antiguedad     : antiguedad_anios en tramos de 5 años
  anio_ingreso         : año de fecha_ingreso
  anio_jerarquizacion  : año de fecha_jerarquizacion (texto M/D/YYYY)
  sexo                 : recodificado a HOMBRE / MUJER
"""

import pandas as pd
from sqlalchemy import create_engine

DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"
engine = create_engine(DB_URL)

df = pd.read_sql("SELECT * FROM analisis.docente_ambos", engine)
print(f"docente_ambos: {len(df)} filas")

# ── sexo ─────────────────────────────────────────────────────────────────────
df["sexo"] = df["sexo"].map({"MASCULINO": "HOMBRE", "FEMENINO": "MUJER"})
print(f"sexo:  {df['sexo'].value_counts().to_dict()}")

# ── anio_ingreso ──────────────────────────────────────────────────────────────
df["anio_ingreso"] = pd.to_datetime(df["fecha_ingreso"], errors="coerce").dt.year
print(f"anio_ingreso nulos: {df['anio_ingreso'].isna().sum()}")

# ── anio_jerarquizacion ───────────────────────────────────────────────────────
df["anio_jerarquizacion"] = (
    pd.to_datetime(df["fecha_jerarquizacion"], format="%m/%d/%Y", errors="coerce")
    .dt.year
)
print(f"anio_jerarquizacion nulos: {df['anio_jerarquizacion'].isna().sum()}")

# ── tramo_edad ────────────────────────────────────────────────────────────────
bins_edad   = [0, 30, 35, 40, 45, 50, 55, 60, 65, 70, 200]
labels_edad = ["<30","30-34","35-39","40-44","45-49","50-54","55-59","60-64","65-69","70+"]
df["tramo_edad"] = pd.cut(df["edad_anios"], bins=bins_edad, labels=labels_edad, right=False)
print(f"\ntramo_edad:\n{df['tramo_edad'].value_counts().sort_index().to_string()}")

# ── tramo_antiguedad ──────────────────────────────────────────────────────────
bins_ant   = [0, 5, 10, 15, 20, 25, 30, 200]
labels_ant = ["0-4","5-9","10-14","15-19","20-24","25-29","30+"]
df["tramo_antiguedad"] = pd.cut(df["antiguedad_anios"], bins=bins_ant, labels=labels_ant, right=False)
print(f"\ntramo_antiguedad:\n{df['tramo_antiguedad'].value_counts().sort_index().to_string()}")

# ── Guardar ───────────────────────────────────────────────────────────────────
df.to_sql("docente_ambos", engine, schema="analisis", if_exists="replace", index=False)
print("\nActualizado: analisis.docente_ambos")

OUT = r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO\Downloads\Analisis_UCEN_v2\PROCESADO"
df.to_csv(f"{OUT}/docente_ambos.csv", index=False, encoding="utf-8-sig")
print("Guardado: docente_ambos.csv")
print("\nPED-001 completado.")
