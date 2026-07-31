"""
ETL evaluacion_periodo + evaluacion_respuesta
Lee 6 archivos de evaluacion estudiantil (2023-01 a 2025-02) y genera:
  - evaluacion_periodo.csv  : metadata de cada instancia (docente x asignatura x seccion x periodo)
  - evaluacion_respuesta.csv: respuestas en formato largo (una fila por instancia x pregunta)

Notas de estructura:
  - 2023-01 a 2025-01: skiprows=2 (3 filas de encabezado, usar fila 3 como nombres)
  - 2025-02          : skiprows=1 (2 filas de encabezado, usar fila 2 como nombres)
  - Columnas 0-13    : metadata de la instancia
  - Columnas 14-64   : 17 preguntas Likert x 3 cols cada una (acuerdo, indiferente, desacuerdo)
  - Columnas 65-66   : SAT_BIN (% SI, % NO)
  - Columna  67      : SAT_NOTA (promedio nota 1-7)
"""

import pandas as pd
import os

EVALS = r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO\Downloads\Analisis_UCEN_v2\CONSOLIDADO EVALUACION ESTUDIANTES UCEN 3-5-2026"
OUT   = r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO\Downloads\Analisis_UCEN_v2\PROCESADO"

# ── Definicion de preguntas por posicion de columna ───────────────────────────
# (pregunta_id, tipo, [indices de columnas en el df])
PREGUNTAS = [
    ("APR_01","LIKERT",  [14,15,16]),
    ("APR_02","LIKERT",  [17,18,19]),
    ("APR_03","LIKERT",  [20,21,22]),
    ("MET_01","LIKERT",  [23,24,25]),
    ("MET_02","LIKERT",  [26,27,28]),
    ("MET_03","LIKERT",  [29,30,31]),
    ("MET_04","LIKERT",  [32,33,34]),
    ("MET_05","LIKERT",  [35,36,37]),
    ("AFO_01","LIKERT",  [38,39,40]),
    ("AFO_02","LIKERT",  [41,42,43]),
    ("AFO_03","LIKERT",  [44,45,46]),
    ("AFO_04","LIKERT",  [47,48,49]),
    ("AFO_05","LIKERT",  [50,51,52]),
    ("AFO_06","LIKERT",  [53,54,55]),
    ("AFO_07","LIKERT",  [56,57,58]),
    ("AFO_08","LIKERT",  [59,60,61]),
    ("AFO_09","LIKERT",  [62,63,64]),
    ("SAT_BIN","BINARIO",[65,66]),
    ("SAT_NOTA","NOTA",  [67]),
]

# ── Nombres limpios para las 14 columnas de metadata ─────────────────────────
META_COLS = [
    "periodo","rut_director","rut_docente","nombre_docente",
    "cod_facultad","facultad","cod_plan","plan",
    "cod_asignatura","nombre_asignatura","seccion",
    "total_alumnos_evaluar","n_alumnos_evaluaron","cobertura_pct",
]

def limpiar_pct(serie):
    return (serie.astype(str).str.strip()
            .str.replace("%","",regex=False)
            .str.replace(",",".",regex=False)
            .str.strip()
            .replace("nan", None)
            .pipe(pd.to_numeric, errors="coerce"))

# ── Configuracion por periodo ─────────────────────────────────────────────────
PERIODOS = {
    "2023-01": 2, "2023-02": 2,
    "2024-01": 2, "2024-02": 2,
    "2025-01": 2, "2025-02": 1,   # 2025-02 tiene una fila menos de encabezado
}

all_periodos  = []
all_respuestas = []
eval_id_counter = 1

