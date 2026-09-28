"""Rotación — Balance de entradas y salidas: de la planta del registro a la planta 2026 (puente),
con prueba chi-cuadrado sobre el contrato de quienes entran vs quienes salen (D39, extensión 1)."""
import sys
from pathlib import Path
import numpy as np
from scipy import stats
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import rotacion_comun as rc  # noqa: E402
from pptx_helpers import prueba_dict, es_significativa, lectura_p  # noqa: E402

VERDE, ROJO = "#4CAF7A", "#D9534F"
df = rc.cargar_datos()
plan = rc.cargar_plan()
altas = plan[~plan["rut_key"].isin(df["rut_key"])]["NIVEL_PROF"].value_counts()

F = {}
for c in rc.CONTRATOS:
    otro = "HONORARIO" if c == "JORNADA" else "JORNADA"
    s = df[df["contrato"] == c]
    F[c] = dict(ini=len(s), baja=int(s["baja"].sum()),
                sale=int(((s["estado"] == "Activo") & (s["tipo_contrato_2026"] == otro)).sum()),
                llega=int(((df["contrato"] == otro) & (df["tipo_contrato_2026"] == c)).sum()),
                nuevos=int(altas.get(c, 0)), fin=int((plan["NIVEL_PROF"] == c).sum()))
    cuadra = F[c]["ini"] - F[c]["baja"] - F[c]["sale"] + F[c]["llega"] + F[c]["nuevos"]
    assert cuadra == F[c]["fin"], f"El balance de {c} no cuadra: {cuadra} vs {F[c]['fin']}"

ENTRAN = {c: F[c]["nuevos"] for c in rc.CONTRATOS}
SALEN = {c: F[c]["baja"] for c in rc.CONTRATOS}
PCT_H_ENTRAN = 100 * ENTRAN["HONORARIO"] / sum(ENTRAN.values())
PCT_H_SALEN = 100 * SALEN["HONORARIO"] / sum(SALEN.values())
CLAVE = "Contrato de quienes entran (nuevos 2026) vs quienes salen (bajas)"
_t = np.array([[ENTRAN["JORNADA"], ENTRAN["HONORARIO"]], [SALEN["JORNADA"], SALEN["HONORARIO"]]])
_chi2, _p, _, _ = stats.chi2_contingency(_t)
PRUEBAS = [prueba_dict(rc.BLOQUE_EXT, CLAVE, f"Honorario: {PCT_H_ENTRAN:.1f}% de quienes entran / {PCT_H_SALEN:.1f}% de quienes salen",
                       int(_t.sum()), _p, prueba="chi-cuadrado")]


def agregar(prs):
    assert es_significativa(_p, CLAVE), "El veredicto cambió: reescribir título y punteos"
    kit = rc.kit_para(HERE)
    fig, axes = rc.paneles(kit, [1, 1], bottom=0.14,
                           leyenda=[("Planta", rc.COL_ACTIVO), ("Salen", ROJO), ("Entran", VERDE)])
    ymax = max(max(f["ini"], f["fin"]) for f in F.values()) * 1.22
    for ax, c in zip(axes, rc.CONTRATOS):
        f = F[c]
        pasos = [("Registro", f["ini"], "total"), ("Bajas", -f["baja"], "paso"), ("Pasan\na otro", -f["sale"], "paso"),
                 ("Llegan\nde otro", f["llega"], "paso"), ("Nuevos", f["nuevos"], "paso"), ("2026", f["fin"], "total")]
        nivel = 0
        for i, (_, v, tipo) in enumerate(pasos):
            if tipo == "total":
                ax.bar(i, v, color=rc.COL_ACTIVO, width=0.62, zorder=3)
                rc.etiqueta(ax, i, v + ymax * 0.015, f"{v}", ha="center", va="bottom", fontsize=10)
                nivel = v
            else:
                base = nivel + min(v, 0)
                ax.bar(i, abs(v), bottom=base, color=ROJO if v < 0 else VERDE, width=0.62, zorder=3)
                rc.etiqueta(ax, i, base + abs(v) + ymax * 0.015, f"{v:+d}", ha="center", va="bottom", fontsize=9)
                nivel += v
            if i < len(pasos) - 1:   # línea de conexión entre escalones
                ax.plot([i + 0.31, i + 0.69], [nivel, nivel], color="white", alpha=0.35, lw=0.8, zorder=2)
        ax.set_xticks(range(len(pasos))); ax.set_xticklabels([p[0] for p in pasos], color="white", fontsize=8)
        ax.set_ylim(0, ymax)
        rc.estilo(ax, f"{c.capitalize()}: {f['ini']} → {f['fin']} ({100 * (f['fin'] - f['ini']) / f['ini']:+.0f}%)")
    chart = rc.guardar_paneles(kit, fig, axes, "balance_chart.png")

    J, H = F["JORNADA"], F["HONORARIO"]
    sl = rc.lamina_base(kit, prs, "La planta Jornada se achica y la de Honorario crece",
                        "N° de docentes: del registro histórico a la planeación 2026, paso a paso")
    kit.pic_chart(sl, prs, chart)
    kit.punteo_numerado(sl, [
        f"Jornada pasa de {J['ini']} a {J['fin']}: salen {J['baja']}, {J['sale']} pasan a Honorario y solo entran "
        f"{J['nuevos']} nuevos.",
        f"Honorario pasa de {H['ini']} a {H['fin']}: {H['nuevos']} de los {H['fin']} docentes de 2026 son nuevos.",
        f"El {PCT_H_ENTRAN:.0f}% de quienes entran es Honorario, contra el {PCT_H_SALEN:.0f}% de quienes salen. "
        + lectura_p(_p, "prueba chi-cuadrado", CLAVE).split(":")[0] + ".",
    ], fs=12)
    kit.notas(sl,
        "Registro = contrato de entrada del registro histórico; 2026 = archivo de planeación docente 2026. Nuevos = "
        "docentes del archivo 2026 sin registro histórico. Bajas = no aparecen en 2026. Pasan a otro / llegan de otro "
        "= siguen activos pero cambiaron de contrato. La prueba compara el contrato de quienes entran con el de quienes "
        "salen (chi-cuadrado). D39, extensión 1.")
    return sl
