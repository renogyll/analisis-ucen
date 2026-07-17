import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib
import numpy as np
import os

BASE = os.path.dirname(__file__)
DOT_CSV = os.path.join(BASE, "..", "..", "CONSOLIDADO DOCENTES 3-05-2026",
                        "CONSOLIDADO DOCENTES 3-05-2026.xlsx - DOTACION_CON_GRADOREC.csv")

matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11, "axes.titlesize": 13, "axes.labelsize": 12,
    "xtick.labelsize": 10, "ytick.labelsize": 10,
})

# ── Paleta corporativa ────────────────────────────────────────────────────────
C1, C2, C3, C4 = "#1565C0", "#1976D2", "#42A5F5", "#66BB6A"
C5, C6, C7     = "#FFA726", "#E65100", "#CFD8DC"
PALETTE_BLUE = ["#1565C0","#1976D2","#1E88E5","#42A5F5",
                "#78909C","#546E7A","#E65100","#EF6C00","#F57C00","#FF8F00"]
PALETTE_FAC  = ["#1565C0","#1976D2","#1E88E5","#42A5F5",
                "#66BB6A","#43A047","#A5D6A7","#FFA726","#FF7043"]

# ── Cargar datos ─────────────────────────────────────────────────────────────
p3 = pd.read_csv(os.path.join(BASE, "..", "PROCESADO", "p3_918.csv"),
                 encoding="utf-8-sig", dtype={"rut_key": str})
p3["rut_key"] = p3["rut_key"].str.strip()

aptos = p3[p3["apto_p3"] == True].drop_duplicates("rut_key").copy()
N = len(aptos)
print(f"Aptos P3: {N} docentes únicos")

# Dotación con GRADOREC + Institución + País
has_dot = os.path.exists(DOT_CSV)
if has_dot:
    dot = pd.read_csv(DOT_CSV, dtype=str, encoding="utf-8-sig")
    dot.columns = dot.columns.str.strip()
    dot["rut_key"] = (dot["RUT"].str.strip()
                      .str.replace(".", "", regex=False)
                      .str.split("-").str[0].str.strip())
    dot197 = dot[dot["rut_key"].isin(set(aptos["rut_key"]))].copy()
    print(f"Dotación 197: {len(dot197)} registros")
else:
    dot197 = pd.DataFrame()
    print("AVISO: no se encontró DOTACION_CON_GRADOREC.csv — gráficos de grado usarán nivel_formacion")


# ═══════════════════════════════════════════════════════════════════════
# GRÁFICO 1 — Edad + Sexo (panel doble)
# ═══════════════════════════════════════════════════════════════════════
OUT_EDAD = os.path.join(BASE, "G_edad_197.png")
OUT_SEXO = os.path.join(BASE, "G_sexo_197.png")

ORD_EDAD = ["<30","30-34","35-39","40-44","45-49","50-54","55-59","60-64","65-69","70+"]

con_edad = aptos[aptos["tramo_edad"].notna() & (aptos["tramo_edad"].astype(str).str.strip() != "nan")].copy()
n_edad   = len(con_edad)
edad_med = pd.to_numeric(aptos["edad_anios"], errors="coerce").median()
edad_avg = pd.to_numeric(aptos["edad_anios"], errors="coerce").mean()

tbl_edad = (con_edad.groupby("tramo_edad")["rut_key"]
            .count().reindex(ORD_EDAD).fillna(0).astype(int))
vals_e   = [int(tbl_edad.get(t, 0)) for t in ORD_EDAD]
pcts_e   = [100*v/n_edad for v in vals_e]

fig, ax = plt.subplots(figsize=(14, 6))
x = np.arange(len(ORD_EDAD))
bars = ax.bar(x, vals_e, width=0.65, color=PALETTE_BLUE, alpha=0.88, edgecolor="white")
for i, (v, p) in enumerate(zip(vals_e, pcts_e)):
    if v > 0:
        ax.text(i, v + 0.3, f"{v}\n({p:.0f}%)", ha="center",
                fontsize=9.5, fontweight="bold", color="#222")

# Mediana estimada
if pd.notnull(edad_med):
    med_t = f"{edad_med:.0f}-{int(edad_med)+4}" if edad_med < 70 else "70+"
    if any(t == med_t for t in ORD_EDAD):
        mi = ORD_EDAD.index(med_t)
    else:
        mi = min(range(len(ORD_EDAD)), key=lambda i: abs(ORD_EDAD[i].split("-")[0].replace("<","").replace("+","") and
                                                           int(ORD_EDAD[i].split("-")[0].replace("<","0").replace("+","")) - edad_med))
    ax.axvline(mi + 0.05, color="#333", linewidth=1.8, linestyle="--", alpha=0.6)
    ax.text(mi + 0.2, max(v for v in vals_e if v) * 0.88,
            f"Mediana ≈{edad_med:.0f} años", fontsize=9.5, color="#333", fontstyle="italic")

