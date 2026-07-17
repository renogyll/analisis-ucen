"""
ETL tabla_docente — tabla maestra de docentes (PK del sistema)
Fuentes: NOMINA + DOTACION + evaluacion_periodo (para SOLO_EVALUACIONES)

Opcion A: columnas de DOTACION integradas directamente en tabla_docente.
  - Filas NOMINA_DOTACION y SOLO_DOTACION tienen columnas DOTACION completas.
  - Filas NOMINA y SOLO_EVALUACIONES tienen columnas DOTACION en NULL.

Deduplicacion NOMINA documentada en DECISIONES_METODOLOGICAS.md seccion 2.
"""

import pandas as pd
import os

BASE = r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO\Downloads\Analisis_UCEN_v2"
DOCS = os.path.join(BASE, "CONSOLIDADO DOCENTES 3-05-2026")
OUT  = os.path.join(BASE, "PROCESADO")

def strip_dv(serie):
    return (serie.astype(str).str.strip()
            .str.replace(".", "", regex=False)
            .str.split("-").str[0].str.strip())

def normalizar_fecha(serie):
    return pd.to_datetime(serie, errors="coerce", dayfirst=False).dt.strftime("%Y-%m-%d")

# ── Cargar NOMINA ─────────────────────────────────────────────────────────────
nom = pd.read_csv(
    os.path.join(DOCS, "CONSOLIDADO DOCENTES 3-05-2026.xlsx - NOMINA .csv"),
    dtype=str
)
nom.columns = nom.columns.str.strip()
nom["rut_key"] = strip_dv(nom["RUT"])
nom = nom.rename(columns={
    "NOMBRE":                            "nombre",
    "SEXO":                              "sexo",
    "JORNADA/HONORARIO":                 "tipo_contrato",
    "ESTAMENTO FUNCIONAL":               "estamento",
    "FUNCIÓN PRINCIPAL ACADÉMICA":       "funcion_principal",
    "NOMBRE DEPARTAMENTO FUNCIÓN PRINCIPAL": "departamento",
    "JERARQUÍA":                         "jerarquia",
    "FECHA JERARQUIZACIÓN":              "fecha_jerarquizacion",
    "OBSERVACIONES":                     "observaciones_nomina",
})
print(f"NOMINA cruda: {len(nom)} filas | {nom['rut_key'].nunique()} RUTs unicos")

# ── Reglas de deduplicacion ───────────────────────────────────────────────────

# Caso 1: Filas completamente identicas
nom = nom.drop_duplicates(
    subset=[c for c in nom.columns if c not in ["RUT", "rut_key"]], keep="first"
)
print(f"Tras eliminar filas identicas: {len(nom)}")

# Caso 2: Jornada vs Honorario — conservar Jornada, marcar tipo_contrato
ruts_jornada_honorario = {"10286160", "10989977", "16356862", "19925201"}
for rut in ruts_jornada_honorario:
    mask = nom["rut_key"] == rut
    if mask.sum() == 2:
        idx_j = nom[(nom["rut_key"] == rut) & (nom["tipo_contrato"] == "Jornada")].index
        if len(idx_j):
            nom.loc[idx_j[0], "tipo_contrato"] = "Jornada+Honorario"
        idx_h = nom[(nom["rut_key"] == rut) & (nom["tipo_contrato"] == "Honorario")].index
        nom = nom.drop(idx_h)
print(f"Tras colapsar Jornada+Honorario: {len(nom)}")

# Caso 3: ROYFEL SISO (26836719) — error tipografico en nombre
mask_siso = nom["rut_key"] == "26836719"
if mask_siso.sum() == 2:
    nom.loc[nom[mask_siso].index[0], "nombre"] = "ROYFEL JOSE SISO MARCANO"
    nom = nom.drop(nom[mask_siso].index[1])
print(f"Tras normalizar ROYFEL SISO: {len(nom)}")

# Caso 4: JORG STIPPEL (25600736) — misma persona, dos departamentos
# Se conservan ambas filas hasta confirmar con contraparte

# Caso 5: Carlos/Rodrigo ESPINOZA (16322128) — personas distintas, mismo RUT
# Eliminar ambas: imposible distinguir a cual corresponden los datos
nom = nom[nom["rut_key"] != "16322128"].copy()
print(f"Tras eliminar ESPINOZA (RUT ambiguo): {len(nom)} filas | {nom['rut_key'].nunique()} RUTs unicos")

# ── Cargar DOTACION ───────────────────────────────────────────────────────────
dot = pd.read_csv(
    os.path.join(DOCS, "CONSOLIDADO DOCENTES 3-05-2026.xlsx - DOTACION.csv"),
    dtype=str, encoding="latin-1"
)
dot.columns = dot.columns.str.strip()
dot["rut_key"] = strip_dv(dot["RUT"])

