"""
ETL: Cruce NOMINA vs DOTACION
Genera un CSV consolidado con tag de origen:
  - AMBOS: docente presente en nomina Y dotacion
  - SOLO_NOMINA: solo en nomina
  - SOLO_DOTACION: solo en dotacion

RUT sin DV es la clave de cruce universal.
Los archivos madre NO se modifican.
"""

import pandas as pd
import os

BASE = r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO\Downloads\Analisis_UCEN_v2"
DOCENTES = os.path.join(BASE, "CONSOLIDADO DOCENTES 3-05-2026")
OUT = os.path.join(BASE, "PROCESADO")

# ── Función para limpiar RUT ──────────────────────────────────────────────────
def strip_dv(rut_serie):
    """Extrae solo el número del RUT, descartando DV y puntos."""
    return (
        rut_serie.astype(str)
        .str.strip()
        .str.replace(".", "", regex=False)
        .str.split("-").str[0]
        .str.strip()
    )

# ── Cargar NOMINA ─────────────────────────────────────────────────────────────
nomina = pd.read_csv(
    os.path.join(DOCENTES, "CONSOLIDADO DOCENTES 3-05-2026.xlsx - NOMINA .csv"),
    dtype=str
)
nomina.columns = nomina.columns.str.strip()
nomina["rut_key"] = strip_dv(nomina["RUT"])

# flag de duplicados en nomina (mismo rut_key)
nomina["duplicado_nomina"] = nomina.duplicated(subset="rut_key", keep=False)

print(f"NOMINA   total filas: {len(nomina)}")
print(f"         RUT unicos:  {nomina['rut_key'].nunique()}")
print(f"         Duplicados:  {nomina['duplicado_nomina'].sum()} filas con rut repetido")

# ── Cargar DOTACION ───────────────────────────────────────────────────────────
dotacion = pd.read_csv(
    os.path.join(DOCENTES, "CONSOLIDADO DOCENTES 3-05-2026.xlsx - DOTACION.csv"),
    dtype=str
)
dotacion.columns = dotacion.columns.str.strip()
dotacion["rut_key"] = strip_dv(dotacion["RUT"])

print(f"\nDOTACION total filas: {len(dotacion)}")
print(f"         RUT unicos:  {dotacion['rut_key'].nunique()}")

# ── Cruce FULL OUTER JOIN ────────────────────────────────────────────────────
# Renombrar columnas para identificar origen
nomina_cols  = {c: f"nom_{c}" for c in nomina.columns  if c != "rut_key"}
dotacion_cols = {c: f"dot_{c}" for c in dotacion.columns if c != "rut_key"}

nomina_r   = nomina.rename(columns=nomina_cols)
dotacion_r = dotacion.rename(columns=dotacion_cols)

merged = pd.merge(nomina_r, dotacion_r, on="rut_key", how="outer", indicator=True)

# ── Tag legible ───────────────────────────────────────────────────────────────
tag_map = {"both": "AMBOS", "left_only": "SOLO_NOMINA", "right_only": "SOLO_DOTACION"}
merged["origen"] = merged["_merge"].map(tag_map)
merged = merged.drop(columns=["_merge"])

# Columna resumen al frente
cols_order = ["rut_key", "origen"] + [c for c in merged.columns if c not in ("rut_key", "origen")]
merged = merged[cols_order]

# ── Estadísticas ──────────────────────────────────────────────────────────────
conteos = merged["origen"].value_counts()
print(f"\n{'='*45}")
print("RESULTADO DEL CRUCE:")
print(f"  AMBOS        (en nomina Y dotacion): {conteos.get('AMBOS', 0)}")
print(f"  SOLO_NOMINA  (en nomina, NO dotacion): {conteos.get('SOLO_NOMINA', 0)}")
print(f"  SOLO_DOTACION(en dotacion, NO nomina): {conteos.get('SOLO_DOTACION', 0)}")
print(f"  TOTAL filas consolidado: {len(merged)}")
print(f"{'='*45}")

# ── Guardar CSVs ──────────────────────────────────────────────────────────────
# 1. Consolidado completo (todos los casos, todas las columnas)
out_consolidado = os.path.join(OUT, "P1_docente_consolidado.csv")
merged.to_csv(out_consolidado, index=False, encoding="utf-8-sig")
print(f"\nGuardado: P1_docente_consolidado.csv  ({len(merged)} filas)")

# 2. Solo los que están en AMBOS
ambos = merged[merged["origen"] == "AMBOS"].copy()
out_ambos = os.path.join(OUT, "P1_docente_AMBOS.csv")
ambos.to_csv(out_ambos, index=False, encoding="utf-8-sig")
print(f"Guardado: P1_docente_AMBOS.csv        ({len(ambos)} filas)")

# 3. Solo NOMINA
solo_nomina = merged[merged["origen"] == "SOLO_NOMINA"].copy()
out_nomina = os.path.join(OUT, "P1_docente_SOLO_NOMINA.csv")
solo_nomina.to_csv(out_nomina, index=False, encoding="utf-8-sig")
print(f"Guardado: P1_docente_SOLO_NOMINA.csv  ({len(solo_nomina)} filas)")

# 4. Solo DOTACION
solo_dotacion = merged[merged["origen"] == "SOLO_DOTACION"].copy()
out_dotacion = os.path.join(OUT, "P1_docente_SOLO_DOTACION.csv")
solo_dotacion.to_csv(out_dotacion, index=False, encoding="utf-8-sig")
print(f"Guardado: P1_docente_SOLO_DOTACION.csv ({len(solo_dotacion)} filas)")

print("\nListo. Archivos madre no modificados.")
