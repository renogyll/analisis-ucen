"""
Organiza las tablas de ucen en 3 schemas:
  consolidados  — tablas maestras y transaccionales (fuentes limpias)
  analisis      — subconjuntos y tablas derivadas P1-P3
  intel         — tablas de analisis especifico construidas a pedido
"""

from sqlalchemy import create_engine, text

DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"

SCHEMAS = {
    "consolidados": [
        "docente",
        "pregunta",
        "catalogo_calificacion",
        "evaluacion_periodo",
        "evaluacion_respuesta",
        "calificacion_alumno",
        "participacion_formacion",
    ],
    "analisis": [
        "docente_ambos",
        "docente_solo_nomina",
        "docente_solo_dotacion",
        "docente_solo_evaluaciones",
        "grupo_control_p3",
        "resumen_participacion",
        "p3_grupo_tratamiento",
    ],
    "intel": [
        # se poblara con tablas de analisis especifico
    ],
}

engine = create_engine(DB_URL)

with engine.begin() as conn:
    # Crear schemas
    for schema in SCHEMAS:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        print(f"Schema '{schema}' listo")

    print()

    # Mover tablas desde public a su schema
    for schema, tablas in SCHEMAS.items():
        for tabla in tablas:
            conn.execute(text(f"ALTER TABLE public.{tabla} SET SCHEMA {schema}"))
            print(f"  {tabla:<35} -> {schema}")

print("\nListo. Refresca la conexion en DBeaver para ver los schemas.")