# Renombrar columnas de DOTACION (columnas por indice para evitar problemas de encoding)
C = dot.columns.tolist()
dot_rename = {
    C[2]:  "dot_nombre",
    C[3]:  "cargo",
    C[4]:  "centro_costo",
    C[5]:  "area_carrera",
    C[6]:  "unidad_facultad",
    C[7]:  "ubicacion",
    C[8]:  "fecha_ingreso",
    C[9]:  "fecha_retiro",
    C[10]: "antiguedad_anios",
    C[11]: "clasificacion",
    C[12]: "jornada_dot",
    C[13]: "fecha_nacimiento",
    C[14]: "edad_anios",
    C[15]: "jerarquia_dot",
    C[16]: "nivel_formacion",
    C[17]: "nombre_grado",
    C[18]: "institucion_grado",
    C[19]: "pais_grado",
}
dot = dot.rename(columns=dot_rename)

# Decision metodologica 4: INDEFINIDO -> NULL en fecha_retiro
dot["fecha_retiro"] = dot["fecha_retiro"].replace("INDEFINIDO", None)

# Normalizar fechas a YYYY-MM-DD para PostgreSQL
dot["fecha_ingreso"]    = normalizar_fecha(dot["fecha_ingreso"])
dot["fecha_retiro"]     = normalizar_fecha(dot["fecha_retiro"])
dot["fecha_nacimiento"] = normalizar_fecha(dot["fecha_nacimiento"])

DOT_COLS = ["rut_key", "dot_nombre", "cargo", "centro_costo", "area_carrera",
            "unidad_facultad", "ubicacion", "fecha_ingreso", "fecha_retiro",
            "antiguedad_anios", "clasificacion", "jornada_dot", "fecha_nacimiento",
            "edad_anios", "jerarquia_dot", "nivel_formacion", "nombre_grado",
            "institucion_grado", "pais_grado"]
dot_clean = dot[DOT_COLS].copy()

print(f"DOTACION: {len(dot_clean)} filas | {dot_clean['rut_key'].nunique()} RUTs unicos")

# ── Combinar NOMINA + DOTACION ────────────────────────────────────────────────
ruts_nom = set(nom["rut_key"].unique())
ruts_dot = set(dot_clean["rut_key"].unique())

# Merge NOMINA con columnas DOTACION (left join — todas las filas de NOMINA)
nom_merged = nom.merge(dot_clean, on="rut_key", how="left")

# Asignar fuente
nom_merged["fuente"] = nom_merged["rut_key"].apply(
    lambda r: "NOMINA_DOTACION" if r in ruts_dot else "NOMINA"
)
print(f"NOMINA_DOTACION: {(nom_merged['fuente']=='NOMINA_DOTACION').sum()}")
print(f"NOMINA:          {(nom_merged['fuente']=='NOMINA').sum()}")

# ── Agregar SOLO_DOTACION ─────────────────────────────────────────────────────
solo_dot_ruts = ruts_dot - ruts_nom
dot_extra = dot_clean[dot_clean["rut_key"].isin(solo_dot_ruts)].copy()
dot_extra["nombre"]   = dot_extra["dot_nombre"]
dot_extra["fuente"]   = "SOLO_DOTACION"
print(f"SOLO_DOTACION: {len(dot_extra)}")

# ── Agregar SOLO_EVALUACIONES ─────────────────────────────────────────────────
ep = pd.read_csv(os.path.join(OUT, "evaluacion_periodo.csv"), dtype=str)
ruts_eval = set(ep["rut_docente"].str.strip().unique())
solo_eval_ruts = ruts_eval - ruts_nom - solo_dot_ruts

ep_sorted  = ep.sort_values("periodo", ascending=False)
ep_nombres = (ep_sorted
              .drop_duplicates("rut_docente")[["rut_docente", "nombre_docente"]]
              .rename(columns={"rut_docente": "rut_key", "nombre_docente": "nombre"}))
ep_nombres = ep_nombres[ep_nombres["rut_key"].isin(solo_eval_ruts)].copy()
ep_nombres["fuente"] = "SOLO_EVALUACIONES"
print(f"SOLO_EVALUACIONES: {len(ep_nombres)}")

# ── Agregar SOLO_CALIFICACIONES ───────────────────────────────────────────────
# Docentes en calificacion_alumno no presentes en ninguna fuente anterior
cal = pd.read_csv(os.path.join(OUT, "calificacion_alumno.csv"), dtype=str)
ruts_cal = set(cal["rut_docente"].str.strip().unique())
solo_cal_ruts = ruts_cal - ruts_nom - solo_dot_ruts - solo_eval_ruts

