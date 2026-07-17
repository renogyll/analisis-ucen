import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib
import numpy as np
import os
from sqlalchemy import create_engine, text

BASE   = os.path.dirname(__file__)
OUT    = os.path.join(BASE, "G_tipologias_918.png")
engine = create_engine("postgresql://ucen_user:ucen2026@localhost:5432/ucen")

matplotlib.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12})

doc917   = pd.read_csv(os.path.join(BASE,"..","PROCESADO","docente_918.csv"),
                       encoding="utf-8-sig", dtype={"rut_key": str})
ruts_917 = list(doc917["rut_key"].str.strip().astype(str))
n_univ   = len(doc917)

PREGS_APR = ["APR_01","APR_02","APR_03"]
PREGS_MET = ["MET_01","MET_02","MET_03","MET_04","MET_05"]
PREGS_AFO = ["AFO_01","AFO_02","AFO_03","AFO_04","AFO_05",
             "AFO_06","AFO_07","AFO_08","AFO_09"]
ALL_PREGS  = PREGS_APR + PREGS_MET + PREGS_AFO

with engine.connect() as conn:
    df = pd.read_sql(text("""
        SELECT ep.rut_docente, er.pregunta_id, AVG(er.pct_acuerdo) AS score
        FROM consolidados.evaluacion_respuesta er
        JOIN consolidados.evaluacion_periodo ep ON er.evaluacion_id = ep.evaluacion_id
        WHERE ep.rut_docente::text = ANY(:ruts)
          AND er.pregunta_id = ANY(:pregs)
        GROUP BY ep.rut_docente, er.pregunta_id
    """), conn, params={"ruts": ruts_917, "pregs": ALL_PREGS})

# ── Score por dimensión por docente ───────────────────────────────────────────
def dim_score(df, pregs):
    return (df[df["pregunta_id"].isin(pregs)]
            .groupby("rut_docente")["score"].mean())

apr_s = dim_score(df, PREGS_APR)
met_s = dim_score(df, PREGS_MET)
afo_s = dim_score(df, PREGS_AFO)

docentes = pd.DataFrame({"apr": apr_s, "met": met_s, "afo": afo_s}).dropna()

def nivel_apr(p): return "A" if p>=80 else ("M" if p>=60 else "B")
def nivel_met(p): return "A" if p>=80 else ("M" if p>=60 else "B")
def nivel_afo(p): return "A" if p>=90 else ("M" if p>=75 else "B")

docentes["nAPR"] = docentes["apr"].apply(nivel_apr)
docentes["nMET"] = docentes["met"].apply(nivel_met)
docentes["nAFO"] = docentes["afo"].apply(nivel_afo)

# ── Clasificación por tipología (prioridad en orden) ─────────────────────────
def tipologia(row):
    a, m, f = row["nAPR"], row["nMET"], row["nAFO"]

    # G1 — Sello UCEN: Alto en APR y AFO, máx 1 Medio en MET
    if a == "A" and f == "A" and m in ("A","M"):
        return "G1"
    # G6 — Alerta: Bajo en 2 o 3 dimensiones
    if [a,m,f].count("B") >= 2:
        return "G6"
    # G2 — Administrador Tradicional: Alto AFO, Bajo MET
    if f == "A" and m == "B":
        return "G2"
    # G3 — Práctico Desorganizado: Alto APR, Bajo AFO
    if a == "A" and f == "B":
        return "G3"
    # G4 — Desconectado del Perfil: Bajo APR, no Bajo en el resto
    if a == "B" and m != "B" and f != "B":
        return "G4"
    # G5 — En Desarrollo: todo lo demás
    return "G5"

docentes["tipo"] = docentes.apply(tipologia, axis=1)

n_doc = len(docentes)
n_sin = n_univ - n_doc

TIPOS = {
    "G1": {"nombre": "Sello UCEN\n(Excelencia Integral)",       "color": "#1B5E20"},
    "G2": {"nombre": "Administrador\nTradicional",               "color": "#1565C0"},
    "G3": {"nombre": "Práctico\nDesorganizado",                  "color": "#E65100"},
    "G4": {"nombre": "Cercano Pedagógicamente,\nDesconectado",   "color": "#6A1B9A"},
    "G5": {"nombre": "En Desarrollo\n(Rendimiento Promedio)",    "color": "#78909C"},
    "G6": {"nombre": "Alerta\nInstitucional",                    "color": "#B71C1C"},
}

conteo = docentes["tipo"].value_counts().reindex(list(TIPOS.keys())).fillna(0).astype(int)

# ── Cascada ───────────────────────────────────────────────────────────────────
print("=" * 65)
print("  TIPOLOGÍA DOCENTE — Mapa de distribución de perfiles")
print("=" * 65)
print(f"  917 docentes jerarquizados (Universo 917)")
print(f"    ├── {n_doc} clasificados con evaluación completa APR+MET+AFO")
for gid, cfg in TIPOS.items():
    n  = conteo[gid]
    pct = 100*n/n_doc
    nombre = cfg["nombre"].replace("\n"," ")
    print(f"    │     ├── {gid}: {n:3d} docentes ({pct:.1f}%)  — {nombre}")