n_central = sum(vals_e[ORD_EDAD.index(t)] for t in ["35-39","40-44","45-49","50-54"])
ax.axvspan(ORD_EDAD.index("35-39") - 0.35, ORD_EDAD.index("50-54") + 0.35,
           alpha=0.06, color="#1565C0", zorder=0)
ax.text((ORD_EDAD.index("35-39") + ORD_EDAD.index("50-54")) / 2,
        max(v for v in vals_e if v) * 0.70,
        f"Núcleo 35–54\n{n_central} doc. ({100*n_central/n_edad:.0f}%)",
        ha="center", fontsize=9, color="#1565C0", alpha=0.85, fontstyle="italic")

ax.set_xticks(x); ax.set_xticklabels(ORD_EDAD, fontsize=11)
ax.set_ylabel("N° docentes"); ax.set_ylim(0, max(vals_e) * 1.22)
ax.set_xlabel("Tramo de edad")
ax.set_title(
    f"Distribución por Tramo de Edad — 197 Aptos P3\n"
    f"n={n_edad} con dato de edad · Prom {edad_avg:.1f} años · Mediana {edad_med:.0f} años",
    fontweight="bold")
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
plt.tight_layout()
plt.savefig(OUT_EDAD, dpi=150, bbox_inches="tight"); plt.close()
print(f"✓ {OUT_EDAD}")

# Sexo (dona)
con_sexo = aptos[aptos["sexo"].notna() & (aptos["sexo"].astype(str).str.strip() != "nan")].copy()
n_sexo   = len(con_sexo)
SEXO_MAP = {
    "MASCULINO": "Hombre", "HOMBRE": "Hombre",
    "FEMENINO":  "Mujer",  "MUJER":  "Mujer",
}
con_sexo["sexo_clean"] = con_sexo["sexo"].str.strip().str.upper().map(SEXO_MAP).fillna(
    con_sexo["sexo"].str.strip().str.title())
cnt_sexo = con_sexo["sexo_clean"].value_counts()
labels_s = cnt_sexo.index.tolist()
vals_s   = cnt_sexo.values.tolist()
pcts_s   = [100*v/n_sexo for v in vals_s]
cols_s   = ["#1565C0", "#E65100", "#66BB6A", "#FFA726"][:len(labels_s)]

fig, ax = plt.subplots(figsize=(8, 6))
wedges, _ = ax.pie(vals_s, colors=cols_s, startangle=90, counterclock=False,
                   wedgeprops=dict(width=0.55, edgecolor="white", linewidth=2.5))
for w, lbl, v, p, c in zip(wedges, labels_s, vals_s, pcts_s, cols_s):
    ang = (w.theta2 + w.theta1) / 2
    x2  = 1.3 * np.cos(np.radians(ang))
    y2  = 1.3 * np.sin(np.radians(ang))
    ha  = "left" if x2 > 0 else "right"
    ax.annotate(f"{lbl}\n{v} ({p:.1f}%)",
                xy=(0.75*np.cos(np.radians(ang)), 0.75*np.sin(np.radians(ang))),
                xytext=(x2, y2),
                arrowprops=dict(arrowstyle="-", color="#888", lw=1),
                fontsize=12, ha=ha, va="center", fontweight="bold", color=c)
ax.text(0, 0, f"{n_sexo}\ndoc.", ha="center", va="center",
        fontsize=13, fontweight="bold", color="#333")
ax.set_xlim(-2, 2)
ax.set_title(f"Distribución por Sexo — 197 Aptos P3\n(n={n_sexo} con dato)",
             fontweight="bold")
plt.tight_layout()
plt.savefig(OUT_SEXO, dpi=150, bbox_inches="tight"); plt.close()
print(f"✓ {OUT_SEXO}")


# ═══════════════════════════════════════════════════════════════════════
# GRÁFICO COMBINADO — Edad + Sexo en un solo PNG
# ═══════════════════════════════════════════════════════════════════════
OUT_EDAD_SEXO = os.path.join(BASE, "G_edad_sexo_197.png")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6),
                                gridspec_kw={"width_ratios": [2.2, 1]})
