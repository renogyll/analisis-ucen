"""
Análisis de Cobertura — Reunión Contraparte
Mapea el funnel completo desde el universo de docentes hasta los análisis P3.
Genera también PROCESADO/docente_cobertura.csv (520 filas × métricas cruzadas).
"""

import sys, time
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
from sqlalchemy import create_engine, text

DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"
engine  = create_engine(DB_URL)
OUT     = r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO\Downloads\Analisis_UCEN_v2\PROCESADO"
PERIODOS = ["2023-01","2023-02","2024-01","2024-02","2025-01","2025-02"]

t0 = time.time()

def seccion(titulo):
    print(f"\n{'═'*65}")
    print(f"  {titulo}")
    print(f"{'═'*65}")

def sub(titulo):
    print(f"\n  ── {titulo}")

def q(sql):
    with engine.connect() as conn:
        return conn.execute(text(sql)).scalar()

def qdf(sql):
    return pd.read_sql(sql, engine)

# ── Cargar tablas clave una vez ───────────────────────────────────────────────
da    = qdf("SELECT * FROM analisis.docente_ambos")
ruts_520 = set(da["rut_key"].astype(str))

ep  = qdf("SELECT rut_docente, periodo, cobertura_pct FROM consolidados.evaluacion_periodo")
er  = qdf("""
    SELECT ep.rut_docente, ep.periodo, er.nota_promedio
    FROM consolidados.evaluacion_periodo ep
    JOIN consolidados.evaluacion_respuesta er ON er.evaluacion_id = ep.evaluacion_id
    WHERE er.pregunta_id = 'SAT_NOTA'
""")
pf  = qdf("SELECT rut_key, tipo_formacion, anio_evento FROM consolidados.participacion_formacion")
p3  = qdf("SELECT rut_key, tipo_formacion, apto_p3 FROM analisis.p3_grupo_tratamiento")
sat = qdf("SELECT rut_key, tipo_formacion, nota_pre, nota_durante, nota_post, delta_pre_post FROM intel.pre_during_post_sat")
pp  = qdf("SELECT rut_key FROM intel.pre_post_sat")
nd  = qdf("SELECT rut_docente, nota FROM intel.notas_docente WHERE nota IS NOT NULL")
nap = qdf("SELECT DISTINCT rut_docente FROM intel.notas_alumno_pre_during_post")

# convertir a str
for df_ in [ep, er, pf, p3, sat, pp, nd, nap]:
    for col in ["rut_docente","rut_key"]:
        if col in df_.columns:
            df_[col] = df_[col].astype(str)

# ══════════════════════════════════════════════════════════════════════════════
seccion("1. UNIVERSO COMPLETO — ¿cuántos quedan fuera de los 520?")
# ══════════════════════════════════════════════════════════════════════════════

fuentes = qdf("SELECT fuente, COUNT(*) AS n FROM consolidados.docente GROUP BY fuente ORDER BY n DESC")
total = fuentes["n"].sum()
print()
print(f"  {'Fuente':<25} {'N':>6}   {'% total':>7}")
print(f"  {'-'*42}")
for _, r in fuentes.iterrows():
    print(f"  {r['fuente']:<25} {r['n']:>6}   {r['n']/total*100:>6.1f}%")
print(f"  {'-'*42}")
print(f"  {'TOTAL':<25} {total:>6}   100.0%")

# Match entre dotación y nómina
n_dotacion = fuentes.loc[fuentes["fuente"].isin(["NOMINA_DOTACION","SOLO_DOTACION"]), "n"].sum()
n_match    = fuentes.loc[fuentes["fuente"] == "NOMINA_DOTACION", "n"].values[0]
pct_match  = n_match / n_dotacion * 100
print(f"""
  ► Match entre dotación y nómina: {pct_match:.1f}%
    De los {n_dotacion} docentes en dotación, {n_match} tienen match en nómina ({pct_match:.1f}%).
    Los {n_dotacion - n_match} restantes (SOLO_DOTACION) son registros históricos o personal
    administrativo sin función docente activa — no accionables para el análisis.
""")

# Para grupos fuera de los 520: ¿tienen datos útiles?
sub("Datos disponibles para docentes FUERA de los 520")
grupos_ext = {
    "SOLO_NOMINA":        qdf("SELECT rut_key FROM consolidados.docente WHERE fuente = 'SOLO_NOMINA'")["rut_key"].astype(str).tolist(),
    "SOLO_DOTACION":      qdf("SELECT rut_key FROM consolidados.docente WHERE fuente = 'SOLO_DOTACION'")["rut_key"].astype(str).tolist(),
    "SOLO_EVALUACIONES":  qdf("SELECT rut_key FROM consolidados.docente WHERE fuente = 'SOLO_EVALUACIONES'")["rut_key"].astype(str).tolist(),
}

