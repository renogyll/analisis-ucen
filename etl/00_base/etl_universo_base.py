"""
ETL: Universo Base — NOMINA × DOTACION ∪ SOLO_FORMACION
FUENTE : data/raw/consolidado_docentes/
SALIDAS: analisis.universo_base (DB)
         data/cascade/00_base/nomina_x_dotacion.csv

Universo base del proyecto: todos los RUTs únicos presentes en NOMINA, DOTACION,
o en actividades de formación (Taller 2025 + Proyectos de Investigación).

Origen:
  AMBOS          → en NOMINA y DOTACION          (~520)
  SOLO_NOMINA    → solo en NOMINA                (~437)
  SOLO_DOTACION  → solo en DOTACION              ( ~27)
  SOLO_FORMACION → solo en Taller2025/Proyectos  (~160)  ← nuevo 2026-07-18

Actualización 2026-07-18:
  Se incorporan 160 RUTs nuevos detectados en Certificación Oferta Formativa 2025
  y Proyectos de Investigación que no estaban en NOMINA ni DOTACION.
  Estos tienen perfil parcial: nombre, sexo, jerarquía, facultad y contrato.
  Campos de RRHH (antigüedad, grado académico, fecha ingreso) quedan NULL.
"""
import sys; sys.stdout.reconfigure(encoding="utf-8")
import os
from pathlib import Path
import pandas as pd
import numpy as np
from sqlalchemy import create_engine

# ── Config ────────────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parents[2]))
from config import DATA_RAW, C00_BASE

RAW    = Path(DATA_RAW) / "consolidado_docentes"
DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"
engine = create_engine(DB_URL)

# ── Mapeo CARGO → tipo_contrato_tag para los 27 SOLO_DOTACION ─────────────────
# Fuente: etl/00_base/solo_dotacion_28tageables.csv (revisión manual)
CARGO_TAG = {
    "Académico(a) Investigador(a)":            "JORNADA",
    "Analista Senior Financiero":              "JORNADA",
    "Asistente Biblioteca":                    "JORNADA",
    "Coordinado(a) de Simulación":             "JORNADA",
    "Coordinador de Proyectos":                "HONORARIO",
    "Coordinador(a) Advance y Vespertino":     "JORNADA",
    "Coordinador(a) Campos Clínicos":          "JORNADA",
    "Coordinador(a) Curricular":               "JORNADA",
    "Director(a) Carrera":                     "JORNADA",
    "Jefe de Sistemas Académicos":             "JORNADA",
    "Profesor":                                "HONORARIO",
    "Profesor 1/2 Jornada":                   "JORNADA",
    "Profesor por Jornada":                    "JORNADA",
    "Secretario(a) de Facultad":               "JORNADA",
    "Secretario(a) de Facultad (I)":           "JORNADA",
    "Subdirector(a) Gestión del Conocimiento": "JORNADA",
    "Vicerrector Regional":                    "JORNADA",
}

def strip_dv(serie):
    return (
        serie.astype(str).str.strip()
        .str.replace(".", "", regex=False)
        .str.split("-").str[0].str.strip()
        .str.rstrip("Kk")   # RUTs con dígito verificador 'k' sin guión (ej: 15913282k)
    )

def find_col(df, *keywords):
    """Busca columna por palabras clave (tolerante a acentos y mayúsculas)."""
    for col in df.columns:
        col_n = col.lower()
        if all(k.lower() in col_n for k in keywords):
            return col
    return None

# ── Leer NOMINA ───────────────────────────────────────────────────────────────
nom_raw = pd.read_csv(RAW / "CONSOLIDADO DOCENTES 3-05-2026.xlsx - NOMINA .csv", dtype=str)
nom_raw.columns = nom_raw.columns.str.strip()
nom_raw["rut_key"] = strip_dv(nom_raw["RUT"])

n_filas_nom = len(nom_raw)
nom = nom_raw.drop_duplicates(subset="rut_key", keep="first").copy()
print(f"NOMINA  : {n_filas_nom} filas → {len(nom)} RUTs únicos  ({n_filas_nom - len(nom)} duplicados)")

NOM_RENAME = {
    find_col(nom, "nombre"):                           "nombre",
    find_col(nom, "sexo"):                             "sexo",
    find_col(nom, "jornada", "honorario"):             "tipo_contrato_nomina",
    find_col(nom, "estamento"):                        "estamento",
    find_col(nom, "funci"):                            "funcion_principal",
    find_col(nom, "departamento"):                     "departamento",
    find_col(nom, "jerarqu"):                          "jerarquia",
    find_col(nom, "jerarquizaci"):                     "fecha_jerarquizacion",
    find_col(nom, "observaci"):                        "observaciones_nomina",
}
NOM_RENAME = {k: v for k, v in NOM_RENAME.items() if k is not None}
nom = nom.rename(columns=NOM_RENAME)

