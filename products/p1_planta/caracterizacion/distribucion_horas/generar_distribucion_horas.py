"""
P1 — Caracterización del Cuerpo Académico de Planta
Distribución de la Jornada (horas semanales de dotación) — Docentes de Jornada.

Pedido de la contraparte: profundizar en `jornada_dot` (consolidados.docente /
analisis.universo_base) — horas semanales contratadas según DOTACION. No
confundir con `tipo_contrato_tag` (Jornada/Honorario, ya usado en todo P1):
acá se trabaja DENTRO del universo Jornada, viendo cuántas horas trabaja cada
docente. 3 diapositivas: intro, dona (composición general + detalle de jornada
parcial) y comparación por sexo/jerarquía.

Categorías: Completa (44h, la moda absoluta) / Parcial (<44h) / Sin dato-variable
(sin registro en DOTACION, o "Jornada indefinida Variable" sin horas fijas —
mismo patrón de brecha NOMINA→DOTACION que D22/D23, no es un hallazgo nuevo).

FUENTE: data/cascade/01_jornada/docentes_jornada.csv (en vivo, sin copiar)
SALIDA: P1_distribucion_horas.pptx (3 diapositivas) + distribucion_horas_donut_chart.png
        + distribucion_horas_sexo_jerarquia_chart.png
"""
import sys; sys.stdout.reconfigure(encoding="utf-8")
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "shared"))
from config import CASCADE, OUTPUTS
from pptx_helpers import UcenSlideKit

import numpy as np
import pandas as pd
import matplotlib.patheffects as pe
from matplotlib.patches import ConnectionPatch
from pptx import Presentation
from pptx.util import Emu

HERE = Path(__file__).parent
OUT_PPTX = Path(OUTPUTS) / "pptx" / "P1_distribucion_horas.pptx"
OUT_PPTX.parent.mkdir(parents=True, exist_ok=True)

CAT_ORD = ["Parcial", "Completa", "Sin dato / variable"]   # orden de despliegue en la dona
COL_COMPLETA = "#5C9BD6"
COL_PARCIAL = "#FFB74D"
COL_SINDATO = "#9085E9"   # violeta — chequeado con validate_palette.js (CVD/contraste OK
                          # junto a #5C9BD6/#FFB74D; mismo criterio de paleta ya usado en P1)
COL_MAP = {"Completa": COL_COMPLETA, "Parcial": COL_PARCIAL, "Sin dato / variable": COL_SINDATO}

CAT_JERARQUIA = ["INSTRUCTOR DOCENTE", "INSTRUCTOR REGULAR",
                  "ASISTENTE DOCENTE",  "ASISTENTE REGULAR",
                  "ASOCIADO DOCENTE",   "ASOCIADO REGULAR",
                  "TITULAR DOCENTE",    "TITULAR REGULAR"]

# ── Datos ───────────────────────────────────────────────────────────────────
doc = pd.read_csv(Path(CASCADE) / "01_jornada" / "docentes_jornada.csv", encoding="utf-8-sig")
N_JORNADA = len(doc)


def _parse_horas(v):
    if pd.isna(v):
        return None
    m = re.search(r"(\d+)", str(v))
    return int(m.group(1)) if m else None


doc["horas"] = doc["jornada_dot"].apply(_parse_horas)
doc["categoria"] = "Sin dato / variable"
doc.loc[doc["horas"] == 44, "categoria"] = "Completa"
doc.loc[doc["horas"].notna() & (doc["horas"] < 44), "categoria"] = "Parcial"

resumen = doc["categoria"].value_counts().reindex(CAT_ORD).fillna(0).astype(int)
N_SIN_HORAS_FIJAS = int((doc["categoria"] == "Sin dato / variable").sum())
N_VARIABLE = int((doc["jornada_dot"] == "Jornada indefinida Variable").sum())
N_SIN_DATO = N_SIN_HORAS_FIJAS - N_VARIABLE

parcial_detalle = (doc.loc[doc["categoria"] == "Parcial"]
                    .groupby("horas").size().sort_index())

print(f"Universo Jornada: {N_JORNADA}")
print(resumen)
print(f"(de los {N_SIN_HORAS_FIJAS} 'Sin dato / variable': {N_SIN_DATO} sin registro en DOTACION, "
      f"{N_VARIABLE} 'Jornada indefinida Variable')")
print("\nDetalle jornada parcial (horas → N° docentes):")
print(parcial_detalle)

# ── Datos para el panel por sexo/jerarquía: solo docentes con horas válidas ───
con_dato = doc[doc["categoria"].isin(["Completa", "Parcial"])].copy()
N_CON_DATO = len(con_dato)

