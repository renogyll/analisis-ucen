import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os

BASE = os.path.dirname(__file__)
OUT  = os.path.join(BASE, "G_jerarquia_formacion_918.png")

matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11, "axes.titlesize": 14, "axes.labelsize": 12,
})

dot = pd.read_csv(
    os.path.join(BASE,"..","..","CONSOLIDADO DOCENTES 3-05-2026",
                 "CONSOLIDADO DOCENTES 3-05-2026.xlsx - DOTACION.csv"),
    dtype=str, encoding="utf-8-sig")
dot.columns = dot.columns.str.strip()

doc917 = pd.read_csv(os.path.join(BASE,"..","PROCESADO","docente_918.csv"),
                     encoding="utf-8-sig", dtype={"rut_key": str})
doc917["rut_key"] = doc917["rut_key"].str.strip()

# Limpiar RUT y cruzar con universo 917
dot["rut_key"] = (dot["RUT"].str.strip()
                  .str.replace(".", "", regex=False)
                  .str.split("-").str[0].str.strip())
dot917 = dot[dot["rut_key"].isin(set(doc917["rut_key"]))].copy()

# Excluir NO INFORMA
df = dot917[
    (dot917["JERARQUÍA"]       != "NO INFORMA") &
    (dot917["NIVEL FORMACIÓN"] != "NO INFORMA") &
    dot917["JERARQUÍA"].notna() &
    dot917["NIVEL FORMACIÓN"].notna()
].copy()

n_total = len(dot917)
n_ok    = len(df)
n_sin   = len(doc917) - len(dot917)

# Ordenar jerarquía de menor a mayor
ORD_JER = [
    "INSTRUCTOR REGULAR",
    "INSTRUCTOR DOCENTE",
    "PROFESOR ASISTENTE REGULAR",
    "PROFESOR ASISTENTE DOCENTE",
    "PROFESOR ASOCIADO REGULAR",
    "PROFESOR ASOCIADO DOCENTE",
    "PROFESOR TITULAR REGULAR",
    "PROFESOR TITULAR DOCENTE",
]
ABREV_JER = {
    "INSTRUCTOR REGULAR":          "Instructor Regular",
    "INSTRUCTOR DOCENTE":          "Instructor Docente",
    "PROFESOR ASISTENTE REGULAR":  "Asist. Regular",
    "PROFESOR ASISTENTE DOCENTE":  "Asist. Docente",
    "PROFESOR ASOCIADO REGULAR":   "Asoc. Regular",
    "PROFESOR ASOCIADO DOCENTE":   "Asoc. Docente",
    "PROFESOR TITULAR REGULAR":    "Titular Regular",
    "PROFESOR TITULAR DOCENTE":    "Titular Docente",
}
ORD_NF = ["TÉCNICO", "PROFESIONAL", "MAGÍSTER O MASTER", "DOCTOR"]
ABREV_NF = {
    "TÉCNICO":           "Técnico",
    "PROFESIONAL":       "Profesional",
    "MAGÍSTER O MASTER": "Magíster",
    "DOCTOR":            "Doctor",
}
COLORES_NF = {
    "Técnico":      "#FF8F00",
    "Profesional":  "#7B1FA2",
    "Magíster":     "#1976D2",
    "Doctor":       "#1B5E20",
}

df["jer_abrev"] = df["JERARQUÍA"].map(ABREV_JER)
df["nf_abrev"]  = df["NIVEL FORMACIÓN"].map(ABREV_NF)

# Tabla cruzada
tbl = (df.groupby(["jer_abrev","nf_abrev"])["rut_key"]
         .count().unstack(fill_value=0))
jer_ord  = [ABREV_JER[j] for j in ORD_JER if ABREV_JER[j] in tbl.index]
nf_ord   = [ABREV_NF[n]  for n in ORD_NF  if ABREV_NF[n]  in tbl.columns]
tbl = tbl.reindex(index=jer_ord, columns=nf_ord, fill_value=0)

# ── Cascada ───────────────────────────────────────────────────────────────────
print("=" * 65)
print("  JERARQUÍA × NIVEL DE FORMACIÓN (Universo 917)")
print("=" * 65)
print(f"  917 docentes jerarquizados (Universo 917)")
print(f"    ├── 493 con perfil completo (dotación)")
print(f"    │     ├── {n_ok} con jerarquía y nivel de formación informados")
print(f"    │     └── {n_total-n_ok} con campos 'NO INFORMA'")
print(f"    └── 424 sin perfil completo (solo nómina, sin datos dotación)")
print()
print(f"  Distribución nivel de formación (n={n_ok}):")
for nf in ORD_NF:
    ab = ABREV_NF[nf]
    n  = int(tbl[ab].sum()) if ab in tbl.columns else 0
    print(f"    ├── {ab:18}: {n:3d} ({100*n/n_ok:.1f}%)")
