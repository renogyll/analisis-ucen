import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.patches as mpatches
import numpy as np
from scipy.stats import ttest_rel, ttest_ind
from sqlalchemy import create_engine, text
import os

engine = create_engine("postgresql://ucen_user:ucen2026@localhost:5432/ucen")
BASE = os.path.dirname(__file__)

matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 12,
})

# ── Datos ya calculados ────────────────────────────────────────────────────────
resultados_c = pd.DataFrame([
    {"Periodo": "2023-01", "n_trat": 169, "n_ctrl": 299, "diff": +0.089, "t": +1.039, "p": 0.2997, "d": +0.099},
    {"Periodo": "2023-02", "n_trat": 172, "n_ctrl": 296, "diff": +0.141, "t": +1.733, "p": 0.0839, "d": +0.167},
    {"Periodo": "2024-01", "n_trat": 195, "n_ctrl": 350, "diff": +0.240, "t": +3.008, "p": 0.0028, "d": +0.260},
    {"Periodo": "2024-02", "n_trat": 186, "n_ctrl": 332, "diff": +0.197, "t": +2.607, "p": 0.0094, "d": +0.231},
    {"Periodo": "2025-01", "n_trat": 193, "n_ctrl": 415, "diff": +0.117, "t": +1.555, "p": 0.1206, "d": +0.132},
    {"Periodo": "2025-02", "n_trat": 152, "n_ctrl": 337, "diff": +0.244, "t": +3.275, "p": 0.0012, "d": +0.302},
])

def sig(p):
    if p < 0.001: return "***"
    if p < 0.01:  return "**"
    if p < 0.05:  return "*"
    return "ns"

resultados_c["sig"] = resultados_c["p"].apply(sig)
resultados_c["sig_color"] = resultados_c["p"].apply(
    lambda p: "#1B5E20" if p < 0.001 else "#388E3C" if p < 0.01 else "#66BB6A" if p < 0.05 else "#9E9E9E")

# ── FIGURA: dos paneles ────────────────────────────────────────────────────────
fig, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(16, 11),
                                      gridspec_kw={"height_ratios": [1, 2.2]})
fig.suptitle("Pruebas t de Student sobre Z-scores SAT\nUniverso 917 — 6 períodos 2023–2025",
             fontsize=18, fontweight="bold", y=0.98)

# ── Panel superior: Prueba A (pareada) ────────────────────────────────────────
ax_top.axis("off")
datos_a = [
    ["TALLER",    "154", "+0.090", "+0.056", "−0.035", "+0.544", "0.588", "−0.044", "ns"],
    ["DIPLOMADO",  "36", "+0.204", "+0.177", "−0.028", "+0.208", "0.836", "−0.035", "ns"],
    ["PROYECTO",    "7", "+0.482", "+0.257", "−0.225", "+0.674", "0.525", "−0.255", "ns"],
]
cols_a = ["Tipo", "n", "Z baseline", "Z resultado", "Δ Z", "t", "p-valor", "Cohen d", "Sig."]
tbl_a = ax_top.table(cellText=datos_a, colLabels=cols_a,
                     loc="center", cellLoc="center")
tbl_a.auto_set_font_size(False)
tbl_a.set_fontsize(13)
tbl_a.scale(1, 1.8)

# Estilo encabezado
for j in range(len(cols_a)):
    tbl_a[0, j].set_facecolor("#37474F")
    tbl_a[0, j].set_text_props(color="white", fontweight="bold")

# Colorear Sig.
for i in range(1, 4):
    tbl_a[i, 8].set_facecolor("#EEEEEE")
    tbl_a[i, 8].set_text_props(color="#757575", fontstyle="italic")

ax_top.set_title("Prueba A — T Pareada: ¿Cambia el docente entre baseline y resultado?",
                 fontsize=13, fontweight="bold", loc="left", pad=8)

# ── Panel inferior: Prueba C (independiente por período) ──────────────────────
ax_bot.axis("off")
datos_c = []
for _, row in resultados_c.iterrows():
    datos_c.append([
        row["Periodo"],
        f"{int(row['n_trat'])}",
        f"{int(row['n_ctrl'])}",
        f"{row['diff']:+.3f}",
        f"{row['t']:+.3f}",
        f"{row['p']:.4f}",
        f"{row['d']:+.3f}",
        row["sig"],
    ])
cols_c = ["Período", "n Formados", "n Control", "Diferencia Z", "t", "p-valor", "Cohen d", "Sig."]
tbl_c = ax_bot.table(cellText=datos_c, colLabels=cols_c,
                     loc="center", cellLoc="center")
tbl_c.auto_set_font_size(False)
tbl_c.set_fontsize(13)
tbl_c.scale(1, 1.85)

for j in range(len(cols_c)):
    tbl_c[0, j].set_facecolor("#37474F")
    tbl_c[0, j].set_text_props(color="white", fontweight="bold")

# Colorear filas significativas
sig_rows = {3: "#E8F5E9", 4: "#E8F5E9", 6: "#C8E6C9"}  # 2024-01, 2024-02, 2025-02
for row_idx, color in sig_rows.items():
    for j in range(len(cols_c)):
        tbl_c[row_idx, j].set_facecolor(color)

# Colorear columna Sig.
sig_colors = {"***": "#1B5E20", "**": "#388E3C", "*": "#66BB6A", "ns": "#9E9E9E"}
for i, row in enumerate(datos_c, start=1):
    s = row[-1]
    tbl_c[i, 7].set_text_props(color=sig_colors[s], fontweight="bold" if s != "ns" else "normal")

ax_bot.set_title("Prueba C — T Independiente por período: Formados vs Sin Formación",
                 fontsize=13, fontweight="bold", loc="left", pad=8)

# Leyenda significancia
legend_items = [
    mpatches.Patch(color="#1B5E20", label="*** p < 0.001"),
    mpatches.Patch(color="#388E3C", label="**  p < 0.01"),
    mpatches.Patch(color="#9E9E9E", label="ns  no significativo"),
]
fig.legend(handles=legend_items, loc="lower center", ncol=3,
           fontsize=13, framealpha=0.9, bbox_to_anchor=(0.5, 0.01))

plt.tight_layout(rect=[0, 0.05, 1, 0.96])
out = os.path.join(BASE, "G11_pruebas_t_918.png")
plt.savefig(out, dpi=150, bbox_inches="tight")
plt.close()
print(f"Guardado: {out}")
