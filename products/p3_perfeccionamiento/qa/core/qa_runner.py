"""
QA Runner — Análisis UCEN
Escanea la base de datos validando integridad, rangos, decisiones metodológicas
y flancos objetables. Imprime reporte con ✓ / ✗ / ⚠ y tiempo total.
"""

import sys, time
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
from sqlalchemy import create_engine, text

DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"
engine = create_engine(DB_URL)

t_inicio = time.time()

# ── Helpers ───────────────────────────────────────────────────────────────────
PASS  = "  ✓"
FAIL  = "  ✗"
WARN  = "  ⚠"

resultados = []

def ok(msg):
    print(f"{PASS} {msg}")
    resultados.append(("PASS", msg))

def fail(msg):
    print(f"{FAIL} {msg}")
    resultados.append(("FAIL", msg))

def warn(msg):
    print(f"{WARN} {msg}")
    resultados.append(("WARN", msg))

def seccion(titulo):
    print(f"\n{'─'*60}")
    print(f"  {titulo}")
    print(f"{'─'*60}")

def q(sql):
    with engine.connect() as conn:
        return conn.execute(text(sql)).scalar()

def qdf(sql):
    return pd.read_sql(sql, engine)

# ══════════════════════════════════════════════════════════════════════════════
seccion("1. CONTEOS ESPERADOS (decisiones metodológicas)")
# ══════════════════════════════════════════════════════════════════════════════

checks_conteos = [
    ("consolidados.docente",                "SELECT COUNT(*) FROM consolidados.docente",                                  2300, 2320),
    ("consolidados.docente RUTs únicos",    "SELECT COUNT(DISTINCT rut_key) FROM consolidados.docente",                   2300, 2320),
    ("analisis.docente_ambos (520)",         "SELECT COUNT(*) FROM analisis.docente_ambos",                               518,  522),
    ("analisis.p3_grupo_tratamiento total",  "SELECT COUNT(*) FROM analisis.p3_grupo_tratamiento",                        395,  410),
    ("analisis.p3_grupo_tratamiento apto",   "SELECT COUNT(*) FROM analisis.p3_grupo_tratamiento WHERE apto_p3 = true",   205,  215),
    ("intel.pre_during_post_sat (202)",      "SELECT COUNT(*) FROM intel.pre_during_post_sat",                            198,  206),
    ("intel.pre_post_sat (209)",             "SELECT COUNT(*) FROM intel.pre_post_sat",                                   205,  213),
    ("intel.trayectoria_alumno (~802)",      "SELECT COUNT(*) FROM intel.trayectoria_alumno",                             780,  820),
    ("intel.notas_docente (sin placeholders)","SELECT COUNT(*) FROM intel.notas_docente",                                 328000, 333000),
]

for nombre, sql, minv, maxv in checks_conteos:
    n = q(sql)
    if minv <= n <= maxv:
        ok(f"{nombre}: {n:,}")
    else:
        fail(f"{nombre}: {n:,}  (esperado {minv:,}–{maxv:,})")

# ══════════════════════════════════════════════════════════════════════════════
seccion("2. INTEGRIDAD FK — rut_key debe existir en tabla_docente")
# ══════════════════════════════════════════════════════════════════════════════

tablas_fk = [
    ("consolidados.evaluacion_periodo",      "rut_docente"),
    ("consolidados.calificacion_alumno",     "rut_docente"),
    ("consolidados.participacion_formacion", "rut_key"),
    ("consolidados.consolidado_jefes",       "rut_key"),
    ("analisis.docente_ambos",               "rut_key"),
    ("analisis.p3_grupo_tratamiento",        "rut_key"),
    ("intel.pre_during_post_sat",            "rut_key"),
    ("intel.pre_post_sat",                   "rut_key"),
    ("intel.trayectoria_alumno",             "rut_docente"),
    ("intel.notas_docente",                  "rut_docente"),
]

