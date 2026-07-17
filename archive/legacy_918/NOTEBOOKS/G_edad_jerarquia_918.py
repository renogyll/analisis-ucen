import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os

BASE = os.path.dirname(__file__)
OUT  = os.path.join(BASE, "G_edad_jerarquia_918.png")

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
dot917["edad"] = pd.to_numeric(dot917["EDAD \n(AÑOS)"], errors="coerce")

df = dot917[(dot917["JERARQUÍA"] != "NO INFORMA") & dot917["edad"].notna()].copy()

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
ABREV = {
    "INSTRUCTOR REGULAR":          "Instructor\nRegular",
    "INSTRUCTOR DOCENTE":          "Instructor\nDocente",
    "PROFESOR ASISTENTE REGULAR":  "Asist.\nRegular",
    "PROFESOR ASISTENTE DOCENTE":  "Asist.\nDocente",
    "PROFESOR ASOCIADO REGULAR":   "Asoc.\nRegular",
    "PROFESOR ASOCIADO DOCENTE":   "Asoc.\nDocente",
    "PROFESOR TITULAR REGULAR":    "Titular\nRegular",
    "PROFESOR TITULAR DOCENTE":    "Titular\nDocente",
}

jer_ord  = [j for j in ORD_JER if j in df["JERARQUÍA"].values]
n_total  = len(doc917)
n_dot    = len(dot917)
n_ok     = len(df)
n_sin    = n_total - n_dot

# ── Cascada ───────────────────────────────────────────────────────────────────
print("=" * 65)
print("  EDAD × JERARQUÍA ACADÉMICA (Universo 917)")
print("=" * 65)
print(f"  917 docentes jerarquizados (Universo 917)")
print(f"    ├── 493 con perfil completo (dotación)")
print(f"    │     └── {n_ok} con edad y jerarquía informadas")
for j in jer_ord:
    sub = df[df["JERARQUÍA"] == j]["edad"]
    print(f"    │           ├── {ABREV[j].replace(chr(10),' '):22}: n={len(sub):3d} | "
          f"media={sub.mean():.1f} | mediana={sub.median():.1f} años")
print(f"    └── 424 sin perfil completo (solo nómina)")
print("=" * 65)

# ── Figura ────────────────────────────────────────────────────────────────────
# Gradiente de color: azul (junior) → rojo (senior)
COLORES = ["#42A5F5","#1976D2","#66BB6A","#388E3C",
           "#FFA726","#E65100","#EF5350","#B71C1C"]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
fig.suptitle(
    "Edad × Jerarquía Académica — Cuerpo Docente Jerarquizado UCEN\n"
    f"Universo 917 → {n_dot} con perfil completo (dotación) → {n_ok} con edad y jerarquía informadas",
    fontsize=12, fontweight="bold")

# Panel A — Boxplot por jerarquía
datos_box = [df[df["JERARQUÍA"] == j]["edad"].dropna().values for j in jer_ord]
labels_box = [ABREV[j] for j in jer_ord]

bp = ax1.boxplot(datos_box, patch_artist=True,
                 medianprops=dict(color="black", linewidth=2.5),
                 whiskerprops=dict(linewidth=1.5),
                 capprops=dict(linewidth=1.5),
                 flierprops=dict(marker="o", markersize=4, alpha=0.5))

for patch, color in zip(bp["boxes"], COLORES[:len(jer_ord)]):
    patch.set_facecolor(color)
    patch.set_alpha(0.75)

# Anotaciones mediana + n
for i, (j, color) in enumerate(zip(jer_ord, COLORES)):
    sub = df[df["JERARQUÍA"] == j]["edad"].dropna()
    ax1.text(i+1, sub.median() + 1.2, f"{sub.median():.0f}",
             ha="center", fontsize=9, fontweight="bold", color="black")
    ax1.text(i+1, ax1.get_ylim()[0] + 0.5 if ax1.get_ylim()[0] > 20 else 22,
             f"n={len(sub)}", ha="center", fontsize=8.5, color=color, fontweight="bold")

ax1.set_xticks(range(1, len(jer_ord)+1))
ax1.set_xticklabels(labels_box, fontsize=9)
ax1.set_ylabel("Edad (años)")
ax1.set_title("Distribución de edad por jerarquía\n(mediana en negrita)", pad=10)
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)

# Panel B — Edad media + IC por jerarquía (línea de tendencia)
medias  = [df[df["JERARQUÍA"]==j]["edad"].mean()   for j in jer_ord]
medianas= [df[df["JERARQUÍA"]==j]["edad"].median() for j in jer_ord]
ns      = [len(df[df["JERARQUÍA"]==j])             for j in jer_ord]
x       = np.arange(len(jer_ord))

ax2.plot(x, medianas, marker="o", color="#333333", linewidth=2.5,
         markersize=10, label="Mediana", zorder=3)
ax2.bar(x, medias, color=COLORES[:len(jer_ord)], alpha=0.6,
        width=0.6, label="Media")

for i, (med, mn, n) in enumerate(zip(medianas, medias, ns)):
    ax2.text(i, med + 0.8, f"{med:.0f}",
             ha="center", fontsize=10, fontweight="bold", color="#333333")

ax2.set_xticks(x)
ax2.set_xticklabels(labels_box, fontsize=9)
ax2.set_ylabel("Edad promedio (años)")
ax2.set_title("Edad media y mediana por jerarquía\n(tendencia de carrera académica)", pad=10)
ax2.set_ylim(30, max(medias)+10)
ax2.legend(loc="upper left", fontsize=10)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)

# Flecha de trayectoria
ax2.annotate("", xy=(len(jer_ord)-1, max(medianas)-2),
             xytext=(0, min(medianas)+2),
             arrowprops=dict(arrowstyle="-|>", color="#666666",
                             lw=1.5, connectionstyle="arc3,rad=0.1"))
ax2.text(len(jer_ord)/2 - 0.5, (max(medianas)+min(medianas))/2,
         "Trayectoria\ncreciente", fontsize=9, color="#666666",
         fontstyle="italic", ha="center")

plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nGuardado: {OUT}")

edad_inst = df[df["JERARQUÍA"]=="INSTRUCTOR DOCENTE"]["edad"].median()
edad_tit  = df[df["JERARQUÍA"]=="PROFESOR TITULAR DOCENTE"]["edad"].median()
brecha    = edad_tit - edad_inst

print(f"""
BAJADAS
• La edad mediana aumenta consistentemente con la jerarquía académica:
  desde {edad_inst:.0f} años en Instructor Docente hasta {edad_tit:.0f} años en
  Titular Docente, una brecha de {brecha:.0f} años que refleja las décadas
  de trayectoria requeridas para alcanzar los niveles superiores del
  escalafón académico UCEN.

• Los tramos Asociado y Titular Docente concentran la mayor dispersión
  etaria (mayor amplitud del boxplot), lo que indica que en los rangos
  superiores coexisten docentes de distintas generaciones — algunos
  que alcanzaron jerarquía tempranamente y otros que lo hicieron
  tras larga trayectoria. Instructor Docente, en cambio, es el grupo
  más joven y homogéneo en edad (mediana {edad_inst:.0f} años).
""")