print(f"    └── {n_sin} sin evaluación registrada")
print("=" * 65)

# ── Figura: Dona + tabla resumen ──────────────────────────────────────────────
fig, (ax_dona, ax_tbl) = plt.subplots(1, 2, figsize=(16, 8),
                                       gridspec_kw={"width_ratios": [1, 1.2]})
fig.suptitle(
    "Mapa de Tipología Docente — Cuerpo Jerarquizado UCEN\n"
    f"Universo 917 · {n_doc} docentes con evaluación APR + MET + AFO",
    fontsize=14, fontweight="bold")

# Dona
sizes  = [conteo[g] for g in TIPOS]
colors = [TIPOS[g]["color"] for g in TIPOS]
labels = [f"{TIPOS[g]['nombre'].replace(chr(10),' ')}\n{conteo[g]} ({100*conteo[g]/n_doc:.1f}%)"
          for g in TIPOS]

wedges, texts = ax_dona.pie(
    sizes, colors=colors, startangle=90, counterclock=False,
    wedgeprops=dict(width=0.55, edgecolor="white", linewidth=2.5),
    labels=None)

# Anotaciones con líneas
for i, (wedge, gid) in enumerate(zip(wedges, TIPOS)):
    ang  = (wedge.theta2 + wedge.theta1) / 2
    x    = 0.75 * np.cos(np.radians(ang))
    y    = 0.75 * np.sin(np.radians(ang))
    x2   = 1.2  * np.cos(np.radians(ang))
    y2   = 1.2  * np.sin(np.radians(ang))
    ha   = "left" if x2 > 0 else "right"
    n    = conteo[gid]
    pct  = 100*n/n_doc
    if pct < 1:
        continue
    ax_dona.annotate(
        f"{TIPOS[gid]['nombre'].replace(chr(10),' ')}\n{n} doc. ({pct:.1f}%)",
        xy=(x, y), xytext=(x2*1.05, y2*1.05),
        arrowprops=dict(arrowstyle="-", color="#666666", lw=1),
        fontsize=9, ha=ha, va="center", color=TIPOS[gid]["color"],
        fontweight="bold")

# Centro de la dona
ax_dona.text(0, 0, f"{n_doc}\ndocentes", ha="center", va="center",
             fontsize=13, fontweight="bold", color="#333333")
ax_dona.set_xlim(-1.8, 1.8)

# Panel derecho: tabla de descripción
ax_tbl.axis("off")
row_data = []
for gid, cfg in TIPOS.items():
    n   = conteo[gid]
    pct = 100*n/n_doc
    row_data.append([gid, cfg["nombre"].replace("\n"," "),
                     f"{n}", f"{pct:.1f}%"])

col_labels = ["Perfil", "Descripción", "N", "%"]
tbl = ax_tbl.table(cellText=row_data, colLabels=col_labels,
                   loc="center", cellLoc="left")
tbl.auto_set_font_size(False)
tbl.set_fontsize(11)
tbl.scale(1, 2.2)

# Header
for j in range(4):
    tbl[0, j].set_facecolor("#37474F")
    tbl[0, j].set_text_props(color="white", fontweight="bold")

# Filas con color de tipología
for i, gid in enumerate(TIPOS, start=1):
    color_hex = TIPOS[gid]["color"]
    for j in range(4):
        tbl[i, j].set_facecolor("#F5F5F5" if i%2==0 else "#FFFFFF")
    tbl[i, 0].set_text_props(color=color_hex, fontweight="bold")
    tbl[i, 1].set_text_props(color=color_hex)

tbl.auto_set_column_width([0,1,2,3])
ax_tbl.set_title("Distribución por tipología", fontsize=12,
                 fontweight="bold", pad=10)

plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nGuardado: {OUT}")

g1_pct = 100*conteo["G1"]/n_doc
g5_pct = 100*conteo["G5"]/n_doc
g6_pct = 100*conteo["G6"]/n_doc
g2_pct = 100*conteo["G2"]/n_doc

print(f"""
BAJADAS
• El perfil más frecuente es "Sello UCEN" ({g1_pct:.1f}% del cuerpo docente),
  lo que indica que la mayoría alcanza simultáneamente niveles altos en las
  tres dimensiones evaluadas. El perfil "En Desarrollo" agrupa al {g5_pct:.1f}%,
  configurando la segunda masa más relevante — docentes con desempeño
  homogéneo en rango medio que representan el principal potencial de
  mejora sistémica con acompañamiento formativo diferenciado.

• El perfil "Alerta Institucional" afecta al {g6_pct:.1f}% de los docentes
  evaluados — aquellos con Nivel Bajo en 2 o más dimensiones simultáneamente.
  Aunque es el grupo minoritario, concentra el mayor riesgo para los
  indicadores de acreditación y satisfacción estudiantil, y requiere
  intervención prioritaria e individualizada.
""")