# ── Leer DOTACION ─────────────────────────────────────────────────────────────
dot_raw = pd.read_csv(RAW / "CONSOLIDADO DOCENTES 3-05-2026.xlsx - DOTACION.csv", dtype=str)
dot_raw.columns = dot_raw.columns.str.strip()
dot_raw["rut_key"] = strip_dv(dot_raw["RUT"])

n_filas_dot = len(dot_raw)
dot = dot_raw.drop_duplicates(subset="rut_key", keep="first").copy()
print(f"DOTACION: {n_filas_dot} filas → {len(dot)} RUTs únicos  ({n_filas_dot - len(dot)} duplicados)")

DOT_RENAME = {
    find_col(dot, "nombre", "nueva"):          "nombre_dot",
    find_col(dot, "cargo"):                    "cargo_dot",
    find_col(dot, "centro"):                   "centro_costo",
    find_col(dot, "rea", "carrera"):           "area_carrera",
    find_col(dot, "unidad"):                   "unidad_facultad",
    find_col(dot, "ubicaci"):                  "ubicacion",
    find_col(dot, "ingreso"):                  "fecha_ingreso",
    find_col(dot, "retiro"):                   "fecha_retiro",
    find_col(dot, "ant"):                      "antiguedad_anios",
    find_col(dot, "clasificaci"):              "clasificacion",
    find_col(dot, "jornada"):                  "jornada_dot",
    find_col(dot, "nacimiento"):               "fecha_nacimiento",
    find_col(dot, "edad"):                     "edad_anios",
    find_col(dot, "jerarqu"):                  "jerarquia_dot",
    find_col(dot, "nivel", "formaci"):         "nivel_formacion",
    find_col(dot, "nombre", "grado"):          "nombre_grado",
    find_col(dot, "instituci"):                "institucion_grado",
    find_col(dot, "pa"):                       "pais_grado",
}
DOT_RENAME = {k: v for k, v in DOT_RENAME.items() if k is not None}
dot = dot.rename(columns=DOT_RENAME)
dot = dot.drop(columns=["RUT", "NOMBRE(variable original)"], errors="ignore")

# ── FULL OUTER JOIN ───────────────────────────────────────────────────────────
nom_cols = [c for c in nom.columns if c != "rut_key"]
dot_cols = [c for c in dot.columns if c != "rut_key"]

nom_r = nom[["rut_key"] + nom_cols].rename(columns={c: f"n_{c}" for c in nom_cols})
dot_r = dot[["rut_key"] + dot_cols].rename(columns={c: f"d_{c}" for c in dot_cols})

merged = pd.merge(nom_r, dot_r, on="rut_key", how="outer", indicator=True)
merged["origen"] = merged["_merge"].map({
    "both": "AMBOS", "left_only": "SOLO_NOMINA", "right_only": "SOLO_DOTACION"
})
merged = merged.drop(columns=["_merge"])

print(f"\nResultado cruce:")
print(merged["origen"].value_counts().to_string())
print(f"Total RUTs únicos: {len(merged)}")

# ── tipo_contrato_tag ─────────────────────────────────────────────────────────
merged["tipo_contrato_tag"] = (
    merged["n_tipo_contrato_nomina"].str.strip().str.upper()
)
mask_dot = merged["origen"] == "SOLO_DOTACION"
merged.loc[mask_dot, "tipo_contrato_tag"] = (
    merged.loc[mask_dot, "d_cargo_dot"].map(CARGO_TAG)
)
merged["tipo_contrato_tag"] = merged["tipo_contrato_tag"].fillna("DESCONOCIDO")

desconocidos = (merged["tipo_contrato_tag"] == "DESCONOCIDO").sum()
if desconocidos > 0:
    print(f"\nAVISO: {desconocidos} docentes con tipo_contrato_tag=DESCONOCIDO")
    print(merged[merged["tipo_contrato_tag"] == "DESCONOCIDO"][["rut_key","origen","d_cargo_dot"]])

# ── Columnas derivadas ────────────────────────────────────────────────────────
merged["nombre"] = merged["n_nombre"].fillna(merged["d_nombre_dot"])
merged["sexo"]   = merged["n_sexo"].str.strip().str.upper().map(
    {"MASCULINO": "HOMBRE", "FEMENINO": "MUJER"}
)

