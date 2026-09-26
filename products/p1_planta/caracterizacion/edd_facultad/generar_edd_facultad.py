"""
P1 — Caracterización del Cuerpo Académico de Planta
Calificación EDD (Evaluación de Desempeño Docente) según Facultad — Jornada.

`facultad_jefe` puede variar entre años para un mismo docente, así que se usa la "facultad
predominante" (la más frecuente entre sus años evaluados) — extensión del criterio D27.
Facultad no es binaria: 6 pruebas t de Welch, cada facultad vs. el resto combinado.

Revisión 2026-09-26:
  - D36: usa la EDD ajustada por año (edd_comun.py). Sin ajuste, VRIIP (evaluada solo en
    2024-2025, los años de escala baja) aparecía artificialmente más baja.
  - Obs. 10: se muestran nombres de facultad (mismos del Bloque I) en vez de siglas. Ojo:
    `facultad_jefe` (unidad de la jefatura que evalúa) NO es el mismo campo que
    `unidad_facultad` del Bloque I; los N° no coinciden y se aclara en notas.
  - Obs. 21: descriptivo y prueba en una sola diapositiva (barra por facultad, * = difiere
    del resto al 5%).

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
from pptx_helpers import UcenSlideKit, prueba_dict
from edd_comun import cargar_edd, NOTA_AJUSTE, ANIO_REF

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

# ── Datos ───────────────────────────────────────────────────────────────────
doc = pd.read_csv(Path(CASCADE) / "01_jornada" / "docentes_jornada.csv", encoding="utf-8-sig")
N_JORNADA = len(doc)

engine = create_engine(DB_URL)
edd = cargar_edd(engine)
raw = edd.dropna(subset=["facultad_jefe"])
conteo = raw.groupby(["rut_key", "facultad_jefe"]).size().reset_index(name="n")
predominante = conteo.loc[conteo.groupby("rut_key")["n"].idxmax(), ["rut_key", "facultad_jefe"]]
por_docente = predominante.merge(raw.groupby("rut_key")["edd_aj"].mean().reset_index(), on="rut_key")
por_docente["fac"] = por_docente["facultad_jefe"].map(FAC_NOMBRE).fillna(por_docente["facultad_jefe"])
N_FACULTAD_CAMBIO = int((conteo.groupby("rut_key")["facultad_jefe"].nunique() > 1).sum())
SIN_2022_23 = sorted(set(raw["facultad_jefe"]) - set(raw.loc[raw["anio"] <= 2023, "facultad_jefe"]))

resultados = []
for fac, g in por_docente.groupby("fac"):
    resto = por_docente.loc[por_docente["fac"] != fac, "edd_aj"]
    t_stat, p_val = stats.ttest_ind(g["edd_aj"], resto, equal_var=False)
    resultados.append(dict(fac=fac, media=g["edd_aj"].mean(), media_resto=resto.mean(), n=len(g),
                           t=t_stat, p=p_val))
res = pd.DataFrame(resultados).set_index("fac").sort_values("media", ascending=False)
res["signif"] = res["p"] < 0.05
res["dif"] = res["media"] - res["media_resto"]

PRUEBAS = [prueba_dict("III · EDD", f"EDD ajustada por año: {fac} vs resto",
                       f"{r.media:.2f} vs {r.media_resto:.2f}", len(por_docente), r.p)
           for fac, r in res.iterrows()]

print(f"Universo Jornada: {N_JORNADA}  |  docentes con EDD y facultad: {len(por_docente)}  |  "
      f"cambiaron de facultad: {N_FACULTAD_CAMBIO}  |  sin evaluaciones 2022-2023: {SIN_2022_23}")
print(res[["media", "media_resto", "dif", "n", "t", "p", "signif"]].round(4))


def agregar(prs):
    kit = UcenSlideKit(out_dir=HERE)
    kit.ensure_bg()
    fig = kit.new_chart_fig()
    ax = kit.chart_axes(fig, left=0.25, top=0.10)

    y = np.arange(len(res))
    colors = [COL_SIGNIF if s else COL_NO_SIGNIF for s in res["signif"]]
    ax.barh(y, res["media"], height=0.6, color=colors, alpha=0.92, edgecolor="none", zorder=3)
    ax.axvline(por_docente["edd_aj"].mean(), color="white", linestyle="--", linewidth=1, alpha=0.6)
    ax.text(por_docente["edd_aj"].mean(), -0.75, "promedio general", color="#DDDDDD", fontsize=8,
            style="italic", ha="center")
    stroke = [pe.withStroke(linewidth=2, foreground="#0A0F18")]
    for i, (fac, r) in enumerate(res.iterrows()):
        marca = "*" if r["signif"] else ""
        ax.text(r["media"] + 0.012, i, f"{r['media']:.2f}{marca}   ({r['dif']:+.2f} vs resto · N°={int(r['n'])})",
                ha="left", va="center", fontsize=9.5, fontweight="bold", color="white",
                path_effects=stroke, zorder=6)
    ax.set_yticks(y); ax.set_yticklabels(res.index, fontsize=10.5, color="white")
    ax.invert_yaxis()
    ax.set_ylim(len(res) - 0.4, -1.1)
    ax.set_xlabel(f"EDD ajustada por año (escala {ANIO_REF})  ·  dorado y * = difiere del resto al 5%",
                  color="#AAAAAA", fontsize=9)
    ax.set_xlim(0, res["media"].max() * 1.6)
    ax.tick_params(axis="y", length=0, pad=8); ax.tick_params(axis="x", colors="#AAAAAA", labelsize=8.5)
    for sp in ax.spines.values():
        sp.set_edgecolor("white"); sp.set_alpha(0.20); sp.set_linewidth(0.7)
    ax.xaxis.grid(True, color="white", alpha=0.07, linewidth=0.5); ax.set_axisbelow(True)
    chart_path = kit.save_chart(fig, "edd_facultad_chart.png")

    sl = kit.new_slide(prs)
    kit.pic(sl, prs, kit.SHARED_BG)
    kit.pic_chart(sl, prs, chart_path)
    kit.title(sl, "Calificación EDD según facultad — Docentes Jornada")
    kit.subtitulo(sl, f"EDD ajustada por año, 1 valor por docente, facultad predominante  ·  "
                      f"N°={len(por_docente)} docentes  ·  6 pruebas t de Welch, cada facultad vs. el resto")
    arriba = [f for f, r in res.iterrows() if r["signif"] and r["dif"] > 0]
    abajo = [f for f, r in res.iterrows() if r["signif"] and r["dif"] < 0]
    no_sig = [f for f, r in res.iterrows() if not r["signif"]]
    bullets = [f"{int(res['signif'].sum())} de 6 facultades difieren del resto al 5%: por encima "
               f"{', '.join(arriba)}; por debajo {', '.join(abajo)}."]
    if no_sig:
        bullets.append(f"Sin diferencia significativa: {', '.join(no_sig)}. Sin corrección por comparaciones "
                       f"múltiples; con corrección de Holm, ver anexo.")
    kit.punteo_numerado(sl, bullets, fs=12)
    kit.notas(sl,
        f"Facultad = facultad_jefe (unidad de la jefatura que evalúa), predominante entre los años "
        f"evaluados; {N_FACULTAD_CAMBIO} docentes cambiaron de facultad entre años. No es el mismo campo "
        f"que la unidad/facultad del Bloque I, por eso los N° no coinciden. "
        f"{', '.join(FAC_NOMBRE.get(f, f) for f in SIN_2022_23)} no tiene evaluaciones 2022-2023. "
        + NOTA_AJUSTE)
    return sl


if __name__ == "__main__":
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(UcenSlideKit.SW_EMU), Emu(UcenSlideKit.SH_EMU)
    agregar(prs)
    prs.save(OUT_PPTX)
    print(f"\n✓ Guardado: {OUT_PPTX}")
