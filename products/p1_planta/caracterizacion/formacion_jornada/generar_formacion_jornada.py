"""
P1 — Caracterización del Cuerpo Académico de Planta
Perfil de la participación en oferta formativa — docentes de Jornada (6 diapositivas).

Pedido de la contraparte (2026-09-26): replicar para el universo Jornada 6 gráficos del
deck de P3 (que se hicieron sobre los 316 "Aptos P3"): modalidades de formación, Venn de
tipos, antigüedad, tipo × antigüedad (+ sexo y edad), jerarquía e intensidad. Todos van en
un solo script para que las 6 diapositivas compartan la misma definición de participante,
de modalidad y de instancia.

Definiciones (mismas de P3 / D31, para que los dos productos se lean igual):
  - Participante ("formado") = docente Jornada con al menos 1 registro en
    analisis.universo_formados_p3 (Taller/Diplomado/Proyecto), sin filtrar a apto_p3.
  - Taller se muestra como "Oferta formativa" (terminología pedida por la contraparte en P3).
  - Modalidad del docente = combinación de tipos que cursó; "Participación Mixta" = más de un tipo.
  - Instancia = actividad distinta (nombre_actividad + periodo_evento); se descarta 1 registro
    duplicado exacto. Cursar la misma actividad en 2 períodos distintos cuenta 2 veces.

FUENTE: analisis.universo_base (Postgres) — universo Jornada (624)
        + analisis.universo_formados_p3 (Postgres) — participación (D31)
SALIDA: P1_formacion_jornada.pptx (6 diapositivas) + 6 PNG *_chart.png
"""
import sys; sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "shared"))
from config import OUTPUTS
from pptx_helpers import UcenSlideKit

import numpy as np
import pandas as pd
import matplotlib.patheffects as pe
from matplotlib.patches import Circle
from sqlalchemy import create_engine, text
from pptx import Presentation
from pptx.util import Emu

HERE = Path(__file__).parent
OUT_PPTX = Path(OUTPUTS) / "pptx" / "P1_formacion_jornada.pptx"
OUT_PPTX.parent.mkdir(parents=True, exist_ok=True)
DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"

TIPO_LABEL = {"TALLER": "Oferta formativa", "DIPLOMADO": "Diplomado", "PROYECTO": "Proyecto"}
# Colores de tipo = los mismos del gráfico tipo × antigüedad de P3
TIPO_COLS = {"Oferta formativa": "#5C9BD6", "Diplomado": "#FFB74D",
             "Proyecto": "#80DEEA", "Participación Mixta": "#CE93D8"}
TIPO_ORD = list(TIPO_COLS)
COL_SI, COL_NO = "#5C9BD6", "#FFB74D"
CAT_JER = ["INSTRUCTOR DOCENTE", "INSTRUCTOR REGULAR", "ASISTENTE DOCENTE", "ASISTENTE REGULAR",
           "ASOCIADO DOCENTE", "ASOCIADO REGULAR", "TITULAR DOCENTE", "TITULAR REGULAR"]
