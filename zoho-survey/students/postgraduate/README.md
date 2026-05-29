# students/postgraduate

Estructura preparada para dashboards de encuestas de **posgrado**. Actualmente contiene solo archivos placeholder (`.txt` vacíos) sin datos procesados ni instancias de dashboard funcionales.

## Architecture Role

Espacio reservado para futuras encuestas de posgrado. Sigue la misma convención de estructura que `undergraduate/` (subdirectorios por año con `json/` y `index.html`), pero sin datos reales.

## Current State

```
postgraduate/
├── 2025/
│   ├── 1.txt           # Placeholder (empty)
│   └── json/           # Empty directory
└── 2026/
    ├── 1.txt           # Placeholder (empty)
    └── json/           # Empty directory
```

## Activation Requirements

Para activar el módulo de posgrado:

1. Colocar archivo CSV con nombre conteniendo `POSGRADO` en `students/data/`
2. El nombre debe incluir el patrón de periodo `(20\d{2}-[12])`
3. Ejecutar `python scripts/build_json.py`
4. El ETL generará automáticamente:
   - `postgraduate/{periodo}/index.html` (copiado del template)
   - `postgraduate/{periodo}/json/*.json` (13 contract files)
   - `postgraduate/periodos.json` (auto-generado)

## Technical Debt

- **Estructura huérfana**: Los directorios `2025/` y `2026/` existen sin datos válidos. El validador fallará si se ejecuta `validate_generated_json.py postgraduate`.
- **Archivos .txt placeholder**: Los archivos `1.txt` están vacíos y no tienen propósito funcional. Deben ser reemplazados por datos reales o eliminados.
- **Sin periodos.json**: El archivo `periodos.json` de posgrado no existe hasta que se ejecute el ETL con datos de posgrado.

## AI Agent Notes

- El ETL detecta el nivel `postgraduate` por el substring `POSGRADO` en el nombre del CSV.
- `validate_generated_json.py postgraduate` actualmente falla porque no hay JSON válidos.
- La estructura de directorios `{año}/` (sin semestre) difiere de la convención de pregrado `{año}-{semestre}/`. El ETL usa el regex `(20\d{2}-[12])` que extrae el periodo del nombre del archivo, no del directorio.
