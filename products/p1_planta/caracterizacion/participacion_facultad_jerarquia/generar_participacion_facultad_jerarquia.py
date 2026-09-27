"""
P1 — Caracterización del Cuerpo Académico de Planta
Participación en oferta formativa según Facultad y según Jerarquía — docentes de Jornada.

Pedido de la contraparte (2026-09-25): dos distribuciones en una diapositiva, por facultad
y por jerarquía, separando a quienes cursan oferta formativa de quienes no. Descriptivo,
sin prueba t (la de jerarquía ya existe en participacion_formacion_jerarquia/).

Participó = al menos 1 instancia formativa (Taller/Diplomado/Proyecto) registrada — mismo
criterio que participacion_formacion_* (D31). Barras 100% apiladas horizontales, con el N°
de cada categoría, para comparar composición entre grupos de distinto tamaño.

FUENTE: analisis.universo_base (Postgres, en vivo) — universo Jornada
        + analisis.universo_formados_p3 (Postgres, en vivo) — ver D31
SALIDA: P1_participacion_facultad_jerarquia.pptx (1 diapositiva)
        + participacion_facultad_jerarquia_chart.png
"""
import sys; sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "shared"))
from config import OUTPUTS
from pptx_helpers import UcenSlideKit

import numpy as np
import pandas as pd
import matplotlib.patheffects as pe
from sqlalchemy import create_engine, text
from pptx import Presentation
from pptx.util import Emu

HERE = Path(__file__).parent
OUT_PPTX = Path(OUTPUTS) / "pptx" / "P1_participacion_facultad_jerarquia.pptx"
OUT_PPTX.parent.mkdir(parents=True, exist_ok=True)

DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"

COL_SI = "#5C9BD6"
COL_NO = "#FFB74D"
N_MIN_CONFIABLE = 15

FAC_ORD = ["Medicina y C. Salud", "Ingeniería y Arq.", "Educación",
           "Economía, Gob. y Com.", "Derecho y Humanidades",
           "VR Investigación y Postgrado", "VR Académica", "Otras unidades"]
CAT_ORD = ["INSTRUCTOR DOCENTE", "INSTRUCTOR REGULAR",
           "ASISTENTE DOCENTE",  "ASISTENTE REGULAR",
           "ASOCIADO DOCENTE",   "ASOCIADO REGULAR",
           "TITULAR DOCENTE",    "TITULAR REGULAR"]


def fac_norm(s):
    """Misma normalización que facultad/generar_facultad.py (None = sin dato)."""
    if not isinstance(s, str) or not s.strip():
        return None
    u = s.upper()
    if "MEDICINA" in u: return "Medicina y C. Salud"
    if "INGENIER" in u: return "Ingeniería y Arq."
    if "EDUCACI" in u: return "Educación"
    if "ECONOM" in u: return "Economía, Gob. y Com."
    if "DERECHO" in u: return "Derecho y Humanidades"
    if "INVEST" in u: return "VR Investigación y Postgrado"
    if "VICERRECTOR" in u and "ACAD" in u: return "VR Académica"
    return "Otras unidades"


# ── Datos ───────────────────────────────────────────────────────────────────
engine = create_engine(DB_URL)
base = pd.read_sql(text("""
    SELECT rut_key, jerarquia, unidad_facultad
    FROM analisis.universo_base WHERE tipo_contrato_tag='JORNADA'
"""), engine)
N_JORNADA = len(base)
participantes = set(pd.read_sql(text("""
    SELECT DISTINCT rut_key FROM analisis.universo_formados_p3 WHERE tipo_contrato_tag='JORNADA'
"""), engine)["rut_key"])
base["participo"] = base["rut_key"].isin(participantes)
base["fac"] = base["unidad_facultad"].apply(fac_norm)
N_PARTICIPA = int(base["participo"].sum())


def _tabla(df, col, orden):
    t = df.groupby(col)["participo"].agg(n="count", si="sum").reindex(orden).dropna()
    t["pct_si"] = 100 * t["si"] / t["n"]
    t["pct_no"] = 100 - t["pct_si"]
    return t


tab_fac = _tabla(base.dropna(subset=["fac"]), "fac", FAC_ORD)
tab_jer = _tabla(base[base["jerarquia"].isin(CAT_ORD)], "jerarquia", CAT_ORD)
N_FAC, N_JER = int(tab_fac["n"].sum()), int(tab_jer["n"].sum())