fig.suptitle("Distribución por Edad y Sexo — 197 Aptos P3",
             fontsize=14, fontweight="bold")

# Panel A: Edad
bars = ax1.bar(x, vals_e, width=0.65, color=PALETTE_BLUE, alpha=0.88, edgecolor="white")
for i, (v, p) in enumerate(zip(vals_e, pcts_e)):
    if v > 0:
        ax1.text(i, v + 0.3, f"{v} ({p:.0f}%)", ha="center",
                 fontsize=9, fontweight="bold", color="#222")
ax1.set_xticks(x); ax1.set_xticklabels(ORD_EDAD, fontsize=10, rotation=30, ha="right")
ax1.set_ylabel("N° docentes")
ax1.set_title(f"Tramo de edad · n={n_edad} con dato", pad=8)
ax1.set_ylim(0, max(vals_e) * 1.25)
ax1.axvspan(ORD_EDAD.index("35-39") - 0.4, ORD_EDAD.index("50-54") + 0.4,
            alpha=0.06, color="#1565C0", zorder=0)
ax1.text((ORD_EDAD.index("35-39") + ORD_EDAD.index("50-54")) / 2,
         max(vals_e) * 0.75,
         f"35–54: {n_central} ({100*n_central/n_edad:.0f}%)",
         ha="center", fontsize=9, color="#1565C0", alpha=0.8, fontstyle="italic")
ax1.spines["top"].set_visible(False); ax1.spines["right"].set_visible(False)

# Panel B: Sexo dona
wedges, _ = ax2.pie(vals_s, colors=cols_s, startangle=90, counterclock=False,
                    wedgeprops=dict(width=0.55, edgecolor="white", linewidth=2.5))
for w, lbl, v, p, c in zip(wedges, labels_s, vals_s, pcts_s, cols_s):
    ang = (w.theta2 + w.theta1) / 2
    x2  = 1.35 * np.cos(np.radians(ang))
    y2  = 1.35 * np.sin(np.radians(ang))
    ha  = "left" if x2 > 0 else "right"
    ax2.annotate(f"{lbl}\n{v} ({p:.1f}%)",
                 xy=(0.75*np.cos(np.radians(ang)), 0.75*np.sin(np.radians(ang))),
                 xytext=(x2, y2),
                 arrowprops=dict(arrowstyle="-", color="#888", lw=1),
                 fontsize=11, ha=ha, va="center", fontweight="bold", color=c)
ax2.text(0, 0, f"{n_sexo}\ndoc.", ha="center", va="center",
         fontsize=12, fontweight="bold", color="#333")
ax2.set_xlim(-2.2, 2.2)
ax2.set_title(f"Sexo · n={n_sexo} con dato", pad=8)

plt.tight_layout()
plt.savefig(OUT_EDAD_SEXO, dpi=150, bbox_inches="tight"); plt.close()
print(f"✓ {OUT_EDAD_SEXO}")


# ═══════════════════════════════════════════════════════════════════════
# GRÁFICO 2 — Facultad / Unidad
# ═══════════════════════════════════════════════════════════════════════
OUT_FAC = os.path.join(BASE, "G_facultad_197.png")

con_fac = aptos[aptos["unidad_facultad"].notna()].copy()
n_fac   = len(con_fac)
cnt_fac = con_fac["unidad_facultad"].str.strip().value_counts()

# Abreviar nombres
ABREV_FAC = {
    "FAC. DE MEDICINA Y CIENCIAS DE LA SALUD": "Medicina y C. Salud",
    "FAC. DERECHO Y HUMANIDADES":              "Derecho y Humanidades",
    "FAC. DE INGENIERÍA Y ARQUITECTURA":       "Ingeniería y Arq.",
    "FAC. DE EDUCACIÓN":                       "Educación",
    "FAC. ECONOMÍA, GOBIERNO Y COMUNICACIONES":"Economía, Gob. y Com.",
    "VICERRECTORIA DE INVEST, INNOV Y POSTGRA":"VR Invest./Postgrado",
    "VICERRECTORIA ACADEMICA":                 "VR Académica",
    "DIRECCION DE ASEGURAMIENTO DE LA CALIDAD":"Dir. Aseg. Calidad",
}
labels_f  = [ABREV_FAC.get(k, k) for k in cnt_fac.index]
vals_f    = cnt_fac.values.tolist()
pcts_f    = [100*v/n_fac for v in vals_f]

fig, ax = plt.subplots(figsize=(13, 6))
y = np.arange(len(labels_f))
ax.barh(y[::-1], vals_f, color=PALETTE_FAC[:len(labels_f)], alpha=0.88,
        height=0.62, edgecolor="white")
