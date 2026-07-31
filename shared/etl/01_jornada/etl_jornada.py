"""
ETL: Universo Jornada
FILTRO: analisis.universo_base WHERE tipo_contrato_tag = 'JORNADA'
SALIDAS: analisis.universo_jornada (DB)
         data/cascade/01_jornada/docentes_jornada.csv
"""
import sys; sys.stdout.reconfigure(encoding="utf-8")
import os
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).parents[2]))
from config import C01_JORNADA

DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"
engine = create_engine(DB_URL)

with engine.connect() as conn:
    df = pd.read_sql(
        text("SELECT * FROM analisis.universo_base WHERE tipo_contrato_tag = 'JORNADA'"),
        conn
    )

print(f"universo_jornada: {len(df)} docentes")
print(f"  origen: {df['origen'].value_counts().to_dict()}")

os.makedirs(C01_JORNADA, exist_ok=True)
df.to_csv(os.path.join(C01_JORNADA, "docentes_jornada.csv"), index=False, encoding="utf-8-sig")
df.to_sql("universo_jornada", engine, schema="analisis", if_exists="replace", index=False)
print("Guardado: CSV + analisis.universo_jornada")