cal_sorted  = cal.sort_values("periodo", ascending=False)
cal_nombres = (cal_sorted
               .drop_duplicates("rut_docente")[["rut_docente", "nombre_docente"]]
               .rename(columns={"rut_docente": "rut_key", "nombre_docente": "nombre"}))
cal_nombres = cal_nombres[cal_nombres["rut_key"].isin(solo_cal_ruts)].copy()
cal_nombres["fuente"] = "SOLO_CALIFICACIONES"
print(f"SOLO_CALIFICACIONES: {len(cal_nombres)}")

# ── Agregar SOLO_FORMACION ────────────────────────────────────────────────────
# Docentes en archivos de formacion no presentes en ninguna fuente anterior
form_ruts = set()
form_nombres = {}

# Diplomados
for anio in [2022, 2023, 2024, 2025]:
    path = os.path.join(DOCS, f"CONSOLIDADO DOCENTES 3-05-2026.xlsx - DIPLOMADO {anio}.csv")
    df_f = pd.read_csv(path, dtype=str)
    df_f.columns = df_f.columns.str.strip()
    df_f["rut_key"] = strip_dv(df_f["RUT"])
    for _, row in df_f.iterrows():
        r = row["rut_key"]
        form_ruts.add(r)
        if r not in form_nombres:
            form_nombres[r] = row.get("NOMBRE DOCENTE", None)

# Talleres
for fname in ["CONSOLIDADO DOCENTES 3-05-2026.xlsx - TALLERES 2023_2.csv",
              "CONSOLIDADO DOCENTES 3-05-2026.xlsx - TALLERES 2024_1.csv",
              "CONSOLIDADO DOCENTES 3-05-2026.xlsx - TALLERES 2024_2.csv"]:
    df_f = pd.read_csv(os.path.join(DOCS, fname), dtype=str)
    df_f.columns = df_f.columns.str.strip()
    df_f["rut_key"] = strip_dv(df_f["RUT"])
    nom_col = next((c for c in df_f.columns if "nombre" in c.lower() and "docente" in c.lower()), None)
    for _, row in df_f.iterrows():
        r = row["rut_key"]
        form_ruts.add(r)
        if r not in form_nombres and nom_col:
            form_nombres[r] = row[nom_col]

# Proyectos
df_f = pd.read_csv(
    os.path.join(DOCS, "CONSOLIDADO DOCENTES 3-05-2026.xlsx - PROYECTOS DE INVESTIGACION.csv"),
    dtype=str
)
df_f.columns = df_f.columns.str.strip()
df_f["rut_key"] = strip_dv(df_f["RUT"])
for _, row in df_f.iterrows():
    r = row["rut_key"]
    form_ruts.add(r)
    if r not in form_nombres:
        form_nombres[r] = row.get("NOMBRE DOCENTE", None)

solo_form_ruts = form_ruts - ruts_nom - solo_dot_ruts - solo_eval_ruts - solo_cal_ruts
form_rows = pd.DataFrame([
    {"rut_key": r, "nombre": form_nombres.get(r), "fuente": "SOLO_FORMACION"}
    for r in solo_form_ruts
])
print(f"SOLO_FORMACION: {len(form_rows)}")

# ── Consolidar tabla final ────────────────────────────────────────────────────
NOM_COLS = ["rut_key", "nombre", "sexo", "tipo_contrato", "estamento",
            "funcion_principal", "departamento", "jerarquia",
            "fecha_jerarquizacion", "observaciones_nomina", "fuente"]

KEEP_COLS = NOM_COLS + [c for c in DOT_COLS if c not in ("rut_key", "dot_nombre")]

bloques = [nom_merged, dot_extra, ep_nombres, cal_nombres, form_rows]
for col in KEEP_COLS:
    for bloque in bloques:
        if col not in bloque.columns:
            bloque[col] = None

tabla_docente = pd.concat(
    [b[KEEP_COLS] for b in bloques],
    ignore_index=True
)

out_path = os.path.join(OUT, "tabla_docente.csv")
tabla_docente.to_csv(out_path, index=False, encoding="utf-8-sig")

print(f"\ntabla_docente.csv generada")
print(f"  Total filas:    {len(tabla_docente)}")
print(f"  RUTs unicos:    {tabla_docente['rut_key'].nunique()}")
print(f"\nDistribucion por fuente:")
print(tabla_docente["fuente"].value_counts().to_string())
print(f"\nColumnas ({len(tabla_docente.columns)}): {tabla_docente.columns.tolist()}")
print("\nListo. Archivos madre no modificados.")
