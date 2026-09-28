"""Rotación — Perfil de los docentes que cambiaron de contrato: sexo, escalafón y facultad.
Descriptivo: grupo chico (73), sin pruebas."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import rotacion_comun as rc  # noqa: E402

df = rc.cargar_datos()
trans = df[df["transicion"] != "N/A (baja o sin cambio)"].copy()
N = len(trans)
trans["fac_"] = trans["fac"].fillna("Sin facultad")
sexo = trans["sexo_"].fillna("Sin dato").value_counts()
esc = trans["escalafon"].fillna("Sin dato").value_counts()
fac = trans["fac_"].value_counts()
FAC_ORD = rc.FACULTADES + ["Sin facultad"]
FAC_ET = ["Medicina", "Ingeniería", "Educación", "Economía", "Derecho", "Sin\nfacultad"]


def _barras(ax, cats, etiquetas, serie, colores, titulo):
    vals = [int(serie.get(c, 0)) for c in cats]
    ax.bar(range(len(cats)), vals, width=0.6, color=colores, zorder=3)
    for xi, v in enumerate(vals):
        rc.etiqueta(ax, xi, v + 1, f"{v}", ha="center", va="bottom")
    ax.set_xticks(range(len(cats)))
    ax.set_xticklabels(etiquetas, color="white", fontsize=8 if len(cats) > 3 else 8.5)
    ax.set_ylim(0, max(vals) * 1.25)
    rc.estilo(ax, titulo)


def agregar(prs):
    kit = rc.kit_para(HERE)
    fig, axes = rc.paneles(kit, [0.8, 0.9, 1.7], bottom=0.16)
    a1, a2, a3 = axes
    _barras(a1, rc.SEXOS, rc.SEXOS, sexo, ["#E88FB0", rc.COL_ACTIVO], "Sexo")
    cats_esc = rc.ESCALAFONES + (["Sin dato"] if "Sin dato" in esc else [])
    _barras(a2, cats_esc, cats_esc, esc, [rc.COL_ACTIVO, rc.COL_TRANS, rc.GRIS][:len(cats_esc)], "Escalafón")
    _barras(a3, FAC_ORD, FAC_ET, fac, [rc.COL_ACTIVO] * 5 + [rc.GRIS], "Facultad")
    chart = rc.guardar_paneles(kit, fig, axes, "perfil_transicionados_chart.png")

    sl = rc.lamina_base(kit, prs, "Quiénes cambiaron de contrato",
                        f"Universo: {N} docentes activos que cambiaron de contrato · descriptivo, grupo chico (sin pruebas)")
    kit.pic_chart(sl, prs, chart)
    kit.punteo_numerado(sl, [
        f"{sexo.get('Mujer', 0)} mujeres y {sexo.get('Hombre', 0)} hombres; {esc.get('Docente', 0)} de {N} "
        "son del escalafón Docente.",
        f"{fac.get('Sin facultad', 0)} de {N} no tienen facultad registrada.",
    ], fs=12)
    kit.notas(sl, "Sin pruebas estadísticas: con 73 casos repartidos en varias categorías, las celdas quedan "
                  "demasiado chicas.")
    return sl
