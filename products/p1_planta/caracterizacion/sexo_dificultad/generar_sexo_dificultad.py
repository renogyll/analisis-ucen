"""
P1 — Caracterización del Cuerpo Académico de Planta
Sexo de los Docentes según Grupo de Dificultad de Asignatura — Jornada.

Mismo patrón que antiguedad_dificultad/ (ver ese script y
docs/DECISIONES_METODOLOGICAS.md D27 para el detalle metodológico completo). El sexo
es un atributo fijo del docente (no varía por instancia), así que — igual que
antigüedad/edad — la prueba t usa "grupo de dificultad predominante" por docente,
codificando sexo como binario (Mujer=1/Hombre=0) para poder aplicar Welch.

FUENTE: intel.rendimiento_academico_alumnos (Postgres, en vivo)
        + data/cascade/01_jornada/docentes_jornada.csv (universo de RUTs)
SALIDA: P1_sexo_dificultad.pptx (2 diapositivas) + sexo_dificultad_chart.png
        + sexo_dificultad_ttest_chart.png
"""
import sys; sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "shared"))
from config import CASCADE, OUTPUTS
from pptx_helpers import UcenSlideKit

import numpy as np
import pandas as pd
import matplotlib.patheffects as pe
from scipy import stats
from sqlalchemy import create_engine, text
from pptx import Presentation
from pptx.util import Emu

HERE = Path(__file__).parent
OUT_PPTX = Path(OUTPUTS) / "pptx" / "P1_sexo_dificultad.pptx"
OUT_PPTX.parent.mkdir(parents=True, exist_ok=True)

DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"
GRUPOS_ORD = ["Baja", "Media", "Alta"]
COL_HOMBRE = "#5C9BD6"   # mismo par usado en el resto de P1 (edad_sexo, grado_academico_sexo)
COL_MUJER = "#FFB74D"

# ── Datos ───────────────────────────────────────────────────────────────────
doc = pd.read_csv(Path(CASCADE) / "01_jornada" / "docentes_jornada.csv", encoding="utf-8-sig")
N_JORNADA = len(doc)

engine = create_engine(DB_URL)
q = text("""
    SELECT grupo_dificultad,
           COUNT(*) AS n_instancias,
           COUNT(DISTINCT rut_docente) AS n_docentes,
           100.0 * AVG((sexo = 'MUJER')::int) AS pct_mujer
    FROM intel.rendimiento_academico_alumnos
    WHERE tipo_contrato_tag = 'JORNADA' AND grupo_dificultad IS NOT NULL
      AND sexo IS NOT NULL
    GROUP BY grupo_dificultad
""")
with engine.connect() as conn:
    tab = pd.read_sql(q, conn).set_index("grupo_dificultad").reindex(GRUPOS_ORD)
tab["pct_hombre"] = 100 - tab["pct_mujer"]

N_SIN_SEXO = int(pd.read_sql(text("""
    SELECT COUNT(*) AS n FROM intel.rendimiento_academico_alumnos
    WHERE tipo_contrato_tag='JORNADA' AND grupo_dificultad IS NOT NULL AND sexo IS NULL
"""), engine).iloc[0, 0])

print(f"Universo Jornada: {N_JORNADA}")
print(tab)
print(f"Instancias sin dato de sexo: {N_SIN_SEXO}")

grupo_mayor = tab["pct_mujer"].idxmax()
grupo_menor = tab["pct_mujer"].idxmin()
diferencia = tab.loc[grupo_mayor, "pct_mujer"] - tab.loc[grupo_menor, "pct_mujer"]

# ── Datos para la prueba t: grupo de dificultad PREDOMINANTE por docente (el sexo
# es un atributo fijo, no varía por instancia — ver D27) ───────────────────────
q2 = text("""
    SELECT rut_docente, sexo, grupo_dificultad
    FROM intel.rendimiento_academico_alumnos
    WHERE tipo_contrato_tag = 'JORNADA' AND grupo_dificultad IS NOT NULL
      AND sexo IS NOT NULL
""")
with engine.connect() as conn:
    raw_doc = pd.read_sql(q2, conn)

conteo = raw_doc.groupby(["rut_docente", "grupo_dificultad"]).size().reset_index(name="n")
idx_predominante = conteo.groupby("rut_docente")["n"].idxmax()
predominante = conteo.loc[idx_predominante, ["rut_docente", "grupo_dificultad"]] \
    .rename(columns={"grupo_dificultad": "grupo_predominante"})
sexo_doc = raw_doc.drop_duplicates("rut_docente")[["rut_docente", "sexo"]].copy()
sexo_doc["es_mujer"] = (sexo_doc["sexo"] == "MUJER").astype(int)
por_docente = predominante.merge(sexo_doc, on="rut_docente")

grupo_baja = por_docente.loc[por_docente["grupo_predominante"] == "Baja", "es_mujer"]
grupo_resto = por_docente.loc[por_docente["grupo_predominante"] != "Baja", "es_mujer"]
T_STAT, P_VAL = stats.ttest_ind(grupo_baja, grupo_resto, equal_var=False)   # Welch

print(f"\nPrueba t (por docente, grupo predominante Baja vs Media+Alta, %Mujer): "
      f"Baja N°={len(grupo_baja)} %mujer={100*grupo_baja.mean():.1f}  "
      f"Resto N°={len(grupo_resto)} %mujer={100*grupo_resto.mean():.1f}  t={T_STAT:.3f}  p={P_VAL:.4f}")



# ── Revisión 2026-09-26 (obs. 3 y 21): descriptivo y prueba con la misma unidad (1 valor por
# docente, grupo predominante), en una sola diapositiva. Ver dificultad_comun.py. ──────────
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dificultad_comun import slide_por_grupo
from pptx_helpers import prueba_dict

PRUEBAS = [prueba_dict("IV · Aprobación", "% mujeres: grupo predominante Baja vs Media+Alta",
                       f"{100 * grupo_baja.mean():.1f}% vs {100 * grupo_resto.mean():.1f}%",
                       len(grupo_baja) + len(grupo_resto), P_VAL)]


def agregar(prs):
    kit = UcenSlideKit(out_dir=HERE)
    kit.ensure_bg()
    return slide_por_grupo(
        prs, kit, por_docente, "es_mujer", escala=100, fmt="{:.1f}", unidad="%",
        ylabel="% de docentes mujeres",
        titulo="Sexo de los docentes según grupo de dificultad — Docentes Jornada",
        subtitulo=f"1 valor por docente (Mujer=1/Hombre=0), asignado a su grupo de dificultad "
                  f"predominante  ·  N°={len(por_docente)} docentes con sexo registrado",
        frase_valor=lambda b, r: (f"Entre los docentes que dictan principalmente asignaturas de baja "
                                  f"aprobación, el {b:.1f}% son mujeres, vs {r:.1f}% en el resto: los "
                                  f"hombres están sobrerrepresentados en las asignaturas más exigentes."),
        notas="% de mujeres = promedio de la variable Mujer=1/Hombre=0.",
        chart_name="sexo_dificultad_chart.png")


if __name__ == "__main__":
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(UcenSlideKit.SW_EMU), Emu(UcenSlideKit.SH_EMU)
    agregar(prs)
    prs.save(OUT_PPTX)
    print(f"\n✓ Guardado: {OUT_PPTX}")
