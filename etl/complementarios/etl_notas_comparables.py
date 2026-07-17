"""
ETL: notas_comparables.csv
Una fila por asignatura con nota promedio cap vs no-cap y delta.
Base: 347 asignaturas con cap + no-cap y 3+ períodos.
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text

DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"
OUT    = r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO\Downloads\Analisis_UCEN_v2\PROCESADO\notas_comparables.csv"

engine = create_engine(DB_URL)

with engine.connect() as conn:
    nd = pd.read_sql(text("""
        SELECT n.rut_docente, n.nombre_docente, n.cod_asignatura,
               n.nombre_asignatura, n.facultad, n.periodo,
               ROUND(AVG(n.nota)::numeric, 3) AS nota_avg,
               COUNT(*) AS n_alumnos
        FROM intel.notas_docente n
        WHERE n.nota IS NOT NULL
        GROUP BY n.rut_docente, n.nombre_docente, n.cod_asignatura,
                 n.nombre_asignatura, n.facultad, n.periodo
    """), conn)

    cap = pd.read_sql(text("""
        SELECT rut_key, tipo_formacion, periodo_resultado
        FROM analisis.p3_grupo_tratamiento
        WHERE periodo_resultado IS NOT NULL
    """), conn)

nd["rut_docente"] = nd["rut_docente"].astype(str)
cap["rut_key"]    = cap["rut_key"].astype(str)

# Tipo principal por docente
tipo_map = (cap.sort_values("tipo_formacion")
              .groupby("rut_key")["tipo_formacion"]
              .apply(lambda x: "DIPLOMADO" if "DIPLOMADO" in x.values
                     else ("PROYECTO" if "PROYECTO" in x.values else "TALLER"))
              .reset_index()
              .rename(columns={"tipo_formacion": "tipo_principal"}))

cap_min = cap.groupby("rut_key")["periodo_resultado"].min().reset_index()
cap_min.columns = ["rut_docente", "periodo_cap"]
cap_min = cap_min.merge(tipo_map, left_on="rut_docente", right_on="rut_key", how="left").drop(columns="rut_key")

nd = nd.merge(cap_min, on="rut_docente", how="left")

nd["capacitado"] = (
    nd["periodo_cap"].notna() &
    (nd["periodo"] >= nd["periodo_cap"])
)

# ── Filtros ───────────────────────────────────────────────────────────────────
palabras_excluir = ["PRACTICA","PRÁCTICA","PRÃCTICA","PROYECTO DE TIT",
                    "SEMINARIO","CICLO FORMATIVO","INTEGRACION PROFESIONAL",
                    "INTEGRACIÃN PROFESIONAL","INTEGRACIÓN PROFESIONAL"]
def es_subjetiva(n):
    if pd.isna(n): return True
    return any(p in n.upper() for p in palabras_excluir)

nd = nd[~nd["nombre_asignatura"].apply(es_subjetiva)]
nd = nd[nd["n_alumnos"] >= 7]

# ── Asignaturas comparables con 3+ períodos ───────────────────────────────────
asig_meta = nd.groupby("cod_asignatura").agg(
    n_cap    = ("capacitado", "sum"),
    n_nocap  = ("capacitado", lambda x: (~x).sum()),
    periodos = ("periodo",    "nunique"),
    nombre   = ("nombre_asignatura", "first"),
    facultad = ("facultad",          "first"),
).reset_index()

comparables = asig_meta[
    (asig_meta["n_cap"] > 0) &
    (asig_meta["n_nocap"] > 0) &
    (asig_meta["periodos"] >= 3)
]["cod_asignatura"]

nd_comp = nd[nd["cod_asignatura"].isin(comparables)].copy()
print(f"Asignaturas comparables : {comparables.nunique()}")
print(f"Secciones en análisis   : {len(nd_comp):,}")

# ── Nota promedio cap vs no-cap por asignatura ────────────────────────────────
def agg_grupo(g):
    cap   = g[g["capacitado"]]
    nocap = g[~g["capacitado"]]
    return pd.Series({
        "nota_cap"        : cap["nota_avg"].mean(),
        "nota_nocap"      : nocap["nota_avg"].mean(),
        "n_secciones_cap" : len(cap),
        "n_secciones_nocap": len(nocap),
        "n_alumnos_cap"   : cap["n_alumnos"].sum(),
        "n_alumnos_nocap" : nocap["n_alumnos"].sum(),
        "tipo_formacion"  : cap["tipo_principal"].dropna().mode().iloc[0] if not cap["tipo_principal"].dropna().empty else None,
        "periodos"        : g["periodo"].nunique(),
    })

resultado = nd_comp.groupby("cod_asignatura").apply(agg_grupo).reset_index()
resultado = resultado.merge(
    asig_meta[["cod_asignatura","nombre","facultad"]], on="cod_asignatura"
)

resultado["delta_nota"] = (resultado["nota_cap"] - resultado["nota_nocap"]).round(3)
resultado["cap_mejor"]  = resultado["delta_nota"] > 0

resultado["nota_cap"]   = resultado["nota_cap"].round(3)
resultado["nota_nocap"] = resultado["nota_nocap"].round(3)

# ── Resumen ───────────────────────────────────────────────────────────────────
print(f"\n=== RESULTADO GLOBAL ===")
print(f"Asignaturas analizadas  : {len(resultado)}")
print(f"Nota cap promedio       : {resultado['nota_cap'].mean():.3f}")
print(f"Nota no-cap promedio    : {resultado['nota_nocap'].mean():.3f}")
print(f"Delta promedio          : {resultado['delta_nota'].mean():+.3f}")
print(f"% asig donde cap > nocap: {resultado['cap_mejor'].mean()*100:.1f}%")

print(f"\n=== POR TIPO DE FORMACIÓN ===")
print(resultado.groupby("tipo_formacion").agg(
    n            = ("cod_asignatura",  "count"),
    nota_cap     = ("nota_cap",        "mean"),
    nota_nocap   = ("nota_nocap",      "mean"),
    delta        = ("delta_nota",      "mean"),
    pct_cap_mejor= ("cap_mejor",       "mean"),
).round(3).to_string())

print(f"\n=== POR FACULTAD ===")
print(resultado.groupby("facultad").agg(
    n      = ("cod_asignatura", "count"),
    delta  = ("delta_nota",     "mean"),
    pct_mejor = ("cap_mejor",   "mean"),
).round(3).sort_values("n", ascending=False).to_string())

# ── Guardar ───────────────────────────────────────────────────────────────────
cols_out = ["cod_asignatura","nombre","facultad","tipo_formacion",
            "periodos","n_secciones_cap","n_secciones_nocap",
            "n_alumnos_cap","n_alumnos_nocap",
            "nota_cap","nota_nocap","delta_nota","cap_mejor"]
resultado[cols_out].to_csv(OUT, index=False, encoding="utf-8-sig")
print(f"\nGuardado: {OUT}")