for i, (v, p, c) in enumerate(zip(vals_f[::-1], pcts_f[::-1], PALETTE_FAC[:len(labels_f)][::-1])):
    ax.text(v + 0.3, i, f"{v}  ({p:.1f}%)", va="center",
            fontsize=10.5, fontweight="bold", color=c)
ax.set_yticks(y); ax.set_yticklabels(labels_f[::-1], fontsize=10.5, fontweight="bold")
ax.set_xlabel("N° docentes")
ax.set_xlim(0, max(vals_f) * 1.35)
ax.set_title(f"Distribución por Unidad/Facultad — 197 Aptos P3\n(n={n_fac} con dato)",
             fontweight="bold")
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
plt.tight_layout()
plt.savefig(OUT_FAC, dpi=150, bbox_inches="tight"); plt.close()
print(f"✓ {OUT_FAC}")


# ═══════════════════════════════════════════════════════════════════════
# GRÁFICO 3 — Antigüedad
# ═══════════════════════════════════════════════════════════════════════
OUT_ANT = os.path.join(BASE, "G_antiguedad_197.png")

ORD_ANT = ["0-4","5-9","10-14","15-19","20-24","25-29","30+"]
con_ant = aptos[aptos["tramo_antiguedad"].notna()].copy()
n_ant   = len(con_ant)
ant_med = pd.to_numeric(aptos["antiguedad_anios"], errors="coerce").median()
ant_avg = pd.to_numeric(aptos["antiguedad_anios"], errors="coerce").mean()

tbl_ant = (con_ant.groupby("tramo_antiguedad")["rut_key"]
           .count().reindex(ORD_ANT).fillna(0).astype(int))
vals_a  = [int(tbl_ant.get(t, 0)) for t in ORD_ANT]
pcts_a  = [100*v/n_ant for v in vals_a]

PALETTE_A = ["#42A5F5","#1E88E5","#1976D2","#1565C0","#0D47A1","#546E7A","#78909C"]

fig, ax = plt.subplots(figsize=(12, 6))
xa = np.arange(len(ORD_ANT))
ax.bar(xa, vals_a, width=0.65, color=PALETTE_A, alpha=0.88, edgecolor="white")
for i, (v, p) in enumerate(zip(vals_a, pcts_a)):
    if v > 0:
        ax.text(i, v + 0.3, f"{v}\n({p:.0f}%)", ha="center",
                fontsize=9.5, fontweight="bold", color="#222")
ax.set_xticks(xa); ax.set_xticklabels(ORD_ANT, fontsize=11)
ax.set_ylabel("N° docentes"); ax.set_xlabel("Tramo de antigüedad (años)")
ax.set_ylim(0, max(vals_a) * 1.22)
ax.set_title(
    f"Distribución por Antigüedad — 197 Aptos P3\n"
    f"n={n_ant} con dato · Prom {ant_avg:.1f} años · Mediana {ant_med:.0f} años",
    fontweight="bold")
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
plt.tight_layout()
plt.savefig(OUT_ANT, dpi=150, bbox_inches="tight"); plt.close()
print(f"✓ {OUT_ANT}")


# ═══════════════════════════════════════════════════════════════════════
# GRÁFICO 4 — Cuerpo Docente (Jornada vs Honorario)
# ═══════════════════════════════════════════════════════════════════════
OUT_CUERPO = os.path.join(BASE, "G_cuerpo_197.png")

con_cuerpo = aptos[aptos["tipo_contrato"].notna()].copy()
n_cuerpo   = len(con_cuerpo)
cnt_cuerpo = con_cuerpo["tipo_contrato"].str.strip().value_counts()
labels_c   = cnt_cuerpo.index.tolist()
vals_c     = cnt_cuerpo.values.tolist()
pcts_c     = [100*v/n_cuerpo for v in vals_c]
cols_c     = ["#1565C0", "#E65100", "#66BB6A"][:len(labels_c)]

fig, (axA, axB) = plt.subplots(1, 2, figsize=(12, 6),
                                gridspec_kw={"width_ratios": [1.2, 1]})
fig.suptitle(f"Cuerpo Docente por Tipo de Contrato — 197 Aptos P3\n(n={n_cuerpo} con dato)",
             fontsize=13, fontweight="bold")

# Barras
y_c = np.arange(len(labels_c))
axA.barh(y_c, vals_c, color=cols_c, alpha=0.88, height=0.5, edgecolor="white")
for i, (v, p, c) in enumerate(zip(vals_c, pcts_c, cols_c)):
    axA.text(v + 0.3, i, f"{v}  ({p:.1f}%)", va="center",
             fontsize=12, fontweight="bold", color=c)
