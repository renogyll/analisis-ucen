import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os

BASE = os.path.dirname(__file__)
OUT  = os.path.join(BASE, "G_jerarquia_918.png")

matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11, "axes.titlesize": 14, "axes.labelsize": 12,
})

doc917 = pd.read_csv(os.path.join(BASE,"..","PROCESADO","docente_918.csv"),
                     encoding="utf-8-sig", dtype={"rut_key": str})
doc917["rut_key"] = doc917["rut_key"].str.strip()

ORD_JER = [
    "INSTRUCTOR REGULAR",
    "INSTRUCTOR DOCENTE",
    "ASISTENTE REGULAR",
    "ASISTENTE DOCENTE",
    "ASOCIADO REGULAR",
    "ASOCIADO DOCENTE",
    "TITULAR REGULAR",
    "TITULAR DOCENTE",
]
ABREV = {
    "INSTRUCTOR REGULAR": "Instructor\nRegular",
    "INSTRUCTOR DOCENTE": "Instructor\nDocente",
    "ASISTENTE REGULAR":  "Asist.\nRegular",
    "ASISTENTE DOCENTE":  "Asist.\nDocente",
    "ASOCIADO REGULAR":   "Asoc.\nRegular",
    "ASOCIADO DOCENTE":   "Asoc.\nDocente",
    "TITULAR REGULAR":    "Titular\nRegular",
    "TITULAR DOCENTE":    "Titular\nDocente",
}
COLORES = ["#42A5F5","#1976D2","#66BB6A","#388E3C",
           "#FFA726","#E65100","#EF5350","#B71C1C"]

# Para los 2 docentes de origen=dotacion, jerarquia (nómina) es NaN
# → usar jerarquia_dot (sin prefijo "PROFESOR ")
doc917["jer_efectiva"] = doc917["jerarquia"].fillna(
    doc917["jerarquia_dot"].str.replace(r"^PROFESOR\s+", "", regex=True)
)
doc917.loc[doc917["jer_efectiva"] == "NO INFORMA", "jer_efectiva"] = None

df = doc917[doc917["jer_efectiva"].notna()].copy()
df["jerarquia"] = df["jer_efectiva"]
n_total = len(doc917)
n_ok    = len(df)

jer_validos = [j for j in ORD_JER if j in df["jerarquia"].values]
conteo = df["jerarquia"].value_counts()

vals  = [int(conteo.get(j, 0)) for j in jer_validos]
pcts  = [100*v/n_ok for v in vals]
abrevs = [ABREV[j] for j in jer_validos]
colores = COLORES[:len(jer_validos)]

# ── Cascada ───────────────────────────────────────────────────────────────────
print("=" * 65)
print("  DISTRIBUCIÓN DE JERARQUÍA ACADÉMICA (Universo 917)")
print("=" * 65)
print(f"  917 docentes jerarquizados (Universo 917)")
print(f"    ├── {n_ok} con jerarquía informada")
for j, v, p in zip(jer_validos, vals, pcts):
    print(f"    │     ├── {ABREV[j].replace(chr(10),' '):22}: n={v:3d} ({p:.1f}%)")
print(f"    └── {n_total - n_ok} sin jerarquía informada")
print("=" * 65)

# ── Figura: dos paneles — barras absolutas + % acumulado ─────────────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7),
                                gridspec_kw={"width_ratios": [1.4, 1]})
fig.suptitle(
    "Distribución de la Jerarquía Académica — Cuerpo Docente Jerarquizado UCEN\n"
    f"Universo 917 · {n_ok} docentes con jerarquía informada",
    fontsize=13, fontweight="bold")

# Panel A — Barras horizontales ordenadas de mayor a menor jerarquía
x = np.arange(len(jer_validos))
bars = ax1.barh(x[::-1], vals, color=colores, alpha=0.88,
                height=0.62, edgecolor="white")

for i, (v, p, color) in enumerate(zip(vals[::-1], pcts[::-1], colores[::-1])):
    ax1.text(v + 3, i, f"{v}  ({p:.1f}%)",
             va="center", fontsize=11, fontweight="bold", color=color)

ax1.set_yticks(x)
ax1.set_yticklabels(abrevs[::-1], fontsize=10, fontweight="bold")
ax1.set_xlabel("N° de docentes")
ax1.set_title("Distribución por nivel de jerarquía\n(de mayor a menor rango)", pad=10)
ax1.set_xlim(0, max(vals) * 1.38)
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)

# Panel B — Pirámide/escalera: % acumulado ascendente
pct_acum = np.cumsum(pcts)
ax2.barh(x, pcts, color=colores, alpha=0.75, height=0.62, edgecolor="white")
ax2.step(pct_acum, x - 0.31, where="post",
         color="#333333", linewidth=2, linestyle="--", alpha=0.7)

for i, (p, pa, color) in enumerate(zip(pcts, pct_acum, colores)):
    ax2.text(p/2, i, f"{p:.1f}%", va="center", ha="center",
             fontsize=9.5, fontweight="bold", color="white")

ax2.set_yticks(x)
ax2.set_yticklabels(abrevs, fontsize=10, fontweight="bold")
ax2.set_xlabel("% del universo")
ax2.set_title("Peso relativo por jerarquía\n(% sobre universo con dato)", pad=10)
ax2.set_xlim(0, max(pcts) * 1.4)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nGuardado: {OUT}")

# ── Bajadas ───────────────────────────────────────────────────────────────────
d = {j: v for j, v in zip(jer_validos, vals)}
p_dict = {j: p for j, p in zip(jer_validos, pcts)}

n_id  = d.get("INSTRUCTOR DOCENTE", 0)
n_ad  = d.get("ASISTENTE DOCENTE", 0)
n_aod = d.get("ASOCIADO DOCENTE", 0)
p_id  = p_dict.get("INSTRUCTOR DOCENTE", 0)
p_ad  = p_dict.get("ASISTENTE DOCENTE", 0)
p_aod = p_dict.get("ASOCIADO DOCENTE", 0)
pct_docente = p_id + p_ad + p_aod

print(f"""
BAJADAS
• La jerarquía de **Instructor Docente** es la más numerosa del
  escalafón (n={n_id}, {p_id:.1f}%), seguida de **Asistente Docente**
  (n={n_ad}, {p_ad:.1f}%) y **Asociado Docente** (n={n_aod}, {p_aod:.1f}%).
  En conjunto, los tres niveles "Docente" concentran el {pct_docente:.1f}%
  del universo jerarquizado, confirmando que la carrera académica
  en UCEN se desarrolla predominantemente por la vía Docente.

• Los niveles superiores — Titular Regular y Titular Docente —
  representan el {p_dict.get("TITULAR REGULAR",0)+p_dict.get("TITULAR DOCENTE",0):.1f}%
  del cuerpo (n={d.get("TITULAR REGULAR",0)+d.get("TITULAR DOCENTE",0)}), lo que
  refleja la exigencia acumulativa de la carrera académica: pocos
  docentes alcanzan el escalón más alto, y quienes lo hacen exhiben
  trayectorias de largo aliento dentro de la institución.
""")