print(f"\n  {'Grupo':<22} {'N total':>8} {'Con SAT':>8} {'Con Form.':>10} {'Con Notas alumnos':>18}")
print(f"  {'-'*68}")
for nombre, ruts in grupos_ext.items():
    rut_set = set(ruts)
    n   = len(rut_set)
    sat_n  = len(rut_set & set(ep["rut_docente"]))
    form_n = len(rut_set & set(pf["rut_key"]))
    nota_n = len(rut_set & set(nd["rut_docente"]))
    print(f"  {nombre:<22} {n:>8} {sat_n:>8} {form_n:>10} {nota_n:>18}")

# ══════════════════════════════════════════════════════════════════════════════
seccion("2. LOS 520 — COMPLETITUD DEL PERFIL")
# ══════════════════════════════════════════════════════════════════════════════

campos_clave = ["nivel_formacion","fecha_nacimiento","fecha_ingreso","jerarquia","sexo","tramo_edad","tramo_antiguedad"]
print(f"\n  {'Campo':<25} {'Completos':>10} {'Nulos':>8} {'% completo':>11}")
print(f"  {'-'*56}")
for campo in campos_clave:
    if campo in da.columns:
        nulos = da[campo].isna().sum() + (da[campo].astype(str).str.strip() == "").sum()
        comp  = len(da) - nulos
        print(f"  {campo:<25} {comp:>10} {nulos:>8} {comp/len(da)*100:>10.1f}%")

sub("Distribución por sexo")
print(da["sexo"].value_counts().to_string())

sub("Distribución por jerarquía")
print(da["jerarquia"].value_counts().head(8).to_string())

sub("Distribución por tramo de antigüedad")
print(da["tramo_antiguedad"].value_counts().sort_index().to_string())

# ══════════════════════════════════════════════════════════════════════════════
seccion("3. COBERTURA SAT — ¿cuántos de los 520 tienen evaluación por período?")
# ══════════════════════════════════════════════════════════════════════════════

ep_520 = ep[ep["rut_docente"].isin(ruts_520)]

sub("Docentes de los 520 con evaluación SAT por período")
print(f"\n  {'Período':>10} {'N docentes':>12} {'% de 520':>10} {'Cob.pct prom.':>14}")
print(f"  {'-'*48}")
for per in PERIODOS:
    sub_p = ep_520[ep_520["periodo"] == per]
    n  = sub_p["rut_docente"].nunique()
    cob = sub_p["cobertura_pct"].mean()
    print(f"  {per:>10} {n:>12} {n/520*100:>9.1f}% {cob:>13.1f}%")

sub("Distribución: cuántos períodos SAT tiene cada docente de los 520")
n_per_doc = ep_520.groupby("rut_docente")["periodo"].nunique().reindex(list(ruts_520)).fillna(0).astype(int)
dist = n_per_doc.value_counts().sort_index()
print(f"\n  {'N períodos':>10} {'N docentes':>12} {'% de 520':>10}")
print(f"  {'-'*34}")
for nper, ndoc in dist.items():
    print(f"  {nper:>10} {ndoc:>12} {ndoc/520*100:>9.1f}%")

sin_sat = (n_per_doc == 0).sum()
con_sat = (n_per_doc >= 1).sum()
todos   = (n_per_doc == 6).sum()
print(f"\n  Con al menos 1 período SAT : {con_sat} ({con_sat/520*100:.1f}%)")
print(f"  Sin ningún período SAT     : {sin_sat} ({sin_sat/520*100:.1f}%)")
print(f"  Con los 6 períodos         : {todos}  ({todos/520*100:.1f}%)")

# ══════════════════════════════════════════════════════════════════════════════
seccion("4. COBERTURA FORMACIÓN — participación de los 520")
# ══════════════════════════════════════════════════════════════════════════════

pf_520 = pf[pf["rut_key"].isin(ruts_520)]
con_form = pf_520["rut_key"].nunique()
sin_form = 520 - con_form
print(f"\n  Con formación    : {con_form} ({con_form/520*100:.1f}%)")
print(f"  Sin formación    : {sin_form} ({sin_form/520*100:.1f}%)  ← grupo control potencial")

sub("Por tipo de formación")
print(pf_520.groupby("tipo_formacion")["rut_key"].nunique().to_string())

sub("Por año de evento")
print(pf_520.groupby("anio_evento")["rut_key"].nunique().sort_index().to_string())

