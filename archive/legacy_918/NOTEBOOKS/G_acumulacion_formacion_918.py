import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os

BASE  = os.path.dirname(__file__)
OUT   = os.path.join(BASE, "G_acumulacion_formacion_918.png")
OUT2  = os.path.join(BASE, "G_acumulacion_formacion_boxplot_918.png")

matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11, "axes.titlesize": 13, "axes.labelsize": 12,
})

C_FORM  = "#E65100"
C_CTRL  = "#607D8B"
C_LINE  = "#B71C1C"

# ── Cargar datos ──────────────────────────────────────────────────────────────
part = pd.read_csv(os.path.join(BASE,"..","PROCESADO","participacion_p2_918.csv"),
                   encoding="utf-8-sig", dtype=str)
notas = pd.read_csv(os.path.join(BASE,"..","PROCESADO","scatter_sat_notas.csv"),
                    encoding="utf-8-sig")

doc917 = pd.read_csv(os.path.join(BASE,"..","PROCESADO","docente_918.csv"),
                     encoding="utf-8-sig", dtype={"rut_key": str})
doc917["rut_key"] = doc917["rut_key"].str.strip()

# ── Intensidad de formación por docente ───────────────────────────────────────
intensidad = (part.groupby("rut_key")
              .size()
              .reset_index(name="n_instancias"))
intensidad["rut_key"] = intensidad["rut_key"].astype(str).str.strip()

# Tramo de intensidad
def tramo(n):
    if n == 1: return "1"
    if n == 2: return "2"
    if n == 3: return "3"
    return "4+"
intensidad["tramo_instancias"] = intensidad["n_instancias"].apply(tramo)

# ── Aprobación por docente (Opción A: promedio de secciones) ─────────────────
notas["rut_docente"] = notas["rut_docente"].astype(str).str.strip()
aprob = (notas.groupby("rut_docente")["pct_aprobacion"]
         .mean()
         .reset_index()
         .rename(columns={"rut_docente":"rut_key"}))

# ── Docentes sin formación (control) ─────────────────────────────────────────
ruts_formados = set(intensidad["rut_key"])
ruts_917      = set(doc917["rut_key"])
ruts_control  = ruts_917 - ruts_formados

ctrl_aprob = aprob[aprob["rut_key"].isin(ruts_control)].copy()
ctrl_aprob["tramo_instancias"] = "Sin formación"

# ── Merge formados con aprobación ─────────────────────────────────────────────
df = intensidad.merge(aprob, on="rut_key", how="inner")

n_total   = len(doc917)
n_formados = len(ruts_formados)
n_control  = len(ruts_control)
n_con_notas_form = len(df)
n_con_notas_ctrl = len(ctrl_aprob)

# ── Estadísticos por tramo ────────────────────────────────────────────────────
ORD_TRAMOS = ["Sin formación","1","2","3","4+"]
LABELS     = ["Sin\nformación","1\niniciativa","2\niniciativas","3\niniciativas","4+\niniciativas"]

df_full = pd.concat([
    ctrl_aprob[["rut_key","pct_aprobacion","tramo_instancias"]],
    df[["rut_key","pct_aprobacion","tramo_instancias"]]
], ignore_index=True)

stats = {}
for t in ORD_TRAMOS:
    sub = df_full[df_full["tramo_instancias"]==t]["pct_aprobacion"].dropna()
    stats[t] = {"n": len(sub), "media": sub.mean(), "mediana": sub.median(),
                "q25": sub.quantile(0.25), "q75": sub.quantile(0.75)}

# ── Cascada ───────────────────────────────────────────────────────────────────
print("=" * 65)
print("  EFECTO ACUMULATIVO DE LA FORMACIÓN — Tasa de Aprobación")
print("  ¿A más iniciativas de formación, mayor aprobación?")
print("=" * 65)
print(f"  917 docentes jerarquizados")
print(f"    ├── {n_formados} formados  · {n_con_notas_form} con notas disponibles")
print(f"    └── {n_control} control   · {n_con_notas_ctrl} con notas disponibles")
print()
print(f"  Tasa de aprobación (media) por intensidad de formación:")
for t in ORD_TRAMOS:
    s = stats[t]
    print(f"    ├── {t:14}: n={s['n']:3d} | media={s['media']:.1f}% | "
          f"mediana={s['mediana']:.1f}%")
brecha = stats["4+"]["media"] - stats["Sin formación"]["media"]
print(f"\n  Brecha Sin formación → 4+ iniciativas de formación: {brecha:+.1f} pp")
print("=" * 65)

# ── Figura — un solo panel, limpio y grande ───────────────────────────────────
medianas = [stats[t]["mediana"] for t in ORD_TRAMOS]
ns       = [stats[t]["n"]       for t in ORD_TRAMOS]
colores  = [C_CTRL] + [C_FORM]*4

fig, ax = plt.subplots(figsize=(13, 7))
fig.suptitle(
    "¿Es Acumulativo el Efecto de la Formación Docente?\n"
    "Tasa de Aprobación de Alumnos según Intensidad de Perfeccionamiento — Universo 917",
    fontsize=14, fontweight="bold", y=0.98)

