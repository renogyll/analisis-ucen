import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import os
import re

BASE    = os.path.dirname(__file__)
SRC     = os.path.join(BASE, "..", "..", "CONSOLIDADO DOCENTES 3-05-2026")
OUT     = os.path.join(BASE, "participacion_p2_918.csv")
DOC917  = os.path.join(BASE, "docente_918.csv")

# ── Función limpieza RUT ───────────────────────────────────────────────────────
def limpiar_rut(s):
    s = str(s).strip().replace(".", "").replace(" ", "")
    s = s.split("-")[0]
    return s.strip()

# ── Cargar universo 917 ───────────────────────────────────────────────────────
doc917 = pd.read_csv(DOC917, encoding="utf-8-sig", dtype={"rut_key": str})
doc917["rut_key"] = doc917["rut_key"].str.strip()

# Fallback jerarquía
doc917["jerarquia"] = doc917["jerarquia"].fillna(
    doc917["jerarquia_dot"].str.replace(r"^PROFESOR\s+", "", regex=True))
doc917.loc[doc917["jerarquia"] == "NO INFORMA", "jerarquia"] = None

# Agrupar antigüedad 15+
REMAP_ANT = {"15-19":"15+","20-24":"15+","25-29":"15+","30+":"15+"}
doc917["tramo_ant"] = doc917["tramo_antiguedad"].replace(REMAP_ANT)

perfil = doc917[["rut_key","jerarquia","tramo_ant","unidad_facultad",
                  "sexo","nivel_formacion"]].copy()

frames = []

# ── DIPLOMADOS 2022-2025 ──────────────────────────────────────────────────────
for year in ["2022","2023","2024","2025"]:
    fname = os.path.join(SRC, f"CONSOLIDADO DOCENTES 3-05-2026.xlsx - DIPLOMADO {year}.csv")
    df = pd.read_csv(fname, encoding="utf-8-sig", dtype=str)
    df.columns = df.columns.str.strip()
    df["rut_key"]        = df["RUT"].apply(limpiar_rut)
    df["tipo_formacion"] = "DIPLOMADO"
    df["anio"]           = year
    df["nombre_actividad"] = "Diplomado"
    df["linea"]          = None
    df = df.rename(columns={"unidad_ofertante": "unidad_ofertante"})
    frames.append(df[["rut_key","tipo_formacion","anio","nombre_actividad",
                       "linea","unidad_ofertante"]])

# ── PROYECTOS ─────────────────────────────────────────────────────────────────
fname = os.path.join(SRC, "CONSOLIDADO DOCENTES 3-05-2026.xlsx - PROYECTOS DE INVESTIGACION.csv")
df = pd.read_csv(fname, encoding="utf-8-sig", dtype=str)
df.columns = df.columns.str.strip()
df["rut_key"]          = df["RUT"].apply(limpiar_rut)
df["tipo_formacion"]   = "PROYECTO"
df["anio"]             = df["Año"].str.strip()
df["nombre_actividad"] = df["Nombre proyecto"].str.strip()
df["linea"]            = df["Linea"].str.strip()
frames.append(df[["rut_key","tipo_formacion","anio","nombre_actividad",
                   "linea","unidad_ofertante"]])

# ── TALLERES ──────────────────────────────────────────────────────────────────
talleres = {
    "2023": "CONSOLIDADO DOCENTES 3-05-2026.xlsx - TALLERES 2023_2.csv",
    "2024": "CONSOLIDADO DOCENTES 3-05-2026.xlsx - TALLERES 2024_1.csv",
    "2024": "CONSOLIDADO DOCENTES 3-05-2026.xlsx - TALLERES 2024_2.csv",
}
taller_files = [
    ("2023", "CONSOLIDADO DOCENTES 3-05-2026.xlsx - TALLERES 2023_2.csv"),
    ("2024", "CONSOLIDADO DOCENTES 3-05-2026.xlsx - TALLERES 2024_1.csv"),
    ("2024", "CONSOLIDADO DOCENTES 3-05-2026.xlsx - TALLERES 2024_2.csv"),
]
for anio, archivo in taller_files:
    fname = os.path.join(SRC, archivo)
    df = pd.read_csv(fname, encoding="utf-8-sig", dtype=str)
    df.columns = df.columns.str.strip()
    df["rut_key"]          = df["RUT"].apply(limpiar_rut)
    df["tipo_formacion"]   = "TALLER"
    df["anio"]             = anio
    df["nombre_actividad"] = df["Actividad"].str.strip()
    df["linea"]            = None
    frames.append(df[["rut_key","tipo_formacion","anio","nombre_actividad",
                       "linea","unidad_ofertante"]])

# ── Consolidar ────────────────────────────────────────────────────────────────
todo = pd.concat(frames, ignore_index=True)
todo["anio"] = todo["anio"].astype(str).str.strip().str[:4]

n_raw = len(todo)
ruts_917 = set(doc917["rut_key"])
todo["en_917"] = todo["rut_key"].isin(ruts_917)

n_en_917  = todo["en_917"].sum()
n_fuera   = n_raw - n_en_917

# Filtrar al universo 917
todo917 = todo[todo["en_917"]].copy()

# Merge con perfil docente
todo917 = todo917.merge(perfil, on="rut_key", how="left")

# ── Guardar ───────────────────────────────────────────────────────────────────
todo917.drop(columns=["en_917"]).to_csv(OUT, index=False, encoding="utf-8-sig")

# ── Cascada ───────────────────────────────────────────────────────────────────
n_doc_part  = todo917["rut_key"].nunique()
n_doc_total = len(doc917)
n_doc_no    = n_doc_total - n_doc_part

print("=" * 65)
print("  ETL PARTICIPACIÓN P2 — Universo 917")
print("=" * 65)
print(f"  Registros brutos (8 CSV): {n_raw}")
print(f"    ├── En universo 917:    {n_en_917}")
print(f"    └── Fuera de universo:  {n_fuera} (no jerarquizados)")
print()
print(f"  917 docentes jerarquizados")
print(f"    ├── {n_doc_part} participaron al menos 1 vez ({100*n_doc_part/n_doc_total:.1f}%)")
print(f"    └── {n_doc_no} nunca participaron ({100*n_doc_no/n_doc_total:.1f}%)")
print()
print("  Por tipo de formación:")
for tipo, grp in todo917.groupby("tipo_formacion"):
    n_inst = len(grp)
    n_doc  = grp["rut_key"].nunique()
    print(f"    ├── {tipo:10}: {n_inst:3d} instancias · {n_doc:3d} docentes únicos")
print()
print("  Por unidad ofertante:")
for unidad, grp in todo917.groupby("unidad_ofertante"):
    print(f"    ├── {unidad:6}: {len(grp):3d} instancias · {grp['rut_key'].nunique():3d} docentes únicos")
print()
print("  Por año:")
for anio, grp in todo917.groupby("anio"):
    print(f"    ├── {anio}: {grp['rut_key'].nunique():3d} docentes únicos · {len(grp):3d} instancias")
print("=" * 65)
print(f"\nGuardado: {OUT}")
