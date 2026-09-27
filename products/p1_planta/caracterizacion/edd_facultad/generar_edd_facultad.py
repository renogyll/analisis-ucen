"""
P1 — Caracterización del Cuerpo Académico de Planta
Calificación EDD (Evaluación de Desempeño Docente) según Facultad — Jornada.

`facultad_jefe` puede variar entre años para un mismo docente, así que se usa la "facultad
predominante" (la más frecuente entre sus años evaluados) — extensión del criterio D27.
Facultad no es binaria: 6 pruebas t de Welch, cada facultad vs. el resto combinado.
Nombres de facultad como en el Bloque I; `facultad_jefe` (unidad de la jefatura que evalúa)
no es el mismo campo que `unidad_facultad` del Bloque I, por eso los N° no coinciden.

Revisión 2026-09-27 (D37): usa la EDD limpia (sin notas dañadas de 2024-2025, edd_comun.py) y
el veredicto binario con p corregido por Holm por bloque (barra dorada = difiere del resto).

FUENTE: intel.evaluacion_jefes (Postgres, en vivo) — vía edd_comun.cargar_edd
SALIDA: P1_edd_facultad.pptx (1 diapositiva) + edd_facultad_chart.png
"""
import sys; sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "shared"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import CASCADE, OUTPUTS
from pptx_helpers import UcenSlideKit, prueba_dict, es_significativa
from edd_comun import cargar_edd, NOTA_LIMPIEZA

import numpy as np
import pandas as pd
import matplotlib.patheffects as pe
from scipy import stats
from sqlalchemy import create_engine
from pptx import Presentation
from pptx.util import Emu

HERE = Path(__file__).parent
OUT_PPTX = Path(OUTPUTS) / "pptx" / "P1_edd_facultad.pptx"
OUT_PPTX.parent.mkdir(parents=True, exist_ok=True)

DB_URL = "postgresql://ucen_user:ucen2026@localhost:5432/ucen"
FAC_NOMBRE = {
    "FAMEDSA": "Medicina y C. Salud", "FINARQ": "Ingeniería y Arq.", "FED": "Educación",
    "FEGOC": "Economía, Gob. y Com.", "FACDEH": "Derecho y Humanidades",
    "VRIIP": "VR Investigación y Postgrado",
}
COL_SIGNIF = "#F2D675"
COL_NO_SIGNIF = "#4E8FC9"


def clave(fac):
    return f"EDD limpia: {fac} vs resto"


# ── Datos ───────────────────────────────────────────────────────────────────
doc = pd.read_csv(Path(CASCADE) / "01_jornada" / "docentes_jornada.csv", encoding="utf-8-sig")
N_JORNADA = len(doc)

engine = create_engine(DB_URL)
edd = cargar_edd(engine)
raw = edd.dropna(subset=["facultad_jefe"])
conteo = raw.groupby(["rut_key", "facultad_jefe"]).size().reset_index(name="n")
predominante = conteo.loc[conteo.groupby("rut_key")["n"].idxmax(), ["rut_key", "facultad_jefe"]]
por_docente = (predominante.merge(raw.groupby("rut_key")["edd_limpia"].mean().reset_index(), on="rut_key")
               .dropna(subset=["edd_limpia"]))
por_docente["fac"] = por_docente["facultad_jefe"].map(FAC_NOMBRE).fillna(por_docente["facultad_jefe"])
N_FACULTAD_CAMBIO = int((conteo.groupby("rut_key")["facultad_jefe"].nunique() > 1).sum())

resultados = []
for fac, g in por_docente.groupby("fac"):
    resto = por_docente.loc[por_docente["fac"] != fac, "edd_limpia"]
    t_stat, p_val = stats.ttest_ind(g["edd_limpia"], resto, equal_var=False)
    resultados.append(dict(fac=fac, media=g["edd_limpia"].mean(), media_resto=resto.mean(), n=len(g),
                           t=t_stat, p=p_val))
res = pd.DataFrame(resultados).set_index("fac").sort_values("media", ascending=False)
res["dif"] = res["media"] - res["media_resto"]

PRUEBAS = [prueba_dict("III · EDD", clave(fac), f"{r.media:.3f} vs {r.media_resto:.3f}", len(por_docente), r.p)
           for fac, r in res.iterrows()]

print(f"Universo Jornada: {N_JORNADA}  |  docentes con EDD limpia y facultad: {len(por_docente)}  |  "
      f"cambiaron de facultad: {N_FACULTAD_CAMBIO}")
