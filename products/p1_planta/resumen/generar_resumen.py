"""
P1 — Versión resumida del deck (11 láminas, para directivos). D38.

Cada lámina junta varias diapositivas del deck completo alrededor de UN hallazgo: título que
afirma el hallazgo, gráficos chicos (2-3 paneles) y hasta 3 punteos con su cifra. Sin jerga
estadística en pantalla: "difiere" solo si la prueba es significativa con la regla D37 (p
corregido por Holm dentro del bloque < 0.05), decidido con `es_significativa`; los p van en las
notas del orador y en la nota metodológica.

Los datos NO se recalculan: se cargan los mismos módulos del deck completo con
`generar_presentacion.cargar_todo()` y se leen sus variables, así el resumen nunca contradice
al completo.

SALIDA: outputs/pptx/P1_resumen.pptx
"""
import sys; sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.patheffects as pe

HERE = Path(__file__).resolve().parent
P1 = HERE.parent
ROOT = P1.parents[1]
sys.path.insert(0, str(P1)); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "shared"))

from pptx import Presentation
from pptx.util import Emu
from config import OUTPUTS
from pptx_helpers import UcenSlideKit, es_significativa, P_AJUSTADO

import generar_presentacion as gp

OUT_PPTX = Path(OUTPUTS) / "pptx" / "P1_resumen.pptx"
OUT_PPTX.parent.mkdir(parents=True, exist_ok=True)

kit = UcenSlideKit(out_dir=HERE)
STROKE = [pe.withStroke(linewidth=2, foreground="#0A0F18")]
AZUL, AZUL_CLARO, DORADO, GRIS = "#4E8FC9", "#AFCBE8", "#F2D675", "#8A9BB0"
C_H, C_M = "#5C9BD6", "#E88FB0"


# ── Helpers de gráfico compacto ─────────────────────────────────────────────────────────────
def paneles(n, anchos=None, wspace=0.10, izq=None):
    """Figura del tamaño de la caja de gráfico con n ejes lado a lado. izq = margen izquierdo
    (fracción de la figura) que cada panel reserva para sus etiquetas de eje."""
    fig = kit.new_chart_fig()
    anchos = anchos or [1] * n
    izq = izq or [0] * n
    total, l0, util = sum(anchos), 0.02, 0.96 - wspace * (n - 1)
    axes, x = [], l0
    for a, m in zip(anchos, izq):
        w = util * a / total
        axes.append(fig.add_axes([x + m, 0.10, w - m, 0.78], facecolor="none", zorder=5))
        x += w + wspace
    return fig, axes


def estilo(ax, titulo, horizontal=False):
    ax.set_title(titulo, color="white", fontsize=11, fontweight="bold", pad=8)
    for k, sp in ax.spines.items():
        sp.set_visible(k == ("left" if horizontal else "bottom"))
        sp.set_edgecolor("white"); sp.set_alpha(0.3)
    ax.tick_params(colors="white", length=0, labelsize=9)
    (ax.set_xticks if horizontal else ax.set_yticks)([])


def etiqueta(ax, x, y, texto, fontsize=10, **kw):
    ax.text(x, y, texto, color="white", fontsize=fontsize, fontweight="bold",
            path_effects=STROKE, zorder=6, **kw)


def barras_h(ax, labels, valores, fmt, colores, titulo, xmax=None):
    y = np.arange(len(labels))
    ax.barh(y, valores, color=colores, height=0.62, zorder=3)
    xmax = xmax or max(valores) * 1.28
    for yi, v in zip(y, valores):
        etiqueta(ax, v + xmax * 0.015, yi, fmt.format(v), va="center", ha="left")
    ax.set_yticks(y); ax.set_yticklabels(labels, color="white", fontsize=9)
    ax.invert_yaxis(); ax.set_xlim(0, xmax)
    estilo(ax, titulo, horizontal=True)


def barras_v(ax, labels, valores, fmt, colores, titulo, ymax=None, ymin=0):
    x = np.arange(len(labels))
    ax.bar(x, valores, color=colores, width=0.6, zorder=3)
    ymax = ymax or max(valores) * 1.2
    for xi, v in zip(x, valores):
        etiqueta(ax, xi, v + (ymax - ymin) * 0.02, fmt.format(v), ha="center", va="bottom")
    ax.set_xticks(x); ax.set_xticklabels(labels, color="white", fontsize=9)
    ax.set_ylim(ymin, ymax)
    estilo(ax, titulo)


