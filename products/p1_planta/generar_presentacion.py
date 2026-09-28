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
BLOQUE_I/II/III/IV más abajo.

SALIDA: P1_presentacion.pptx
Estructura (45 diapositivas) — reordenada 2026-09-26 para seguir los 4 bloques que anuncia
la grilla; cada bloque abre con su Universo/Índice/Hallazgos (formato franjas). Historial
de cambios de contenido en los comentarios de BLOQUE_I..IV y en comentarios_decisiones.py.
  1     Portada
  2     Grilla de apertura — 4 franjas, Bloques I a IV (grid_bloques)
  3     Bloque I — UIH
  4-11  Bloque I (caracterización): edad_sexo, edad_jerarquia, antiguedad_jerarquia, facultad,
        funcion_academica, grado_academico_sexo, distribucion_horas (dona + sexo)
  12    Bloque II — UIH
  13-23 Bloque II (participación en formación, D31): formacion_jornada (modalidades, Venn,
        intensidad), participacion_formacion_sexo (+t), _jerarquia (+t), participación por
        facultad, formacion_jornada (antigüedad), participacion_formacion_edad (sin t,
        p=0.0724), formacion_jornada (tipo × antigüedad/sexo/edad, mosaico)
  24    Bloque III — UIH
  25-30 Bloque III (EDD, D28/D29): edd_sexo (+t), edd_jerarquia (+t), edd_facultad (+6 t)
  31    Bloque IV — UIH
  32-45 Bloque IV (aprobación/reprobación): global, +sexo (+t), +jerarquia (+t), antigüedad
        4 tramos, evolución por sexo, grupos de dificultad D27 (composición + antigüedad/edad/
        sexo con su t). Fuera: jerarquia_dificultad (p=0.0716) y antigüedad 3 tramos (duplicada).
Comentarios de decisiones para la contraparte: comentarios_decisiones.py (se reaplican al final).
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
    # 4 diapositivas nuevas pedidas por la contraparte (2026-09-25), a continuación de
    # edad_jerarquia en este orden exacto.
    ("antiguedad_jerarquia", "generar_antiguedad_jerarquia.py", ["agregar"]),
    ("facultad", "generar_facultad.py", ["agregar"]),
    ("funcion_academica", "generar_funcion_academica.py", ["agregar"]),
    ("grado_academico_sexo", "generar_grado_academico_sexo.py", ["agregar"]),
    # Distribución de jornada (D30) — movida desde el final de Bloque II a continuación
    # de grado_academico_sexo (2026-09-25, anotaciones de la contraparte: "dejarla antes
    # de la 8"). agregar_intro() se sigue excluyendo (ver docstring del script).
    # agregar_sexo (1 panel) reemplaza a agregar_sexo_jerarquia desde 2026-09-25 — la
    # contraparte pidió quitar el panel de escalafón.
    ("distribucion_horas", "generar_distribucion_horas.py", ["agregar_donut", "agregar_sexo"]),
]

# ── REORDEN 2026-09-26 (acordado con el usuario) ─────────────────────────────────────
# El cuerpo del deck sigue ahora el orden que anuncia la grilla: I Caracterización,
# II Participación, III EDD, IV Aprobación. Toda la participación en formación (antes
# repartida entre Bloque I y el final del deck) queda junta en Bloque II: primero cuánto
# y cómo participan, después quién participa. Salen del consolidado (los scripts siguen):
# formacion_jornada.agregar_jerarquia (composición que repetía la tasa por jerarquía), el
# panel de jerarquía de participacion_facultad_jerarquia (ídem) y
# aprobacion_reprobacion_antiguedad_3tramos (variante duplicada de 4 tramos).
# Evaluación estudiantil APR/MET/AFO sigue fuera (2026-09-25, "borrar" diapos 9-14).
BLOQUE_II = [
    ("formacion_jornada", "generar_formacion_jornada.py",
     ["agregar_modalidades", "agregar_venn", "agregar_intensidad"]),
    # ── REVISIÓN DE COHERENCIA 2026-09-26 (obs. 21): cada par descriptivo + prueba t quedó
    # en una sola diapositiva (el script expone una sola función para el consolidado).
    ("participacion_formacion_sexo", "generar_participacion_formacion_sexo.py", ["agregar_ttest"]),
    ("participacion_formacion_jerarquia", "generar_participacion_formacion_jerarquia.py", ["agregar"]),
    ("participacion_facultad_jerarquia", "generar_participacion_facultad_jerarquia.py",
     ["agregar_facultad"]),
    ("formacion_jornada", "generar_formacion_jornada.py", ["agregar_antiguedad"]),
    # participacion_formacion_edad: prueba no significativa (p=0.0724), ahora dicha en el punteo
    ("participacion_formacion_edad", "generar_participacion_formacion_edad.py", ["agregar"]),
    ("formacion_jornada", "generar_formacion_jornada.py", ["agregar_tipo_por_grupo"]),
]

# EDD limpia (D37, reemplaza el ajuste por año de D36): primero la diapositiva de calidad de
# datos por año (notas dañadas 2024-2025), después las comparaciones con la nota limpia.
BLOQUE_III = [
    ("edd_sexo", "generar_edd_sexo.py", ["agregar_por_anio", "agregar"]),
    ("edd_jerarquia", "generar_edd_jerarquia.py", ["agregar"]),
    ("edd_facultad", "generar_edd_facultad.py", ["agregar"]),
]

