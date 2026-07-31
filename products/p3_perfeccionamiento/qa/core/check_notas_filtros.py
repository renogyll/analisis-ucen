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

    # Capacitados con su período de resultado (post-capacitación)
    cap = pd.read_sql(text("""
        SELECT rut_key, periodo_resultado
        FROM analisis.p3_grupo_tratamiento
        WHERE periodo_resultado IS NOT NULL
    """), conn)

nd["rut_docente"] = nd["rut_docente"].astype(str)
cap["rut_key"]    = cap["rut_key"].astype(str)

print("=" * 55)
print("CASCADA DE FILTROS — NOTAS COMPARABLES")
print("=" * 55)
print(f"\nBase: {len(nd):>8,}  secciones (docente × asig × período)")
print(f"      {nd['cod_asignatura'].nunique():>8,}  asignaturas distintas")

# ── FILTRO 1: Excluir evaluación subjetiva ────────────────
palabras_excluir = [
    "PRACTICA", "PRÁCTICA", "PROYECTO DE TITULO", "PROYECTO DE TÍTULO",
    "SEMINARIO DE INVESTIGACION", "SEMINARIO DE INVESTIGACIÓN",
    "SEMINARIO DE TESIS", "SEMINARIO INTEGRATIVO", "SEMINARIO DE GRADO",
    "CICLO FORMATIVO", "INTEGRACION PROFESIONAL", "INTEGRACIÓN PROFESIONAL",
    "CERTIFICACION", "CERTIFICACIÓN", "RCP", "PRACTICA INICIAL",
]

def es_subjetiva(nombre):
    if pd.isna(nombre):
        return True
    n = nombre.upper()
    return any(p in n for p in palabras_excluir)

nd["subjetiva"] = nd["nombre_asignatura"].apply(es_subjetiva)
nd_f1 = nd[~nd["subjetiva"]].copy()

print(f"\n  Filtro 1 — Excluir asignaturas de evaluación subjetiva")
print(f"  (prácticas, proyectos título, seminarios, ciclos)")
print(f"  └─ {nd_f1['cod_asignatura'].nunique():>6,}  asignaturas restantes")
print(f"     {len(nd_f1):>6,}  secciones")

# ── FILTRO 2: Mínimo 7 alumnos por sección ────────────────
nd_f2 = nd_f1[nd_f1["n_alumnos"] >= 7].copy()

print(f"\n  Filtro 2 — Mínimo 7 alumnos por sección")
print(f"  └─ {nd_f2['cod_asignatura'].nunique():>6,}  asignaturas restantes")
print(f"     {len(nd_f2):>6,}  secciones")

# ── FILTRO 3: Temporalidad ────────────────────────────────
# Para cada docente capacitado, obtener su período de resultado más temprano
cap_min = cap.groupby("rut_key")["periodo_resultado"].min().reset_index()
cap_min.columns = ["rut_docente", "periodo_cap"]

nd_f3 = nd_f2.merge(cap_min, on="rut_docente", how="left")

# Etiquetar correctamente:
# - capacitado: docente en cap Y período >= periodo_cap
# - no capacitado: docente no en cap, O período < periodo_cap
nd_f3["capacitado"] = (
    nd_f3["periodo_cap"].notna() &
    (nd_f3["periodo"] >= nd_f3["periodo_cap"])
)

print(f"\n  Filtro 3 — Temporalidad (cap solo en períodos post-capacitación)")
print(f"  └─ {nd_f3['capacitado'].sum():>6,}  secciones 'capacitado'")
print(f"     {(~nd_f3['capacitado']).sum():>6,}  secciones 'no capacitado'")

# ── Asignaturas con AMBOS tipos ───────────────────────────
asig = nd_f3.groupby("cod_asignatura").agg(
    n_cap    = ("capacitado", lambda x: x.sum()),
    n_nocap  = ("capacitado", lambda x: (~x).sum()),
    periodos = ("periodo",    "nunique"),
    nombre   = ("nombre_asignatura", "first"),
    facultad = ("facultad",   "first"),
).reset_index()

asig_ambos = asig[(asig["n_cap"] > 0) & (asig["n_nocap"] > 0)]

print(f"\n  Con AMBOS tipos en misma asignatura (comparables)")
print(f"  └─ {len(asig_ambos):>6,}  asignaturas comparables")
print(f"     {(asig_ambos['periodos'] >= 3).sum():>6,}  con 3+ períodos")

# ── Resumen ejecutivo ─────────────────────────────────────
print()
print("=" * 55)
print("CASCADA RESUMEN")
print("=" * 55)
print(f"  2.503  asignaturas con nota válida")
print(f"    F1 → {nd_f1['cod_asignatura'].nunique():>4}  excl. evaluación subjetiva")
print(f"    F2 → {nd_f2['cod_asignatura'].nunique():>4}  excl. secciones < 7 alumnos")
print(f"    F3 → {len(asig_ambos):>4}  con cap+no-cap en período correcto")

# Top asignaturas comparables
print(f"\nTop 15 asignaturas comparables tras filtros:")
print(asig_ambos.sort_values("n_cap", ascending=False).head(15)[
    ["nombre","facultad","n_cap","n_nocap","periodos"]
].to_string(index=False))
