"""
ETL: tag de rotación docente — punto inicial (fecha_ingreso/fecha_jerarquizacion
de analisis.universo_base) vs punto final (archivo de planeación 2026).

Pedido de la contraparte (vía el usuario, 2026-09-14): entender la rotación
del universo de docentes — quiénes siguen en la planta y quiénes no, entre
el universo histórico consolidado (analisis.universo_base, 1.144) y el
snapshot vigente de dotación 2026.

FUENTE PUNTO FINAL: "Planeación docente- Docentes planta + honorarios 2026
(1).xlsx" (raíz del repo) — RUT_PROFESOR/NOMBRE COMPLETO/NIVEL_PROF, 1.393
filas. Se entiende como snapshot vigente: no aparecer ahí = baja asumida
(decisión explícita del usuario — no se pudo verificar por otra vía, ver
D35). Los 539 RUT presentes en este archivo pero NO en universo_base
("altas nuevas") se EXCLUYEN del análisis — no tienen punto inicial, y sin
los dos extremos no se puede medir rotación para ellos (decisión del
usuario: "si tenemos los dos datos entonces no son bajas").

Se descartó `analisis.universo_base.fecha_retiro` como señal de baja: 503
de los 854 docentes que SÍ siguen en el plan 2026 también tienen esa
columna poblada (refleja fin de un contrato/período puntual, no separación
real — común en Honorario con renovación por período) — hallazgo D35.

⚠ D39 (2026-09-27): las tasas de baja ahora usan tipo_contrato_tag (contrato de entrada)
para todos; la columna híbrida de abajo se conserva pero ya no se usa en el deck. La
antigüedad tampoco se usa (inflada para las bajas, ver D39).

CRITERIO DE CONTRATO (indicación explícita del usuario, D35): a quienes
siguen activos se los reclasifica por su tipo de contrato FINAL (NIVEL_PROF
2026), no el histórico de universo_base — "entender a los que transitan
bajo el estado final resultante". A quienes se dan de baja, al no tener
estado final conocido, se les mantiene su tipo de contrato de origen (única
información disponible). `tipo_contrato_rotacion` es esa columna híbrida,
usada como corte principal de contrato en todo el análisis.

Antigüedad al corte: mismo mecanismo confirmado/estimado de D33
(fecha_ingreso directo + cota inferior por fecha_jerarquizacion cuando
falta) — sin fecha exacta de baja, para quienes se fueron esto es una
antigüedad MÍNIMA conocida, no la duración real de su paso por la
universidad (no hay forma de saberla con los datos disponibles).

SALIDA: analisis.universo_rotacion (DB), 1.144 filas (universo histórico
completo, con 539 altas nuevas excluidas desde el origen).
"""
import sys; sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text

REPO = Path(__file__).resolve().parents[3]
DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"
engine = create_engine(DB_URL)

PLAN_2026_PATH = REPO / "Planeación docente- Docentes planta + honorarios 2026 (1).xlsx"

FECHA_REFERENCIA = pd.Timestamp.today().normalize()


def cargar_base():
    return pd.read_sql(text("""
        SELECT rut_key, nombre, tipo_contrato_tag, funcion_principal, jerarquia,
               unidad_facultad, sexo, fecha_ingreso, fecha_jerarquizacion
        FROM analisis.universo_base
    """), engine)


def cargar_plan_2026():
    plan = pd.read_excel(PLAN_2026_PATH, sheet_name="Hoja1")
    plan["rut_key"] = plan["RUT_PROFESOR"].astype(str)
    plan = plan.rename(columns={"NOMBRE COMPLETO": "nombre_2026", "NIVEL_PROF": "tipo_contrato_2026"})
    return plan[["rut_key", "nombre_2026", "tipo_contrato_2026"]]


# Correcciones de RUT (D39, 2026-09-27), verificadas cruzando nómina, dotación, calificaciones,
# evaluación estudiantil, EDD y formación:
# - 15042382: el archivo 2026 lo trae como 15024382 (dígitos traspuestos; mismo nombre, Honorario).
#   Sin corregir quedaba como baja falsa + alta nueva falsa.
# - 16322128: la nómina asigna este RUT a otra persona (Honorario); en dotación, formación y el
#   archivo 2026 es un profesor Jornada con ingreso 2015. La otra persona tiene su propio RUT en
#   calificaciones y en el archivo 2026 (alta nueva). Sin corregir quedaba como transición H→J falsa.
# - 17980343 (sin corregir): el RUT aparece con dos nombres distintos según la fuente; no se puede
#   resolver con los datos. Queda como activo Jornada (el RUT está en el archivo 2026). Informar a UCEN.
CORRECCION_RUT_PLAN = {"15024382": "15042382"}
# 16322128 se corrige en el origen (shared/etl/00_base/etl_universo_base.py, RUT_NOMINA_ERRONEO).
CORRECCION_CONTRATO_BASE = {}


