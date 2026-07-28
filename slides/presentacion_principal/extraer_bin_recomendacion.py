"""
Extrae % recomendación (P4526 % SI) desde los CSVs brutos de evaluación
para TODOS los docentes (no solo los 918 jerarquizados).
Aplica los mismos criterios de exclusión del análisis principal.
Salida: bin_recomendacion_completo.csv  (rut_key, periodo, bin, n_alumnos)
"""
import sys; sys.stdout.reconfigure(encoding="utf-8")
import os, pathlib, re
import pandas as pd

BASE_RAW = (r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO\Downloads"
            r"\Analisis_UCEN_v2\CONSOLIDADO EVALUACION ESTUDIANTES UCEN 3-5-2026")
REPO     = str(pathlib.Path(__file__).parents[2])
OUT_CSV  = os.path.join(REPO, "data", "cascade", "complementarios",
                        "bin_recomendacion_completo.csv")

PERIODOS = ["2023-01", "2023-02", "2024-01", "2024-02", "2025-01", "2025-02"]

# Asignaturas excluidas (mismo criterio del análisis principal)
EXCLUIR_ASIG = [
    "practica", "práctica", "proyecto de titulo", "proyecto de título",
    "seminario", "ciclo formativo", "integracion profesional",
    "integración profesional",
]

def asig_excluida(nombre: str) -> bool:
    n = str(nombre).lower()
    return any(k in n for k in EXCLUIR_ASIG)


def detectar_estructura(raw: pd.DataFrame):
    """
    Devuelve (data_start_row, col_rut, col_psi, col_mat, col_resp, col_cob, col_asig).
    Busca dinámicamente en las primeras 4 filas.
    """
    col_rut = col_psi = col_mat = col_resp = col_cob = col_asig = None

    # Recorrer filas 0-3 para detectar encabezados
    for r in range(min(4, raw.shape[0])):
        for c in range(raw.shape[1]):
            val = str(raw.iloc[r, c])
            # Columna RUT docente
            if col_rut is None and ("4497" in val or
               ("rut" in val.lower() and "docente" in val.lower())):
                col_rut = c
            # Columna nombre asignatura
            if col_asig is None and ("4504" in val or
               ("nombre" in val.lower() and "asignatura" in val.lower())):
                col_asig = c
            # N matriculados (total que deben evaluar)
            if col_mat is None and ("4506" in val or
               ("total" in val.lower() and "evaluar" in val.lower())):
                col_mat = c
            # N respondieron
            if col_resp is None and ("4507" in val or
               ("n de estudiantes que evaluaron" in val.lower())):
                col_resp = c
            # Cobertura
            if col_cob is None and ("4508" in val or
               "cobertura" in val.lower()):
                col_cob = c

    # Buscar columna % SI de P4526
    # La etiqueta del grupo puede estar en una fila diferente a "% SI"
    p4526_col = None
    for r in range(min(4, raw.shape[0])):
        for c in range(raw.shape[1]):
            val = str(raw.iloc[r, c])
            if "4526" in val or "recomendar" in val.lower():
                p4526_col = c
                break
        if p4526_col is not None:
            break

    if p4526_col is not None:
        # Buscar "% SI" en la misma col o adyacentes, en cualquier fila header
        for r in range(min(4, raw.shape[0])):
            for c in [p4526_col, p4526_col + 1]:
                if c < raw.shape[1] and "% si" in str(raw.iloc[r, c]).lower():
                    col_psi = c
                    break
            if col_psi is not None:
                break

    # data_start = primera fila donde rut_col tiene un número (RUT)
    data_start = None
    if col_rut is not None:
        for r in range(raw.shape[0]):
            val = str(raw.iloc[r, col_rut]).strip()
            if re.match(r"^\d{6,10}$", val):
                data_start = r
                break

    return data_start, col_rut, col_psi, col_mat, col_resp, col_cob, col_asig


def pct_to_float(val) -> float:
    """'69,23%' → 69.23   /   '100' → 100.0"""
    s = str(val).strip().replace("%", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return float("nan")


# ── Extracción ────────────────────────────────────────────────────────────────
all_rows = []

for per in PERIODOS:
    fname = f"CONSOLIDADO EVALUACION ESTUDIANTES UCEN 3-5-2026.xlsx - {per}.csv"
    fpath = os.path.join(BASE_RAW, fname)

    raw = pd.read_csv(fpath, encoding="latin-1", header=None, dtype=str,
                      low_memory=False)

    ds, c_rut, c_psi, c_mat, c_resp, c_cob, c_asig = detectar_estructura(raw)

    print(f"{per}: data_start={ds} rut={c_rut} psi={c_psi} "
          f"mat={c_mat} resp={c_resp} cob={c_cob} asig={c_asig}")

    if ds is None or c_rut is None or c_psi is None:
        print(f"  !! No se pudo detectar estructura en {per}, saltando.")
        continue

    data = raw.iloc[ds:].copy()
    data.columns = range(data.shape[1])

    data["rut_key"]    = pd.to_numeric(data[c_rut], errors="coerce")
    data["bin"]        = data[c_psi].apply(pct_to_float)
    data["n_mat"]      = pd.to_numeric(data[c_mat], errors="coerce") if c_mat else float("nan")
    data["n_resp"]     = pd.to_numeric(data[c_resp], errors="coerce") if c_resp else float("nan")
    data["cobertura"]  = data[c_cob].apply(pct_to_float) if c_cob else float("nan")
    data["asignatura"] = data[c_asig].astype(str) if c_asig else ""
    data["periodo"]    = per

    # Eliminar filas sin RUT o sin % SI
    data = data.dropna(subset=["rut_key", "bin"])
    data["rut_key"] = data["rut_key"].astype(int)

    # ── Filtros (igual que análisis principal) ────────────────────────────────
    n_ini = len(data)

    # Cobertura ≥ 40%
    if c_cob:
        data = data[data["cobertura"] >= 40]

    # Sección ≥ 7 alumnos matriculados
    if c_mat:
        data = data[data["n_mat"] >= 7]

    # Excluir asignaturas prácticas
    data = data[~data["asignatura"].apply(asig_excluida)]

    n_fin = len(data)
    print(f"  filas: {n_ini} → {n_fin} tras filtros  |  "
          f"docentes únicos: {data['rut_key'].nunique()}")

    # ── Agregar por docente: % SI ponderado por n_resp ────────────────────────
    if c_resp and data["n_resp"].notna().any():
        data["bin_w"] = data["bin"] * data["n_resp"]
        agg = (data.groupby("rut_key")
               .agg(bin=("bin_w", "sum"),
                    n_total=("n_resp", "sum"))
               .reset_index())
        agg["bin"] = agg["bin"] / agg["n_total"]
        agg.rename(columns={"n_total": "n_alumnos"}, inplace=True)
    else:
        agg = (data.groupby("rut_key")
               .agg(bin=("bin", "mean"),
                    n_alumnos=("n_mat", "sum"))
               .reset_index())

    agg["periodo"] = per
    all_rows.append(agg)

# ── Consolidar y guardar ──────────────────────────────────────────────────────
result = pd.concat(all_rows, ignore_index=True)
result = result[["rut_key", "periodo", "bin", "n_alumnos"]]

result.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
print(f"\n✓ Guardado: {OUT_CSV}")
print(f"  {len(result)} filas  |  {result['rut_key'].nunique()} docentes únicos")
print(result.groupby("periodo")["rut_key"].nunique().to_string())
