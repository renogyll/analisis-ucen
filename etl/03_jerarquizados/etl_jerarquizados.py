"""
ETL: Universo Jerarquizados (~917)
FILTRO: analisis.universo_base WHERE jerarquia válida
SALIDAS: analisis.universo_jerarquizados (DB)
         data/cascade/03_jerarquizados/docentes_jerarquizados.csv
         data/cascade/03_jerarquizados/docente_918.csv  (alias por compatibilidad)

NOTA: N=917 (se excluyó ESPINOZA RUT 16322128 por ambigüedad de identidad).
      La cifra histórica 918 era previa a esa exclusión.
      Rama paralela — NO es prerequisito para formados_p3 ni aptos_p3.
"""
import sys; sys.stdout.reconfigure(encoding="utf-8")
import os
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).parents[2]))
from config import C03_JERARQUIZADOS

DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"
engine = create_engine(DB_URL)

SIN_JERARQUIA = {"SIN JERARQUÍA", "SIN JERARQUIA", "NO INFORMA", ""}

with engine.connect() as conn:
    base = pd.read_sql(text("SELECT * FROM analisis.universo_base"), conn)

print(f"universo_base cargado: {len(base)} RUTs")

# Filtrar jerarquía válida (campos nomina y dotacion)
def jer_ok(val):
    return str(val).strip().upper() not in SIN_JERARQUIA and pd.notna(val)

mask_nom = base["jerarquia"].apply(jer_ok)
mask_dot = base["jerarquia_dot"].apply(jer_ok) if "jerarquia_dot" in base.columns else pd.Series(False, index=base.index)

df = base[mask_nom | mask_dot].copy()

print(f"\nuniverse_jerarquizados: {len(df)} docentes")
print(f"  origen: {df['origen'].value_counts().to_dict()}")
print(f"  tipo_contrato_tag: {df['tipo_contrato_tag'].value_counts().to_dict()}")
print(f"  Distribución jerarquía (top 8):")
print(df["jerarquia"].value_counts(dropna=False).head(8).to_string())

os.makedirs(C03_JERARQUIZADOS, exist_ok=True)
csv_path = os.path.join(C03_JERARQUIZADOS, "docentes_jerarquizados.csv")
df.to_csv(csv_path, index=False, encoding="utf-8-sig")

# Alias para compatibilidad con scripts legados que buscan docente_918.csv
alias_path = os.path.join(C03_JERARQUIZADOS, "docente_918.csv")
df.to_csv(alias_path, index=False, encoding="utf-8-sig")

df.to_sql("universo_jerarquizados", engine, schema="analisis", if_exists="replace", index=False)
print(f"\nGuardado: CSV + alias docente_918.csv + analisis.universo_jerarquizados")
