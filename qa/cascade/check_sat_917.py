import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
from sqlalchemy import create_engine, text
import os

engine = create_engine("postgresql://ucen_user:ucen2026@localhost:5432/ucen")

# Cargar universo 917
ruta_csv = os.path.join(os.path.dirname(__file__), "..", "PROCESADO", "docente_918.csv")
doc = pd.read_csv(ruta_csv, encoding="utf-8-sig", dtype={"rut_key": str})
doc["rut_key"] = doc["rut_key"].str.strip()
ruts_917 = set(doc["rut_key"])

PERIODOS = ["2023-01","2023-02","2024-01","2024-02","2025-01","2025-02"]

# SAT con CM-1 (cobertura ≥40%) y CM-2 (ponderado por n_alumnos_evaluaron)
with engine.connect() as conn:
    sat_raw = pd.read_sql(text("""
        SELECT e.rut_docente AS rut_key,
               e.periodo,
               e.n_alumnos_evaluaron,
               e.cobertura_pct,
               r.nota_promedio
        FROM consolidados.evaluacion_periodo e
        JOIN consolidados.evaluacion_respuesta r ON r.evaluacion_id = e.evaluacion_id
        WHERE r.pregunta_id = 'SAT_NOTA'
        AND e.cobertura_pct >= 40
        ORDER BY e.rut_docente, e.periodo
    """), conn)

sat_raw["rut_key"] = sat_raw["rut_key"].astype(str).str.strip()

# Filtrar solo docentes del universo 917
sat = sat_raw[sat_raw["rut_key"].isin(ruts_917)].copy()

# Promedio ponderado por periodo y docente (CM-2)
sat["peso_nota"] = sat["nota_promedio"] * sat["n_alumnos_evaluaron"]
sat_per = (sat.groupby(["rut_key","periodo"])
           .agg(sat_pond=("peso_nota","sum"),
                n_alumnos=("n_alumnos_evaluaron","sum"))
           .reset_index())
sat_per["sat_periodo"] = sat_per["sat_pond"] / sat_per["n_alumnos"]

# Pivot: una fila por docente, columna por periodo
pivot = sat_per.pivot(index="rut_key", columns="periodo", values="sat_periodo")
pivot.columns.name = None
for p in PERIODOS:
    if p not in pivot.columns:
        pivot[p] = float("nan")
pivot = pivot[PERIODOS].reset_index()

# Merge con perfil
df = doc.merge(pivot, on="rut_key", how="left")
df["n_periodos_sat"] = df[PERIODOS].notna().sum(axis=1)

# ── SECCIÓN 1: Visión general ─────────────────────────────────────────────────
print("="*60)
print("PASO 2 — COBERTURA SAT UNIVERSO 917")
print("="*60)

con_sat = (df["n_periodos_sat"] > 0).sum()
sin_sat = (df["n_periodos_sat"] == 0).sum()
print(f"\n1. COBERTURA GENERAL")
print(f"   Total docentes:            {len(df)}")
print(f"   Con al menos 1 período SAT: {con_sat}  ({con_sat/len(df)*100:.1f}%)")
print(f"   Sin ningún período SAT:    {sin_sat}  ({sin_sat/len(df)*100:.1f}%)")

# ── SECCIÓN 2: Por origen ─────────────────────────────────────────────────────
print(f"\n2. COBERTURA SAT POR ORIGEN")
print(f"   {'Origen':<12} {'Total':>6} {'Con SAT':>8} {'Sin SAT':>8} {'%':>6}")
print(f"   {'-'*44}")
for origen in ["ambos","nomina","dotacion"]:
    sub = df[df["origen"]==origen]
    cs = (sub["n_periodos_sat"]>0).sum()
    ss = (sub["n_periodos_sat"]==0).sum()
    pct = cs/len(sub)*100 if len(sub)>0 else 0
    print(f"   {origen:<12} {len(sub):>6} {cs:>8} {ss:>8} {pct:>5.1f}%")

# ── SECCIÓN 3: Por n° períodos ────────────────────────────────────────────────
print(f"\n3. DISTRIBUCIÓN POR N° DE PERÍODOS SAT (de 6 posibles)")
dist = df["n_periodos_sat"].value_counts().sort_index()
for n, cnt in dist.items():
    barra = "█" * (cnt // 5)
    print(f"   {n} períodos: {cnt:4d}  {barra}")

# ── SECCIÓN 4: Cobertura por período ─────────────────────────────────────────
print(f"\n4. DOCENTES CON SAT VÁLIDO POR PERÍODO (cobertura ≥40%, ponderado)")
print(f"   {'Período':<10} {'N docentes':>10} {'% del 917':>10} {'SAT prom':>10}")
print(f"   {'-'*44}")
for p in PERIODOS:
    n = df[p].notna().sum()
    prom = df[p].mean()
    print(f"   {p:<10} {n:>10} {n/len(df)*100:>9.1f}% {prom:>10.3f}")

# ── SECCIÓN 5: Perfil completo vs solo nómina ─────────────────────────────────
print(f"\n5. LOS 424 SOLO-NÓMINA — ¿CUÁNTOS TIENEN SAT?")
nomina_solo = df[df["tiene_perfil_completo"]==False]
cs_n = (nomina_solo["n_periodos_sat"]>0).sum()
ss_n = (nomina_solo["n_periodos_sat"]==0).sum()
print(f"   Con SAT:     {cs_n}  ({cs_n/len(nomina_solo)*100:.1f}%)")
print(f"   Sin SAT:     {ss_n}  ({ss_n/len(nomina_solo)*100:.1f}%)")
print(f"\n   Distribución por períodos (solo nómina):")
dist_n = nomina_solo["n_periodos_sat"].value_counts().sort_index()
for n, cnt in dist_n.items():
    print(f"     {n} períodos: {cnt:4d}")

# ── SECCIÓN 6: Resumen ejecutivo ──────────────────────────────────────────────
print(f"\n6. RESUMEN EJECUTIVO")
con_3plus = (df["n_periodos_sat"] >= 3).sum()
con_2plus = (df["n_periodos_sat"] >= 2).sum()
nomina_con_sat = (nomina_solo["n_periodos_sat"] > 0).sum()
print(f"   917 docentes jerarquizados")
print(f"   → {con_sat} ({con_sat/len(df)*100:.0f}%) tienen al menos 1 período SAT válido")
print(f"   → {con_2plus} ({con_2plus/len(df)*100:.0f}%) tienen ≥2 períodos (aptos para pre/post)")
print(f"   → {con_3plus} ({con_3plus/len(df)*100:.0f}%) tienen ≥3 períodos (aptos para pre/durante/post)")
print(f"   → {nomina_con_sat} de los 424 solo-nómina tienen SAT")
print(f"   → {ss_n} de los 424 solo-nómina NO tienen SAT (fuera del análisis)")