def lamina(prs, titulo, bajada, fig, nombre_png, punteos, notas):
    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.pic_chart(sl, prs, kit.save_chart(fig, nombre_png))
    kit.title(sl, titulo, fs=19)
    kit.subtitulo(sl, bajada)
    kit.punteo_numerado(sl, punteos, fs=13)
    kit.notas(sl, notas)
    return sl


def lamina_texto(prs, titulo, bajada, filas, notas, fs=11):
    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.title(sl, titulo, fs=19)
    kit.subtitulo(sl, bajada)
    kit.franjas(sl, filas, fs=fs, col_split=0.39)
    kit.notas(sl, notas)
    return sl


def p_txt(clave):
    """Para notas del orador: 'p corregido = 0.0114 (significativa)'."""
    pa = P_AJUSTADO[clave]
    return f"p corregido = {'<0.0001' if pa < 0.0001 else f'{pa:.4f}'} ({'significativa' if pa < 0.05 else 'no significativa'})"


def difiere(clave, si, no):
    """Texto según el veredicto D37. 'Revisar' marca la rama que contradiría el resumen: si sale,
    el hallazgo cambió y hay que reescribir la lámina."""
    assert clave in P_AJUSTADO, f"Clave de prueba inexistente: {clave}"
    txt = si if es_significativa(1.0, clave) else no
    assert txt != "Revisar", f"El veredicto de '{clave}' cambió: reescribir el punteo"
    return txt


# ── Datos (mismos módulos que el deck completo) ─────────────────────────────────────────────
gp.cargar_todo()
M = gp.MODULOS
kit.ensure_bg()

# Bloque I
es, ga, fa = M["edad_sexo"], M["grado_academico_sexo"], M["funcion_academica"]
ej, aj = M["edad_jerarquia"], M["antiguedad_jerarquia"]
N_JORNADA = int(es.N_TOTAL)
# Bloque II
fj = M["formacion_jornada"]
ps, pj, pf, pe_ = (M["participacion_formacion_sexo"], M["participacion_formacion_jerarquia"],
                   M["participacion_facultad_jerarquia"], M["participacion_formacion_edad"])
# Bloque III
eds, edj, edf = M["edd_sexo"], M["edd_jerarquia"], M["edd_facultad"]
# Bloque IV
ar, ars, arj, ara = (M["aprobacion_reprobacion"], M["aprobacion_reprobacion_sexo"],
                     M["aprobacion_reprobacion_jerarquia"], M["aprobacion_reprobacion_antiguedad_4tramos"])
sd = M["sexo_dificultad"]

# Cifras derivadas
PCT_FORM = 100 * fj.N_FORM / fj.N_JORNADA
PCT_OF = 100 * fj.N_T / fj.N_FORM
PCT_3MAS = 100 * fj.N_3MAS / fj.N_FORM
tasa_ant_ok = fj.tasa_ant[fj.tasa_ant["size"] >= 15]["mean"] * 100
part_h, part_m = ps.tab.loc["HOMBRE", "tasa"], ps.tab.loc["MUJER", "tasa"]
part_doc, part_reg = pj.docente_g.mean() * 100, pj.regular_g.mean() * 100
VRIIP = "VR Investigación y Postgrado"
vr_si, vr_resto, _ = pf.RES_FAC[VRIIP]
edd_lim = eds.escala["limpia"]
rec = eds.edd[eds.edd["anio"] >= 2024]; ant = eds.edd[eds.edd["anio"] < 2024]
PCT_BAJO_REC = 100 * (rec["edd_total"] < 0.55).mean()
PCT_BAJO_ANT = 100 * (ant["edd_total"] < 0.55).mean()
apr_m, apr_h = ars.mujer.mean(), ars.hombre.mean()
apr_doc, apr_reg = arj.grupo_docente.mean(), arj.grupo_regular.mean()
apr_ant = {k: v.mean() for k, v in ara.series.items()}
muj_grupo = sd.por_docente.groupby("grupo_predominante")["es_mujer"].mean().reindex(["Baja", "Media", "Alta"]) * 100
muj_baja, muj_resto = sd.grupo_baja.mean() * 100, sd.grupo_resto.mean() * 100
dif = {g: (ars.DIF[g]["m"].mean(), ars.DIF[g]["h"].mean()) for g in ("Baja", "Media", "Alta")}

