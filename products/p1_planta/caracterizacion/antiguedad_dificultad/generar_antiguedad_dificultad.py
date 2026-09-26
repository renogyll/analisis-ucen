"""
P1 — Caracterización del Cuerpo Académico de Planta
Antigüedad de los Docentes según Grupo de Dificultad de Asignatura — Jornada.

¿Los docentes con más antigüedad institucional dictan asignaturas más difíciles
(menor % de aprobación histórico)? Usa los grupos de dificultad definidos en
docs/DECISIONES_METODOLOGICAS.md D27 (terciles Baja/Media/Alta de % aprobación
histórico por asignatura). Unidad de análisis: instancia docente×asignatura×período
(una fila de intel.rendimiento_academico_alumnos) — un docente que dicta materias
de dos grupos distintos aporta a los dos, ponderado por su volumen de calificaciones
en cada uno (mismo criterio que el resto de los gráficos "por grupo" de este bloque).

FUENTE: intel.rendimiento_academico_alumnos (Postgres, en vivo)
        + data/cascade/01_jornada/docentes_jornada.csv (universo de RUTs)
SALIDA: P1_antiguedad_dificultad.pptx (1 diapositiva) + antiguedad_dificultad_chart.png
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
OUT_PPTX = Path(OUTPUTS) / "pptx" / "P1_antiguedad_dificultad.pptx"
OUT_PPTX.parent.mkdir(parents=True, exist_ok=True)

DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"
GRUPOS_ORD = ["Baja", "Media", "Alta"]
# Mismo criterio ordinal que edad_jerarquia/: claro→oscuro seguido el eje de la
# variable (acá % aprobación creciente Baja→Alta), no un juicio de "bueno/malo".
COLORS = ["#AFCBE8", "#4E8FC9", "#1F5C99"]

# ── Datos ───────────────────────────────────────────────────────────────────
doc = pd.read_csv(Path(CASCADE) / "01_jornada" / "docentes_jornada.csv", encoding="utf-8-sig")
N_JORNADA = len(doc)

engine = create_engine(DB_URL)
q = text("""
    SELECT grupo_dificultad,
           COUNT(*) AS n_instancias,
           COUNT(DISTINCT rut_docente) AS n_docentes,
           AVG(antiguedad_anios) AS antiguedad_prom
    FROM intel.rendimiento_academico_alumnos
    WHERE tipo_contrato_tag = 'JORNADA' AND grupo_dificultad IS NOT NULL
      AND antiguedad_anios IS NOT NULL
    GROUP BY grupo_dificultad
""")
with engine.connect() as conn:
    tab = pd.read_sql(q, conn).set_index("grupo_dificultad").reindex(GRUPOS_ORD)

N_SIN_ANTIGUEDAD = int(pd.read_sql(text("""
    SELECT COUNT(*) AS n FROM intel.rendimiento_academico_alumnos
    WHERE tipo_contrato_tag='JORNADA' AND grupo_dificultad IS NOT NULL AND antiguedad_anios IS NULL
"""), engine).iloc[0, 0])

print(f"Universo Jornada: {N_JORNADA}")
print(tab)
print(f"Instancias sin dato de antigüedad: {N_SIN_ANTIGUEDAD}")

grupo_mayor = tab["antiguedad_prom"].idxmax()
grupo_menor = tab["antiguedad_prom"].idxmin()
diferencia = tab.loc[grupo_mayor, "antiguedad_prom"] - tab.loc[grupo_menor, "antiguedad_prom"]

# ── Datos para la prueba t: grupo DIFICULTAD PREDOMINANTE por docente. La antigüedad
# es un atributo fijo del docente (no varía por instancia), así que a diferencia de
# las pruebas t de aprobación acá no se pondera por volumen — cada docente aporta
# un solo valor, asignado al grupo donde tiene más instancias (evita que un mismo
# docente cuente en dos muestras a la vez, lo que rompería la independencia del t-test).
q2 = text("""
    SELECT rut_docente, antiguedad_anios, grupo_dificultad
    FROM intel.rendimiento_academico_alumnos
    WHERE tipo_contrato_tag = 'JORNADA' AND grupo_dificultad IS NOT NULL
      AND antiguedad_anios IS NOT NULL
""")
with engine.connect() as conn:
    raw_doc = pd.read_sql(q2, conn)

conteo = raw_doc.groupby(["rut_docente", "grupo_dificultad"]).size().reset_index(name="n")
idx_predominante = conteo.groupby("rut_docente")["n"].idxmax()
predominante = conteo.loc[idx_predominante, ["rut_docente", "grupo_dificultad"]] \
    .rename(columns={"grupo_dificultad": "grupo_predominante"})
antig_doc = raw_doc.drop_duplicates("rut_docente")[["rut_docente", "antiguedad_anios"]]
por_docente = predominante.merge(antig_doc, on="rut_docente")

grupo_baja = por_docente.loc[por_docente["grupo_predominante"] == "Baja", "antiguedad_anios"]
grupo_resto = por_docente.loc[por_docente["grupo_predominante"] != "Baja", "antiguedad_anios"]
T_STAT, P_VAL = stats.ttest_ind(grupo_baja, grupo_resto, equal_var=False)   # Welch

print(f"\nPrueba t (por docente, grupo predominante Baja vs Media+Alta): "
      f"Baja N°={len(grupo_baja)} media={grupo_baja.mean():.2f}  "
      f"Resto N°={len(grupo_resto)} media={grupo_resto.mean():.2f}  t={T_STAT:.3f}  p={P_VAL:.4f}")



# ── Revisión 2026-09-26 (obs. 3 y 21): descriptivo y prueba con la misma unidad (1 valor por
# docente, grupo predominante), en una sola diapositiva. Ver dificultad_comun.py. ──────────
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dificultad_comun import slide_por_grupo
from pptx_helpers import prueba_dict

PRUEBAS = [prueba_dict("IV · Aprobación", "Antigüedad: grupo predominante Baja vs Media+Alta",
                       f"{grupo_baja.mean():.1f} vs {grupo_resto.mean():.1f} años",
                       len(grupo_baja) + len(grupo_resto), P_VAL)]


def agregar(prs):
    kit = UcenSlideKit(out_dir=HERE)
    kit.ensure_bg()
    return slide_por_grupo(
        prs, kit, por_docente, "antiguedad_anios", fmt="{:.1f}", unidad=" años",
        ylabel="Antigüedad promedio (años)",
        titulo="Antigüedad de los docentes según grupo de dificultad — Docentes Jornada",
        subtitulo=f"1 valor por docente, asignado a su grupo de dificultad predominante  ·  "
                  f"N°={len(por_docente)} docentes con antigüedad registrada",
        frase_valor=lambda b, r: (f"Los docentes que dictan principalmente asignaturas de baja aprobación "
                                  f"tienen en promedio {b:.1f} años de antigüedad, vs {r:.1f} en el resto "
                                  f"(diferencia de {b - r:.1f} años)."),
        notas="Antigüedad = años desde la fecha de ingreso a UCEN.",
        chart_name="antiguedad_dificultad_chart.png")


if __name__ == "__main__":
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(UcenSlideKit.SW_EMU), Emu(UcenSlideKit.SH_EMU)
    agregar(prs)
    prs.save(OUT_PPTX)
    print(f"\n✓ Guardado: {OUT_PPTX}")