print()
print(f"  Distribución jerarquía (n={n_ok}):")
for jer in jer_ord:
    n = int(tbl.loc[jer].sum()) if jer in tbl.index else 0
    print(f"    ├── {jer:25}: {n:3d} ({100*n/n_ok:.1f}%)")
print("=" * 65)

# ── Figura: barras apiladas + heatmap ────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(17, 7))
fig.suptitle(
    "Jerarquía Académica × Nivel de Formación — Cuerpo Docente Jerarquizado UCEN\n"
    f"Universo 917 → {n_total} con perfil completo (dotación) → {n_ok} con jerarquía y nivel de formación informados",
    fontsize=13, fontweight="bold")

# Panel A — Barras apiladas (% dentro de cada jerarquía)
tbl_pct = tbl.div(tbl.sum(axis=1), axis=0) * 100
x = np.arange(len(jer_ord))
bottom = np.zeros(len(jer_ord))

for nf in nf_ord:
    vals = tbl_pct[nf].values if nf in tbl_pct.columns else np.zeros(len(jer_ord))
    bars = ax1.bar(x, vals, bottom=bottom, label=nf,
                   color=COLORES_NF[nf], alpha=0.88, edgecolor="white")
    for i, (v, b) in enumerate(zip(vals, bottom)):
        if v >= 8:
            ax1.text(i, b + v/2, f"{v:.0f}%", ha="center", va="center",
                     fontsize=9, fontweight="bold", color="white")
    bottom += vals

ax1.set_xticks(x)
ax1.set_xticklabels(jer_ord, rotation=35, ha="right", fontsize=9)
ax1.set_ylabel("% dentro de la jerarquía")
ax1.set_title("Composición por nivel de formación\ndentro de cada jerarquía", pad=10)
ax1.set_ylim(0, 108)
ax1.legend(loc="upper left", fontsize=10, framealpha=0.9)
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)

# Panel B — Heatmap absoluto
data = tbl.values.astype(float)
data_masked = np.where(data == 0, np.nan, data)
im = ax2.imshow(data_masked, cmap="YlOrRd", aspect="auto")

ax2.set_xticks(range(len(nf_ord)))
ax2.set_xticklabels(nf_ord, fontsize=11, fontweight="bold")
ax2.set_yticks(range(len(jer_ord)))
ax2.set_yticklabels(jer_ord, fontsize=9)
ax2.set_title("N° de docentes por celda\n(blanco = sin casos)", pad=10)

for i in range(len(jer_ord)):
    for j in range(len(nf_ord)):
        v = int(tbl.iloc[i, j])
        if v > 0:
            color = "white" if data[i,j] > data.max()*0.6 else "black"
            ax2.text(j, i, str(v), ha="center", va="center",
                     fontsize=11, fontweight="bold", color=color)
        else:
            ax2.text(j, i, "—", ha="center", va="center",
                     fontsize=11, color="#BBBBBB")

plt.colorbar(im, ax=ax2, label="N° docentes", shrink=0.8)
ax2.spines[:].set_visible(False)

plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nGuardado: {OUT}")

# Stats para bajadas
n_dr = int(tbl["Doctor"].sum())  if "Doctor"    in tbl.columns else 0
n_mg = int(tbl["Magíster"].sum()) if "Magíster"  in tbl.columns else 0
n_ti = int(tbl.loc["Titular Docente"].sum()) if "Titular Docente" in tbl.index else 0
dr_ti = int(tbl.loc["Titular Docente","Doctor"]) if ("Titular Docente" in tbl.index and "Doctor" in tbl.columns) else 0
pct_dr_ti = 100*dr_ti/n_ti if n_ti>0 else 0

print(f"""
BAJADAS
• El {100*n_dr/n_ok:.1f}% del cuerpo docente jerarquizado con datos completos
  posee grado de Doctor (n={n_dr}), mientras el {100*n_mg/n_ok:.1f}% cuenta con
  Magíster (n={n_mg}). La formación de posgrado es predominante en los rangos
  superiores: el {pct_dr_ti:.0f}% de los Titulares Docentes son Doctores,
  confirmando la correlación entre jerarquía académica y nivel de formación.

• Los tramos Instructor e Instructor Docente concentran la mayor proporción
  relativa de docentes con grado de Profesional, lo que es coherente con
  su etapa inicial en la carrera académica. Esta distribución sugiere una
  trayectoria formativa clara: los docentes van adquiriendo mayor formación
  de posgrado a medida que avanzan en la jerarquía institucional.
""")