K_PART_SEXO = "Participación: Mujer vs Hombre"
K_PART_ESC = "Participación: escalafón Regular vs Docente"
K_PART_VR = f"Participación: {VRIIP} vs resto"
K_PART_EDAD = "Edad: participó vs no participó"
K_EDD_SEXO = "EDD limpia: Mujer vs Hombre"
K_EDD_ESC = "EDD limpia: escalafón Regular vs Docente"
K_EDD_FAC = [k for k in P_AJUSTADO if k.startswith("EDD limpia:") and k.endswith("vs resto")]
K_APR_SEXO = "% aprobación por docente: Mujer vs Hombre"
K_APR_ESC = "% aprobación por docente: escalafón Docente vs Regular"
K_APR_ANT = "% aprobación por docente según tramo de antigüedad (4 tramos)"
K_SEXO_DIF = "% mujeres: grupo predominante Baja vs Media+Alta"
K_DIF_GRUPO = {"Baja": "% aprobación Mujer vs Hombre, dentro de baja aprobación",
               "Media": "% aprobación Mujer vs Hombre, dentro de aprobación media",
               "Alta": "% aprobación Mujer vs Hombre, dentro de aprobación alta"}
otras_fac_sig = [k for k in P_AJUSTADO if k.startswith("Participación:") and k.endswith("vs resto")
                 and k != K_PART_VR and es_significativa(1.0, k)]
assert not otras_fac_sig, f"Revisar punteo de facultad: {otras_fac_sig}"
assert not any(es_significativa(1.0, k) for k in K_EDD_FAC + [K_EDD_SEXO, K_EDD_ESC]), "Revisar lámina EDD"
assert not any(es_significativa(1.0, k) for k in K_DIF_GRUPO.values()), "Revisar lámina 9"


# ── Láminas ─────────────────────────────────────────────────────────────────────────────────
prs = Presentation()
prs.slide_width, prs.slide_height = Emu(UcenSlideKit.SW_EMU), Emu(UcenSlideKit.SH_EMU)

# 1. Portada
sl = kit.new_slide(prs)
kit.portada(sl, titulo="Resultados del Perfeccionamiento Docente", subtitulo1="Resumen ejecutivo",
            footer_lines=["Universidad Central",
                          "Producto 1: Caracterización Cuerpo Académico Jornada",
                          "Septiembre 2026"])

# 2. Cinco hallazgos
lamina_texto(prs, "Cinco hallazgos",
    f"Universo: {N_JORNADA} docentes Jornada · 2022-2025 · detalle y pruebas en el deck completo",
    [("1. Perfil",
      [f"Cuerpo académico posgraduado ({ga.pct_postgrado:.0f}% Magíster o Doctor) y centrado en la "
       f"docencia ({100 * fa.conteo['Docencia'] / fa.N:.0f}% de los cargos). A mayor jerarquía, más "
       "edad y más años en UCEN."]),
     ("2. Formación",
      [f"2 de cada 3 docentes se formaron ({fj.N_FORM} de {fj.N_JORNADA}), casi todos vía Oferta "
       f"formativa ({PCT_OF:.0f}%). La mitad acumula 3 o más instancias."]),
     ("3. Quién se forma",
      [f"Participan más las mujeres ({part_m:.0f}% vs {part_h:.0f}%) y el escalafón Docente "
       f"({part_doc:.0f}% vs {part_reg:.0f}% Regular). VR Investigación queda muy abajo "
       f"({vr_si:.0f}% vs {vr_resto:.0f}%)."]),
     ("4. EDD",
      [f"Los datos 2024-2025 traen notas dañadas ({PCT_BAJO_REC:.0f}% bajo 0.55). Sin ellas, la EDD "
       f"es alta y estable ({edd_lim.min():.2f}-{edd_lim.max():.2f}) y no difiere por sexo, "
       "escalafón ni facultad."]),
     ("5. Aprobación",
      [f"Aprueba el {ar.PCT_APROB:.1f}%. Las docentes mujeres aprueban más ({apr_m:.0f}% vs "
       f"{apr_h:.0f}%), pero la brecha se explica por la dificultad de los cursos que dicta cada uno."])],
    "Síntesis del deck completo (39 diapositivas). Cada hallazgo se desarrolla en las láminas "
    "siguientes, en el mismo orden.", fs=13)

