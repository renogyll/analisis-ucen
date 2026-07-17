import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib
import numpy as np
import os

BASE = os.path.dirname(__file__)
OUT  = os.path.join(BASE, "G_carga_academica_918.png")

matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 12, "axes.titlesize": 14, "axes.labelsize": 12,
})

doc917 = pd.read_csv(os.path.join(BASE,"..","PROCESADO","docente_918.csv"),
                     encoding="utf-8-sig", dtype={"rut_key": str})
doc917["rut_key"] = doc917["rut_key"].str.strip()

dot = pd.read_csv(os.path.join(BASE,"..","..","PROCESADO",
                               "dotacion_con_clasificacion.csv"),
                  encoding="utf-8-sig", dtype={"rut_key": str})
dot["rut_key"] = dot["rut_key"].str.strip()

# Filtrar al universo 917
dot917 = dot[dot["rut_key"].isin(set(doc917["rut_key"]))].copy()

# ── Mapeo a 4 categorías PEI ──────────────────────────────────────────────────
MAPEO = {
    "DOCENCIA":                  "Docencia",
    "DOCENTE":                   "Docencia",
    "GESTIÓN ACADÉMICA":         "Gestión Directiva Académica",
    "DOCENTE/GESTOR":            "Gestión Directiva Académica",
    "INVESTIGACIÓN/INNOVACIÓN":  "Investigación e Innovación",
    "VCM":                       "Vinculación con el Medio",
}
dot917["categoria_pei"] = dot917["clasificacion"].map(MAPEO).fillna("Sin clasificar")

n_univ = len(doc917)
n_dot  = len(dot917)
n_sin  = n_univ - n_dot

conteo = dot917.groupby("categoria_pei")["rut_key"].count()

CATS = [
    "Docencia",
    "Gestión Directiva Académica",
    "Investigación e Innovación",
    "Vinculación con el Medio",
]
COLORES = ["#1565C0","#6A1B9A","#2E7D32","#E65100"]

vals = [int(conteo.get(c, 0)) for c in CATS]
pcts = [100*v/n_dot for v in vals]

# ── Cascada ───────────────────────────────────────────────────────────────────
print("=" * 65)
print("  DISTRIBUCIÓN DE LA CARGA ACADÉMICA (Universo 917)")
print("=" * 65)
print(f"  917 docentes jerarquizados (Universo 917)")
print(f"    ├── {n_dot} con datos de cargo (perfil completo — dotación)")
for cat, v, p in zip(CATS, vals, pcts):
    print(f"    │     ├── {v:3d} ({p:.1f}%)  {cat}")
print(f"    └── {n_sin} sin datos de cargo (solo nómina — sin dotación)")
print()
print("  Metodología: cargo asignado en dotación → clasificado por")
print("  la contraparte en 6 tipos → reagrupado en 4 categorías PEI.")
print("  Un docente puede ejercer más de una función simultáneamente.")
print("=" * 65)

# ── Figura: dona + barras horizontales ───────────────────────────────────────
fig, (ax_dona, ax_bar) = plt.subplots(1, 2, figsize=(16, 7),
                                       gridspec_kw={"width_ratios": [1, 1.3]})
fig.suptitle(
    "Distribución de la Carga Académica — Cuerpo Docente Jerarquizado UCEN\n"
    f"Universo 917 · {n_dot} docentes con cargo asignado en dotación",
    fontsize=13, fontweight="bold")

# Panel A — Dona
wedges, texts = ax_dona.pie(
    vals, colors=COLORES, startangle=90, counterclock=False,
    wedgeprops=dict(width=0.55, edgecolor="white", linewidth=2.5))

