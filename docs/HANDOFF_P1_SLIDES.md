# Traspaso de sesión — P1 Caracterización Cuerpo Académico (Jornada)

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

## Estado actual (commit `54faf24`, 2026-08-04)

`products/p1_planta/generar_presentacion.py` genera el consolidado `P1_presentacion.pptx`
(en `outputs/pptx/`, carpeta gitignoreada — hay que correr el script para regenerarlo, no está
versionado). **30 diapositivas**, estructura:

- **1-4**: Portada + 2 grillas de apertura (resumen Bloque I+II, resumen Bloque III+IV) + Bloque I Universo/Índice/Hallazgos
- **5-7 (Bloque I — caracterización demográfica)**: sexo/edad, edad por jerarquía, grado académico por sexo
- **8-14 (Bloque II — evaluación estudiantil)**: dimensiones APR/MET/AFO del instrumento de evaluación estudiantil
- **15-23 (Bloque III, parte 1 — aprobación/reprobación directa)**: global, por sexo (+prueba t), por escalafón (+prueba t), por antigüedad (2 variantes), evolución por sexo
- **24-30 (Bloque III, parte 2 — grupos de dificultad de asignaturas, D27)**: composición, antigüedad/edad/sexo según grupo de dificultad (cada uno con su prueba t)

**Bloque II vacío** (sin avance) y **Bloque IV** (sin definir) quedan como placeholders
honestos ("sin avance aún") en las diapositivas estructurales — no se inventó contenido.

Todo el trabajo de hoy está **commiteado**. `git log --oneline -3` para confirmar el estado real
antes de asumir nada (esto puede quedar desactualizado si el usuario sigue trabajando).

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

## Qué falta / posibles próximos pasos

No hay una lista de pendientes explícita del usuario al cierre de esta sesión — el último pedido
fue justamente cerrar y consolidar. Si el usuario pide seguir, preguntarle directamente qué
sigue en vez de asumir. Bloque II y Bloque IV siguen vacíos por decisión explícita (sin avance
real todavía, no inventar contenido para llenarlos).
