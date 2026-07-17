import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os

BASE = os.path.dirname(__file__)
OUT  = os.path.join(BASE, "G_oferta_formativa_contrato_918.png")
SRC  = os.path.join(BASE, "..", "..", "CONSOLIDADO DOCENTES 3-05-2026")

matplotlib.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})

C_JORNADA   = "#1565C0"
C_HONORARIO = "#E65100"

def limpiar_rut(s):
    return str(s).strip().replace(".", "").split("-")[0].strip()

# ── NOMINA ────────────────────────────────────────────────────────────────────
nom = pd.read_csv(os.path.join(SRC, "CONSOLIDADO DOCENTES 3-05-2026.xlsx - NOMINA .csv"),
                  dtype=str, encoding="utf-8-sig")
nom.columns = nom.columns.str.strip()
nom["rut_key"] = nom["RUT"].apply(limpiar_rut)
nom["tipo_contrato"] = nom["JORNADA/HONORARIO"].str.strip().str.upper()
tipo_map = nom.drop_duplicates("rut_key").set_index("rut_key")["tipo_contrato"].to_dict()
ruts_nomina = set(nom["rut_key"].unique())

# ── Contar formaciones ────────────────────────────────────────────────────────
conteo = {}

for year in ["2022","2023","2024","2025"]:
    df = pd.read_csv(os.path.join(SRC, f"CONSOLIDADO DOCENTES 3-05-2026.xlsx - DIPLOMADO {year}.csv"),
                     encoding="utf-8-sig", dtype=str)
    df["rut_key"] = df["RUT"].apply(limpiar_rut)
    for rut in df["rut_key"]:
        if rut in ruts_nomina:
            conteo.setdefault(rut, {"D":0,"T":0,"P":0})
            conteo[rut]["D"] += 1

for f in ["TALLERES 2023_2","TALLERES 2024_1","TALLERES 2024_2"]:
    df = pd.read_csv(os.path.join(SRC, f"CONSOLIDADO DOCENTES 3-05-2026.xlsx - {f}.csv"),
                     encoding="utf-8-sig", dtype=str)
    df.columns = df.columns.str.strip()
    df["rut_key"] = df["RUT"].apply(limpiar_rut)
    for rut in df["rut_key"]:
        if rut in ruts_nomina:
            conteo.setdefault(rut, {"D":0,"T":0,"P":0})
            conteo[rut]["T"] += 1

df = pd.read_csv(os.path.join(SRC, "CONSOLIDADO DOCENTES 3-05-2026.xlsx - PROYECTOS DE INVESTIGACION.csv"),
                 encoding="utf-8-sig", dtype=str)
df.columns = df.columns.str.strip()
df["rut_key"] = df["RUT"].apply(limpiar_rut)
for rut in df["rut_key"]:
    if rut in ruts_nomina:
        conteo.setdefault(rut, {"D":0,"T":0,"P":0})
        conteo[rut]["P"] += 1

# ── Construir tabla ───────────────────────────────────────────────────────────
rows = []
for rut, c in conteo.items():
    rows.append({"rut_key":rut, "D":c["D"],"T":c["T"],"P":c["P"],
                 "tipo": tipo_map.get(rut,"?")})
for rut in ruts_nomina - set(conteo.keys()):
    rows.append({"rut_key":rut, "D":0,"T":0,"P":0, "tipo": tipo_map.get(rut,"?")})

result = pd.DataFrame(rows)
result = result[result["tipo"].isin(["JORNADA","HONORARIO"])].copy()

# Patrón legible
def patron(r):
    parts = []
    if r["D"]>0: parts.append(f"{r['D']} Diplomado{'s' if r['D']>1 else ''}")
    if r["T"]>0: parts.append(f"{r['T']} Taller{'es' if r['T']>1 else ''}")
    if r["P"]>0: parts.append(f"{r['P']} Proyecto{'s' if r['P']>1 else ''}")
    return " + ".join(parts) if parts else "Sin formación"
result["patron"] = result.apply(patron, axis=1)

# Categoría agrupada para gráfico
def categoria(r):
    if r["D"]==0 and r["T"]==0 and r["P"]==0: return "Sin formación"
    if r["D"]>0  and r["T"]==0 and r["P"]==0: return "Solo Diplomado"
    if r["D"]==0 and r["T"]>0  and r["P"]==0: return f"Solo Taller{'es' if r['T']>1 else ''} ({r['T']})"
    if r["D"]==0 and r["T"]==0 and r["P"]>0:  return "Solo Proyecto"
    if r["D"]>0  and r["T"]>0  and r["P"]==0: return f"Diplomado + {r['T']}T"
    return "Mixto con Proyecto"
result["cat"] = result.apply(categoria, axis=1)

# Agrupar talleres solo en 1T, 2T, 3T+
def cat_simple(r):
    if r["D"]==0 and r["T"]==0 and r["P"]==0: return "Sin formación"
    if r["D"]>0  and r["T"]==0 and r["P"]==0: return "Solo Diplomado(s)"
    if r["D"]==0 and r["T"]>0  and r["P"]==0:
        if r["T"]==1: return "Solo 1 Taller"
        if r["T"]==2: return "Solo 2 Talleres"
        return "Solo 3+ Talleres"
    if r["D"]==0 and r["T"]==0 and r["P"]>0:  return "Solo Proyecto(s)"
    if r["D"]>0  and r["T"]>0  and r["P"]==0:
        return f"Diplomado + {r['T']}T"
    return "Mixto con Proyecto"
