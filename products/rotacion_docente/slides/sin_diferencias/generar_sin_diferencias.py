"""Rotación — Variables que NO explican la rotación: escalafón, nivel de jerarquía, facultad y sexo
(D39: las no significativas van juntas en una diapositiva). Cada variable se prueba en el total y
dentro de cada contrato de entrada, para separar su efecto del efecto del contrato."""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import rotacion_comun as rc  # noqa: E402
import pandas as pd  # noqa: E402
from pptx_helpers import es_significativa, prueba_dict  # noqa: E402

df = rc.cargar_datos()
VARIABLES = [("escalafon", "Escalafón", rc.ESCALAFONES, rc.ESCALAFONES),
             ("nivel", "Nivel de jerarquía", rc.NIVELES, ["Instr.", "Asist.", "Asoc.", "Titular"]),
             ("fac", "Facultad", rc.FACULTADES, ["Medicina", "Ingeniería", "Educación", "Economía", "Derecho"]),
             ("sexo_", "Sexo", rc.SEXOS, rc.SEXOS)]
ESTRATOS = [("total", df), ("Jornada", df[df["contrato"] == "JORNADA"]),
            ("Honorario", df[df["contrato"] == "HONORARIO"])]

PRUEBAS, CLAVES = [], []
for col, nombre, _cats, _ in VARIABLES:
    for estrato, sub in ESTRATOS:
        clave = f"Baja según {nombre.lower()} — {estrato}"
        pr, _, _ = rc.chi2(sub, col, clave, orden=_cats)
        PRUEBAS.append(pr); CLAVES.append(clave)

# Desempeño (extensión, D39): EDD limpia (solo Jornada tiene EDD) y % de aprobación de sus alumnos.
from scipy import stats as _st  # noqa: E402
from sqlalchemy import create_engine as _ce, text as _tx  # noqa: E402
sys.path.insert(0, str(rc.ROOT / "products" / "p1_planta" / "caracterizacion"))
from edd_comun import cargar_edd  # noqa: E402
_eng = _ce(rc.DB_URL)
_edd = cargar_edd(_eng)
_edd = _edd.assign(rut_key=_edd["rut_key"].astype(str)).groupby("rut_key")["edd_limpia"].mean().dropna()
_apr = pd.read_sql(_tx("""SELECT rut_docente::text AS rut_key, AVG(CASE WHEN aprueba THEN 1.0 ELSE 0 END) * 100 AS pct
                          FROM intel.rendimiento_academico_alumnos WHERE aprueba IS NOT NULL GROUP BY 1"""), _eng)
DESEMP = {}
for nombre, serie, contratos in [("EDD", _edd, ["JORNADA"]), ("% de aprobación", _apr.set_index("rut_key")["pct"], rc.CONTRATOS)]:
    for c in contratos:
        s = df[df["contrato"] == c].merge(serie.rename("v"), left_on="rut_key", right_index=True)
        a, b = s.loc[s["baja"] == 1, "v"], s.loc[s["baja"] == 0, "v"]
        clave = f"{nombre}: bajas vs activos — {c.capitalize()}"
        fmt = "{:.3f}" if nombre == "EDD" else "{:.1f}%"
        PRUEBAS.append(prueba_dict(rc.BLOQUE_EXT, clave, f"Bajas: {fmt.format(a.mean())} / Siguen: {fmt.format(b.mean())}",
                                   len(s), _st.ttest_ind(a, b, equal_var=False).pvalue))
        DESEMP[(nombre, c)] = (a.mean(), b.mean())
CLAVES_DESEMP = [pr["comparacion"] for pr in PRUEBAS if pr["bloque"] == rc.BLOQUE_EXT]

esc_tot = rc.tasa_baja(df, "escalafon", rc.ESCALAFONES)
reg_por_contrato = df[df["escalafon"] == "Regular"]["contrato"].value_counts()
N_SIN_FAC = int(df["fac"].isna().sum())
N_SIN_FAC_H = int((df["fac"].isna() & (df["contrato"] == "HONORARIO")).sum())


