"""
ETL Capa 2 - Participacion en formacion docente
Fuentes: Diplomados 2022-2025, Talleres 2023_2 / 2024_1, Proyectos Investigacion
Output:
  P3_participacion_formacion.csv  -> una fila por docente x actividad
  P3_docentes_perfil_completo_sinformacion.csv -> grupo control (520 AMBOS sin formacion, con evaluaciones)
  P3_resumen_participacion.csv    -> conteos por tipo y anio para la contraparte
"""

import pandas as pd
import os

BASE   = r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO\Downloads\Analisis_UCEN_v2"
DOCS   = os.path.join(BASE, "CONSOLIDADO DOCENTES 3-05-2026")
EVALS  = os.path.join(BASE, "CONSOLIDADO EVALUACION ESTUDIANTES UCEN 3-5-2026")
OUT    = os.path.join(BASE, "PROCESADO")

def strip_dv(serie):
    return (serie.astype(str).str.strip()
            .str.replace(".", "", regex=False)
            .str.split("-").str[0].str.strip())

# ── Cargar los 520 RUTs de referencia (AMBOS desde tabla_docente limpia) ─────
td = pd.read_csv(os.path.join(OUT, "tabla_docente.csv"), dtype=str)
ambos = td[td["fuente"] == "NOMINA_DOTACION"].copy()
ruts_520 = set(ambos["rut_key"].unique())
print(f"RUTs de referencia (AMBOS unicos): {len(ruts_520)}")

# ── Mapeo de periodos texto -> codigo estandar ────────────────────────────────
PERIODO_MAP = {
    "primer semestre 2022":  "2022-01",
    "segundo semestre 2022": "2022-02",
    "primer semestre 2023":  "2023-01",
    "segundo semestre 2023": "2023-02",
    "primer semestre 2024":  "2024-01",
    "segundo semestre 2024": "2024-02",
    "primer semestre 2025":  "2025-01",
    "segundo semestre 2025": "2025-02",
}

def normalizar_periodo(s):
    return s.str.strip().str.lower().map(PERIODO_MAP).fillna(s.str.strip())

# ── DIPLOMADOS (4 archivos -> 1 tabla) ───────────────────────────────────────
diplomas = []
for anio in [2022, 2023, 2024, 2025]:
    path = os.path.join(DOCS, f"CONSOLIDADO DOCENTES 3-05-2026.xlsx - DIPLOMADO {anio}.csv")
    df = pd.read_csv(path, dtype=str)
    df.columns = df.columns.str.strip()
    df["rut_key"] = strip_dv(df["RUT"])
    df["tipo_formacion"] = "DIPLOMADO"
    df["periodo_evento"] = None   # diplomados son anuales, no tienen semestre
    df["anio_evento"] = str(anio)
    df = df.rename(columns={
        "NOMBRE DOCENTE": "nombre_docente",
        "Facultad ": "facultad", "Facultad": "facultad",
        "Carrera": "carrera", "Sede": "sede",
        "Tipo formación ": "nombre_actividad", "Tipo formación": "nombre_actividad",
    })
    df["jerarquia_evento"] = None
    df["contrato_evento"]  = None
    df["linea_proyecto"]   = None
    diplomas.append(df[["rut_key","tipo_formacion","periodo_evento","anio_evento",
                         "nombre_docente","nombre_actividad","facultad","carrera","sede",
                         "jerarquia_evento","contrato_evento","linea_proyecto"]])

df_dipl = pd.concat(diplomas, ignore_index=True)
print(f"\nDIPLOMADOS  filas raw: {len(df_dipl)} | RUTs unicos: {df_dipl['rut_key'].nunique()}")

# ── TALLERES (3 archivos, 2024_1 es duplicado -> usar solo 2 distintos) ───────
taller_files = [
    ("CONSOLIDADO DOCENTES 3-05-2026.xlsx - TALLERES 2023_2.csv", None),
    ("CONSOLIDADO DOCENTES 3-05-2026.xlsx - TALLERES 2024_1.csv", None),
    ("CONSOLIDADO DOCENTES 3-05-2026.xlsx - TALLERES 2024_2.csv", None),
    # TALLERES 2024_1 (1).csv es copia exacta de 2024_1 -> excluido
]
talleres = []
for fname, _ in taller_files:
    df = pd.read_csv(os.path.join(DOCS, fname), dtype=str)
    df.columns = df.columns.str.strip()
    df["rut_key"] = strip_dv(df["RUT"])
    df["tipo_formacion"] = "TALLER"
    df["periodo_evento"] = normalizar_periodo(df["Periodo"])
    df["anio_evento"] = df["periodo_evento"].str[:4]
    df = df.rename(columns={
        "NOMBRE DOCENTE ": "nombre_docente", "NOMBRE DOCENTE": "nombre_docente",
        "Actividad": "nombre_actividad",
        "Sede": "sede", "Facultad": "facultad", "Carrera": "carrera",
    })
    df["jerarquia_evento"] = None
    df["contrato_evento"]  = None
    df["linea_proyecto"]   = None
    talleres.append(df[["rut_key","tipo_formacion","periodo_evento","anio_evento",
                         "nombre_docente","nombre_actividad","facultad","carrera","sede",
                         "jerarquia_evento","contrato_evento","linea_proyecto"]])

df_tall = pd.concat(talleres, ignore_index=True)
print(f"TALLERES    filas raw: {len(df_tall)} | RUTs unicos: {df_tall['rut_key'].nunique()}")

