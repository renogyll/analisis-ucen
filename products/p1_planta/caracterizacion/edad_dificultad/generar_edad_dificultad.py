"""
P1 — Caracterización del Cuerpo Académico de Planta
Edad de los Docentes según Grupo de Dificultad de Asignatura — Jornada.

Mismo patrón que antiguedad_dificultad/ (ver ese script y
docs/DECISIONES_METODOLOGICAS.md D27 para el detalle metodológico completo: grupos
de dificultad = terciles de % aprobación histórico por asignatura; la edad es un
atributo fijo del docente, así que la prueba t usa "grupo de dificultad
predominante" por docente, no promedio por docente×grupo).

FUENTE: intel.rendimiento_academico_alumnos (Postgres, en vivo)
        + data/cascade/01_jornada/docentes_jornada.csv (universo de RUTs)
SALIDA: P1_edad_dificultad.pptx (2 diapositivas) + edad_dificultad_chart.png
        + edad_dificultad_ttest_chart.png
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
OUT_PPTX = Path(OUTPUTS) / "pptx" / "P1_edad_dificultad.pptx"
OUT_PPTX.parent.mkdir(parents=True, exist_ok=True)

DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"
GRUPOS_ORD = ["Baja", "Media", "Alta"]
COLORS = ["#AFCBE8", "#4E8FC9", "#1F5C99"]

# ── Datos ───────────────────────────────────────────────────────────────────
doc = pd.read_csv(Path(CASCADE) / "01_jornada" / "docentes_jornada.csv", encoding="utf-8-sig")
N_JORNADA = len(doc)

engine = create_engine(DB_URL)
q = text("""
    SELECT grupo_dificultad,
           COUNT(*) AS n_instancias,
           COUNT(DISTINCT rut_docente) AS n_docentes,
           AVG(edad_anios) AS edad_prom
    FROM intel.rendimiento_academico_alumnos
    WHERE tipo_contrato_tag = 'JORNADA' AND grupo_dificultad IS NOT NULL
      AND edad_anios IS NOT NULL
    GROUP BY grupo_dificultad
""")
with engine.connect() as conn:
    tab = pd.read_sql(q, conn).set_index("grupo_dificultad").reindex(GRUPOS_ORD)

N_SIN_EDAD = int(pd.read_sql(text("""
    SELECT COUNT(*) AS n FROM intel.rendimiento_academico_alumnos
    WHERE tipo_contrato_tag='JORNADA' AND grupo_dificultad IS NOT NULL AND edad_anios IS NULL
"""), engine).iloc[0, 0])

print(f"Universo Jornada: {N_JORNADA}")
print(tab)
print(f"Instancias sin dato de edad: {N_SIN_EDAD}")

grupo_mayor = tab["edad_prom"].idxmax()
grupo_menor = tab["edad_prom"].idxmin()
diferencia = tab.loc[grupo_mayor, "edad_prom"] - tab.loc[grupo_menor, "edad_prom"]

# ── Datos para la prueba t: grupo de dificultad PREDOMINANTE por docente (la edad
# es un atributo fijo, no varía por instancia — ver D27) ───────────────────────
q2 = text("""
    SELECT rut_docente, edad_anios, grupo_dificultad
    FROM intel.rendimiento_academico_alumnos
    WHERE tipo_contrato_tag = 'JORNADA' AND grupo_dificultad IS NOT NULL
      AND edad_anios IS NOT NULL
""")
with engine.connect() as conn:
    raw_doc = pd.read_sql(q2, conn)

conteo = raw_doc.groupby(["rut_docente", "grupo_dificultad"]).size().reset_index(name="n")
idx_predominante = conteo.groupby("rut_docente")["n"].idxmax()
predominante = conteo.loc[idx_predominante, ["rut_docente", "grupo_dificultad"]] \
    .rename(columns={"grupo_dificultad": "grupo_predominante"})
edad_doc = raw_doc.drop_duplicates("rut_docente")[["rut_docente", "edad_anios"]]
por_docente = predominante.merge(edad_doc, on="rut_docente")

grupo_baja = por_docente.loc[por_docente["grupo_predominante"] == "Baja", "edad_anios"]
grupo_resto = por_docente.loc[por_docente["grupo_predominante"] != "Baja", "edad_anios"]
T_STAT, P_VAL = stats.ttest_ind(grupo_baja, grupo_resto, equal_var=False)   # Welch

print(f"\nPrueba t (por docente, grupo predominante Baja vs Media+Alta): "
      f"Baja N°={len(grupo_baja)} media={grupo_baja.mean():.2f}  "
      f"Resto N°={len(grupo_resto)} media={grupo_resto.mean():.2f}  t={T_STAT:.3f}  p={P_VAL:.4f}")



# ── Revisión 2026-09-26 (obs. 3 y 21): descriptivo y prueba con la misma unidad (1 valor por
# docente, grupo predominante), en una sola diapositiva. Ver dificultad_comun.py. ──────────
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dificultad_comun import slide_por_grupo
from pptx_helpers import prueba_dict

PRUEBAS = [prueba_dict("IV · Aprobación", "Edad: grupo predominante Baja vs Media+Alta",
                       f"{grupo_baja.mean():.1f} vs {grupo_resto.mean():.1f} años",
                       len(grupo_baja) + len(grupo_resto), P_VAL)]


def agregar(prs):
    kit = UcenSlideKit(out_dir=HERE)
    kit.ensure_bg()
    return slide_por_grupo(
        prs, kit, por_docente, "edad_anios", fmt="{:.1f}", unidad=" años",
        ylabel="Edad promedio (años)",
        titulo="Edad de los docentes según grupo de dificultad — Docentes Jornada",
        subtitulo=f"1 valor por docente, asignado a su grupo de dificultad predominante  ·  "
                  f"N°={len(por_docente)} docentes con edad registrada",
        frase_valor=lambda b, r: (f"Los docentes que dictan principalmente asignaturas de baja aprobación "
                                  f"tienen en promedio {b:.1f} años de edad, vs {r:.1f} en el resto "
                                  f"(diferencia de {b - r:.1f} años)."),
        notas="Edad a la fecha de corte.",
        clave="Edad: grupo predominante Baja vs Media+Alta",
        chart_name="edad_dificultad_chart.png")


if __name__ == "__main__":
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(UcenSlideKit.SW_EMU), Emu(UcenSlideKit.SH_EMU)
    agregar(prs)
    prs.save(OUT_PPTX)
    print(f"\n✓ Guardado: {OUT_PPTX}")
