"""Rotación — Formación y permanencia en Jornada: % de baja de quienes se formaron vs quienes no,
en todos los Jornada y solo en quienes dictaron clases 2023-2025 (D39, extensión de formación)."""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import rotacion_comun as rc  # noqa: E402
from pptx_helpers import es_significativa  # noqa: E402

FORMADO, NO_FORMADO = "#4CAF7A", "#8A9BB0"
df = rc.cargar_datos()
j = df[df["contrato"] == "JORNADA"].copy()
j["formado"] = np.where(j["rut_key"].isin(rc.formados()), "Se formó", "No se formó")
j["clases"] = j["rut_key"].isin(rc.carga_docente()["rut_key"])
GRUPOS = [("Todos los Jornada", j), ("Jornada con clases 2023-2025", j[j["clases"]])]
CLAVES = ["Baja según formación — Jornada, todos", "Baja según formación — Jornada con clases"]
PRUEBAS, TAB = [], []
for (nombre, s), clave in zip(GRUPOS, CLAVES):
    pr, _, _ = rc.chi2(s, "formado", clave, orden=["Se formó", "No se formó"])
    pr["bloque"] = rc.BLOQUE_EXT
    PRUEBAS.append(pr); TAB.append(rc.tasa_baja(s, "formado", ["Se formó", "No se formó"]))
SIN_CLASES = j[~j["clases"]]
PCT_NF_SIN = 100 * (SIN_CLASES["formado"] == "No se formó").mean()


def agregar(prs):
    sig_todos, sig_clases = (es_significativa(pr["p"], pr["comparacion"]) for pr in PRUEBAS)
    assert sig_todos and not sig_clases, "El veredicto cambió: reescribir título y punteos"
    kit = rc.kit_para(HERE)
    fig, axes = rc.paneles(kit, [1, 1], bottom=0.14, leyenda=[("Se formó", FORMADO), ("No se formó", NO_FORMADO)])
    for ax, (nombre, _), t, pr in zip(axes, GRUPOS, TAB, PRUEBAS):
        ax.bar([0, 1], t["pct"], color=[FORMADO, NO_FORMADO], width=0.55, zorder=3)
        for xi, (v, n) in enumerate(zip(t["pct"], t["n"])):
            rc.etiqueta(ax, xi, v + 0.8, f"{v:.1f}%", ha="center", va="bottom", fontsize=11)
        ax.set_xticks([0, 1]); ax.set_xticklabels([f"Se formó\nN°={t['n'].iloc[0]}", f"No se formó\nN°={t['n'].iloc[1]}"],
                                                 color="white", fontsize=9)
        ax.set_ylim(0, 30)
        veredicto = "diferencia significativa" if es_significativa(pr["p"], pr["comparacion"]) else "sin diferencia significativa"
        rc.estilo(ax, f"{nombre}\n% de baja · {veredicto}")
    chart = rc.guardar_paneles(kit, fig, axes, "formacion_jornada_chart.png")

    t0, t1 = TAB
    sl = rc.lamina_base(kit, prs, "En Jornada, formarse no se asocia a quedarse entre quienes dictan clases",
                        "% de docentes Jornada que no aparece en 2026, según si cursaron alguna instancia formativa")
    kit.pic_chart(sl, prs, chart)
    kit.punteo_numerado(sl, [
        f"En todos los Jornada, quienes se formaron salen menos ({t0['pct'].iloc[0]:.1f}% vs {t0['pct'].iloc[1]:.1f}%).",
        f"Entre quienes dictaron clases la diferencia desaparece ({t1['pct'].iloc[0]:.1f}% vs {t1['pct'].iloc[1]:.1f}%).",
        f"La brecha del total viene de los {len(SIN_CLASES)} Jornada sin clases registradas 2023-2025: el "
        f"{PCT_NF_SIN:.0f}% no se formó y se van más.",
    ], fs=12)
    kit.notas(sl,
        "Formado = al menos una instancia formativa (Taller, Diplomado o Proyecto) en consolidados.participacion_formacion. "
        "Con clases = aparece como docente en las calificaciones de alumnos 2023-2025. Chi-cuadrado en cada grupo. "
        "Solo Jornada (decisión del usuario): en Honorario no hay diferencia significativa. D39.")
    return sl
