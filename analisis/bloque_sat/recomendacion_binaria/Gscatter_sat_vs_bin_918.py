import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from sqlalchemy import create_engine, text
import os

engine = create_engine("postgresql://ucen_user:ucen2026@localhost:5432/ucen")
BASE   = os.path.dirname(__file__)
OUT    = os.path.join(BASE, "Gscatter_sat_vs_bin_918.png")

# ── Cargar flag formado ───────────────────────────────────────────────────────
doc = pd.read_csv(os.path.join(BASE,"..","PROCESADO","docente_918.csv"),
                  encoding="utf-8-sig", dtype={"rut_key":str})
doc["rut_key"] = doc["rut_key"].str.strip()

with engine.connect() as conn:
    pf = pd.read_sql(text("SELECT DISTINCT rut_key FROM consolidados.participacion_formacion"), conn)
pf["rut_key"] = pf["rut_key"].astype(str).str.strip()
ruts_formados = set(pf["rut_key"])

# ── Datos sección-nivel: SAT_NOTA + SAT_BIN en misma sección ─────────────────
with engine.connect() as conn:
    df = pd.read_sql(text("""
        SELECT ep.rut_docente                                              AS rut_key,
               ep.periodo,
               ep.n_alumnos_evaluaron,
               r_sat.nota_promedio                                         AS sat,
               r_bin.pct_si
        FROM consolidados.evaluacion_periodo ep
        JOIN consolidados.evaluacion_respuesta r_sat
            ON r_sat.evaluacion_id = ep.evaluacion_id
            AND r_sat.pregunta_id  = 'SAT_NOTA'
        JOIN consolidados.evaluacion_respuesta r_bin
            ON r_bin.evaluacion_id = ep.evaluacion_id
            AND r_bin.pregunta_id  = 'SAT_BIN'
        WHERE ep.cobertura_pct     >= 40
          AND r_sat.nota_promedio  IS NOT NULL
          AND r_bin.pct_si         IS NOT NULL
    """), conn)

df["rut_key"] = df["rut_key"].astype(str).str.strip()
df["formado"] = df["rut_key"].isin(ruts_formados)
print(f"Secciones: {len(df):,}  |  Docentes: {df['rut_key'].nunique():,}")
print(f"Formados: {df[df['formado']]['rut_key'].nunique():,}  |  Sin formación: {df[~df['formado']]['rut_key'].nunique():,}")

r = df["sat"].corr(df["pct_si"])
print(f"Correlación SAT_NOTA vs pct_si: r = {r:.3f}")

matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 13, "axes.titlesize": 16, "axes.labelsize": 14,
    "xtick.labelsize": 12, "ytick.labelsize": 12, "legend.fontsize": 12,
})

fig, ax = plt.subplots(figsize=(11, 7))

for formado, color, label, alpha in [
    (False, "#607D8B", "Sin formación (n={:,})".format(df[~df["formado"]]["rut_key"].nunique()), 0.20),
    (True,  "#FF6B35", "Formados (n={:,})".format(df[df["formado"]]["rut_key"].nunique()),       0.30),
]:
    sub = df[df["formado"] == formado]
    ax.scatter(sub["sat"], sub["pct_si"], c=color, alpha=alpha,
               marker="o", s=18, label=label, linewidths=0)

# Línea de tendencia
coeffs = np.polyfit(df["sat"], df["pct_si"], 1)
x_line = np.linspace(df["sat"].min(), df["sat"].max(), 200)
ax.plot(x_line, np.polyval(coeffs, x_line), color="#333333",
        linewidth=2, linestyle="--", label=f"Tendencia global (r = {r:.2f})")

# Referencias
ax.axhline(df["pct_si"].mean(), color="#9E9E9E", linewidth=1,
           linestyle=":", alpha=0.7, label=f"% rec. media = {df['pct_si'].mean():.1f}%")
ax.axvline(df["sat"].mean(), color="#9E9E9E", linewidth=1,
           linestyle=":", alpha=0.7)

# Cuadrantes
x_mid = df["sat"].mean(); y_mid = df["pct_si"].mean()
ax.text(x_mid + 0.05, y_mid + 2,  "Bien evaluado\nAlta recomendación",
        fontsize=9, color="#4CAF50", alpha=0.7, ha="left")
ax.text(df["sat"].min() + 0.05, y_mid + 2, "Mal evaluado\nAlta recomendación",
        fontsize=9, color="#FF9800", alpha=0.7, ha="left")
ax.text(x_mid + 0.05, df["pct_si"].min() + 2, "Bien evaluado\nBaja recomendación",
        fontsize=9, color="#FF9800", alpha=0.7, ha="left")
ax.text(df["sat"].min() + 0.05, df["pct_si"].min() + 2, "Mal evaluado\nBaja recomendación",
        fontsize=9, color="#F44336", alpha=0.7, ha="left")

ax.set_xlabel("Evaluación docente SAT (nota sobre 7)")
ax.set_ylabel("% alumnos que recomendarían al docente")
ax.set_title(f"Correlación entre Nota SAT y % Recomendación\nUniverso 917 — 6 períodos 2023–2025  (n = {len(df):,} secciones)",
             pad=14, fontweight="bold")
ax.legend(loc="upper left", framealpha=0.9)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

strength = "muy fuerte" if abs(r) >= 0.80 else "fuerte" if abs(r) >= 0.60 else "moderada"
ax.text(0.98, 0.05,
        f"r = {r:.3f}  (correlación {strength})\np < 0.001",
        transform=ax.transAxes, ha="right", va="bottom", fontsize=12,
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#FFF9C4",
                  edgecolor="#FBC02D", alpha=0.95))

plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches="tight")
plt.close()
print(f"Guardado: {OUT}")
print(f"r = {r:.3f} | pendiente = {coeffs[0]:.2f} | n secciones = {len(df):,}")
