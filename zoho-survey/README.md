# zoho-survey

Aplicacion estatica principal. Contiene el loader, assets compartidos, scripts ETL, templates y dashboards generados por nivel academico y periodo.

Para arquitectura general ver `../ARCHITECTURE.md`. Para contratos JSON ver `../CONTRACTS.md`.

## Estructura Local

```text
zoho-survey/
├── index.html                 # Loader publicado en GitHub Pages
├── underconstruction.html     # Placeholder
├── shared/                    # CSS, JS e imagenes compartidas
├── template/                  # Template HTML para nuevos periodos
├── scripts/                   # ETL, validacion y schemas
└── students/                  # Dashboards y datos por nivel/periodo
```

## Scripts Principales

| Ruta | Responsabilidad |
| --- | --- |
| `scripts/build_json.py` | Transforma CSVs de `../data/` en JSONs por periodo. |
| `scripts/validate_generated_json.py` | Valida estructura de JSONs y contratos HTML esperados. |
| `scripts/lib/config.py` | Configuracion ETL externalizada: columnas, mappings y topicos. |
| `scripts/schemas/` | JSON Schemas para contratos versionados. |

## Flujo De Ejecucion

Desde la raiz del repo:

```bash
python zoho-survey/scripts/build_json.py
python zoho-survey/scripts/validate_generated_json.py undergraduate
npm start
```

Abrir `http://localhost:8080/zoho-survey/`.

## Reglas Locales

- No modificar manualmente archivos en `students/**/json/`.
- Cambios en la forma de datos deben actualizar `../CONTRACTS.md`.
- Cambios en estructura compartida deben actualizar `../ARCHITECTURE.md`.
- El frontend debe seguir funcionando como sitio estatico en GitHub Pages.

## Deuda Tecnica Local

- `posgraduate/` permanece como placeholder.
- `nps_carrera.json` y `csat_carrera.json` son legacy.
- `template/index.html` no tiene version de contrato propia.