axA.set_yticks(y_c); axA.set_yticklabels(labels_c, fontsize=12, fontweight="bold")
axA.set_xlabel("N° docentes")
axA.set_xlim(0, max(vals_c) * 1.35)
axA.spines["top"].set_visible(False); axA.spines["right"].set_visible(False)
axA.set_title("Distribución absoluta")

# Dona
wedges, _ = axB.pie(vals_c, colors=cols_c, startangle=90, counterclock=False,
                    wedgeprops=dict(width=0.55, edgecolor="white", linewidth=2.5))
for w, lbl, v, p, c in zip(wedges, labels_c, vals_c, pcts_c, cols_c):
    ang = (w.theta2 + w.theta1) / 2
    x2  = 1.3 * np.cos(np.radians(ang))
    y2  = 1.3 * np.sin(np.radians(ang))
    ha  = "left" if x2 > 0 else "right"
    axB.annotate(f"{lbl}\n{v} ({p:.1f}%)",
                 xy=(0.75*np.cos(np.radians(ang)), 0.75*np.sin(np.radians(ang))),
                 xytext=(x2, y2),
                 arrowprops=dict(arrowstyle="-", color="#888", lw=1),
                 fontsize=11, ha=ha, va="center", fontweight="bold", color=c)
axB.text(0, 0, f"{n_cuerpo}\ndoc.", ha="center", va="center",
         fontsize=13, fontweight="bold", color="#333")
axB.set_xlim(-2.2, 2.2); axB.set_title("Composición relativa")

plt.tight_layout()
plt.savefig(OUT_CUERPO, dpi=150, bbox_inches="tight"); plt.close()
print(f"✓ {OUT_CUERPO}")


# ═══════════════════════════════════════════════════════════════════════
# GRÁFICO 5 — Distribución Jerarquía
# ═══════════════════════════════════════════════════════════════════════
OUT_JER = os.path.join(BASE, "G_jerarquia_197.png")

JER_ORD = ["INSTRUCTOR REGULAR","INSTRUCTOR DOCENTE","ASISTENTE REGULAR","ASISTENTE DOCENTE",
           "ASOCIADO REGULAR","ASOCIADO DOCENTE","TITULAR REGULAR","TITULAR DOCENTE"]
JER_ABREV = {
    "INSTRUCTOR REGULAR":  "Instructor Regular",
    "INSTRUCTOR DOCENTE":  "Instructor Docente",
    "ASISTENTE REGULAR":   "Asistente Regular",
    "ASISTENTE DOCENTE":   "Asistente Docente",
    "ASOCIADO REGULAR":    "Asociado Regular",
    "ASOCIADO DOCENTE":    "Asociado Docente",
    "TITULAR REGULAR":     "Titular Regular",
    "TITULAR DOCENTE":     "Titular Docente",
}
COLORES_JER = {
    "INSTRUCTOR REGULAR": "#90CAF9", "INSTRUCTOR DOCENTE": "#1E88E5",
    "ASISTENTE REGULAR":  "#A5D6A7", "ASISTENTE DOCENTE":  "#43A047",
    "ASOCIADO REGULAR":   "#FFA726", "ASOCIADO DOCENTE":   "#E65100",
    "TITULAR REGULAR":    "#CE93D8", "TITULAR DOCENTE":    "#7B1FA2",
}

con_jer = aptos[aptos["jerarquia"].notna()].copy()
n_jer   = len(con_jer)
cnt_jer = con_jer["jerarquia"].str.strip().str.upper().value_counts()

rows = []
for j in JER_ORD:
    v = int(cnt_jer.get(j, 0))
    rows.append({"jerarquia": j, "label": JER_ABREV.get(j, j), "n": v, "color": COLORES_JER[j]})
df_jer = pd.DataFrame(rows)
df_jer = df_jer[df_jer["n"] > 0]

fig, (axA, axB) = plt.subplots(1, 2, figsize=(16, 6),
                                gridspec_kw={"width_ratios": [1.5, 1]})
fig.suptitle(f"Distribución por Jerarquía Académica — 197 Aptos P3\n(n={n_jer})",
             fontsize=13, fontweight="bold")

y_j = np.arange(len(df_jer))
axA.barh(y_j, df_jer["n"].values, color=df_jer["color"].values,
         alpha=0.88, height=0.65, edgecolor="white")
