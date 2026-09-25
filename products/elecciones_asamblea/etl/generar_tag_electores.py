"""
ETL: tag Elector / Elegible por docente — reglamento de elección de Asamblea
General (pedido nuevo de la contraparte, 2026-09-13).

FUENTE : analisis.universo_base (1.144 docentes)
SALIDA : analisis.universo_electores (DB)

Reglas (ver D33 en docs/DECISIONES_METODOLOGICAS.md para el detalle completo
y los caveats de cobertura de datos):

  Art. 2° (Elector) — "cualquier jerarquía académica" + antigüedad
  ininterrumpida ≥ 3 años. No se filtra por jerarquía (el artículo no
  restringe rango); sí se excluye a quienes no son académicos
  (funcion_principal == 'ADMINISTRATIVO').

  Art. 4° (Elegible/Candidato) — "las 2 jerarquías académicas más altas" +
  antigüedad ininterrumpida ≥ 8 años. Mapeo de "las 2 más altas" (decisión
  explícita del usuario, 2026-09-13, ver D33 — supuesto documentado,
  pendiente de que la contraparte lo confirme o corrija): lectura literal de
  "dos jerarquías" (dos categorías, no dos niveles de rango) = TITULAR
  DOCENTE + TITULAR REGULAR, las dos líneas de carrera académica que
  alcanzan el rango máximo ("igualdad de rango académico" entre ambas, según
  `DOCUMENTO EXPLICATIVO DE CATEGORIA VARIAS`). Deliberadamente NO incluye
  Asociado (ninguna de las 2 líneas) — evita la ambigüedad de si "Asociado
  Docente" cuenta, que el documento de apoyo no resolvía.

Cobertura de datos: `fecha_ingreso` solo existe para 547/1.144 docentes
(origen AMBOS + SOLO_DOTACION) — el resto (SOLO_NOMINA + SOLO_FORMACION,
597 docentes, la gran mayoría Honorario) queda marcado 'Sin dato', no 'No'.

Estimación por `fecha_jerarquizacion` (agregada 2026-09-13, ver D33): para
los 'Sin dato' de arriba, `fecha_jerarquizacion` tiene mejor cobertura
(916/1.144, incluye 424 de los 597 sin `fecha_ingreso`) y sirve como **cota
inferior segura** de antigüedad — jerarquizarse ocurre después de ingresar,
nunca antes, así que "años desde jerarquización ≥ umbral" implica
antigüedad real ≥ umbral también. Es unidireccional: solo promueve
'Sin dato' → 'Sí (estimado)' cuando la cota ya cruza el umbral; nunca
degrada a 'No' (alguien jerarquizado hace poco pudo haber ingresado mucho
antes). Caveat de calidad de datos: varias fechas se repiten masivamente
(ej. 12/2/2024 × 37, 10/26/2016 × 29) — probablemente son fechas de sesión
de comisión evaluadora (evento batch), no la fecha individual exacta de
cada docente; no invalida la lógica de cota inferior, pero es una
aproximación, no un dato duro — por eso se mantiene en un tag separado
('Sí (estimado)'), nunca mezclado con 'Sí' confirmado por `fecha_ingreso`.
"""
import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
from sqlalchemy import create_engine, text

DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"
engine = create_engine(DB_URL)

# Fecha de referencia para calcular antigüedad ("fecha de convocatoria" del
# reglamento) — placeholder: hoy. Reemplazar por la fecha real apenas la
# contraparte la confirme y volver a correr el script.
FECHA_REFERENCIA = pd.Timestamp.today().normalize()

UMBRAL_ELECTOR_ANIOS = 3
UMBRAL_ELEGIBLE_ANIOS = 8

# Ver docstring arriba y D33 — supuesto documentado, no confirmado por la contraparte.
JERARQUIAS_ELEGIBLE = {"TITULAR DOCENTE", "TITULAR REGULAR"}


def cargar_base():
    return pd.read_sql(text("""
        SELECT rut_key, tipo_contrato_tag, funcion_principal, jerarquia,
               unidad_facultad, fecha_ingreso, fecha_jerarquizacion
        FROM analisis.universo_base
    """), engine)