# 3. Perfil
fig, (a1, a2, a3) = paneles(3, [1.0, 0.9, 1.4], wspace=0.07, izq=[0.04, 0, 0.17])
tab = es.tab
y = np.arange(len(tab))
a1.barh(y, -tab["HOMBRE"], color=C_H, height=0.7, zorder=3, label="Hombre")
a1.barh(y, tab["MUJER"], color=C_M, height=0.7, zorder=3, label="Mujer")
a1.set_yticks(y); a1.set_yticklabels(tab.index, color="white", fontsize=8)
a1.axvline(0, color="white", alpha=0.4, lw=0.8)
a1.legend(loc="lower right", fontsize=8, frameon=False, labelcolor="white")
estilo(a1, "Edad y sexo (N°)", horizontal=True)
niveles = ["Doctor", "Magíster o Master", "Profesional/Técnico"]
g = ga.tab.loc[niveles]
pct_g = 100 * g / g.sum()
x = np.arange(len(niveles))
for i, (sx, col) in enumerate([("HOMBRE", C_H), ("MUJER", C_M)]):
    a2.bar(x + (i - 0.5) * 0.36, pct_g[sx], width=0.34, color=col, zorder=3)
    for xi, v in zip(x, pct_g[sx]):
        etiqueta(a2, xi + (i - 0.5) * 0.36, v + 1.5, f"{v:.0f}%", ha="center", va="bottom", fontsize=8)
a2.set_xticks(x); a2.set_xticklabels(["Doctor", "Magíster", "Profesional"], color="white", fontsize=9)
a2.set_ylim(0, 75); estilo(a2, "Grado académico (% por sexo)")
c = fa.conteo
barras_h(a3, [l.replace(" e Innovación", "") for l in c.index], (100 * c / fa.N).values, "{:.0f}%",
         [AZUL if l == "Docencia" else AZUL_CLARO for l in c.index], "Función del cargo (%)")
lamina(prs, "Cuerpo académico posgraduado y centrado en la docencia",
       f"Docentes Jornada con dato: edad y sexo {es.N_CON_DATOS} · grado {ga.N_CON_DATOS} · cargo {fa.N} de {N_JORNADA}",
       fig, "r03_perfil.png",
       [f"{ga.pct_postgrado:.0f}% tiene Magíster o Doctorado; entre los hombres el doctorado es más "
        f"frecuente ({ga.pct_doc_h:.0f}% vs {ga.pct_doc_m:.0f}% de las mujeres).",
        f"{100 * c['Docencia'] / fa.N:.0f}% ocupa un cargo de docencia; la gestión (Docente/Gestor + "
        f"Gestión Académica) suma el {fa.pct_gestion:.0f}%.",
        f"El tramo 40-44 años es el más numeroso ({int(es.n_top)} docentes, "
        f"{100 * es.n_top / es.N_CON_DATOS:.0f}%), con más mujeres que hombres."],
       "Resume las diapositivas 4, 8 y 9 del deck completo. Carga académica: columna CLASIFICACION "
       "del archivo de dotación, con Vicedecanos y autoridades superiores en Gestión Académica (D37).")

# 4. Jerarquía
NIV = ["INSTRUCTOR", "ASISTENTE", "ASOCIADO", "TITULAR"]
fig, (a1, a2) = paneles(2, wspace=0.10)
for ax, tb, col, tit, fmt in [(a1, ej.tab, "edad_prom", "Edad promedio (años)", "{:.0f}"),
                              (a2, aj.tab, "tray_prom", "Años en UCEN (promedio)", "{:.0f}")]:
    x = np.arange(len(NIV))
    for i, (esc, color) in enumerate([("DOCENTE", AZUL), ("REGULAR", DORADO)]):
        vals = []
        for n in NIV:
            fila = tb.loc[f"{n} {esc}"]
            vals.append(fila[col] if fila["n"] >= 15 else np.nan)
        xs = x + (i - 0.5) * 0.38
        ax.bar(xs, vals, width=0.36, color=color, zorder=3, label=esc.capitalize())
        for xi, v in zip(xs, vals):
            if not np.isnan(v):
                etiqueta(ax, xi, v + 0.8, fmt.format(v), ha="center", va="bottom", fontsize=9)
    ax.set_xticks(x); ax.set_xticklabels([n.capitalize() for n in NIV], color="white", fontsize=9)
    ax.set_ylim(0, max(tb[col]) * 1.2)
    estilo(ax, tit)
