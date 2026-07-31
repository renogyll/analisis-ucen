import sys
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
from sqlalchemy import create_engine, text

engine = create_engine("postgresql://ucen_user:ucen2026@localhost:5432/ucen")

with engine.connect() as conn:
    nd = pd.read_sql(text("""
        SELECT n.rut_docente, n.nombre_docente, n.cod_asignatura,
               n.nombre_asignatura, n.periodo,
               ROUND(AVG(n.nota)::numeric, 2) AS nota_avg,
               COUNT(*) AS n_alumnos
        FROM intel.notas_docente n
        WHERE n.nota IS NOT NULL
        GROUP BY n.rut_docente, n.nombre_docente, n.cod_asignatura,
                 n.nombre_asignatura, n.periodo
    """), conn)

    cap = pd.read_sql(text("""
        SELECT rut_key, tipo_formacion, periodo_resultado
        FROM analisis.p3_grupo_tratamiento
        WHERE periodo_resultado IS NOT NULL
    """), conn)

nd["rut_docente"] = nd["rut_docente"].astype(str)
cap["rut_key"]    = cap["rut_key"].astype(str)

cap_min = cap.groupby("rut_key").agg(
    periodo_cap    = ("periodo_resultado", "min"),
    tipo_formacion = ("tipo_formacion",    "first"),
).reset_index()

nd = nd.merge(cap_min, left_on="rut_docente", right_on="rut_key", how="left")

nd["capacitado"] = (
    nd["periodo_cap"].notna() &
    (nd["periodo"] >= nd["periodo_cap"])
)
nd["estado"] = nd.apply(lambda r:
    "✓ CAPACITADO"        if r["capacitado"]
    else ("~ antes de cap." if pd.notna(r["periodo_cap"])
          else "— no capacitado"),
    axis=1
)

# Filtros
palabras_excluir = ["PRACTICA","PRÁCTICA","PRÃCTICA","PROYECTO DE TIT",
                    "SEMINARIO","CICLO FORMATIVO","INTEGRACION","INTEGRACIÓN"]
def es_subjetiva(n):
    if pd.isna(n): return True
    return any(p in n.upper() for p in palabras_excluir)

nd = nd[~nd["nombre_asignatura"].apply(es_subjetiva)]
nd = nd[nd["n_alumnos"] >= 7]

# Asignaturas limpias con ambos tipos
asig_ok = nd.groupby("cod_asignatura").agg(
    n_cap   = ("capacitado", "sum"),
    n_nocap = ("capacitado", lambda x: (~x).sum()),
    n_doc   = ("rut_docente", "nunique"),
    nombre  = ("nombre_asignatura", "first"),
).reset_index()
asig_ok = asig_ok[
    (asig_ok["n_cap"] > 0) &
    (asig_ok["n_nocap"] > 0) &
    (asig_ok["n_doc"].between(2, 5))
].sort_values("n_doc", ascending=False)

# Orden cronológico de períodos
ORD_PER = ["2022-01","2022-02","2023-01","2023-02",
           "2024-01","2024-02","2025-01","2025-02","2026-01"]

for cod in asig_ok["cod_asignatura"].head(3):
    sub = nd[nd["cod_asignatura"] == cod].copy()
    sub["per_ord"] = pd.Categorical(sub["periodo"], categories=ORD_PER, ordered=True)
    sub = sub.sort_values("per_ord")
    nombre_asig = sub["nombre_asignatura"].iloc[0]

    print(f"\n{'='*72}")
    print(f"ASIGNATURA: {nombre_asig}")
    print(f"{'='*72}")
    print(f"{'Período':<12} {'Docente':<38} {'Cap. desde':<12} {'Nota avg':<10} {'N alum':<7} Estado")
    print("-"*100)
    for _, r in sub.iterrows():
        cap_desde = str(r["periodo_cap"]) if pd.notna(r["periodo_cap"]) else "—"
        print(f"{r['periodo']:<12} {r['nombre_docente'][:37]:<38} {cap_desde:<12} "
              f"{r['nota_avg']:<10} {r['n_alumnos']:<7} {r['estado']}")
