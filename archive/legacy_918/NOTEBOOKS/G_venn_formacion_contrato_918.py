import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os
from matplotlib_venn import venn2, venn2_circles

BASE = os.path.dirname(__file__)
OUT1 = os.path.join(BASE, "G_venn_formacion_jornada_918.png")
OUT2 = os.path.join(BASE, "G_venn_formacion_honorario_918.png")
SRC  = os.path.join(BASE, "..", "..", "CONSOLIDADO DOCENTES 3-05-2026")

matplotlib.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})

def limpiar_rut(s):
    return str(s).strip().replace(".", "").split("-")[0].strip()

# ── NOMINA ────────────────────────────────────────────────────────────────────
nom = pd.read_csv(os.path.join(SRC, "CONSOLIDADO DOCENTES 3-05-2026.xlsx - NOMINA .csv"),
                  dtype=str, encoding="utf-8-sig")
nom.columns = nom.columns.str.strip()
nom["rut_key"] = nom["RUT"].apply(limpiar_rut)
nom["tipo_contrato"] = nom["JORNADA/HONORARIO"].str.strip().str.upper()
# Deduplicar: si tiene Jornada+Honorario → Jornada
tipo_map = {}
for _, row in nom.iterrows():
    rut = row["rut_key"]
    tipo = row["tipo_contrato"]
    if rut not in tipo_map or tipo == "JORNADA":
        tipo_map[rut] = tipo

ruts_nomina = set(tipo_map.keys())

# ── Sets de formación ─────────────────────────────────────────────────────────
ruts_diplomado = set()
for year in ["2022","2023","2024","2025"]:
    df = pd.read_csv(os.path.join(SRC, f"CONSOLIDADO DOCENTES 3-05-2026.xlsx - DIPLOMADO {year}.csv"),
                     encoding="utf-8-sig", dtype=str)
    df["rut_key"] = df["RUT"].apply(limpiar_rut)
    ruts_diplomado |= set(df[df["rut_key"].isin(ruts_nomina)]["rut_key"])

ruts_taller = set()
for f in ["TALLERES 2023_2","TALLERES 2024_1","TALLERES 2024_2"]:
    df = pd.read_csv(os.path.join(SRC, f"CONSOLIDADO DOCENTES 3-05-2026.xlsx - {f}.csv"),
                     encoding="utf-8-sig", dtype=str)
    df.columns = df.columns.str.strip()
    df["rut_key"] = df["RUT"].apply(limpiar_rut)
    ruts_taller |= set(df[df["rut_key"].isin(ruts_nomina)]["rut_key"])

ruts_proyecto = set()
df = pd.read_csv(os.path.join(SRC, "CONSOLIDADO DOCENTES 3-05-2026.xlsx - PROYECTOS DE INVESTIGACION.csv"),
                 encoding="utf-8-sig", dtype=str)
df.columns = df.columns.str.strip()
df["rut_key"] = df["RUT"].apply(limpiar_rut)
ruts_proyecto = set(df[df["rut_key"].isin(ruts_nomina)]["rut_key"])

# ── Función Venn por tipo de contrato ─────────────────────────────────────────
def make_venn(ax, tipo_label, ruts_tipo):
    set_d = ruts_diplomado & ruts_tipo
    set_t = ruts_taller & ruts_tipo
    set_p = ruts_proyecto & ruts_tipo
    n_tipo = len(ruts_tipo)
    n_sin  = len(ruts_tipo - set_d - set_t - set_p)

    solo_d = set_d - set_t - set_p
    solo_t = set_t - set_d - set_p
    solo_p = set_p - set_d - set_t
    d_t    = (set_d & set_t) - set_p
    d_p    = (set_d & set_p) - set_t
    t_p    = (set_t & set_p) - set_d
    d_t_p  = set_d & set_t & set_p

    n_form = len(ruts_tipo & (set_d | set_t | set_p))

    from matplotlib_venn import venn3, venn3_circles
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
                lbl.set_fontsize(12); lbl.set_fontweight("bold")
            else:
                lbl.set_text("")

    circles = venn3_circles(
        subsets=(len(solo_d), len(solo_t), len(d_t),
                 len(solo_p), len(d_p), len(t_p), len(d_t_p)),
        ax=ax, linewidth=2.5)
    for circle, color in zip(circles, ["#388E3C","#1976D2","#E65100"]):
        circle.set_edgecolor(color); circle.set_alpha(0.8)

    ax.text(-0.75, 0.5, f"DIPLOMADO\n({len(set_d)})",
            fontsize=12, fontweight="bold", color="#388E3C", ha="center")
    ax.text(0.75, 0.5, f"TALLER\n({len(set_t)})",
            fontsize=12, fontweight="bold", color="#1976D2", ha="center")
    ax.text(0, -0.75, f"PROYECTO\n({len(set_p)})",
            fontsize=12, fontweight="bold", color="#E65100", ha="center")

    ax.set_title(f"{tipo_label}\n{n_tipo} docentes · {n_form} con formación ({100*n_form/n_tipo:.1f}%)"
                 f" · {n_sin} sin formación ({100*n_sin/n_tipo:.1f}%)",
                 pad=15, fontsize=11, fontweight="bold")

    return {"solo_d":len(solo_d),"solo_t":len(solo_t),"solo_p":len(solo_p),
            "d_t":len(d_t),"d_p":len(d_p),"t_p":len(t_p),"d_t_p":len(d_t_p),
            "sin":n_sin,"total":n_tipo,"form":n_form}

# ── Figura: dos Venns lado a lado ─────────────────────────────────────────────
ruts_jornada   = {r for r, t in tipo_map.items() if t=="JORNADA"}
ruts_honorario = {r for r, t in tipo_map.items() if t=="HONORARIO"}

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))
stats_j = make_venn(ax1, "JORNADA", ruts_jornada)
stats_h = make_venn(ax2, "HONORARIO", ruts_honorario)

fig.suptitle(
    "Combinaciones de Oferta Formativa — Jornada vs Honorario\n"
    f"Universo NOMINA · Jornada: {stats_j['total']} ({stats_j['form']} formados) · "
    f"Honorario: {stats_h['total']} ({stats_h['form']} formados) · Formación 2022–2025",
    fontsize=13, fontweight="bold")

plt.tight_layout()
plt.savefig(os.path.join(BASE, "G_venn_formacion_contrato_918.png"),
            dpi=150, bbox_inches="tight")
plt.close()
print(f"Guardado: G_venn_formacion_contrato_918.png")

# ── Cascada ───────────────────────────────────────────────────────────────────
print()
for label, s in [("JORNADA", stats_j), ("HONORARIO", stats_h)]:
    print(f"  {label} ({s['total']} doc):")
    print(f"    Sin formación     : {s['sin']}")
    print(f"    Solo Diplomado    : {s['solo_d']}")
    print(f"    Solo Taller       : {s['solo_t']}")
    print(f"    Solo Proyecto     : {s['solo_p']}")
    print(f"    Diplomado+Taller  : {s['d_t']}")
    print(f"    Diplomado+Proyecto: {s['d_p']}")
    print(f"    Taller+Proyecto   : {s['t_p']}")
    print(f"    Las 3 modalidades : {s['d_t_p']}")
    print()
