import sys
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
from sqlalchemy import create_engine, text

engine = create_engine("postgresql://ucen_user:ucen2026@localhost:5432/ucen")

with engine.connect() as conn:
    # Total registros en notas_docente con y sin nota
    resumen = pd.read_sql(text("""
        SELECT
            COUNT(*)                                      AS total_registros,
            COUNT(nota)                                   AS con_nota,
            COUNT(*) - COUNT(nota)                        AS sin_nota,
            ROUND(COUNT(nota)::numeric / COUNT(*) * 100, 1) AS pct_con_nota,
            COUNT(DISTINCT cod_asignatura)                AS asignaturas_totales,
            COUNT(DISTINCT CASE WHEN nota IS NOT NULL THEN cod_asignatura END) AS asignaturas_con_nota,
            COUNT(DISTINCT rut_docente)                   AS docentes_totales,
            COUNT(DISTINCT CASE WHEN nota IS NOT NULL THEN rut_docente END) AS docentes_con_nota
        FROM intel.notas_docente
    """), conn)
    print("=== RESUMEN GENERAL ===")
    print(resumen.T.to_string())

    # Qué tan vacías están las asignaturas sin nota
    asig_nulas = pd.read_sql(text("""
        SELECT
            nombre_asignatura,
            facultad,
            COUNT(*) AS total_filas,
            COUNT(nota) AS filas_con_nota,
            COUNT(*) - COUNT(nota) AS filas_sin_nota,
            ROUND(COUNT(nota)::numeric / COUNT(*) * 100, 1) AS pct_con_nota
        FROM intel.notas_docente
        GROUP BY nombre_asignatura, facultad
        HAVING COUNT(nota) = 0
        ORDER BY total_filas DESC
        LIMIT 20
    """), conn)
    print(f"\n=== ASIGNATURAS COMPLETAMENTE SIN NOTA (top 20, {len(asig_nulas)} total) ===")
    print(asig_nulas.to_string(index=False))

    # Distribución de notas válidas
    dist = pd.read_sql(text("""
        SELECT
            CASE
                WHEN nota IS NULL THEN 'NULL'
                WHEN nota < 1    THEN '< 1'
                WHEN nota < 4    THEN '1-3.9 (reprobado)'
                WHEN nota <= 7   THEN '4-7 (aprobado)'
                ELSE '> 7'
            END AS rango,
            COUNT(*) AS n
        FROM intel.notas_docente
        GROUP BY 1 ORDER BY 2 DESC
    """), conn)
    print("\n=== DISTRIBUCIÓN DE VALORES DE NOTA ===")
    print(dist.to_string(index=False))
