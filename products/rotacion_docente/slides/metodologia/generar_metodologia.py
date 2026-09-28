"""Rotación — Metodología: línea de tiempo del registro histórico al corte 2026 (D35, D39)."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import rotacion_comun as rc  # noqa: E402

df = rc.cargar_datos()
N = len(df)
N_ALTAS_EXCLUIDAS = rc.n_altas()   # RUT del archivo 2026 sin registro histórico (D35)


def agregar(prs):
    kit = rc.kit_para(HERE)
    fig = kit.new_chart_fig()
    ax = fig.add_axes([0, 0, 1, 1], facecolor="none"); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    y, x0, xc, xk = 0.50, 0.15, 0.48, 0.60
    ax.plot([x0, xc], [y, y], color="white", lw=2.5, alpha=0.85)
    ax.scatter([x0], [y], s=200, color=rc.COL_ACTIVO, edgecolor="white", linewidth=1.5, zorder=5)
    ax.text(x0, y + 0.17, "REGISTRO HISTÓRICO", ha="center", fontsize=12, fontweight="bold", color="white")
    ax.text(x0, y - 0.13, f"{N:,} docentes",
            ha="center", va="top", fontsize=9, color="#C8DCF0")
    ax.plot([xc, xc], [y - 0.30, y + 0.30], color="white", lw=1.3, ls="--", alpha=0.6)
    ax.text(xc, y + 0.36, "CORTE — PLANEACIÓN 2026", ha="center", fontsize=12, fontweight="bold", color="white")
    ax.text(xc, y - 0.34, "archivo de dotación vigente", ha="center", va="top", fontsize=9, color="#C8DCF0")
    ya, yb = y + 0.20, y - 0.20
    ax.plot([xc, xk, 0.74], [y, ya, ya], color=rc.COL_ACTIVO, lw=2.8, solid_capstyle="round")
    ax.annotate("", xy=(0.755, ya), xytext=(0.74, ya), arrowprops=dict(arrowstyle="-|>", color=rc.COL_ACTIVO, lw=2.8))
    ax.text(0.775, ya, "ACTIVO\naparece en 2026", fontsize=10.5, fontweight="bold", color=rc.COL_ACTIVO, va="center")
    ax.plot([xc, xk, 0.72], [y, yb, yb], color=rc.COL_BAJA, lw=2.8, solid_capstyle="round")
    ax.scatter([0.72], [yb], marker="x", s=160, color=rc.COL_BAJA, linewidth=3.2, zorder=5)
    ax.text(0.755, yb, "BAJA\nno aparece en 2026", fontsize=10.5, fontweight="bold", color=rc.COL_BAJA, va="center")
    chart = kit.save_chart(fig, "metodologia_chart.png")

    sl = rc.lamina_base(kit, prs, "Cómo se mide la rotación",
                        "Dos fuentes: el registro histórico de docentes y la planeación docente 2026")
    kit.pic_chart(sl, prs, chart)
    kit.punteo_numerado(sl, [
        "Activo = el docente aparece en la planeación 2026; baja = no aparece. Se sabe si se fue, no cuándo.",
        "Cada docente se compara según su contrato de entrada (Jornada u Honorario), siga activo o no.",
        f"Quedan fuera {N_ALTAS_EXCLUIDAS} docentes nuevos de 2026 sin registro histórico, y la antigüedad "
        "(sin fecha de salida no se puede medir para las bajas).",
    ], fs=12)
    kit.notas(sl,
        "D35 y D39. Contrato de entrada = tipo_contrato_tag del registro histórico (analisis.universo_base); "
        "reemplaza el criterio híbrido de D35. La antigüedad se descartó porque, sin fecha de salida, para "
        "las bajas se mide hasta hoy (queda inflada) y la fecha de ingreso falta en el 58% de las bajas de "
        "Jornada vs 6% de los activos.")
    return sl
