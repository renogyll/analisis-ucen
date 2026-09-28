"""
Rotación docente — datos y estilo compartidos por los scripts de cada diapositiva (D35, D39).

Criterios D39 (decisiones del usuario 2026-09-27):
- Las tasas de baja se comparan con el CONTRATO DE ENTRADA (`tipo_contrato_tag`, registro
  histórico) para todos, activos y bajas. El contrato 2026 (`tipo_contrato_2026`) solo se usa
  para describir la transición de régimen. La columna híbrida `tipo_contrato_rotacion` de D35
  ya no se usa: mezclaba el contrato final de los activos con el de origen de las bajas, y los
  59 que pasaron de Jornada a Honorario contaban como activos de Honorario (bajaba su tasa).
- La antigüedad NO se usa: sin fecha de salida, para las bajas se mide hasta hoy (queda
  inflada) y el dato de ingreso falta mucho más en las bajas (58% vs 6% en Jornada).
- Facultad: solo las 5 facultades. "Sin facultad" (549, 364 de ellos Honorario) no es una
  facultad y repetía el efecto del contrato; se informa en la bajada.
- Jerarquía: nivel en 4 categorías (Instructor, Asistente, Asociado, Titular); el escalafón
  (Docente/Regular) va aparte. Así se evitan celdas de 0-7 casos del cruce de 8 categorías.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.patheffects as pe
from scipy import stats
from sqlalchemy import create_engine, text

SLIDES = Path(__file__).resolve().parent
ROOT = SLIDES.parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "shared"))
from pptx_helpers import UcenSlideKit, prueba_dict  # noqa: E402

DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"
BLOQUE = "Rotación"

COL_ACTIVO, COL_BAJA = "#5C9BD6", "#F0B04D"
COL_J, COL_H = "#5C9BD6", "#F0B04D"          # Jornada / Honorario
COL_TRANS, GRIS = "#9085E9", "#7A8699"
STROKE = [pe.withStroke(linewidth=2, foreground="#0A0F18")]

CONTRATOS = ["JORNADA", "HONORARIO"]
FACULTADES = ["Medicina y C. Salud", "Ingeniería y Arq.", "Educación",
              "Economía, Gob. y Com.", "Derecho y Humanidades"]
NIVELES = ["Instructor", "Asistente", "Asociado", "Titular"]
ESCALAFONES = ["Docente", "Regular"]
SEXOS = ["Mujer", "Hombre"]


def fac5(s):
    if not isinstance(s, str) or not s.strip():
        return None
    u = s.upper()
    if "MEDICINA" in u and "SALUD" in u: return "Medicina y C. Salud"
    if "DERECHO" in u and "HUMANIDADES" in u: return "Derecho y Humanidades"
    if "INGENIER" in u: return "Ingeniería y Arq."
    if "EDUCACI" in u: return "Educación"
    if "ECONOM" in u and "GOBIERNO" in u: return "Economía, Gob. y Com."
    return None


_CACHE = {}


def cargar_datos():
    """1 fila por docente del universo histórico (1.144), con las variables de corte D39."""
    if "df" not in _CACHE:
        engine = create_engine(DB_URL)
        df = pd.read_sql(text("SELECT * FROM analisis.universo_rotacion"), engine)
        df["rut_key"] = df["rut_key"].astype(str)
        df["baja"] = (df["estado"] == "Baja").astype(int)
        df["contrato"] = df["tipo_contrato_tag"]
        df["fac"] = df["unidad_facultad"].apply(fac5)
        jer = df["jerarquia"].where(~df["jerarquia"].isin(["SIN JERARQUÍA"]))
        df["nivel"] = jer.str.split().str[0].str.capitalize()
        df["escalafon"] = jer.str.split().str[-1].str.capitalize()
        df["sexo_"] = df["sexo"].map({"MUJER": "Mujer", "HOMBRE": "Hombre"})
        _CACHE["df"] = df
    return _CACHE["df"]


PLAN_2026 = ROOT / "Planeación docente- Docentes planta + honorarios 2026 (1).xlsx"
BLOQUE_EXT = "Rotación — composición"


def cargar_plan():
    """Archivo de planeación 2026 con la misma corrección de RUT que el ETL (D39)."""
    if "plan" not in _CACHE:
        sys.path.insert(0, str(ROOT / "products" / "rotacion_docente" / "etl"))
        from generar_tag_rotacion import CORRECCION_RUT_PLAN
        plan = pd.read_excel(PLAN_2026, sheet_name="Hoja1")
        plan["rut_key"] = plan["RUT_PROFESOR"].astype(str).replace(CORRECCION_RUT_PLAN)
        _CACHE["plan"] = plan
    return _CACHE["plan"]


def n_altas():
    """Docentes del archivo 2026 sin registro histórico (no se puede medir su rotación)."""
    return int((~cargar_plan()["rut_key"].isin(cargar_datos()["rut_key"].astype(str))).sum())


def carga_docente():
    """Por docente con calificaciones 2023-2025: semestres dictados y secciones por semestre."""
    if "carga" not in _CACHE:
        engine = create_engine(DB_URL)
        c = pd.read_sql(text("""
            SELECT rut_docente::text AS rut_key, COUNT(DISTINCT periodo) AS semestres,
                   COUNT(DISTINCT periodo || '|' || cod_asignatura || '|' || COALESCE(seccion::text, '')) AS secciones
            FROM consolidados.calificacion_alumno WHERE periodo IS NOT NULL GROUP BY 1"""), engine)
        c["sec_sem"] = c["secciones"] / c["semestres"]
        _CACHE["carga"] = c
    return _CACHE["carga"]


def formados():
    """RUT con al menos una instancia formativa (cualquier contrato)."""
    if "form" not in _CACHE:
        engine = create_engine(DB_URL)
        _CACHE["form"] = set(pd.read_sql(text("SELECT DISTINCT rut_key::text FROM consolidados.participacion_formacion"),
                                         engine).iloc[:, 0])
    return _CACHE["form"]


def tasa_baja(df, col, cats):
    """% de baja y N° por categoría."""
    g = df.dropna(subset=[col]).groupby(col)["baja"].agg(["mean", "size"]).reindex(cats)
    g["mean"] *= 100
    return g.rename(columns={"mean": "pct", "size": "n"})


def chi2(df, col, comparacion, orden=None):
    """Chi-cuadrado de independencia estado × categoría. Devuelve (prueba_dict, chi2, gl)."""
    s = df.dropna(subset=[col])
    t = pd.crosstab(s[col], s["baja"])
    est, p, gl, _ = stats.chi2_contingency(t)
    tasas = (100 * t[1] / t.sum(axis=1)) if 1 in t else pd.Series(dtype=float)
    if orden:
        tasas = tasas.reindex([o for o in orden if o in tasas.index])
    resultado = " / ".join(f"{str(k).capitalize() if str(k).isupper() else k}: {v:.1f}%" for k, v in tasas.items())
    return prueba_dict(BLOQUE, comparacion, resultado, len(s), p, prueba="chi-cuadrado"), est, gl


def kit_para(carpeta):
    kit = UcenSlideKit(out_dir=carpeta)
    kit.ensure_bg()
    return kit


def lamina_base(kit, prs, titulo, bajada):
    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.title(sl, titulo, fs=19)
    kit.subtitulo(sl, bajada)
    return sl


def estilo(ax, titulo, horizontal=False):
    ax.set_title(titulo, color="white", fontsize=11, fontweight="bold", pad=8)
    for k, sp in ax.spines.items():
        sp.set_visible(k == ("left" if horizontal else "bottom"))
        sp.set_edgecolor("white"); sp.set_alpha(0.3)
    ax.tick_params(colors="white", length=0, labelsize=9)
    (ax.set_xticks if horizontal else ax.set_yticks)([])


def etiqueta(ax, x, y, texto, fontsize=10, **kw):
    ax.text(x, y, texto, color="white", fontsize=fontsize, fontweight="bold",
            path_effects=STROKE, zorder=6, **kw)


def paneles(kit, anchos, wspace=0.045, izq=None, bottom=0.16, pad=0.02, leyenda=None):
    """Figura con varios gráficos lado a lado. Cada gráfico va en su propio recuadro con contorno
    blanco tenue y separado del siguiente (pedido del usuario 2026-09-27). `leyenda` = lista de
    (etiqueta, color) común a todos: va arriba, fuera de los recuadros. izq = margen extra a la
    izquierda para etiquetas de eje largas. Guardar con `guardar_paneles` (verifica contención)."""
    from matplotlib.patches import Rectangle, Patch
    fig = kit.new_chart_fig()
    izq = izq or [0] * len(anchos)
    techo = 0.87 if leyenda else 0.985
    total, util = sum(anchos), 0.99 - wspace * (len(anchos) - 1)
    axes, x = [], 0.005
    fig._recuadros = []
    for a, m in zip(anchos, izq):
        w = util * a / total
        r = Rectangle((x, 0.01), w, techo - 0.01, transform=fig.transFigure, fill=False,
                      edgecolor="white", alpha=0.28, linewidth=0.9, zorder=1)
        fig.patches.append(r); fig._recuadros.append((x, 0.01, x + w, techo))
        axes.append(fig.add_axes([x + pad + m, bottom, w - 2 * pad - m, techo - 0.145 - bottom],
                                 facecolor="none", zorder=5))
        x += w + wspace
    if leyenda:
        fig.legend(handles=[Patch(color=c, label=l) for l, c in leyenda], loc="upper center",
                   bbox_to_anchor=(0.5, 1.0), ncol=len(leyenda), fontsize=10, frameon=False,
                   labelcolor="white", handlelength=1.4, columnspacing=1.8)
    return fig, axes


def guardar_paneles(kit, fig, axes, nombre):
    """Guarda la figura, pero antes verifica que todo lo de cada gráfico (título, barras, etiquetas)
    quede dentro de su recuadro: si algo se sale, se detiene (pedido del usuario 2026-09-27)."""
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    W, H = fig.bbox.width, fig.bbox.height
    for i, (ax, (x0, y0, x1, y1)) in enumerate(zip(axes, fig._recuadros)):
        bb = ax.get_tightbbox(r)
        fuera = (bb.x0 / W < x0 - 1e-3, bb.x1 / W > x1 + 1e-3, bb.y0 / H < y0 - 1e-3, bb.y1 / H > y1 + 1e-3)
        assert not any(fuera), (f"{nombre}: el gráfico {i + 1} se sale de su recuadro "
                                f"(izq, der, abajo, arriba) = {fuera}")
        # etiquetas horizontales: no deben chocar (las inclinadas se revisan a ojo; su caja siempre se toca)
        cajas = [t.get_window_extent(r) for t in ax.get_xticklabels() if t.get_text() and t.get_rotation() == 0]
        for a, b in zip(cajas, cajas[1:]):
            assert a.x1 <= b.x0 + 1 or a.y1 < b.y0 or b.y1 < a.y0,                 f"{nombre}: en el gráfico {i + 1} las etiquetas del eje se superponen"
    return kit.save_chart(fig, nombre)
