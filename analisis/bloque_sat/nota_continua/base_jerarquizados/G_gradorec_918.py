import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os

BASE = os.path.dirname(__file__)
OUT  = os.path.join(BASE, "G_gradorec_918.png")

matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11, "axes.titlesize": 13, "axes.labelsize": 12,
})

doc917 = pd.read_csv(os.path.join(BASE,"..","PROCESADO","docente_918.csv"),
                     encoding="utf-8-sig", dtype={"rut_key": str})
doc917["rut_key"] = doc917["rut_key"].str.strip()

dot = pd.read_csv(
    os.path.join(BASE,"..","..","CONSOLIDADO DOCENTES 3-05-2026",
                 "CONSOLIDADO DOCENTES 3-05-2026.xlsx - DOTACION_CON_GRADOREC.csv"),
    dtype=str, encoding="utf-8-sig")
dot.columns = dot.columns.str.strip()
dot["rut_key"] = (dot["RUT"].str.strip()
                  .str.replace(".", "", regex=False)
                  .str.split("-").str[0].str.strip())

dot917 = dot[dot["rut_key"].isin(set(doc917["rut_key"]))].copy()

# Excluir NO INFORMA
df = dot917[dot917["GRADOREC"].notna() & (dot917["GRADOREC"].str.strip() != "NO INFORMA")].copy()
df["GRADOREC"] = df["GRADOREC"].str.strip()

n_total = len(doc917)
n_dot   = len(dot917)
n_ok    = len(df)
n_ni    = n_dot - n_ok

# Renombrar para legibilidad
RENAME = {
    "(MAG-PRO).": "Magíster\nProfesional",
    "DOC":        "Doctor",
    "(MAG-ACA)":  "Magíster\nAcadémico",
    "PROFESIONAL":"Profesional",
    "POST-DOC":   "Post-Doctor",
    "TECNICO":    "Técnico",
    "DIPLOMA DE ESTUDIOS AVANZADOS (DEA)": "DEA",
    "DIPLOMADO":  "Diplomado",
}
df["grado_label"] = df["GRADOREC"].map(RENAME).fillna(df["GRADOREC"])

conteo = df["grado_label"].value_counts()
grados_ord = conteo.index.tolist()
vals = conteo.values.tolist()
pcts = [100*v/n_ok for v in vals]

COLORES = ["#1976D2","#1B5E20","#6A1B9A","#90A4AE",
           "#E65100","#CFD8DC","#FF8F00","#F57C00"]

# ── Cascada ───────────────────────────────────────────────────────────────────
print("=" * 65)
print("  DISTRIBUCIÓN POR GRADO RECONOCIDO (GRADOREC)")
print("  Universo 917 · Dotación con clasificación de grado")
print("=" * 65)
print(f"  917 docentes jerarquizados")
print(f"    ├── {n_dot} con perfil completo (dotación)")
print(f"    │     ├── {n_ok} con grado clasificado")
for g, v, p in zip(grados_ord, vals, pcts):
    label = g.replace("\n"," ")
    print(f"    │     │     ├── {v:3d} ({p:5.1f}%)  {label}")
print(f"    │     └── {n_ni} NO INFORMA")
print(f"    └── {n_total - n_dot} sin datos de dotación (solo nómina)")
print("=" * 65)

# Agrupar para análisis
n_mag_pro = conteo.get("Magíster\nProfesional", 0)
n_mag_aca = conteo.get("Magíster\nAcadémico", 0)
n_doc     = conteo.get("Doctor", 0)
n_postdoc = conteo.get("Post-Doctor", 0)
n_prof    = conteo.get("Profesional", 0)
n_mag_tot = n_mag_pro + n_mag_aca
pct_mag_pro_of_mag = 100*n_mag_pro/n_mag_tot if n_mag_tot > 0 else 0
pct_postgrado = 100*(n_mag_tot + n_doc + n_postdoc)/n_ok

# ── Figura ────────────────────────────────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7),
                                gridspec_kw={"width_ratios": [1.3, 1]})
