import sys
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
from sqlalchemy import create_engine, text

engine = create_engine("postgresql://ucen_user:ucen2026@localhost:5432/ucen")

with engine.connect() as conn:
    nd = pd.read_sql(text("""
        SELECT n.rut_docente, n.cod_asignatura, n.nombre_asignatura,
               n.facultad, n.periodo, n.nota
        FROM intel.notas_docente n
        WHERE n.nota IS NOT NULL
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
nd["aprobado"]   = nd["nota"] >= 4.0

# ── Tasa institucional (base completa 327.276) ─────────────────────────────
print("=" * 55)
print("TASA GLOBAL INSTITUCIONAL (327.276 registros)")
print("=" * 55)
total = len(nd)
aprob = nd["aprobado"].sum()
reprob = (~nd["aprobado"]).sum()
print(f"  Aprobados   : {aprob:>7,}  ({aprob/total*100:.1f}%)")
print(f"  Reprobados  : {reprob:>7,}  ({reprob/total*100:.1f}%)")

# ── Aplicar filtros F1 + F2 ────────────────────────────────────────────────
palabras = ["PRACTICA","PRÁCTICA","PRÃCTICA","PROYECTO DE TIT",
            "SEMINARIO","CICLO FORMATIVO","INTEGRACION PROFESIONAL",
            "INTEGRACIÃN PROFESIONAL","INTEGRACIÓN PROFESIONAL"]
def es_subjetiva(n):
    if pd.isna(n): return True
    return any(p in n.upper() for p in palabras)

nd_f = nd[~nd["nombre_asignatura"].apply(es_subjetiva)].copy()

# F2: secciones con >= 7 alumnos
secciones_validas = (nd_f.groupby(["rut_docente","cod_asignatura","periodo"])
                         .size().reset_index(name="n_alumnos"))
secciones_validas = secciones_validas[secciones_validas["n_alumnos"] >= 7]
nd_f = nd_f.merge(secciones_validas[["rut_docente","cod_asignatura","periodo"]],
                  on=["rut_docente","cod_asignatura","periodo"])

# F3: asignaturas con ambos tipos y 3+ períodos
asig_meta = (nd_f.groupby("cod_asignatura")
             .agg(n_cap=("capacitado","sum"),
                  n_nocap=("capacitado", lambda x: (~x).sum()),
                  periodos=("periodo","nunique"))
             .reset_index())
comparables = asig_meta[
    (asig_meta["n_cap"] > 0) &
    (asig_meta["n_nocap"] > 0) &
    (asig_meta["periodos"] >= 3)
]["cod_asignatura"]

nd_338 = nd_f[nd_f["cod_asignatura"].isin(comparables)].copy()

print(f"\n{'='*55}")
print(f"TASA EN 338 ASIGNATURAS COMPARABLES")
print(f"{'='*55}")
t = len(nd_338)
a = nd_338["aprobado"].sum()
r = (~nd_338["aprobado"]).sum()
print(f"  Registros   : {t:>7,}")
print(f"  Aprobados   : {a:>7,}  ({a/t*100:.1f}%)")
print(f"  Reprobados  : {r:>7,}  ({r/t*100:.1f}%)")

print(f"\n  --- Por grupo ---")
for grupo, label in [(True, "Docente CAPACITADO"), (False, "Docente NO CAPACITADO")]:
    sub = nd_338[nd_338["capacitado"] == grupo]
    t2  = len(sub)
    a2  = sub["aprobado"].sum()
    r2  = (~sub["aprobado"]).sum()
    print(f"\n  {label} ({t2:,} registros)")
    print(f"    Aprobados  : {a2:,}  ({a2/t2*100:.1f}%)")
    print(f"    Reprobados : {r2:,}  ({r2/t2*100:.1f}%)")

print(f"\n  --- Por facultad ---")
fac = nd_338.groupby("facultad").agg(
    n         = ("aprobado", "count"),
    pct_aprob = ("aprobado", "mean"),
).round(3)
fac["pct_aprob"] = (fac["pct_aprob"] * 100).round(1)
print(fac.sort_values("n", ascending=False).to_string())
