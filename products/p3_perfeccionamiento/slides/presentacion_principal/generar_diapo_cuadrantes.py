"""
Standalone: DIAPO_cuadrantes_v3.pptx — 1 slide, 4 cuadrantes iguales
Marco metodológico P3 — 2 secciones por cuadrante + panel azul oscuro unificado.
"""
import sys; sys.stdout.reconfigure(encoding="utf-8")
import os, pathlib
import pandas as pd
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

BASE      = os.path.dirname(os.path.abspath(__file__))
REPO      = str(pathlib.Path(BASE).parents[3])
CASCADE   = os.path.join(REPO, "data", "cascade")
OUT_DIR   = os.path.join(BASE, "dark_slides_v3")
SHARED_BG = os.path.join(OUT_DIR, "_background.png")
OUT_PPTX  = r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO\Downloads\DIAPO_cuadrantes_v3.pptx"

SW_EMU = 12192000
SH_EMU = 6858000

# ── Datos reales ──────────────────────────────────────────────────────────────
sat = pd.read_csv(os.path.join(CASCADE, "05_aptos_p3", "p3_sat_zscore.csv"),
                  encoding="utf-8-sig")
vc  = sat["tipos_formacion"].value_counts()
n_t = len(sat)
lbl = [str(t).title().replace("Taller", "Oferta formativa") for t in vc.index]
val = vc.values.tolist()
n_of = sum(v for l, v in zip(lbl, val) if l == "Oferta formativa")
n_di = sum(v for l, v in zip(lbl, val) if l == "Diplomado")
n_pr = sum(v for l, v in zip(lbl, val) if l == "Proyecto")
n_mx = sum(v for l, v in zip(lbl, val) if "|" in l)
print(f"Universo: {n_t}  OF={n_of}  Di={n_di}  Pr={n_pr}  Mx={n_mx}")

# ── Colores ───────────────────────────────────────────────────────────────────
W    = RGBColor(0xFF, 0xFF, 0xFF)
CEL  = RGBColor(0x7E, 0xBF, 0xF0)
AMA  = RGBColor(0xFF, 0xC8, 0x00)
GRI  = RGBColor(0xCC, 0xDD, 0xEE)
AZL  = RGBColor(0x3A, 0x6E, 0xA8)
BGD  = RGBColor(0x0B, 0x1A, 0x35)   # azul oscuro — panel unificado
B1C  = RGBColor(0x14, 0x5E, 0x9E)
B2C  = RGBColor(0x1B, 0x7A, 0x55)
B3C  = RGBColor(0x8C, 0x4A, 0x10)
B4C  = RGBColor(0x5B, 0x21, 0x86)

# ── PPTX ─────────────────────────────────────────────────────────────────────
prs = Presentation()
prs.slide_width  = Emu(SW_EMU)
prs.slide_height = Emu(SH_EMU)
sl = prs.slides.add_slide(prs.slide_layouts[6])
sl.shapes.add_picture(SHARED_BG, Emu(0), Emu(0), Emu(SW_EMU), Emu(SH_EMU))

