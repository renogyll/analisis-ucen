"""
P1 — EDD ajustada por año (D36, 2026-09-26). Módulo común de edd_sexo/, edd_jerarquia/ y
edd_facultad/.

Problema: la escala de `edd_total` cambia entre años. Promedio 0.86-0.88 en 2022-2023 y
0.67-0.69 en 2024-2025, con dispersión que se duplica (desv. est. 0.15 → 0.33). Promediar
años distintos por docente mezcla escalas: quien solo fue evaluado en 2024-2025 queda más
bajo por el año, no por su desempeño (216 de 491 docentes Jornada; VRIIP entero).

Solución: estandarizar dentro de cada año (z = (edd − media del año) / desv. est. del año)
y re-expresar en la escala del año de referencia (2025, la vigente y la de mayor cobertura):
    edd_aj = z · desv_2025 + media_2025
Es una transformación lineal del z-score, así que las pruebas t dan exactamente lo mismo que
con z; la ventaja es que los números se leen en la escala 0-1 conocida. Se estandariza con
media y desv. est. (no solo restando la media) porque la dispersión también cambia entre años.
"""
import pandas as pd
from sqlalchemy import text

ANIO_REF = 2025


def cargar_edd(engine):
    """1 fila por docente × año, con `edd_total` original y `edd_aj` (ajustada por año)."""
    d = pd.read_sql(text("""
        SELECT rut_key, sexo, jerarquia, facultad_jefe,
               anio_evaluacion::int AS anio, edd_total
        FROM intel.evaluacion_jefes
        WHERE tipo_contrato_tag = 'JORNADA' AND edd_total IS NOT NULL
    """), engine)
    g = d.groupby("anio")["edd_total"]
    d["z"] = (d["edd_total"] - g.transform("mean")) / g.transform("std")
    ref = d.loc[d["anio"] == ANIO_REF, "edd_total"]
    d["edd_aj"] = d["z"] * ref.std() + ref.mean()
    return d


def resumen_por_anio(d):
    """Media y desv. est. de `edd_total` por año (para notas y la diapositiva por año)."""
    return d.groupby("anio")["edd_total"].agg(["count", "mean", "std"])


NOTA_AJUSTE = (
    "EDD ajustada por año: la escala de edd_total cambió entre 2023 y 2024 (promedio 0.87 → 0.68, "
    "dispersión que se duplica). Cada evaluación se estandarizó dentro de su año y se expresó en "
    f"la escala de {ANIO_REF}; después se promedió por docente. Las pruebas t equivalen a comparar "
    "z-scores por año. Ver D36."
)
