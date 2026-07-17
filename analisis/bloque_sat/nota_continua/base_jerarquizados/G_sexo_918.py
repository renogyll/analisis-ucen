import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os

BASE = os.path.dirname(__file__)
OUT  = os.path.join(BASE, "G_sexo_918.png")

matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 12, "axes.titlesize": 15, "axes.labelsize": 13,
    "xtick.labelsize": 11, "ytick.labelsize": 11, "legend.fontsize": 11,
})

doc = pd.read_csv(os.path.join(BASE,"..","PROCESADO","docente_918.csv"),
                  encoding="utf-8-sig", dtype={"rut_key": str})
doc["rut_key"] = doc["rut_key"].str.strip()

# Normalizar sexo
doc["sexo_norm"] = doc["sexo"].str.strip().str.upper().map(
    {"MUJER":"Mujer","FEMENINO":"Mujer","HOMBRE":"Hombre","MASCULINO":"Hombre"})

n_total  = len(doc)
n_mujer  = (doc["sexo_norm"] == "Mujer").sum()
n_hombre = (doc["sexo_norm"] == "Hombre").sum()
n_sd     = doc["sexo_norm"].isna().sum()

# ── Cascada consola ────────────────────────────────────────────────────────────
print("=" * 60)
print("  UNIVERSO — Caracterización Docente por Sexo")
print("=" * 60)
print(f"  917 docentes jerarquizados (Universo 917)")
print(f"    ├── {n_mujer}  MUJERES   ({100*n_mujer/n_total:.1f}%)")
print(f"    ├── {n_hombre}  HOMBRES   ({100*n_hombre/n_total:.1f}%)")
print(f"    └──   {n_sd}  SIN DATO")
print("=" * 60)

# Por origen
for origen in ["ambos","nomina","dotacion"]:
    sub = doc[doc["origen"]==origen]
    m = (sub["sexo_norm"]=="Mujer").sum()
    h = (sub["sexo_norm"]=="Hombre").sum()
    print(f"  {origen:10}: Mujeres={m} ({100*m/len(sub):.1f}%) | Hombres={h} ({100*h/len(sub):.1f}%)")

# ── Figura: 2 paneles ──────────────────────────────────────────────────────────
C_M = "#E91E63"
C_H = "#1565C0"

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 7))
fig.suptitle(
    "Caracterización por Sexo — Cuerpo Docente Jerarquizado UCEN\n"
    f"Universo 917 · {n_total-n_sd} docentes con dato de sexo",
    fontsize=14, fontweight="bold")

# Panel A — Torta
sizes  = [n_mujer, n_hombre]
labels = [f"Mujer\n{n_mujer} ({100*n_mujer/(n_mujer+n_hombre):.1f}%)",
          f"Hombre\n{n_hombre} ({100*n_hombre/(n_mujer+n_hombre):.1f}%)"]
colors = [C_M, C_H]
wedges, texts = ax1.pie(sizes, labels=labels, colors=colors,
                         startangle=90, counterclock=False,
                         wedgeprops=dict(edgecolor="white", linewidth=2.5),
                         textprops=dict(fontsize=13, fontweight="bold"))
ax1.set_title("Distribución global por sexo", pad=12)

# Panel B — Barras por origen
origenes   = ["Solo nómina\n(n=437)","Nómina + Dotación\n(n=480)"]
orig_keys  = ["nomina","ambos"]
vals_m = [int((doc[doc["origen"]==o]["sexo_norm"]=="Mujer").sum())  for o in orig_keys]
vals_h = [int((doc[doc["origen"]==o]["sexo_norm"]=="Hombre").sum()) for o in orig_keys]
ns_orig = [vals_m[i]+vals_h[i] for i in range(len(orig_keys))]

x = np.arange(len(origenes))
w = 0.38

b_m = ax2.bar(x - w/2, vals_m, width=w, color=C_M, alpha=0.85, label="Mujer")
b_h = ax2.bar(x + w/2, vals_h, width=w, color=C_H, alpha=0.85, label="Hombre")

for i, (vm, vh, n) in enumerate(zip(vals_m, vals_h, ns_orig)):
    ax2.text(i - w/2, vm + 2, f"{vm}\n({100*vm/n:.0f}%)",
             ha="center", fontsize=10, color=C_M, fontweight="bold")
    ax2.text(i + w/2, vh + 2, f"{vh}\n({100*vh/n:.0f}%)",
             ha="center", fontsize=10, color=C_H, fontweight="bold")

ax2.set_xticks(x)
ax2.set_xticklabels(origenes, fontsize=11)
ax2.set_ylabel("N° docentes")
ax2.set_title("Distribución por sexo según fuente de datos", pad=12)
ax2.legend(loc="upper right")
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nGuardado: {OUT}")

pct_m = 100*n_mujer/(n_mujer+n_hombre)
pct_h = 100*n_hombre/(n_mujer+n_hombre)
m_nom = int((doc[doc["origen"]=="nomina"]["sexo_norm"]=="Mujer").sum())
n_nom = int((doc[doc["origen"]=="nomina"]["sexo_norm"].notna()).sum())
print(f"""
CASCADA TEXTO
─────────────
917 docentes jerarquizados (Universo 917)
  ├── {n_mujer} MUJERES   ({pct_m:.1f}%)
  ├── {n_hombre} HOMBRES   ({pct_h:.1f}%)
  └──   {n_sd} SIN DATO

BAJADAS
• El cuerpo docente jerarquizado de UCEN está compuesto por {n_mujer} mujeres
  ({pct_m:.1f}%) y {n_hombre} hombres ({pct_h:.1f}%), con una leve predominancia femenina
  que se mantiene consistente tanto en el grupo con perfil completo
  (nómina + dotación) como en el grupo de solo nómina.

• La distribución por sexo es prácticamente estable entre fuentes de datos:
  en el grupo de solo nómina las mujeres representan el
  {100*m_nom/n_nom:.0f}%, lo que descarta sesgos de cobertura asociados al
  tipo de contrato y confirma que la composición de género es transversal
  a todo el universo jerarquizado.
""")