a1.legend(loc="upper left", fontsize=8.5, frameon=False, labelcolor="white")
tit_d, tit_r = ej.tab.loc["TITULAR DOCENTE", "edad_prom"], ej.tab.loc["INSTRUCTOR DOCENTE", "edad_prom"]
lamina(prs, "A mayor jerarquía, más edad y más años en UCEN",
       f"Docentes Jornada con jerarquía y edad: {ej.N_CON_DATOS} de {N_JORNADA} · años en UCEN desde la "
       "fecha de ingreso (sin carrera previa) · Instructor Regular (N°=5) no se grafica",
       fig, "r04_jerarquia.png",
       [f"En el escalafón Docente la edad sube de {tit_r:.0f} años (Instructor) a {tit_d:.0f} (Titular).",
        f"Los años en UCEN siguen el mismo orden: de {aj.tab.loc['INSTRUCTOR DOCENTE', 'tray_prom']:.0f} "
        f"(Instructor) a {aj.tab.loc['TITULAR DOCENTE', 'tray_prom']:.0f} (Titular Docente)."],
       "Resume las diapositivas 5 y 6 del deck completo. Categorías con menos de 15 docentes no se "
       "grafican.")

# 5. Formación
fig, (a1, a2) = paneles(2, [1.3, 1], wspace=0.08, izq=[0.20, 0])
mod = fj.modalidades
otras = mod.drop(["Oferta formativa", "Diplomado | Oferta formativa", "Diplomado"]).sum()
barras_h(a1, ["Solo Oferta formativa", "Oferta formativa + Diplomado", "Solo Diplomado", "Otras combinaciones"],
         [mod["Oferta formativa"], mod["Diplomado | Oferta formativa"], mod["Diplomado"], otras],
         "{:.0f}", [AZUL, AZUL, AZUL_CLARO, AZUL_CLARO], "Cómo se formaron (N° docentes)")
it = fj.intens
cats = ["1", "2", "3", "4", "5+"]
vals = [it.get(1, 0), it.get(2, 0), it.get(3, 0), it.get(4, 0), it[it.index >= 5].sum()]
barras_v(a2, cats, vals, "{:.0f}", [AZUL_CLARO, AZUL_CLARO, AZUL, AZUL, AZUL],
         "Instancias por docente (N° docentes)")
lamina(prs, "2 de cada 3 docentes se formaron, casi todos vía Oferta formativa",
       f"Universo: {fj.N_JORNADA} docentes Jornada · formados = al menos 1 instancia 2022-2025",
       fig, "r05_formacion.png",
       [f"{fj.N_FORM} de {fj.N_JORNADA} docentes ({PCT_FORM:.0f}%) cursó al menos una instancia formativa.",
        f"{fj.N_T} ({PCT_OF:.0f}%) pasó por Oferta formativa (Taller); {fj.N_D} por Diplomado y "
        f"{fj.N_P} por Proyecto.",
        f"La mitad ({fj.N_3MAS}, {PCT_3MAS:.0f}%) acumula 3 o más instancias."],
       "Resume las diapositivas 13, 14 y 15 del deck completo. Instancia = actividad distinta "
       "(nombre + período).")

# 6. Quién se forma
fig, (a1, a2, a3) = paneles(3, [0.6, 0.6, 1.6], wspace=0.07, izq=[0, 0, 0.19])
barras_v(a1, ["Mujer", "Hombre"], [part_m, part_h], "{:.0f}%", [C_M, C_H], "Sexo", ymax=100)
barras_v(a2, ["Docente", "Regular"], [part_doc, part_reg], "{:.0f}%", [AZUL, DORADO], "Escalafón", ymax=100)
fo = pf.fac_ok.sort_values("pct_si", ascending=False)
barras_h(a3, [f.replace("VR Investigación y Postgrado", "VR Investigación") for f in fo.index],
         fo["pct_si"].values, "{:.0f}%", [DORADO if f == VRIIP else AZUL for f in fo.index],
         "Unidad", xmax=100)