NIVEL_COLORS = ["#AFCBE8", "#7FADD9", "#4E8FC9", "#1F5C99"]
JER_COLS = {c: NIVEL_COLORS[i // 2] for i, c in enumerate(CAT_JER)}
JER_COLS["TITULAR REGULAR"] = "#5C8CB3"
N_MIN = 15
STROKE = [pe.withStroke(linewidth=2, foreground="#0A0F18")]

# ── Datos ───────────────────────────────────────────────────────────────────
engine = create_engine(DB_URL)
base = pd.read_sql(text("""
    SELECT rut_key, sexo, jerarquia, antiguedad_anios, edad_anios
    FROM analisis.universo_base WHERE tipo_contrato_tag='JORNADA'
"""), engine)
reg = pd.read_sql(text("""
    SELECT rut_key, tipo_formacion, nombre_actividad, periodo_evento
    FROM analisis.universo_formados_p3 WHERE tipo_contrato_tag='JORNADA'
"""), engine)
N_JORNADA = len(base)
N_REG_BRUTO = len(reg)
reg = reg.drop_duplicates(["rut_key", "tipo_formacion", "nombre_actividad", "periodo_evento"])
N_DUP = N_REG_BRUTO - len(reg)

tipos_doc = reg.groupby("rut_key")["tipo_formacion"].apply(lambda s: frozenset(s))
por_doc = pd.DataFrame({
    "tipos": tipos_doc,
    "instancias": reg.groupby("rut_key").size(),
})
por_doc["modalidad"] = por_doc["tipos"].apply(
    lambda t: " | ".join(sorted(TIPO_LABEL[x] for x in t)))
por_doc["tipo_simple"] = por_doc["tipos"].apply(
    lambda t: TIPO_LABEL[next(iter(t))] if len(t) == 1 else "Participación Mixta")

base["participo"] = base["rut_key"].isin(por_doc.index)
form = base[base["participo"]].merge(por_doc, left_on="rut_key", right_index=True)
N_FORM = len(form)
N_NO = N_JORNADA - N_FORM

print(f"Universo Jornada: {N_JORNADA}  |  formados: {N_FORM}  |  no: {N_NO}  "
      f"|  registros: {N_REG_BRUTO} ({N_DUP} duplicado exacto descartado)")

# 1) Modalidades
modalidades = form["modalidad"].value_counts()
N_MIXTA = int((form["tipo_simple"] == "Participación Mixta").sum())
print("\nModalidades:"); print(modalidades)

# 2) Venn — conteo por región (T=Taller/Oferta formativa, D=Diplomado, P=Proyecto)
def _region(t, d, p):
    return int(form["tipos"].apply(lambda s: (("TALLER" in s) == t) and (("DIPLOMADO" in s) == d)
                                   and (("PROYECTO" in s) == p)).sum())
VENN = {k: _region(*k) for k in [(1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, 0), (1, 0, 1), (0, 1, 1), (1, 1, 1)]}
N_T = sum(v for k, v in VENN.items() if k[0])
N_D = sum(v for k, v in VENN.items() if k[1])
N_P = sum(v for k, v in VENN.items() if k[2])
print(f"\nVenn: {VENN}  |  T={N_T} D={N_D} P={N_P}")

# 3) Antigüedad de los formados (tramos de 5 años) + tasa de participación por tramo
TRAMOS_ANT = [(0, 5, "0-4"), (5, 10, "5-9"), (10, 15, "10-14"), (15, 20, "15-19"),
              (20, 25, "20-24"), (25, 30, "25-29"), (30, 200, "30+")]
def _tramo_ant(a, tramos=TRAMOS_ANT):
    if pd.isna(a): return None
    for lo, hi, lab in tramos:
        if lo <= a < hi: return lab
base["tramo_ant"] = base["antiguedad_anios"].apply(_tramo_ant)
form["tramo_ant"] = form["antiguedad_anios"].apply(_tramo_ant)
ANT_LABS = [t[2] for t in TRAMOS_ANT]
ant_form = form["tramo_ant"].value_counts().reindex(ANT_LABS, fill_value=0)
N_FORM_ANT = int(ant_form.sum())
MEDIANA_ANT = form["antiguedad_anios"].median()
tasa_ant = (base.dropna(subset=["tramo_ant"]).groupby("tramo_ant")["participo"]
            .agg(["mean", "size"]).reindex(ANT_LABS))
print("\nAntigüedad formados:"); print(ant_form.to_dict(), "mediana", round(MEDIANA_ANT, 1))
print("Tasa de participación por tramo (sobre todos los Jornada del tramo):")
print((tasa_ant["mean"] * 100).round(1).to_dict())

# 4) Tipo × antigüedad / sexo / edad (composición 100% entre formados)
# 15-19 y 20+ fusionados en 15+ (19 + 4 docentes): en el mosaico de ancho ∝ N° eran franjas
# ilegibles, y 20+ con 4 casos no permite leer composición
TRAMOS_ANT4 = [(0, 5, "0-4"), (5, 10, "5-9"), (10, 15, "10-14"), (15, 200, "15+")]
TRAMOS_EDAD = [(0, 35, "<35"), (35, 45, "35-44"), (45, 55, "45-54"), (55, 65, "55-64"), (65, 200, "65+")]
form["tramo_ant4"] = form["antiguedad_anios"].apply(lambda a: _tramo_ant(a, TRAMOS_ANT4))
form["tramo_edad"] = form["edad_anios"].apply(lambda a: _tramo_ant(a, TRAMOS_EDAD))
form["sexo_lab"] = form["sexo"].str.title()

def _comp(col, orden):
    t = pd.crosstab(form[col], form["tipo_simple"]).reindex(index=orden, columns=TIPO_ORD, fill_value=0)
    return t[t.sum(axis=1) > 0]
comp_ant = _comp("tramo_ant4", [t[2] for t in TRAMOS_ANT4])
comp_sexo = _comp("sexo_lab", ["Hombre", "Mujer"])
comp_edad = _comp("tramo_edad", [t[2] for t in TRAMOS_EDAD])
for nom, t in [("antigüedad", comp_ant), ("sexo", comp_sexo), ("edad", comp_edad)]:
    print(f"\nTipo × {nom}:"); print(t)

# 5) Jerarquía de los formados
jer_form = form["jerarquia"].value_counts().reindex(CAT_JER, fill_value=0)
N_FORM_JER = int(jer_form.sum())
n_doc_esc = int(jer_form[[c for c in CAT_JER if "DOCENTE" in c]].sum())
n_reg_esc = int(jer_form[[c for c in CAT_JER if "REGULAR" in c]].sum())
print("\nJerarquía formados:"); print(jer_form.to_dict())

# 6) Intensidad (N° de instancias por docente)
intens = form["instancias"].value_counts().sort_index()
N_3MAS = int((form["instancias"] >= 3).sum())
MEDIANA_INST = form["instancias"].median()
print("\nIntensidad:"); print(intens.to_dict())


# ── Helpers de estilo ───────────────────────────────────────────────────────
def _estilo(ax, grid="x"):
    for sp in ax.spines.values():
        sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.7)
    ax.tick_params(colors="#AAAAAA", labelsize=8)
    getattr(ax, f"{grid}axis").grid(True, color="white", alpha=0.07, linewidth=0.5)
    ax.set_axisbelow(True)


def _slide(prs, kit, chart_path, titulo, subtitulo, punteo, notas, fs=12):
    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.pic_chart(sl, prs, chart_path)
    kit.title(sl, titulo, fs=19)
    kit.subtitulo(sl, subtitulo)
    kit.punteo_numerado(sl, punteo, fs=fs)
    kit.notas(sl, notas)
    return sl


SUB_FORM = (f"Universo: {N_JORNADA} docentes Jornada  ·  {N_FORM} formados "
            f"(al menos una instancia de Oferta formativa, Diplomado o Proyecto)")


# ── 1) Participación + modalidades ──────────────────────────────────────────
def agregar_modalidades(prs):
    kit = UcenSlideKit(out_dir=HERE); kit.ensure_bg()
    fig = kit.new_chart_fig()

    ax0 = fig.add_axes([0.03, 0.10, 0.10, 0.80])
    p_si = 100 * N_FORM / N_JORNADA
    ax0.bar([0], [p_si], width=0.6, color=COL_SI, alpha=0.92, edgecolor="none")
    ax0.bar([0], [100 - p_si], bottom=[p_si], width=0.6, color=COL_NO, alpha=0.92, edgecolor="none")
    ax0.text(0, p_si / 2, f"Cursa\n{N_FORM}\n({p_si:.0f}%)", ha="center", va="center",
             fontsize=8.5, fontweight="bold", color="white", path_effects=STROKE)
    ax0.text(0, p_si + (100 - p_si) / 2, f"No cursa\n{N_NO}\n({100 - p_si:.0f}%)", ha="center",
             va="center", fontsize=8.5, fontweight="bold", color="#3A2A00")
    ax0.set_xlim(-0.5, 0.5); ax0.set_ylim(0, 100); ax0.set_xticks([])
    ax0.set_yticks([0, 25, 50, 75, 100])
    ax0.set_title(f"Jornada (N°={N_JORNADA})", color="#DDDDDD", fontsize=9, pad=6)
    _estilo(ax0, "y")

    ax = fig.add_axes([0.42, 0.10, 0.46, 0.80], facecolor="none")
    y = np.arange(len(modalidades))
    colores = [TIPO_COLS.get(m, TIPO_COLS["Participación Mixta"]) for m in modalidades.index]
    ax.barh(y, modalidades.values, height=0.6, color=colores, alpha=0.92, edgecolor="none", zorder=3)
    for i, n in enumerate(modalidades.values):
        ax.text(n + modalidades.max() * 0.012, i, f"{n}  ({100 * n / N_FORM:.1f}%)", ha="left",
                va="center", fontsize=9, fontweight="bold", color="white", path_effects=STROKE)
    ax.set_yticks(y)
    ax.set_yticklabels(modalidades.index, fontsize=8.5, color="white")
    ax.invert_yaxis()
    ax.set_xlim(0, modalidades.max() * 1.25)
    ax.set_title(f"Modalidad de formación de los formados (N°={N_FORM})", color="#DDDDDD",
                 fontsize=9, pad=6)
    ax.tick_params(axis="y", length=0)
    _estilo(ax)
    chart = kit.save_chart(fig, "modalidades_chart.png")

    top = modalidades.index[0]
    return _slide(prs, kit, chart,
        "Participación en instancias formativas y modalidades — Docentes Jornada",
        SUB_FORM,
        [f"{p_si:.0f}% de los docentes Jornada ({N_FORM} de {N_JORNADA}) cursó al menos una instancia "
         f"formativa; {N_NO} ({100 - p_si:.0f}%) no registra ninguna.",
         f"Entre los formados, {N_FORM - N_MIXTA} ({100 * (N_FORM - N_MIXTA) / N_FORM:.0f}%) participó en "
         f"una sola modalidad —{top} (Taller) es la más común ({modalidades[top]})— y {N_MIXTA} "
         f"({100 * N_MIXTA / N_FORM:.0f}%) tiene Participación Mixta (2 o más tipos)."],
        "Formado = al menos 1 registro de Taller, Diplomado o Proyecto (analisis.universo_formados_p3, "
        "D31). Taller se muestra como 'Oferta formativa', igual que en P3. Modalidad = combinación de "
        "tipos que cursó el docente en todo el período. Coincidencia a tener presente: 418 es también "
        "el N° de docentes con jornada completa (Bloque I); son grupos distintos.")


# ── 2) Venn ─────────────────────────────────────────────────────────────────
def agregar_venn(prs):
    kit = UcenSlideKit(out_dir=HERE); kit.ensure_bg()
    fig = kit.new_chart_fig()
    ax = fig.add_axes([0.25, 0.0, 0.50, 1.0])
    ax.set_xlim(-2.6, 2.6); ax.set_ylim(-2.3, 2.35); ax.set_aspect("equal"); ax.axis("off")

    # Diagrama esquemático (áreas NO proporcionales): posición fija, conteo real en cada región
    centros = {"T": (0, 0.55), "D": (-0.85, -0.75), "P": (0.85, -0.75)}
    r = 1.25
    cols = {"T": TIPO_COLS["Oferta formativa"], "D": TIPO_COLS["Diplomado"], "P": TIPO_COLS["Proyecto"]}
    for k, (cx, cy) in centros.items():
        ax.add_patch(Circle((cx, cy), r, facecolor=cols[k], alpha=0.40, edgecolor="white", linewidth=1.2))
    pos = {(1, 0, 0): (0, 1.15), (0, 1, 0): (-1.45, -1.2), (0, 0, 1): (1.45, -1.2),
           (1, 1, 0): (-0.75, 0.05), (1, 0, 1): (0.75, 0.05), (0, 1, 1): (0, -1.2), (1, 1, 1): (0, -0.35)}
    for k, (x, yy) in pos.items():
        ax.text(x, yy, str(VENN[k]), ha="center", va="center", fontsize=12, fontweight="bold",
                color="white", path_effects=STROKE)
    ax.text(0, 1.95, f"Oferta formativa (Taller) (N°={N_T})", ha="center", fontsize=9.5, fontweight="bold",
            color="white", path_effects=STROKE)
    ax.text(-2.15, -2.15, f"Diplomado\n(N°={N_D})", ha="center", fontsize=9.5, fontweight="bold",
            color="white", path_effects=STROKE)
    ax.text(2.15, -2.15, f"Proyecto\n(N°={N_P})", ha="center", fontsize=9.5, fontweight="bold",
            color="white", path_effects=STROKE)
    chart = kit.save_chart(fig, "venn_chart.png")

    t_solo, d_solo, p_solo = VENN[(1, 0, 0)], VENN[(0, 1, 0)], VENN[(0, 0, 1)]
    return _slide(prs, kit, chart,
        "Tipos de formación (diagrama de Venn) — Docentes Jornada formados",
        f"Formados: {N_FORM}  ·  Oferta formativa: {N_T}  ·  Diplomado: {N_D}  ·  Proyecto: {N_P}  ·  "
        f"Participación Mixta: {N_MIXTA}",
        [f"La Oferta formativa es la modalidad más frecuente ({N_T} docentes, {100 * N_T / N_FORM:.0f}% de "
         f"los formados), seguida por Diplomado ({N_D}) y Proyecto ({N_P}).",
         f"{t_solo} realizaron solo Oferta formativa · {d_solo} solo Diplomado · {p_solo} solo Proyecto. "
         f"Las intersecciones suman {N_MIXTA} docentes con Participación Mixta, {VENN[(1, 1, 1)]} de ellos "
         f"con los 3 tipos."],
        "Diagrama esquemático: el tamaño de los círculos NO es proporcional al N°; el número de cada "
        "región es el conteo real de docentes que cursaron exactamente esa combinación.")


# ── 3) Antigüedad de los formados ───────────────────────────────────────────
def agregar_antiguedad(prs):
    kit = UcenSlideKit(out_dir=HERE); kit.ensure_bg()
    fig = kit.new_chart_fig()
    ax = kit.chart_axes(fig, left=0.08, top=0.10, bottom=0.18)
    x = np.arange(len(ANT_LABS))
    ramp = ["#90CAF9", "#64B5F6", "#42A5F5", "#1E88E5", "#1976D2", "#1565C0", "#0D47A1"]
    ax.bar(x, ant_form.values, width=0.65, color=ramp, alpha=0.92, edgecolor="none", zorder=3)
    for xi, n in zip(x, ant_form.values):
        ax.text(xi, n + ant_form.max() * 0.02, f"{n}\n({100 * n / N_FORM_ANT:.0f}%)", ha="center",
                va="bottom", fontsize=8.5, fontweight="bold", color="white", path_effects=STROKE)
    # Mediana: posición interpolada dentro de su tramo de 5 años
    lo = [t[0] for t in TRAMOS_ANT]
    idx = max(i for i, l in enumerate(lo) if MEDIANA_ANT >= l)
    xm = idx - 0.5 + (MEDIANA_ANT - lo[idx]) / 5
    ax.axvline(xm, color="white", linestyle="--", linewidth=1, alpha=0.7, zorder=4)
    ax.text(xm + 0.08, ant_form.max() * 0.95, f"Mediana ≈ {MEDIANA_ANT:.1f} años", fontsize=8.5,
            style="italic", color="#DDDDDD")
    ax.set_xticks(x); ax.set_xticklabels(ANT_LABS, color="white", fontsize=9.5)
    ax.set_xlabel("Años en la institución", color="#AAAAAA", fontsize=9)
    ax.set_ylim(0, ant_form.max() * 1.30)
    ax.tick_params(axis="x", length=0)
    _estilo(ax, "y")
    chart = kit.save_chart(fig, "antiguedad_formados_chart.png")

    t0 = ANT_LABS[int(np.argmax(ant_form.values))]
    tasa = (tasa_ant["mean"] * 100)
    tasa_ok = tasa[tasa_ant["size"] >= N_MIN]
    return _slide(prs, kit, chart,
        "Antigüedad en la institución de los docentes formados — Docentes Jornada",
        f"Formados Jornada con antigüedad registrada: {N_FORM_ANT} de {N_FORM} ({N_FORM - N_FORM_ANT} sin fecha de ingreso)",
        [f"El tramo {t0} años concentra la mayor cantidad de formados ({ant_form[t0]}, "
         f"{100 * ant_form[t0] / N_FORM_ANT:.0f}%); la mitad de los formados tiene menos de "
         f"{MEDIANA_ANT:.1f} años en la institución.",
         f"Que haya menos formados antiguos refleja en parte que hay menos docentes antiguos: medida "
         f"como tasa, la participación va de {tasa_ok.min():.0f}% a {tasa_ok.max():.0f}% entre los "
         f"tramos con N° suficiente."],
        "Antigüedad = años desde la fecha de ingreso a UCEN (antiguedad_anios). Mediana calculada sobre "
        "los años exactos, ubicada dentro de su tramo por interpolación. Tasa de participación por "
        "tramo = formados / todos los docentes Jornada del tramo; los tramos con 15 o más docentes son: "
        + ", ".join(f"{k}: {v:.0f}%" for k, v in tasa_ok.items()) + ".")


# ── 4) Tipo × antigüedad / sexo / edad ──────────────────────────────────────
def agregar_tipo_por_grupo(prs):
    kit = UcenSlideKit(out_dir=HERE); kit.ensure_bg()
    fig = kit.new_chart_fig()
    paneles = [(comp_ant, "Según antigüedad (años)"), (comp_sexo, "Según sexo"),
               (comp_edad, "Según tramo de edad (años)")]
    # Mosaico (2026-09-26, observación del usuario: con barras de igual ancho, un grupo de
    # 4 docentes se veía igual que uno de 190). Ancho de cada barra ∝ N° del grupo dentro de
    # su panel; grupos con N° < 15 además con textura, mismo criterio que el resto de P1.
    anchos = [0.36, 0.16, 0.36]
    GAP = 0.012
    x0 = 0.05
    for (t, titulo), w in zip(paneles, anchos):
        ax = fig.add_axes([x0, 0.24, w - 0.04, 0.58], facecolor="none")
        x0 += w + 0.02
        n_grupo = t.sum(axis=1).values
        wid = n_grupo / n_grupo.sum() * (1 - GAP * (len(t) - 1))
        left = np.concatenate([[0], np.cumsum(wid + GAP)[:-1]])
        xs = left + wid / 2
        pct = t.div(t.sum(axis=1), axis=0) * 100
        bottom = np.zeros(len(t))
        for tipo in TIPO_ORD:
            v = pct[tipo].values
            bars = ax.bar(xs, v, bottom=bottom, width=wid, color=TIPO_COLS[tipo], alpha=0.92,
                          edgecolor="#0A0F18", linewidth=0.4, label=tipo)
            for bar, n in zip(bars, n_grupo):
                if n < N_MIN:
                    bar.set_hatch("///")
            for xi, wi, vi, b, n in zip(xs, wid, v, bottom, t[tipo].values):
                if vi >= 9 and wi >= 0.06:
                    ax.text(xi, b + vi / 2, str(n), ha="center", va="center", fontsize=7.5,
                            fontweight="bold", color="#0A0F18")
            bottom += v
        # barras angostas: etiqueta un renglón más abajo para no pisar a la vecina
        etiquetas = [("\n\n" if wi < 0.10 else "") + f"{g}\nN°={n}" + (" ⚠" if n < N_MIN else "")
                     for g, n, wi in zip(t.index, n_grupo, wid)]
        ax.set_xticks(xs); ax.set_xticklabels(etiquetas, color="white", fontsize=7)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 100); ax.set_yticks([0, 25, 50, 75, 100])
        ax.set_title(titulo, color="#DDDDDD", fontsize=8.5, pad=12)
        ax.tick_params(axis="x", length=0)
        _estilo(ax, "y")
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 1.0), ncol=4, fontsize=8,
               framealpha=0.22, labelcolor="white", facecolor="#101820", edgecolor="#444")
    chart = kit.save_chart(fig, "tipo_por_grupo_chart.png")

    def _pct(t, tipo):
        ok = t[t.sum(axis=1) >= N_MIN]   # solo grupos con N° suficiente
        return (100 * ok[tipo] / ok.sum(axis=1))
    mix_ant, mix_edad, mix_sexo = (_pct(comp_ant, "Participación Mixta"), _pct(comp_edad, "Participación Mixta"),
                                   _pct(comp_sexo, "Participación Mixta"))
    of = _pct(comp_ant, "Oferta formativa")
    joven = comp_edad.loc[["<35", "35-44"]].sum(); mayor = comp_edad.drop(index=["<35", "35-44"]).sum()
    mix_joven = 100 * joven["Participación Mixta"] / joven.sum()
    mix_mayor = 100 * mayor["Participación Mixta"] / mayor.sum()
    return _slide(prs, kit, chart,
        "Tipo de formación según antigüedad, sexo y edad — Docentes Jornada formados",
        f"Formados: {N_FORM}  ·  composición 100% por grupo  ·  el ancho de cada barra es proporcional "
        f"al N° del grupo",
        [f"La Oferta formativa (sola) es el tipo más frecuente en todos los grupos ({of.min():.0f}% a "
         f"{of.max():.0f}% según antigüedad); el Proyecto como única modalidad es casi inexistente.",
         f"La Participación Mixta se concentra en los docentes nuevos ({mix_ant.iloc[0]:.0f}% con "
         f"{mix_ant.index[0]} años vs {mix_ant.iloc[1]:.0f}% con {mix_ant.index[1]}) y en los menores de 45 "
         f"({mix_joven:.0f}% vs {mix_mayor:.0f}%); por sexo la diferencia es menor "
         f"(Mujer {mix_sexo['Mujer']:.0f}%, Hombre {mix_sexo['Hombre']:.0f}%)."],
        "Tipo por docente: si cursó un solo tipo, ese tipo; si cursó 2 o más, 'Participación Mixta' "
        "(mismo criterio de P3). Tramos de edad de 10 años para evitar grupos muy chicos. Descriptivo, "
        "sin prueba estadística. Formados sin antigüedad/edad/sexo registrados no aparecen en el panel "
        "respectivo.", fs=11)


