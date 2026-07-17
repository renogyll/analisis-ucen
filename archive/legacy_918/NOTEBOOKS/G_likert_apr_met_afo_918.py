import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib
import numpy as np
import os
from sqlalchemy import create_engine, text

BASE   = os.path.dirname(__file__)
OUT1   = os.path.join(BASE, "G_likert_divergente_918.png")
OUT2   = os.path.join(BASE, "G_dimensiones_resumen_918.png")

engine = create_engine("postgresql://ucen_user:ucen2026@localhost:5432/ucen")

matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 12,
})

# ── Cargar universo 917 ───────────────────────────────────────────────────────
doc917 = pd.read_csv(os.path.join(BASE,"..","PROCESADO","docente_918.csv"),
                     encoding="utf-8-sig", dtype={"rut_key": str})
doc917["rut_key"] = doc917["rut_key"].str.strip()
ruts_917 = set(doc917["rut_key"].astype(str))

# ── Query: promedios por pregunta filtrado al universo 917 ────────────────────
with engine.connect() as conn:
    df = pd.read_sql(text("""
        SELECT
            er.pregunta_id,
            AVG(er.pct_acuerdo)                        AS pct_acuerdo,
            AVG(er.pct_indiferente)                    AS pct_indiferente,
            AVG(er.pct_desacuerdo)                     AS pct_desacuerdo,
            AVG(er.pct_acuerdo)                        AS pct_favorable,
            COUNT(DISTINCT ep.rut_docente)             AS n_docentes,
            COUNT(*)                                   AS n_secciones
        FROM consolidados.evaluacion_respuesta er
        JOIN consolidados.evaluacion_periodo ep
             ON er.evaluacion_id = ep.evaluacion_id
        WHERE ep.rut_docente::text = ANY(:ruts)
          AND er.pregunta_id NOT IN ('SAT_BIN','SAT_NOTA')
        GROUP BY er.pregunta_id
        ORDER BY er.pregunta_id
    """), conn, params={"ruts": list(ruts_917)})

print("=== Promedios por pregunta (universo 917) ===")
print(df.to_string(index=False))

# ── Textos cortos de cada pregunta ───────────────────────────────────────────
TEXTOS = {
    "APR_01": "Vincula enseñanza con ejercicio profesional",
    "APR_02": "Promueve aplicación de aprendizajes",
    "APR_03": "Relaciona conocimientos previos/otras asig.",
    "MET_01": "Respeta diversidad e incluye mirada de género",
    "MET_02": "Evaluaciones permiten mostrar lo aprendido",
    "MET_03": "Metodología ayuda a lograr aprendizajes",
    "MET_04": "Orienta y clarifica ante dudas",
    "MET_05": "Comunica criterios de evaluación con anticipación",
    "AFO_01": "Usa lenguaje inclusivo",
    "AFO_02": "Comportamiento acorde a su rol",
    "AFO_03": "Revisa syllabus y competencias del perfil",
    "AFO_04": "Desarrolla todos los temas del syllabus",
    "AFO_05": "Asiste regularmente a clases",
    "AFO_06": "Respeta el horario de clases",
    "AFO_07": "Entrega resultados en tiempos establecidos",
    "AFO_08": "Demuestra interés por enseñar",
    "AFO_09": "Demuestra dominio de la materia",
}

DIMENSIONES = {
    "APR": ["APR_01","APR_02","APR_03"],
    "MET": ["MET_01","MET_02","MET_03","MET_04","MET_05"],
    "AFO": ["AFO_01","AFO_02","AFO_03","AFO_04","AFO_05","AFO_06","AFO_07","AFO_08","AFO_09"],
}
DIM_COLORES = {"APR": "#1565C0", "MET": "#6A1B9A", "AFO": "#2E7D32"}
DIM_NOMBRES = {
    "APR": "Aprendizajes",
    "MET": "Metodologías y Evaluación",
    "AFO": "Aspectos Formales",
}

# Ordenar: APR → MET → AFO
ORD_PREGS = (DIMENSIONES["APR"] + DIMENSIONES["MET"] + DIMENSIONES["AFO"])[::-1]
df = df.set_index("pregunta_id")