lamina(prs, "Se forman más las mujeres y el escalafón Docente; menos VR Investigación",
       "% de docentes Jornada que cursó al menos una instancia formativa 2022-2025",
       fig, "r06_quien.png",
       [difiere(K_PART_SEXO, f"Mujeres {part_m:.0f}% vs hombres {part_h:.0f}%; escalafón Docente "
                f"{part_doc:.0f}% vs Regular {part_reg:.0f}%.", "Revisar"),
        difiere(K_PART_VR, f"VR Investigación ({vr_si:.0f}%) es la única unidad que difiere del resto "
                f"({vr_resto:.0f}%); las facultades no difieren entre sí.", "Revisar"),
        difiere(K_PART_EDAD, "Revisar", "Por edad no difiere; por antigüedad la tasa es pareja "
                f"({tasa_ant_ok.min():.0f}%-{tasa_ant_ok.max():.0f}%).")],
       "Resume las diapositivas 16 a 21 del deck completo. Pruebas: sexo " + p_txt(K_PART_SEXO) +
       "; escalafón " + p_txt(K_PART_ESC) + "; VR Investigación vs resto " + p_txt(K_PART_VR) +
       "; edad " + p_txt(K_PART_EDAD) + ". Antigüedad: sin prueba, tasa por tramo con N°≥15.")

# 7. EDD
fig, (a1, a2) = paneles(2, [1, 1.2], wspace=0.06, izq=[0, 0.16])
anios = [str(a) for a in eds.escala.index]
x = np.arange(len(anios))
a1.bar(x - 0.19, eds.escala["original"], width=0.36, color=GRIS, zorder=3, label="Original")
a1.bar(x + 0.19, eds.escala["limpia"], width=0.36, color=AZUL, zorder=3, label="Sin notas dañadas")
for xi, (o, l, s) in zip(x, eds.escala[["original", "limpia", "pct_sospechosa"]].values):
    etiqueta(a1, xi - 0.19, o + 0.015, f"{o:.2f}", ha="center", va="bottom", fontsize=8)
    etiqueta(a1, xi + 0.19, l + 0.015, f"{l:.2f}", ha="center", va="bottom", fontsize=8)
    if s > 0:
        a1.text(xi, 0.05, f"{s:.0f}%\ndañadas", ha="center", color=DORADO, fontsize=8, fontweight="bold",
                path_effects=STROKE, zorder=6)
a1.set_xticks(x); a1.set_xticklabels(anios, color="white", fontsize=9); a1.set_ylim(0, 1.12)
a1.legend(loc="upper left", fontsize=8, frameon=False, labelcolor="white", ncol=2)
estilo(a1, "Nota EDD promedio por año")
fac_edd = edf.res.sort_values("media", ascending=False)
et = (["Mujer", "Hombre", "Docente", "Regular"] +
      [f.replace("VR Investigación y Postgrado", "VR Investigación") for f in fac_edd.index])
va = ([eds.mujer.mean(), eds.hombre.mean(), edj.docente_g.mean(), edj.regular_g.mean()] +
      list(fac_edd["media"]))
barras_h(a2, et, va, "{:.2f}", [C_M, C_H, AZUL, DORADO] + [AZUL_CLARO] * len(fac_edd),
         "Nota EDD sin notas dañadas", xmax=1.12)
lamina(prs, "La EDD 2024-2025 trae notas dañadas; sin ellas, es alta y pareja",
       f"Docentes Jornada evaluados: {eds.N_EDD_DOC} · con nota válida: {len(eds.por_docente)} · 2022-2025",
       fig, "r07_edd.png",
       [f"En 2024-2025 el {PCT_BAJO_REC:.0f}% de las notas está bajo 0.55 (en 2022-2023, el "
        f"{PCT_BAJO_ANT:.0f}%): ceros que son datos vacíos y notas contadas a la mitad.",
        f"Sin esas notas la EDD es estable los 4 años ({edd_lim.min():.2f}-{edd_lim.max():.2f}).",
        "No difiere por sexo, escalafón ni facultad."],
       "Resume las diapositivas 23 a 26 del deck completo (D37). Nota dañada = 0, o menor a 0.55 en "
       "2024-2025. Pruebas: sexo " + p_txt(K_EDD_SEXO) + "; escalafón " + p_txt(K_EDD_ESC) +
       "; facultades vs resto: todas no significativas.")

