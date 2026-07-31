"""
ETL tabla_catalogo_calificacion
Catalogo de codigos de calificacion usados en calificacion_alumno.
Fuente: DOCUMENTO EXPLICATIVO DE CATEGORIA VARIAS 9-05-2026.docx + inspeccion datos
"""

import pandas as pd, os

OUT = r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO\Downloads\Analisis_UCEN_v2\PROCESADO"

# Descripciones oficiales segun DOCUMENTO EXPLICATIVO DE CATEGORIA VARIAS 9-05-2026.docx
# aprueba: True=aprueba, False=reprueba, None=indeterminado/administrativo
catalogos = [
    # (codigo, descripcion,   descripcion_oficial,                                                   aprueba, tiene_nota)
    ("SO", "Sobresaliente",
     "Calificacion maxima. Aportes excepcionales: publicaciones, innovaciones pedagogicas premiadas o gestion de alto impacto.",
     True,  True),
    ("MB", "Muy Bueno",
     "Supera las expectativas iniciales. Compromiso mayor con resultados positivos destacados en sus areas de desempeno.",
     True,  True),
    ("B",  "Bueno",
     "Estandar esperado. Cumple de manera responsable y eficiente con todas sus funciones programadas.",
     True,  True),
    ("SU", "Suficiente",
     "Cumple con lo justo y necesario. Desempeno aceptable pero sin valor agregado mas alla de lo basico.",
     True,  True),
    ("M",  "Malo",
     "Desempeno insuficiente. Presenta brechas criticas en sus compromisos.",
     False, True),
    ("MM", "Muy Malo",
     "No cumple con los estandares minimos. Requiere intervencion o planes de mejora inmediata.",
     False, True),
    ("I",  "Insuficiente",
     "Calificacion numerica insuficiente (sin descripcion oficial en el documento).",
     False, True),
    ("A",  "Aprobado",
     "Aprobado sin nota numerica.",
     True,  False),
    ("R",  "Reprobado",
     "Reprobado sin nota numerica.",
     False, False),
    ("NP", "No se Presento",
     "El estudiante no se presento a evaluacion.",
     False, False),
    ("P",  "Postergado",
     "Evaluacion postergada, estado administrativo pendiente.",
     None,  False),
    ("SC", "Sin Calificacion",
     "Sin calificacion registrada.",
     None,  False),
    ("SD", "Sin Datos",
     "Sin datos disponibles.",
     None,  False),
]

df = pd.DataFrame(catalogos, columns=["codigo","descripcion","descripcion_oficial","aprueba","tiene_nota"])
df.to_csv(os.path.join(OUT, "catalogo_calificacion.csv"), index=False, encoding="utf-8-sig")

print("catalogo_calificacion.csv generada")
print(df.to_string(index=False))
