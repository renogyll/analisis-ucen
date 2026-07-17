import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib
import numpy as np
from scipy.stats import ttest_rel, ttest_ind
from sqlalchemy import create_engine, text
import os

engine = create_engine("postgresql://ucen_user:ucen2026@localhost:5432/ucen")
BASE   = os.path.dirname(__file__)
matplotlib.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12})

# ── Cargar datos P3 (bin z-scores) ───────────────────────────────────────────
df_p3 = pd.read_csv(os.path.join(BASE,"..","PROCESADO","p3_bin_zscore_918.csv"),
                    encoding="utf-8-sig", dtype={"rut_key":str})
df_p3["rut_key"] = df_p3["rut_key"].str.strip()
print(f"Aptos P3 cargados: {len(df_p3)}")

# ── Prueba A: T pareada z_bin_baseline → z_bin_resultado por tipo ─────────────
def sig(p):
    if p < 0.001: return "***"
    if p < 0.01:  return "**"
    if p < 0.05:  return "*"
    return "ns"

datos_a = []
for tipo in ["TALLER", "DIPLOMADO", "PROYECTO"]:
    sub = df_p3[df_p3["tipo_principal"] == tipo].dropna(
        subset=["z_bin_baseline","z_bin_resultado"])
    if len(sub) < 3:
        continue
    b  = sub["z_bin_baseline"].values
    r  = sub["z_bin_resultado"].values
    t_val, p_val = ttest_rel(r, b)
    d  = (r - b).mean() / (r - b).std() if (r - b).std() > 0 else 0.0
    datos_a.append([
        tipo,
        f"{len(sub)}",
        f"{b.mean():+.3f}",
        f"{r.mean():+.3f}",
        f"{(r - b).mean():+.3f}",
        f"{t_val:+.3f}",
        f"{p_val:.3f}",
        f"{d:+.3f}",
        sig(p_val),
    ])
    print(f"  {tipo}: n={len(sub)}, Δz={r.mean()-b.mean():+.3f}, t={t_val:+.3f}, p={p_val:.4f}, d={d:+.3f}")

# ── Prueba C: T independiente pct_si z-score por período ─────────────────────
# Cargar z-scores individuales de toda la población
df_all = pd.read_csv(os.path.join(BASE,"..","PROCESADO","bin_zscore_all_918.csv"),
                     encoding="utf-8-sig", dtype={"rut_key":str})
df_all["rut_key"] = df_all["rut_key"].str.strip()

ruts_treatment = set(df_p3["rut_key"].unique())

with engine.connect() as conn:
    pf = pd.read_sql(text("SELECT DISTINCT rut_key FROM consolidados.participacion_formacion"), conn)
pf["rut_key"] = pf["rut_key"].astype(str).str.strip()
ruts_con_formacion = set(pf["rut_key"])

doc = pd.read_csv(os.path.join(BASE,"..","PROCESADO","docente_918.csv"),
                  encoding="utf-8-sig", dtype={"rut_key":str})
doc["rut_key"] = doc["rut_key"].str.strip()
ruts_917     = set(doc["rut_key"])
ruts_control = ruts_917 - ruts_con_formacion

PERIODOS = ["2023-01","2023-02","2024-01","2024-02","2025-01","2025-02"]
datos_c  = []

print("\nPrueba C — T independiente por período (z_bin):")
for p in PERIODOS:
    sub_p    = df_all[df_all["periodo"] == p]
    trat_z   = sub_p[sub_p["rut_key"].isin(ruts_treatment)]["z"].dropna().values
    ctrl_z   = sub_p[sub_p["rut_key"].isin(ruts_control)]["z"].dropna().values
    if len(trat_z) < 3 or len(ctrl_z) < 3:
        continue
    diff     = trat_z.mean() - ctrl_z.mean()
    t_val, p_val = ttest_ind(trat_z, ctrl_z, equal_var=False)
    pool_sd  = np.sqrt((trat_z.std()**2 + ctrl_z.std()**2) / 2)
    d        = diff / pool_sd if pool_sd > 0 else 0.0
    datos_c.append([
        p,
        f"{len(trat_z)}",
        f"{len(ctrl_z)}",
        f"{diff:+.3f}",
        f"{t_val:+.3f}",
        f"{p_val:.4f}",
        f"{d:+.3f}",
        sig(p_val),
    ])
    print(f"  {p}: n_trat={len(trat_z)}, n_ctrl={len(ctrl_z)}, diff={diff:+.3f}, t={t_val:+.3f}, p={p_val:.4f}, d={d:+.3f}, {sig(p_val)}")

