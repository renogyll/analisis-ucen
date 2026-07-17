import sys; sys.stdout.reconfigure(encoding="utf-8")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib
import numpy as np
import os

BASE = os.path.dirname(__file__)
matplotlib.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12})

fig, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(16, 11),
                                      gridspec_kw={"height_ratios": [1.1, 1.8]})
fig.suptitle("Validacion Estadistica — EDD Evaluacion de Jefes\nUniverso 917 (Prueba t y Chi-cuadrado)",
             fontsize=18, fontweight="bold", y=0.98)

# ── Panel A: T independiente por anio ────────────────────────────────────────
ax_top.axis("off")
datos_a = [
    ["2022", "75",  "0.864", "145", "0.854", "+0.010", "+0.536", "0.5927", "+0.072", "ns"],
    ["2023", "95",  "0.897", "151", "0.872", "+0.025", "+1.300", "0.1950", "+0.164", "ns"],
    ["2024", "126", "0.734", "244", "0.655", "+0.079", "+3.118", "0.0020", "+0.339", "**"],
    ["2025", "129", "0.864", "336", "0.604", "+0.260", "+11.035","0.0000", "+0.955", "***"],
    ["GLOBAL","425","0.833", "876", "0.706", "+0.127", "+9.615", "< 0.001","+0.522", "***"],
]
cols_a = ["Anio", "n Form.", "EDD Form.", "n Ctrl", "EDD Ctrl", "Diferencia", "t", "p-valor", "Cohen d", "Sig."]
tbl_a = ax_top.table(cellText=datos_a, colLabels=cols_a, loc="center", cellLoc="center")
tbl_a.auto_set_font_size(False)
tbl_a.set_fontsize(13)
tbl_a.scale(1, 1.8)

for j in range(len(cols_a)):
    tbl_a[0, j].set_facecolor("#37474F")
    tbl_a[0, j].set_text_props(color="white", fontweight="bold")

sig_colors = {"***": ("#C8E6C9", "#1B5E20"), "**": ("#DCEDC8", "#388E3C"),
              "ns": ("#F5F5F5", "#9E9E9E")}
for i, row in enumerate(datos_a, start=1):
    s = row[-1]
    bg, fg = sig_colors[s]
    for j in range(len(cols_a)):
        tbl_a[i, j].set_facecolor(bg)
    tbl_a[i, 9].set_text_props(color=fg, fontweight="bold" if s != "ns" else "normal")
    # Fila GLOBAL en negrita
    if row[0] == "GLOBAL":
        for j in range(len(cols_a)):
            tbl_a[i, j].set_text_props(fontweight="bold")
            tbl_a[i, j].set_facecolor("#E8F5E9")

ax_top.set_title("Prueba t Independiente — EDD Total: Formados vs Sin Formacion",
                 fontsize=13, fontweight="bold", loc="left", pad=8)

# ── Panel B: Chi-cuadrado concepto ───────────────────────────────────────────
ax_bot.axis("off")
datos_b = [
    ["Global (todos los anios)", "439", "971", "16.213", "3", "0.001025", "0.107", "Pequeno",  "**"],
    ["2022",                      "64",  "256", "4.893",  "3", "0.1798",   "0.138", "—",        "ns"],
    ["2023",                      "96",  "307", "4.894",  "3", "0.1798",   "0.126", "—",        "ns"],
    ["2024",                     "115",  "484", "13.924", "3", "0.0030",   "0.190", "Pequeno",  "**"],
    ["2025",                     "164",  "930", "5.379",  "3", "0.1461",   "0.108", "—",        "ns"],
]
cols_b = ["Alcance", "n Form.", "n Ctrl", "Chi2", "gl", "p-valor", "Cramer V", "Efecto", "Sig."]
tbl_b = ax_bot.table(cellText=datos_b, colLabels=cols_b, loc="center", cellLoc="center")
tbl_b.auto_set_font_size(False)
tbl_b.set_fontsize(13)
tbl_b.scale(1, 2.0)

for j in range(len(cols_b)):
    tbl_b[0, j].set_facecolor("#37474F")
    tbl_b[0, j].set_text_props(color="white", fontweight="bold")

for i, row in enumerate(datos_b, start=1):
    s = row[-1]
    bg, fg = sig_colors[s]
    for j in range(len(cols_b)):
        tbl_b[i, j].set_facecolor(bg)
    tbl_b[i, 8].set_text_props(color=fg, fontweight="bold" if s != "ns" else "normal")
    if row[0].startswith("Global"):
        for j in range(len(cols_b)):
            tbl_b[i, j].set_text_props(fontweight="bold")
            tbl_b[i, j].set_facecolor("#E8F5E9")

ax_bot.set_title("Chi-cuadrado — Distribucion de Concepto EDD (Muy Bueno / Bueno / Insuficiente / Deficiente)",
                 fontsize=13, fontweight="bold", loc="left", pad=8)

legend_items = [
    mpatches.Patch(color="#1B5E20", label="*** p < 0.001"),
    mpatches.Patch(color="#388E3C", label="**  p < 0.01"),
    mpatches.Patch(color="#9E9E9E", label="ns  no significativo"),
]
fig.legend(handles=legend_items, loc="lower center", ncol=3,
           fontsize=13, framealpha=0.9, bbox_to_anchor=(0.5, 0.01))

plt.tight_layout(rect=[0, 0.05, 1, 0.96])
out = os.path.join(BASE, "G12_pruebas_t_edd_918.png")
plt.savefig(out, dpi=150, bbox_inches="tight")
plt.close()
print(f"Guardado: {out}")
