"""
ETL: Universo Honorario
FILTRO: analisis.universo_base WHERE tipo_contrato_tag = 'HONORARIO'
SALIDAS: analisis.universo_honorario (DB)
         data/cascade/02_honorario/docentes_honorario.csv
"""
import sys; sys.stdout.reconfigure(encoding="utf-8")
import os
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).parents[2]))
from config import C02_HONORARIO

DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"
engine = create_engine(DB_URL)

with engine.connect() as conn:
    df = pd.read_sql(
        text("SELECT * FROM analisis.universo_base WHERE tipo_contrato_tag = 'HONORARIO'"),
        conn
    )

print(f"universo_honorario: {len(df)} docentes")
print(f"  origen: {df['origen'].value_counts().to_dict()}")

os.makedirs(C02_HONORARIO, exist_ok=True)
df.to_csv(os.path.join(C02_HONORARIO, "docentes_honorario.csv"), index=False, encoding="utf-8-sig")
df.to_sql("universo_honorario", engine, schema="analisis", if_exists="replace", index=False)
print("Guardado: CSV + analisis.universo_honorario")
