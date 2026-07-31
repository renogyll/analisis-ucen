# Análisis UCEN

Consultoría de análisis para UCEN. Cubre los 4 productos de los Términos de Referencia
(TdR): caracterización del cuerpo académico de planta (P1), participación en formación
docente (P2), perfeccionamiento docente / SAT-EDD (P3), y evaluación/rediseño del
instrumento de evaluación docente (P4).

| Producto | Descripción | Monto TdR | Estado |
|---|---|---|---|
| **P1** | Caracterización del cuerpo académico de planta | $2.000.000 | No iniciado |
| **P2** | Participación en formación docente | $600.000 | No iniciado |
| **P3** | Perfeccionamiento docente (SAT, rendimiento académico, EDD) | $1.400.000 | Completo |
| **P4** | Evaluación y rediseño del instrumento de evaluación docente (cualitativo) | $2.000.000 | No iniciado |

## Estructura

```
analisis-ucen/
├── config.py               # rutas y constantes centralizadas (BASE, CASCADE, ASSETS...)
├── data/                    # no está en git (ver abajo)
│   ├── raw/                 # datos originales de la contraparte
│   ├── staging/              # CSV intermedios antes de cargar a Postgres
│   └── cascade/              # CSVs de la cascada de universos, por nivel
├── assets/                   # plantillas de diseño (Fondotipop.pptx) — no está en git
├── docs/                     # documentación metodológica y TdR
├── outputs/                  # archivos generados (PPTX/DOCX/PNG) — no está en git
├── archive/                   # trabajo histórico (universo legacy N≈918, prototipos)
├── shared/                    # pipeline de datos común a todos los productos
│   ├── etl/
│   │   ├── 00_base/, 01_jornada/, 02_honorario/, docker/
│   │   └── complementarios/    # ingesta, tabla_docente, participación, evaluaciones...
│   └── qa/
└── products/
    ├── p1_planta/              # ver products/p1_planta/README.md
    ├── p2_formacion/           # ver products/p2_formacion/README.md
    ├── p3_perfeccionamiento/   # ver products/p3_perfeccionamiento/ (completo)
    │   ├── etl/03_jerarquizados/, 04_formados_p3/, 05_aptos_p3/, complementarios/
    │   ├── slides/presentacion_principal/, comparacion_grupos/, fichas/
    │   ├── word/, qa/core/, qa/jerarquia_revision/
    └── p4_instrumento_edd/     # ver products/p4_instrumento_edd/README.md
```

## Por qué esta división

El proyecto se desarrolló íntegramente para P3 antes de que arrancaran P1/P2/P4. La
cascada de universos (`00_base → 01_jornada/02_honorario → 04_formados_p3 → 05_aptos_p3`)
es común a varios productos, así que vive en `shared/`. Lo que es específico de la
presentación/análisis de cada producto vive en `products/<nombre>/`.

Dentro de cada producto, el trabajo nuevo (P1, P2) se organiza **por bloque temático**,
no por tipo técnico: cada sub-análisis junta en una misma carpeta el script generador,
su CSV de referencia y el PNG de salida. P3 (ya construido antes de este criterio) sigue
organizado por tipo (`etl/`, `slides/`, `word/`, `qa/`) — su remapeo a bloques queda
pendiente de una pasada futura.

## Cascada de universos

Ver [docs/CASCADE.md](docs/CASCADE.md) para el detalle de cada filtro y los N reales.

El universo base son los 1.144 docentes únicos (por RUT) del cruce NOMINA × DOTACION
(Jornada + Honorario). La jerarquía académica es un campo/etiqueta descriptivo, no un
filtro que margina instancias — el nivel `03_jerarquizados` es un subconjunto de
análisis específico de P3, no el punto de partida del proyecto.

## Cómo correr

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Generar el universo base y la cascada (orden: A → B → D → C → resto)
python shared/etl/00_base/etl_universo_base.py
python shared/etl/01_jornada/etl_jornada.py
python shared/etl/02_honorario/etl_honorario.py

# 3. Generar la presentación principal de P3
python products/p3_perfeccionamiento/slides/presentacion_principal/generar_presentacion.py
```

## Contexto histórico

El análisis previo (universo N≈918, jerarquizados) está preservado en `archive/legacy_918/`.
Ver `archive/legacy_918/README_918.md` para la explicación del supuesto original.
