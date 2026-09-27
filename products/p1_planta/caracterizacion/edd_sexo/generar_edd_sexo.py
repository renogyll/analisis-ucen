"""
P1 — Caracterización del Cuerpo Académico de Planta
Calificación EDD (Evaluación de Desempeño Docente) según Sexo del Docente — Jornada.

EDD = evaluación hecha por la jefatura/director (distinta de la evaluación estudiantil).
Fuente: intel.evaluacion_jefes (D28), 1 fila por docente × año de evaluación (2022-2025).

Revisión 2026-09-27 (D37): se usa la EDD limpia (sin notas dañadas de 2024-2025, ver
edd_comun.py). La primera diapositiva muestra el problema de datos: nota original vs limpia
por año, y cuánto afectó a cada sexo. La segunda compara hombres y mujeres con la nota limpia
(descriptivo + prueba en una diapositiva).

FUENTE: intel.evaluacion_jefes (Postgres, en vivo) — vía edd_comun.cargar_edd
SALIDA: P1_edd_sexo.pptx (2 diapositivas) + edd_sexo_anio_chart.png + edd_sexo_chart.png
"""
import sys; sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "shared"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import CASCADE, OUTPUTS
from pptx_helpers import UcenSlideKit, lectura_p, prueba_dict, encabezado_prueba, es_significativa
from edd_comun import cargar_edd, resumen_por_anio, NOTA_LIMPIEZA

import numpy as np
import pandas as pd
import matplotlib.patheffects as pe
from scipy import stats
from sqlalchemy import create_engine
from pptx import Presentation
from pptx.util import Emu

HERE = Path(__file__).parent
OUT_PPTX = Path(OUTPUTS) / "pptx" / "P1_edd_sexo.pptx"
OUT_PPTX.parent.mkdir(parents=True, exist_ok=True)

DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"
COL_HOMBRE = "#5C9BD6"
COL_MUJER = "#FFB74D"
COL_ORIGINAL = "#7A8699"
COL_LIMPIA = "#5C9BD6"
STROKE = [pe.withStroke(linewidth=2, foreground="#0A0F18")]
CLAVE = "EDD limpia: Mujer vs Hombre"

# ── Datos ───────────────────────────────────────────────────────────────────
doc = pd.read_csv(Path(CASCADE) / "01_jornada" / "docentes_jornada.csv", encoding="utf-8-sig")
N_JORNADA = len(doc)

engine = create_engine(DB_URL)
edd = cargar_edd(engine)
N_EDD_DOC = edd["rut_key"].nunique()
escala = resumen_por_anio(edd)
recientes = edd[edd["anio"] >= 2024]
PCT_SOSP_SEXO = (100 * recientes.groupby("sexo")["sospechosa"].mean()).to_dict()

con_sexo = edd[edd["sexo"].isin(["HOMBRE", "MUJER"])]
por_docente = con_sexo.groupby(["rut_key", "sexo"])["edd_limpia"].mean().dropna().reset_index()
hombre = por_docente.loc[por_docente["sexo"] == "HOMBRE", "edd_limpia"]
mujer = por_docente.loc[por_docente["sexo"] == "MUJER", "edd_limpia"]
T_STAT, P_VAL = stats.ttest_ind(mujer, hombre, equal_var=False)   # Welch
N_SIN_LIMPIA = N_EDD_DOC - edd.groupby("rut_key")["edd_limpia"].count().gt(0).sum()

PRUEBAS = [prueba_dict("III · EDD", CLAVE, f"{mujer.mean():.3f} vs {hombre.mean():.3f}", len(por_docente), P_VAL)]

print(f"Universo Jornada: {N_JORNADA}  |  docentes con EDD: {N_EDD_DOC}  |  sin nota limpia: {N_SIN_LIMPIA}")
print(escala.round(3))
print(f"EDD limpia — Mujer {mujer.mean():.3f} (N°={len(mujer)})  Hombre {hombre.mean():.3f} (N°={len(hombre)})  "
      f"t={T_STAT:.3f}  p={P_VAL:.4f}  |  % sospechosas 2024-25 por sexo: {PCT_SOSP_SEXO}")