def calcular_tags(df):
    df = df.copy()
    df["fecha_ingreso_dt"] = pd.to_datetime(df["fecha_ingreso"], format="%m/%d/%Y", errors="coerce")
    df["antiguedad_ref_anios"] = (FECHA_REFERENCIA - df["fecha_ingreso_dt"]).dt.days / 365.25

    df["fecha_jerarquizacion_dt"] = pd.to_datetime(df["fecha_jerarquizacion"], format="%m/%d/%Y", errors="coerce")
    df["anios_desde_jerarquizacion"] = (FECHA_REFERENCIA - df["fecha_jerarquizacion_dt"]).dt.days / 365.25

    es_administrativo = df["funcion_principal"] == "ADMINISTRATIVO"
    sin_dato = df["fecha_ingreso_dt"].isna()

    def _tag_umbral(anios_ok, umbral):
        tag = pd.Series("Sí", index=df.index)
        tag[~anios_ok] = "No"
        tag[sin_dato] = "Sin dato"
        # Promoción por cota inferior (fecha_jerarquizacion): solo sobre los
        # que quedaron 'Sin dato' por falta de fecha_ingreso — nunca degrada
        # a 'No', ver docstring.
        promovible = sin_dato & (df["anios_desde_jerarquizacion"] >= umbral)
        tag[promovible] = "Sí (estimado)"
        tag[es_administrativo] = "No"
        return tag

    df["es_elector"] = _tag_umbral(df["antiguedad_ref_anios"] >= UMBRAL_ELECTOR_ANIOS, UMBRAL_ELECTOR_ANIOS)
    df["cumple_antiguedad_8anios"] = _tag_umbral(df["antiguedad_ref_anios"] >= UMBRAL_ELEGIBLE_ANIOS, UMBRAL_ELEGIBLE_ANIOS)

    # es_elegible: el rango descalifica antes que la antigüedad — si la
    # jerarquía no es una de las 2 más altas, es 'No' sin importar si hay
    # dato de antigüedad o no (a diferencia de es_elector, acá si falta
    # jerarquía SÍ es bloqueante: sin saber el rango no se puede confirmar).
    en_rango_top = df["jerarquia"].isin(JERARQUIAS_ELEGIBLE)
    jerarquia_desconocida = df["jerarquia"].isna()

    es_elegible = pd.Series("No", index=df.index)
    es_elegible[jerarquia_desconocida] = "Sin dato"
    es_elegible[en_rango_top & sin_dato] = "Sin dato"
    es_elegible[en_rango_top & ~sin_dato & (df["antiguedad_ref_anios"] >= UMBRAL_ELEGIBLE_ANIOS)] = "Sí"
    es_elegible[en_rango_top & ~sin_dato & (df["antiguedad_ref_anios"] < UMBRAL_ELEGIBLE_ANIOS)] = "No"
    promovible_elegible = en_rango_top & sin_dato & (df["anios_desde_jerarquizacion"] >= UMBRAL_ELEGIBLE_ANIOS)
    es_elegible[promovible_elegible] = "Sí (estimado)"
    es_elegible[es_administrativo] = "No"
    df["es_elegible"] = es_elegible

    df["fecha_referencia_convocatoria"] = FECHA_REFERENCIA.date().isoformat()

    return df.drop(columns=["fecha_ingreso_dt", "fecha_jerarquizacion_dt"])


if __name__ == "__main__":
    base = cargar_base()
    print(f"Universo cargado: {len(base)} docentes")

    tab = calcular_tags(base)

    print(f"\nFecha de referencia (placeholder, ajustar cuando se confirme la "
          f"convocatoria real): {FECHA_REFERENCIA.date()}")

    print("\n--- es_elector x tipo_contrato_tag ---")
    print(pd.crosstab(tab["tipo_contrato_tag"], tab["es_elector"]))

    print("\n--- cumple_antiguedad_8anios x tipo_contrato_tag ---")
    print(pd.crosstab(tab["tipo_contrato_tag"], tab["cumple_antiguedad_8anios"]))

    print("\n--- es_elegible x tipo_contrato_tag ---")
    print(pd.crosstab(tab["tipo_contrato_tag"], tab["es_elegible"]))

    tab.to_sql("universo_electores", engine, schema="analisis",
               if_exists="replace", index=False)
    print(f"\n✓ Guardado: analisis.universo_electores ({len(tab)} filas)")
