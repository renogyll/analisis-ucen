"""
P1 — Caracterización del Cuerpo Académico de Planta
Ensamblador: junta en un solo PPTX las diapositivas de caracterizacion/ ya aprobadas.

Cada sub-tema vive en su propia carpeta con su script generador standalone (sigue
funcionando igual que antes — produce su propio pptx individual). Este ensamblador
importa la función `agregar`/`agregar_todas` de cada uno y las llama en secuencia
sobre una sola Presentation, sin duplicar lógica ni copiar diapositivas a mano
(las copias de slide entre .pptx con python-pptx son frágiles con imágenes).

Para agregar un nuevo sub-tema al consolidado: asegurarse de que su script exponga
`agregar(prs)` (1 diapositiva) o `agregar_todas(prs)` (varias), y sumarlo a la lista
SUBTEMAS más abajo.

SALIDA: P1_presentacion.pptx (9 diapositivas: edad_sexo, edad_jerarquia,
        grado_academico_sexo, evaluacion_apr, evaluacion_met x2, evaluacion_afo x3)
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

CARAC = Path(__file__).parent / "caracterizacion"
OUT_PPTX = Path(OUTPUTS) / "pptx" / "P1_presentacion.pptx"
OUT_PPTX.parent.mkdir(parents=True, exist_ok=True)

# (carpeta, script, función a llamar) — orden = orden final de las diapositivas
SUBTEMAS = [
    ("edad_sexo", "generar_edad_sexo.py", "agregar"),
    ("edad_jerarquia", "generar_edad_jerarquia.py", "agregar"),
    ("grado_academico_sexo", "generar_grado_academico_sexo.py", "agregar"),
    ("evaluacion_apr", "generar_evaluacion_apr.py", "agregar"),
    ("evaluacion_met", "generar_evaluacion_met.py", "agregar_todas"),
    ("evaluacion_afo", "generar_evaluacion_afo.py", "agregar_todas"),
]


def cargar_modulo(carpeta, script_name):
    path = CARAC / carpeta / script_name
    spec = importlib.util.spec_from_file_location(f"p1_{carpeta}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)   # ejecuta el script: carga sus propios datos
    return mod


prs = Presentation()
prs.slide_width, prs.slide_height = Emu(UcenSlideKit.SW_EMU), Emu(UcenSlideKit.SH_EMU)

for carpeta, script_name, funcion in SUBTEMAS:
    print(f"\n── {carpeta} " + "─" * (60 - len(carpeta)))
    mod = cargar_modulo(carpeta, script_name)
    getattr(mod, funcion)(prs)

prs.save(OUT_PPTX)
print(f"\n✓ Guardado: {OUT_PPTX}  ({len(prs.slides)} diapositivas)")
