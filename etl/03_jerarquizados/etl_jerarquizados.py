import sys; sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
from sqlalchemy import create_engine, text
import os

engine = create_engine("postgresql://ucen_user:ucen2026@localhost:5432/ucen")

SIN_NOM = {"SIN JERARQUÍA", "SIN JERARQUIA", ""}
SIN_DOT = {"NO INFORMA", "SIN JERARQUÍA", "SIN JERARQUIA", ""}

def jer_nom_ok(val):
    return str(val).strip().upper() not in SIN_NOM

def jer_dot_ok(val):
    return str(val).strip().upper() not in SIN_DOT

with engine.connect() as conn:
    ambos    = pd.read_sql(text("SELECT * FROM analisis.docente_ambos"),         conn)
    solo_nom = pd.read_sql(text("SELECT * FROM analisis.docente_solo_nomina"),   conn)
    solo_dot = pd.read_sql(text("SELECT * FROM analisis.docente_solo_dotacion"), conn)

print(f"Fuentes: ambos={len(ambos)}, solo_nomina={len(solo_nom)}, solo_dotacion={len(solo_dot)}")

COLS = [
    "rut_key", "nombre", "sexo", "jerarquia", "jerarquia_dot",
    "tipo_contrato", "unidad_facultad", "departamento",
    "nivel_formacion", "nombre_grado",
    "fecha_ingreso", "antiguedad_anios", "tramo_antiguedad",
    "fecha_nacimiento", "edad_anios", "tramo_edad",
    "fuente",
]

filas = []

# ── docente_ambos: tiene datos de ambas fuentes ───────────────────────────────
for _, r in ambos.iterrows():
    ok_n = jer_nom_ok(r.get("jerarquia", ""))
    ok_d = jer_dot_ok(r.get("jerarquia_dot", ""))
    if not (ok_n or ok_d):
        continue
    if ok_n and ok_d:
        origen = "ambos"
    elif ok_n:
        origen = "nomina"
    else:
        origen = "dotacion"
    fila = {c: r.get(c, None) for c in COLS}
    fila["origen"] = origen
    fila["tiene_perfil_completo"] = True
    filas.append(fila)

# ── docente_solo_nomina: solo datos de nómina ─────────────────────────────────
for _, r in solo_nom.iterrows():
    if not jer_nom_ok(r.get("jerarquia", "")):
        continue
    fila = {c: r.get(c, None) for c in COLS}
    fila["origen"] = "nomina"
    fila["tiene_perfil_completo"] = False
    filas.append(fila)

# ── docente_solo_dotacion: solo datos de dotación ────────────────────────────
for _, r in solo_dot.iterrows():
    if not jer_dot_ok(r.get("jerarquia_dot", "")):
        continue
    fila = {c: r.get(c, None) for c in COLS}
    fila["origen"] = "dotacion"
    fila["tiene_perfil_completo"] = True
    filas.append(fila)

df = pd.DataFrame(filas)

# Deduplicar: si un rut aparece dos veces (no debería, pero por seguridad)
# conservar el que tenga origen más informativo: ambos > nomina > dotacion
orden = {"ambos": 0, "nomina": 1, "dotacion": 2}
df["_ord"] = df["origen"].map(orden)
df = df.sort_values("_ord").drop_duplicates(subset="rut_key", keep="first").drop(columns="_ord")
df = df.reset_index(drop=True)

out = os.path.join(os.path.dirname(__file__), "docente_918.csv")
df.to_csv(out, encoding="utf-8-sig", index=False)

print(f"\n{'='*55}")
print(f"UNIVERSO 918 — DOCENTES JERARQUIZADOS")
print(f"{'='*55}")
print(f"Total filas:          {len(df)}")
print(f"RUTs únicos:          {df['rut_key'].nunique()}")
print(f"\nDistribución por origen:")
print(df["origen"].value_counts().to_string())
print(f"\nPerfil completo (dotación disponible):")
print(df["tiene_perfil_completo"].value_counts().to_string())
print(f"\nDistribución jerarquía:")
print(df["jerarquia"].value_counts(dropna=False).head(12).to_string())
print(f"\nCompletitud de campos clave (sobre {len(df)} docentes):")
for col in ["sexo","unidad_facultad","nivel_formacion","antiguedad_anios","edad_anios"]:
    n = df[col].notna().sum()
    print(f"  {col:<22}: {n:4d} ({n/len(df)*100:.0f}%)")
print(f"\nGuardado: {out}")