for periodo, skiprows in PERIODOS.items():
    fname = f"CONSOLIDADO EVALUACION ESTUDIANTES UCEN 3-5-2026.xlsx - {periodo}.csv"
    path  = os.path.join(EVALS, fname)

    df = pd.read_csv(path, dtype=str, skiprows=skiprows, header=0)

    # Verificar que tiene suficientes columnas
    if len(df.columns) < 68:
        print(f"  ADVERTENCIA {periodo}: solo {len(df.columns)} columnas, esperadas 68")
        continue

    # Extraer metadata
    meta = df.iloc[:, :14].copy()
    meta.columns = META_COLS
    meta["cobertura_pct"] = limpiar_pct(meta["cobertura_pct"])
    meta["rut_docente"]   = meta["rut_docente"].astype(str).str.strip()
    meta["rut_director"]  = meta["rut_director"].astype(str).str.strip()

    # Asignar IDs de instancia (continuos entre periodos)
    n = len(meta)
    meta.insert(0, "evaluacion_id", range(eval_id_counter, eval_id_counter + n))
    eval_id_counter += n

    all_periodos.append(meta)

    # Extraer respuestas por pregunta
    for pregunta_id, tipo, idx in PREGUNTAS:
        cols = df.iloc[:, idx]

        if tipo == "LIKERT":
            resp = pd.DataFrame({
                "evaluacion_id": meta["evaluacion_id"].values,
                "pregunta_id":   pregunta_id,
                "pct_acuerdo":   limpiar_pct(cols.iloc[:, 0]),
                "pct_indiferente": limpiar_pct(cols.iloc[:, 1]),
                "pct_desacuerdo": limpiar_pct(cols.iloc[:, 2]),
                "pct_si":        None,
                "pct_no":        None,
                "nota_promedio": None,
            })
        elif tipo == "BINARIO":
            resp = pd.DataFrame({
                "evaluacion_id": meta["evaluacion_id"].values,
                "pregunta_id":   pregunta_id,
                "pct_acuerdo":   None,
                "pct_indiferente": None,
                "pct_desacuerdo": None,
                "pct_si":        limpiar_pct(cols.iloc[:, 0]),
                "pct_no":        limpiar_pct(cols.iloc[:, 1]),
                "nota_promedio": None,
            })
        else:  # NOTA
            resp = pd.DataFrame({
                "evaluacion_id": meta["evaluacion_id"].values,
                "pregunta_id":   pregunta_id,
                "pct_acuerdo":   None,
                "pct_indiferente": None,
                "pct_desacuerdo": None,
                "pct_si":        None,
                "pct_no":        None,
                "nota_promedio": limpiar_pct(cols.iloc[:, 0]),
            })

        all_respuestas.append(resp)

    print(f"{periodo}: {n} instancias | skiprows={skiprows}")

# ── Consolidar y guardar ──────────────────────────────────────────────────────
df_periodos = pd.concat(all_periodos, ignore_index=True)
df_respuestas = pd.concat(all_respuestas, ignore_index=True)
df_respuestas.insert(0, "id", range(1, len(df_respuestas) + 1))

out_periodos   = os.path.join(OUT, "evaluacion_periodo.csv")
out_respuestas = os.path.join(OUT, "evaluacion_respuesta.csv")
df_periodos.to_csv(out_periodos,   index=False, encoding="utf-8-sig")
df_respuestas.to_csv(out_respuestas, index=False, encoding="utf-8-sig")

print(f"\nevaluacion_periodo.csv")
print(f"  Filas: {len(df_periodos)} | RUT docentes unicos: {df_periodos['rut_docente'].nunique()}")
print(f"\nevaluacion_respuesta.csv")
print(f"  Filas: {len(df_respuestas)} ({df_periodos['rut_docente'].nunique()} docentes x 6 periodos x 19 preguntas aprox)")
print(f"\nDistribucion por periodo:")
print(df_periodos.groupby("periodo")["evaluacion_id"].count().to_string())
print(f"\nNota promedio global (SAT_NOTA): {df_respuestas[df_respuestas['pregunta_id']=='SAT_NOTA']['nota_promedio'].astype(float).mean():.2f}")
print("\nListo. Archivos madre no modificados.")
