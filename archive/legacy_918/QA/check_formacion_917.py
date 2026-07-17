import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
from sqlalchemy import create_engine, text
import os

engine = create_engine("postgresql://ucen_user:ucen2026@localhost:5432/ucen")

ruta_csv = os.path.join(os.path.dirname(__file__), "..", "PROCESADO", "docente_918.csv")
doc = pd.read_csv(ruta_csv, encoding="utf-8-sig", dtype={"rut_key": str})
doc["rut_key"] = doc["rut_key"].str.strip()
ruts_917 = set(doc["rut_key"])

with engine.connect() as conn:
    pf = pd.read_sql(text("""
        SELECT rut_key, tipo_formacion, nombre_actividad, anio_evento
        FROM consolidados.participacion_formacion
        ORDER BY rut_key, anio_evento
    """), conn)

pf["rut_key"] = pf["rut_key"].astype(str).str.strip()
pf_917 = pf[pf["rut_key"].isin(ruts_917)].copy()

# ── SECCIÓN 1: Cobertura general ──────────────────────────────────────────────
ruts_con = set(pf_917["rut_key"].unique())
ruts_sin = ruts_917 - ruts_con

print("="*60)
print("PASO 3 — COBERTURA FORMACIÓN UNIVERSO 917")
print("="*60)

print(f"\n1. COBERTURA GENERAL")
print(f"   Total docentes:          {len(ruts_917)}")
print(f"   Con formación registrada: {len(ruts_con)}  ({len(ruts_con)/len(ruts_917)*100:.1f}%)")
print(f"   Sin formación:           {len(ruts_sin)}  ({len(ruts_sin)/len(ruts_917)*100:.1f}%)")

# ── SECCIÓN 2: Por tipo de formación ─────────────────────────────────────────
print(f"\n2. POR TIPO DE FORMACIÓN (RUTs únicos por tipo)")
print(f"   {'Tipo':<12} {'RUTs únicos':>12} {'Instancias':>12} {'% del 917':>10}")
print(f"   {'-'*50}")
for tipo in ["TALLER","DIPLOMADO","PROYECTO"]:
    sub = pf_917[pf_917["tipo_formacion"]==tipo]
    n_ruts = sub["rut_key"].nunique()
    n_inst = len(sub)
    print(f"   {tipo:<12} {n_ruts:>12} {n_inst:>12} {n_ruts/len(ruts_917)*100:>9.1f}%")

# Docentes con más de un tipo
tiene_taller   = set(pf_917[pf_917["tipo_formacion"]=="TALLER"]["rut_key"])
tiene_dipl     = set(pf_917[pf_917["tipo_formacion"]=="DIPLOMADO"]["rut_key"])
tiene_proy     = set(pf_917[pf_917["tipo_formacion"]=="PROYECTO"]["rut_key"])
solo_taller    = tiene_taller - tiene_dipl - tiene_proy
taller_y_dipl  = tiene_taller & tiene_dipl
con_dipl       = tiene_dipl

print(f"\n   Combinaciones:")
print(f"   Solo TALLER (sin diplomado ni proyecto): {len(solo_taller)}")
print(f"   TALLER + DIPLOMADO:                      {len(taller_y_dipl)}")
print(f"   Con DIPLOMADO (cualquier combo):         {len(con_dipl)}")

# ── SECCIÓN 3: Por año ────────────────────────────────────────────────────────
print(f"\n3. INSTANCIAS POR AÑO Y TIPO")
pivot = (pf_917.groupby(["anio_evento","tipo_formacion"])
         .size().unstack(fill_value=0)
         .rename_axis(None, axis=1))
for col in ["TALLER","DIPLOMADO","PROYECTO"]:
    if col not in pivot.columns:
        pivot[col] = 0
print(f"   {'Año':<8} {'TALLER':>8} {'DIPLOMADO':>10} {'PROYECTO':>10} {'Total':>8}")
print(f"   {'-'*46}")
for anio, row in pivot.iterrows():
    total = int(row.get("TALLER",0)) + int(row.get("DIPLOMADO",0)) + int(row.get("PROYECTO",0))
    print(f"   {int(anio):<8} {int(row.get('TALLER',0)):>8} {int(row.get('DIPLOMADO',0)):>10} {int(row.get('PROYECTO',0)):>10} {total:>8}")

# ── SECCIÓN 4: Los 424 solo-nómina ────────────────────────────────────────────
print(f"\n4. LOS 424 SOLO-NÓMINA — ¿CUÁNTOS TIENEN FORMACIÓN?")
nomina_solo = doc[doc["tiene_perfil_completo"]==False]["rut_key"].tolist()
pf_nom = pf_917[pf_917["rut_key"].isin(nomina_solo)]
con_form_nom = pf_nom["rut_key"].nunique()
sin_form_nom = len(nomina_solo) - con_form_nom
print(f"   Con formación: {con_form_nom}  ({con_form_nom/len(nomina_solo)*100:.1f}%)")
print(f"   Sin formación: {sin_form_nom}  ({sin_form_nom/len(nomina_solo)*100:.1f}%)")
print(f"   Por tipo:")
for tipo in ["TALLER","DIPLOMADO","PROYECTO"]:
    n = pf_nom[pf_nom["tipo_formacion"]==tipo]["rut_key"].nunique()
    print(f"     {tipo:<12}: {n}")

# ── SECCIÓN 5: Resumen funnel ─────────────────────────────────────────────────
print(f"\n5. FUNNEL 917 → FORMACIÓN → APTOS P3 (preliminar)")
print(f"   917   jerarquizados totales")
print(f"    ↓")
print(f"   {len(ruts_con):>4}  con formación registrada ({len(ruts_con)/len(ruts_917)*100:.0f}%)")
print(f"    ↓")
print(f"   {len(ruts_sin):>4}  sin formación → grupo CONTROL potencial")
print(f"   (el P3 exacto se calcula en el Paso 4 cruzando con SAT pre+post)")