merged["edad_anios"]       = pd.to_numeric(merged["d_edad_anios"].str.strip()       if "d_edad_anios"       in merged.columns else pd.NA, errors="coerce")
merged["antiguedad_anios"] = pd.to_numeric(merged["d_antiguedad_anios"].str.strip() if "d_antiguedad_anios" in merged.columns else pd.NA, errors="coerce")
merged["anio_ingreso"]     = pd.to_datetime(merged.get("d_fecha_ingreso"),  dayfirst=True, errors="coerce").dt.year
merged["anio_jerarquizacion"] = pd.to_datetime(
    merged.get("n_fecha_jerarquizacion"), format="%m/%d/%Y", errors="coerce"
).dt.year

bins_edad   = [0,30,35,40,45,50,55,60,65,70,200]
labels_edad = ["<30","30-34","35-39","40-44","45-49","50-54","55-59","60-64","65-69","70+"]
merged["tramo_edad"] = pd.cut(
    merged["edad_anios"], bins=bins_edad, labels=labels_edad, right=False
).astype("object").where(merged["edad_anios"].notna())

bins_ant   = [0,5,10,15,20,25,30,200]
labels_ant = ["0-4","5-9","10-14","15-19","20-24","25-29","30+"]
merged["tramo_antiguedad"] = pd.cut(
    merged["antiguedad_anios"], bins=bins_ant, labels=labels_ant, right=False
).astype("object").where(merged["antiguedad_anios"].notna())

# ── Renombrar columnas prefijadas al nombre final ─────────────────────────────
RENAME_FINAL = {
    "n_jerarquia":            "jerarquia",
    "n_estamento":            "estamento",
    "n_funcion_principal":    "funcion_principal",
    "n_departamento":         "departamento",
    "n_fecha_jerarquizacion": "fecha_jerarquizacion",
    "n_observaciones_nomina": "observaciones_nomina",
    "d_jerarquia_dot":        "jerarquia_dot",
    "d_cargo_dot":            "cargo_dot",
    "d_area_carrera":         "area_carrera",
    "d_unidad_facultad":      "unidad_facultad",
    "d_centro_costo":         "centro_costo",
    "d_ubicacion":            "ubicacion",
    "d_clasificacion":        "clasificacion",
    "d_fecha_ingreso":        "fecha_ingreso",
    "d_fecha_retiro":         "fecha_retiro",
    "d_jornada_dot":          "jornada_dot",
    "d_fecha_nacimiento":     "fecha_nacimiento",
    "d_nivel_formacion":      "nivel_formacion",
    "d_nombre_grado":         "nombre_grado",
    "d_institucion_grado":    "institucion_grado",
    "d_pais_grado":           "pais_grado",
}
merged = merged.rename(columns=RENAME_FINAL)

# ── Seleccionar columnas finales ──────────────────────────────────────────────
COLS_FINAL = [
    "rut_key", "origen", "tipo_contrato_tag",
    "nombre", "sexo",
    "jerarquia", "jerarquia_dot",
    "estamento", "funcion_principal", "departamento",
    "cargo_dot", "area_carrera", "unidad_facultad",
    "centro_costo", "ubicacion", "clasificacion",
    "fecha_ingreso", "fecha_retiro", "anio_ingreso",
    "antiguedad_anios", "tramo_antiguedad",
    "fecha_nacimiento", "edad_anios", "tramo_edad",
    "jornada_dot",
    "nivel_formacion", "nombre_grado", "institucion_grado", "pais_grado",
    "fecha_jerarquizacion", "anio_jerarquizacion",
    "observaciones_nomina",
]
out = merged[[c for c in COLS_FINAL if c in merged.columns]].copy()

# ── SOLO_FORMACION: Taller 2025 + Proyectos de Investigación ─────────────────
# Docentes que participaron en formación pero NO están en NOMINA ni DOTACION.
# Tienen perfil parcial: nombre, sexo, jerarquía, facultad y contrato.

CONT_MAP = {
    "JORNADA": "JORNADA", "HONORARIO": "HONORARIO", "HONORARIOS": "HONORARIO"
}

ruts_ya_en_base = set(out["rut_key"].dropna())
filas_form = []

# Taller 2025
tall = pd.read_excel(RAW / "CERTIFICACION OFERTA FORMATIVA 2025.xlsx", dtype=str)
tall["rut_key"] = strip_dv(tall["RUT"])
tall_nuevos = tall[~tall["rut_key"].isin(ruts_ya_en_base)].copy()
tall_nuevos = tall_nuevos.drop_duplicates(subset="rut_key", keep="first")
print(f"TALLER 2025    : {len(tall)} filas → {tall['rut_key'].nunique()} RUTs únicos → {len(tall_nuevos)} nuevos")