SEXO_ORD = ["HOMBRE", "MUJER"]
tab_sexo = (con_dato.groupby("sexo")["categoria"].value_counts(normalize=True)
            .unstack().reindex(SEXO_ORD)[["Completa", "Parcial"]] * 100)
n_sexo = con_dato.groupby("sexo").size().reindex(SEXO_ORD)

con_dato_jer = con_dato[con_dato["jerarquia"].isin(CAT_JERARQUIA)].copy()
con_dato_jer["escalafon"] = np.where(
    con_dato_jer["jerarquia"].str.contains("REGULAR"), "Regular", "Docente")
ESCALAFON_ORD = ["Docente", "Regular"]
tab_escalafon = (con_dato_jer.groupby("escalafon")["categoria"].value_counts(normalize=True)
                  .unstack().reindex(ESCALAFON_ORD)[["Completa", "Parcial"]] * 100)
n_escalafon = con_dato_jer.groupby("escalafon").size().reindex(ESCALAFON_ORD)
N_SIN_JERARQUIA_VALIDA = N_CON_DATO - len(con_dato_jer)

print(f"\nCon horas válidas (Completa/Parcial): {N_CON_DATO}")
print(tab_sexo.round(1))
print(f"\nPor escalafón (excluidos {N_SIN_JERARQUIA_VALIDA} sin jerarquía válida):")
print(tab_escalafon.round(1))


def agregar_intro(prs):
    """Diapositiva 1: intro / roadmap del mini-tema, sin gráfico."""
    kit = UcenSlideKit(out_dir=HERE)
    kit.ensure_bg()

    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.title(sl, "Distribución de la Jornada (Horas Semanales) — Docentes de Jornada")
    kit.subtitulo(sl,
        f"Universo: {N_JORNADA} docentes Jornada  ·  "
        f"N°={N_CON_DATO} con horas de dotación registradas")
    kit.notas(sl,
        "Pedido de la contraparte: profundizar en jornada_dot (horas semanales de "
        "DOTACION), una dimensión dentro del universo Jornada ya trabajado en el resto "
        "de P1 — no confundir con tipo_contrato_tag (Jornada/Honorario). "
        "Fuente: data/cascade/01_jornada/docentes_jornada.csv.")
    kit.punteo_numerado(sl, [
        "¿Qué es? Las horas semanales con las que cada docente Jornada está "
        "contratado según DOTACION — 44 horas es jornada completa, cualquier valor "
        "menor es jornada parcial.",
        "Composición general: qué proporción del universo tiene jornada completa vs. "
        "parcial, y el detalle de en qué horas se reparte la jornada parcial.",
        "¿La jornada completa se distribuye igual entre hombres y mujeres, y entre "
        "escalafón Docente y Regular? Comparación con prueba de composición en la "
        "última diapositiva.",
    ])
    return sl


