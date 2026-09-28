"""Rotación — Diapositivas estructurales (formato P1): Universo/Índice/Hallazgos con los dos bloques,
anexo de pruebas (una tabla por bloque) y anexo de calidad de datos.

Estructura (D39, 2026-09-27):
  Bloque 1 — ¿Quiénes se van?  metodología, activos/bajas, contrato, perfil y desempeño, carga, formación
  Bloque 2 — ¿Cómo cambia la planta?  transición de contrato, quiénes cambian, balance de entradas y salidas
  Anexos — pruebas estadísticas (por bloque) y calidad de los datos
"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rotacion_comun as rc  # noqa: E402

kit = rc.kit_para(HERE)


def _fmt_p(p):
    return "<0.0001" if p < 0.0001 else f"{p:.4f}"


def uih(prs, M):
    """M = módulos cargados por el ensamblador (se leen sus cifras, no se recalculan)."""
    df = rc.cargar_datos()
    n, n_baja = len(df), int(df["baja"].sum())
    tj = 100 * df.loc[df["contrato"] == "JORNADA", "baja"].mean()
    th = 100 * df.loc[df["contrato"] == "HONORARIO", "baja"].mean()
    b, c, s = M["balance"], M["carga_honorario"], M["sin_diferencias"]
    J, H = b.F["JORNADA"], b.F["HONORARIO"]
    edd_b, edd_s = s.DESEMP[("EDD", "JORNADA")]
    sl = rc.lamina_base(kit, prs, f"Rotación docente — registro histórico vs planeación 2026 (N°{n:,})", "")
    kit.franjas(sl, [
        ("Universo", [f"{n:,} docentes del registro histórico (Jornada y Honorario), cruzados con la planeación docente "
                      f"2026: {n - n_baja} siguen y {n_baja} no aparecen (bajas). Cada docente se compara según su "
                      "contrato de entrada."]),
        ("Índice", ["**Bloque 1 — ¿Cómo cambia la planta?**\n\n1. Cómo se mide\n2. Activos y bajas\n"
                    "3. Balance de entradas y salidas\n4. Cambio de contrato\n5. Quiénes cambian\n",  # igual alto que col. 2
                    "**Bloque 2 — ¿Quiénes se van?**\n\n6. Según contrato\n7. Según perfil del docente\n"
                    "8. Carga docente (Honorario)\n\n**Anexos**\nPruebas estadísticas y calidad de datos"]),
        ("Hallazgos", ["\n".join([
            f"1. La planta Jornada se achica ({J['ini']} → {J['fin']}) y la de Honorario crece ({H['ini']} → {H['fin']}).",
            f"2. 1 de cada 4 docentes ({100 * n_baja / n:.0f}%) no sigue en 2026; la baja se concentra en Honorario "
            f"({th:.0f}% vs {tj:.0f}% en Jornada).",
            f"3. Los Honorarios que se van dictaban menos cursos ({c.BAJA.mean():.1f} vs {c.SIGUE.mean():.1f} secciones "
            "por semestre).",
            "4. Ni el perfil (escalafón, jerarquía, facultad, sexo) ni el desempeño (EDD, aprobación de sus alumnos) "
            "se asocian a quién se va.",
        ])]),
    ], fs=12, col_split=0.39, fs_hdr=16, top=kit.POP_T + kit.POP_H + int(0.30 * kit._IN), centrar_v=True)
    kit.notas(sl, "D35 (construcción del universo) y D39 (contrato de entrada, sin antigüedad, 5 facultades, "
                  f"pruebas chi-cuadrado, extensiones). Desempeño: EDD de quienes se van {edd_b:.3f} vs {edd_s:.3f}; "
                  "aprobación sin diferencia en ambos contratos (anexo 2). Los docentes nuevos de 2026 solo se usan "
                  "en el balance.")
    return sl


def anexo(prs, pruebas, holm):
    for bloque, titulo in [(rc.BLOQUE, "Anexo 1 — Pruebas: ¿quiénes se van? (contrato y perfil)"),
                           (rc.BLOQUE_EXT, "Anexo 2 — Pruebas: balance, carga, formación y desempeño")]:
        filas = [[pr["comparacion"], pr["resultado"], pr["n"], pr["prueba"], _fmt_p(pr["p"]),
                  "Sí" if h < 0.05 else "No"] for pr, h in zip(pruebas, holm) if pr["bloque"] == bloque]
        sl = rc.lamina_base(kit, prs, titulo,
            f"{len(filas)} pruebas · {sum(f[-1] == 'Sí' for f in filas)} con diferencia significativa (en dorado)")
        kit.tabla(sl, ["Comparación", "Resultado", "N°", "Prueba", "p", "¿Diferencia significativa?"], filas,
                  anchos=[0.29, 0.36, 0.05, 0.10, 0.07, 0.13], fs=8,
                  resaltar=lambda i, filas=filas: filas[i][-1] == "Sí")
        kit.notas(sl, f"Como son {len(filas)} comparaciones a la vez, el umbral de significancia se ajusta para no "
                      "declarar diferencias por azar (método de Holm, dentro de este anexo). Por eso una prueba con p "
                      "cercano a 0.05 puede quedar como no significativa.")


def calidad_datos(prs):
    df = rc.cargar_datos()
    n_sin_fac = int(df["fac"].isna().sum())
    n_sin_fac_h = int((df["fac"].isna() & (df["contrato"] == "HONORARIO")).sum())
    sin_clases = df[~df["rut_key"].isin(rc.carga_docente()["rut_key"])]
    sl = rc.lamina_base(kit, prs, "Anexo 3 — Calidad de los datos",
                        "Problemas encontrados al cruzar las fuentes y cómo se trataron")
    kit.franjas(sl, [
        ("RUT", ["3 RUT con problemas al cruzar fuentes: uno con dígitos traspuestos en la planeación 2026 (corregido: "
                 "era una baja falsa), uno asignado a otra persona en la nómina (corregido: era un cambio de contrato "
                 "falso) y uno que aparece con dos nombres distintos según la fuente (sin corregir; se informa a UCEN)."]),
        ("Nombres", ["La planeación 2026 trae los acentos dañados, lo que impide cruzar por nombre; el cruce se hizo "
                     "solo por RUT."]),
        ("Facultad", [f"{n_sin_fac} docentes sin facultad registrada ({n_sin_fac_h} de ellos Honorario): no se "
                      "comparan por facultad."]),
        ("Sin clases", [f"{len(sin_clases)} docentes del registro no aparecen en las calificaciones de alumnos "
                        f"2023-2025 ({100 * sin_clases['baja'].mean():.0f}% de baja): son parte de la universidad "
                        "(investigación, gestión, formación) pero con un vínculo docente distinto."]),
        ("Bajas", ["Baja = no aparece en la planeación 2026; no hay fecha de salida, por lo que no se puede medir "
                   "la antigüedad de quienes se fueron."]),
    ], fs=10.5, fs_hdr=13)
    kit.notas(sl, "Detalle de los casos de RUT (con identificación) en docs/DECISIONES_METODOLOGICAS.md, D39.")
    return sl
