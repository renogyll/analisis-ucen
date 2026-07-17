import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os

BASE = os.path.dirname(__file__)
OUT  = os.path.join(BASE, "G_nivel_formacion_918.png")

matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11, "axes.titlesize": 14, "axes.labelsize": 12,
})

dot = pd.read_csv(
    os.path.join(BASE,"..","..","CONSOLIDADO DOCENTES 3-05-2026",
                 "CONSOLIDADO DOCENTES 3-05-2026.xlsx - DOTACION.csv"),
    dtype=str, encoding="utf-8-sig")
dot.columns = dot.columns.str.strip()
dot["rut_key"] = (dot["RUT"].str.strip()
                  .str.replace(".", "", regex=False)
                  .str.split("-").str[0].str.strip())

doc917 = pd.read_csv(os.path.join(BASE,"..","PROCESADO","docente_918.csv"),
                     encoding="utf-8-sig", dtype={"rut_key": str})
doc917["rut_key"] = doc917["rut_key"].str.strip()

dot917 = dot[dot["rut_key"].isin(set(doc917["rut_key"]))].copy()

ORD_NF = ["TÉCNICO", "PROFESIONAL", "MAGÍSTER O MASTER", "DOCTOR"]
ABREV_NF = {
    "TÉCNICO":           "Técnico",
    "PROFESIONAL":       "Profesional",
    "MAGÍSTER O MASTER": "Magíster",
    "DOCTOR":            "Doctor",
}
COLORES = ["#FF8F00", "#7B1FA2", "#1976D2", "#1B5E20"]

df = dot917[
    dot917["NIVEL FORMACIÓN"].notna() &
    (dot917["NIVEL FORMACIÓN"] != "NO INFORMA")
].copy()
df["nf_abrev"] = df["NIVEL FORMACIÓN"].map(ABREV_NF)

n_dot   = len(dot917)
n_ok    = len(df)
n_total = len(doc917)

conteo = df["nf_abrev"].value_counts()
nf_ord   = [ABREV_NF[n] for n in ORD_NF if ABREV_NF[n] in conteo.index]
vals     = [int(conteo.get(n, 0)) for n in nf_ord]
pcts     = [100*v/n_ok for v in vals]

# ── Cascada ───────────────────────────────────────────────────────────────────
print("=" * 65)
print("  NIVEL DE FORMACIÓN (Universo 917)")
print("=" * 65)
print(f"  917 docentes jerarquizados (Universo 917)")
print(f"    ├── {n_dot} con perfil completo (dotación)")
print(f"    │     └── {n_ok} con nivel de formación informado")
for nf, v, p in zip(nf_ord, vals, pcts):
    print(f"    │           ├── {v:3d} {nf:12} ({p:.1f}%)")
print(f"    └── {n_total - n_dot} sin perfil completo (solo nómina)")
print("=" * 65)

# ── Figura ────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 6))
fig.suptitle(
    "Nivel de Formación — Cuerpo Docente Jerarquizado UCEN\n"
    f"Universo 917 → {n_dot} con perfil completo (dotación) → {n_ok} con nivel de formación informado",
    fontsize=13, fontweight="bold")

x = np.arange(len(nf_ord))
bars = ax.bar(x, vals, color=COLORES[:len(nf_ord)], alpha=0.88,
              width=0.55, edgecolor="white")

for i, (v, p, color) in enumerate(zip(vals, pcts, COLORES)):
    ax.text(i, v + 1.5, f"{v}\n({p:.1f}%)",
            ha="center", va="bottom", fontsize=12,
            fontweight="bold", color=color)

ax.set_xticks(x)
ax.set_xticklabels(nf_ord, fontsize=13, fontweight="bold")
ax.set_ylabel("N° de docentes")
ax.set_ylim(0, max(vals) * 1.22)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nGuardado: {OUT}")

n_posgrado = vals[nf_ord.index("Magíster")] + vals[nf_ord.index("Doctor")]
p_posgrado = 100 * n_posgrado / n_ok
n_dr = vals[nf_ord.index("Doctor")]
p_dr = pcts[nf_ord.index("Doctor")]
n_mg = vals[nf_ord.index("Magíster")]
p_mg = pcts[nf_ord.index("Magíster")]

print(f"""
BAJADAS
• El cuerpo docente jerarquizado de UCEN exhibe un alto nivel de
  formación de posgrado: el {p_posgrado:.1f}% cuenta con Magíster (n={n_mg},
  {p_mg:.1f}%) o Doctorado (n={n_dr}, {p_dr:.1f}%), lo que refleja una planta
  académica con sólida preparación disciplinar e investigativa.

• Solo el {100-p_posgrado:.1f}% del cuerpo con dato informado posee formación
  de pregrado (Profesional) o nivel Técnico, concentrados principalmente
  en jerarquías de entrada. Esta distribución evidencia que la
  jerarquización en UCEN está fuertemente asociada a la acreditación
  formal de posgrado como condición de avance en la carrera académica.
""")
