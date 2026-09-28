"""
Rotación docente — Ensamblador (misma estructura que P1: un script por diapositiva en su carpeta,
cada uno expone `agregar(prs)` y, si prueba algo, `PRUEBAS`).

Pasada 1: carga los scripts, junta PRUEBAS y deja el p corregido por Holm en
pptx_helpers.P_AJUSTADO (regla D37; Holm por bloque = por anexo). Pasada 2: arma el deck.
Estructura (D39): UIH · Bloque 1 ¿Cómo cambia la planta? · Bloque 2 ¿Quiénes se van? · Anexos.

SALIDA: outputs/pptx/Rotacion_presentacion.pptx
"""
import sys; sys.stdout.reconfigure(encoding="utf-8")
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rotacion_comun as rc  # noqa: E402
import pptx_helpers  # noqa: E402
from pptx import Presentation  # noqa: E402
from pptx.util import Emu  # noqa: E402
from config import OUTPUTS  # noqa: E402

OUT_PPTX = Path(OUTPUTS) / "pptx" / "Rotacion_presentacion.pptx"
OUT_PPTX.parent.mkdir(parents=True, exist_ok=True)

# Orden (usuario 2026-09-27): primero el cambio de la planta (el balance es de las conclusiones más fuertes),
# después quiénes se van. formacion_jornada no va como diapositiva (no significativa entre quienes dictan
# clases); se carga igual para que sus pruebas queden en el anexo 2.
BLOQUE_1 = ["metodologia", "estado_general", "balance", "transicion", "perfil_transicionados"]
BLOQUE_2 = ["contrato", "sin_diferencias", "carga_honorario"]
SOLO_PRUEBAS = ["formacion_jornada"]
MODULOS = {}


def cargar_todo():
    pruebas = []
    for carpeta in BLOQUE_1 + BLOQUE_2 + SOLO_PRUEBAS:
        spec = importlib.util.spec_from_file_location(f"rot_{carpeta}", HERE / carpeta / f"generar_{carpeta}.py")
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        MODULOS[carpeta] = mod
        pruebas.extend(getattr(mod, "PRUEBAS", []))
    holm = pptx_helpers.holm_por_bloque(pruebas)
    pptx_helpers.P_AJUSTADO.update({pr["comparacion"]: h for pr, h in zip(pruebas, holm)})
    return pruebas, holm


if __name__ == "__main__":
    # La entrega final no muestra el "p corregido" (pedido del usuario 2026-09-27); el veredicto sí lo usa.
    pptx_helpers.MOSTRAR_P_CORREGIDO = False
    PRUEBAS, HOLM = cargar_todo()
    for pr, h in zip(PRUEBAS, HOLM):
        print(f"  [{pr['bloque'][:22]:<22}] {pr['comparacion'][:58]:<58} p={pr['p']:.4f}  corr={h:.4f}  {'SIGNIF.' if h < 0.05 else ''}")

    import estructura  # noqa: E402
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(rc.UcenSlideKit.SW_EMU), Emu(rc.UcenSlideKit.SH_EMU)
    estructura.uih(prs, MODULOS)
    for carpeta in BLOQUE_1 + BLOQUE_2:
        MODULOS[carpeta].agregar(prs)
    estructura.anexo(prs, PRUEBAS, HOLM)
    estructura.calidad_datos(prs)
    prs.save(OUT_PPTX)
    print(f"\n✓ Guardado: {OUT_PPTX}  ({len(prs.slides)} diapositivas)")
