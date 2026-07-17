"""
ETL intel.trayectoria_alumno
Alumnos que tuvieron el mismo docente capacitado en los 3 períodos (pre/durante/post).
Una fila por alumno x docente x evento de formación.

Nota promedio por período = promedio de todas las asignaturas que el alumno
cursó con ese docente en ese período (puede ser más de una asignatura).
"""

import pandas as pd
from sqlalchemy import create_engine

OUT    = r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO\Downloads\Analisis_UCEN_v2\PROCESADO"
DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"

engine = create_engine(DB_URL)

# ── Fuentes ───────────────────────────────────────────────────────────────────
trat = pd.read_sql("SELECT * FROM intel.pre_during_post_sat", engine)
nd   = pd.read_sql("""
    SELECT rut_alumno, rut_docente, periodo,
           cod_asignatura, nombre_asignatura, nota
    FROM intel.notas_docente
    WHERE nota IS NOT NULL
""", engine)

nd["nota"] = pd.to_numeric(nd["nota"], errors="coerce")

def expandir_periodos(label):
    """Convierte '2022' → ['2022-01','2022-02'], '2023-01' → ['2023-01']"""
    if len(str(label)) == 4:
        return [f"{label}-01", f"{label}-02"]
    return [str(label)]

# ── Construir tabla ───────────────────────────────────────────────────────────
filas = []

for _, doc in trat.drop_duplicates(["rut_key","periodo_pre","periodo_durante","periodo_post"]).iterrows():
    rut   = doc["rut_key"]
    p_pre = expandir_periodos(doc["periodo_pre"])
    p_dur = expandir_periodos(doc["periodo_durante"])
    p_pos = expandir_periodos(doc["periodo_post"])

    d = nd[nd["rut_docente"] == rut]

    alumnos_pre = set(d[d["periodo"].isin(p_pre)]["rut_alumno"])
    alumnos_dur = set(d[d["periodo"].isin(p_dur)]["rut_alumno"])
    alumnos_pos = set(d[d["periodo"].isin(p_pos)]["rut_alumno"])
    alumnos_3p  = alumnos_pre & alumnos_dur & alumnos_pos

    for alum in alumnos_3p:
        a = d[d["rut_alumno"] == alum]

        filas_pre = a[a["periodo"].isin(p_pre)]
        filas_dur = a[a["periodo"].isin(p_dur)]
        filas_pos = a[a["periodo"].isin(p_pos)]

        nota_pre = filas_pre["nota"].mean()
        nota_dur = filas_dur["nota"].mean()
        nota_pos = filas_pos["nota"].mean()

        filas.append({
            "rut_alumno":       alum,
            "rut_docente":      rut,
            "nombre_docente":   doc["nombre"],
            "tipo_formacion":   doc["tipo_formacion"],
            "nombre_actividad": doc["nombre_actividad"],
            "anio_evento":      doc["anio_evento"],
            "periodo_evento":   doc["periodo_evento"],
            "periodo_pre":      doc["periodo_pre"],
            "periodo_durante":  doc["periodo_durante"],
            "periodo_post":     doc["periodo_post"],
            # notas promedio del alumno con ese docente en cada período
            "nota_pre":         round(nota_pre,  3) if pd.notna(nota_pre)  else None,
            "nota_durante":     round(nota_dur,  3) if pd.notna(nota_dur)  else None,
            "nota_post":        round(nota_pos,  3) if pd.notna(nota_pos)  else None,
            # asignaturas cursadas (para contexto)
            "n_asig_pre":       filas_pre["cod_asignatura"].nunique(),
            "n_asig_durante":   filas_dur["cod_asignatura"].nunique(),
            "n_asig_post":      filas_pos["cod_asignatura"].nunique(),
            "asig_pre":         ", ".join(sorted(filas_pre["nombre_asignatura"].dropna().unique())),
            "asig_durante":     ", ".join(sorted(filas_dur["nombre_asignatura"].dropna().unique())),
            "asig_post":        ", ".join(sorted(filas_pos["nombre_asignatura"].dropna().unique())),
        })

df = pd.DataFrame(filas)
df["delta_pre_post"]    = (df["nota_post"]    - df["nota_pre"]).round(3)
df["delta_pre_durante"] = (df["nota_durante"] - df["nota_pre"]).round(3)

# ── Resumen ───────────────────────────────────────────────────────────────────
print(f"\nintel.trayectoria_alumno:")
print(f"  Total filas:       {len(df)}")
print(f"  Alumnos únicos:    {df['rut_alumno'].nunique()}")
print(f"  Docentes únicos:   {df['rut_docente'].nunique()}")
print(f"\nPor tipo de formación:")
print(df.groupby("tipo_formacion").agg(
    filas         = ("rut_alumno",      "count"),
    alumnos       = ("rut_alumno",      "nunique"),
    docentes      = ("rut_docente",     "nunique"),
    nota_pre_avg  = ("nota_pre",        "mean"),
    nota_dur_avg  = ("nota_durante",    "mean"),
    nota_pos_avg  = ("nota_post",       "mean"),
    delta_avg     = ("delta_pre_post",  "mean"),
).round(3).to_string())

# ── Guardar ───────────────────────────────────────────────────────────────────
df.to_csv(f"{OUT}/intel_trayectoria_alumno.csv", index=False, encoding="utf-8-sig")
df.to_sql("trayectoria_alumno", engine, schema="intel", if_exists="replace", index=False)
print("\nCargado: intel.trayectoria_alumno")
print("Listo.")