for tabla, col in tablas_fk:
    n_huerfanos = q(f"""
        SELECT COUNT(DISTINCT t.{col})
        FROM {tabla} t
        WHERE t.{col} IS NOT NULL
          AND LENGTH(t.{col}) >= 7
          AND t.{col} NOT IN (SELECT rut_key FROM consolidados.docente)
    """)
    if n_huerfanos == 0:
        ok(f"{tabla}.{col} — 0 RUTs huérfanos")
    else:
        fail(f"{tabla}.{col} — {n_huerfanos} RUTs huérfanos sin match en tabla_docente")

# ══════════════════════════════════════════════════════════════════════════════
seccion("3. CASOS CONOCIDOS — ESPINOZA y STIPPEL")
# ══════════════════════════════════════════════════════════════════════════════

esp = q("SELECT COUNT(*) FROM consolidados.docente WHERE rut_key = '16322128'")
if esp == 0:
    ok("ESPINOZA (16322128) no aparece en tabla_docente")
else:
    fail(f"ESPINOZA (16322128) aparece {esp} vez/veces en tabla_docente — debería ser 0")

tablas_esp = [
    "consolidados.evaluacion_periodo", "analisis.docente_ambos",
    "analisis.p3_grupo_tratamiento",   "intel.pre_during_post_sat",
]
for tabla in tablas_esp:
    col = "rut_docente" if "evaluacion" in tabla else "rut_key"
    n = q(f"SELECT COUNT(*) FROM {tabla} WHERE {col} = '16322128'")
    if n == 0:
        ok(f"ESPINOZA ausente en {tabla}")
    else:
        fail(f"ESPINOZA presente en {tabla}: {n} filas")

stippel = q("SELECT COUNT(*) FROM consolidados.docente WHERE rut_key = '25600736'")
if stippel == 2:
    warn(f"STIPPEL (25600736) aparece {stippel} veces en tabla_docente (2 departamentos — pendiente confirmar con contraparte)")
elif stippel == 1:
    ok(f"STIPPEL (25600736) aparece 1 vez en tabla_docente")
else:
    fail(f"STIPPEL (25600736) aparece {stippel} veces — revisar")

# ══════════════════════════════════════════════════════════════════════════════
seccion("4. RANGOS DE VALORES")
# ══════════════════════════════════════════════════════════════════════════════

checks_rango = [
    ("SAT_NOTA fuera de 1–7",
     "SELECT COUNT(*) FROM consolidados.evaluacion_respuesta WHERE pregunta_id='SAT_NOTA' AND nota_promedio NOT BETWEEN 1 AND 7"),
    ("nota_pre fuera de 1–7 en pre_during_post_sat",
     "SELECT COUNT(*) FROM intel.pre_during_post_sat WHERE nota_pre NOT BETWEEN 1 AND 7"),
    ("nota_post fuera de 1–7 en pre_during_post_sat",
     "SELECT COUNT(*) FROM intel.pre_during_post_sat WHERE nota_post NOT BETWEEN 1 AND 7"),
    ("nota alumno fuera de 1–7 en notas_docente",
     "SELECT COUNT(*) FROM intel.notas_docente WHERE nota NOT BETWEEN 1 AND 7"),
    ("cobertura_pct fuera de 0–100",
     "SELECT COUNT(*) FROM consolidados.evaluacion_periodo WHERE cobertura_pct NOT BETWEEN 0 AND 100"),
    ("delta_pre_post fuera de -6 a +6",
     "SELECT COUNT(*) FROM intel.pre_during_post_sat WHERE delta_pre_post NOT BETWEEN -6 AND 6"),
]

for nombre, sql in checks_rango:
    n = q(sql)
    if n == 0:
        ok(f"{nombre}: 0 casos")
    else:
        fail(f"{nombre}: {n} casos fuera de rango")

# ══════════════════════════════════════════════════════════════════════════════
seccion("5. NULOS CRÍTICOS")
# ══════════════════════════════════════════════════════════════════════════════