def agregar(prs):
    sig = [pr["comparacion"] for pr in PRUEBAS if es_significativa(pr["p"], pr["comparacion"])]  # incluye desempeño
    assert not sig, f"Hay pruebas significativas, reescribir la diapositiva: {sig}"
    kit = rc.kit_para(HERE)
    fig, axes = rc.paneles(kit, [0.9, 1.3, 1.6, 0.85], bottom=0.22, izq=[0, 0, 0.035, 0],
                           leyenda=[("Jornada", rc.COL_J), ("Honorario", rc.COL_H)])
    for ax, (col, nombre, cats, etiquetas) in zip(axes, VARIABLES):
        x = np.arange(len(cats))
        for i, (contrato, color) in enumerate([("JORNADA", rc.COL_J), ("HONORARIO", rc.COL_H)]):
            t = rc.tasa_baja(df[df["contrato"] == contrato], col, cats)
            xs = x + (i - 0.5) * 0.4
            ax.bar(xs, t["pct"], width=0.38, color=color, zorder=3)
            for xi, v in zip(xs, t["pct"]):
                rc.etiqueta(ax, xi, v + 1.5, f"{v:.0f}", ha="center", va="bottom", fontsize=7.5)
        ax.set_xticks(x)
        if col == "fac":
            ax.set_xticklabels(etiquetas, color="white", fontsize=8, rotation=30, ha="right", rotation_mode="anchor")
        else:
            ax.set_xticklabels(etiquetas, color="white", fontsize=8.5)
        ax.set_ylim(0, 75)
        rc.estilo(ax, f"{nombre}\n% que se fue")
    chart = rc.guardar_paneles(kit, fig, axes, "sin_diferencias_chart.png")

    n_perfil = len(PRUEBAS) - len(CLAVES_DESEMP)
    sl = rc.lamina_base(kit, prs, "El perfil del docente no explica quién se va",
        "Cada barra = % del grupo que se fue (no aparece en 2026), según contrato de entrada · facultad: solo las 5 facultades")
    kit.pic_chart(sl, prs, chart)
    kit.punteo_numerado(sl, [
        f"Se compararon 4 características del docente, en el total y dentro de cada contrato ({n_perfil} pruebas "
        "estadísticas): ninguna muestra diferencia significativa en el % que se fue.",
        f"En el total, Regular parece irse menos ({esc_tot.loc['Regular', 'pct']:.1f}% vs "
        f"{esc_tot.loc['Docente', 'pct']:.1f}% Docente), pero es porque "
        f"{reg_por_contrato.get('JORNADA', 0)} de {reg_por_contrato.sum()} Regulares son Jornada; dentro de cada contrato no difiere.",
        "Lo que se repite en todos los gráficos es la distancia entre Jornada (azul) y Honorario (amarillo): el contrato.",
    ], fs=12)
    kit.notas(sl,
        "Chi-cuadrado de independencia (estado × categoría) en el total y dentro de cada contrato de entrada; "
        f"{len(PRUEBAS)} pruebas, ninguna con diferencia significativa (detalle en el anexo). "
        "Nivel de jerarquía = Instructor/Asistente/Asociado/Titular (el escalafón va aparte), para evitar celdas "
        f"de 0-7 casos del cruce de 8 categorías. Sin facultad: {N_SIN_FAC} docentes, {N_SIN_FAC_H} de ellos "
        "Honorario; no es una facultad y repetía el efecto del contrato (D39). En Honorario las facultades tienen "
        "pocos casos (145 en total), por eso sus barras varían más. La diferencia entre barras azules y amarillas es la del "
        "contrato. Desempeño: EDD limpia (D37, solo Jornada) y % de aprobación por docente (t de Welch), pruebas en el anexo.")
    return sl