print(f"Universo Jornada: {N_JORNADA}  |  participaron: {N_PARTICIPA}")
print(f"\nPor facultad (N°={N_FAC}):"); print(tab_fac.round(1))
print(f"\nPor jerarquía (N°={N_JER}):"); print(tab_jer.round(1))

# Hallazgos (solo categorías con N° suficiente)
fac_ok = tab_fac[tab_fac["n"] >= N_MIN_CONFIABLE]
fac_max, fac_min = fac_ok["pct_si"].idxmax(), fac_ok["pct_si"].idxmin()
jer_ok = tab_jer[tab_jer["n"] >= N_MIN_CONFIABLE]
jer_max, jer_min = jer_ok["pct_si"].idxmax(), jer_ok["pct_si"].idxmin()

# Pruebas por facultad (decisión del usuario 2026-09-26): cada unidad con N° suficiente vs el
# resto, prueba t de Welch sobre participó=1/no=0 — mismo criterio que EDD por facultad. Entran
# al anexo y a la corrección de Holm del Bloque II.
from scipy import stats
from pptx_helpers import prueba_dict, lectura_p, es_significativa
_con_fac = base.dropna(subset=["fac"])
PRUEBAS, RES_FAC = [], {}
for _f in fac_ok.index:
    _g = _con_fac.loc[_con_fac["fac"] == _f, "participo"].astype(float)
    _r = _con_fac.loc[_con_fac["fac"] != _f, "participo"].astype(float)
    _p = stats.ttest_ind(_g, _r, equal_var=False).pvalue
    RES_FAC[_f] = (100 * _g.mean(), 100 * _r.mean(), _p)
    PRUEBAS.append(prueba_dict("II · Participación", f"Participación: {_f} vs resto",
                               f"{100 * _g.mean():.1f}% vs {100 * _r.mean():.1f}%", len(_con_fac), _p))
print("\nPruebas por facultad (vs resto):", {k: round(v[2], 4) for k, v in RES_FAC.items()})


def _panel(ax, t, labels, titulo):
    y = np.arange(len(t))
    ax.barh(y, t["pct_si"], height=0.62, color=COL_SI, alpha=0.92, edgecolor="none",
            label="Cursa instancias formativas", zorder=3)
    ax.barh(y, t["pct_no"], height=0.62, left=t["pct_si"], color=COL_NO, alpha=0.92,
            edgecolor="none", label="No cursa", zorder=3)
    stroke = [pe.withStroke(linewidth=1.8, foreground="#0A0F18")]
    for i, (s, n) in enumerate(zip(t["pct_si"], t["n"])):
        ax.text(s / 2, i, f"{s:.0f}%", ha="center", va="center", fontsize=8.5,
                fontweight="bold", color="white", path_effects=stroke, zorder=6)
        if 100 - s > 9:
            ax.text(s + (100 - s) / 2, i, f"{100 - s:.0f}%", ha="center", va="center",
                    fontsize=8.5, fontweight="bold", color="#3A2A00", zorder=6)
        ax.text(101.5, i, f"N°={int(n)}" + (" ⚠" if n < N_MIN_CONFIABLE else ""),
                ha="left", va="center", fontsize=7.5, color="#DDDDDD")
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8.5, color="white")
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.tick_params(axis="y", length=0, pad=5)
    ax.tick_params(axis="x", colors="#AAAAAA", labelsize=7.5)
    for sp in ax.spines.values():
        sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.7)
    ax.set_title(titulo, color="#DDDDDD", fontsize=9.5, pad=6)


