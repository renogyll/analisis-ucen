"""Rotación — Transición de régimen entre los activos: contrato de entrada vs contrato 2026 (D35)."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import rotacion_comun as rc  # noqa: E402

df = rc.cargar_datos()
N_ACTIVO = int((df["estado"] == "Activo").sum())
N_JH = int((df["transicion"] == "Jornada -> Honorario").sum())
N_HJ = int((df["transicion"] == "Honorario -> Jornada").sum())
N_TRANS = N_JH + N_HJ
N_J_ACT = int(((df["contrato"] == "JORNADA") & (df["estado"] == "Activo")).sum())


def agregar(prs):
    kit = rc.kit_para(HERE)
    fig = kit.new_chart_fig()
    ax = kit.chart_axes(fig, left=0.30, right=0.30, top=0.08, bottom=0.18)
    ax.bar([0, 1], [N_JH, N_HJ], width=0.5, color=[rc.COL_TRANS, rc.COL_BAJA], zorder=3)
    for xi, v in [(0, N_JH), (1, N_HJ)]:
        rc.etiqueta(ax, xi, v + 1.5, f"{v}", ha="center", va="bottom", fontsize=18)
    ax.set_xticks([0, 1]); ax.set_xticklabels(["Jornada → Honorario", "Honorario → Jornada"], color="white", fontsize=11)
    ax.set_ylim(0, max(N_JH, N_HJ) * 1.3)
    rc.estilo(ax, "")
    chart = kit.save_chart(fig, "transicion_chart.png")

    sl = rc.lamina_base(kit, prs, "El cambio de contrato va casi siempre de Jornada a Honorario",
                        f"Universo: {N_ACTIVO} docentes activos · {N_TRANS} cambiaron de contrato entre su registro "
                        "histórico y la planeación 2026")
    kit.pic_chart(sl, prs, chart)
    kit.punteo_numerado(sl, [
        f"{N_JH} docentes pasaron de Jornada a Honorario y {N_HJ} de Honorario a Jornada.",
        f"Los {N_JH} equivalen al {100 * N_JH / N_J_ACT:.0f}% de los {N_J_ACT} docentes Jornada que siguen activos.",
        "En las tasas de baja cuentan con su contrato de entrada: siguen activos, no son bajas.",
    ], fs=12)
    kit.notas(sl, "Descriptivo. La lista con nombre y RUT de los transicionados se exporta aparte "
                  "(outputs/transiciones_jornada_honorario.csv, generado por el ETL; contiene datos personales).")
    return sl
