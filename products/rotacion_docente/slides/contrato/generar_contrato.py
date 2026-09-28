"""Rotación — Tasa de baja según contrato de entrada, con prueba chi-cuadrado (D39)."""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import rotacion_comun as rc  # noqa: E402
from pptx_helpers import encabezado_prueba, lectura_p, es_significativa  # noqa: E402

df = rc.cargar_datos()
tab = rc.tasa_baja(df, "contrato", rc.CONTRATOS)
CLAVE = "Baja según contrato de entrada: Honorario vs Jornada"
PR, CHI2, GL = rc.chi2(df, "contrato", CLAVE, orden=["HONORARIO", "JORNADA"])
PRUEBAS = [PR]
PCT_J, PCT_H = tab.loc["JORNADA", "pct"], tab.loc["HONORARIO", "pct"]


def agregar(prs):
    assert es_significativa(PR["p"], CLAVE), "El veredicto cambió: reescribir título y punteos"
    kit = rc.kit_para(HERE)
    fig = kit.new_chart_fig()
    ax = kit.chart_axes(fig, left=0.25, right=0.25, top=0.20, bottom=0.14)
    x = np.arange(2)
    act = 100 - tab["pct"].values
    ax.bar(x, act, width=0.5, color=rc.COL_ACTIVO, label="Activo", zorder=3)
    ax.bar(x, tab["pct"].values, bottom=act, width=0.5, color=rc.COL_BAJA, label="Baja", zorder=3)
    for xi, a, b, n in zip(x, act, tab["pct"].values, tab["n"].values):
        rc.etiqueta(ax, xi, a / 2, f"{a:.1f}%", ha="center", va="center")
        rc.etiqueta(ax, xi, a + b / 2, f"{b:.1f}%", ha="center", va="center")
        ax.text(xi, -4, f"N°={n}", ha="center", va="top", fontsize=9, color="#C8DCF0")
    ax.set_xticks(x); ax.set_xticklabels(["Jornada", "Honorario"], color="white", fontsize=11)
    ax.tick_params(axis="x", pad=18)
    ax.set_ylim(0, 100)
    ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), fontsize=10, frameon=False, labelcolor="white")
    rc.estilo(ax, "")
    ax.text(0.5, 1.09, encabezado_prueba("Chi-cuadrado", "χ²", CHI2, PR["p"], CLAVE), transform=ax.transAxes,
            ha="center", va="bottom", fontsize=9.5, color="#F2D675", fontweight="bold")
    chart = kit.save_chart(fig, "contrato_chart.png")

    sl = rc.lamina_base(kit, prs, "La rotación se concentra en Honorario",
                        "% de docentes que no aparece en la planeación 2026, según su contrato de entrada")
    kit.pic_chart(sl, prs, chart)
    kit.punteo_numerado(sl, [
        f"Honorario: {PCT_H:.1f}% de baja; Jornada: {PCT_J:.1f}%. Un docente a honorarios tiene "
        f"{PCT_H / PCT_J:.1f} veces más probabilidad de no seguir en 2026.",
        lectura_p(PR["p"], "prueba chi-cuadrado", CLAVE).split(" (es poco")[0].rstrip(".") + ".",
    ], fs=12)
    kit.notas(sl,
        "D39: contrato de entrada para todos (activos y bajas). Con el criterio híbrido anterior (D35: activos "
        "con su contrato 2026) la brecha se veía menor (33.3% vs 17.6%) porque los 59 que pasaron de Jornada a "
        "Honorario contaban como activos de Honorario. Chi-cuadrado de independencia, 1 docente = 1 caso.")
    return sl
