"""
ETL: Incorporar talleres 2025 desde CERTIFICACION OFERTA FORMATIVA 2025.xlsx
Fuente: data/raw/consolidado_docentes/CERTIFICACION OFERTA FORMATIVA 2025.xlsx
Output: INSERT INTO consolidados.participacion_formacion (2025-01 y 2025-02)

Semestre 1 -> periodo_evento = 2025-01
Semestre 2 -> periodo_evento = 2025-02
Tipos PEI y Perfil Docente -> tipo_formacion = TALLER
"""
import sys; sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text

ROOT = Path(__file__).parents[4]
XLSX = ROOT / "data/raw/consolidado_docentes/CERTIFICACION OFERTA FORMATIVA 2025.xlsx"

DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"
engine = create_engine(DB_URL)

# ── Verificar si ya existe data 2025 en la tabla ─────────────────────────────
with engine.connect() as c:
    n_exist = c.execute(text(
        "SELECT COUNT(*) FROM consolidados.participacion_formacion "
        "WHERE tipo_formacion='TALLER' AND anio_evento='2025'"
    )).scalar()
    if n_exist > 0:
        print(f"Ya existen {n_exist} filas TALLER 2025 en la BD. Saliendo sin insertar duplicados.")
        sys.exit(0)

# ── Leer xlsx ────────────────────────────────────────────────────────────────
df = pd.read_excel(XLSX, dtype=str)
df.columns = df.columns.str.strip()
print(f"Leídas {len(df)} filas de {XLSX.name}")
print(f"Semestres: {df['Semestre'].unique()}")
print(f"Tipos: {df['Tipo'].unique()}")

# ── Normalizar RUT: quitar guión y dígito verificador ────────────────────────
df["rut_key"] = (df["RUT"].astype(str).str.strip()
                 .str.replace(".", "", regex=False)
                 .str.split("-").str[0].str.strip())

# ── Mapear semestre a periodo_evento ─────────────────────────────────────────
df["periodo_evento"] = df["Semestre"].map({"1": "2025-01", "2": "2025-02"})
df["anio_evento"]    = "2025"
df["tipo_formacion"] = "TALLER"

# ── Nombre docente completo ───────────────────────────────────────────────────
nombre_cols = [c for c in ["Nombre", "1er Apellido", "2do Apellido"] if c in df.columns]
df["nombre_docente"] = df[nombre_cols].fillna("").agg(" ".join, axis=1).str.strip()

# ── Renombrar columnas ────────────────────────────────────────────────────────
df = df.rename(columns={
    "Taller":     "nombre_actividad",
    "Facultad":   "facultad",
    "Carrera":    "carrera",
    "Sede":       "sede",
    "Jerarquía":  "jerarquia_evento",
    "Contrato":   "contrato_evento",
})
df["linea_proyecto"] = None

COLS = ["rut_key","tipo_formacion","periodo_evento","anio_evento",
        "nombre_docente","nombre_actividad","facultad","carrera","sede",
        "jerarquia_evento","contrato_evento","linea_proyecto"]
out = df[COLS].copy()

print(f"\nFilas a insertar: {len(out)}")
print(f"RUTs únicos: {out['rut_key'].nunique()}")
print(f"Por periodo:\n{out['periodo_evento'].value_counts().to_string()}")

# ── Verificar cuántos RUTs están en el universo base ────────────────────────
with engine.connect() as c:
    ub = pd.read_sql(text("SELECT rut_key FROM analisis.universo_base"), c)

ruts_base = set(ub["rut_key"].astype(str).str.strip())
en_base = out["rut_key"].isin(ruts_base).sum()
print(f"\nFilas con RUT en universo_base: {en_base} / {len(out)}")
print(f"RUTs únicos en universo_base: {out[out['rut_key'].isin(ruts_base)]['rut_key'].nunique()}")

# ── Insertar ─────────────────────────────────────────────────────────────────
out.to_sql("participacion_formacion", engine, schema="consolidados",
           if_exists="append", index=False)
print(f"\nInsertadas {len(out)} filas en consolidados.participacion_formacion")
print("Listo. Ahora re-ejecutar: python etl/04_formados_p3/etl_formados_p3.py")