fig.suptitle(
    "Distribución por Grado Académico Reconocido (GRADOREC)\n"
    f"Universo 917 → {n_dot} con perfil completo (dotación) → {n_ok} con grado clasificado",
    fontsize=12, fontweight="bold")

# Panel A — Barras horizontales
y = np.arange(len(grados_ord))
bars = ax1.barh(y[::-1], vals, color=COLORES[:len(grados_ord)],
                alpha=0.88, height=0.62, edgecolor="white")
for i, (v, p, color) in enumerate(zip(vals[::-1], pcts[::-1], COLORES[:len(grados_ord)][::-1])):
    ax1.text(v + 2, i, f"{v}  ({p:.1f}%)",
             va="center", fontsize=10.5, fontweight="bold", color=color)
ax1.set_yticks(y)
ax1.set_yticklabels(grados_ord[::-1], fontsize=10, fontweight="bold")
ax1.set_xlabel("N° de docentes")
ax1.set_title("Distribución por grado reconocido", pad=10)
ax1.set_xlim(0, max(vals) * 1.4)
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)

# Panel B — Dona agrupada: Postgrado (Doc+Mag) vs Pregrado
grupos_dona = {
    "Magíster Profesional": n_mag_pro,
    "Magíster Académico":   n_mag_aca,
    "Doctor / Post-Doc":    n_doc + n_postdoc,
    "Profesional / Técnico / Otro": n_prof + conteo.get("Técnico",0) + conteo.get("DEA",0) + conteo.get("Diplomado",0),
}
dona_labels = list(grupos_dona.keys())
dona_vals   = list(grupos_dona.values())
dona_colors = ["#1976D2","#6A1B9A","#1B5E20","#90A4AE"]

wedges, _ = ax2.pie(dona_vals, colors=dona_colors, startangle=90,
                    counterclock=False,
                    wedgeprops=dict(width=0.55, edgecolor="white", linewidth=2.5))

for wedge, lbl, v, color in zip(wedges, dona_labels, dona_vals, dona_colors):
    ang = (wedge.theta2 + wedge.theta1) / 2
    x2 = 1.25 * np.cos(np.radians(ang))
    y2 = 1.25 * np.sin(np.radians(ang))
    ha = "left" if x2 > 0 else "right"
    ax2.annotate(f"{lbl}\n{v} ({100*v/n_ok:.1f}%)",
                 xy=(0.75*np.cos(np.radians(ang)), 0.75*np.sin(np.radians(ang))),
                 xytext=(x2, y2),
                 arrowprops=dict(arrowstyle="-", color="#888", lw=1),
                 fontsize=9, ha=ha, va="center", fontweight="bold", color=color)

ax2.text(0, 0, f"{n_ok}\ndocentes", ha="center", va="center",
         fontsize=13, fontweight="bold", color="#333333")
ax2.set_xlim(-2.1, 2.1)
ax2.set_title("Agrupación por nivel de grado", pad=10)

plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nGuardado: {OUT}")

print(f"""
BAJADAS
• El cuerpo docente jerarquizado de UCEN muestra una fuerte orientación
  hacia el posgrado: el {pct_postgrado:.1f}% de los docentes con grado clasificado
  posee Magíster, Doctorado o Post-Doctorado. Dentro de los magísteres,
  el {pct_mag_pro_of_mag:.0f}% corresponde a Magíster Profesional (n={n_mag_pro}) frente
  al {100-pct_mag_pro_of_mag:.0f}% de Magíster Académico (n={n_mag_aca}), lo que refleja
  una planta académica con énfasis en la aplicación profesional del
  conocimiento más que en la investigación disciplinar pura.

• Los Doctores y Post-Doctores suman {n_doc+n_postdoc} docentes ({100*(n_doc+n_postdoc)/n_ok:.1f}%),
  configurando el núcleo de mayor calificación académica. El segmento
  de nivel Profesional ({n_prof}, {100*n_prof/n_ok:.1f}%) corresponde a docentes
  que aún no cuentan con formación de posgrado, concentrados
  previsiblemente en los rangos de entrada del escalafón.
""")