def aplicar_correcciones(base, plan):
    plan = plan.copy(); base = base.copy()
    plan["rut_key"] = plan["rut_key"].replace(CORRECCION_RUT_PLAN)
    for rut, contrato in CORRECCION_CONTRATO_BASE.items():
        base.loc[base["rut_key"].astype(str) == rut, "tipo_contrato_tag"] = contrato
    return base, plan


def calcular_rotacion(base, plan):
    base, plan = aplicar_correcciones(base, plan)
    df = base.merge(plan, on="rut_key", how="left")

    df["activo_2026"] = df["nombre_2026"].notna()
    df["estado"] = df["activo_2026"].map({True: "Activo", False: "Baja"})

    # tipo_contrato_rotacion: para activos, el tipo FINAL (2026); para bajas,
    # se mantiene el de origen (único dato disponible) — ver docstring/D35.
    df["tipo_contrato_rotacion"] = df["tipo_contrato_2026"].fillna(df["tipo_contrato_tag"])

    # Movilidad de régimen entre los que siguen activos
    df["transicion"] = "N/A (baja o sin cambio)"
    mask_activo = df["activo_2026"]
    j_a_h = mask_activo & (df["tipo_contrato_tag"] == "JORNADA") & (df["tipo_contrato_2026"] == "HONORARIO")
    h_a_j = mask_activo & (df["tipo_contrato_tag"] == "HONORARIO") & (df["tipo_contrato_2026"] == "JORNADA")
    df.loc[j_a_h, "transicion"] = "Jornada -> Honorario"
    df.loc[h_a_j, "transicion"] = "Honorario -> Jornada"

    # Antigüedad al corte — mismo mecanismo confirmado/estimado de D33.
    df["fecha_ingreso_dt"] = pd.to_datetime(df["fecha_ingreso"], format="%m/%d/%Y", errors="coerce")
    df["fecha_jerarquizacion_dt"] = pd.to_datetime(df["fecha_jerarquizacion"], format="%m/%d/%Y", errors="coerce")
    df["antiguedad_confirmada_anios"] = (FECHA_REFERENCIA - df["fecha_ingreso_dt"]).dt.days / 365.25
    df["antiguedad_estimada_anios"] = (FECHA_REFERENCIA - df["fecha_jerarquizacion_dt"]).dt.days / 365.25

    df["antiguedad_minima_anios"] = df["antiguedad_confirmada_anios"]
    sin_ingreso = df["fecha_ingreso_dt"].isna()
    df.loc[sin_ingreso, "antiguedad_minima_anios"] = df.loc[sin_ingreso, "antiguedad_estimada_anios"]
    df["antiguedad_fuente"] = "Sin dato"
    df.loc[~sin_ingreso, "antiguedad_fuente"] = "Confirmada (fecha_ingreso)"
    df.loc[sin_ingreso & df["fecha_jerarquizacion_dt"].notna(), "antiguedad_fuente"] = "Estimada (fecha_jerarquizacion)"

    bins = [0, 5, 10, 15, 20, 200]
    labels = ["0-4", "5-9", "10-14", "15-19", "20+"]
    df["tramo_antiguedad_corte"] = pd.cut(df["antiguedad_minima_anios"], bins=bins, labels=labels, right=False)

    return df.drop(columns=["fecha_ingreso_dt", "fecha_jerarquizacion_dt"])


if __name__ == "__main__":
    base = cargar_base()
    plan = cargar_plan_2026()
    print(f"Universo histórico: {len(base)} docentes")
    print(f"Plan 2026: {len(plan)} filas")

    df = calcular_rotacion(base, plan)

    print(f"\n--- Estado (Activo/Baja) ---")
    print(df["estado"].value_counts())

    print(f"\n--- Estado x tipo_contrato_tag (origen) ---")
    print(pd.crosstab(df["tipo_contrato_tag"], df["estado"]))

    print(f"\n--- Estado x tipo_contrato_rotacion (final para activos) ---")
    print(pd.crosstab(df["tipo_contrato_rotacion"], df["estado"]))

    print(f"\n--- Transición de régimen (activos) ---")
    print(df["transicion"].value_counts())

    print(f"\n--- Cobertura antigüedad ---")
    print(df["antiguedad_fuente"].value_counts())

    df.to_sql("universo_rotacion", engine, schema="analisis", if_exists="replace", index=False)
    print(f"\n✓ Guardado: analisis.universo_rotacion ({len(df)} filas)")

    # Tarea final aparte: CSV con SOLO nombre + RUT de los que transicionaron de
    # régimen (pedido explícito del usuario: "solo nombre y rut de los 59 y 14").
    # Se ordena por tipo de transición internamente (J->H primero, luego H->J)
    # para que las 2 tandas queden contiguas, sin exponer esa columna en el CSV.
    transicionados = df[df["transicion"] != "N/A (baja o sin cambio)"].sort_values(
        ["transicion", "nombre"])[["nombre", "rut_key"]].rename(columns={"rut_key": "rut"})
    csv_path = REPO / "outputs" / "transiciones_jornada_honorario.csv"
    transicionados.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"✓ Guardado: {csv_path} ({len(transicionados)} filas)")