for i, (v, c) in enumerate(zip(df_jer["n"].values, df_jer["color"].values)):
    p = 100*v/n_jer
    axA.text(v + 0.2, i, f"{v}  ({p:.1f}%)", va="center",
             fontsize=10.5, fontweight="bold", color=c)
axA.set_yticks(y_j); axA.set_yticklabels(df_jer["label"].values, fontsize=10.5, fontweight="bold")
axA.set_xlabel("N° docentes"); axA.set_xlim(0, df_jer["n"].max() * 1.4)
axA.spines["top"].set_visible(False); axA.spines["right"].set_visible(False)
axA.set_title("Distribución completa por escalafón")

# Dona agrupada: DOCENTE vs REGULAR
n_docente = df_jer[df_jer["jerarquia"].str.contains("DOCENTE")]["n"].sum()
n_regular = df_jer[df_jer["jerarquia"].str.contains("REGULAR")]["n"].sum()
grp_v = [n_docente, n_regular]
grp_l = [f"Cuerpo Docente\n{n_docente} ({100*n_docente/n_jer:.1f}%)",
         f"Cuerpo Regular\n{n_regular} ({100*n_regular/n_jer:.1f}%)"]
grp_c = ["#1565C0", "#E65100"]

wedges, _ = axB.pie(grp_v, colors=grp_c, startangle=90, counterclock=False,
                    wedgeprops=dict(width=0.55, edgecolor="white", linewidth=2.5))
for w, lbl, c in zip(wedges, grp_l, grp_c):
    ang = (w.theta2 + w.theta1) / 2
    x2  = 1.3 * np.cos(np.radians(ang))
    y2  = 1.3 * np.sin(np.radians(ang))
    ha  = "left" if x2 > 0 else "right"
    axB.annotate(lbl, xy=(0.75*np.cos(np.radians(ang)), 0.75*np.sin(np.radians(ang))),
                 xytext=(x2, y2),
                 arrowprops=dict(arrowstyle="-", color="#888", lw=1),
                 fontsize=12, ha=ha, va="center", fontweight="bold", color=c)
axB.text(0, 0, f"{n_jer}\ndoc.", ha="center", va="center",
         fontsize=13, fontweight="bold", color="#333")
axB.set_xlim(-2.2, 2.2); axB.set_title("Docente vs Regular")

plt.tight_layout()
plt.savefig(OUT_JER, dpi=150, bbox_inches="tight"); plt.close()
print(f"✓ {OUT_JER}")


# ═══════════════════════════════════════════════════════════════════════
# GRÁFICO 6 — Grado Reconocido (GRADOREC o nivel_formacion)
# ═══════════════════════════════════════════════════════════════════════
OUT_GRADO = os.path.join(BASE, "G_gradorec_197.png")

if has_dot and len(dot197) > 0 and "GRADOREC" in dot197.columns:
    df_gr = dot197[dot197["GRADOREC"].notna() &
                   (dot197["GRADOREC"].str.strip() != "NO INFORMA")].copy()
    df_gr["grado_label"] = df_gr["GRADOREC"].str.strip()
    RENAME_GR = {
        "(MAG-PRO).": "Magíster\nProfesional",
        "DOC":        "Doctor",
        "(MAG-ACA)":  "Magíster\nAcadémico",
        "PROFESIONAL":"Profesional",
        "POST-DOC":   "Post-Doctor",
        "TECNICO":    "Técnico",
        "DIPLOMA DE ESTUDIOS AVANZADOS (DEA)": "DEA",
        "DIPLOMADO":  "Diplomado",
    }
    df_gr["grado_label"] = df_gr["grado_label"].map(RENAME_GR).fillna(df_gr["grado_label"])
    cnt_gr = df_gr["grado_label"].value_counts()
    n_gr   = len(df_gr)
    fuente_label = "GRADOREC (dotación)"
else:
    # Fallback: usar nivel_formacion de p3_918
    df_nf = aptos[aptos["nivel_formacion"].notna()].copy()
    NF_MAP = {
        "DOCTOR": "Doctor",
        "MAGÍSTER O MASTER": "Magíster",
        "MÃSTER O MASTER": "Magíster",
        "PROFESIONAL": "Profesional",
        "NO INFORMA": None,
    }
    df_nf["grado_label"] = df_nf["nivel_formacion"].str.strip().map(NF_MAP).fillna(
        df_nf["nivel_formacion"].str.strip().str.title())
    df_nf = df_nf[df_nf["grado_label"].notna()]
    cnt_gr = df_nf["grado_label"].value_counts()
    n_gr   = len(df_nf)
    fuente_label = "nivel_formacion (p3_918)"

