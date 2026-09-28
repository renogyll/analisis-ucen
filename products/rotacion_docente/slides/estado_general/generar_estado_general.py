"""Rotación — Cifras generales: activos y bajas del universo histórico (D35)."""
import sys
from pathlib import Path
from pptx.enum.text import PP_ALIGN
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import rotacion_comun as rc  # noqa: E402

df = rc.cargar_datos()
N = len(df)
N_ACTIVO = int((df["estado"] == "Activo").sum())
N_BAJA = int(df["baja"].sum())
N_TRANS = int((df["transicion"] != "N/A (baja o sin cambio)").sum())
VERDE, ROJO = "#4CAF7A", "#D9534F"


def agregar(prs):
    kit = rc.kit_para(HERE)
    sl = rc.lamina_base(kit, prs, f"1 de cada 4 docentes del registro histórico no sigue en 2026",
                        f"Universo: {N:,} docentes del registro histórico (Jornada y Honorario)")
    # Círculos con área proporcional al N° (pedido del usuario 2026-09-27): verde activos, rojo bajas.
    from matplotlib.patches import Circle
    fig = kit.new_chart_fig()
    W, H = fig.get_size_inches()
    ax = fig.add_axes([0, 0, 1, 1], facecolor="none"); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
    r_max = H * 0.40
    for cx, valor, color, titulo in [(W * 0.32, N_ACTIVO, VERDE, "ACTIVOS · siguen en 2026"),
                                     (W * 0.70, N_BAJA, ROJO, "BAJAS · no aparecen en 2026")]:
        r = r_max * (valor / N_ACTIVO) ** 0.5
        cy = H * 0.44
        ax.add_patch(Circle((cx, cy), r, facecolor=color, alpha=0.85, edgecolor="white", linewidth=1.2))
        rc.etiqueta(ax, cx, cy + r * 0.12, f"{valor}", ha="center", va="center", fontsize=30 if r > 0.8 else 22)
        rc.etiqueta(ax, cx, cy - r * 0.38, f"{100 * valor / N:.0f}%", ha="center", va="center", fontsize=12)
        ax.text(cx, cy + r + 0.12, titulo, ha="center", va="bottom", fontsize=12, fontweight="bold", color="white")
    chart = kit.save_chart(fig, "estado_general_chart.png")
    kit.pic_chart(sl, prs, chart)
    kit.punteo_numerado(sl, [
        f"{N_BAJA} de {N:,} docentes ({100 * N_BAJA / N:.0f}%) no aparece en la planeación 2026.",
        f"De los {N_ACTIVO} que siguen, {N_TRANS} cambiaron de contrato (Jornada ↔ Honorario).",
    ], fs=13)
    kit.notas(sl, "Área de cada círculo proporcional al N° de docentes. Baja = no aparece en la planeación 2026 (supuesto D35: no se pudo verificar por otra vía). "
                  "La transición de régimen se detalla más adelante.")
    return sl
