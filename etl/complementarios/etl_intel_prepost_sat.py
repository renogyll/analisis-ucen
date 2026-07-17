"""
ETL intel.prepost_sat
Una fila por docente x evento de formacion (apto_p3=True).
Calcula nota SAT_NOTA promedio en 3 momentos:
  nota_pre     : promedio SAT_NOTA en periodo baseline
  nota_durante : promedio SAT_NOTA en periodo del evento formativo
  nota_post    : promedio SAT_NOTA en periodo resultado

Para DIPLOMADO/PROYECTO los periodos son anuales (agrupa 2 semestres).
Para TALLER son semestrales exactos.
"""

import pandas as pd
from sqlalchemy import create_engine

OUT    = r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO\Downloads\Analisis_UCEN_v2\PROCESADO"
DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"

engine = create_engine(DB_URL)

# ── Cargar fuentes desde DB ───────────────────────────────────────────────────
trat = pd.read_sql("SELECT * FROM analisis.p3_grupo_tratamiento WHERE apto_p3 = true", engine)

# CM-1: solo secciones con cobertura >= 40%
# CM-2: promedio ponderado por n_alumnos_evaluaron
sat_raw = pd.read_sql("""
    SELECT e.rut_docente, e.periodo,
           e.n_alumnos_evaluaron,
           r.nota_promedio
    FROM consolidados.evaluacion_periodo e
    JOIN consolidados.evaluacion_respuesta r ON r.evaluacion_id = e.evaluacion_id
    WHERE r.pregunta_id = 'SAT_NOTA'
      AND e.cobertura_pct >= 40
      AND r.nota_promedio IS NOT NULL
""", engine)

print(f"Tratamiento aptos: {len(trat)} filas | {trat['rut_key'].nunique()} docentes")

# SAT ponderado por docente x periodo (CM-2)
sat_raw["peso_nota"] = sat_raw["nota_promedio"] * sat_raw["n_alumnos_evaluaron"]
sat_avg = (sat_raw.groupby(["rut_docente", "periodo"])
           .agg(sat_pond=("peso_nota", "sum"), n_alumnos=("n_alumnos_evaluaron", "sum"))
           .reset_index())
sat_avg["sat_nota"] = sat_avg["sat_pond"] / sat_avg["n_alumnos"]
sat_avg = sat_avg[["rut_docente", "periodo", "sat_nota"]]

# ── Mapeo de periodos durante para cada tipo ──────────────────────────────────
TALLER_DURANTE = {
    "2023-02": ["2023-02"],
    "2024-01": ["2024-01"],
    "2024-02": ["2024-02"],
}

def periodos_durante_diplomado(anio):
    a = int(anio)
    return [f"{a}-01", f"{a}-02"]

def get_nota(rut, periodos, sat_avg):
    mask = (sat_avg["rut_docente"] == rut) & (sat_avg["periodo"].isin(periodos))
    vals = sat_avg.loc[mask, "sat_nota"].dropna()
    return round(vals.mean(), 4) if len(vals) > 0 else None

# ── Construir tabla ───────────────────────────────────────────────────────────
filas = []