checks_nulos = [
    ("docente.rut_key",              "SELECT COUNT(*) FROM consolidados.docente WHERE rut_key IS NULL"),
    ("docente.fuente",               "SELECT COUNT(*) FROM consolidados.docente WHERE fuente IS NULL"),
    ("evaluacion_periodo.periodo",   "SELECT COUNT(*) FROM consolidados.evaluacion_periodo WHERE periodo IS NULL"),
    ("evaluacion_periodo.rut_docente","SELECT COUNT(*) FROM consolidados.evaluacion_periodo WHERE rut_docente IS NULL"),
    ("p3_grupo_tratamiento.apto_p3", "SELECT COUNT(*) FROM analisis.p3_grupo_tratamiento WHERE apto_p3 IS NULL"),
]

for nombre, sql in checks_nulos:
    n = q(sql)
    if n == 0:
        ok(f"{nombre}: sin nulos")
    else:
        fail(f"{nombre}: {n} nulos inesperados")

# ══════════════════════════════════════════════════════════════════════════════
seccion("6. PLACEHOLDERS EN TABLAS INTEL")
# ══════════════════════════════════════════════════════════════════════════════

tablas_intel_rut = [
    ("intel.notas_docente",        "rut_docente"),
    ("intel.pre_during_post_sat",  "rut_key"),
    ("intel.pre_post_sat",         "rut_key"),
    ("intel.trayectoria_alumno",   "rut_docente"),
]

for tabla, col in tablas_intel_rut:
    n = q(f"SELECT COUNT(*) FROM {tabla} WHERE LENGTH({col}) < 7")
    if n == 0:
        ok(f"{tabla} — sin RUTs placeholder (< 7 dígitos)")
    else:
        fail(f"{tabla} — {n} filas con RUT placeholder")

# ══════════════════════════════════════════════════════════════════════════════
seccion("7. FLANCOS OBJETABLES")
# ══════════════════════════════════════════════════════════════════════════════

# Docentes en más de un tipo de formación en pre_during_post_sat
multi_tipo = q("""
    SELECT COUNT(*) FROM (
        SELECT rut_key
        FROM intel.pre_during_post_sat
        GROUP BY rut_key
        HAVING COUNT(DISTINCT tipo_formacion) > 1
    ) t
""")
if multi_tipo == 0:
    ok("Ningún docente aparece en más de un tipo de formación en pre_during_post_sat")
else:
    warn(f"{multi_tipo} docentes aparecen en más de un tipo de formación — pueden inflar métricas")

# PROYECTO tiene muestra pequeña
n_doc_proyecto = q("""
    SELECT COUNT(DISTINCT rut_key) FROM intel.pre_during_post_sat
    WHERE tipo_formacion = 'PROYECTO'
""")
if n_doc_proyecto < 10:
    warn(f"PROYECTO tiene solo {n_doc_proyecto} docentes únicos — inferencia estadística limitada")
else:
    ok(f"PROYECTO: {n_doc_proyecto} docentes únicos")

# Períodos en pre_during_post_sat que no existen en evaluacion_periodo
periodos_invalidos = q("""
    SELECT COUNT(*) FROM (
        SELECT DISTINCT unnest(ARRAY[
            periodo_pre || '-01', periodo_pre || '-02',
            periodo_post || '-01', periodo_post || '-02'
        ]) AS p
        FROM intel.pre_during_post_sat
        WHERE LENGTH(periodo_pre) = 4
    ) sub
    WHERE sub.p NOT IN (
        SELECT DISTINCT periodo FROM consolidados.evaluacion_periodo
    )
    AND sub.p NOT LIKE '%2025%'
""")
if periodos_invalidos == 0:
    ok("Todos los períodos de baseline/resultado existen en evaluacion_periodo")
else:
    warn(f"{periodos_invalidos} períodos de baseline/resultado no encontrados en evaluacion_periodo")