# Aprobación: una sola medida por comparación (promedio por docente, obs. 2); sexo seguido
# del control por grupo de dificultad (obs. 4); dificultad con grupo predominante (obs. 3).
BLOQUE_IV = [
    ("aprobacion_reprobacion", "generar_aprobacion_reprobacion.py", ["agregar"]),
    ("aprobacion_reprobacion_sexo", "generar_aprobacion_reprobacion_sexo.py",
     ["agregar", "agregar_por_dificultad"]),
    ("aprobacion_reprobacion_jerarquia", "generar_aprobacion_reprobacion_jerarquia.py", ["agregar"]),
    ("aprobacion_reprobacion_antiguedad_4tramos",
     "generar_aprobacion_reprobacion_antiguedad_4tramos.py", ["agregar"]),
    ("evolucion_aprobacion_sexo", "generar_evolucion_aprobacion_sexo.py", ["agregar"]),
    # Grupos de dificultad de asignaturas (D27).
    ("dificultad_composicion", "generar_dificultad_composicion.py", ["agregar"]),
    ("antiguedad_dificultad", "generar_antiguedad_dificultad.py", ["agregar"]),
    ("edad_dificultad", "generar_edad_dificultad.py", ["agregar"]),
    ("sexo_dificultad", "generar_sexo_dificultad.py", ["agregar"]),
    # jerarquia_dificultad: sin diapositiva (p=0.0716), pero su prueba va al anexo.
    ("jerarquia_dificultad", "generar_jerarquia_dificultad.py", []),
]


MODULOS = {}   # carpeta -> módulo ya cargado (cada script se ejecuta una sola vez)


def cargar_modulo(carpeta, script_name):
    if carpeta not in MODULOS:
        path = CARAC / carpeta / script_name
        spec = importlib.util.spec_from_file_location(f"p1_{carpeta}", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)   # ejecuta el script: carga sus datos y calcula sus pruebas
        MODULOS[carpeta] = mod
    return MODULOS[carpeta]


def agregar_bloque(prs, bloque, etiqueta):
    for carpeta, script_name, funciones in bloque:
        print(f"\n── {etiqueta}: {carpeta} " + "─" * max(1, 50 - len(carpeta) - len(etiqueta)))
        mod = cargar_modulo(carpeta, script_name)
        for funcion in funciones:
            getattr(mod, funcion)(prs)


# ── Pasada 1: cargar todos los scripts y corregir sus pruebas ANTES de crear diapositivas ──
# (decisión del usuario 2026-09-27: regla binaria — significativa solo si el p corregido por
# Holm dentro del bloque es < 0.05). El p corregido se deja en pptx_helpers.P_AJUSTADO y cada
# script lo usa para el recuadro del gráfico y el punteo (encabezado_prueba / lectura_p).
import pptx_helpers


def cargar_todo():
    """Pasada 1: carga todos los scripts, junta sus PRUEBAS y deja el p corregido por Holm en
    pptx_helpers.P_AJUSTADO. La usan este ensamblador y el resumen (resumen/generar_resumen.py)."""
    print("── Pasada 1: cargando scripts y pruebas ──────────────────────")
    pruebas = []
    for bloque in (BLOQUE_I, BLOQUE_II, BLOQUE_III, BLOQUE_IV):
        for carpeta, script_name, _ in bloque:
            if carpeta not in MODULOS:
                mod = cargar_modulo(carpeta, script_name)
                pruebas.extend(getattr(mod, "PRUEBAS", []))
    holm = estructura.holm_por_bloque(pruebas)
    pptx_helpers.P_AJUSTADO.update({pr["comparacion"]: h for pr, h in zip(pruebas, holm)})
    for pr, h in zip(pruebas, holm):
        if (pr["p"] < 0.05) != (h < 0.05):
            print(f"  Sin ajuste significativa, con Holm por bloque no: {pr['comparacion']} "
                  f"(p={pr['p']:.4f} → {h:.4f})")
    return pruebas, holm


if __name__ == "__main__":
    PRUEBAS, HOLM = cargar_todo()

    # ── Pasada 2: diapositivas ──────────────────────────────────────────────────────────────
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(UcenSlideKit.SW_EMU), Emu(UcenSlideKit.SH_EMU)

    print("── Portada y estructura ──────────────────────────────────────")
    estructura.portada(prs)
    # Grilla de apertura en 4 franjas (2026-09-25) + cada bloque abre con su
    # Universo/Índice/Hallazgos en formato franjas (2026-09-26, los 4 bloques por igual).
    estructura.grid_bloques(prs)

    estructura.uih_b1(prs)
    agregar_bloque(prs, BLOQUE_I, "Bloque I — Caracterización")

    estructura.uih_b2(prs)
    agregar_bloque(prs, BLOQUE_II, "Bloque II — Participación")

    estructura.uih_b3(prs)
    agregar_bloque(prs, BLOQUE_III, "Bloque III — EDD")

    estructura.uih_b4(prs)
    agregar_bloque(prs, BLOQUE_IV, "Bloque IV — Aprobación")

    print(f"\n── Anexo: {len(PRUEBAS)} pruebas estadísticas ───────────────────────────")
    # Holm por bloque (decisión del usuario 2026-09-26); el veredicto ya va en cada diapositiva.
    estructura.anexo_pruebas(prs, PRUEBAS, HOLM)

    prs.save(OUT_PPTX)
    print(f"\n✓ Guardado: {OUT_PPTX}  ({len(prs.slides)} diapositivas)")

    # Comentarios de decisiones para la contraparte (2026-09-26) — se reaplican en cada corrida
    # porque el pptx se crea desde cero. Requiere PowerPoint (COM); si no está, el deck igual queda.
    print("\n── Comentarios de decisiones ─────────────────────────────────")
    try:
        import comentarios_decisiones
        comentarios_decisiones.aplicar(OUT_PPTX)
    except Exception as e:
        print(f"  ⚠ No se agregaron comentarios ({type(e).__name__}: {e}) — el deck quedó sin ellos.")