def agregar_donut(prs):
    """Diapositiva 2: dona con la composición general + detalle de jornada parcial
    (callout con flecha hacia un mini gráfico de puntos)."""
    kit = UcenSlideKit(out_dir=HERE)
    kit.ensure_bg()

    fig = kit.new_chart_fig()

    # Dona a la izquierda, callout de detalle a la derecha
    ax1 = fig.add_axes([0.02, 0.06, 0.46, 0.92])
    ax1.set_aspect("equal")
    ax2 = fig.add_axes([0.60, 0.28, 0.37, 0.46])

    vals = resumen.values
    colors = [COL_MAP[c] for c in CAT_ORD]
    wedges, _ = ax1.pie(
        vals, colors=colors, startangle=90, counterclock=False,
        wedgeprops=dict(width=0.42, edgecolor="#0A0F18", linewidth=2),
        explode=[0.06 if c == "Parcial" else 0 for c in CAT_ORD],
    )

    stroke = [pe.withStroke(linewidth=2, foreground="#0A0F18")]
    for w, cat, v in zip(wedges, CAT_ORD, vals):
        ang = np.deg2rad((w.theta1 + w.theta2) / 2)
        r_label = 1.28 if cat != "Parcial" else 1.40
        x, y = np.cos(ang) * r_label, np.sin(ang) * r_label
        ha = "left" if x >= 0 else "right"
        pct = 100 * v / N_JORNADA
        ax1.text(x, y, f"{cat}\n{pct:.1f}%  (N°={int(v)})", ha=ha, va="center",
                  fontsize=9.5, fontweight="bold", color=COL_MAP[cat],
                  path_effects=stroke, zorder=6)

    # Límites explícitos con margen para las etiquetas radiales — si no, el pie
    # autoescala solo a los wedges (radio ~1) y las etiquetas a r=1.4 se cortan
    # contra el borde de la figura.
    ax1.set_xlim(-1.75, 1.75)
    ax1.set_ylim(-1.6, 1.6)

    ax1.text(0, 0.08, f"{N_JORNADA}", ha="center", va="center", fontsize=22,
              fontweight="bold", color="white")
    ax1.text(0, -0.14, "docentes\nJornada", ha="center", va="center", fontsize=9,
              color="#AAAAAA")

    # ── Callout: distribución en puntos de la jornada parcial (horas → N°) ────
    # Posiciones categóricas equiespaciadas (no la escala numérica real de horas):
    # con horas tan cercanas entre sí (32/33/36h), el tamaño de los puntos por N°
    # los hace solaparse en una escala lineal — equiespaciado evita eso sin perder
    # el orden ni el valor real (mostrado en la etiqueta de cada punto).
    horas_vals = parcial_detalle.index.values
    ns = parcial_detalle.values
    xpos = np.arange(len(horas_vals))
    sizes = 110 + 1000 * np.sqrt(ns) / np.sqrt(ns.max())
    ax2.scatter(xpos, np.zeros(len(xpos)), s=sizes, color=COL_PARCIAL,
                alpha=0.88, edgecolor="#0A0F18", linewidth=1.1, zorder=4)

    for i, (xi, h, n) in enumerate(zip(xpos, horas_vals, ns)):
        va = "bottom" if i % 2 == 0 else "top"
        y_txt = 0.62 if i % 2 == 0 else -0.62
        ax2.plot([xi, xi], [0, y_txt * 0.55], color=COL_PARCIAL, alpha=0.35, linewidth=0.8, zorder=2)
        ax2.text(xi, y_txt, f"{int(h)}h\nN°={int(n)}", ha="center", va=va, fontsize=7.3,
                  color=COL_PARCIAL, fontweight="bold")

    ax2.set_ylim(-1.15, 1.15)
    ax2.set_xlim(-0.8, len(xpos) - 0.2)
    ax2.set_yticks([])
    ax2.set_xticks([])
    ax2.set_xlabel("Horas semanales (jornada parcial), ordenadas de menor a mayor",
                    color="#AAAAAA", fontsize=7.5)
    for sp in ax2.spines.values():
        sp.set_visible(False)
    ax2.axhline(0, color="white", alpha=0.15, linewidth=0.7, zorder=1)
    ax2.set_title(f"Detalle jornada parcial  ·  N°={int(ns.sum())} docentes",
                   color="#DDDDDD", fontsize=8.5, pad=6)

    # Flecha desde el borde del sector "Parcial" hasta el callout
    w_parcial = wedges[CAT_ORD.index("Parcial")]
    ang_mid = np.deg2rad((w_parcial.theta1 + w_parcial.theta2) / 2)
    x0, y0 = np.cos(ang_mid) * 1.06, np.sin(ang_mid) * 1.06
    con = ConnectionPatch(xyA=(x0, y0), coordsA=ax1.transData,
                           xyB=(0.0, 0.5), coordsB=ax2.transAxes,
                           arrowstyle="-|>", mutation_scale=14,
                           color=COL_PARCIAL, linewidth=1.6, zorder=10)
    fig.add_artist(con)

    chart_path = kit.save_chart(fig, "distribucion_horas_donut_chart.png")

    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.pic_chart(sl, prs, chart_path)
    kit.title(sl, "Composición de la Jornada (Horas Semanales) — Docentes de Jornada")
    kit.subtitulo(sl,
        f"Universo: {N_JORNADA} docentes Jornada  ·  "
        f"{resumen['Completa']} con jornada completa (44h), {resumen['Parcial']} parcial")
    kit.notas(sl,
        f"'Sin dato / variable' = {N_SIN_DATO} sin registro en DOTACION (misma brecha "
        f"NOMINA→DOTACION de D22/D23) + {N_VARIABLE} con 'Jornada indefinida Variable' "
        f"(sin horas fijas). El detalle de jornada parcial muestra cada valor de horas "
        f"registrado y cuántos docentes lo tienen (tamaño del punto ∝ N°).")
    kit.punteo_numerado(sl, [
        f"{resumen['Completa']} de {N_JORNADA} docentes Jornada ({100*resumen['Completa']/N_JORNADA:.1f}%) "
        f"tienen jornada completa (44 horas semanales).",
        f"La jornada parcial ({resumen['Parcial']} docentes, {100*resumen['Parcial']/N_JORNADA:.1f}%) se "
        f"concentra en 22 horas (N°={int(parcial_detalle.get(22,0))}) y 33 horas "
        f"(N°={int(parcial_detalle.get(33,0))}) — juntas explican "
        f"{100*(parcial_detalle.get(22,0)+parcial_detalle.get(33,0))/resumen['Parcial']:.0f}% de la jornada parcial.",
    ])
    return sl