grados_ord = cnt_gr.index.tolist()
vals_gr    = cnt_gr.values.tolist()
pcts_gr    = [100*v/n_gr for v in vals_gr]
COLS_GR    = ["#1976D2","#1B5E20","#6A1B9A","#90A4AE","#E65100","#CFD8DC","#FF8F00","#F57C00"]

fig, (axA, axB) = plt.subplots(1, 2, figsize=(15, 7),
                                gridspec_kw={"width_ratios": [1.3, 1]})
fig.suptitle(
    f"Grado Académico — 197 Aptos P3\n"
    f"n={n_gr} con grado clasificado  ·  fuente: {fuente_label}",
    fontsize=12, fontweight="bold")

y_gr = np.arange(len(grados_ord))
axA.barh(y_gr[::-1], vals_gr, color=COLS_GR[:len(grados_ord)],
         alpha=0.88, height=0.62, edgecolor="white")
for i, (v, p, c) in enumerate(zip(vals_gr[::-1], pcts_gr[::-1], COLS_GR[:len(grados_ord)][::-1])):
    axA.text(v + 0.5, i, f"{v}  ({p:.1f}%)", va="center",
             fontsize=10.5, fontweight="bold", color=c)
axA.set_yticks(y_gr)
axA.set_yticklabels([g.replace("\n"," ") for g in grados_ord[::-1]],
                     fontsize=10, fontweight="bold")
axA.set_xlabel("N° docentes"); axA.set_xlim(0, max(vals_gr) * 1.4)
axA.spines["top"].set_visible(False); axA.spines["right"].set_visible(False)
axA.set_title("Distribución por grado reconocido")

# Dona agrupada
n_mag = sum(cnt_gr.get(g, 0) for g in cnt_gr.index if "Magíster" in g or "Mágister" in g or "agister" in g)
n_doc = sum(cnt_gr.get(g, 0) for g in cnt_gr.index if "Doctor" in g or "doctor" in g)
n_prof = n_gr - n_mag - n_doc
dona_v = [v for v in [n_mag, n_doc, n_prof] if v > 0]
dona_l = [f"Magíster\n{n_mag} ({100*n_mag/n_gr:.1f}%)" if n_mag else "",
          f"Doctor/Post-Doc\n{n_doc} ({100*n_doc/n_gr:.1f}%)" if n_doc else "",
          f"Profesional/Otro\n{n_prof} ({100*n_prof/n_gr:.1f}%)" if n_prof else ""]
dona_l = [l for l, v in zip(dona_l, [n_mag, n_doc, n_prof]) if v > 0]
dona_c = ["#1976D2","#1B5E20","#90A4AE"][:len(dona_v)]

wedges, _ = axB.pie(dona_v, colors=dona_c, startangle=90, counterclock=False,
                    wedgeprops=dict(width=0.55, edgecolor="white", linewidth=2.5))
for w, lbl, c in zip(wedges, dona_l, dona_c):
    ang = (w.theta2 + w.theta1) / 2
    x2  = 1.3 * np.cos(np.radians(ang))
    y2  = 1.3 * np.sin(np.radians(ang))
    ha  = "left" if x2 > 0 else "right"
    axB.annotate(lbl, xy=(0.75*np.cos(np.radians(ang)), 0.75*np.sin(np.radians(ang))),
                 xytext=(x2, y2),
                 arrowprops=dict(arrowstyle="-", color="#888", lw=1),
                 fontsize=11, ha=ha, va="center", fontweight="bold", color=c)
axB.text(0, 0, f"{n_gr}\ndoc.", ha="center", va="center",
         fontsize=13, fontweight="bold", color="#333")
axB.set_xlim(-2.2, 2.2); axB.set_title("Agrupación por nivel de grado")

plt.tight_layout()
plt.savefig(OUT_GRADO, dpi=150, bbox_inches="tight"); plt.close()
print(f"✓ {OUT_GRADO}")


# ═══════════════════════════════════════════════════════════════════════
# GRÁFICO 7 — Institución del Grado
# ═══════════════════════════════════════════════════════════════════════
OUT_INST = os.path.join(BASE, "G_institucion_197.png")