for _, r in tall_nuevos.iterrows():
    nombre = " ".join(filter(None, [
        str(r.get("Nombre","")).strip(),
        str(r.get("1er Apellido","")).strip(),
        str(r.get("2do Apellido","")).strip()
    ]))
    filas_form.append({
        "rut_key":          r["rut_key"],
        "origen":           "SOLO_FORMACION",
        "tipo_contrato_tag": CONT_MAP.get(str(r.get("Contrato","")).strip().upper(), "DESCONOCIDO"),
        "nombre":           nombre,
        "sexo":             str(r.get("Sexo","")).strip().upper() or None,
        "jerarquia":        str(r.get("Jerarquía","")).strip() or None,
        "unidad_facultad":  str(r.get("Facultad","")).strip() or None,
        "area_carrera":     str(r.get("Carrera","")).strip() or None,
    })

# Proyectos de Investigación
proy = pd.read_csv(RAW / "CONSOLIDADO DOCENTES 3-05-2026.xlsx - PROYECTOS DE INVESTIGACION.csv", dtype=str)
proy["rut_key"] = strip_dv(proy["RUT"])
proy_nuevos = proy[~proy["rut_key"].isin(ruts_ya_en_base | {r["rut_key"] for r in filas_form})].copy()
proy_nuevos = proy_nuevos.drop_duplicates(subset="rut_key", keep="first")
print(f"PROYECTOS I+D  : {len(proy)} filas → {proy['rut_key'].nunique()} RUTs únicos → {len(proy_nuevos)} nuevos")

for _, r in proy_nuevos.iterrows():
    filas_form.append({
        "rut_key":          r["rut_key"],
        "origen":           "SOLO_FORMACION",
        "tipo_contrato_tag": CONT_MAP.get(str(r.get("Tipo de contrato","")).strip().upper(), "DESCONOCIDO"),
        "nombre":           str(r.get("NOMBRE DOCENTE","")).strip() or None,
        "jerarquia":        str(r.get("Jerarquía","")).strip() or None,
        "unidad_facultad":  str(r.get("Facultad","")).strip() or None,
        "area_carrera":     str(r.get("Carrera","")).strip() or None,
    })

if filas_form:
    df_form = pd.DataFrame(filas_form)
    df_form["sexo"] = df_form.get("sexo", pd.NA)
    descon_form = (df_form["tipo_contrato_tag"] == "DESCONOCIDO").sum()
    if descon_form:
        print(f"\nAVISO SOLO_FORMACION: {descon_form} con tipo_contrato_tag=DESCONOCIDO")
        print(df_form[df_form["tipo_contrato_tag"] == "DESCONOCIDO"][["rut_key","nombre"]])
    out = pd.concat([out, df_form], ignore_index=True, sort=False)
    print(f"\nSOLO_FORMACION incorporados: {len(df_form)} docentes")

# ── Guardar CSV ───────────────────────────────────────────────────────────────
os.makedirs(C00_BASE, exist_ok=True)
csv_path = os.path.join(C00_BASE, "nomina_x_dotacion.csv")
out.to_csv(csv_path, index=False, encoding="utf-8-sig")
print(f"\nCSV: {csv_path}  ({len(out)} filas, {len(out.columns)} columnas)")

# ── Guardar DB ────────────────────────────────────────────────────────────────
out.to_sql("universo_base", engine, schema="analisis", if_exists="replace", index=False)
print(f"DB : analisis.universo_base  ({len(out)} filas)")

# ── Resumen ───────────────────────────────────────────────────────────────────
print(f"\n{'='*55}")
print(f"UNIVERSO BASE — RESUMEN FINAL")
print(f"{'='*55}")
print(f"Total RUTs únicos:  {len(out)}")
print(f"\nPor origen:")
print(out["origen"].value_counts().to_string())
print(f"\nPor tipo_contrato_tag:")
print(out["tipo_contrato_tag"].value_counts().to_string())
print(f"\nCompletitud campos clave:")
for col in ["sexo","unidad_facultad","nivel_formacion","antiguedad_anios","edad_anios","jerarquia"]:
    if col in out.columns:
        n = out[col].notna().sum()
        pct = n / len(out) * 100
        bar = "█" * int(pct / 5)
        print(f"  {col:<25}: {n:4d}/{len(out)}  {pct:5.1f}%  {bar}")

print(f"\nNOTA: SOLO_FORMACION tiene perfil parcial (NULL en antigüedad, grado académico,")
print(f"      fecha ingreso). Son docentes confirmados en actividades P3 no registrados")
print(f"      en NOMINA ni DOTACION a la fecha del corte (mayo 2026).")
