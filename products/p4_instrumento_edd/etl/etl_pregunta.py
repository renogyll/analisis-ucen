"""
ETL Tabla pregunta
Catalogo canonico de preguntas del instrumento de evaluacion estudiantil.
IDs semanticos: APR_01-03, MET_01-05, AFO_01-09, SAT_BIN, SAT_NOTA
"""

import pandas as pd, os

OUT = r"c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO\Downloads\Analisis_UCEN_v2\PROCESADO"

# texto_principal = version vigente (2023-02 en adelante)
# texto_alternativo = version usada solo en 2023-01 (MET_04)
preguntas = [
    ("APR_01","Aprendizajes",             1,"LIKERT",
     "El profesor(a) vincula lo que enseña con el ejercicio futuro de la profesión",
     None, None, "4509"),
    ("APR_02","Aprendizajes",             2,"LIKERT",
     "El profesor(a) promueve la aplicación de los aprendizajes en la resolución de algún problema o situación",
     None, None, "4510"),
    ("APR_03","Aprendizajes",             3,"LIKERT",
     "El profesor(a) promueve que los/las estudiantes relacionen conocimientos anteriores o de otras asignaturas con los temas tratados",
     None, None, "4511"),
    ("MET_01","Metodologías y Evaluación",4,"LIKERT",
     "La metodología de clases del profesor(a) y sus formas de evaluación respetan la diversidad de los distintos/as estudiantes, incluyendo la mirada de género",
     None, None, "4512"),
    ("MET_02","Metodologías y Evaluación",5,"LIKERT",
     "Las formas de evaluación utilizadas por el profesor(a) me permitieron mostrar que aprendí lo que se esperaba",
     None, None, "4513"),
    ("MET_03","Metodologías y Evaluación",6,"LIKERT",
     "La metodología de clases del profesor(a) me ayudó a lograr los aprendizajes esperados para la asignatura",
     None, None, "4514"),
    ("MET_04","Metodologías y Evaluación",7,"LIKERT",
     "El profesor(a) frente a las dudas o consultas de los estudiantes, orienta y clarifica los resultados de aprendizaje",
     "Cuando una explicación no satisface de manera efectiva a los/las estudiantes, el profesor(a) rápidamente ajusta su discurso y utiliza un método alternativo para explicar la materia",
     "2023-01", "4515"),
    ("MET_05","Metodologías y Evaluación",8,"LIKERT",
     "El profesor(a) comunica con antelación los criterios de evaluación a los/las estudiantes",
     None, None, "4516"),
    ("AFO_01","Aspectos Formales",        9,"LIKERT",
     "El profesor(a) utiliza un lenguaje inclusivo que dé cuenta del respeto a las personas",
     None, None, "4517"),
    ("AFO_02","Aspectos Formales",       10,"LIKERT",
     "El comportamiento del profesor(a) es acorde a su rol y respeta los límites en la relación con sus estudiantes",
     None, None, "4518"),
    ("AFO_03","Aspectos Formales",       11,"LIKERT",
     "El profesor(a) revisa con los (las) estudiantes el syllabus de la asignatura especificando su relación con las competencias del perfil de egreso de la carrera",
     None, None, "4519"),
    ("AFO_04","Aspectos Formales",       12,"LIKERT",
     "El profesor(a) desarrolla todos los temas estipulados en el syllabus",
     None, None, "4520"),
    ("AFO_05","Aspectos Formales",       13,"LIKERT",
     "El profesor(a) asiste regularmente a clases",
     None, None, "4521"),
    ("AFO_06","Aspectos Formales",       14,"LIKERT",
     "El profesor(a) respeta el horario de clases",
     None, None, "4522"),
    ("AFO_07","Aspectos Formales",       15,"LIKERT",
     "El profesor(a) entrega los resultados de las evaluaciones de acuerdo a los tiempos establecidos",
     None, None, "4523"),
    ("AFO_08","Aspectos Formales",       16,"LIKERT",
     "El profesor(a) demuestra interés por enseñar esta asignatura",
     None, None, "4524"),
    ("AFO_09","Aspectos Formales",       17,"LIKERT",
     "El profesor(a) demuestra pleno conocimiento de las materias que enseña en esta asignatura",
     None, None, "4525"),
    ("SAT_BIN","Satisfacción",           18,"BINARIO",
     "¿Recomendaría a este profesor(a) a otro/a estudiante que quiera lograr un real aprendizaje en esta asignatura?",
     None, None, "4526"),
    ("SAT_NOTA","Satisfacción",          19,"NOTA",
     "¿Con qué nota (escala 1-7) calificaría el desempeño general del profesor(a) en esta asignatura?",
     None, None, "4527"),
]

cols = ["pregunta_id","dimension","orden","tipo_respuesta",
        "texto_principal","texto_alternativo","periodos_texto_alt","id_original"]
df = pd.DataFrame(preguntas, columns=cols)

df.to_csv(os.path.join(OUT,"tabla_pregunta.csv"), index=False, encoding="utf-8-sig")
df[["id_original","pregunta_id"]].to_csv(os.path.join(OUT,"mapeo_id_pregunta.csv"), index=False, encoding="utf-8-sig")

print("tabla_pregunta.csv generada")
print(f"  LIKERT: {(df.tipo_respuesta=='LIKERT').sum()} | BINARIO: {(df.tipo_respuesta=='BINARIO').sum()} | NOTA: {(df.tipo_respuesta=='NOTA').sum()}")
print(f"  Con texto alternativo (MET_04): {df.texto_alternativo.notna().sum()}")
print()
print(df[["pregunta_id","dimension","orden","tipo_respuesta"]].to_string(index=False))
print("\nmapeo_id_pregunta.csv generado")
