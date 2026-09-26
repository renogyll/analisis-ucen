"""
P1 — Diapositiva común para antiguedad_dificultad/, edad_dificultad/ y sexo_dificultad/
(revisión 2026-09-26, obs. 3 y 21).

Antes, el descriptivo usaba instancias (un docente contaba en varios grupos y el promedio se
ponderaba por volumen) y comparaba Baja vs Alta, mientras la prueba usaba 1 valor por docente
y comparaba Baja vs Media+Alta: dos números distintos para "la misma" comparación. Ahora
descriptivo y prueba usan la misma unidad: 1 valor por docente, asignado a su grupo de
dificultad predominante (D27). Se muestran los 3 grupos con su intervalo de confianza y, en la
misma diapositiva, la prueba t de Welch Baja vs Media+Alta.
"""
import numpy as np
import matplotlib.patheffects as pe
from scipy import stats

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared"))
from pptx_helpers import lectura_p

GRUPOS_ORD = ["Baja", "Media", "Alta"]
ETIQUETAS = {"Baja": "Baja aprobación", "Media": "Aprobación media", "Alta": "Aprobación alta"}
COLORS = ["#AFCBE8", "#4E8FC9", "#1F5C99"]


def prueba_baja_vs_resto(por_docente, col):
    baja = por_docente.loc[por_docente["grupo_predominante"] == "Baja", col]
    resto = por_docente.loc[por_docente["grupo_predominante"] != "Baja", col]
    t, p = stats.ttest_ind(baja, resto, equal_var=False)
    return baja, resto, t, p


def slide_por_grupo(prs, kit, por_docente, col, *, escala=1.0, fmt="{:.1f}", unidad="",
                    ylabel, titulo, subtitulo, frase_valor, notas, chart_name):
    """por_docente: 1 fila por docente con `grupo_predominante` y la columna `col`.
    escala: multiplicador para mostrar (100 para proporciones → %).
    frase_valor(baja_media, resto_media) -> str: primer punteo, en palabras."""
    stroke = [pe.withStroke(linewidth=2, foreground="#0A0F18")]
    series = [por_docente.loc[por_docente["grupo_predominante"] == g, col] * escala for g in GRUPOS_ORD]
    medias = [s.mean() for s in series]
    cis = [stats.t.ppf(0.975, len(s) - 1) * s.std(ddof=1) / np.sqrt(len(s)) for s in series]
    baja, resto, t, p = prueba_baja_vs_resto(por_docente, col)

    fig = kit.new_chart_fig()
    ax = kit.chart_axes(fig, top=0.14)
    x = np.arange(3)
    ax.bar(x, medias, width=0.5, color=COLORS, alpha=0.92, edgecolor="none",
           yerr=cis, capsize=6, error_kw={"ecolor": "#DDDDDD", "linewidth": 1.3})
    ymax = max(m + c for m, c in zip(medias, cis)) * 1.3
    for xi, m, ci, s in zip(x, medias, cis, series):
        ax.text(xi, m + ci + ymax * 0.02, fmt.format(m) + unidad, ha="center", va="bottom",
                fontsize=13, fontweight="bold", color="white", path_effects=stroke, zorder=6)
        ax.text(xi, ymax * 0.02, f"N°={len(s)} docentes", ha="center", va="bottom",
                fontsize=8.5, color="white")
    sig = "significativa" if p < 0.05 else "no significativa"
    ax.text(0.5, 0.99, f"Prueba t de Welch, Baja vs Media+Alta:  t = {t:.2f}   ·   p = {p:.4f}   ·   "
            f"diferencia {sig} al 5%", transform=ax.transAxes, ha="center", va="top",
            fontsize=9.5, color="#F2D675", fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels([ETIQUETAS[g] for g in GRUPOS_ORD], fontsize=11.5, color="white")
    ax.set_xlabel("Grupo de dificultad predominante del docente", color="#AAAAAA", fontsize=9)
    ax.set_ylabel(ylabel, color="#AAAAAA", fontsize=9)
    ax.set_ylim(0, ymax)
    ax.tick_params(axis="x", length=0, pad=6); ax.tick_params(axis="y", colors="#AAAAAA", labelsize=8.5)
    for sp in ax.spines.values():
        sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.7)
    ax.yaxis.grid(True, color="white", alpha=0.07, linewidth=0.5); ax.set_axisbelow(True)
    chart_path = kit.save_chart(fig, chart_name)

    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.pic_chart(sl, prs, chart_path)
    kit.title(sl, titulo)
    kit.subtitulo(sl, subtitulo)
    kit.punteo_numerado(sl, [frase_valor(baja.mean() * escala, resto.mean() * escala), lectura_p(p)], fs=12)
    kit.notas(sl, notas + " Grupo predominante = el grupo de dificultad (Baja/Media/Alta) donde el "
                  "docente tiene más instancias docente×asignatura×período (D27); cada docente aporta "
                  "un solo valor. Barras = intervalo de confianza 95%.")
    return sl