# ── FIGURA ─────────────────────────────────────────────────────────────────────
fig, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(15, 10),
                                      gridspec_kw={"height_ratios": [1, 2.0]})
fig.suptitle("Validación Estadística — % Recomendación (SAT_BIN)\nUniverso 917 (Prueba t paired y Prueba t independiente)",
             fontsize=18, fontweight="bold", y=0.98)

# Panel A
ax_top.axis("off")
cols_a = ["Tipo", "n", "Z baseline", "Z resultado", "Δ Z", "t", "p-valor", "Cohen d", "Sig."]
tbl_a = ax_top.table(cellText=datos_a, colLabels=cols_a, loc="center", cellLoc="center")
tbl_a.auto_set_font_size(False)
tbl_a.set_fontsize(13)
tbl_a.scale(1, 1.8)

for j in range(len(cols_a)):
    tbl_a[0, j].set_facecolor("#37474F")
    tbl_a[0, j].set_text_props(color="white", fontweight="bold")

for i in range(1, len(datos_a)+1):
    for j in range(len(cols_a)):
        tbl_a[i, j].set_facecolor("#EEEEEE")
    tbl_a[i, 8].set_text_props(color="#757575", fontstyle="italic")

ax_top.set_title("Prueba A — T Pareada: ¿Cambia el docente entre baseline y resultado?",
                 fontsize=14, fontweight="bold", loc="left", pad=8)

# Panel C
ax_bot.axis("off")
cols_c = ["Período", "n Formados", "n Control", "Diferencia Z", "t", "p-valor", "Cohen d", "Sig."]
tbl_c = ax_bot.table(cellText=datos_c, colLabels=cols_c, loc="center", cellLoc="center")
tbl_c.auto_set_font_size(False)
tbl_c.set_fontsize(13)
tbl_c.scale(1, 1.85)

for j in range(len(cols_c)):
    tbl_c[0, j].set_facecolor("#37474F")
    tbl_c[0, j].set_text_props(color="white", fontweight="bold")

# Colorear significativas
sig_colors = {"***": "#1B5E20", "**": "#388E3C", "*": "#66BB6A", "ns": "#9E9E9E"}
sig_bg     = {"***": "#C8E6C9", "**": "#DCEDC8", "*": "#F1F8E9",  "ns": "#F5F5F5"}
for i, row in enumerate(datos_c, start=1):
    s = row[-1]
    for j in range(len(cols_c)):
        tbl_c[i, j].set_facecolor(sig_bg[s])
    tbl_c[i, 7].set_text_props(color=sig_colors[s],
                                fontweight="bold" if s != "ns" else "normal")

ax_bot.set_title("Prueba C — T Independiente por período: Formados vs Sin Formación\n(Z-score % Recomendación, misma metodología que SAT nota)",
                 fontsize=14, fontweight="bold", loc="left", pad=8)

legend_items = [
    mpatches.Patch(color="#1B5E20", label="*** p < 0.001"),
    mpatches.Patch(color="#388E3C", label="**  p < 0.01"),
    mpatches.Patch(color="#66BB6A", label="*   p < 0.05"),
    mpatches.Patch(color="#9E9E9E", label="ns  no significativo"),
]
fig.legend(handles=legend_items, loc="lower center", ncol=4,
           fontsize=12, framealpha=0.9, bbox_to_anchor=(0.5, 0.01))

plt.tight_layout(rect=[0, 0.05, 1, 0.96])
out = os.path.join(BASE, "G11.2_pruebas_t_bin_918.png")
plt.savefig(out, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nGuardado: {out}")