result["cat_s"] = result.apply(cat_simple, axis=1)

# Orden para gráfico
ORD_CAT = [
    "Sin formación",
    "Solo 1 Taller",
    "Solo 2 Talleres",
    "Solo 3+ Talleres",
    "Solo Diplomado(s)",
    "Solo Proyecto(s)",
    "Diplomado + 1T",
    "Diplomado + 2T",
    "Diplomado + 3T",
    "Mixto con Proyecto",
]
ord_validos = [c for c in ORD_CAT if c in result["cat_s"].values]

n_j = len(result[result["tipo"]=="JORNADA"])
n_h = len(result[result["tipo"]=="HONORARIO"])
n_j_form = len(result[(result["tipo"]=="JORNADA") & (result["cat_s"]!="Sin formación")])
n_h_form = len(result[(result["tipo"]=="HONORARIO") & (result["cat_s"]!="Sin formación")])

# ── Cascada ───────────────────────────────────────────────────────────────────
print("=" * 70)
print("  COMBINACIONES DE OFERTA FORMATIVA — Jornada vs Honorario")
print("=" * 70)
print(f"  957 docentes NOMINA")
print(f"    ├── Jornada   : {n_j} | con formación: {n_j_form} ({100*n_j_form/n_j:.1f}%)")
print(f"    └── Honorario : {n_h} | con formación: {n_h_form} ({100*n_h_form/n_h:.1f}%)")
print()
print(f"  {'Combinación':<25} {'Jornada':>10} {'Honorario':>10}")
print(f"  {'-'*25} {'-'*10} {'-'*10}")
for cat in ord_validos:
    nj = len(result[(result["tipo"]=="JORNADA")   & (result["cat_s"]==cat)])
    nh = len(result[(result["tipo"]=="HONORARIO") & (result["cat_s"]==cat)])
    pj = f"({100*nj/n_j:.1f}%)" if nj>0 else ""
    ph = f"({100*nh/n_h:.1f}%)" if nh>0 else ""
    print(f"  {cat:<25} {nj:>4} {pj:>6}  {nh:>4} {ph:>6}")

# Agrupar Diplomado + nT que son muy pequeños
def cat_grafico(r):
    if r["D"]==0 and r["T"]==0 and r["P"]==0: return "Sin formación"
    if r["D"]>0  and r["T"]==0 and r["P"]==0: return "Solo Diplomado(s)"
    if r["D"]==0 and r["T"]==1 and r["P"]==0: return "Solo 1 Taller"
    if r["D"]==0 and r["T"]>=2 and r["P"]==0: return "Solo 2+ Talleres"
    if r["D"]==0 and r["T"]==0 and r["P"]>0:  return "Solo Proyecto(s)"
    if r["D"]>0  and r["T"]>0  and r["P"]==0: return "Diplomado + Taller(es)"
    return "Con Proyecto + otro"
result["cat_g"] = result.apply(cat_grafico, axis=1)

ORD_G = [
    "Sin formación",
    "Solo 1 Taller",
    "Solo 2+ Talleres",
    "Solo Diplomado(s)",
    "Solo Proyecto(s)",
    "Diplomado + Taller(es)",
    "Con Proyecto + otro",
]
ord_g = [c for c in ORD_G if c in result["cat_g"].values]

# ── Figura ────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(14, 8))
fig.suptitle(
    "Combinaciones de Oferta Formativa — Jornada vs Honorario\n"
    f"Universo NOMINA · {n_j} Jornada · {n_h} Honorario · Formación 2022–2025",
    fontsize=13, fontweight="bold")

y = np.arange(len(ord_g))
w = 0.35

vals_j = [len(result[(result["tipo"]=="JORNADA")  &(result["cat_g"]==c)]) for c in ord_g]
vals_h = [len(result[(result["tipo"]=="HONORARIO")&(result["cat_g"]==c)]) for c in ord_g]
pcts_j = [100*v/n_j for v in vals_j]
pcts_h = [100*v/n_h for v in vals_h]

ax.barh(y + w/2, pcts_j, height=w, color=C_JORNADA, alpha=0.85,
        label=f"Jornada (n={n_j})", edgecolor="white")
ax.barh(y - w/2, pcts_h, height=w, color=C_HONORARIO, alpha=0.85,
        label=f"Honorario (n={n_h})", edgecolor="white")

for i, (pj, ph, vj, vh) in enumerate(zip(pcts_j, pcts_h, vals_j, vals_h)):
    if vj > 0:
        ax.text(pj + 0.5, i + w/2, f"{vj} ({pj:.1f}%)",
                va="center", fontsize=9, fontweight="bold", color=C_JORNADA)
    if vh > 0:
        ax.text(ph + 0.5, i - w/2, f"{vh} ({ph:.1f}%)",
                va="center", fontsize=9, fontweight="bold", color=C_HONORARIO)

ax.set_yticks(y)
ax.set_yticklabels(ord_g, fontsize=11, fontweight="bold")
ax.set_xlabel("% del grupo")
ax.set_xlim(0, max(max(pcts_j), max(pcts_h)) * 1.35)
ax.legend(fontsize=11, loc="lower right")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nGuardado: {OUT}")

print("=" * 70)