C_DA   = "#1565C0"   # De acuerdo — azul
C_IND  = "#CFD8DC"   # Indiferente — gris claro
C_DS   = "#C62828"   # Desacuerdo — rojo

# ══════════════════════════════════════════════════════════════════════════════
# GRÁFICO 1 — Divergente Likert completo
# ══════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(16, 11))

y_pos   = range(len(ORD_PREGS))
sep_dim = {"MET_05": 0.5, "APR_03": 0.5}   # separadores entre dimensiones

for i, pid in enumerate(ORD_PREGS):
    if pid not in df.index: continue
    row = df.loc[pid]
    da  = row["pct_acuerdo"]
    ind = row["pct_indiferente"]
    ds  = row["pct_desacuerdo"]

    # Barra De Acuerdo (derecha)
    ax.barh(i, da,  left=0,    height=0.7, color=C_DA,  alpha=0.85)
    # Barra Indiferente (continúa hacia la derecha, desde da)
    ax.barh(i, ind, left=da,   height=0.7, color=C_IND, alpha=0.85)
    # Barra Desacuerdo (izquierda)
    ax.barh(i, -ds, left=0,    height=0.7, color=C_DS,  alpha=0.85)

    # Etiquetas
    if da  > 4: ax.text(da/2,        i, f"{da:.0f}%",  ha="center", va="center", fontsize=9,  color="white", fontweight="bold")
    if ind > 4: ax.text(da + ind/2,  i, f"{ind:.0f}%", ha="center", va="center", fontsize=8,  color="#546E7A")
    if ds  > 4: ax.text(-ds/2,       i, f"{ds:.0f}%",  ha="center", va="center", fontsize=9,  color="white", fontweight="bold")

# Etiquetas preguntas (izquierda)
ax.set_yticks(list(y_pos))
ax.set_yticklabels(
    [f"{pid}  {TEXTOS.get(pid,'')}" for pid in ORD_PREGS],
    fontsize=10)

# Colores por dimensión en ytick labels
for i, pid in enumerate(ORD_PREGS):
    dim = pid.split("_")[0]
    ax.get_yticklabels()[i].set_color(DIM_COLORES[dim])

# Separadores entre dimensiones
for pid, gap in {"APR_03": 2.5, "MET_05": 8.5}.items():
    if pid in ORD_PREGS:
        ax.axhline(ORD_PREGS.index(pid) + 0.5, color="#EEEEEE", linewidth=1.5)

# Etiquetas de dimensión
dim_limits = {
    "AFO": (0,   8.5),
    "MET": (8.5, 13.5),
    "APR": (13.5, 16.5),
}
for dim, (y0, y1) in {"AFO":(0,8.5),"MET":(8.5,13.5),"APR":(13.5,16.5)}.items():
    mid = (y0 + y1) / 2
    ax.text(102, mid, DIM_NOMBRES[dim], ha="left", va="center",
            fontsize=10, fontweight="bold", color=DIM_COLORES[dim],
            clip_on=False)

ax.axvline(0, color="#333333", linewidth=1.2)
ax.set_xlim(-35, 100)
ax.set_xlabel("← % Desacuerdo        % De Acuerdo →", fontsize=12)
ax.set_title(
    "Evaluación Docente — Distribución de respuestas por pregunta\n"
    "Dimensiones APR · MET · AFO  ·  Universo 917 docentes jerarquizados",
    fontsize=14, fontweight="bold", pad=14)

