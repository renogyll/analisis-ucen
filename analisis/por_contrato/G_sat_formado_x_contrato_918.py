import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os
from sqlalchemy import create_engine, text

BASE   = os.path.dirname(__file__)
OUT    = os.path.join(BASE, "G_sat_formado_x_contrato_918.png")
SRC    = os.path.join(BASE, "..", "..", "CONSOLIDADO DOCENTES 3-05-2026")
engine = create_engine("postgresql://ucen_user:ucen2026@localhost:5432/ucen")

matplotlib.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})

C_FORM = "#1565C0"
C_NO   = "#CFD8DC"

def limpiar_rut(s):
    return str(s).strip().replace(".", "").split("-")[0].strip()

# NOMINA
nom = pd.read_csv(os.path.join(SRC, "CONSOLIDADO DOCENTES 3-05-2026.xlsx - NOMINA .csv"),
                  dtype=str, encoding="utf-8-sig")
nom.columns = nom.columns.str.strip()
nom["rut_key"] = nom["RUT"].apply(limpiar_rut)
nom["tipo_contrato"] = nom["JORNADA/HONORARIO"].str.strip().str.upper()
tipo_map = {}
for _, row in nom.iterrows():
    rut, tipo = row["rut_key"], row["tipo_contrato"]
    if rut not in tipo_map or tipo == "JORNADA": tipo_map[rut] = tipo

# Sets formados
ruts_form = set()
for year in ["2022","2023","2024","2025"]:
    df = pd.read_csv(os.path.join(SRC, f"CONSOLIDADO DOCENTES 3-05-2026.xlsx - DIPLOMADO {year}.csv"),
                     encoding="utf-8-sig", dtype=str)
    df["rut_key"] = df["RUT"].apply(limpiar_rut); ruts_form |= set(df["rut_key"])
for f in ["TALLERES 2023_2","TALLERES 2024_1","TALLERES 2024_2"]:
    df = pd.read_csv(os.path.join(SRC, f"CONSOLIDADO DOCENTES 3-05-2026.xlsx - {f}.csv"),
                     encoding="utf-8-sig", dtype=str)
    df.columns = df.columns.str.strip(); df["rut_key"] = df["RUT"].apply(limpiar_rut)
    ruts_form |= set(df["rut_key"])
df = pd.read_csv(os.path.join(SRC, "CONSOLIDADO DOCENTES 3-05-2026.xlsx - PROYECTOS DE INVESTIGACION.csv"),
                 encoding="utf-8-sig", dtype=str)
df.columns = df.columns.str.strip(); df["rut_key"] = df["RUT"].apply(limpiar_rut)
ruts_form |= set(df["rut_key"])

ruts = list(tipo_map.keys())

# SAT promedio global por docente
with engine.connect() as conn:
    df_sat = pd.read_sql(text("""
        SELECT ep.rut_docente::text AS rut_key, AVG(er.nota_promedio) AS sat_nota
        FROM consolidados.evaluacion_respuesta er
        JOIN consolidados.evaluacion_periodo ep ON er.evaluacion_id = ep.evaluacion_id
        WHERE er.pregunta_id = 'SAT_NOTA' AND ep.rut_docente::text = ANY(:ruts)
        GROUP BY ep.rut_docente
    """), conn, params={"ruts": ruts})

df_sat["tipo"]    = df_sat["rut_key"].map(tipo_map)
df_sat["formado"] = df_sat["rut_key"].isin(ruts_form)
df_sat = df_sat[df_sat["tipo"].isin(["JORNADA","HONORARIO"])].copy()

# 4 grupos
GRUPOS = [
    ("Jornada\nFormado",       "JORNADA",   True),
    ("Jornada\nSin formación", "JORNADA",   False),
    ("Honorario\nFormado",     "HONORARIO", True),
    ("Honorario\nSin formación","HONORARIO", False),
]
COLORES = [C_FORM, C_NO, C_FORM, C_NO]

stats = []
for label, tipo, formado in GRUPOS:
    sub = df_sat[(df_sat["tipo"]==tipo) & (df_sat["formado"]==formado)]["sat_nota"]
    stats.append({"label":label, "n":len(sub), "media":sub.mean(), "mediana":sub.median()})

# ── Cascada ───────────────────────────────────────────────────────────────────
print("=" * 65)
print("  SAT por Tipo de Contrato × Condición de Formación")
print("=" * 65)
for s in stats:
    print(f"  {s['label'].replace(chr(10),' '):25}: n={s['n']:3d} | "
          f"media={s['media']:.3f} | mediana={s['mediana']:.3f}")
