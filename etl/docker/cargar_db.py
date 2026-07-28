"""
Carga todos los CSV de PROCESADO a PostgreSQL (ucen_db).
Crea las tablas automaticamente con tipos correctos.
Sin FK constraints en esta carga — agregar despues de validar integridad.

Requiere: pip install sqlalchemy psycopg2-binary pandas
"""

import pandas as pd
from sqlalchemy import create_engine, text
import os, time

PROCESADO = r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO\Downloads\Analisis_UCEN_v2\PROCESADO"
DB_URL    = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"

# (schema, nombre_tabla, archivo_csv, columnas_date, columnas_numeric)
TABLAS = [
    # ── consolidados ──────────────────────────────────────────────────────────
    ("consolidados", "docente", "tabla_docente.csv",
     ["fecha_ingreso", "fecha_retiro", "fecha_nacimiento"],
     ["antiguedad_anios", "edad_anios"]),

    ("consolidados", "pregunta", "tabla_pregunta.csv", [], []),

    ("consolidados", "catalogo_calificacion", "catalogo_calificacion.csv", [], []),

    ("consolidados", "evaluacion_periodo", "evaluacion_periodo.csv", [],
     ["total_alumnos_evaluar", "n_alumnos_evaluaron", "cobertura_pct"]),

    ("consolidados", "evaluacion_respuesta", "evaluacion_respuesta.csv", [],
     ["pct_acuerdo", "pct_indiferente", "pct_desacuerdo",
      "pct_si", "pct_no", "nota_promedio"]),

    ("consolidados", "calificacion_alumno", "calificacion_alumno.csv", [],
     ["nota"]),

    ("consolidados", "participacion_formacion",
     "P3_participacion_formacion_todos.csv", [], []),

    ("consolidados", "consolidado_jefes",
     "P1_consolidado_con_evaluacion_jefes.csv",
     ["fecha_ingreso", "fecha_retiro", "fecha_nacimiento"],
     ["antiguedad_anios", "edad_anios", "cumplimiento_cd",
      "edd_total", "edd_director", "edd_docente", "porcentaje_concepto"]),

    # ── analisis ──────────────────────────────────────────────────────────────
    ("analisis", "docente_ambos", "docente_ambos.csv",
     ["fecha_ingreso", "fecha_retiro", "fecha_nacimiento"],
     ["antiguedad_anios", "edad_anios"]),

    ("analisis", "docente_solo_nomina", "docente_solo_nomina.csv",
     ["fecha_ingreso", "fecha_retiro", "fecha_nacimiento"],
     ["antiguedad_anios", "edad_anios"]),

    ("analisis", "docente_solo_dotacion", "docente_solo_dotacion.csv",
     ["fecha_ingreso", "fecha_retiro", "fecha_nacimiento"],
     ["antiguedad_anios", "edad_anios"]),

    ("analisis", "docente_solo_evaluaciones", "docente_solo_evaluaciones.csv",
     ["fecha_ingreso", "fecha_retiro", "fecha_nacimiento"],
     ["antiguedad_anios", "edad_anios"]),

    ("analisis", "grupo_control_p3",
     "P3_docentes_perfil_completo_sinformacion.csv",
     ["fecha_ingreso", "fecha_retiro", "fecha_nacimiento"],
     ["antiguedad_anios", "edad_anios"]),

    ("analisis", "resumen_participacion", "P3_resumen_participacion.csv", [],
     ["total_registros", "ruts_unicos"]),

    ("analisis", "p3_grupo_tratamiento", "P3_grupo_tratamiento.csv", [],
     ["antiguedad_anios"]),

    # ── intel ─────────────────────────────────────────────────────────────────
    ("intel", "pre_during_post_sat", "intel_pre_during_post_sat.csv", [],
     ["nota_pre", "nota_durante", "nota_post",
      "delta_pre_post", "delta_pre_durante", "antiguedad_anios"]),

    ("intel", "pre_post_sat", "intel_pre_post_sat.csv", [],
     ["nota_1", "nota_durante", "nota_2",
      "delta_pre_post", "delta_pre_durante", "antiguedad_anios"]),

    ("intel", "notas_docente", "intel_notas_docente.csv", [],
     ["nota"]),
]

def cargar_tabla(engine, schema, nombre, archivo, cols_date, cols_numeric):
    path = os.path.join(PROCESADO, archivo)
    df = pd.read_csv(path, dtype=str, encoding="utf-8-sig")

    for col in cols_date:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    for col in cols_numeric:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in df.columns:
        if df[col].dropna().isin(["True","False","true","false"]).all():
            df[col] = df[col].map({"True": True, "False": False,
                                   "true": True, "false": False})

    df.to_sql(nombre, engine, schema=schema, if_exists="replace", index=False)
    print(f"  OK  {schema}.{nombre:<35} {len(df):>7} filas")

# ── Conectar ──────────────────────────────────────────────────────────────────
print("Conectando a PostgreSQL...")
engine = create_engine(DB_URL)

# Esperar hasta 30s si el contenedor acaba de arrancar
for intento in range(6):
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("Conexion OK\n")
        break
    except Exception:
        print(f"  Esperando DB... ({intento+1}/6)")
        time.sleep(5)

# ── Crear schemas ─────────────────────────────────────────────────────────────
with engine.begin() as conn:
    for s in ["consolidados", "analisis", "intel"]:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {s}"))

# ── Cargar ────────────────────────────────────────────────────────────────────
print("Cargando tablas:")
for schema, nombre, archivo, cols_date, cols_num in TABLAS:
    try:
        cargar_tabla(engine, schema, nombre, archivo, cols_date, cols_num)
    except Exception as e:
        print(f"  ERROR {schema}.{nombre}: {e}")

print("\nCarga completa.")
print("Conectar DBeaver: host=localhost port=5432 db=ucen user=ucen_user pass=ucen2026")