def agregar_por_anio(prs):
    """Calidad de datos de la EDD: promedio original vs limpio por año."""
    kit = UcenSlideKit(out_dir=HERE)
    kit.ensure_bg()
    fig = kit.new_chart_fig()
    ax = kit.chart_axes(fig, top=0.14)
    anios = escala.index.tolist()
    x = np.arange(len(anios)); w = 0.36
    for off, col, color, lab in [(-w / 2, "original", COL_ORIGINAL, "Nota original"),
                                 (w / 2, "limpia", COL_LIMPIA, "Nota limpia (sin notas dañadas)")]:
        ax.bar(x + off, escala[col], width=w, color=color, alpha=0.92, edgecolor="none", label=lab)
        for xi, v in zip(x + off, escala[col]):
            ax.text(xi, v + 0.015, f"{v:.2f}", ha="center", va="bottom", fontsize=10.5,
                    fontweight="bold", color="white", path_effects=STROKE)
    for xi, pct in zip(x, escala["pct_sospechosa"]):
        if pct > 0:
            ax.text(xi, 0.04, f"{pct:.0f}% de notas\ndañadas", ha="center", va="bottom", fontsize=8,
                    color="white", fontweight="bold", path_effects=STROKE)
    ax.set_xticks(x); ax.set_xticklabels([str(a) for a in anios], fontsize=11, color="white")
    ax.set_ylabel("Calificación EDD promedio (0-1)", color="#AAAAAA", fontsize=9)
    ax.set_ylim(0, 1.15)
    ax.tick_params(axis="x", length=0, pad=6); ax.tick_params(axis="y", colors="#AAAAAA", labelsize=8.5)
    for sp in ax.spines.values():
        sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.7)
    ax.yaxis.grid(True, color="white", alpha=0.07, linewidth=0.5); ax.set_axisbelow(True)
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, fontsize=9, framealpha=0.22, labelcolor="white", facecolor="#101820",
               edgecolor="#444", loc="upper center", bbox_to_anchor=(0.5, 0.99), ncol=2)
    chart_path = kit.save_chart(fig, "edd_sexo_anio_chart.png")

    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.pic_chart(sl, prs, chart_path)
    kit.title(sl, "Calidad de los datos de la EDD por año — Docentes Jornada")
    kit.subtitulo(sl, f"Universo: {N_JORNADA} docentes Jornada  ·  {N_EDD_DOC} con al menos una EDD 2022-2025  ·  "
                      f"nota original vs nota sin las notas dañadas")
    kit.punteo_numerado(sl, [
        f"En 2024 y 2025, entre un tercio y dos quintos de las notas están dañadas (ceros que son datos vacíos y "
        f"notas partidas a la mitad por un componente faltante). Sin ellas, la EDD es estable: "
        f"{escala['limpia'].min():.2f}-{escala['limpia'].max():.2f} los 4 años.",
        f"Las notas dañadas afectaron más a las mujeres ({PCT_SOSP_SEXO.get('MUJER', 0):.0f}% vs "
        f"{PCT_SOSP_SEXO.get('HOMBRE', 0):.0f}% de hombres en 2024-2025). Todas las comparaciones de este bloque "
        f"usan la nota limpia.",
    ], fs=12)
    kit.notas(sl, NOTA_LIMPIEZA + f" {N_SIN_LIMPIA} docentes solo tienen notas dañadas y quedan fuera de las "
                  "comparaciones. Conviene informar este problema a quien administra la base de EDD.")
    return sl


def agregar(prs):
    """Hombres vs mujeres con la EDD limpia (descriptivo + prueba en una diapositiva)."""
    kit = UcenSlideKit(out_dir=HERE)
    kit.ensure_bg()
    series = [hombre, mujer]
    medias = [s.mean() for s in series]
    cis = [stats.t.ppf(0.975, len(s) - 1) * s.std(ddof=1) / np.sqrt(len(s)) for s in series]
    fig = kit.new_chart_fig()
    ax = kit.chart_axes(fig, top=0.14)
    x = np.arange(2)
    ax.bar(x, medias, width=0.42, color=[COL_HOMBRE, COL_MUJER], alpha=0.92, edgecolor="none",
           yerr=cis, capsize=6, error_kw={"ecolor": "#DDDDDD", "linewidth": 1.3})
    for xi, m, ci, s in zip(x, medias, cis, series):
        ax.text(xi, m + ci + 0.015, f"{m:.2f}", ha="center", va="bottom", fontsize=13,
                fontweight="bold", color="white", path_effects=STROKE, zorder=6)
        ax.text(xi, 0.02, f"N°={len(s)} docentes", ha="center", va="bottom", fontsize=8.5, color="white")
    ax.text(0.5, 0.99, encabezado_prueba("Prueba t de Welch", "t", T_STAT, P_VAL, CLAVE),
            transform=ax.transAxes, ha="center", va="top", fontsize=9.5, color="#F2D675", fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels(["Hombre", "Mujer"], fontsize=12, color="white")
    ax.set_ylabel("EDD limpia promedio por docente (0-1)", color="#AAAAAA", fontsize=9)
    ax.set_ylim(0, 1.2)
    ax.tick_params(axis="x", length=0, pad=8); ax.tick_params(axis="y", colors="#AAAAAA", labelsize=8.5)
    for sp in ax.spines.values():
        sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.7)
    ax.yaxis.grid(True, color="white", alpha=0.07, linewidth=0.5); ax.set_axisbelow(True)
    chart_path = kit.save_chart(fig, "edd_sexo_chart.png")

    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.pic_chart(sl, prs, chart_path)
    kit.title(sl, "¿Difiere la calificación EDD según sexo? — Docentes Jornada")
    kit.subtitulo(sl, f"EDD limpia, 1 valor por docente  ·  N°={len(por_docente)} docentes con nota limpia y sexo "
                      f"registrado  ·  barras = intervalo de confianza 95%")
    if es_significativa(P_VAL, CLAVE):
        mayor = "los hombres" if hombre.mean() > mujer.mean() else "las mujeres"
        frase = f"Con la nota limpia, {mayor} tienen una calificación EDD más alta"
    else:
        frase = "Con la nota limpia, hombres y mujeres tienen una calificación EDD similar"
    kit.punteo_numerado(sl, [
        f"{frase}: hombres {hombre.mean():.2f} vs mujeres {mujer.mean():.2f}.",
        lectura_p(P_VAL, clave=CLAVE),
    ], fs=12)
    kit.notas(sl, "La diferencia a favor de los hombres que mostraba la versión anterior venía de las notas "
                  "dañadas, que afectaron más a las mujeres. " + NOTA_LIMPIEZA)
    return sl


if __name__ == "__main__":
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(UcenSlideKit.SW_EMU), Emu(UcenSlideKit.SH_EMU)
    agregar_por_anio(prs)
    agregar(prs)
    prs.save(OUT_PPTX)
    print(f"\n✓ Guardado: {OUT_PPTX}")