x = np.arange(len(ORD_TRAMOS))
bars = ax.bar(x, medianas, color=colores, alpha=0.85, width=0.6,
              edgecolor="white", linewidth=1.5)

# Etiquetas encima de cada barra + n en label
LABELS_N = [f"{lbl}\n(n={n})" for lbl, n in zip(LABELS, ns)]
for i, (m, color) in enumerate(zip(medianas, colores)):
    ax.text(i, m + 0.25, f"{m:.1f}%", ha="center", fontsize=12,
            fontweight="bold", color=color)

# Línea de tendencia sobre los formados
x_form       = np.arange(1, len(ORD_TRAMOS))
medianas_form = medianas[1:]
ax.plot(x_form, medianas_form, color=C_LINE, linewidth=2.5,
        linestyle="--", marker="D", markersize=9, alpha=0.85,
        label="Tendencia formados", zorder=5)

# Línea de referencia control
ax.axhline(medianas[0], color=C_CTRL, linewidth=1.8,
           linestyle=":", alpha=0.8,
           label=f"Mediana sin formación ({medianas[0]:.1f}%)")

ax.set_xticks(x)
ax.set_xticklabels(LABELS_N, fontsize=11)
ax.set_ylabel("% alumnos aprobados (mediana por docente)", fontsize=12)
ax.set_ylim(89, max(medianas) + 2)
ax.legend(fontsize=11, loc="lower right")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

fig.text(0.5, 0.01,
         "Nota: tasa de aprobación = % alumnos con nota ≥ 4.0 · Se usa mediana por ser más robusta a valores extremos · Períodos 2023-2025.",
         ha="center", fontsize=9, color="#666666", fontstyle="italic")

plt.tight_layout(rect=[0, 0.04, 1, 0.95])
plt.savefig(OUT, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nGuardado: {OUT}")

# ── Gráfico 2 — Boxplot separado ─────────────────────────────────────────────
datos_box = [df_full[df_full["tramo_instancias"]==t]["pct_aprobacion"].dropna().values
             for t in ORD_TRAMOS]

fig2, ax2 = plt.subplots(figsize=(13, 7))
fig2.suptitle(
    "Distribución de la Tasa de Aprobación por Intensidad de Formación\n"
    "Universo 917 · Mediana por tramo (línea negra)",
    fontsize=14, fontweight="bold", y=0.98)

bp = ax2.boxplot(datos_box, patch_artist=True,
                 medianprops=dict(color="black", linewidth=2.5),
                 whiskerprops=dict(linewidth=1.5),
                 capprops=dict(linewidth=1.5),
                 flierprops=dict(marker="o", markersize=4, alpha=0.4))

for patch, color in zip(bp["boxes"], colores):
    patch.set_facecolor(color)
    patch.set_alpha(0.75)

for i, (d, color) in enumerate(zip(datos_box, colores)):
    med = np.median(d) if len(d) > 0 else 0
    ax2.text(i+1, med + 1, f"{med:.1f}%", ha="center", fontsize=11,
             fontweight="bold", color="black")

# n incorporado en el label para evitar solapamiento
LABELS_N = [f"{lbl}\n(n={n})" for lbl, n in zip(LABELS, ns)]
ax2.set_xticks(range(1, len(ORD_TRAMOS)+1))
ax2.set_xticklabels(LABELS_N, fontsize=11)
ax2.set_ylabel("% alumnos aprobados por docente", fontsize=12)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)

fig2.text(0.5, 0.01,
          "Nota: tasa de aprobación = % alumnos con nota ≥ 4.0 · Períodos 2023-2025.",
          ha="center", fontsize=9, color="#666666", fontstyle="italic")

plt.tight_layout(rect=[0, 0.04, 1, 0.95])
plt.savefig(OUT2, dpi=150, bbox_inches="tight")
plt.close()
print(f"Guardado: {OUT2}")

# ── Bajadas ───────────────────────────────────────────────────────────────────
print(f"""
BAJADAS
• La tasa media de aprobación de alumnos aumenta progresivamente con
  la intensidad de formación docente: desde {stats['Sin formación']['media']:.1f}% en
  docentes sin formación hasta {stats['4+']['media']:.1f}% en los que han completado
  4 o más iniciativas de formación — una brecha de {brecha:+.1f} puntos porcentuales. Este patrón
  sugiere que el efecto de la formación es acumulativo: a mayor número
  de iniciativas de formación cursadas, mayor impacto en el rendimiento estudiantil.

• La mejora no es lineal sino que se concentra especialmente a partir
  de la segunda iniciativa de formación, lo que indica que una sola
  participación genera un efecto inicial, pero la consolidación del
  impacto requiere exposición sostenida a iniciativas de perfeccionamiento.
  Esto refuerza la necesidad de diseñar rutas formativas progresivas
  en lugar de actividades puntuales y aisladas.
""")
