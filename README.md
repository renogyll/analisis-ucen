# Análisis UCEN — Perfeccionamiento Docente P3

Proyecto de análisis de impacto del programa de perfeccionamiento docente P3 de la UCEN.

## Estructura

```
analisis-ucen/
├── config.py              # rutas y constantes centralizadas
├── data/
│   ├── raw/               # datos originales de la contraparte (no en git)
│   └── cascade/           # CSVs generados por ETL, organizados por filtro (no en git)
├── etl/                   # scripts que generan la cascada de universos
├── qa/                    # validaciones de integridad de datos
├── slides/                # generadores de presentaciones PPTX
├── word/                  # generadores de documentos Word
├── analisis/              # scripts de visualización por supuesto metodológico
├── docs/                  # documentación metodológica
│   └── CASCADE.md         # registro de cada nivel del universo y sus filtros
├── outputs/               # archivos generados (no en git)
└── archive/               # trabajo histórico
    └── legacy_918/        # análisis con universo jerarquizados (N≈918)
```

## Cascada de universos

Ver [docs/CASCADE.md](docs/CASCADE.md) para el detalle de cada filtro y los N reales.

El universo base son todos los docentes únicos (por RUT) del cruce NOMINA × DOTACION.
La jerarquía académica es un campo/etiqueta, no un filtro que margina instancias.

## Cómo correr

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Generar universo base
python etl/00_base/etl_nomina_dotacion.py

# 3. Generar la presentación principal
python slides/presentacion_principal/generar_presentacion.py
```

## Contexto histórico

El análisis previo (universo N≈918, jerarquizados) está preservado en `archive/legacy_918/`.
Ver `archive/legacy_918/README_918.md` para la explicación del supuesto original.
