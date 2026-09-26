"""
P1 — Caracterización del Cuerpo Académico de Planta
Calificación EDD (Evaluación de Desempeño Docente) según Sexo del Docente — Jornada.

EDD = evaluación hecha por la jefatura/director (distinta de la evaluación estudiantil).
Fuente: intel.evaluacion_jefes (D28), 1 fila por docente × año de evaluación (2022-2025).

Revisión 2026-09-26 (D36): la escala de edd_total cambió entre 2023 y 2024, así que la
comparación usa la EDD ajustada por año (edd_comun.py) y se agrega una diapositiva por año
que muestra el cambio de escala y la inversión de la brecha por sexo (mujeres más alto en
2022-2023, hombres más alto en 2024-2025). La diapositiva descriptiva y la de prueba t se
fundieron en una sola (revisión, obs. 21).

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
from pptx_helpers import UcenSlideKit, lectura_p, prueba_dict
from edd_comun import cargar_edd, resumen_por_anio, NOTA_AJUSTE, ANIO_REF

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
STROKE = [pe.withStroke(linewidth=2, foreground="#0A0F18")]

# ── Datos ───────────────────────────────────────────────────────────────────
doc = pd.read_csv(Path(CASCADE) / "01_jornada" / "docentes_jornada.csv", encoding="utf-8-sig")
N_JORNADA = len(doc)

engine = create_engine(DB_URL)
edd = cargar_edd(engine)
N_EDD_DOC = edd["rut_key"].nunique()
con_sexo = edd[edd["sexo"].isin(["HOMBRE", "MUJER"])]

# Por año (escala original): media por docente-año
por_anio = con_sexo.pivot_table(index="anio", columns="sexo", values="edd_total", aggfunc="mean")
n_anio = con_sexo.pivot_table(index="anio", columns="sexo", values="rut_key", aggfunc="nunique")
escala = resumen_por_anio(edd)

# Comparación principal: EDD ajustada, 1 valor por docente
por_docente = con_sexo.groupby(["rut_key", "sexo"])["edd_aj"].mean().reset_index()
hombre = por_docente.loc[por_docente["sexo"] == "HOMBRE", "edd_aj"]
mujer = por_docente.loc[por_docente["sexo"] == "MUJER", "edd_aj"]
T_STAT, P_VAL = stats.ttest_ind(mujer, hombre, equal_var=False)   # Welch
N_SIN_DATO = N_EDD_DOC - len(por_docente)

PRUEBAS = [prueba_dict("III · EDD", "EDD ajustada por año: Mujer vs Hombre",
                       f"{mujer.mean():.2f} vs {hombre.mean():.2f}", len(por_docente), P_VAL)]

print(f"Universo Jornada: {N_JORNADA}  |  docentes con EDD: {N_EDD_DOC}  |  con sexo: {len(por_docente)}")
print("EDD original por año y sexo:"); print(por_anio.round(3))
print(f"EDD ajustada — Mujer {mujer.mean():.3f} (N°={len(mujer)})  Hombre {hombre.mean():.3f} "
      f"(N°={len(hombre)})  t={T_STAT:.3f}  p={P_VAL:.4f}")


def agregar_por_anio(prs):
    """EDD original por año y sexo: muestra el cambio de escala 2023→2024 y la inversión
    de la brecha por sexo."""
    kit = UcenSlideKit(out_dir=HERE)
    kit.ensure_bg()
    fig = kit.new_chart_fig()
    ax = kit.chart_axes(fig, top=0.14)

    anios = por_anio.index.tolist()
    x = np.arange(len(anios)); w = 0.36
    for off, sexo, col, lab in [(-w / 2, "HOMBRE", COL_HOMBRE, "Hombre"), (w / 2, "MUJER", COL_MUJER, "Mujer")]:
        ax.bar(x + off, por_anio[sexo], width=w, color=col, alpha=0.92, edgecolor="none", label=lab)
        for xi, v, n in zip(x + off, por_anio[sexo], n_anio[sexo]):
            ax.text(xi, v + 0.015, f"{v:.2f}", ha="center", va="bottom", fontsize=10.5,
                    fontweight="bold", color="white", path_effects=STROKE)
            ax.text(xi, 0.02, f"N°={int(n)}", ha="center", va="bottom", fontsize=7.5, color="white")
    ax.axvline(1.5, color="white", linestyle="--", linewidth=1, alpha=0.5)
    ax.text(1.52, 1.07, "cambio de escala", color="#DDDDDD", fontsize=8.5, style="italic")
    ax.set_xticks(x); ax.set_xticklabels([str(a) for a in anios], fontsize=11, color="white")
    ax.set_ylabel("Calificación EDD promedio (escala original 0-1)", color="#AAAAAA", fontsize=9)
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
    kit.title(sl, "Calificación EDD por año y sexo — Docentes Jornada")
    kit.subtitulo(sl, f"Universo: {N_JORNADA} docentes Jornada  ·  {N_EDD_DOC} con al menos una EDD "
                      f"2022-2025  ·  escala original, sin ajustar")
    e22_23 = escala.loc[[2022, 2023], "mean"].mean(); e24_25 = escala.loc[[2024, 2025], "mean"].mean()
    kit.punteo_numerado(sl, [
        f"La EDD promedio baja de {e22_23:.2f} (2022-2023) a {e24_25:.2f} (2024-2025), en todas las "
        f"facultades aunque con distinta magnitud: sugiere un cambio de escala o de instrumento más que "
        f"de desempeño. Por eso las comparaciones siguientes usan la EDD ajustada por año.",
        "La brecha por sexo se invierte: las mujeres puntúan más alto en 2022-2023 y los hombres en "
        "2024-2025.",
    ], fs=12)
    kit.notas(sl, "Promedio de edd_total por docente-año, escala original. " + NOTA_AJUSTE)
    return sl


def agregar(prs):
    """Comparación principal (fundida descriptivo + prueba t): EDD ajustada por año, Hombre vs Mujer."""
    kit = UcenSlideKit(out_dir=HERE)
    kit.ensure_bg()
    grupos = ["Hombre", "Mujer"]
    series = [hombre, mujer]
    medias = [s.mean() for s in series]
    cis = [stats.t.ppf(0.975, len(s) - 1) * s.std(ddof=1) / np.sqrt(len(s)) for s in series]
    colors = [COL_HOMBRE, COL_MUJER]

    fig = kit.new_chart_fig()
    ax = kit.chart_axes(fig, top=0.14)
    x = np.arange(2)
    ax.bar(x, medias, width=0.42, color=colors, alpha=0.92, edgecolor="none",
           yerr=cis, capsize=6, error_kw={"ecolor": "#DDDDDD", "linewidth": 1.3})
    for xi, m, ci, s in zip(x, medias, cis, series):
        ax.text(xi, m + ci + 0.015, f"{m:.2f}", ha="center", va="bottom", fontsize=13,
                fontweight="bold", color="white", path_effects=STROKE, zorder=6)
        ax.text(xi, 0.02, f"N°={len(s)} docentes", ha="center", va="bottom", fontsize=8.5, color="white")
    sig = "significativa" if P_VAL < 0.05 else "no significativa"
    ax.text(0.5, 0.99, f"Prueba t de Welch:  t = {T_STAT:.2f}   ·   p = {P_VAL:.4f}   ·   diferencia {sig} al 5%",
            transform=ax.transAxes, ha="center", va="top", fontsize=9.5, color="#F2D675", fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels(grupos, fontsize=12, color="white")
    ax.set_ylabel(f"EDD ajustada por año (escala {ANIO_REF})", color="#AAAAAA", fontsize=9)
    ax.set_ylim(0, max(medias) * 1.5)
    ax.tick_params(axis="x", length=0, pad=8); ax.tick_params(axis="y", colors="#AAAAAA", labelsize=8.5)
    for sp in ax.spines.values():
        sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.7)
    ax.yaxis.grid(True, color="white", alpha=0.07, linewidth=0.5); ax.set_axisbelow(True)
    chart_path = kit.save_chart(fig, "edd_sexo_chart.png")

    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.pic_chart(sl, prs, chart_path)
    kit.title(sl, "¿Difiere la calificación EDD según sexo? — Docentes Jornada")
    kit.subtitulo(sl, f"EDD ajustada por año, 1 valor por docente  ·  N°={len(por_docente)} docentes con "
                      f"EDD y sexo registrados  ·  barras = intervalo de confianza 95%")
    mayor = "los hombres" if hombre.mean() > mujer.mean() else "las mujeres"
    kit.punteo_numerado(sl, [
        f"Con la EDD ajustada por año, {mayor} tienen una calificación promedio más alta: hombres "
        f"{hombre.mean():.2f} vs mujeres {mujer.mean():.2f}.",
        lectura_p(P_VAL) + " La brecha viene de 2024-2025 (ver diapositiva anterior).",
    ], fs=12)
    kit.notas(sl, f"{N_SIN_DATO} docentes con EDD sin sexo registrado, excluidos. " + NOTA_AJUSTE)
    return sl


if __name__ == "__main__":
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(UcenSlideKit.SW_EMU), Emu(UcenSlideKit.SH_EMU)
    agregar_por_anio(prs)
    agregar(prs)
    prs.save(OUT_PPTX)
    print(f"\n✓ Guardado: {OUT_PPTX}")
