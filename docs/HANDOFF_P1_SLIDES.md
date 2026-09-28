# Traspaso de sesión — P1 Caracterización Cuerpo Académico (Jornada)

> ⚠️ **HISTÓRICO (2026-09-27).** Este traspaso describe el estado del 2026-08-04 y ya no está
> vigente: el deck se reestructuró en 4 bloques (Caracterización, Participación, EDD,
> Aprobación), la EDD usa la nota limpia (D37) y la significancia se decide con el p corregido
> por Holm dentro de cada bloque. Las rutas `c:\Users\r.gonzalez_fluxsolar…` son del PC anterior;
> el repo está hoy en `C:\Users\renat\Downloads\RESCATE_TODO_UCEN\analisis-ucen`.
> **Fuente vigente:** `docs/DECISIONES_METODOLOGICAS.md` (D36, D37 y el "Catálogo de
> visualizaciones P1 confirmadas", que lista las 39 diapositivas actuales).

**Para:** la próxima conversación que continúe este trabajo (mismo Claude Code, chat nuevo).
**Escrito por:** Claude, al cierre de la sesión del 2026-08-04.
**Repo:** `c:\Users\r.gonzalez_fluxsolar.LAPTOP-FLUX-ECO\Downloads\analisis-ucen` (git, branch `main`).

Si estás retomando esto: leé este archivo primero, después `docs/DECISIONES_METODOLOGICAS.md`
completo (es la fuente de verdad de toda decisión metodológica — universos, filtros, criterios
de pruebas t, todo). No hace falta releer el historial de conversación anterior.

---

## Qué es esto

Consultoría para Universidad Central (UCEN). El proyecto completo tiene 4 "Productos" (P1-P4,
ver TdR). **Esta sesión trabajó exclusivamente en P1: Caracterización del Cuerpo Académico de
Jornada** — el resto de los productos (P2/P3/P4) están en otras carpetas de `products/` con
distinto grado de avance, no los toqué en esta sesión salvo para leer código de referencia (P3
tenía el patrón visual que reutilicé).

**Universo de P1:** 624 docentes con contrato de Jornada (planta), sub-universo de
`analisis.universo_base` (1.144 docentes totales, Postgres local `ucen` — ver credenciales en
cualquier script, `postgresql://ucen_user:ucen2026@localhost:5432/ucen`).

## Estado actual (2026-08-04, después de compilar participación formativa en Bloque IV)

`products/p1_planta/generar_presentacion.py` genera el consolidado `P1_presentacion.pptx`
(en `outputs/pptx/`, carpeta gitignoreada — hay que correr el script para regenerarlo, no está
versionado). **44 diapositivas**, estructura:

- **1-4**: Portada + 2 grillas de apertura (resumen Bloque I+II, resumen Bloque III+IV) + Bloque I Universo/Índice/Hallazgos
- **5-7 (Bloque I — caracterización demográfica)**: sexo/edad, edad por jerarquía, grado académico por sexo
- **8-14 (Bloque II — evaluación estudiantil)**: dimensiones APR/MET/AFO del instrumento de evaluación estudiantil
- **15-16 (Bloque II, cont. — distribución de jornada, D30)**: dona de composición (Completa/Parcial/Sin dato) + comparación por sexo/escalafón. No es evaluación estudiantil en sentido estricto — se integró acá a pedido explícito de la contraparte, a continuación de lo anterior. La intro de `distribucion_horas/` se excluyó del ensamblado (queda redundante con el título de cada diapositiva; el script standalone la sigue teniendo definida, sin usar).
- **17-25 (Bloque III, parte 1 — aprobación/reprobación directa)**: global, por sexo (+prueba t), por escalafón (+prueba t), por antigüedad (2 variantes), evolución por sexo
- **26-32 (Bloque III, parte 2 — grupos de dificultad de asignaturas, D27)**: composición, antigüedad/edad/sexo según grupo de dificultad (cada uno con su prueba t)
- **33 (Bloque IV — Universo/Índice/Hallazgos)**: EDD + participación formativa
- **34-39 (Bloque IV, parte 1 — Evaluación de Desempeño Docente, D28/D29)**: EDD según sexo (+prueba t), jerarquía/escalafón (+prueba t), facultad (+6 pruebas t, cada facultad vs. el resto)
- **40-44 (Bloque IV, parte 2 — participación en instancias formativas, D31)**: según sexo (+prueba t), jerarquía/escalafón (+prueba t), tramo de edad (sin prueba t — no significativa, p=0.0724, mismo criterio que aprobacion_reprobacion_antiguedad). No es EDD en sentido estricto, se integró acá a pedido explícito de la contraparte, a continuación de lo anterior.

Bloque IV ya no es placeholder — tiene contenido real (EDD + participación formativa). Si se
agregan más cortes de cualquiera de los dos temas, van a continuación de lo último en
`BLOQUE_IV` de `generar_presentacion.py`.

Todo el trabajo hasta acá está **commiteado** (confirmar con `git status`/`git log --oneline -3`
antes de asumir el estado real si esto se retoma más adelante).

## Patrón para agregar un gráfico nuevo (seguir esto, no inventar otro)

1. Carpeta nueva en `products/p1_planta/caracterizacion/<subtema>/`, un script
   `generar_<subtema>.py` adentro.
2. El script usa `shared/pptx_helpers.py` → clase `UcenSlideKit` (fondo UCEN, título, bajada,
   punteo numerado, notas del orador, layouts de portada/grillas/universo-índice-hallazgos).
   **Leer ese archivo primero** — tiene todo documentado en el docstring de cabecera y en cada
   método.
3. El script expone una función `agregar(prs)` que agrega su(s) diapositiva(s) a un `Presentation`
   recibido como parámetro, y devuelve el `slide`. Si necesita más de una diapositiva o una
   variante con prueba t, se agrega `agregar_ttest(prs)` como función separada (mismo patrón en
   los 5 scripts de `*_dificultad/`).
4. Al final del script, bloque `if __name__ == "__main__":` que arma su propio `Presentation()`
   y llama a `agregar()`/`agregar_ttest()`, para que el script siga funcionando standalone
   (genera su propio pptx individual en `outputs/pptx/P1_<subtema>.pptx`).
5. Para sumarlo al consolidado: agregarlo a `BLOQUE_I`/`BLOQUE_II`/`BLOQUE_III` en
   `products/p1_planta/generar_presentacion.py` (tupla `(carpeta, script, [funciones])`).
6. Correr el script suelto primero, revisar los números impresos en consola, y **verificar
   visualmente el PNG del gráfico** (no el pptx — no hay renderer de pptx disponible en este
   entorno). Truco para ver el PNG con fondo real en vez de transparente:
   ```python
   from PIL import Image
   fg = Image.open('ruta/al/chart.png').convert('RGBA')
   bg = Image.new('RGBA', fg.size, (16,24,32,255))
   bg.alpha_composite(fg)
   bg.convert('RGB').save('ruta/temporal/preview.png')
   ```
   y después `Read` esa imagen. **Las diapositivas estructurales (portada, grillas,
   universo/índice/hallazgos) no se pueden pre-visualizar así** porque no generan PNG — son
   shapes de pptx directo. Avisar siempre al usuario que esas quedan sin verificación visual.

## Convenciones que hay que respetar (están en `shared/pptx_helpers.py` también)

- Cualquier N se escribe **"N°="**, nunca "n=".
- La bajada (`kit.subtitulo()`) nunca menciona el archivo/CSV fuente. El detalle secundario
  (por qué falta un dato, la fuente, etc.) va en `kit.notas(sl, texto)` — notas del orador, no
  se ve en pantalla.
- Pruebas t: siempre Welch (`equal_var=False`). Unidad de análisis = 1 valor por docente (nunca
  por calificación individual, para evitar pseudo-repetición). Si la variable es fija por
  docente (edad, sexo, antigüedad, jerarquía — no varía por instancia), y el docente puede caer
  en más de un grupo, se usa el **"grupo predominante"** (el grupo donde tiene más instancias)
  para que cada docente aporte un solo valor a una sola muestra — ver D27 en
  `docs/DECISIONES_METODOLOGICAS.md` para el detalle completo con ejemplos de código.
- **Pruebas t no significativas (p≥0.05) se descartan del consolidado** a pedido de la
  contraparte, pero el script/pptx suelto y el hallazgo documentado en el `.md` quedan —
  no se borran del repo, solo se excluyen de `generar_presentacion.py`. Ejemplo real:
  `jerarquia_dificultad/` (p=0.0716).
- Colores establecidos (reusar, no inventar nuevos sin necesidad): Hombre `#5C9BD6` / Mujer
  `#FFB74D`; Aprobación `#3E9E68` / Reprobación `#E4572E`; Docente `#5C9BD6` / Regular `#FFB74D`;
  rampa secuencial de jerarquía (junior→senior, claro→oscuro) `#AFCBE8, #7FADD9, #4E8FC9, #1F5C99`.
- Para binarios (sexo, escalafón) donde se quiere ver la composición completa: barra 100%
  apilada (ver `sexo_dificultad/` y `jerarquia_dificultad/` como ejemplo), no barra de un solo lado.
- Todo cambio metodológico nuevo (filtro, criterio, umbral) se documenta en
  `docs/DECISIONES_METODOLOGICAS.md` como decisión numerada nueva (D28 sería la próxima), y cada
  visualización confirmada se agrega a la tabla "Catálogo de visualizaciones P1 confirmadas" al
  final del mismo archivo — no es opcional, es la práctica establecida.
- **No commitear sin que el usuario lo pida explícitamente.** El usuario a veces commitea él
  mismo desde VS Code — revisar `git status`/`git log` antes de asumir que algo quedó sin
  guardar.
- Cuidado con `PermissionError` al guardar el .pptx — casi siempre es porque el archivo está
  abierto en PowerPoint. Pedirle al usuario que lo cierre, no intentar workarounds.

## Tabla principal de datos

`intel.rendimiento_academico_alumnos` (Postgres) es la tabla que alimenta casi todo el trabajo
de aprobación/reprobación. Nace de `consolidados.calificacion_alumno` y se enriquece vía
`products/p3_perfeccionamiento/etl/complementarios/etl_intel_rendimiento_academico_alumnos.py`
con: `tipo_contrato_tag`, `sexo`, `tramo_edad`/`edad_anios`, `jerarquia`,
`tramo_antiguedad`/`antiguedad_anios`, `aprueba` (booleano, vía `catalogo_calificacion`), y
`grupo_dificultad`/`pct_aprob_asignatura` (terciles D27). Si se necesita otra columna del
docente que no esté ahí, probablemente se pueda agregar con un LEFT JOIN más contra
`analisis.universo_base` en ese mismo script — seguir el mismo patrón, no crear una tabla nueva.

Para gráficos de P1 que no dependen de calificaciones (edad, sexo, grado académico del cuerpo
completo), la fuente es `data/cascade/01_jornada/docentes_jornada.csv` — no consultar la DB en
vivo para eso, ya está materializado ahí.

**`intel.evaluacion_jefes`** (agregada 2026-08-04, D28) — evaluación de desempeño docente (EDD)
hecha por la jefatura/director, NO es la evaluación estudiantil (esa es
`intel.rendimiento_academico_alumnos`, no confundirlas). Nace de
`consolidados.evaluacion_jefes` (1.646 filas, 604 docentes, 1 fila por docente × año 2022-2025)
vía `shared/etl/complementarios/etl_intel_evaluacion_jefes.py`, enriquecida igual que la otra
tabla: `tipo_contrato_tag`/`sexo`/`jerarquia` por LEFT JOIN contra `universo_base`. Ojo:
`facultad_jefe` **ya venía en la fuente** con 100% de cobertura (códigos FAMEDSA/FINARQ/FED/
FEGOC/FACDEH/VRIIP) — no la agregues de nuevo, y en general antes de unir un campo desde
`universo_base` revisar primero si la tabla fuente ya lo trae (pasó 2 veces con
`rendimiento_academico_alumnos` también: `rut_docente` y `facultad` ya estaban).
Columnas de interés ya numéricas (`errors="coerce"` aplicado en el ETL): `edd_total`,
`edd_director`, `edd_docente`, `cumplimiento_cd`, `porcentaje_concepto`.

## Qué falta / posibles próximos pasos

**EDD (`intel.evaluacion_jefes`) — 3 visualizaciones construidas y verificadas (2026-08-04),
ver D29.** `edd_sexo/`, `edd_jerarquia/`, `edd_facultad/` (cada una con descriptivo + prueba t,
mismo patrón `agregar`/`agregar_ttest` que el resto de P1). Resultados: sexo significativo
(p=0.0183, Hombres 0.72 vs Mujeres 0.66 — ojo, dirección OPUESTA a la evaluación estudiantil),
escalafón significativo (p=0.0011, Docente 0.71 vs Regular 0.59), facultad con 4/6 significativas
vs. el resto (FACDEH/FINARQ más altas, FAMEDSA/VRIIP más bajas — sin corrección por
comparaciones múltiples, ver limitación en D29). Hallazgo metodológico nuevo: a diferencia de
sexo/jerarquía (atributos fijos, 0 casos con >1 valor entre años), `facultad_jefe` SÍ puede
cambiar entre años para un mismo docente (46/491 casos) — se resolvió con "facultad
predominante", extensión del criterio D27.

**Distribución de la Jornada (`jornada_dot`) — 3 diapositivas construidas y verificadas
(2026-08-04), ver D30.** Otra dimensión nueva pedida por la contraparte, dentro del universo
Jornada (no otro universo): horas semanales de dotación. `distribucion_horas/` (`agregar_todas`,
3 slides): intro sin gráfico, dona de composición (Completa 44h 67.0% / Parcial <44h 18.1% /
Sin dato-variable 14.9%) con un callout de detalle de jornada parcial (flecha + mini scatter de
puntos, tamaño ∝ N°), y comparación por sexo/escalafón (2 paneles, barra 100% apilada, mismo
colapso Docente/Regular del resto de P1). Sin prueba t — no fue pedida esta vez, a diferencia
del resto de P1. Hallazgo: mujeres y escalafón Docente tienen jornada parcial con más
frecuencia (24.9%/24.2%) que hombres y escalafón Regular (17.6%/9.5%).

**Participación en instancias formativas (sexo/jerarquía/edad) — 3 temas construidos,
verificados y ya compilados al consolidado (2026-08-04), ver D31, Bloque IV parte 2.**
Fuente: `analisis.universo_formados_p3` — confirmado que, pese al nombre, no está filtrada a
`apto_p3` (trae TODA la participación del universo Jornada en Taller/Diplomado/Proyecto).
`participacion_formacion_sexo/`, `participacion_formacion_jerarquia/`,
`participacion_formacion_edad/` — mismo patrón `agregar`/`agregar_ttest`. Resultados: sexo
significativo (p=0.0016, Mujeres 74.4% vs Hombres 62.4%), escalafón muy significativo
(p<0.0001, Docente 76.5% vs Regular 48.9%), **edad NO significativa** (p=0.0724, 47.4 vs 49.4
años) — la diapositiva de prueba t de edad se excluyó del consolidado (mismo criterio que
aprobacion_reprobacion_antiguedad_4tramos/3tramos), pero el descriptivo por tramo de edad sí
se incluyó.

**Aún sin generar**: EDD por tipo de contrato (Jornada vs Honorario), evolución 2022-2025 —
nota: `edd_total_avg` bajó de ~0.85-0.88 en 2022-2023 a ~0.67-0.68 en 2024-2025, vale la pena
mirar por qué antes de asumir que es un hallazgo real y no un cambio de metodología de medición
entre años. **Tampoco se decidió todavía** si estas 3 (o las futuras) se suman al consolidado
`generar_presentacion.py` como Bloque IV (hoy placeholder "sin avance aún" en
`slides_estructura.py`) — no asumir, preguntar al usuario cuándo corresponda. Seguir el mismo
flujo: preguntar al usuario qué corte quiere antes de construir, no asumir.

Fuera de eso, no hay una lista de pendientes explícita del usuario — Bloque II y Bloque IV de
`P1_presentacion.pptx` siguen vacíos por decisión explícita (sin avance real todavía, no
inventar contenido para llenarlos). Si el usuario pide seguir, preguntarle directamente qué
sigue en vez de asumir.