# ── 5) Jerarquía de los formados ────────────────────────────────────────────
def agregar_jerarquia(prs):
    kit = UcenSlideKit(out_dir=HERE); kit.ensure_bg()
    fig = kit.new_chart_fig()
    ax = kit.chart_axes(fig, left=0.22, bottom=0.08, top=0.04)
    y = np.arange(len(CAT_JER))
    ax.barh(y, jer_form.values, height=0.62, color=[JER_COLS[c] for c in CAT_JER], alpha=0.92,
            edgecolor="none", zorder=3)
    for i, n in enumerate(jer_form.values):
        ax.text(n + jer_form.max() * 0.012, i, f"{n}  ({100 * n / N_FORM_JER:.1f}%)", ha="left",
                va="center", fontsize=9.5, fontweight="bold", color="white", path_effects=STROKE)
    ax.set_yticks(y); ax.set_yticklabels([c.title() for c in CAT_JER], color="white", fontsize=10)
    ax.invert_yaxis()
    ax.set_xlim(0, jer_form.max() * 1.25)
    ax.tick_params(axis="y", length=0)
    _estilo(ax)
    chart = kit.save_chart(fig, "jerarquia_formados_chart.png")

    top2 = jer_form.sort_values(ascending=False).index[:2]
    return _slide(prs, kit, chart,
        "Distribución de los Docentes Formados según Jerarquía Académica",
        f"Formados Jornada con jerarquía válida: {N_FORM_JER} de {N_FORM} ({N_FORM - N_FORM_JER} sin jerarquía)",
        [f"Los formados se concentran en {top2[0].title()} ({jer_form[top2[0]]}) y {top2[1].title()} "
         f"({jer_form[top2[1]]}): los rangos de entrada del escalafón Docente.",
         f"Escalafón Docente: {n_doc_esc} formados ({100 * n_doc_esc / N_FORM_JER:.0f}%) · Escalafón "
         f"Regular: {n_reg_esc} ({100 * n_reg_esc / N_FORM_JER:.0f}%)."],
        "Mismas 8 categorías y colores que el resto de P1 (D25). Es la composición de los formados, no "
        "la tasa de participación: la tasa por jerarquía está en la diapositiva de participación por "
        "facultad y jerarquía, y en el Bloque II.")