print(res[["media", "media_resto", "dif", "n", "t", "p"]].round(4))


def agregar(prs):
    kit = UcenSlideKit(out_dir=HERE)
    kit.ensure_bg()
    signif = {f: es_significativa(r["p"], clave(f)) for f, r in res.iterrows()}
    fig = kit.new_chart_fig()
    ax = kit.chart_axes(fig, left=0.25, top=0.10)
    y = np.arange(len(res))
    colors = [COL_SIGNIF if signif[f] else COL_NO_SIGNIF for f in res.index]
    ax.barh(y, res["media"], height=0.6, color=colors, alpha=0.92, edgecolor="none", zorder=3)
    ax.axvline(por_docente["edd_limpia"].mean(), color="white", linestyle="--", linewidth=1, alpha=0.6)
    ax.text(por_docente["edd_limpia"].mean(), -0.75, "promedio general", color="#DDDDDD", fontsize=8,
            style="italic", ha="center")
    stroke = [pe.withStroke(linewidth=2, foreground="#0A0F18")]
    for i, (fac, r) in enumerate(res.iterrows()):
        marca = "*" if signif[fac] else ""
        ax.text(r["media"] + 0.012, i, f"{r['media']:.2f}{marca}   ({r['dif']:+.2f} vs resto · N°={int(r['n'])})",
                ha="left", va="center", fontsize=9.5, fontweight="bold", color="white",
                path_effects=stroke, zorder=6)
    ax.set_yticks(y); ax.set_yticklabels(res.index, fontsize=10.5, color="white")
    ax.invert_yaxis()
    ax.set_ylim(len(res) - 0.4, -1.1)
    ax.set_xlabel("EDD limpia promedio por docente (0-1)  ·  dorado y * = difiere del resto "
                  "(con corrección por comparaciones múltiples)", color="#AAAAAA", fontsize=9)
    ax.set_xlim(0, 1.45)
    ax.tick_params(axis="y", length=0, pad=8); ax.tick_params(axis="x", colors="#AAAAAA", labelsize=8.5)
    for sp in ax.spines.values():
        sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.7)
    ax.xaxis.grid(True, color="white", alpha=0.07, linewidth=0.5); ax.set_axisbelow(True)
    chart_path = kit.save_chart(fig, "edd_facultad_chart.png")

    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.pic_chart(sl, prs, chart_path)
    kit.title(sl, "Calificación EDD según facultad — Docentes Jornada")
    kit.subtitulo(sl, f"EDD limpia, 1 valor por docente, facultad predominante  ·  N°={len(por_docente)} docentes  ·  "
                      f"6 pruebas t de Welch, cada facultad vs el resto")
    difieren = [f for f in res.index if signif[f]]
    if difieren:
        arriba = [f for f in difieren if res.loc[f, "dif"] > 0]
        abajo = [f for f in difieren if res.loc[f, "dif"] < 0]
        partes = ([f"por encima {', '.join(arriba)}"] if arriba else []) + ([f"por debajo {', '.join(abajo)}"] if abajo else [])
        b1 = f"{len(difieren)} de 6 facultades difieren del resto: {'; '.join(partes)}."
    else:
        b1 = (f"Ninguna facultad difiere del resto: con la nota limpia la EDD va de {res['media'].min():.2f} a "
              f"{res['media'].max():.2f} entre facultades.")
    kit.punteo_numerado(sl, [
        b1,
        "Criterio: cada facultad vs el resto con prueba t de Welch y p corregido por comparaciones múltiples "
        "(Holm por bloque); detalle en el anexo.",
    ], fs=12)
    kit.notas(sl,
        f"Facultad = facultad_jefe (unidad de la jefatura que evalúa), predominante entre los años evaluados; "
        f"{N_FACULTAD_CAMBIO} docentes cambiaron de facultad entre años. No es el mismo campo que la "
        f"unidad/facultad del Bloque I. Las diferencias de la versión anterior (VR Investigación y Medicina "
        f"más bajas) venían de las notas dañadas: VR Investigación solo tiene evaluaciones 2024-2025. "
        + NOTA_LIMPIEZA)
    return sl


if __name__ == "__main__":
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(UcenSlideKit.SW_EMU), Emu(UcenSlideKit.SH_EMU)
    agregar(prs)
    prs.save(OUT_PPTX)
    print(f"\n✓ Guardado: {OUT_PPTX}")
