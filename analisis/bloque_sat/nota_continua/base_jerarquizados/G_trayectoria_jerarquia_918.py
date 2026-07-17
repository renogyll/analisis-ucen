import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os

BASE = os.path.dirname(__file__)
OUT1 = os.path.join(BASE, "G_anios_hasta_jerarquia_918.png")
OUT2 = os.path.join(BASE, "G_edad_al_jerarquizarse_918.png")

matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11, "axes.titlesize": 14, "axes.labelsize": 12,
})

# ── Cargar y cruzar datos ─────────────────────────────────────────────────────
nom = pd.read_csv(
    os.path.join(BASE,"..","..","CONSOLIDADO DOCENTES 3-05-2026",
                 "CONSOLIDADO DOCENTES 3-05-2026.xlsx - NOMINA .csv"),
    dtype=str, encoding="utf-8-sig")
dot = pd.read_csv(
    os.path.join(BASE,"..","..","CONSOLIDADO DOCENTES 3-05-2026",
                 "CONSOLIDADO DOCENTES 3-05-2026.xlsx - DOTACION.csv"),
    dtype=str, encoding="utf-8-sig")
dot.columns = dot.columns.str.strip()
doc917 = pd.read_csv(os.path.join(BASE,"..","PROCESADO","docente_918.csv"),
                     encoding="utf-8-sig", dtype={"rut_key": str})

def clean_rut(s):
    return s.str.strip().str.replace(".", "", regex=False).str.split("-").str[0].str.strip()

nom["rut_key"]   = clean_rut(nom["RUT"])
dot["rut_key"]   = clean_rut(dot["RUT"])
doc917["rut_key"] = doc917["rut_key"].str.strip()

df = nom.merge(dot[["rut_key","FECHA NACIMIENTO","F. INGRESO"]], on="rut_key", how="left")
df  = df[df["rut_key"].isin(set(doc917["rut_key"]))].copy()

for col in ["FECHA JERARQUIZACIÓN","FECHA NACIMIENTO","F. INGRESO"]:
    df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=False)

df["anios_hasta_jer"] = (df["FECHA JERARQUIZACIÓN"] - df["F. INGRESO"]).dt.days / 365.25
df["edad_al_jer"]     = (df["FECHA JERARQUIZACIÓN"] - df["FECHA NACIMIENTO"]).dt.days / 365.25

df = df[
    (df["JERARQUÍA"] != "NO INFORMA") &
    df["anios_hasta_jer"].notna() & df["edad_al_jer"].notna() &
    (df["anios_hasta_jer"] >= 0)   & (df["edad_al_jer"] > 20)
].copy()

ORD_JER = [
    "INSTRUCTOR REGULAR", "INSTRUCTOR DOCENTE",
    "ASISTENTE REGULAR",  "ASISTENTE DOCENTE",
    "ASOCIADO REGULAR",   "ASOCIADO DOCENTE",
    "TITULAR REGULAR",    "TITULAR DOCENTE",
]
ABREV = {
    "INSTRUCTOR REGULAR": "Instructor\nRegular",
    "INSTRUCTOR DOCENTE": "Instructor\nDocente",
    "ASISTENTE REGULAR":  "Asist.\nRegular",
    "ASISTENTE DOCENTE":  "Asist.\nDocente",
    "ASOCIADO REGULAR":   "Asoc.\nRegular",
    "ASOCIADO DOCENTE":   "Asoc.\nDocente",
    "TITULAR REGULAR":    "Titular\nRegular",
    "TITULAR DOCENTE":    "Titular\nDocente",
}
COLORES = ["#42A5F5","#1976D2","#66BB6A","#388E3C",
           "#FFA726","#E65100","#EF5350","#B71C1C"]

jer_validos = [j for j in ORD_JER if j in df["JERARQUÍA"].values]
n_ok = len(df)
n_univ = len(doc917)