brecha_j = stats[0]["mediana"] - stats[1]["mediana"]
brecha_h = stats[2]["mediana"] - stats[3]["mediana"]
print(f"\n  Brecha formado vs no (mediana):")
print(f"    Jornada   : {brecha_j:+.3f}")
print(f"    Honorario : {brecha_h:+.3f}")
print("=" * 65)

# ── Figura ────────────────────────────────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
fig.suptitle(
    "SAT Nota Promedio: Formados vs Sin Formación dentro de cada Tipo de Contrato\n"
    "Universo NOMINA · ¿La formación impacta igual en Jornada y Honorario?",
    fontsize=13, fontweight="bold")

# Panel A — Barras de mediana
x = np.arange(4)
medianas = [s["mediana"] for s in stats]
bars = ax1.bar(x, medianas, color=COLORES, alpha=0.85, width=0.6,
               edgecolor="white", linewidth=1.5)

for i, (m, s, color) in enumerate(zip(medianas, stats, COLORES)):
    ax1.text(i, m + 0.008, f"{m:.2f}", ha="center", fontsize=12,
             fontweight="bold", color="#333333")
    ax1.text(i, 5.95, f"n={s['n']}", ha="center", fontsize=9.5,
             color="#555555", fontweight="bold")

# Flechas de brecha
ax1.annotate("", xy=(0, medianas[0]), xytext=(1, medianas[1]),
             arrowprops=dict(arrowstyle="<->", color="#C62828", lw=2))
ax1.text(0.5, (medianas[0]+medianas[1])/2 + 0.008,
         f"Δ={brecha_j:+.2f}", ha="center", fontsize=10,
         fontweight="bold", color="#C62828")

ax1.annotate("", xy=(2, medianas[2]), xytext=(3, medianas[3]),
             arrowprops=dict(arrowstyle="<->", color="#C62828", lw=2))
ax1.text(2.5, (medianas[2]+medianas[3])/2 + 0.008,
         f"Δ={brecha_h:+.2f}", ha="center", fontsize=10,
         fontweight="bold", color="#C62828")

# Separador visual
ax1.axvline(1.5, color="#CCCCCC", linewidth=1, linestyle="--", alpha=0.7)
ax1.text(0.5, 5.92, "JORNADA", ha="center", fontsize=11,
         fontweight="bold", color="#333333")
ax1.text(2.5, 5.92, "HONORARIO", ha="center", fontsize=11,
         fontweight="bold", color="#333333")

ax1.set_xticks(x)
ax1.set_xticklabels([s["label"] for s in stats], fontsize=10)
ax1.set_ylabel("SAT Nota (mediana por docente)")
ax1.set_ylim(5.9, max(medianas) + 0.06)
ax1.set_title("Mediana SAT por grupo", pad=10)
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)

import matplotlib.patches as mpatches
p1 = mpatches.Patch(color=C_FORM, alpha=0.85, label="Formado")
p2 = mpatches.Patch(color=C_NO,   alpha=0.85, label="Sin formación")
ax1.legend(handles=[p1,p2], fontsize=10, loc="lower right")

# Panel B — Boxplot
datos_box = []
for label, tipo, formado in GRUPOS:
    datos_box.append(df_sat[(df_sat["tipo"]==tipo) & (df_sat["formado"]==formado)]["sat_nota"].dropna().values)

bp = ax2.boxplot(datos_box, patch_artist=True,
                 medianprops=dict(color="black", linewidth=2.5),
                 whiskerprops=dict(linewidth=1.5),
                 capprops=dict(linewidth=1.5),
                 flierprops=dict(marker="o", markersize=3, alpha=0.35))

for patch, color in zip(bp["boxes"], COLORES):
    patch.set_facecolor(color); patch.set_alpha(0.75)

for i, (d, s) in enumerate(zip(datos_box, stats)):
    med = np.median(d)
    ax2.text(i+1, med + 0.02, f"{med:.2f}", ha="center", fontsize=9.5,
             fontweight="bold", color="black")

ax2.axvline(2.5, color="#CCCCCC", linewidth=1, linestyle="--", alpha=0.7)
ax2.text(1.5, ax2.get_ylim()[1] if ax2.get_ylim()[1]>6 else 7.2,
         "JORNADA", ha="center", fontsize=11, fontweight="bold", color="#333333")
ax2.text(3.5, ax2.get_ylim()[1] if ax2.get_ylim()[1]>6 else 7.2,
         "HONORARIO", ha="center", fontsize=11, fontweight="bold", color="#333333")

labels_box = [s["label"]+f"\n(n={s['n']})" for s in stats]
ax2.set_xticks([1,2,3,4])
ax2.set_xticklabels(labels_box, fontsize=9)
ax2.set_ylabel("SAT Nota por docente")
ax2.set_title("Distribución SAT por grupo", pad=10)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nGuardado: {OUT}")