# ══════════════════════════════════════════════════════════════════════════════
seccion("5. FUNNEL 520 → P3 → ANÁLISIS SAT")
# ══════════════════════════════════════════════════════════════════════════════

n_520        = 520
n_con_form   = pf_520["rut_key"].nunique()
n_sin_form   = n_520 - n_con_form

p3_520       = p3[p3["rut_key"].isin(ruts_520)]
n_apto       = p3_520[p3_520["apto_p3"] == True]["rut_key"].nunique()
n_no_apto    = p3_520[p3_520["apto_p3"] == False]["rut_key"].nunique()

n_3pt        = sat[sat["rut_key"].isin(ruts_520)]["rut_key"].nunique()
n_2pt        = pp[pp["rut_key"].isin(ruts_520)]["rut_key"].nunique()

print(f"""
  {n_520:>4}  Perfil completo (NOMINA + DOTACION)
    │
    ├─ {n_con_form:>4}  con participación en formación  ({n_con_form/n_520*100:.1f}%)
    │     │
    │     ├─ {n_apto:>4}  aptos P3 (eval SAT pre + post)  ({n_apto/n_520*100:.1f}% del total)
    │     │     │
    │     │     ├─ {n_3pt:>4}  con 3 puntos SAT (pre+durante+post)  → intel.pre_during_post_sat
    │     │     └─ {n_2pt:>4}  con 2 puntos SAT (pre+post)          → intel.pre_post_sat
    │     │
    │     └─ {n_no_apto:>4}  con formación pero sin eval SAT completa
    │
    └─ {n_sin_form:>4}  sin formación registrada  ({n_sin_form/n_520*100:.1f}%)  ← grupo control
""")

# Flags de disponibilidad en p3
sub("Flags de evaluación en p3_grupo_tratamiento (únicos por docente)")
flags = p3_520.groupby("rut_key")[["tiene_eval_alumnos_baseline","tiene_eval_alumnos_resultado","tiene_eval_jefe"]].any() if "tiene_eval_alumnos_baseline" in p3_520.columns else None
if flags is not None:
    print(f"  Con eval alumnos baseline   : {flags['tiene_eval_alumnos_baseline'].sum()}")
    print(f"  Con eval alumnos resultado  : {flags['tiene_eval_alumnos_resultado'].sum()}")
    print(f"  Con eval jefe               : {flags['tiene_eval_jefe'].sum() if 'tiene_eval_jefe' in flags else 'N/D'}")

# ══════════════════════════════════════════════════════════════════════════════
seccion("6. RESUMEN EJECUTIVO")
# ══════════════════════════════════════════════════════════════════════════════

nd_520   = nd[nd["rut_docente"].isin(ruts_520)]
n_notas  = nd_520["rut_docente"].nunique()

filas = [
    ("Base consolidada (todos fuentes)",     total,       total/total*100),
    ("Perfil completo (NOMINA+DOTACION)",     n_520,       n_520/total*100),
    ("  Con formación registrada",            n_con_form,  n_con_form/n_520*100),
    ("  Sin formación (control potencial)",   n_sin_form,  n_sin_form/n_520*100),
    ("  Aptos P3 (eval SAT pre+post)",        n_apto,      n_apto/n_520*100),
    ("  SAT 3 puntos (P3 gráfico)",           n_3pt,       n_3pt/n_520*100),
    ("  SAT 2 puntos (pre+post)",             n_2pt,       n_2pt/n_520*100),
    ("  Con notas de alumnos",                n_notas,     n_notas/n_520*100),
]

print(f"\n  {'Universo':<40} {'N':>6}   {'% de 520':>9}")
print(f"  {'-'*58}")
for nombre, n, pct in filas:
    base = f"{pct:.1f}%" if "Base" not in nombre else "—"
    print(f"  {nombre:<40} {n:>6}   {base:>9}")

# ══════════════════════════════════════════════════════════════════════════════
seccion("7. GENERANDO docente_cobertura.csv")
# ══════════════════════════════════════════════════════════════════════════════

# Perfil base
cob = da[["rut_key","nombre","sexo","jerarquia","nivel_formacion",
          "tramo_edad","tramo_antiguedad","unidad_facultad","tipo_contrato","antiguedad_anios"]].copy()
cob["rut_key"] = cob["rut_key"].astype(str)

# --- SAT ---
ep_520_sat = er[er["rut_docente"].isin(ruts_520)]

sat_periodos = ep_520[["rut_docente","periodo","cobertura_pct"]].copy()
sat_periodos = sat_periodos[sat_periodos["periodo"].isin(PERIODOS)]