legend_items = [
    mpatches.Patch(color=C_DA,  label="De acuerdo"),
    mpatches.Patch(color=C_IND, label="Indiferente"),
    mpatches.Patch(color=C_DS,  label="Desacuerdo"),
]
ax.legend(handles=legend_items, loc="lower right", fontsize=11, framealpha=0.9)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig(OUT1, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nGuardado: {OUT1}")

# ══════════════════════════════════════════════════════════════════════════════
# GRÁFICO 2 — Resumen por dimensión
# ══════════════════════════════════════════════════════════════════════════════
dim_agg = {}
for dim, pregs in DIMENSIONES.items():
    sub = df.reindex(pregs).dropna(subset=["pct_acuerdo"])
    dim_agg[dim] = {
        "pct_acuerdo":     sub["pct_acuerdo"].mean(),
        "pct_indiferente": sub["pct_indiferente"].mean(),
        "pct_desacuerdo":  sub["pct_desacuerdo"].mean(),
        "n_pregs":         len(sub),
    }

print("\n=== Resumen por dimensión ===")
for dim, v in dim_agg.items():
    print(f"  {DIM_NOMBRES[dim]}: DA={v['pct_acuerdo']:.1f}% | IND={v['pct_indiferente']:.1f}% | DS={v['pct_desacuerdo']:.1f}%")

fig2, ax2 = plt.subplots(figsize=(10, 6))

dims    = list(DIMENSIONES.keys())
x       = np.arange(len(dims))
w       = 0.55
da_vals  = [dim_agg[d]["pct_acuerdo"]     for d in dims]
ind_vals = [dim_agg[d]["pct_indiferente"] for d in dims]
ds_vals  = [dim_agg[d]["pct_desacuerdo"]  for d in dims]

b_da  = ax2.bar(x, da_vals,                    width=w, color=[DIM_COLORES[d] for d in dims], alpha=0.88, label="De acuerdo")
b_ind = ax2.bar(x, ind_vals, bottom=da_vals,   width=w, color=C_IND, alpha=0.85, label="Indiferente")
b_ds  = ax2.bar(x, ds_vals,  bottom=[a+b for a,b in zip(da_vals,ind_vals)], width=w, color=C_DS, alpha=0.82, label="Desacuerdo")

for i, (da, ind, ds) in enumerate(zip(da_vals, ind_vals, ds_vals)):
    ax2.text(i, da/2,          f"{da:.1f}%",  ha="center", va="center", fontsize=13, color="white", fontweight="bold")
    if ind > 2:
        ax2.text(i, da+ind/2,  f"{ind:.1f}%", ha="center", va="center", fontsize=11, color="#546E7A")
    ax2.text(i, da+ind+ds/2,   f"{ds:.1f}%",  ha="center", va="center", fontsize=12, color="white", fontweight="bold")

ax2.set_xticks(x)
ax2.set_xticklabels([f"{DIM_NOMBRES[d]}\n({dim_agg[d]['n_pregs']} preguntas)" for d in dims],
                    fontsize=12, fontweight="bold")
ax2.set_ylabel("% de respuestas")
ax2.set_ylim(0, 105)
ax2.set_title(
    "Evaluación Docente — Resumen por dimensión\n"
    "% De acuerdo · Indiferente · Desacuerdo  ·  Universo 917",
    fontsize=14, fontweight="bold", pad=14)
ax2.legend(loc="upper right", fontsize=11, framealpha=0.9)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig(OUT2, dpi=150, bbox_inches="tight")
plt.close()
print(f"Guardado: {OUT2}")

# ── Bajadas ───────────────────────────────────────────────────────────────────
da_apr = dim_agg["APR"]["pct_acuerdo"]
da_met = dim_agg["MET"]["pct_acuerdo"]
da_afo = dim_agg["AFO"]["pct_acuerdo"]
mejor  = max(dim_agg, key=lambda d: dim_agg[d]["pct_acuerdo"])
peor   = min(dim_agg, key=lambda d: dim_agg[d]["pct_acuerdo"])

print(f"""
BAJADAS — Gráfico resumen por dimensión
• Las tres dimensiones de la evaluación docente muestran altos niveles de
  acuerdo estudiantil: {DIM_NOMBRES['AFO']} lidera con {da_afo:.1f}% de respuestas
  favorables, seguida de {DIM_NOMBRES['APR']} ({da_apr:.1f}%) y
  {DIM_NOMBRES['MET']} ({da_met:.1f}%). La dimensión de metodologías
  concentra la mayor proporción de respuestas neutrales e indiferentes,
  lo que abre un espacio prioritario para intervención formativa.

• El gráfico divergente revela que las preguntas sobre asistencia, puntualidad
  y dominio de la materia (AFO) concentran los mayores porcentajes de acuerdo,
  mientras las preguntas sobre diversidad metodológica y criterios de evaluación
  (MET) presentan mayor dispersión. Este patrón es consistente con los
  objetivos de los programas de formación docente vigentes.
""")
