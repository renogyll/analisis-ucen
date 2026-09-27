"""
P1 — EDD limpia (D37, 2026-09-27). Módulo común de edd_sexo/, edd_jerarquia/ y edd_facultad/.

Reemplaza el "ajuste por año" de D36, que partía de un diagnóstico equivocado (creíamos que la
escala de la EDD había cambiado en 2024). La investigación en los datos mostró otra cosa: en
2024 y 2025 hay notas DAÑADAS, y sin ellas la EDD es estable los 4 años (0.86 / 0.88 / 0.87 /
0.89):
  - 2025: 62 notas exactamente 0 (37 de ellas con concepto "Muy Bueno"): datos vacíos
    guardados como 0.
  - 2024-2025: grupo de notas bajo 0.55 cuyo valor es casi exactamente la mitad del puntaje del
    director (razón mediana 0.47): un componente faltante contado como 0. En 2022-2023 solo el
    5% de las notas era < 0.55; en 2024-2025, el 38%.
  - Los mismos docentes con el mismo concepto en 2023 y 2024 "bajaban" de 0.88 a 0.72.

Regla (decisión del usuario 2026-09-27, opción B): nota sospechosa = edd_total == 0, o
edd_total < 0.55 en 2024-2025. Se excluyen y se promedia por docente solo lo limpio. Costo
reconocido: la regla también saca algunas notas bajas reales (~5% esperado) y 95 de 491
docentes quedan sin ninguna nota limpia. Verificación con el concepto (% "Muy Bueno"), que no
está afectado, en notas de cada diapositiva.
"""
import pandas as pd
from sqlalchemy import text

UMBRAL_MITAD = 0.55


def cargar_edd(engine):
    """1 fila por docente × año con `edd_total` original, `sospechosa` y `edd_limpia`."""
    d = pd.read_sql(text("""
        SELECT rut_key, sexo, jerarquia, facultad_jefe, concepto,
               anio_evaluacion::int AS anio, edd_total
        FROM intel.evaluacion_jefes
        WHERE tipo_contrato_tag = 'JORNADA' AND edd_total IS NOT NULL
    """), engine)
    d["sospechosa"] = (d["edd_total"] == 0) | ((d["anio"] >= 2024) & (d["edd_total"] < UMBRAL_MITAD))
    d["edd_limpia"] = d["edd_total"].where(~d["sospechosa"])
    return d


def resumen_por_anio(d):
    """Promedio original vs limpio, % de notas sospechosas y N° por año."""
    g = d.groupby("anio")
    return pd.DataFrame({"original": g["edd_total"].mean(), "limpia": g["edd_limpia"].mean(),
                         "pct_sospechosa": 100 * g["sospechosa"].mean(), "n": g.size()})


NOTA_LIMPIEZA = (
    "EDD limpia (D37): se excluyen las notas dañadas de 2024-2025 — 0 exacto (dato vacío guardado "
    f"como 0) o menor a {UMBRAL_MITAD} en 2024-2025 (nota que es la mitad del puntaje del director: "
    "componente faltante contado como 0). Sin ellas la EDD es estable 2022-2025. Cada docente se "
    "resume con el promedio de sus notas limpias."
)