# n_periodos_sat y lista de períodos
n_per = sat_periodos.groupby("rut_docente")["periodo"].nunique().rename("n_periodos_sat")
lista = sat_periodos.groupby("rut_docente")["periodo"].apply(lambda x: " | ".join(sorted(x))).rename("periodos_sat")
cob_pct_p = sat_periodos.groupby("rut_docente")["cobertura_pct"].mean().round(1).rename("cobertura_pct_promedio")

nota_sat_avg = ep_520_sat.groupby("rut_docente")["nota_promedio"].mean().round(3).rename("nota_sat_promedio")

cob = cob.merge(n_per.reset_index().rename(columns={"rut_docente":"rut_key"}), on="rut_key", how="left")
cob = cob.merge(lista.reset_index().rename(columns={"rut_docente":"rut_key"}), on="rut_key", how="left")
cob = cob.merge(cob_pct_p.reset_index().rename(columns={"rut_docente":"rut_key"}), on="rut_key", how="left")
cob = cob.merge(nota_sat_avg.reset_index().rename(columns={"rut_docente":"rut_key"}), on="rut_key", how="left")
cob["n_periodos_sat"] = cob["n_periodos_sat"].fillna(0).astype(int)
cob["periodos_sat"]   = cob["periodos_sat"].fillna("—")

# --- Formación ---
form_agg = pf_520.groupby("rut_key").agg(
    n_eventos_formacion = ("tipo_formacion", "count"),
    tipos_formacion     = ("tipo_formacion", lambda x: " | ".join(sorted(x.unique()))),
).reset_index()
cob = cob.merge(form_agg, on="rut_key", how="left")
cob["tiene_formacion"]     = cob["n_eventos_formacion"].notna()
cob["n_eventos_formacion"] = cob["n_eventos_formacion"].fillna(0).astype(int)
cob["tipos_formacion"]     = cob["tipos_formacion"].fillna("—")

# --- P3 ---
apto_map = p3_520[p3_520["apto_p3"] == True]["rut_key"].unique()
cob["apto_p3"] = cob["rut_key"].isin(apto_map)

sat3 = sat[sat["rut_key"].isin(ruts_520)][["rut_key","nota_pre","nota_durante","nota_post","delta_pre_post"]].copy()
sat3 = sat3.groupby("rut_key").first().reset_index()  # tomar primer evento si tiene más de uno
cob = cob.merge(sat3, on="rut_key", how="left")
cob["en_pre_during_post_sat"] = cob["rut_key"].isin(sat["rut_key"].astype(str))
cob.rename(columns={"nota_pre":"nota_sat_pre","nota_durante":"nota_sat_durante",
                     "nota_post":"nota_sat_post","delta_pre_post":"delta_sat_pre_post"}, inplace=True)

# --- Notas alumnos ---
n_notas_doc = nd_520.groupby("rut_docente").agg(
    n_notas_alumnos    = ("nota", "count"),
    nota_alumno_promedio = ("nota", "mean"),
).round({"nota_alumno_promedio": 3}).reset_index().rename(columns={"rut_docente":"rut_key"})
cob = cob.merge(n_notas_doc, on="rut_key", how="left")
cob["n_notas_alumnos"]     = cob["n_notas_alumnos"].fillna(0).astype(int)
cob["en_notas_prepost"]    = cob["rut_key"].isin(nap["rut_docente"].astype(str))

# Ordenar columnas
cols_orden = [
    "rut_key","nombre","sexo","jerarquia","nivel_formacion",
    "tramo_edad","tramo_antiguedad","antiguedad_anios","unidad_facultad","tipo_contrato",
    # SAT
    "n_periodos_sat","periodos_sat","cobertura_pct_promedio","nota_sat_promedio",
    # Formación
    "tiene_formacion","tipos_formacion","n_eventos_formacion",
    # P3
    "apto_p3","en_pre_during_post_sat","nota_sat_pre","nota_sat_durante","nota_sat_post","delta_sat_pre_post",
    # Notas alumnos
    "n_notas_alumnos","nota_alumno_promedio","en_notas_prepost",
]
cob = cob[[c for c in cols_orden if c in cob.columns]]

cob.to_csv(f"{OUT}/docente_cobertura.csv", index=False, encoding="utf-8-sig")
print(f"  Guardado: docente_cobertura.csv ({len(cob)} filas × {len(cob.columns)} columnas)")
print(f"\n  Columnas: {', '.join(cob.columns.tolist())}")

# ── Tiempo total ──────────────────────────────────────────────────────────────
elapsed = time.time() - t0
print(f"\n{'═'*65}")
print(f"  Tiempo total: {elapsed:.2f} segundos")
print(f"{'═'*65}")
