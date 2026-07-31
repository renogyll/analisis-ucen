"""
ETL Tablas derivadas de tabla_docente
Genera los 4 subconjuntos filtrando por fuente — siempre consistentes con tabla_docente.
Reemplaza los P1_docente_*.csv generados antes de la deduplicacion completa.
"""

import sys, os
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from config import DATA_STAGING

OUT = DATA_STAGING

td = pd.read_csv(os.path.join(OUT, "tabla_docente.csv"), dtype=str)
print(f"tabla_docente cargada: {len(td)} filas | {td['rut_key'].nunique()} RUTs unicos")
print(td["fuente"].value_counts().to_string())

# ── Subconjuntos por fuente ───────────────────────────────────────────────────
ambos = td[td["fuente"] == "NOMINA_DOTACION"].copy()
solo_nom = td[td["fuente"] == "NOMINA"].copy()
solo_dot = td[td["fuente"] == "SOLO_DOTACION"].copy()
solo_eval = td[td["fuente"] == "SOLO_EVALUACIONES"].copy()

ambos.to_csv(os.path.join(OUT,    "docente_ambos.csv"),            index=False, encoding="utf-8-sig")
solo_nom.to_csv(os.path.join(OUT, "docente_solo_nomina.csv"),      index=False, encoding="utf-8-sig")
solo_dot.to_csv(os.path.join(OUT, "docente_solo_dotacion.csv"),    index=False, encoding="utf-8-sig")
solo_eval.to_csv(os.path.join(OUT,"docente_solo_evaluaciones.csv"),index=False, encoding="utf-8-sig")

print(f"\ndocente_ambos.csv            {len(ambos)} filas")
print(f"docente_solo_nomina.csv      {len(solo_nom)} filas")
print(f"docente_solo_dotacion.csv    {len(solo_dot)} filas")
print(f"docente_solo_evaluaciones.csv {len(solo_eval)} filas")
print("\nListo.")
