import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os
from matplotlib_venn import venn3, venn3_circles

BASE = os.path.dirname(__file__)
OUT  = os.path.join(BASE, "G_venn_formacion_917_918.png")
SRC  = os.path.join(BASE, "..", "..", "CONSOLIDADO DOCENTES 3-05-2026")

matplotlib.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})

def limpiar_rut(s):
    return str(s).strip().replace(".", "").split("-")[0].strip()

doc917 = pd.read_csv(os.path.join(BASE,"..","PROCESADO","docente_918.csv"),
                     encoding="utf-8-sig", dtype={"rut_key": str})
doc917["rut_key"] = doc917["rut_key"].str.strip()
ruts_917 = set(doc917["rut_key"])

ruts_dip = set()
for year in ["2022","2023","2024","2025"]:
    df = pd.read_csv(os.path.join(SRC, f"CONSOLIDADO DOCENTES 3-05-2026.xlsx - DIPLOMADO {year}.csv"),
                     encoding="utf-8-sig", dtype=str)
    df["rut_key"] = df["RUT"].apply(limpiar_rut)
    ruts_dip |= (set(df["rut_key"]) & ruts_917)

ruts_tal = set()
for f in ["TALLERES 2023_2","TALLERES 2024_1","TALLERES 2024_2"]:
    df = pd.read_csv(os.path.join(SRC, f"CONSOLIDADO DOCENTES 3-05-2026.xlsx - {f}.csv"),
                     encoding="utf-8-sig", dtype=str)
    df.columns = df.columns.str.strip()
    df["rut_key"] = df["RUT"].apply(limpiar_rut)
    ruts_tal |= (set(df["rut_key"]) & ruts_917)

df = pd.read_csv(os.path.join(SRC, "CONSOLIDADO DOCENTES 3-05-2026.xlsx - PROYECTOS DE INVESTIGACION.csv"),
                 encoding="utf-8-sig", dtype=str)
df.columns = df.columns.str.strip()
df["rut_key"] = df["RUT"].apply(limpiar_rut)
ruts_pro = set(df["rut_key"]) & ruts_917

solo_d = ruts_dip - ruts_tal - ruts_pro
solo_t = ruts_tal - ruts_dip - ruts_pro
solo_p = ruts_pro - ruts_dip - ruts_tal
d_t    = (ruts_dip & ruts_tal) - ruts_pro
d_p    = (ruts_dip & ruts_pro) - ruts_tal
t_p    = (ruts_tal & ruts_pro) - ruts_dip
d_t_p  = ruts_dip & ruts_tal & ruts_pro
sin    = ruts_917 - ruts_dip - ruts_tal - ruts_pro

n_form = len(ruts_917 - sin)
n_sin  = len(sin)
n_total = len(ruts_917)

# ── Cascada ───────────────────────────────────────────────────────────────────
print("=" * 65)
print("  VENN — Combinaciones de Formación (Universo 917)")
print("=" * 65)
print(f"  917 docentes jerarquizados")
print(f"    ├── {n_form} con formación ({100*n_form/n_total:.1f}%)")
print(f"    │     ├── Solo Diplomado : {len(solo_d):3d} ({100*len(solo_d)/n_form:.0f}%)")
print(f"    │     ├── Solo Taller    : {len(solo_t):3d} ({100*len(solo_t)/n_form:.0f}%)")
print(f"    │     ├── Solo Proyecto  : {len(solo_p):3d} ({100*len(solo_p)/n_form:.0f}%)")
print(f"    │     ├── D+T            : {len(d_t):3d} ({100*len(d_t)/n_form:.0f}%)")
print(f"    │     ├── D+P            : {len(d_p):3d} ({100*len(d_p)/n_form:.0f}%)")
print(f"    │     ├── T+P            : {len(t_p):3d} ({100*len(t_p)/n_form:.0f}%)")
print(f"    │     └── D+T+P          : {len(d_t_p):3d} ({100*len(d_t_p)/n_form:.0f}%)")
print(f"    └── {n_sin} sin formación ({100*n_sin/n_total:.1f}%)")
print("=" * 65)

# ── Figura ────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 9))
fig.suptitle(
    "Combinaciones de Modalidades de Formación — Universo 917\n"
    f"357 docentes con formación · 560 sin formación · Períodos 2022–2025",
    fontsize=14, fontweight="bold")

v = venn3(subsets=(len(solo_d), len(solo_t), len(d_t),
                   len(solo_p), len(d_p), len(t_p), len(d_t_p)),
          set_labels=("","",""), ax=ax)

colors = {"100":"#388E3C","010":"#1976D2","001":"#E65100",
          "110":"#FFA726","101":"#66BB6A","011":"#FF7043","111":"#BDBDBD"}
for rid, color in colors.items():
    patch = v.get_patch_by_id(rid)
    if patch:
        patch.set_color(color); patch.set_alpha(0.7)
        patch.set_edgecolor("white"); patch.set_linewidth(2)

labels_map = {
    "100": (len(solo_d), "Solo D"),
    "010": (len(solo_t), "Solo T"),
    "001": (len(solo_p), "Solo P"),
    "110": (len(d_t),    "D+T"),
    "101": (len(d_p),    "D+P"),
    "011": (len(t_p),    "T+P"),
    "111": (len(d_t_p),  "D+T+P"),
}
for rid, (n_val, short) in labels_map.items():
    lbl = v.get_label_by_id(rid)
    if lbl:
        if n_val > 0:
            pct = 100*n_val/n_form
            lbl.set_text(f"{short}\n{n_val}\n({pct:.0f}%)")
            lbl.set_fontsize(13); lbl.set_fontweight("bold")
        else:
            lbl.set_text("")

circles = venn3_circles(
    subsets=(len(solo_d), len(solo_t), len(d_t),
             len(solo_p), len(d_p), len(t_p), len(d_t_p)),
    ax=ax, linewidth=2.5)
for circle, color in zip(circles, ["#388E3C","#1976D2","#E65100"]):
    circle.set_edgecolor(color); circle.set_alpha(0.8)

ax.text(-0.75, 0.55, f"DIPLOMADO\n({len(ruts_dip)} doc.)",
        fontsize=14, fontweight="bold", color="#388E3C", ha="center")
ax.text(0.75, 0.55, f"TALLER\n({len(ruts_tal)} doc.)",
        fontsize=14, fontweight="bold", color="#1976D2", ha="center")
ax.text(0, -0.8, f"PROYECTO\n({len(ruts_pro)} doc.)",
        fontsize=14, fontweight="bold", color="#E65100", ha="center")

ax.text(0, -1.05,
        f"Sin formación: {n_sin} docentes ({100*n_sin/n_total:.1f}% del universo)",
        ha="center", fontsize=12, color="#888888", fontstyle="italic")

plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nGuardado: {OUT}")