def agregar_sexo_jerarquia(prs):
    """Diapositiva 3: % jornada completa/parcial por sexo y por escalafón, 2 paneles."""
    kit = UcenSlideKit(out_dir=HERE)
    kit.ensure_bg()

    fig = kit.new_chart_fig()
    ax1 = fig.add_axes([0.09, 0.20, 0.38, 0.68])
    ax2 = fig.add_axes([0.58, 0.20, 0.38, 0.68])

    stroke = [pe.withStroke(linewidth=1.8, foreground="#0A0F18")]

    def _panel(ax, tab, n_ser, labels, titulo):
        x = np.arange(len(labels))
        w = 0.5
        ax.bar(x, tab["Completa"], width=w, color=COL_COMPLETA, alpha=0.92,
               edgecolor="none", label="Completa (44h)")
        ax.bar(x, tab["Parcial"], width=w, bottom=tab["Completa"], color=COL_PARCIAL,
               alpha=0.92, edgecolor="none", label="Parcial (<44h)")
        for xi, c, p in zip(x, tab["Completa"], tab["Parcial"]):
            ax.text(xi, c / 2, f"{c:.0f}%", ha="center", va="center", fontsize=10.5,
                     fontweight="bold", color="white", path_effects=stroke, zorder=6)
            ax.text(xi, 101.5, f"Parcial {p:.0f}%", ha="center", va="bottom",
                     fontsize=8.5, fontweight="bold", color=COL_PARCIAL,
                     path_effects=stroke, zorder=6)
        for xi, n in zip(x, n_ser):
            ax.text(xi, 4, f"N°={int(n)}", ha="center", va="bottom", fontsize=7.5,
                     color="white", alpha=0.85)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=10.5, color="white")
        ax.set_ylim(0, 112)
        ax.set_yticks([0, 20, 40, 60, 80, 100])
        ax.tick_params(axis="x", length=0, pad=6)
        ax.tick_params(axis="y", colors="#AAAAAA", labelsize=8)
        for sp in ax.spines.values():
            sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.7)
        ax.yaxis.grid(True, color="white", alpha=0.07, linewidth=0.5)
        ax.set_axisbelow(True)
        ax.set_title(titulo, color="#DDDDDD", fontsize=9.5, pad=8)

    _panel(ax1, tab_sexo, n_sexo, ["Hombre", "Mujer"], "Por sexo")
    _panel(ax2, tab_escalafon, n_escalafon, ["Docente", "Regular"], "Por escalafón")
    ax1.set_ylabel("% de docentes", color="#AAAAAA", fontsize=9)

    handles, lbls = ax1.get_legend_handles_labels()
    fig.legend(handles, lbls, fontsize=9, framealpha=0.22, labelcolor="white",
               facecolor="#101820", edgecolor="#444", loc="upper center",
               bbox_to_anchor=(0.5, 0.99), ncol=2)

    chart_path = kit.save_chart(fig, "distribucion_horas_sexo_jerarquia_chart.png")

    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.pic_chart(sl, prs, chart_path)
    kit.title(sl, "Jornada Completa/Parcial según Sexo y Escalafón — Docentes de Jornada")
    kit.subtitulo(sl,
        f"N°={N_CON_DATO} docentes Jornada con horas de dotación válidas  ·  "
        f"escalafón sobre {len(con_dato_jer)} con jerarquía válida")
    kit.notas(sl,
        f"Excluidos de este gráfico los {N_SIN_HORAS_FIJAS} docentes sin horas válidas "
        f"(Sin dato/Variable) y, en el panel de escalafón, {N_SIN_JERARQUIA_VALIDA} "
        f"adicionales sin jerarquía válida. Escalafón = colapso Docente/Regular, mismo "
        f"criterio que el resto de P1 (D25/D27).")
    kit.punteo_numerado(sl, [
        f"Los hombres tienen jornada completa con más frecuencia que las mujeres "
        f"({tab_sexo.loc['HOMBRE','Completa']:.1f}% vs {tab_sexo.loc['MUJER','Completa']:.1f}%) "
        f"— las mujeres concentran más jornada parcial.",
        f"El escalafón Regular tiene jornada completa con más frecuencia que el escalafón "
        f"Docente ({tab_escalafon.loc['Regular','Completa']:.1f}% vs "
        f"{tab_escalafon.loc['Docente','Completa']:.1f}%).",
    ])
    return sl


def agregar_todas(prs):
    agregar_intro(prs)
    agregar_donut(prs)
    agregar_sexo_jerarquia(prs)


if __name__ == "__main__":
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(UcenSlideKit.SW_EMU), Emu(UcenSlideKit.SH_EMU)
    agregar_todas(prs)
    prs.save(OUT_PPTX)
    print(f"\n✓ Guardado: {OUT_PPTX}")