# ── Helpers ───────────────────────────────────────────────────────────────────
def box(text, lx, ty, w, h, sz=8.5, bold=False, italic=False,
        color=W, align=PP_ALIGN.LEFT):
    txb = sl.shapes.add_textbox(Emu(lx), Emu(ty), Emu(w), Emu(h))
    tf  = txb.text_frame; tf.word_wrap = True
    for i, line in enumerate(str(text).split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        run = p.add_run(); run.text = line
        run.font.size = Pt(sz); run.font.bold = bold; run.font.italic = italic
        run.font.color.rgb = color; run.font.name = "Calibri"

def rct(lx, ty, w, h, color, border=None):
    sh = sl.shapes.add_shape(1, Emu(lx), Emu(ty), Emu(w), Emu(h))
    sh.fill.solid(); sh.fill.fore_color.rgb = color
    if border:
        sh.line.color.rgb = border
        sh.line.width = Pt(0.75)
    else:
        sh.line.fill.background()

# ── Layout ────────────────────────────────────────────────────────────────────
ML    = 186000
MR    = 12006000
VDIV  = 6096000
HDIV  = 3672000
BDY_T = 525000

QW_L = VDIV - ML - 28000
QW_R = MR - VDIV - 52000
QX_L = ML
QX_R = VDIV + 52000

INNER = 35000   # margen interno horizontal en cada cuadrante

# Título principal
box("Marco Metodológico por Bloque — Programa P3",
    ML, 140000, MR - ML, 340000, sz=16, bold=True, align=PP_ALIGN.CENTER)

# Línea bajo título
rct(ML, 512000, MR - ML, 10000, AZL)

# Panel azul oscuro unificado (cubre los 4 cuadrantes)
PANEL_H = SH_EMU - BDY_T - 75000
rct(ML, BDY_T, MR - ML, PANEL_H, BGD, border=AZL)

# Divisores sobre el panel (z-order posterior = encima)
rct(VDIV, BDY_T, 12000, PANEL_H, AZL)    # vertical
rct(ML,   HDIV,  MR - ML, 12000,  AZL)   # horizontal

# ── Función cuadrante (2 secciones) ──────────────────────────────────────────
def quadrant(lx, ty, w, num, name, bc, universo, analysis):
    # Banda de color con título del bloque
    rct(lx, ty, w, 248000, bc)
    box(f"BLOQUE {num}  ·  {name}",
        lx + 22000, ty + 14000, w - 44000, 225000,
        sz=10.5, bold=True, color=AMA)

    cy = ty + 275000

    # Sección 1: Descripción del Universo
    box("Descripción del Universo — Filtros y Metodología",
        lx + INNER, cy, w - 2 * INNER, 190000,
        sz=8.5, bold=True, color=CEL)
    cy += 200000
    box(universo,
        lx + INNER, cy, w - 2 * INNER, 1080000,
        sz=8.2, color=W)
    cy += 1105000

    rct(lx, cy, w, 8000, AZL)
    cy += 38000

    # Sección 2: Descripción del Análisis
    box("Descripción del Análisis",
        lx + INNER, cy, w - 2 * INNER, 190000,
        sz=8.5, bold=True, color=CEL)
    cy += 200000
    box(analysis,
        lx + INNER, cy, w - 2 * INNER, 1080000,
        sz=8.2, color=W)

# ═══════════════════════════════════════════════════════════════════════════════
# Q1 — BLOQUE I: Caracterización  (top-left)
# ═══════════════════════════════════════════════════════════════════════════════
quadrant(
    QX_L, BDY_T, QW_L,
    "I", "Caracterización", B1C,
    universo=(
        f"N°=316 Aptos P3 — análisis descriptivo, sin grupo de control. "
        f"Derivación: 1.144 universo base → 726 formados en P3 → 316 con SAT "
        f"válido ≥3 períodos (pre · durante · post) → 206 con EDD disponible.\n"
        f"Criterios: cobertura ≥40%, sección ≥7 alumnos matriculados; "
        f"excluye asignaturas prácticas, proyecto de título, seminario y ciclo formativo."
    ),
    analysis=(
        f"Distribución de los {n_t} Aptos P3 por tipo de formación: "
        f"OF pura N°={n_of}  ·  Diplomado N°={n_di}  ·  "
        f"Proyecto N°={n_pr}  ·  Mixta N°={n_mx}.\n"
        "Frecuencias y porcentajes por categoría, jerarquía académica, "
        "tipo de contrato (Jornada / Honorario), facultad y período (2022–2025)."
    )
)

# ═══════════════════════════════════════════════════════════════════════════════
# Q2 — BLOQUE II: Satisfacción Estudiantil SAT  (top-right)
# ═══════════════════════════════════════════════════════════════════════════════
quadrant(
    QX_R, BDY_T, QW_R,
    "II", "Satisfacción Estudiantil — SAT", B2C,
    universo=(
        "Tratamiento N°=316 Aptos P3 (SAT válido pre y post, cobertura ≥40%). "
        "Control N°=300 docentes sin P3, con ≥1 SAT en período 2023–2025. "
        "De 726 formados, 316 cumplen el criterio de validez en ambas ventanas.\n"
        "Estandarización: z = (SAT docente − media facultad · período) / DE facultad · período. "
        "Criterios: cobertura ≥40%, sección ≥7 alumnos; excluye asig. prácticas y "
        "de escala no comparable."
    ),
    analysis=(
        "Comparación del SAT z-score: baseline (período pre) vs resultado "
        "(durante y post intervención P3). "
        "% de Recomendación Estudiantil (P4526 — Sí/No) ponderada por N° respondentes.\n"
        "Período pre = promedio de todos los semestres anteriores a la primera "
        "instancia formativa del docente."
    )
)

# ═══════════════════════════════════════════════════════════════════════════════
# Q3 — BLOQUE III: Rendimiento Académico  (bottom-left)
# ═══════════════════════════════════════════════════════════════════════════════
quadrant(
    QX_L, HDIV + 22000, QW_L,
    "III", "Rendimiento Académico", B3C,
    universo=(
        "Tratamiento (perfil): N°=316 Aptos P3. "
        "Tratamiento (amplio): N°=619 formados con notas disponibles. "
        "Control: N°=300 sin P3, con notas en período 2023–2025. "
        "Los 316 son subconjunto de los 619.\n"
        "Criterios: sección ≥7 alumnos matriculados; excluye asignaturas "
        "prácticas y de escala no comparable. "
        "Período pre = promedio semestres anteriores a primera instancia P3."
    ),
    analysis=(
        "Comparación antes–después de la intervención formativa. "
        "Métricas: nota promedio alumnos (escala 1–7) y % aprobación (nota ≥4.0).\n"
        "La doble muestra (316 y 619) permite triangular resultados y "
        "descartar artefactos de selección en el grupo de tratamiento."
    )
)

# ═══════════════════════════════════════════════════════════════════════════════
# Q4 — BLOQUE IV: Evaluación de Desempeño EDD  (bottom-right)
# ═══════════════════════════════════════════════════════════════════════════════
quadrant(
    QX_R, HDIV + 22000, QW_R,
    "IV", "Evaluación de Desempeño — EDD", B4C,
    universo=(
        "Tratamiento N°=206 Aptos P3 con EDD disponible "
        "(110 de los 316 no tienen registro EDD — son excluidos). "
        "Control N°=130 docentes sin P3, con EDD disponible en ventana 2023–2024.\n"
        "Instrumento: evaluación anual por jefatura directa, "
        "escala 0–1 expresada como % (0%–100%)."
    ),
    analysis=(
        "Comparación de EDD promedio entre formados P3 y control "
        "en ventana 2023–2024. "
        "Evolución temporal por año y distribución por facultad.\n"
        "Control seleccionado del universo base de docentes sin formación P3 "
        "con registro EDD disponible en la misma ventana temporal."
    )
)

# ── Guardar ───────────────────────────────────────────────────────────────────
prs.save(OUT_PPTX)
print(f"\n✓ Guardado: {OUT_PPTX}")
print("  1 slide  ·  4 cuadrantes  ·  2 secciones  ·  panel azul oscuro unificado")
