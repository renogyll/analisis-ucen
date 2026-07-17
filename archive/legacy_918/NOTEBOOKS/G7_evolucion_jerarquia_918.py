import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from sqlalchemy import create_engine, text
import os

engine = create_engine("postgresql://ucen_user:ucen2026@localhost:5432/ucen")
BASE   = os.path.dirname(__file__)
PERIODOS = ["2023-01","2023-02","2024-01","2024-02","2025-01","2025-02"]

# ── Cargar aptos P3 con jerarquía ─────────────────────────────────────────────
doc = pd.read_csv(os.path.join(BASE,"..","PROCESADO","docente_918.csv"),
                  encoding="utf-8-sig", dtype={"rut_key":str})
doc["rut_key"] = doc["rut_key"].str.strip()

p3 = pd.read_csv(os.path.join(BASE,"..","PROCESADO","p3_918.csv"),
                 encoding="utf-8-sig", dtype={"rut_key":str})
p3["rut_key"] = p3["rut_key"].str.strip()
aptos = p3[p3["apto_p3"]==True].copy()

def tipo_principal(row):
    if row["tipo_formacion"] == "DIPLOMADO": return "DIPLOMADO"
    if row["tipo_formacion"] == "PROYECTO":  return "PROYECTO"
    return "TALLER"
aptos["tipo_principal"] = aptos.apply(tipo_principal, axis=1)

# Un RUT puede tener múltiples filas → quedarse con tipo_principal más relevante
# (DIPLOMADO > PROYECTO > TALLER)
orden_tipo = {"DIPLOMADO":0,"PROYECTO":1,"TALLER":2}
aptos["_ord"] = aptos["tipo_principal"].map(orden_tipo)
aptos_uniq = (aptos.sort_values("_ord")
              .drop_duplicates("rut_key", keep="first")
              [["rut_key","tipo_principal"]])

# Merge con jerarquía
aptos_uniq = aptos_uniq.merge(doc[["rut_key","jerarquia","unidad_facultad"]], on="rut_key", how="left")
print(f"Aptos P3 únicos: {len(aptos_uniq)}")
print(aptos_uniq.groupby(["tipo_principal","jerarquia"]).size().to_string())

# ── SAT ponderado por docente × período (CM-1+CM-2) ──────────────────────────
with engine.connect() as conn:
    sat_raw = pd.read_sql(text("""
        SELECT e.rut_docente AS rut_key, e.periodo,
               e.n_alumnos_evaluaron, r.nota_promedio
        FROM consolidados.evaluacion_periodo e
        JOIN consolidados.evaluacion_respuesta r ON r.evaluacion_id = e.evaluacion_id
        WHERE r.pregunta_id = 'SAT_NOTA'
          AND e.cobertura_pct >= 40
          AND r.nota_promedio IS NOT NULL
    """), conn)

sat_raw["rut_key"] = sat_raw["rut_key"].astype(str).str.strip()
sat_raw["peso_nota"] = sat_raw["nota_promedio"] * sat_raw["n_alumnos_evaluaron"]
sat_per = (sat_raw.groupby(["rut_key","periodo"])
           .agg(sat_pond=("peso_nota","sum"), n_al=("n_alumnos_evaluaron","sum"))
           .reset_index())
sat_per["sat"] = sat_per["sat_pond"] / sat_per["n_al"]

# ── Estadísticas de referencia (universo 917) ─────────────────────────────────
ruts_917 = set(doc["rut_key"])
sat_pop = sat_per[sat_per["rut_key"].isin(ruts_917)].merge(
    doc[["rut_key","unidad_facultad"]], on="rut_key", how="inner")
n_por_uf = sat_pop.groupby("unidad_facultad")["rut_key"].nunique()
pequenas = n_por_uf[n_por_uf < 30].index.tolist()
sat_pop["uf_ref"] = sat_pop["unidad_facultad"].apply(
    lambda x: "Otras" if x in pequenas or pd.isna(x) else x)
stats_per = (sat_pop.groupby(["uf_ref","periodo"])["sat"]
             .agg(mu="mean", sigma="std").reset_index())
stats_per["sigma"] = stats_per["sigma"].fillna(1.0)
sigma_g = sat_pop["sat"].std(); mu_g = sat_pop["sat"].mean()
stats_per.loc[stats_per["sigma"] < 0.01, "sigma"] = sigma_g

# ── Z-score para aptos P3 en TODOS los períodos ───────────────────────────────
sat_aptos = sat_per[sat_per["rut_key"].isin(set(aptos_uniq["rut_key"]))].copy()
sat_aptos = sat_aptos.merge(aptos_uniq[["rut_key","tipo_principal","jerarquia","unidad_facultad"]],
                             on="rut_key", how="left")
sat_aptos["uf_ref"] = sat_aptos["unidad_facultad"].apply(
    lambda x: "Otras" if x in pequenas or pd.isna(x) else x)
sat_aptos = sat_aptos.merge(
    stats_per.rename(columns={"mu":"ref_mu","sigma":"ref_sigma"}),
    on=["uf_ref","periodo"], how="left")