for wedge, cat, v, p, color in zip(wedges, CATS, vals, pcts, COLORES):
    ang  = (wedge.theta2 + wedge.theta1) / 2
    x    = 0.75 * np.cos(np.radians(ang))
    y    = 0.75 * np.sin(np.radians(ang))
    x2   = 1.22 * np.cos(np.radians(ang))
    y2   = 1.22 * np.sin(np.radians(ang))
    ha   = "left" if x2 > 0 else "right"
    ax_dona.annotate(
        f"{cat}\n{v} doc. ({p:.1f}%)",
        xy=(x, y), xytext=(x2, y2),
        arrowprops=dict(arrowstyle="-", color="#888888", lw=1),
        fontsize=9.5, ha=ha, va="center",
        color=color, fontweight="bold")

ax_dona.text(0, 0, f"{n_dot}\ndocentes", ha="center", va="center",
             fontsize=13, fontweight="bold", color="#333333")
ax_dona.set_xlim(-1.9, 1.9)

# Panel B — Barras horizontales con desglose por cargo original
DESGLOSE = {
    "Docencia":                   ["DOCENCIA","DOCENTE"],
    "Gestión Directiva Académica":["GESTIÓN ACADÉMICA","DOCENTE/GESTOR"],
    "Investigación e Innovación": ["INVESTIGACIÓN/INNOVACIÓN"],
    "Vinculación con el Medio":   ["VCM"],
}
y_pos = np.arange(len(CATS))

for i, (cat, color) in enumerate(zip(CATS[::-1], COLORES[::-1])):
    v = int(conteo.get(cat, 0))
    ax_bar.barh(i, v, color=color, alpha=0.85, height=0.55, edgecolor="white")
    ax_bar.text(v + 2, i, f"{v} ({100*v/n_dot:.1f}%)",
                va="center", fontsize=11, fontweight="bold", color=color)

    # Detalle de los cargos que componen la categoría
    sub_tipos = DESGLOSE[cat]
    detalle = []
    for tipo in sub_tipos:
        n_tipo = int((dot917["clasificacion"] == tipo).sum())
        if n_tipo > 0:
            detalle.append(f"{tipo.title()}: {n_tipo}")
    if detalle:
        ax_bar.text(3, i - 0.27, " / ".join(detalle),
                    va="center", fontsize=8, color="#666666",
                    fontstyle="italic")

ax_bar.set_yticks(y_pos)
ax_bar.set_yticklabels(CATS[::-1], fontsize=11, fontweight="bold")
ax_bar.set_xlabel("N° de docentes")
ax_bar.set_title("Distribución por función académica\n(detalle de cargo original en cursiva)",
                 pad=10)
ax_bar.set_xlim(0, max(vals) * 1.35)
ax_bar.spines["top"].set_visible(False)
ax_bar.spines["right"].set_visible(False)

# Nota metodológica
fig.text(0.5, 0.01,
         "Nota: clasificación basada en el cargo en dotación (493 de 917 docentes). "
         "Los 424 de solo nómina no tienen cargo asignado y quedan fuera de esta distribución. "
         "Un docente puede ejercer más de una función simultáneamente.",
         ha="center", fontsize=8.5, color="#666666", fontstyle="italic")

plt.tight_layout(rect=[0, 0.05, 1, 0.97])
plt.savefig(OUT, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nGuardado: {OUT}")

print(f"""
BAJADAS
• La función de **Docencia** concentra la mayor proporción del cuerpo
  jerarquizado con perfil completo ({vals[0]} docentes, {pcts[0]:.1f}%),
  confirmando que la actividad de aula es el eje central de la carga
  académica en UCEN. La **Gestión Directiva** agrupa a {vals[1]} docentes
  ({pcts[1]:.1f}%) que combinan funciones de dirección de carrera,
  coordinación o secretaría de estudios con su rol docente.

• Las funciones de **Investigación e Innovación** ({vals[2]} doc., {pcts[2]:.1f}%)
  y **Vinculación con el Medio** ({vals[3]} doc., {pcts[3]:.1f}%) representan
  en conjunto el {pcts[2]+pcts[3]:.1f}% del cuerpo con cargo asignado,
  evidenciando que casi 1 de cada 4 docentes jerarquizados ejerce
  funciones más allá del aula — dato relevante para la acreditación
  institucional y el cumplimiento del modelo educativo declarado en el PEI.
""")