# ── Cascada ───────────────────────────────────────────────────────────────────
print("=" * 65)
print("  TRAYECTORIA ACADÉMICA — Años y Edad al jerarquizarse")
print("=" * 65)
print(f"  917 docentes jerarquizados (Universo 917)")
print(f"    ├── {n_ok} con datos de fecha ingreso + jerarquización + nacimiento")
print(f"    │")
print(f"    │   Gráfico 1 — Años desde ingreso hasta jerarquización actual")
for j in jer_validos:
    sub = df[df["JERARQUÍA"]==j]["anios_hasta_jer"]
    print(f"    │     ├── {ABREV[j].replace(chr(10),' '):22}: mediana={sub.median():.1f} años  (n={len(sub)})")
print(f"    │")
print(f"    │   Gráfico 2 — Edad al momento de jerarquizarse")
for j in jer_validos:
    sub = df[df["JERARQUÍA"]==j]["edad_al_jer"]
    print(f"    │     ├── {ABREV[j].replace(chr(10),' '):22}: mediana={sub.median():.1f} años  (n={len(sub)})")
print(f"    └── {n_univ - n_ok} sin datos suficientes para el cálculo")
print("=" * 65)

def make_boxplot(ax, col, jer_validos, df, ABREV, COLORES, title, ylabel, show_n=True):
    datos = [df[df["JERARQUÍA"]==j][col].dropna().values for j in jer_validos]
    ns    = [len(df[df["JERARQUÍA"]==j][col].dropna()) for j in jer_validos]
    # n incorporado en el label para evitar solapamiento
    labels = [f"{ABREV[j]}\n(n={n})" for j, n in zip(jer_validos, ns)]

    bp = ax.boxplot(datos, patch_artist=True,
                    medianprops=dict(color="black", linewidth=2.5),
                    whiskerprops=dict(linewidth=1.5),
                    capprops=dict(linewidth=1.5),
                    flierprops=dict(marker="o", markersize=4, alpha=0.4))
    for patch, color in zip(bp["boxes"], COLORES[:len(jer_validos)]):
        patch.set_facecolor(color)
        patch.set_alpha(0.75)

    for i, (j, color) in enumerate(zip(jer_validos, COLORES)):
        sub = df[df["JERARQUÍA"]==j][col].dropna()
        med = sub.median()
        ax.text(i+1, med + 0.3, f"{med:.1f}",
                ha="center", fontsize=9, fontweight="bold", color="black")

    ax.set_xticks(range(1, len(jer_validos)+1))
    ax.set_xticklabels(labels, fontsize=8.5)
    ax.set_ylabel(ylabel)
    ax.set_title(title, pad=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

# ══════════════════════════════════════════════════════════════════════════════
# GRÁFICO 1 — Años desde ingreso hasta jerarquización actual
# ══════════════════════════════════════════════════════════════════════════════
fig1, ax1 = plt.subplots(figsize=(13, 7))
fig1.suptitle(
    "¿Cuántos años tardaron en alcanzar su jerarquía actual?\n"
    "Tiempo desde ingreso a UCEN hasta fecha de jerarquización · Universo 917",
    fontsize=13, fontweight="bold")

make_boxplot(ax1, "anios_hasta_jer", jer_validos, df, ABREV, COLORES,
             "Años desde ingreso a UCEN hasta jerarquización actual",
             "Años transcurridos")

# Línea de tendencia por mediana
medianas_aj = [df[df["JERARQUÍA"]==j]["anios_hasta_jer"].median() for j in jer_validos]
ax1.plot(range(1, len(jer_validos)+1), medianas_aj,
         color="#333333", linewidth=1.5, linestyle="--", alpha=0.5,
         marker="D", markersize=5, label="Mediana por jerarquía")
ax1.legend(fontsize=10, loc="upper left")

# Nota metodológica
ax1.text(0.99, 0.02,
         "Nota: mide años desde el primer ingreso a UCEN,\nno experiencia académica previa.",
         transform=ax1.transAxes, ha="right", va="bottom",
         fontsize=8.5, color="#666666", fontstyle="italic",
         bbox=dict(boxstyle="round,pad=0.3", facecolor="#F5F5F5",
                   edgecolor="#BDBDBD", alpha=0.9))

plt.tight_layout()
plt.savefig(OUT1, dpi=150, bbox_inches="tight")
plt.close()
print(f"\nGuardado: {OUT1}")

# ══════════════════════════════════════════════════════════════════════════════
# GRÁFICO 2 — Edad al momento de jerarquizarse
# ══════════════════════════════════════════════════════════════════════════════
fig2, ax2 = plt.subplots(figsize=(13, 7))
fig2.suptitle(
    "¿A qué edad alcanzaron su jerarquía actual?\n"
    "Edad del docente en la fecha de jerarquización · Universo 917",
    fontsize=13, fontweight="bold")

make_boxplot(ax2, "edad_al_jer", jer_validos, df, ABREV, COLORES,
             "Edad en la fecha de jerarquización",
             "Edad (años)")

medianas_ej = [df[df["JERARQUÍA"]==j]["edad_al_jer"].median() for j in jer_validos]
ax2.plot(range(1, len(jer_validos)+1), medianas_ej,
         color="#333333", linewidth=1.5, linestyle="--", alpha=0.5,
         marker="D", markersize=5, label="Mediana por jerarquía")
ax2.legend(fontsize=10, loc="upper left")

ax2.text(0.99, 0.02,
         "Nota: refleja la edad al obtener el rango actual,\nno la experiencia universitaria total.",
         transform=ax2.transAxes, ha="right", va="bottom",
         fontsize=8.5, color="#666666", fontstyle="italic",
         bbox=dict(boxstyle="round,pad=0.3", facecolor="#F5F5F5",
                   edgecolor="#BDBDBD", alpha=0.9))

plt.tight_layout()
plt.savefig(OUT2, dpi=150, bbox_inches="tight")
plt.close()
print(f"Guardado: {OUT2}")

# ── Bajadas ───────────────────────────────────────────────────────────────────
med_id = df[df["JERARQUÍA"]=="INSTRUCTOR DOCENTE"]["anios_hasta_jer"].median()
med_td = df[df["JERARQUÍA"]=="TITULAR DOCENTE"]["anios_hasta_jer"].median()
med_ad_ej = df[df["JERARQUÍA"]=="ASOCIADO DOCENTE"]["edad_al_jer"].median()
med_td_ej = df[df["JERARQUÍA"]=="TITULAR DOCENTE"]["edad_al_jer"].median()
med_id_ej = df[df["JERARQUÍA"]=="INSTRUCTOR DOCENTE"]["edad_al_jer"].median()

print(f"""
BAJADAS — Gráfico 1 (años hasta jerarquización)
• Los Instructores Docentes alcanzan su rango en los primeros meses tras
  incorporarse a UCEN (mediana {med_id:.1f} años), lo que refleja que el grado
  de Instructor es la jerarquía de entrada para académicos que recién se
  integran a la institución. En el extremo opuesto, los Titulares Docentes
  llevan en promedio {med_td:.1f} años en la institución antes de jerarquizarse,
  evidenciando que el escalón superior de la carrera requiere una trayectoria
  interna consolidada.

• Los rangos "Docente" (Asistente, Asociado y Titular Docente) muestran
  tiempos de jerarquización progresivamente mayores que sus pares "Regular",
  lo que sugiere que la vía Docente responde a una carrera académica más
  lenta y escalonada, mientras la vía Regular puede incorporar docentes
  con jerarquía asignada desde el primer contrato de jornada.

BAJADAS — Gráfico 2 (edad al jerarquizarse)
• La edad mediana al obtener la jerarquía actual sigue una curva ascendente
  clara: {med_id_ej:.0f} años en Instructor Docente, {med_ad_ej:.0f} en Asociado Docente y
  {med_td_ej:.0f} en Titular Docente. Esto confirma que los rangos superiores
  corresponden a docentes en la segunda mitad de su vida profesional,
  con amplia experiencia disciplinar y pedagógica acumulada.

• La amplia dispersión observada en Titular Docente (mayor rango entre
  caja y bigotes) indica que algunos docentes alcanzan ese nivel
  relativamente jóvenes (~50 años) mientras otros lo hacen cerca de
  los 80, evidenciando trayectorias académicas muy diversas dentro
  del mismo nivel jerárquico.
""")