if has_dot and len(dot197) > 0 and "INSTITUCIÓN GRADO TÍTULO" in dot197.columns:
    df_inst = dot197[dot197["INSTITUCIÓN GRADO TÍTULO"].notna() &
                     (dot197["INSTITUCIÓN GRADO TÍTULO"].str.strip() != "NO INFORMA")].copy()
    df_inst["inst"] = df_inst["INSTITUCIÓN GRADO TÍTULO"].str.strip()
    n_inst = len(df_inst)
    cnt_inst = df_inst["inst"].value_counts()
    TOP_N = 6
    top_inst   = cnt_inst.head(TOP_N)
    n_otros    = n_inst - top_inst.sum()
    labels_inst = top_inst.index.tolist() + ([f"Otras ({cnt_inst.shape[0]-TOP_N} instituciones)"] if n_otros > 0 else [])
    vals_inst   = top_inst.values.tolist() + ([n_otros] if n_otros > 0 else [])
    ABREV_INST = {
        "UNIVERSIDAD CENTRAL DE CHILE SANTIAGO": "U. Central Santiago",
        "UNIVERSIDAD DE CHILE":                  "U. de Chile",
        "PONTIFICIA UNIVERSIDAD CATÓLICA DE CHILE": "PUC Chile",
        "UNIVERSIDAD ANDRÉS BELLO":              "U. Andrés Bello",
        "UNIVERSIDAD DE SANTIAGO DE CHILE":      "USACH",
        "UNIVERSIDAD MAYOR":                     "U. Mayor",
        "UNIVERSIDAD DIEGO PORTALES":            "UDP",
    }
    labels_abrev = [ABREV_INST.get(l, l) for l in labels_inst]
    pcts_inst    = [100*v/n_inst for v in vals_inst]
    COLS_INST    = ["#1565C0","#1976D2","#42A5F5","#66BB6A","#FFA726","#E65100","#CFD8DC"]

    fig, ax = plt.subplots(figsize=(13, 6))
    fig.suptitle(
        f"Institución de Obtención del Grado Académico — Top 6\n"
        f"197 Aptos P3  ·  n={n_inst} docentes con dato informado",
        fontsize=12, fontweight="bold")
    y_i = np.arange(len(labels_abrev))
    ax.barh(y_i[::-1], vals_inst, color=COLS_INST[:len(labels_abrev)],
            alpha=0.88, height=0.62, edgecolor="white")
    for i, (v, p, c) in enumerate(zip(vals_inst[::-1], pcts_inst[::-1],
                                       COLS_INST[:len(labels_abrev)][::-1])):
        ax.text(v + 0.3, i, f"{v}  ({p:.1f}%)", va="center",
                fontsize=10.5, fontweight="bold", color=c)
    ax.set_yticks(y_i); ax.set_yticklabels(labels_abrev[::-1], fontsize=10.5, fontweight="bold")
    ax.set_xlabel("N° docentes"); ax.set_xlim(0, max(vals_inst) * 1.4)
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    plt.tight_layout()
    plt.savefig(OUT_INST, dpi=150, bbox_inches="tight"); plt.close()
    print(f"✓ {OUT_INST}")
else:
    print(f"AVISO: sin datos de institución — usando nivel_formacion como proxy")
    # Crea un gráfico placeholder informativo
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.text(0.5, 0.5, "Datos de institución\nno disponibles\n(sin dotación completa)",
            ha="center", va="center", fontsize=16, color="#888",
            transform=ax.transAxes)
    ax.set_title("Institución del Grado — 197 Aptos P3", fontweight="bold")
    plt.tight_layout()
    plt.savefig(OUT_INST, dpi=150, bbox_inches="tight"); plt.close()
    print(f"✓ {OUT_INST} (placeholder)")

print("\n═══ RESUMEN ═══")
print(f"Total 197 Aptos P3: {N}")
print(f"Con tramo_edad:     {n_edad}  ({100*n_edad/N:.0f}%)")
print(f"Con sexo:           {n_sexo}  ({100*n_sexo/N:.0f}%)")
print(f"Con facultad:       {n_fac}  ({100*n_fac/N:.0f}%)")
print(f"Con antigüedad:     {n_ant}  ({100*n_ant/N:.0f}%)")
print(f"Con tipo_contrato:  {n_cuerpo}  ({100*n_cuerpo/N:.0f}%)")
print(f"Con jerarquía:      {n_jer}  ({100*n_jer/N:.0f}%)")
print(f"Con grado:          {n_gr}  ({100*n_gr/N:.0f}%)")
print(f"Gráficos generados: 8 PNG")
print("  G_edad_197.png, G_sexo_197.png, G_edad_sexo_197.png")
print("  G_facultad_197.png, G_antiguedad_197.png, G_cuerpo_197.png")
print("  G_jerarquia_197.png, G_gradorec_197.png, G_institucion_197.png")
