import sys
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
from sqlalchemy import create_engine, text

engine = create_engine("postgresql://ucen_user:ucen2026@localhost:5432/ucen")

with engine.connect() as conn:
    nd = pd.read_sql(text("""
        SELECT n.rut_docente, n.cod_asignatura, n.nombre_asignatura,
               n.facultad, n.periodo,
               AVG(n.nota) AS nota_avg, COUNT(*) AS n_alumnos
        FROM intel.notas_docente n
        WHERE n.nota IS NOT NULL
        GROUP BY n.rut_docente, n.cod_asignatura, n.nombre_asignatura,
                 n.facultad, n.periodo
    """), conn)

    cap = pd.read_sql(text("""
        SELECT rut_key, periodo_resultado
        FROM analisis.p3_grupo_tratamiento
        WHERE periodo_resultado IS NOT NULL
    """), conn)

nd["rut_docente"] = nd["rut_docente"].astype(str)
cap["rut_key"]    = cap["rut_key"].astype(str)
cap_min = cap.groupby("rut_key")["periodo_resultado"].min().reset_index()
cap_min.columns = ["rut_docente", "periodo_cap"]
nd = nd.merge(cap_min, on="rut_docente", how="left")
nd["capacitado"] = nd["periodo_cap"].notna() & (nd["periodo"] >= nd["periodo_cap"])

# Filtro F1 — version check_notas_filtros (347)
palabras_v1 = ["PRACTICA","PRÁCTICA","PRÃCTICA","PROYECTO DE TIT",
               "SEMINARIO","CICLO FORMATIVO","INTEGRACION","INTEGRACIÓN"]

# Filtro F1 — version etl_notas_comparables (333)
palabras_v2 = ["PRACTICA","PRÁCTICA","PRÃCTICA","PROYECTO DE TIT",
               "SEMINARIO","CICLO FORMATIVO","INTEGRACION","INTEGRACIÓN","INTEGRACI"]

def filtra(nd, palabras):
    def es_subjetiva(n):
        if pd.isna(n): return True
        return any(p in n.upper() for p in palabras)
    nd2 = nd[~nd["nombre_asignatura"].apply(es_subjetiva)]
    nd2 = nd2[nd2["n_alumnos"] >= 7]
    asig = nd2.groupby("cod_asignatura").agg(
        n_cap    = ("capacitado", "sum"),
        n_nocap  = ("capacitado", lambda x: (~x).sum()),
        periodos = ("periodo",    "nunique"),
        nombre   = ("nombre_asignatura", "first"),
    ).reset_index()
    return asig[(asig["n_cap"] > 0) & (asig["n_nocap"] > 0) & (asig["periodos"] >= 3)]["cod_asignatura"]

v1 = filtra(nd, palabras_v1)
v2 = filtra(nd, palabras_v2)

print(f"Version check (347): {len(v1)}")
print(f"Version ETL   (333): {len(v2)}")
print(f"Diferencia         : {len(v1) - len(v2)}")

perdidas = set(v1) - set(v2)
print(f"\nAsignaturas en 347 pero no en 333 ({len(perdidas)}):")
for cod in perdidas:
    nombre = nd[nd["cod_asignatura"]==cod]["nombre_asignatura"].iloc[0]
    print(f"  {cod}  {nombre}")