# 8. Aprobación
fig, (a1, a2, a3) = paneles(3, [0.7, 0.7, 1.2], wspace=0.13)
barras_v(a1, ["Mujer", "Hombre"], [apr_m, apr_h], "{:.1f}%", [C_M, C_H], "Sexo", ymax=100, ymin=60)
barras_v(a2, ["Docente", "Regular"], [apr_doc, apr_reg], "{:.1f}%", [AZUL, DORADO], "Escalafón",
         ymax=100, ymin=60)
barras_v(a3, list(apr_ant), list(apr_ant.values()), "{:.0f}%", [AZUL_CLARO] * 4,
         "Años en UCEN", ymax=100, ymin=60)
lamina(prs, f"Aprueba el {ar.PCT_APROB:.1f}%: más con docentes mujeres y del escalafón Docente",
       f"% de aprobación promedio por docente · {ar.N_DOCENTES} docentes Jornada con calificaciones · "
       f"{ar.N_EVALUABLE:,.0f} calificaciones 2023-2025 · eje desde 60%",
       fig, "r08_aprobacion.png",
       [difiere(K_APR_SEXO, f"Docentes mujeres {apr_m:.1f}% vs hombres {apr_h:.1f}%.", "Revisar"),
        difiere(K_APR_ESC, f"Escalafón Docente {apr_doc:.1f}% vs Regular {apr_reg:.1f}%.", "Revisar"),
        difiere(K_APR_ANT, "Revisar", "Por años en UCEN no difiere.")],
       "Resume las diapositivas 28, 29, 31 y 32 del deck completo. Pruebas: sexo " + p_txt(K_APR_SEXO) +
       "; escalafón " + p_txt(K_APR_ESC) + "; antigüedad (ANOVA) " + p_txt(K_APR_ANT) + ".")

# 9. Dificultad
fig, (a1, a2) = paneles(2, [0.8, 1.2], wspace=0.14)
GR = ["Baja", "Media", "Alta"]
ET = ["Baja\naprobación", "Media", "Alta"]
barras_v(a1, ET, muj_grupo.values, "{:.0f}%", [DORADO, AZUL_CLARO, AZUL_CLARO],
         "% de docentes mujeres", ymax=80)
x = np.arange(3)
for i, (k, col, lab) in enumerate([(0, C_M, "Mujer"), (1, C_H, "Hombre")]):
    vals = [dif[g][k] for g in GR]
    xs = x + (i - 0.5) * 0.38
    a2.bar(xs, vals, width=0.36, color=col, zorder=3, label=lab)
    for xi, v in zip(xs, vals):
        etiqueta(a2, xi, v + 0.6, f"{v:.0f}%", ha="center", va="bottom", fontsize=9)
a2.set_xticks(x); a2.set_xticklabels(ET, color="white", fontsize=9); a2.set_ylim(60, 106)
a2.legend(loc="upper left", fontsize=8.5, frameon=False, labelcolor="white", ncol=2)
estilo(a2, "% de aprobación dentro de cada grupo")
lamina(prs, "La brecha de aprobación por sexo se explica por la dificultad del curso",
       "Grupos = terciles del % de aprobación histórico de cada asignatura · cada docente en su "
       "grupo predominante",
       fig, "r09_dificultad.png",
       [difiere(K_SEXO_DIF, f"En los cursos de baja aprobación solo el {muj_baja:.0f}% de los docentes "
                f"son mujeres; en el resto, el {muj_resto:.0f}%.", "Revisar"),
        "Dentro de cada grupo de dificultad, mujeres y hombres aprueban lo mismo "
        f"(baja: {dif['Baja'][0]:.0f}% vs {dif['Baja'][1]:.0f}%).",
        f"La brecha global ({apr_m:.0f}% vs {apr_h:.0f}%) refleja en qué cursos enseña cada grupo."],
       "Resume las diapositivas 30, 34 y 37 del deck completo (D27). Pruebas: % mujeres Baja vs "
       "Media+Alta " + p_txt(K_SEXO_DIF) + "; M vs H dentro de cada grupo: " +
       "; ".join(f"{g} {p_txt(K_DIF_GRUPO[g])}" for g in GR) + ".")