# Alumnos en trayectoria con todas las asignaturas distintas entre períodos
asig_distintas = q("""
    SELECT COUNT(*) FROM intel.trayectoria_alumno
    WHERE asig_pre != asig_post
      AND asig_pre != asig_durante
""")
total_tray = q("SELECT COUNT(*) FROM intel.trayectoria_alumno")
pct = round(asig_distintas / total_tray * 100, 1) if total_tray > 0 else 0
if pct > 80:
    warn(f"trayectoria_alumno: {pct}% de instancias tienen asignaturas distintas entre períodos — considerar z-score")
else:
    ok(f"trayectoria_alumno: {pct}% de instancias tienen asignaturas distintas entre períodos")

# Consistencia CSV vs DB en tablas clave
n_db  = q("SELECT COUNT(*) FROM intel.pre_during_post_sat")
try:
    import os
    csv_path = r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO\Downloads\Analisis_UCEN_v2\PROCESADO\intel_pre_during_post_sat.csv"
    n_csv = len(pd.read_csv(csv_path, dtype=str))
    if n_db == n_csv:
        ok(f"intel_pre_during_post_sat — CSV ({n_csv}) == DB ({n_db})")
    else:
        fail(f"intel_pre_during_post_sat — CSV ({n_csv}) != DB ({n_db})")
except Exception as e:
    warn(f"No se pudo comparar CSV vs DB: {e}")

# ══════════════════════════════════════════════════════════════════════════════
seccion("8. COBERTURA DEL EMBUDO 520 → ANÁLISIS")
# ══════════════════════════════════════════════════════════════════════════════

n_520     = q("SELECT COUNT(DISTINCT rut_key) FROM analisis.docente_ambos")
n_form    = q("SELECT COUNT(DISTINCT rut_key) FROM analisis.p3_grupo_tratamiento")
n_apto    = q("SELECT COUNT(DISTINCT rut_key) FROM analisis.p3_grupo_tratamiento WHERE apto_p3 = true")
n_3pt     = q("SELECT COUNT(DISTINCT rut_key) FROM intel.pre_during_post_sat")
n_tray_d  = q("SELECT COUNT(DISTINCT rut_docente) FROM intel.trayectoria_alumno")

print(f"  Base perfil completo:              {n_520:>4} docentes  (100%)")
print(f"  Con participación en formación:    {n_form:>4} docentes  ({n_form/n_520*100:.1f}%)")
print(f"  Aptos P3 (eval pre + post):        {n_apto:>4} docentes  ({n_apto/n_520*100:.1f}%)")
print(f"  Con 3 puntos SAT (gráfico P3):     {n_3pt:>4} docentes  ({n_3pt/n_520*100:.1f}%)")
print(f"  En trayectoria alumnos (P3.1):     {n_tray_d:>4} docentes  ({n_tray_d/n_520*100:.1f}%)")

# ══════════════════════════════════════════════════════════════════════════════
# RESUMEN FINAL
# ══════════════════════════════════════════════════════════════════════════════
t_fin = time.time()
elapsed = t_fin - t_inicio

n_pass = sum(1 for r in resultados if r[0] == "PASS")
n_fail = sum(1 for r in resultados if r[0] == "FAIL")
n_warn = sum(1 for r in resultados if r[0] == "WARN")

print(f"\n{'═'*60}")
print(f"  RESUMEN QA")
print(f"{'═'*60}")
print(f"  ✓ PASS : {n_pass}")
print(f"  ✗ FAIL : {n_fail}")
print(f"  ⚠ WARN : {n_warn}")
print(f"  Total  : {n_pass + n_fail + n_warn} checks")
print(f"\n  Tiempo de ejecución: {elapsed:.2f} segundos")
print(f"{'═'*60}")

if n_fail == 0:
    print("\n  Base de datos consistente con las decisiones metodológicas.")
else:
    print(f"\n  {n_fail} check(s) fallaron — revisar antes de presentar.")
