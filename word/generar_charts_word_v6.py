# -*- coding: utf-8 -*-
"""
generar_charts_word_v6.py
Regenera los 8 graficos del INFORME_P3_v6.docx con texto negro (ejes, leyendas,
titulos de eje, ticks) para que sean legibles sobre fondo gris claro (235,235,235).
Guarda en dark_slides_v3/word_charts_v6/ como PNGs transparentes.
"""
import sys; sys.stdout.reconfigure(encoding="utf-8")
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from scipy import stats as scipy_stats

BASE   = os.path.dirname(os.path.abspath(__file__))
PROC   = os.path.join(BASE, "..", "PROCESADO")
ROOT_PROC = os.path.normpath(os.path.join(BASE, "..", "..", "PROCESADO"))
OUT    = os.path.join(BASE, "dark_slides_v3", "word_charts_v6")
os.makedirs(OUT, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# Datos
# ─────────────────────────────────────────────────────────────────────────────
sat  = pd.read_csv(os.path.join(PROC, "p3_sat_zscore_918.csv"), encoding="utf-8-sig")
sat["rut_key"] = sat["rut_key"].astype(str).str.strip()

cvt  = pd.read_csv(os.path.join(PROC, "control_vs_trat_918.csv"), encoding="utf-8-sig")
cvt["z_trat"] = pd.to_numeric(cvt["z_trat"], errors="coerce")
cvt["z_ctrl"] = pd.to_numeric(cvt["z_ctrl"], errors="coerce")
cvt["n_trat"]  = pd.to_numeric(cvt["n_trat"], errors="coerce").astype(int)
cvt["n_ctrl"]  = pd.to_numeric(cvt["n_ctrl"], errors="coerce").astype(int)

scat = pd.read_csv(os.path.join(PROC, "scatter_sat_notas.csv"), encoding="utf-8-sig")
scat["pct_aprobacion"] = pd.to_numeric(scat["pct_aprobacion"], errors="coerce")
scat["nota_promedio"]  = pd.to_numeric(scat["nota_promedio"],  errors="coerce")
scat["sat"]            = pd.to_numeric(scat["sat"],            errors="coerce")
scat["formado"] = (scat["formado"].astype(str).str.strip().str.upper()
                   .isin(["TRUE","1","SI","SI","YES"]))

DOC918   = os.path.join(PROC, "docente_918.csv")
EDD_CSV  = os.path.join(ROOT_PROC, "P1_consolidado_con_evaluacion_jefes.csv")
doc918   = pd.read_csv(DOC918, dtype={"rut_key": str}, encoding="utf-8-sig")
doc918["rut_key"] = doc918["rut_key"].str.strip()
ruts_917 = set(doc918["rut_key"])
ruts_form = set(sat["rut_key"])

has_edd = os.path.exists(EDD_CSV)
if has_edd:
    edd_df = pd.read_csv(EDD_CSV, dtype={"rut_key": str}, encoding="utf-8-sig")
    edd_df["rut_key"]   = edd_df["rut_key"].str.strip()
    edd_df["edd_total"] = pd.to_numeric(edd_df["edd_total"], errors="coerce")
    edd_df["anio_eval"] = edd_df["anio_evaluacion"].apply(
        lambda x: str(int(float(x)))[:4] if pd.notna(x) else None)
    edd_form = (edd_df[edd_df["rut_key"].isin(ruts_form) & edd_df["edd_total"].notna()
                       & edd_df["anio_eval"].notna()]
                .drop_duplicates(subset=["rut_key","anio_eval"]))
    edd_ctrl = (edd_df[edd_df["rut_key"].isin(ruts_917) & ~edd_df["rut_key"].isin(ruts_form)
                       & edd_df["edd_total"].notna() & edd_df["anio_eval"].notna()]
                .drop_duplicates(subset=["rut_key","anio_eval"]))
else:
    edd_form = pd.DataFrame()
    edd_ctrl = pd.DataFrame()

def _tipo_simple(t):
    t = str(t).upper()
    if "TALLER" in t and "DIPLOMADO" not in t and "PROYECTO" not in t: return "Taller"
    if "DIPLOMADO" in t and "TALLER" not in t and "PROYECTO" not in t: return "Diplomado"
    if "PROYECTO" in t and "TALLER" not in t and "DIPLOMADO" not in t: return "Proyecto"
    return "Participacion Mixta"

# ─────────────────────────────────────────────────────────────────────────────
# Helpers matplotlib — texto negro para Word imprimible
# ─────────────────────────────────────────────────────────────────────────────
C_TEXT  = "#1A1A1A"
C_SPINE = "#444444"
C_GRID  = "#BBBBBB"
C_ANN   = "#444444"   # color de anotaciones sobre el gráfico

def _tr_fig(w=13, h=5.5):
    fig = plt.figure(figsize=(w, h), facecolor="none")
    fig.patch.set_alpha(0.0)
    return fig

def _ax(w=13, h=5.5):
    fig, ax = plt.subplots(figsize=(w, h), facecolor="none")
    fig.patch.set_alpha(0.0)
    ax.set_facecolor("none")
    return fig, ax

def _style_word(ax, xlabel=None, ygrid=True, xgrid=False):
    """Ejes, ticks y leyenda en negro — para fondo claro."""
    ax.tick_params(axis="x", colors=C_TEXT, labelsize=9.5, length=3, width=0.8)
    ax.tick_params(axis="y", colors=C_TEXT, labelsize=9.5, length=3, width=0.8)
    for sp in ax.spines.values():
        sp.set_edgecolor(C_SPINE); sp.set_alpha(0.55); sp.set_linewidth(0.8)
    if ygrid:
        ax.yaxis.grid(True, color=C_GRID, alpha=0.7, linewidth=0.6)
    if xgrid:
        ax.xaxis.grid(True, color=C_GRID, alpha=0.5, linewidth=0.5)
    ax.set_axisbelow(True)
    if xlabel:
        ax.set_xlabel(xlabel, color=C_TEXT, fontsize=9.5)

def _save(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=150, facecolor="none", transparent=True, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {name}")
    return path

# ─────────────────────────────────────────────────────────────────────────────
# 1. 22_chart.png — SAT z-score 6 periodos
# ─────────────────────────────────────────────────────────────────────────────
def chart_22():
    periodos = cvt["periodo"].tolist()
    z_f  = cvt["z_trat"].tolist(); n_f = cvt["n_trat"].tolist()
    z_c  = cvt["z_ctrl"].tolist(); n_c = cvt["n_ctrl"].tolist()

    fig, ax = _ax()
    xa = range(len(periodos))
    ax.plot(xa, z_f, color="#1565C0", linewidth=2.5, marker="o", markersize=9,
            label="Formados", zorder=5)
    ax.plot(xa, z_c, color="#E65100", linewidth=2.5, linestyle="--", marker="s",
            markersize=8, label="Control", zorder=5)

    for i, (zf, zc, nf, nc) in enumerate(zip(z_f, z_c, n_f, n_c)):
        ax.text(i, zf + 0.016, f"{zf:.2f} (n={nf})",
                ha="center", va="bottom", fontsize=8, fontweight="bold",
                color="#1565C0",
                path_effects=[pe.withStroke(linewidth=1.2, foreground="white")])
        ax.text(i, zc - 0.016, f"{zc:.2f} (n={nc})",
                ha="center", va="top", fontsize=8, fontweight="bold",
                color="#BF360C",
                path_effects=[pe.withStroke(linewidth=1.2, foreground="white")])

    ax.axhline(0, color=C_ANN, linewidth=1, linestyle=":", alpha=0.55)
    ax.set_xticks(list(xa))
    ax.set_xticklabels(periodos, fontsize=9.5, color=C_TEXT, rotation=15)
    _style_word(ax)
    ax.set_ylabel("z-score SAT (promedio)", color=C_TEXT, fontsize=9.5)
    ax.legend(fontsize=10, framealpha=0.85, labelcolor=C_TEXT,
              facecolor="white", edgecolor="#888888")
    plt.tight_layout(pad=0.8)
    _save(fig, "22_chart.png")

# ─────────────────────────────────────────────────────────────────────────────
# 2. 37_chart.png — Evolucion EDD Formados vs Control por Año
# ─────────────────────────────────────────────────────────────────────────────
def chart_37():
    if not has_edd or len(edd_form) == 0:
        print("  [SKIP] 37_chart — sin datos EDD"); return

    anios_ord   = sorted(edd_form["anio_eval"].unique())
    z_f         = [edd_form[edd_form["anio_eval"]==a]["edd_total"].mean() for a in anios_ord]
    z_c         = [edd_ctrl[edd_ctrl["anio_eval"]==a]["edd_total"].mean() if len(edd_ctrl) else float("nan")
                   for a in anios_ord]
    n_f_by_yr   = [edd_form[edd_form["anio_eval"]==a]["rut_key"].nunique() for a in anios_ord]
    n_c_by_yr   = [edd_ctrl[edd_ctrl["anio_eval"]==a]["rut_key"].nunique() if len(edd_ctrl) else 0
                   for a in anios_ord]

    fig, ax = _ax()
    xa = range(len(anios_ord))
    ax.plot(xa, z_f, color="#1565C0", linewidth=2.5, marker="o", markersize=9,
            label="Formados", zorder=5)
    ax.plot(xa, z_c, color="#BF360C", linewidth=2.5, linestyle="--", marker="s",
            markersize=8, label="Control", zorder=5)

    for i, (vf, vc, nf, nc) in enumerate(zip(z_f, z_c, n_f_by_yr, n_c_by_yr)):
        ax.text(i, vf + 0.010, f"{vf:.3f} (n={nf})",
                ha="center", va="bottom", fontsize=8, fontweight="bold",
                color="#1565C0",
                path_effects=[pe.withStroke(linewidth=1.2, foreground="white")])
        ax.text(i, vc - 0.010, f"{vc:.3f} (n={nc})",
                ha="center", va="top", fontsize=8, fontweight="bold",
                color="#BF360C",
                path_effects=[pe.withStroke(linewidth=1.2, foreground="white")])

    ax.axhline(0, color=C_ANN, linewidth=0.8, linestyle=":", alpha=0.5)
    ax.set_xticks(list(xa))
    ax.set_xticklabels(anios_ord, fontsize=10, color=C_TEXT)
    _style_word(ax, ygrid=True)
    ax.set_ylabel("EDD Total (promedio)", color=C_TEXT, fontsize=9.5)
    ax.legend(fontsize=10, framealpha=0.85, labelcolor=C_TEXT,
              facecolor="white", edgecolor="#888888")

    z_valid = [v for v in z_f + z_c if not np.isnan(v)]
    if z_valid:
        ax.set_ylim(max(0, min(z_valid) - 0.08), min(1.0, max(z_valid) + 0.10))
    plt.tight_layout(pad=0.8)
    _save(fig, "37_chart.png")

# ─────────────────────────────────────────────────────────────────────────────
# 3. 30_chart.png — Aprobacion Global (formados vs control)
# ─────────────────────────────────────────────────────────────────────────────
def chart_30():
    form   = scat[scat["formado"]].dropna(subset=["pct_aprobacion","nota_promedio"])
    ctrl_s = scat[~scat["formado"]].dropna(subset=["pct_aprobacion","nota_promedio"])
    n_f    = len(form); n_c = len(ctrl_s)

    grps    = ["Formados", "Control"]
    vals_p  = [form["pct_aprobacion"].mean(), ctrl_s["pct_aprobacion"].mean()]
    vals_n  = [form["nota_promedio"].mean(),   ctrl_s["nota_promedio"].mean()]
    PAL     = ["#1565C0", "#E65100"]

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(13, 5.5), facecolor="none")
    fig.patch.set_alpha(0.0)
    for a in [ax, ax2]: a.set_facecolor("none")

    xa = np.arange(len(grps))

    # Panel 1 — % Aprobacion
    ax.bar(xa, vals_p, width=0.55, color=PAL, alpha=0.88, edgecolor="none")
    mv_p = max(vals_p)
    for i, v in enumerate(vals_p):
        ax.text(i, v + mv_p * 0.025, f"{v:.1f}%",
                ha="center", va="bottom", fontsize=14, fontweight="bold",
                color=PAL[i])
    ax.set_xticks(xa); ax.set_xticklabels(grps, fontsize=12, color=C_TEXT)
    ax.set_title("% Aprobación", color=C_TEXT, fontsize=11, pad=8)
    _style_word(ax)
    ax.set_ylim(0, mv_p * 1.30)
    ax.tick_params(colors=C_TEXT, labelsize=9)

    # Panel 2 — Nota Promedio
    ax2.bar(xa, vals_n, width=0.55, color=PAL, alpha=0.88, edgecolor="none")
    mv_n = max(vals_n)
    for i, v in enumerate(vals_n):
        ax2.text(i, v + mv_n * 0.025, f"{v:.2f}",
                 ha="center", va="bottom", fontsize=14, fontweight="bold",
                 color=PAL[i])
    ax2.set_xticks(xa); ax2.set_xticklabels(grps, fontsize=12, color=C_TEXT)
    ax2.set_title("Nota Promedio (1–7)", color=C_TEXT, fontsize=11, pad=8)
    _style_word(ax2)
    ax2.set_ylim(0, mv_n * 1.30)
    ax2.tick_params(colors=C_TEXT, labelsize=9)

    plt.tight_layout(pad=0.9)
    _save(fig, "30_chart.png")

# ─────────────────────────────────────────────────────────────────────────────
# 4. 31_chart.png — Evolucion Aprobacion por Periodo
# ─────────────────────────────────────────────────────────────────────────────
def chart_31():
    s = scat.dropna(subset=["pct_aprobacion","periodo"])
    periodos_ord = sorted(s["periodo"].unique().tolist())
    pct_f = [s[(s["formado"])  & (s["periodo"]==p)]["pct_aprobacion"].mean() for p in periodos_ord]
    pct_c = [s[(~s["formado"]) & (s["periodo"]==p)]["pct_aprobacion"].mean() for p in periodos_ord]

    fig, ax = _ax()
    xa = range(len(periodos_ord))
    ax.plot(xa, pct_f, color="#1565C0", linewidth=2.5, marker="o", markersize=9,
            label="Formados", zorder=5)
    ax.plot(xa, pct_c, color="#E65100", linewidth=2.5, linestyle="--", marker="s",
            markersize=8, label="Control", zorder=5)
    ax.fill_between(xa, pct_f, pct_c,
                    where=[f > c for f, c in zip(pct_f, pct_c)],
                    alpha=0.10, color="#388E3C", interpolate=True)

    mv_range = max(pct_f + pct_c) - min(pct_f + pct_c) if (pct_f + pct_c) else 5
    for i, (vf, vc) in enumerate(zip(pct_f, pct_c)):
        if not np.isnan(vf):
            ax.text(i, vf + mv_range * 0.07, f"{vf:.1f}%",
                    ha="center", va="bottom", fontsize=8, fontweight="bold",
                    color="#1565C0")
        if not np.isnan(vc):
            ax.text(i, vc - mv_range * 0.07, f"{vc:.1f}%",
                    ha="center", va="top", fontsize=8, fontweight="bold",
                    color="#BF360C")

    ax.axhline(np.nanmean(pct_f + pct_c), color=C_ANN, linewidth=0.8, linestyle=":", alpha=0.5)
    ax.set_xticks(list(xa))
    ax.set_xticklabels(periodos_ord, fontsize=9, color=C_TEXT, rotation=15)
    _style_word(ax)
    ax.set_ylabel("% Aprobación promedio", color=C_TEXT, fontsize=9.5)
    ax.legend(fontsize=10, framealpha=0.85, labelcolor=C_TEXT,
              facecolor="white", edgecolor="#888888")
    plt.tight_layout(pad=0.8)
    _save(fig, "31_chart.png")

# ─────────────────────────────────────────────────────────────────────────────
# 5. 38_chart.png — EDD por Tipo de Formacion (barras horizontales)
# ─────────────────────────────────────────────────────────────────────────────
def chart_38():
    if not has_edd or len(edd_form) == 0:
        print("  [SKIP] 38_chart — sin datos EDD"); return

    edd_ft = edd_form.merge(sat[["rut_key","tipos_formacion"]], on="rut_key", how="left")
    edd_ft["tipo_g"] = edd_ft["tipos_formacion"].apply(_tipo_simple)
    tipo_grp = edd_ft.groupby("tipo_g")["edd_total"].agg(["mean","count"]).reset_index()
    tipo_grp = tipo_grp.sort_values("mean", ascending=False)
    ctrl_mean = edd_ctrl["edd_total"].mean() if len(edd_ctrl) else float("nan")
    ctrl_n    = edd_ctrl["rut_key"].nunique() if len(edd_ctrl) else 0

    lbl  = tipo_grp["tipo_g"].tolist() + ["Control"]
    vals = tipo_grp["mean"].tolist() + [ctrl_mean]
    ns   = tipo_grp["count"].astype(int).tolist() + [ctrl_n]

    TIPO_COLS = {"Taller": "#1565C0", "Diplomado": "#1976D2", "Proyecto": "#2E7D32",
                 "Participacion Mixta": "#6A1B9A", "Control": "#BF360C"}
    cols = [TIPO_COLS.get(l, "#555555") for l in lbl]

    fig, ax = _ax(w=11, h=5)
    n = len(lbl); yp = np.arange(n)
    ax.barh(yp[::-1], vals, color=cols, height=0.55, edgecolor="none", alpha=0.88)

    mv = max(vals) if vals else 1
    for i, (v, nv) in enumerate(zip(vals[::-1], ns[::-1])):
        ax.text(v + mv * 0.015, i, f"{v:.3f}  (n={nv})",
                va="center", ha="left", fontsize=10, fontweight="bold",
                color=cols[::-1][i])

    ax.set_yticks(yp)
    ax.set_yticklabels(lbl[::-1], fontsize=10.5, fontweight="bold", color=C_TEXT)
    ax.tick_params(axis="y", length=0, pad=8)
    ax.tick_params(axis="x", colors=C_TEXT, labelsize=9)
    for sp in ax.spines.values():
        sp.set_edgecolor(C_SPINE); sp.set_alpha(0.45); sp.set_linewidth(0.8)
    ax.set_xlim(0, mv * 1.55)
    ax.set_ylim(-0.5, n - 0.5)
    ax.xaxis.grid(True, color=C_GRID, alpha=0.6, linewidth=0.5)
    ax.set_axisbelow(True)

    plt.tight_layout(pad=0.8)
    _save(fig, "38_chart.png")

# ─────────────────────────────────────────────────────────────────────────────
# 6. 27_chart.png — SAT por Jerarquia Taller (Baseline → Resultado)
# ─────────────────────────────────────────────────────────────────────────────
def chart_27():
    JER_ORD = ["INSTRUCTOR REGULAR","INSTRUCTOR DOCENTE","ASISTENTE REGULAR","ASISTENTE DOCENTE",
               "ASOCIADO REGULAR","ASOCIADO DOCENTE","TITULAR REGULAR","TITULAR DOCENTE"]
    df = sat[(sat["n_taller"] > 0) & (sat["n_diplomado"] == 0) & (sat["n_proyecto"] == 0)].copy()
    df["jer_u"] = df["jerarquia"].str.strip().str.upper()
    grp = df.groupby("jer_u")[["z_baseline","z_resultado"]].mean()
    ord_pres = [j for j in JER_ORD if j in grp.index]
    grp = grp.reindex(ord_pres).dropna()
    if len(grp) == 0:
        print("  [SKIP] 27_chart — sin datos"); return
    jers = [j.title() for j in grp.index.tolist()]
    z_b  = grp["z_baseline"].tolist(); z_r = grp["z_resultado"].tolist()
    n_j  = [int(df[df["jer_u"] == j]["rut_key"].count()) for j in grp.index.tolist()]

    fig, ax = _ax()
    xa = np.arange(len(jers)); w = 0.35
    ax.bar(xa - w/2, z_b, width=w, color="#1565C0", alpha=0.85, edgecolor="none", label="Baseline")
    ax.bar(xa + w/2, z_r, width=w, color="#2E7D32", alpha=0.85, edgecolor="none", label="Resultado")

    for i, (b, r, nv) in enumerate(zip(z_b, z_r, n_j)):
        col_arr = "#2E7D32" if r > b else "#C62828"
        ax.annotate("", xy=(xa[i] + w/2, r), xytext=(xa[i] - w/2, b),
                    arrowprops=dict(arrowstyle="->", color=col_arr, lw=1.3,
                                   connectionstyle="arc3,rad=-0.2"))
        ax.text(xa[i], min(b, r) - 0.04, f"n={nv}",
                ha="center", va="top", fontsize=7.5, color="#666666")

    ax.axhline(0, color=C_ANN, linewidth=1, linestyle=":", alpha=0.55)
    ax.set_xticks(xa)
    ax.set_xticklabels(jers, fontsize=8.5, color=C_TEXT, rotation=20, ha="right")
    _style_word(ax)
    ax.set_ylabel("z-score SAT promedio", color=C_TEXT, fontsize=9.5)
    ax.legend(fontsize=9, framealpha=0.85, labelcolor=C_TEXT,
              facecolor="white", edgecolor="#888888")
    plt.tight_layout(pad=0.8)
    _save(fig, "27_chart.png")

# ─────────────────────────────────────────────────────────────────────────────
# 7. 28_chart.png — SAT por Jerarquia Diplomado (Baseline → Resultado)
# ─────────────────────────────────────────────────────────────────────────────
def chart_28():
    JER_ORD = ["INSTRUCTOR REGULAR","INSTRUCTOR DOCENTE","ASISTENTE REGULAR","ASISTENTE DOCENTE",
               "ASOCIADO REGULAR","ASOCIADO DOCENTE","TITULAR REGULAR","TITULAR DOCENTE"]
    df = sat[(sat["n_diplomado"] > 0) & (sat["n_taller"] == 0) & (sat["n_proyecto"] == 0)].copy()
    if len(df) < 2:
        print(f"  [SKIP] 28_chart — muestra insuficiente (n={len(df)})"); return
    df["jer_u"] = df["jerarquia"].str.strip().str.upper()
    grp = df.groupby("jer_u")[["z_baseline","z_resultado"]].mean()
    ord_pres = [j for j in JER_ORD if j in grp.index]
    grp = grp.reindex(ord_pres).dropna()
    if len(grp) == 0:
        print("  [SKIP] 28_chart — sin jerarquias con datos"); return
    jers = [j.title() for j in grp.index.tolist()]
    z_b  = grp["z_baseline"].tolist(); z_r = grp["z_resultado"].tolist()
    n_j  = [int(df[df["jer_u"] == j]["rut_key"].count()) for j in grp.index.tolist()]

    fig, ax = _ax()
    xa = np.arange(len(jers)); w = 0.35
    ax.bar(xa - w/2, z_b, width=w, color="#E65100", alpha=0.85, edgecolor="none", label="Baseline")
    ax.bar(xa + w/2, z_r, width=w, color="#2E7D32", alpha=0.85, edgecolor="none", label="Resultado")

    for i, (b, r, nv) in enumerate(zip(z_b, z_r, n_j)):
        col_arr = "#2E7D32" if r > b else "#C62828"
        ax.annotate("", xy=(xa[i] + w/2, r), xytext=(xa[i] - w/2, b),
                    arrowprops=dict(arrowstyle="->", color=col_arr, lw=1.3,
                                   connectionstyle="arc3,rad=-0.2"))
        ax.text(xa[i], min(b, r) - 0.04, f"n={nv}",
                ha="center", va="top", fontsize=7.5, color="#666666")

    ax.axhline(0, color=C_ANN, linewidth=1, linestyle=":", alpha=0.55)
    ax.set_xticks(xa)
    ax.set_xticklabels(jers, fontsize=8.5, color=C_TEXT, rotation=20, ha="right")
    _style_word(ax)
    ax.set_ylabel("z-score SAT promedio", color=C_TEXT, fontsize=9.5)
    ax.legend(fontsize=9, framealpha=0.85, labelcolor=C_TEXT,
              facecolor="white", edgecolor="#888888")
    plt.tight_layout(pad=0.8)
    _save(fig, "28_chart.png")

# ─────────────────────────────────────────────────────────────────────────────
# 8. extra_scatter_sat_nota.png — Scatter SAT vs Nota 3 paneles por año
# ─────────────────────────────────────────────────────────────────────────────
def chart_scatter():
    anios    = ["2023","2024","2025"]
    COL_CTRL = "#3D6594"   # azul medio
    COL_FORM = "#C84B10"   # naranja oscuro
    ALPHA    = 0.40
    MS       = 14

    scat_a = scat.copy()
    scat_a["anio"] = scat_a["periodo"].str[:4]
    scat_a = scat_a.dropna(subset=["sat","nota_promedio"])

    stats_by_year = {}
    for y in anios:
        s = scat_a[scat_a["anio"] == y]
        if len(s) < 5:
            stats_by_year[y] = dict(r=float("nan"), p=float("nan"), n_sec=0, n_f=0, n_c=0)
            continue
        r, p = scipy_stats.pearsonr(s["sat"], s["nota_promedio"])
        stats_by_year[y] = dict(r=r, p=p, n_sec=len(s),
                                n_f=int(s["rut_docente"][s["formado"]].nunique()),
                                n_c=int(s["rut_docente"][~s["formado"]].nunique()))

    PANEL_GAP = 0.025
    fig = plt.figure(figsize=(14, 5), facecolor="none")
    fig.patch.set_alpha(0.0)

    gx = 0.05; gy = 0.12; gw = 0.91; gh = 0.80
    panel_w = (gw - PANEL_GAP * 2) / 3

    for i, y in enumerate(anios):
        s   = scat_a[scat_a["anio"] == y]
        sf  = s[s["formado"]]
        sc2 = s[~s["formado"]]
        st  = stats_by_year[y]

        ax_l = gx + i * (panel_w + PANEL_GAP)
        ax   = fig.add_axes([ax_l, gy, panel_w, gh], facecolor="none", zorder=5)

        ax.scatter(sc2["sat"], sc2["nota_promedio"],
                   c=COL_CTRL, alpha=ALPHA, s=MS, marker="o",
                   linewidths=0, zorder=2,
                   label=f"Sin formación (n={st['n_c']})")
        ax.scatter(sf["sat"], sf["nota_promedio"],
                   c=COL_FORM, alpha=ALPHA + 0.15, s=MS, marker="o",
                   linewidths=0, zorder=3,
                   label=f"Formados (n={st['n_f']})")

        if len(s) >= 5:
            x_all = s["sat"].values; y_all = s["nota_promedio"].values
            m, b  = np.polyfit(x_all, y_all, 1)
            xr    = np.array([x_all.min(), x_all.max()])
            ax.plot(xr, m * xr + b, "--", color=C_ANN, linewidth=1.5, alpha=0.70,
                    zorder=4, label=f"Tendencia (r={st['r']:.2f})")

        # Estilo claro
        ax.tick_params(axis="x", colors=C_TEXT, labelsize=9, length=3)
        ax.tick_params(axis="y", colors=C_TEXT, labelsize=9, length=3)
        for sp in ax.spines.values():
            sp.set_edgecolor(C_SPINE); sp.set_alpha(0.55); sp.set_linewidth(0.8)
        ax.yaxis.grid(True, color=C_GRID, alpha=0.6, linewidth=0.5)
        ax.xaxis.grid(True, color=C_GRID, alpha=0.4, linewidth=0.4)
        ax.set_axisbelow(True)

        ax.set_xlim(1, 7); ax.set_ylim(1, 7)
        if i == 0:
            ax.set_ylabel("Nota promedio alumnos (sobre 7)", color=C_TEXT, fontsize=8.5)
        else:
            ax.set_yticklabels([])
        ax.set_xlabel("SAT docente (sobre 7)", color=C_TEXT, fontsize=8.5)
        ax.set_xticks([1, 2, 3, 4, 5, 6, 7])
        ax.set_yticks([1, 2, 3, 4, 5, 6, 7])

        ax.set_title(f"Año {y}", color=C_TEXT, fontsize=10.5, fontweight="bold", pad=6)

        leg = ax.legend(fontsize=7.2, framealpha=0.85,
                        facecolor="white", edgecolor="#AAAAAA",
                        loc="upper left", markerscale=1.5,
                        handlelength=0.8, borderpad=0.5, labelspacing=0.35)
        for txt in leg.get_texts():
            txt.set_color(C_TEXT)

        if not np.isnan(st["r"]):
            p_str = "< 0.001" if st["p"] < 0.001 else f"= {st['p']:.3f}"
            box_txt = f"r = {st['r']:.2f}\np {p_str}\n{st['n_sec']} secciones"
            ax.text(0.97, 0.05, box_txt,
                    transform=ax.transAxes, fontsize=8,
                    va="bottom", ha="right", color=C_TEXT,
                    bbox=dict(boxstyle="round,pad=0.45",
                              facecolor="#F0F4F0",
                              edgecolor="#6AAA40", alpha=0.92))

    _save(fig, "extra_scatter_sat_nota.png")

# ─────────────────────────────────────────────────────────────────────────────
# Ejecutar
# ─────────────────────────────────────────────────────────────────────────────
print("Generando graficos Word v6 (texto negro)...")
chart_22();   print("  [1/8] SAT z-score 6 periodos")
chart_37();   print("  [2/8] EDD evolucion 2022-2025")
chart_30();   print("  [3/8] Aprobacion Global")
chart_31();   print("  [4/8] Evolucion Aprobacion por Periodo")
chart_38();   print("  [5/8] EDD por Tipo de Formacion")
chart_27();   print("  [6/8] SAT Jerarquia Taller")
chart_28();   print("  [7/8] SAT Jerarquia Diplomado")
chart_scatter(); print("  [8/8] Scatter SAT vs Nota")
print(f"\nTodos los graficos guardados en:\n  {OUT}")