sat_aptos["ref_mu"]    = sat_aptos["ref_mu"].fillna(mu_g)
sat_aptos["ref_sigma"] = sat_aptos["ref_sigma"].fillna(sigma_g)
sat_aptos["z"] = ((sat_aptos["sat"] - sat_aptos["ref_mu"]) / sat_aptos["ref_sigma"]).round(4)

# ── Abreviar jerarquías ───────────────────────────────────────────────────────
jer_map = {
    "INSTRUCTOR DOCENTE": "Instructor Doc.",
    "ASISTENTE DOCENTE":  "Asist. Docente",
    "ASISTENTE REGULAR":  "Asist. Regular",
    "ASOCIADO DOCENTE":   "Asoc. Docente",
    "ASOCIADO REGULAR":   "Asoc. Regular",
    "TITULAR DOCENTE":    "Titular Docente",
    "TITULAR REGULAR":    "Titular Regular",
}
sat_aptos["jer_short"] = sat_aptos["jerarquia"].map(jer_map).fillna(sat_aptos["jerarquia"])
ORD_JER = ["Instructor Doc.","Asist. Docente","Asist. Regular",
           "Asoc. Docente","Asoc. Regular","Titular Docente","Titular Regular"]
COLORES_JER = {
    "Instructor Doc.": "#1976D2",
    "Asist. Docente":  "#E91E63",
    "Asist. Regular":  "#9C27B0",
    "Asoc. Docente":   "#FF9800",
    "Asoc. Regular":   "#009688",
    "Titular Docente": "#F44336",
    "Titular Regular": "#4CAF50",
}

matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 13, "axes.titlesize": 16, "axes.labelsize": 14,
    "xtick.labelsize": 11, "ytick.labelsize": 12, "legend.fontsize": 11,
})

# ── Función para crear un gráfico por tipo ────────────────────────────────────
def grafico_tipo(tipo, min_n=5):
    sub = sat_aptos[sat_aptos["tipo_principal"]==tipo]
    ruts_tipo = set(aptos_uniq[aptos_uniq["tipo_principal"]==tipo]["rut_key"])
    n_total = len(ruts_tipo)

    # N por jerarquía en este tipo
    n_jer = (aptos_uniq[aptos_uniq["tipo_principal"]==tipo]
             .groupby("jerarquia")["rut_key"].nunique())
    jer_map_inv = {v:k for k,v in jer_map.items()}

    # Pivot: z promedio por jerarquía × período
    agg = (sub.groupby(["jer_short","periodo"])["z"]
           .agg(z_mean="mean", n="count").reset_index())

    fig, ax = plt.subplots(figsize=(12, 7))

    plotted = []
    for jer in ORD_JER:
        jer_orig = jer_map_inv.get(jer, jer)
        n_doc = int(n_jer.get(jer_orig, 0))
        if n_doc < min_n:
            continue
        sub_jer = agg[agg["jer_short"]==jer].set_index("periodo")
        ys = [sub_jer["z_mean"].get(p, np.nan) for p in PERIODOS]
        if sum(pd.notna(y) for y in ys) < 2:
            continue
        color = COLORES_JER.get(jer, "#333333")
        ax.plot(range(len(PERIODOS)), ys, marker="o", color=color,
                linewidth=2.2, markersize=8, label=f"{jer} (n={n_doc})")
        # Anotar último punto no-nan
        last_i = max(i for i,y in enumerate(ys) if pd.notna(y))
        ax.annotate(f"{ys[last_i]:+.2f}",
                    xy=(last_i, ys[last_i]),
                    xytext=(6, 0), textcoords="offset points",
                    fontsize=10, color=color, fontweight="bold")
        plotted.append(jer)

    # Zona del evento formativo
    if tipo == "DIPLOMADO":
        ax.axvspan(2.0, 3.9, alpha=0.07, color="#FF9800",
                   label="Año del diplomado (2024)")
        ax.axvline(2.0, color="#FF9800", linewidth=1, linestyle="--", alpha=0.5)
        ax.axvline(3.9, color="#FF9800", linewidth=1, linestyle="--", alpha=0.5)
    elif tipo == "TALLER":
        ax.axvspan(0.5, 3.5, alpha=0.05, color="#2196F3",
                   label="Período principal talleres (2023-02 → 2024-02)")

    ax.axhline(0, color="gray", linewidth=1, linestyle=":", alpha=0.6)
    ax.set_xticks(range(len(PERIODOS)))
    ax.set_xticklabels(PERIODOS, rotation=15)
    ax.set_ylabel("Z-score promedio\n(posición relativa en facultad)")
    ax.set_xlabel("Período académico")
    ax.set_title(f"Evolución Z-score SAT por Jerarquía\n{tipo} — Universo 917 (n={n_total} aptos P3)",
                 pad=14, fontweight="bold")
    ax.legend(loc="lower right", framealpha=0.9, bbox_to_anchor=(1.0, 0.01))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    out = os.path.join(BASE, f"G7_{tipo.lower()}_jerarquia_918.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Guardado: {out}  ({len(plotted)} jerarquías graficadas)")
    return out

# ── Generar los 2 gráficos ────────────────────────────────────────────────────
grafico_tipo("TALLER",    min_n=2)
grafico_tipo("DIPLOMADO", min_n=2)
print("\nListo — 2 gráficos de evolución por jerarquía generados.")
