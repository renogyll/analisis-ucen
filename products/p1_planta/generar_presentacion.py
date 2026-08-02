"""
P1 — Caracterización del Cuerpo Académico de Planta
Ensamblador: junta en un solo PPTX la portada, las diapositivas estructurales por
bloque (grillas de apertura + Universo/Índice/Hallazgos) y las diapositivas de
caracterizacion/ ya aprobadas.

Cada sub-tema vive en su propia carpeta con su script generador standalone (sigue
funcionando igual que antes — produce su propio pptx individual). Este ensamblador
importa la función `agregar`/`agregar_todas`/`agregar_ttest` de cada uno y las llama
en secuencia sobre una sola Presentation, sin duplicar lógica ni copiar diapositivas
a mano (las copias de slide entre .pptx con python-pptx son frágiles con imágenes).
Las diapositivas estructurales (portada, grillas, universo/índice/hallazgos) viven en
`slides_estructura.py`, al lado de este archivo.

Para agregar un nuevo sub-tema al consolidado: asegurarse de que su script exponga
`agregar(prs)` (1 diapositiva) o `agregar_todas(prs)` (varias), y sumarlo a la lista
BLOQUE_I/II/III más abajo (o crear un BLOQUE_IV cuando arranque).

SALIDA: P1_presentacion.pptx
Estructura (30 diapositivas):
  1     Portada
  2     Grilla de apertura — Bloque I + II
  3     Grilla de apertura — Bloque III + IV
  4     Bloque I — Universo/Índice/Hallazgos
  5-7   Bloque I (caracterización demográfica): edad_sexo, edad_jerarquia, grado_academico_sexo
  8     Bloque II — Universo/Índice/Hallazgos
  9-14  Bloque II (evaluación estudiantil): evaluacion_apr, evaluacion_met x2, evaluacion_afo x3
        — reclasificado 2026-08-03, antes vivía dentro de Bloque I (ver slides_estructura.py)
  15    Bloque III — Universo/Índice/Hallazgos
  16-23 Bloque III (aprobación/reprobación directa): aprobacion_reprobacion, +sexo (+prueba t),
        +jerarquia (+prueba t), +antiguedad_4tramos, +antiguedad_3tramos, evolucion_aprobacion_sexo
  24-30 Bloque III (grupos de dificultad, D27, agregado 2026-08-03): dificultad_composicion,
        +antiguedad_dificultad (+prueba t), +edad_dificultad (+prueba t), +sexo_dificultad (+prueba t)
        — jerarquia_dificultad NO se incluye: prueba t no significativa (p=0.0716), descartada
        del consolidado a pedido de la contraparte (queda documentada en D27 y como pptx suelto)
"""
import sys; sys.stdout.reconfigure(encoding="utf-8")
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "shared"))
from config import OUTPUTS
from pptx_helpers import UcenSlideKit

from pptx import Presentation
from pptx.util import Emu

import slides_estructura as estructura

CARAC = Path(__file__).parent / "caracterizacion"
OUT_PPTX = Path(OUTPUTS) / "pptx" / "P1_presentacion.pptx"
OUT_PPTX.parent.mkdir(parents=True, exist_ok=True)

# (carpeta, script, [funciones a llamar en orden]) — orden = orden final de las diapositivas
BLOQUE_I = [
    ("edad_sexo", "generar_edad_sexo.py", ["agregar"]),
    ("edad_jerarquia", "generar_edad_jerarquia.py", ["agregar"]),
    ("grado_academico_sexo", "generar_grado_academico_sexo.py", ["agregar"]),
]

BLOQUE_II = [
    ("evaluacion_apr", "generar_evaluacion_apr.py", ["agregar"]),
    ("evaluacion_met", "generar_evaluacion_met.py", ["agregar_todas"]),
    ("evaluacion_afo", "generar_evaluacion_afo.py", ["agregar_todas"]),
]

BLOQUE_III = [
    ("aprobacion_reprobacion", "generar_aprobacion_reprobacion.py", ["agregar"]),
    ("aprobacion_reprobacion_sexo", "generar_aprobacion_reprobacion_sexo.py",
     ["agregar", "agregar_ttest"]),
    ("aprobacion_reprobacion_jerarquia", "generar_aprobacion_reprobacion_jerarquia.py",
     ["agregar", "agregar_ttest"]),
    ("aprobacion_reprobacion_antiguedad_4tramos",
     "generar_aprobacion_reprobacion_antiguedad_4tramos.py", ["agregar"]),
    ("aprobacion_reprobacion_antiguedad_3tramos",
     "generar_aprobacion_reprobacion_antiguedad_3tramos.py", ["agregar"]),
    ("evolucion_aprobacion_sexo", "generar_evolucion_aprobacion_sexo.py", ["agregar"]),
    # Grupos de dificultad de asignaturas (D27, agregado 2026-08-03) — concatenados al
    # final del Bloque III, después de lo que ya había.
    ("dificultad_composicion", "generar_dificultad_composicion.py", ["agregar"]),
    ("antiguedad_dificultad", "generar_antiguedad_dificultad.py", ["agregar", "agregar_ttest"]),
    ("edad_dificultad", "generar_edad_dificultad.py", ["agregar", "agregar_ttest"]),
    ("sexo_dificultad", "generar_sexo_dificultad.py", ["agregar", "agregar_ttest"]),
    # jerarquia_dificultad NO se incluye: prueba t no significativa (p=0.0716) — descartada
    # del consolidado a pedido de la contraparte. El script y su pptx suelto siguen existiendo,
    # el hallazgo queda documentado en D27, solo se excluyó de este ensamblado.
]


def cargar_modulo(carpeta, script_name):
    path = CARAC / carpeta / script_name
    spec = importlib.util.spec_from_file_location(f"p1_{carpeta}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)   # ejecuta el script: carga sus propios datos
    return mod


def agregar_bloque(prs, bloque, etiqueta):
    for carpeta, script_name, funciones in bloque:
        print(f"\n── {etiqueta}: {carpeta} " + "─" * max(1, 50 - len(carpeta) - len(etiqueta)))
        mod = cargar_modulo(carpeta, script_name)
        for funcion in funciones:
            getattr(mod, funcion)(prs)


prs = Presentation()
prs.slide_width, prs.slide_height = Emu(UcenSlideKit.SW_EMU), Emu(UcenSlideKit.SH_EMU)

print("── Portada y estructura ──────────────────────────────────────")
estructura.portada(prs)
estructura.grid_b1_b2(prs)
estructura.grid_b3(prs)
estructura.uih_b1(prs)

agregar_bloque(prs, BLOQUE_I, "Bloque I")

estructura.uih_b2(prs)

agregar_bloque(prs, BLOQUE_II, "Bloque II")

estructura.uih_b3(prs)

agregar_bloque(prs, BLOQUE_III, "Bloque III")

prs.save(OUT_PPTX)
print(f"\n✓ Guardado: {OUT_PPTX}  ({len(prs.slides)} diapositivas)")
