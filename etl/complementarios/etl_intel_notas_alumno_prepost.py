"""
ETL intel.notas_alumno_pre_during_post
Una fila por alumno × asignatura × docente × evento de formación,
etiquetada como pre / durante / post respecto del evento.

Fuente: analisis.p3_grupo_tratamiento × intel.notas_docente
No requiere que sea el mismo alumno en los 3 períodos.
"""

import sys
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
from sqlalchemy import create_engine

OUT    = r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO\Downloads\Analisis_UCEN_v2\PROCESADO"
DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"
engine = create_engine(DB_URL)

# ── Fuentes ───────────────────────────────────────────────────────────────────
p3 = pd.read_sql("""
    SELECT rut_key, nombre, tipo_formacion, nombre_actividad,
           anio_evento, periodo_evento, periodo_baseline, periodo_resultado
    FROM analisis.p3_grupo_tratamiento
    WHERE periodo_baseline IS NOT NULL AND periodo_resultado IS NOT NULL
""", engine)

nd = pd.read_sql("""
    SELECT calificacion_id, periodo, rut_alumno,
           cod_asignatura, nombre_asignatura, nota,
           rut_docente, nombre_docente, sede, facultad, plan
    FROM intel.notas_docente
    WHERE nota IS NOT NULL
""", engine)

nd["nota"]       = pd.to_numeric(nd["nota"], errors="coerce")
nd["rut_docente"] = nd["rut_docente"].astype(str)
p3["rut_key"]    = p3["rut_key"].astype(str)

print(f"p3_grupo_tratamiento : {len(p3)} eventos")
print(f"notas_docente        : {len(nd):,} filas")


def expandir(label):
    """'2022' → ['2022-01','2022-02'], '2023-01' → ['2023-01'], vacío → []"""
    s = str(label).strip()
    if s in ("", "nan", "None"):
        return []
    if len(s) == 4:
        return [f"{s}-01", f"{s}-02"]
    return [s]


# ── Construir tabla ───────────────────────────────────────────────────────────
bloques = []

for _, ev in p3.iterrows():
    rut  = ev["rut_key"]
    tipo = ev["tipo_formacion"]

    # período "durante": usar periodo_evento si está, si no expandir anio_evento
    pe_raw = str(ev["periodo_evento"]).strip()
    if pe_raw in ("", "nan", "None"):
        try:
            p_dur = expandir(str(int(float(ev["anio_evento"]))))
        except (ValueError, TypeError):
            p_dur = []
    else:
        p_dur = expandir(pe_raw)

    p_pre  = expandir(ev["periodo_baseline"])
    p_post = expandir(ev["periodo_resultado"])

    doc_nd = nd[nd["rut_docente"] == rut]
    if doc_nd.empty:
        continue

    # Solo incluir eventos donde AMBOS pre y post tienen datos en notas_docente
    tiene_pre  = bool(p_pre)  and not doc_nd[doc_nd["periodo"].isin(p_pre)].empty
    tiene_post = bool(p_post) and not doc_nd[doc_nd["periodo"].isin(p_post)].empty
    if not tiene_pre or not tiene_post:
        continue

    for label, periodos in [("pre", p_pre), ("durante", p_dur), ("post", p_post)]:
        if not periodos:
            continue
        sub = doc_nd[doc_nd["periodo"].isin(periodos)].copy()
        if sub.empty:
            continue

        pe = str(ev["periodo_evento"]).strip()
        pf = pe if pe not in ("", "nan", "None") else str(int(float(ev["anio_evento"])))
        sub["tipo_formacion"]    = tipo
        sub["nombre_actividad"]  = ev["nombre_actividad"]
        sub["periodo_formacion"] = pf
        sub["periodo_label"]     = label
        bloques.append(sub)

df = pd.concat(bloques, ignore_index=True)
df["nota"] = df["nota"].round(2)

cols = [
    "calificacion_id",
    "rut_docente", "nombre_docente",
    "tipo_formacion", "nombre_actividad", "periodo_formacion",
    "periodo_label", "periodo",
    "rut_alumno", "cod_asignatura", "nombre_asignatura",
    "nota", "sede", "facultad", "plan",
]
df = df[[c for c in cols if c in df.columns]]

# ── Resumen ───────────────────────────────────────────────────────────────────
print(f"\nintel.notas_alumno_pre_during_post:")
print(f"  Total filas      : {len(df):,}")
print(f"  Alumnos únicos   : {df['rut_alumno'].nunique():,}")
print(f"  Docentes únicos  : {df['rut_docente'].nunique():,}")
print(f"  Asignaturas únic.: {df['cod_asignatura'].nunique():,}")

print(f"\nPor tipo + período:")
resumen = df.groupby(["tipo_formacion", "periodo_label"]).agg(
    filas    = ("calificacion_id", "count"),
    docentes = ("rut_docente",     "nunique"),
    alumnos  = ("rut_alumno",      "nunique"),
    nota_avg = ("nota",            "mean"),
).round(3)
print(resumen.to_string())

# ── Guardar ───────────────────────────────────────────────────────────────────
df.to_csv(f"{OUT}/intel_notas_alumno_pre_during_post.csv", index=False, encoding="utf-8-sig")
df.to_sql("notas_alumno_pre_during_post", engine, schema="intel",
          if_exists="replace", index=False)
print("\nCargado : intel.notas_alumno_pre_during_post")
print("Listo.")