# ── 6) Intensidad ───────────────────────────────────────────────────────────
def agregar_intensidad(prs):
    kit = UcenSlideKit(out_dir=HERE); kit.ensure_bg()
    fig = kit.new_chart_fig()
    ax = kit.chart_axes(fig, left=0.07, top=0.10, bottom=0.18)
    x = np.arange(len(intens))
    ax.bar(x, intens.values, width=0.65, color=COL_SI, alpha=0.92, edgecolor="none", zorder=3)
    for xi, n in zip(x, intens.values):
        ax.text(xi, n + intens.max() * 0.02, f"{n}\n({100 * n / N_FORM:.0f}%)", ha="center",
                va="bottom", fontsize=7.5, fontweight="bold", color="white", path_effects=STROKE)
    ax.set_xticks(x); ax.set_xticklabels(intens.index, color="white", fontsize=9)
    ax.set_xlabel("Número de instancias de formación por docente", color="#AAAAAA", fontsize=9)
    ax.set_ylim(0, intens.max() * 1.30)
    ax.tick_params(axis="x", length=0)
    _estilo(ax, "y")
    chart = kit.save_chart(fig, "intensidad_chart.png")

    n1 = int(intens.get(1, 0))
    return _slide(prs, kit, chart,
        "Intensidad de participación en formación — Docentes Jornada",
        f"Formados: {N_FORM}  ·  {len(reg):,} instancias registradas  ·  "
        f"mediana {MEDIANA_INST:.0f} por docente",
        [f"{n1} formados ({100 * n1 / N_FORM:.0f}%) participaron en una sola instancia; {N_3MAS} "
         f"({100 * N_3MAS / N_FORM:.0f}%) participaron en 3 o más.",
         f"Los docentes con 3 o más instancias son el grupo con mayor exposición acumulada: el más "
         f"relevante para evaluar efectos acumulativos de la formación."],
        f"Instancia = actividad distinta (nombre de actividad + período). Se descartó {N_DUP} registro "
        "duplicado exacto; cursar la misma actividad en 2 períodos cuenta 2 veces. Solo se muestran los "
        "valores de N° de instancias que efectivamente ocurren (el eje salta los que no tienen docentes).")


def agregar_todas(prs):
    agregar_modalidades(prs)
    agregar_venn(prs)
    agregar_antiguedad(prs)
    agregar_tipo_por_grupo(prs)
    agregar_jerarquia(prs)
    agregar_intensidad(prs)


if __name__ == "__main__":
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(UcenSlideKit.SW_EMU), Emu(UcenSlideKit.SH_EMU)
    agregar_todas(prs)
    prs.save(OUT_PPTX)
    print(f"\n✓ Guardado: {OUT_PPTX}")
