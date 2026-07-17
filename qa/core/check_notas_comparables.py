import sys
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
from sqlalchemy import create_engine, text

engine = create_engine("postgresql://ucen_user:ucen2026@localhost:5432/ucen")

with engine.connect() as conn:
    nd = pd.read_sql(text("""
        SELECT rut_docente, cod_asignatura, nombre_asignatura, facultad, periodo,
               AVG(nota) AS nota_avg, COUNT(*) AS n_alumnos
        FROM intel.notas_docente
        WHERE nota IS NOT NULL
        GROUP BY rut_docente, cod_asignatura, nombre_asignatura, facultad, periodo
    """), conn)

    cap = pd.read_sql(text("""
        SELECT DISTINCT rut_key FROM analisis.p3_grupo_tratamiento
    """), conn)

nd["rut_docente"] = nd["rut_docente"].astype(str)
cap["rut_key"]    = cap["rut_key"].astype(str)
nd["capacitado"]  = nd["rut_docente"].isin(cap["rut_key"])

# Por asignatura
asig = nd.groupby(["cod_asignatura","nombre_asignatura","facultad"]).agg(
    n_cap      = ("capacitado", lambda x: x.sum()),
    n_nocap    = ("capacitado", lambda x: (~x).sum()),
    n_docentes = ("rut_docente", "nunique"),
    periodos   = ("periodo",    "nunique"),
).reset_index()

asig_ambos = asig[(asig["n_cap"] > 0) & (asig["n_nocap"] > 0)]

print(f"Asignaturas totales con notas     : {len(asig):,}")
print(f"Con solo capacitados              : {(asig['n_nocap']==0).sum()}")
print(f"Con solo no capacitados           : {(asig['n_cap']==0).sum()}")
print(f"Con AMBOS tipos (comparables)     : {len(asig_ambos)}")
print(f"  con 2+ docentes                 : {(asig_ambos['n_docentes']>=2).sum()}")
print(f"  con 3+ periodos                 : {(asig_ambos['periodos']>=3).sum()}")
print()
print("Top 15 asignaturas mas comparables (por n docentes):")
print(asig_ambos.sort_values("n_docentes", ascending=False).head(15)[
    ["nombre_asignatura","facultad","n_cap","n_nocap","n_docentes","periodos"]
].to_string(index=False))