for _, row in trat.iterrows():
    rut  = row["rut_key"]
    tipo = row["tipo_formacion"]
    anio = row["anio_evento"]
    per  = row["periodo_evento"] if pd.notna(row.get("periodo_evento")) else None

    if tipo in ("DIPLOMADO", "PROYECTO"):
        a = int(anio)
        p_pre     = [f"{a-1}-01", f"{a-1}-02"]
        p_durante = periodos_durante_diplomado(anio)
        p_post    = [f"{a+1}-01", f"{a+1}-02"]
        label_pre     = str(a - 1)
        label_durante = str(a)
        label_post    = str(a + 1)
    elif tipo == "TALLER" and per:
        TALLER_BASELINE  = {"2023-02": "2023-01", "2024-01": "2023-02", "2024-02": "2024-01"}
        TALLER_RESULTADO = {"2023-02": "2024-01", "2024-01": "2024-02", "2024-02": "2025-01"}
        p_pre     = [TALLER_BASELINE.get(per)]
        p_durante = TALLER_DURANTE.get(per, [per])
        p_post    = [TALLER_RESULTADO.get(per)]
        label_pre     = p_pre[0]
        label_durante = per
        label_post    = p_post[0]
    else:
        continue

    filas.append({
        "rut_key":        rut,
        "nombre":         row["nombre"],
        "tipo_formacion": tipo,
        "nombre_actividad": row.get("nombre_actividad"),
        "anio_evento":    anio,
        "periodo_evento": per,
        "periodo_pre":    label_pre,
        "periodo_durante":label_durante,
        "periodo_post":   label_post,
        "nota_pre":       get_nota(rut, p_pre,     sat_avg),
        "nota_durante":   get_nota(rut, p_durante, sat_avg),
        "nota_post":      get_nota(rut, p_post,    sat_avg),
        # perfil
        "nivel_formacion":  row.get("nivel_formacion"),
        "jerarquia":        row.get("jerarquia"),
        "departamento":     row.get("departamento"),
        "unidad_facultad":  row.get("unidad_facultad"),
        "antiguedad_anios": row.get("antiguedad_anios"),
        "sexo":             row.get("sexo"),
    })

df = pd.DataFrame(filas)

# Delta calculado
df["delta_pre_post"]    = (df["nota_post"]    - df["nota_pre"]).round(4)
df["delta_pre_durante"] = (df["nota_durante"] - df["nota_pre"]).round(4)

# ── Resumen ───────────────────────────────────────────────────────────────────
print(f"\nintel.prepost_sat:")
print(f"  Total filas:     {len(df)}")
print(f"  RUTs unicos:     {df['rut_key'].nunique()}")
print(f"  Con nota_pre:    {df['nota_pre'].notna().sum()}")
print(f"  Con nota_post:   {df['nota_post'].notna().sum()}")
print(f"  Con nota_durante:{df['nota_durante'].notna().sum()}")
print(f"\nPromedio SAT por momento y tipo:")
print(df.groupby("tipo_formacion")[["nota_pre","nota_durante","nota_post","delta_pre_post"]].mean().round(3).to_string())

# ── Tabla 1: pre_during_post_sat — los 3 momentos no nulos ───────────────────
df_3pt = df[df["nota_pre"].notna() & df["nota_durante"].notna() & df["nota_post"].notna()].copy()
df_3pt.to_csv(f"{OUT}/intel_pre_during_post_sat.csv", index=False, encoding="utf-8-sig")
df_3pt.to_sql("pre_during_post_sat", engine, schema="intel", if_exists="replace", index=False)
print(f"\nCargado: intel.pre_during_post_sat ({len(df_3pt)} filas — 3 puntos completos)")

# ── Tabla 2: pre_post_sat — pre y post, durante opcional ──────────────────────
df_2pt = df[df["nota_pre"].notna() & df["nota_post"].notna()].copy()
df_2pt = df_2pt.rename(columns={
    "periodo_pre":  "periodo_baseline",
    "periodo_post": "periodo_resultado",
    "nota_pre":     "nota_1",
    "nota_post":    "nota_2",
})
cols_order = ["rut_key", "nombre", "tipo_formacion", "nombre_actividad",
              "anio_evento", "periodo_evento",
              "periodo_baseline", "periodo_durante", "periodo_resultado",
              "nota_1", "nota_durante", "nota_2",
              "delta_pre_post", "delta_pre_durante",
              "nivel_formacion", "jerarquia", "departamento", "unidad_facultad",
              "antiguedad_anios", "sexo"]
df_2pt = df_2pt[[c for c in cols_order if c in df_2pt.columns]]
df_2pt["tiene_nota_durante"] = df_2pt["nota_durante"].notna()

sin_durante = (~df_2pt["tiene_nota_durante"]).sum()
df_2pt.to_csv(f"{OUT}/intel_pre_post_sat.csv", index=False, encoding="utf-8-sig")
df_2pt.to_sql("pre_post_sat", engine, schema="intel", if_exists="replace", index=False)
print(f"Cargado: intel.pre_post_sat       ({len(df_2pt)} filas — {sin_durante} sin nota_durante)")
print("\nListo. Archivos madre no modificados.")
