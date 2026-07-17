import sys; sys.stdout.reconfigure(encoding="utf-8")
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os

BASE = os.path.dirname(__file__)

matplotlib.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})

# ════════════════════════════════════════════════════════════════════════════
# p2_g31_modalidad.png — Distribución de Iniciativas de Formación por Modalidad
# ════════════════════════════════════════════════════════════════════════════
labels   = ["Taller", "Diplomado", "Proyecto"]
n_inic   = [376, 201, 38]
n_doc    = [215, 201, 32]
colores  = ["#1976D2", "#388E3C", "#E65100"]
total    = sum(n_inic)
pcts     = [100*v/total for v in n_inic]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7), gridspec_kw={"width_ratios": [1, 1.1]})
fig.suptitle(
    "Distribución de Iniciativas de Formación por Modalidad\n"
    f"Universo 917 · {total} iniciativas de formación en universo jerarquizado",
    fontsize=14, fontweight="bold")

# Panel A — Donut
wedges, _ = ax1.pie(n_inic, colors=colores, startangle=90, counterclock=False,
                     wedgeprops=dict(width=0.45, edgecolor="white", linewidth=2.5))
for w, lbl, v, p, color in zip(wedges, labels, n_inic, pcts, colores):
    ang = (w.theta2 + w.theta1) / 2
    x = 1.25 * np.cos(np.radians(ang)); y = 1.25 * np.sin(np.radians(ang))
    ha = "left" if x > 0 else "right"
    ax1.annotate(f"{lbl}\n{v} inic. ({p:.0f}%)",
                 xy=(0.78*np.cos(np.radians(ang)), 0.78*np.sin(np.radians(ang))),
                 xytext=(x, y), arrowprops=dict(arrowstyle="-", color="#888", lw=1),
                 fontsize=11, ha=ha, va="center", fontweight="bold", color=color)
ax1.text(0, 0, f"{total}\niniciativas", ha="center", va="center",
          fontsize=15, fontweight="bold", color="#333333")
ax1.set_title("Iniciativas de formación por modalidad", pad=12)
ax1.set_xlim(-2.0, 2.0)

# Panel B — Barras comparativas
x = np.arange(len(labels))
w = 0.38
b1 = ax2.bar(x - w/2, n_inic, width=w, color=colores, alpha=0.95, label="Iniciativas de formación")
b2 = ax2.bar(x + w/2, n_doc, width=w, color=colores, alpha=0.45, hatch="//", label="Docentes únicos")
for bars in (b1, b2):
    for bar in bars:
        h = bar.get_height()
        ax2.text(bar.get_x()+bar.get_width()/2, h+4, f"{int(h)}",
                  ha="center", fontsize=11, fontweight="bold", color="#333333")
ax2.set_xticks(x)
ax2.set_xticklabels(labels, fontsize=13, fontweight="bold")
ax2.set_ylabel("N°")
ax2.set_title("Iniciativas de formación vs docentes únicos por modalidad", pad=12)
ax2.legend(fontsize=10, loc="upper right")
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig(os.path.join(BASE, "p2_g31_modalidad.png"), dpi=150, bbox_inches="tight")
plt.close()
print("Guardado: p2_g31_modalidad.png")

# ════════════════════════════════════════════════════════════════════════════
# p2_g41_brechas.png — Perfil de Docentes que No Han Participado
# ════════════════════════════════════════════════════════════════════════════
jer_labels = ["Instr. Regular","Instr. Docente","Asist. Regular","Asist. Docente",
              "Asoc. Regular","Asoc. Docente","Titular Regular","Titular Docente"]
jer_part   = [4, 155, 14, 96, 14, 59, 3, 12]
jer_noPart = [10, 187, 24, 167, 26, 84, 18, 44]

ant_labels = ["0-4 años","5-9 años","10-14 años","15+ años"]
ant_part   = [128, 58, 32, 12]
ant_noPart = [127, 76, 35, 23]

C_PART, C_NOPART = "#1976D2", "#C62828"

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(17, 7), gridspec_kw={"width_ratios": [1.5, 1]})
fig.suptitle(
    "Perfil de Docentes que No Han Participado en Perfeccionamiento\n"
    "Universo 917 · 560 sin ninguna iniciativa de formación registrada (2022-2025)",
    fontsize=14, fontweight="bold")