# 10. Implicancias
lamina_texto(prs, "Implicancias",
    "Propuestas que se desprenden de los hallazgos; no son resultados medidos",
    [("Formación",
      [f"El escalafón Regular ({part_reg:.0f}%) y VR Investigación ({vr_si:.0f}%) participan mucho menos.",
       "Focalizar la convocatoria y la oferta formativa en estos dos grupos."]),
     ("EDD",
      [f"El {PCT_BAJO_REC:.0f}% de las notas 2024-2025 está bajo 0.55, con ceros y notas a la mitad.",
       "Revisar la base con quien la administra antes de usar la EDD para decisiones."]),
     ("Aprobación",
      ["La brecha por sexo desaparece al comparar cursos de dificultad similar.",
       "Comparar tasas de aprobación entre docentes solo dentro de un mismo grupo de dificultad."]),
     ("Grado académico",
      [f"Doctorado: {ga.pct_doc_h:.0f}% de los hombres vs {ga.pct_doc_m:.0f}% de las mujeres.",
       "Posible línea de seguimiento: cómo incide el doctorado en los ascensos de jerarquía."])],
    "Cada implicancia se ata a un hallazgo de las láminas 3 a 9. Son propuestas para discusión, "
    "no conclusiones de una prueba.", fs=12)

# 11. Nota metodológica
lamina_texto(prs, "Nota metodológica",
    "Detalle completo, todas las pruebas y sus decisiones: deck completo y DECISIONES_METODOLOGICAS",
    [("Universo", [f"{N_JORNADA} docentes con contrato Jornada. Cada gráfico usa los docentes con "
                   "el dato disponible; el N° va en la bajada de cada lámina."]),
     ("Período", ["Formación y EDD 2022-2025; aprobación de alumnos 2023-2025."]),
     ("Diferencias", ["Se dice que un grupo \"difiere\" solo si la diferencia es estadísticamente "
                      "significativa: p corregido por comparaciones múltiples (Holm, dentro de cada "
                      "bloque) menor a 0.05. Cada docente aporta un solo valor."]),
     ("EDD", ["Se excluyen las notas iguales a 0 y las menores a 0.55 en 2024-2025 (datos dañados). "
              f"Quedan {len(eds.por_docente)} de {eds.N_EDD_DOC} docentes evaluados con nota válida."]),
     ("Dificultad", ["Asignaturas agrupadas en terciles según su % de aprobación histórico "
                     "(baja, media, alta)."])],
    "27 pruebas en el anexo del deck completo; 6 significativas.", fs=12)

prs.save(OUT_PPTX)
print(f"\n✓ Guardado: {OUT_PPTX}  ({len(prs.slides)} láminas)")

# Comentarios de decisión (criterio de síntesis) — mismo mecanismo que el deck completo
COMENTARIOS_RESUMEN = {
    "Cinco hallazgos": [
        "Versión resumida (D38): la respuesta va primero. Cada hallazgo se respalda en las láminas "
        "siguientes, en el mismo orden, y cada lámina junta varias diapositivas del deck completo "
        "(se indican en las notas del orador).",
        "Audiencia: directivos. Los valores p no van en pantalla; 'difiere' se usa solo cuando la "
        "prueba es significativa con la regla del deck (p corregido por Holm < 0.05).",
    ],
    "La EDD 2024-2025": [
        "El problema de calidad de datos se presenta como hallazgo, no como nota al pie: cambia la "
        "lectura de la EDD (con las notas dañadas aparecían diferencias por sexo y escalafón que no "
        "existen).",
    ],
    "La brecha de aprobación por sexo": [
        "Esta lámina matiza la anterior: la diferencia por sexo es real en el total, pero no dentro de "
        "cursos de dificultad similar. Para el escalafón no se hizo este control; por eso no se afirma "
        "lo mismo.",
    ],
    "Implicancias": [
        "Redactadas como propuestas atadas a un hallazgo. La del grado académico es una posible línea "
        "de seguimiento, no un resultado (mismo criterio que 'posible implicancia' en el deck completo).",
    ],
}
print("\n── Comentarios de decisiones ─────────────────────────────────")
try:
    import comentarios_decisiones
    comentarios_decisiones.aplicar(OUT_PPTX, COMENTARIOS_RESUMEN)
except Exception as e:
    print(f"  ⚠ No se agregaron comentarios ({type(e).__name__}: {e})")
