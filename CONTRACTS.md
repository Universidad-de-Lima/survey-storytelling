# Contratos de Datos (AI-First)

Este documento define los esquemas y responsabilidades de los datos que fluyen a través del sistema.

## 1. Contrato de Entrada (CSV de Zoho Survey)

El archivo CSV de origen debe contener las columnas mapeadas en `build_json.py`.

### Dependencias Críticas:

- `ID de respuesta`: Identificador único.
- `Net Promoter Score (de un total de 10)`: Escala 0-10 para cálculo de NPS.
- `¿Qué carrera profesional estudias?`: Base para filtrado por carrera.
- `¿Qué ciclo es el que cursas?`: Base para filtrado por ciclo.

## 2. Contratos de Salida (JSON) — v2.0

El pipeline ETL genera **9 archivos** en `json/` (7 obligatorios + 2 legacy):

| Archivo | Tipo | Versión | Obligatorio |
|---------|------|---------|-------------|
| `dashboard_data.json` | object | ✅ `"2.0"` | Sí |
| `dimensiones.json` | array | implícita | Sí |
| `ids.json` | array | implícita | Sí |
| `nps_ciclo_carrera.json` | array | implícita | Sí |
| `csat_ciclo_carrera.json` | array | implícita | Sí |
| `filtros.json` | object | ✅ `"2.0"` | Sí |
| `sentimiento.json` | object | ✅ `"2.0"` | Sí |
| `nps_carrera.json` | array | implícita | Legacy |
| `csat_carrera.json` | array | implícita | Legacy |

### 2.1 `dashboard_data.json`

Contiene los agregados globales de la encuesta.

- **Schema**: `scripts/schemas/dashboard_data.schema.json` (JSON Schema draft-07)
- **Esquema resumido**:
  ```json
  {
    "version": "2.0",
    "resumen": { "nps": { "score": 65.4 }, "csat": { "score": 92.1 } },
    "nps": { "Promotores": 2669, "Pasivos": 1111, "Detractores": 218 },
    "csat": { "Totalmente satisfecho": 1626, "Muy satisfecho": 1135 }
  }
  ```
  }
  ```

### 2.2 `dimensiones.json`

Resultados de satisfacción por dimensiones específicas (ej. Calidad docente, Infraestructura).

- **Esquema**: Array de objetos con el promedio de satisfacción (0-100%).

### 2.3 `sentimiento.json`

Análisis de tópicos de los comentarios NPS.

- **Esquema**:
  ```json
  {
    "topicos": [
      {
        "nombre": "Calidad docente",
        "menciones": 45,
        "sentimiento": "positivo",
        "icon": "📚"
      }
    ]
  }
  ```

## 3. Responsabilidades por Capa

### 3.1 Capa ETL (Python)

- **Responsabilidad**: Transformación determinista. No debe realizar suposiciones sobre el layout visual.
- **Garantía**: Si el CSV es válido, el JSON generado debe cumplir estrictamente con los esquemas anteriores.

### 3.2 Capa Frontend (JavaScript)

- **Responsabilidad**: Consumo de datos. No debe recalcular promedios ni agregaciones que ya debieron ser procesadas por el ETL.
- **Garantía**: El frontend fallará de forma controlada (graceful degradation) si un archivo JSON falta o está corrupto.

## 4. Invariantes de Datos

1. **Rango NPS**: -100 a +100.
2. **Rango CSAT**: 0% a 100%.
3. **Integridad Referencial**: Los IDs de carrera en `filtros.json` deben coincidir con los usados en `nps_carrera.json` y `csat_carrera.json`.

## 5. Deuda Técnica en Contratos

- ✅ **Falta de Versión** (resuelto v2.0): `dashboard_data.json`, `filtros.json` y `sentimiento.json` incluyen `"version": "2.0"`.
- ⚠️ **Redundancia NPS/CSAT**: `nps_ciclo_carrera.json` y `csat_ciclo_carrera.json` contienen la unión de datos por carrera y por ciclo. Podrían consolidarse si la latencia se vuelve un problema.
- ⚠️ **Archivos legacy**: `nps_carrera.json` y `csat_carrera.json` se generan pero el frontend usa `nps_ciclo_carrera.json`/`csat_ciclo_carrera.json`. Eliminarlos requeriría refactorizar `renderDetalleCarreras()`.