x1 = np.arange(len(jer_labels))
w = 0.38
b1 = ax1.bar(x1 - w/2, jer_part, width=w, color=C_PART, label="Participaron")
b2 = ax1.bar(x1 + w/2, jer_noPart, width=w, color=C_NOPART, label="No participaron")
for bars, color in zip((b1, b2), (C_PART, C_NOPART)):
    for bar in bars:
        h = bar.get_height()
        ax1.text(bar.get_x()+bar.get_width()/2, h+2, f"{int(h)}",
                  ha="center", fontsize=10, fontweight="bold", color=color)
ax1.set_xticks(x1)
ax1.set_xticklabels(jer_labels, rotation=20, ha="right", fontsize=10)
ax1.set_ylabel("N° docentes")
ax1.set_title("Por jerarquía: formados vs no formados", pad=10)
ax1.legend(fontsize=10)
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)

x2 = np.arange(len(ant_labels))
b3 = ax2.bar(x2 - w/2, ant_part, width=w, color=C_PART, label="Participaron")
b4 = ax2.bar(x2 + w/2, ant_noPart, width=w, color=C_NOPART, label="No participaron")
for bars, color in zip((b3, b4), (C_PART, C_NOPART)):
    for bar in bars:
        h = bar.get_height()
        ax2.text(bar.get_x()+bar.get_width()/2, h+2, f"{int(h)}",
                  ha="center", fontsize=10, fontweight="bold", color=color)
ax2.set_xticks(x2)
ax2.set_xticklabels(ant_labels, fontsize=11)
ax2.set_ylabel("N° docentes")
ax2.set_title("Por antigüedad: formados vs no formados", pad=10)
ax2.legend(fontsize=10)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig(os.path.join(BASE, "p2_g41_brechas.png"), dpi=150, bbox_inches="tight")
plt.close()
print("Guardado: p2_g41_brechas.png")

# ════════════════════════════════════════════════════════════════════════════
# p2_g42_intensidad.png — Intensidad de Participación en Perfeccionamiento
# ════════════════════════════════════════════════════════════════════════════
tramo_labels = ["1 iniciativa", "2 iniciativas", "3 iniciativas", "4 o más"]
vals = [219, 81, 28, 29]
total_form = sum(vals)
pcts = [100*v/total_form for v in vals]
cum  = np.cumsum(pcts)

COLORES_BAR = ["#1565C0", "#1E88E5", "#64B5F6", "#90CAF9"]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6.5))
fig.suptitle(
    "Intensidad de Participación en Perfeccionamiento\n"
    f"Universo 917 · {total_form} docentes con al menos 1 iniciativa de formación",
    fontsize=14, fontweight="bold")

x = np.arange(len(tramo_labels))
bars = ax1.bar(x, vals, color=COLORES_BAR, width=0.6)
for i, (v, p) in enumerate(zip(vals, pcts)):
    ax1.text(i, v+4, f"{v}\n({p:.0f}%)", ha="center", fontsize=11,
              fontweight="bold", color=COLORES_BAR[i])
ax1.set_xticks(x)
ax1.set_xticklabels(tramo_labels, fontsize=11)
ax1.set_ylabel("N° docentes")
ax1.set_title("Distribución por número de iniciativas de formación", pad=10)
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)

ax2.plot(x, cum, color="#1565C0", linewidth=2.5, marker="o", markersize=9)
ax2.fill_between(x, cum, color="#1565C0", alpha=0.15)
for i, c in enumerate(cum):
    ax2.text(i, c+3, f"{c:.0f}%", ha="center", fontsize=11,
              fontweight="bold", color="#1565C0")
ax2.set_xticks(x)
ax2.set_xticklabels(tramo_labels, fontsize=11)
ax2.set_ylabel("% acumulado de docentes formados")
ax2.set_title("Curva acumulada de participación", pad=10)
ax2.set_ylim(0, 110)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig(os.path.join(BASE, "p2_g42_intensidad.png"), dpi=150, bbox_inches="tight")
plt.close()
print("Guardado: p2_g42_intensidad.png")
