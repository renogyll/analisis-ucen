import sys
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
from sqlalchemy import create_engine, text

engine = create_engine("postgresql://ucen_user:ucen2026@localhost:5432/ucen")

with engine.connect() as conn:
    # Todos los jerarquizados
    ambos = pd.read_sql(text("""
        SELECT rut_key, unidad_facultad
        FROM analisis.docente_ambos
        WHERE jerarquia NOT IN ('SIN JERARQUIA')
        AND jerarquia NOT ILIKE '%sin jerarqu%'
    """), conn)

    # Grupo de tratamiento (con formación)
    trat = pd.read_sql(text("""
        SELECT DISTINCT rut_key FROM analisis.p3_grupo_tratamiento
    """), conn)

    # Con SAT pre+post (los 130)
    sat130 = pd.read_sql(text("""
        SELECT DISTINCT rut_key FROM intel.pre_post_sat
    """), conn)

    # SAT por período — todos los jerarquizados
    sat_per = pd.read_sql(text("""
        SELECT e.rut_docente AS rut_key, e.periodo, r.nota_promedio AS sat_nota,
               d.unidad_facultad
        FROM consolidados.evaluacion_respuesta r
        JOIN consolidados.evaluacion_periodo e ON r.evaluacion_id = e.evaluacion_id
        JOIN analisis.docente_ambos d ON e.rut_docente = d.rut_key
        WHERE r.pregunta_id = 'SAT_NOTA'
          AND r.nota_promedio IS NOT NULL
          AND d.jerarquia NOT IN ('SIN JERARQUIA')
          AND d.jerarquia NOT ILIKE '%sin jerarqu%'
    """), conn)

ambos["rut_key"]   = ambos["rut_key"].astype(str)
trat["rut_key"]    = trat["rut_key"].astype(str)
sat130["rut_key"]  = sat130["rut_key"].astype(str)
sat_per["rut_key"] = sat_per["rut_key"].astype(str)

# Clasificar grupos
sin_formacion = set(ambos["rut_key"]) - set(trat["rut_key"])
con_sat       = set(sat_per["rut_key"])

grupo_control_con_sat    = sin_formacion & con_sat
grupo_control_sin_sat    = sin_formacion - con_sat

print("=== UNIVERSO ===")
print(f"Jerarquizados total         : {len(ambos)}")
print(f"Grupo tratamiento           : {len(trat)}")
print(f"Sin formación (control)     : {len(sin_formacion)}")
print(f"  Con SAT utilizable        : {len(grupo_control_con_sat)}")
print(f"  Sin SAT (excluidos)       : {len(grupo_control_sin_sat)}")
print(f"130 con SAT pre+post        : {len(sat130)}")

# Z-score longitudinal: colapsar unidades pequeñas
n_por_unidad = sat_per.groupby("unidad_facultad")["rut_key"].nunique()
pequenas = n_por_unidad[n_por_unidad < 50].index.tolist()
sat_per["uf_ref"] = sat_per["unidad_facultad"].apply(
    lambda x: "Otras" if x in pequenas else x
)

# Estadísticas de referencia por uf_ref × período
stats = (sat_per.groupby(["uf_ref","periodo"])["sat_nota"]
         .agg(media="mean", std="std").reset_index())
stats["std"] = stats["std"].fillna(1.0)
stats.loc[stats["std"] < 0.01, "std"] = stats.loc[stats["std"] >= 0.01, "std"].mean()

# Calcular z-score para cada observación
sat_per2 = sat_per.merge(stats, on=["uf_ref","periodo"], how="left")
media_g  = sat_per["sat_nota"].mean()
std_g    = sat_per["sat_nota"].std()
sat_per2["media"] = sat_per2["media"].fillna(media_g)
sat_per2["std"]   = sat_per2["std"].fillna(std_g)
sat_per2["z"]     = ((sat_per2["sat_nota"] - sat_per2["media"]) / sat_per2["std"]).round(4)

# Etiquetar grupo
sat_per2["grupo"] = sat_per2["rut_key"].apply(
    lambda r: "Tratamiento (130)" if r in set(sat130["rut_key"])
    else ("Control (227)" if r in grupo_control_con_sat else "Otros")
)

# Longitudinal por período
evol = (sat_per2[sat_per2["grupo"].isin(["Tratamiento (130)","Control (227)"])]
        .groupby(["periodo","grupo"])
        .agg(z_mean=("z","mean"), n=("rut_key","nunique"))
        .reset_index()
        .sort_values(["periodo","grupo"]))

print("\n=== Z-SCORE PROMEDIO POR PERÍODO Y GRUPO ===")
print(evol.to_string(index=False))