def agregar_facultad(prs):
    """Variante de 1 panel, solo facultad — la que usa el consolidado desde 2026-09-26: el
    panel de jerarquía repetía la tasa de participacion_formacion_jerarquia/ (acordado con
    el usuario al reordenar el deck)."""
    kit = UcenSlideKit(out_dir=HERE)
    kit.ensure_bg()

    fig = kit.new_chart_fig()
    ax = fig.add_axes([0.30, 0.08, 0.40, 0.74])
    _panel(ax, tab_fac, tab_fac.index.tolist(), f"Por facultad (N°={N_FAC})")
    handles, lbls = ax.get_legend_handles_labels()
    fig.legend(handles, lbls, fontsize=9, framealpha=0.22, labelcolor="white",
               facecolor="#101820", edgecolor="#444", loc="upper center",
               bbox_to_anchor=(0.5, 1.0), ncol=2)
    chart_path = kit.save_chart(fig, "participacion_facultad_chart.png")

    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.pic_chart(sl, prs, chart_path)
    kit.title(sl, "Participación en instancias formativas según facultad — Docentes Jornada", fs=19)
    kit.subtitulo(sl,
        f"Universo: {N_JORNADA} docentes Jornada  ·  {N_FAC} con unidad/facultad registrada  ·  "
        f"{N_PARTICIPA} ({100*N_PARTICIPA/N_JORNADA:.0f}%) cursaron al menos una instancia formativa")
    sin_fac = tab_fac.drop(index=[f for f in tab_fac.index if f.startswith("VR") or f == "Otras unidades"])
    sig = [f for f, (g, r, p) in RES_FAC.items() if es_significativa(p, f"Participación: {f} vs resto")]
    kit.punteo_numerado(sl, [
        f"{fac_max} tiene la mayor participación ({tab_fac.loc[fac_max, 'pct_si']:.0f}%) y "
        f"{fac_min} la menor ({tab_fac.loc[fac_min, 'pct_si']:.0f}%). Entre las 5 facultades académicas "
        f"va de {sin_fac['pct_si'].min():.0f}% a {sin_fac['pct_si'].max():.0f}%.",
        (f"Cada unidad vs el resto (prueba t de Welch, p corregido por comparaciones múltiples): difieren {', '.join(sig)}; el resto no."
         if sig else "Cada unidad vs el resto (prueba t de Welch, p corregido por comparaciones múltiples): ninguna difiere."),
    ], fs=12)
    kit.notas(sl,
        "Participó = al menos 1 Taller, Diplomado o Proyecto registrado (analisis.universo_formados_p3, "
        "sin filtrar a apto_p3 — D31). Facultad normalizada igual que la diapositiva de distribución "
        "por facultad. Unidades con menos de 15 docentes marcadas con ⚠ y excluidas de los hallazgos.")
    return sl


def agregar(prs):
    kit = UcenSlideKit(out_dir=HERE)
    kit.ensure_bg()

    fig = kit.new_chart_fig()
    ax1 = fig.add_axes([0.21, 0.08, 0.25, 0.74])
    ax2 = fig.add_axes([0.66, 0.08, 0.25, 0.74])
    _panel(ax1, tab_fac, tab_fac.index.tolist(), f"Por facultad (N°={N_FAC})")
    _panel(ax2, tab_jer, [c.title() for c in tab_jer.index], f"Por jerarquía (N°={N_JER})")

    handles, lbls = ax1.get_legend_handles_labels()
    fig.legend(handles, lbls, fontsize=9, framealpha=0.22, labelcolor="white",
               facecolor="#101820", edgecolor="#444", loc="upper center",
               bbox_to_anchor=(0.5, 1.0), ncol=2)

    chart_path = kit.save_chart(fig, "participacion_facultad_jerarquia_chart.png")

    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.pic_chart(sl, prs, chart_path)
    kit.title(sl, "Participación en Oferta Formativa según Facultad y Jerarquía — Jornada", fs=18)
    kit.subtitulo(sl,
        f"Universo: {N_JORNADA} docentes Jornada  ·  {N_PARTICIPA} ({100*N_PARTICIPA/N_JORNADA:.0f}%) "
        f"cursaron al menos una instancia formativa (Taller/Diplomado/Proyecto)")
    kit.punteo_numerado(sl, [
        f"Por facultad, {fac_max} tiene la mayor participación ({tab_fac.loc[fac_max, 'pct_si']:.0f}%) "
        f"y {fac_min} la menor ({tab_fac.loc[fac_min, 'pct_si']:.0f}%).",
        f"Por jerarquía, {jer_max.title()} participa más ({tab_jer.loc[jer_max, 'pct_si']:.0f}%) y "
        f"{jer_min.title()} menos ({tab_jer.loc[jer_min, 'pct_si']:.0f}%) — el escalafón Docente "
        f"participa más que el Regular en todos los niveles.",
    ], fs=12)
    kit.notas(sl,
        "Participó = al menos 1 Taller, Diplomado o Proyecto registrado (analisis.universo_formados_p3, "
        "sin filtrar a apto_p3 — D31). Facultad normalizada igual que la diapositiva de distribución "
        "por facultad. Categorías con menos de 15 docentes marcadas con ⚠ y excluidas de los "
        "hallazgos. Descriptivo, sin prueba t.")
    return sl


if __name__ == "__main__":
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(UcenSlideKit.SW_EMU), Emu(UcenSlideKit.SH_EMU)
    agregar(prs)
    prs.save(OUT_PPTX)
    print(f"\n✓ Guardado: {OUT_PPTX}")
