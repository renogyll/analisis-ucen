"""
config.py — Rutas base y constantes del proyecto Análisis UCEN
Importar desde cualquier script: from config import CASCADE, OUTPUTS, COL_FORM
"""
import os

BASE = os.path.dirname(os.path.abspath(__file__))

# ── Rutas de datos ────────────────────────────────────────────────────────────
DATA_RAW = os.path.join(BASE, "data", "raw")
CASCADE  = os.path.join(BASE, "data", "cascade")
OUTPUTS  = os.path.join(BASE, "outputs")

# Atajos a cada nivel de la cascada
C00_BASE          = os.path.join(CASCADE, "00_base")
C01_JORNADA       = os.path.join(CASCADE, "01_jornada")
C02_HONORARIO     = os.path.join(CASCADE, "02_honorario")
C03_JERARQUIZADOS = os.path.join(CASCADE, "03_jerarquizados")
C04_FORMADOS      = os.path.join(CASCADE, "04_formados_p3")
C05_APTOS         = os.path.join(CASCADE, "05_aptos_p3")

# Atajos a outputs
OUT_PPTX = os.path.join(OUTPUTS, "pptx")
OUT_DOCX = os.path.join(OUTPUTS, "docx")
OUT_PNG  = os.path.join(OUTPUTS, "png")

# ── Constantes de diseño PPTX ─────────────────────────────────────────────────
SW_EMU = 12192000
SH_EMU = 6858000
SW = 12.7   # pulgadas
SH = 7.15

PIC_L = 786581;  PIC_T = 1125000; PIC_W = 10599174; PIC_H = 3720000
BUL_L = 786581;  BUL_T = 4870000; BUL_W = 10599174; BUL_H = 1870000
TITLE_L = PIC_L; TITLE_T = 185000; TITLE_W = PIC_W;  TITLE_H = 710000

# ── Paleta de colores ─────────────────────────────────────────────────────────
COL_FORM   = "#5C9BD6"   # azul — grupo formados
COL_CTRL   = "#FFB74D"   # amarillo — grupo control
COL_FORM_P = "#5C9BD6"   # azul — formados en perfiles
COL_CTRL_P = "#FFB74D"   # amarillo — control en perfiles

BG_DARK    = "#1C1C2E"   # fondo oscuro slides
TEXT_WHITE = "#FFFFFF"
TEXT_GRAY  = "#AAAAAA"
