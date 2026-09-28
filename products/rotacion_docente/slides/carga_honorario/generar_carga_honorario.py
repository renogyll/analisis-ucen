"""Rotación — Carga docente en Honorario: secciones por semestre dictado de quienes se van vs quienes
siguen, con prueba de Mann-Whitney (D39, extensión de carga)."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import rotacion_comun as rc  # noqa: E402
from pptx_helpers import prueba_dict, es_significativa, lectura_p  # noqa: E402

ROJO = "#D9534F"
df = rc.cargar_datos()
h = df[df["contrato"] == "HONORARIO"].merge(rc.carga_docente(), on="rut_key", how="inner")
BAJA, SIGUE = h.loc[h["baja"] == 1, "sec_sem"], h.loc[h["baja"] == 0, "sec_sem"]
CLAVE = "Secciones por semestre: bajas vs activos — Honorario"
_u, _p = stats.mannwhitneyu(BAJA, SIGUE)
PRUEBAS = [prueba_dict(rc.BLOQUE_EXT, CLAVE, f"Bajas: {BAJA.mean():.2f} / Siguen: {SIGUE.mean():.2f} secciones por semestre",
                       len(h), _p, prueba="Mann-Whitney")]
TRAMOS = ["1", "2", "3", "4 o más"]


def tramo(x):
    return pd.cut(x, [0, 1.5, 2.5, 3.5, 99], labels=TRAMOS)


def agregar(prs):
    assert es_significativa(_p, CLAVE), "El veredicto cambió: reescribir título y punteos"
    kit = rc.kit_para(HERE)
    dist = pd.DataFrame({"Se van": tramo(BAJA).value_counts(normalize=True).reindex(TRAMOS) * 100,
                         "Siguen": tramo(SIGUE).value_counts(normalize=True).reindex(TRAMOS) * 100})
    fig, axes = rc.paneles(kit, [1.2, 1.1], bottom=0.16,
                           leyenda=[("Se van", ROJO), ("Siguen", rc.COL_ACTIVO)])
    ax = axes[0]
    x = np.arange(len(TRAMOS))
    for i, (col, color) in enumerate([("Se van", ROJO), ("Siguen", rc.COL_ACTIVO)]):
        xs = x + (i - 0.5) * 0.38
        ax.bar(xs, dist[col], width=0.36, color=color, zorder=3)
        for xi, v in zip(xs, dist[col]):
            rc.etiqueta(ax, xi, v + 1, f"{v:.0f}%", ha="center", va="bottom", fontsize=9)
    ax.set_xticks(x); ax.set_xticklabels(TRAMOS, color="white", fontsize=9.5)
    ax.set_ylim(0, dist.values.max() * 1.25)
    rc.estilo(ax, "Secciones que dictaban por semestre" + chr(10) + "(% de docentes)")
    # Panel derecho: % que se va según la carga (la tendencia completa, no solo el promedio)
    ax2 = axes[1]
    h2 = h.assign(tramo=tramo(h["sec_sem"]))
    tasa = h2.groupby("tramo", observed=False)["baja"].agg(["mean", "size"]).reindex(TRAMOS)
    ax2.bar(np.arange(len(TRAMOS)), tasa["mean"] * 100, color=ROJO, width=0.6, zorder=3)
    for xi, (v, n) in enumerate(zip(tasa["mean"] * 100, tasa["size"])):
        rc.etiqueta(ax2, xi, v + 1, f"{v:.0f}%", ha="center", va="bottom", fontsize=10)
    ax2.set_xticks(np.arange(len(TRAMOS)))
    ax2.set_xticklabels([f"{t}\nN°={n}" for t, n in zip(TRAMOS, tasa["size"])], color="white", fontsize=8.5)
    ax2.set_ylim(0, tasa["mean"].max() * 100 * 1.3)
    rc.estilo(ax2, "% que se va, según" + chr(10) + "secciones por semestre")
    chart = rc.guardar_paneles(kit, fig, axes, "carga_honorario_chart.png")

    una_baja, una_sigue = (tramo(BAJA) == "1").mean() * 100, (tramo(SIGUE) == "1").mean() * 100
    TASA = tasa["mean"] * 100
    sl = rc.lamina_base(kit, prs, "Los Honorarios que se van dictaban menos cursos",
                        "Docentes Honorario con clases 2023-2025 · secciones dictadas por semestre en que hicieron clases")
    kit.pic_chart(sl, prs, chart)
    kit.punteo_numerado(sl, [
        f"El {una_baja:.0f}% de quienes se van dictaba una sola sección por semestre, contra el {una_sigue:.0f}% de "
        "quienes siguen.",
        f"El % que se va baja a medida que aumenta la carga: de {TASA.iloc[0]:.0f}% con 1 sección a {TASA.iloc[-1]:.0f}% "
        "con 4 o más.",
        lectura_p(_p, "prueba de Mann-Whitney", CLAVE).split(" (es poco")[0].rstrip(".") + ".",
    ], fs=12)
    kit.notas(sl,
        "Secciones por semestre = secciones distintas (período + asignatura + sección) en las calificaciones de alumnos "
        "2023-2025, divididas por los semestres en que el docente dictó clases. Mann-Whitney porque la distribución no "
        "es simétrica. En Jornada la diferencia va en la misma dirección pero no es significativa. D39.")
    return sl