# ── PROYECTOS INVESTIGACION ───────────────────────────────────────────────────
df_proy = pd.read_csv(
    os.path.join(DOCS, "CONSOLIDADO DOCENTES 3-05-2026.xlsx - PROYECTOS DE INVESTIGACION.csv"),
    dtype=str
)
df_proy.columns = df_proy.columns.str.strip()
df_proy["rut_key"] = strip_dv(df_proy["RUT"])
df_proy["tipo_formacion"] = "PROYECTO"
df_proy["anio_evento"]    = df_proy["Año"].str.strip()
df_proy["periodo_evento"] = None   # proyectos son anuales, no tienen semestre
df_proy = df_proy.rename(columns={
    "NOMBRE DOCENTE": "nombre_docente",
    "Facultad ": "facultad", "Facultad": "facultad",
    "Carrera": "carrera", "Sede": "sede",
    "Nombre proyecto": "nombre_actividad",
    "Tipo de contrato": "contrato_evento",
    "Jerarquía": "jerarquia_evento",
    "Linea ": "linea_proyecto", "Linea": "linea_proyecto",
})
df_proy2 = df_proy[["rut_key","tipo_formacion","periodo_evento","anio_evento",
                     "nombre_docente","nombre_actividad","facultad","carrera","sede",
                     "jerarquia_evento","contrato_evento","linea_proyecto"]]
print(f"PROYECTOS   filas raw: {len(df_proy2)} | RUTs unicos: {df_proy2['rut_key'].nunique()}")

# ── CONSOLIDAR PARTICIPACION ──────────────────────────────────────────────────
participacion = pd.concat([df_dipl, df_tall, df_proy2], ignore_index=True)
participacion = participacion.sort_values(["rut_key","periodo_evento"]).reset_index(drop=True)

print(f"\nTOTAL participacion (sin filtro): {len(participacion)} filas | {participacion['rut_key'].nunique()} RUTs unicos")

# Guardar version completa (todos los docentes con formacion, sin filtrar por los 520)
participacion.to_csv(os.path.join(OUT, "P3_participacion_formacion_todos.csv"), index=False, encoding="utf-8-sig")
print("Guardado: P3_participacion_formacion_todos.csv")

# Filtrar solo los 520 de AMBOS
part_520 = participacion[participacion["rut_key"].isin(ruts_520)].copy()
part_520.to_csv(os.path.join(OUT, "P3_participacion_formacion_520.csv"), index=False, encoding="utf-8-sig")
print(f"Guardado: P3_participacion_formacion_520.csv ({len(part_520)} filas | {part_520['rut_key'].nunique()} RUTs de los 520)")

# ── RESUMEN para contraparte ──────────────────────────────────────────────────
resumen = (participacion.groupby(["tipo_formacion","anio_evento"])
           .agg(total_registros=("rut_key","count"),
                ruts_unicos=("rut_key","nunique"))
           .reset_index())
resumen.to_csv(os.path.join(OUT, "P3_resumen_participacion.csv"), index=False, encoding="utf-8-sig")
print("Guardado: P3_resumen_participacion.csv")

# ── GRUPO CONTROL: 520 sin ninguna formacion, que tengan evaluaciones ─────────
# Paso 1: RUTs de los 520 que NO tienen formacion registrada
ruts_con_formacion = set(part_520["rut_key"].unique())
ruts_sin_formacion = ruts_520 - ruts_con_formacion
print(f"\nDe los 520 AMBOS:")
print(f"  Con alguna formacion (2022-2025): {len(ruts_con_formacion)}")
print(f"  Sin ninguna formacion:            {len(ruts_sin_formacion)}")

# Paso 2: verificar cuales de los sin-formacion tienen al menos 1 evaluacion de estudiantes
periodos = ["2023-01","2023-02","2024-01","2024-02","2025-01","2025-02"]
ruts_con_eval = set()
for p in periodos:
    fname = f"CONSOLIDADO EVALUACION ESTUDIANTES UCEN 3-5-2026.xlsx - {p}.csv"
    path  = os.path.join(EVALS, fname)
    if not os.path.exists(path):
        continue
    # evaluaciones tienen 2 filas de encabezado extra antes de los nombres de columna
    df_ev = pd.read_csv(path, dtype=str, skiprows=2)
    df_ev.columns = df_ev.columns.str.strip()
    # columna real: "4497 Rut Docente"
    rut_col = [c for c in df_ev.columns if "rut" in c.lower() and "docente" in c.lower()]
    if rut_col:
        ruts_con_eval.update(df_ev[rut_col[0]].dropna().astype(str).str.strip())

# las evaluaciones ya vienen sin DV, ruts_520 tampoco tiene DV -> match directo
ruts_control = ruts_sin_formacion & ruts_con_eval
print(f"  Sin formacion Y con evaluaciones (GRUPO CONTROL): {len(ruts_control)}")

# construir CSV del grupo control con su perfil
control_df = ambos[ambos["rut_key"].isin(ruts_control)].drop_duplicates("rut_key").copy()
control_df["grupo"] = "CONTROL_SIN_FORMACION"
control_df.to_csv(
    os.path.join(OUT, "P3_docentes_perfil_completo_sinformacion.csv"),
    index=False, encoding="utf-8-sig"
)
print(f"Guardado: P3_docentes_perfil_completo_sinformacion.csv ({len(control_df)} docentes)")
print("\nListo. Archivos madre no modificados.")
