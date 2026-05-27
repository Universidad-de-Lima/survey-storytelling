# Arquitectura del Sistema de Encuestas de Satisfacción (AI-First)

Este documento describe la arquitectura técnica del sistema de visualización de encuestas. Está diseñado para ser interpretado de forma determinista por agentes de IA y desarrolladores humanos.

## 1. Mapa de Componentes y Dependencias

```mermaid
graph TD
    CSV[CSV de Zoho Survey] -->|Input| ETL[build_json.py]
    ETL -->|Genera| JSON[Contratos JSON]
    JSON -->|Carga| JS[dashboard.js]
    CSS[Estilos Dashboard] -->|Presentación| HTML[index.html]
    JS -->|Manipulación DOM| HTML
```

### 1.1 Directorios Clave
- `zoho-survey/shared/`: Lógica y estilos reutilizables entre todas las encuestas.
- `zoho-survey/students/`: Datos y scripts específicos para encuestas estudiantiles.
- `zoho-survey/students/undergraduate/{periodo}/`: Implementación de una instancia específica de encuesta.

## 2. Pipeline de Datos (ETL)

El proceso de transformación es gestionado por `assets/zoho-survey/students/scripts/build_json.py`.

### Responsabilidades Técnicas:
- **Normalización**: Renombrado de columnas de Zoho Survey a nombres internos estandarizados (ver `COLUMN_RENAME` en el script).
- **Agregación**: Cálculo de NPS (Net Promoter Score) y CSAT (Customer Satisfaction Score) por carrera, facultad y ciclo.
- **Análisis Semántico**: Extracción de tópicos basada en palabras clave para comentarios NPS (detractores y pasivos).
- **Idempotencia**: El script procesa los CSV en `data/` y genera archivos JSON en la carpeta del periodo correspondiente sin efectos secundarios acumulativos.

## 3. Capa de Visualización (Frontend)

El frontend es una aplicación de una sola página (SPA) estática diseñada para alto rendimiento.

### 3.1 `dashboard.js` (Lógica Central)
- **Estado**: Gestionado a través de un objeto `cache` para evitar re-peticiones de red.
- **Filtrado**: Lógica de filtrado multidimensional (Facultad -> Carrera -> Ciclo) implementada en `filtrarDatos()`.
- **Renderizado**: Manipulación directa del DOM basada en eventos de cambio en los selectores.
- **Dependencias Externas**: Ninguna (Vanilla JS), excepto Chart.js (si se añade) o SVGs inline para gráficos de radar.

### 3.2 `dashboard.css` (Diseño)
- Basado en variables CSS para facilitar cambios de tema.
- Layout responsivo utilizando Flexbox y CSS Grid.

## 4. Patrones Arquitectónicos Identificados

- **Separación de Datos y Vista**: Los datos residen exclusivamente en archivos JSON; el JavaScript solo consume estos contratos.
- **Delegación de Eventos**: El sistema de filtrado utiliza listeners en los elementos raíz para optimizar el rendimiento.
- **Registry de DOM**: Referencias centralizadas a elementos del DOM en el objeto `DOM` para evitar búsquedas repetitivas (`document.getElementById`).

## 5. Deuda Técnica y Fragilidad (Advertencia para IA)

- **Acoplamiento de Columnas**: El script ETL depende de que los nombres de las columnas en el CSV de Zoho Survey sean idénticos a los definidos en `COLUMN_RENAME`. Cualquier cambio en Zoho Survey romperá el pipeline.
- **Lógica de Ciclos Hardcoded**: `dashboard.js` contiene lógica específica para "Estudios Generales" y carreras de 12 ciclos (`CARRERAS_12_CICLOS`). Esta lógica debería migrarse a un archivo de configuración (`periodos.json`).
- **Escalabilidad del JSON**: Actualmente se cargan múltiples archivos JSON pequeños. Para conjuntos de datos masivos, esto podría causar problemas de latencia de red en conexiones lentas.

## 6. Convenciones de Desarrollo

- **Nomenclatura**: CamelCase para variables JS, kebab-case para clases CSS e IDs de HTML.
- **Compatibilidad**: Debe funcionar en navegadores modernos sin necesidad de transpiler (ES6+).
- **Estado Estático**: La arquitectura debe permitir el despliegue en GitHub Pages sin servidor dinámico.
