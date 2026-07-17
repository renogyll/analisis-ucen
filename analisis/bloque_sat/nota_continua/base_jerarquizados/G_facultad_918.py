import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os

BASE = os.path.dirname(__file__)
OUT  = os.path.join(BASE, "G_facultad_918.png")

matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 12, "axes.titlesize": 15, "axes.labelsize": 13,
    "xtick.labelsize": 11, "ytick.labelsize": 11, "legend.fontsize": 11,
})

doc = pd.read_csv(os.path.join(BASE,"..","PROCESADO","docente_918.csv"),
                  encoding="utf-8-sig", dtype={"rut_key": str})
doc["rut_key"] = doc["rut_key"].str.strip()

# Solo los que tienen unidad_facultad
con_fac = doc[doc["unidad_facultad"].notna()].copy()
n_total = len(doc)
n_con   = len(con_fac)
n_sin   = n_total - n_con

# Limpiar y abreviar nombres
def map_fac(s):
    if not isinstance(s, str): return "Otras\nunidades"
    su = s.upper()
    if "MEDICINA"    in su: return "Medicina y\nCs. Salud"
    if "INVEST"      in su: return "VRIIP"
    if "INGENIER"    in su: return "Ingeniería y\nArquitectura"
    if "EDUCACI"     in su: return "Educación"
    if "ECONOM"      in su: return "Economía, Gob.\ny Comun."
    if "DERECHO"     in su: return "Derecho y\nHumanidades"
    return "Otras\nunidades"

abrev = {
    "Medicina y\nCs. Salud":          "FAC. DE MEDICINA Y CIENCIAS DE LA SALUD",
    "VRIIP":                           "VICERRECTORIA DE INVEST, INNOV Y POSTGRA",
    "Ingeniería y\nArquitectura":      "FAC. DE INGENIERÍA Y ARQUITECTURA",
    "Educación":                       "FAC. DE EDUCACIÓN",
    "Economía, Gob.\ny Comun.":        "FAC. ECONOMÍA, GOBIERNO Y COMUNICACIONES",
    "Derecho y\nHumanidades":          "FAC. DERECHO Y HUMANIDADES",
}
con_fac["fac_label"] = con_fac["unidad_facultad"].apply(map_fac)

ORD = [
    "Medicina y\nCs. Salud",
    "VRIIP",
    "Ingeniería y\nArquitectura",
    "Educación",
    "Economía, Gob.\ny Comun.",
    "Derecho y\nHumanidades",
    "Otras\nunidades",
]
COLORES = [
    "#1565C0","#6A1B9A","#00838F",
    "#2E7D32","#E65100","#C62828","#78909C",
]

tbl = con_fac.groupby("fac_label")["rut_key"].count().reindex(ORD).fillna(0).astype(int)

# ── Cascada consola ────────────────────────────────────────────────────────────
print("=" * 65)
print("  UNIVERSO — Caracterización Docente por Unidad/Facultad")
print("=" * 65)
print(f"  917 docentes jerarquizados (Universo 917)")
print(f"    ├── {n_con} CON unidad/facultad  ← perfil completo (dotación)")
for label, n in tbl.items():
    nombre_largo = [k for k,v in abrev.items() if v==label]
    nombre = nombre_largo[0] if nombre_largo else label.replace('\n',' ')
    print(f"    │     ├── {n:3d}  {nombre}")
print(f"    └── {n_sin} SIN unidad/facultad  ← solo nómina")
print("=" * 65)

# ── Figura ────────────────────────────────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7))
fig.suptitle(
    "Caracterización por Unidad/Facultad — Cuerpo Docente Jerarquizado UCEN\n"
    f"Universo 917 · {n_con} docentes con dato de unidad/facultad (424 sin dato — solo nómina)",
    fontsize=14, fontweight="bold")

vals = [int(tbl.get(o, 0)) for o in ORD]
pcts = [100*v/n_con for v in vals]
x    = np.arange(len(ORD))

# Panel A — Barras horizontales
ax1.barh(range(len(ORD)), vals, color=COLORES, alpha=0.88, edgecolor="white")
for i, (v, p) in enumerate(zip(vals, pcts)):
    ax1.text(v + 1, i, f"{v}  ({p:.1f}%)", va="center",
             fontsize=11, fontweight="bold", color="#222222")
ax1.set_yticks(range(len(ORD)))
ax1.set_yticklabels(ORD, fontsize=11)
ax1.set_xlabel("N° docentes")
ax1.set_title("Distribución absoluta por unidad/facultad", pad=10)
ax1.set_xlim(0, max(vals) * 1.28)
ax1.invert_yaxis()
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)

# Panel B — Torta
wedges, texts, autotexts = ax2.pie(
    vals, labels=ORD, colors=COLORES,
    autopct=lambda p: f"{p:.1f}%" if p > 3 else "",
    startangle=90, counterclock=False,
    wedgeprops=dict(edgecolor="white", linewidth=2),
    textprops=dict(fontsize=10),
    pctdistance=0.75,
)
for at in autotexts:
    at.set_fontsize(10)
    at.set_fontweight("bold")
    at.set_color("white")
ax2.set_title("Participación porcentual", pad=10)

plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nGuardado: {OUT}")

fac_mayor = ORD[vals.index(max(vals))]
fac_mayor_n = max(vals)
fac_mayor_p = 100*fac_mayor_n/n_con
top2_n = sum(sorted(vals, reverse=True)[:2])

print(f"""
BAJADAS
• La Facultad de Medicina y Ciencias de la Salud concentra la mayor parte
  del cuerpo docente jerarquizado con datos de unidad ({fac_mayor_n} docentes,
  {fac_mayor_p:.1f}%), seguida por la Vicerrectoría de Investigación, Innovación
  y Postgrado (VRIIP) con 77 docentes. Las dos unidades mayores agrupan el
  {100*top2_n/n_con:.0f}% del total con perfil completo, reflejando la vocación
  científico-profesional de la institución.

• Las facultades de Ingeniería y Arquitectura, Educación, Economía y Derecho
  presentan tamaños similares (43–72 docentes), configurando un cuerpo
  académico distribuido en áreas disciplinares diversas. Los 424 docentes
  sin dato de unidad/facultad pertenecen exclusivamente al grupo de solo
  nómina y requieren validación adicional para su clasificación definitiva.
""")
