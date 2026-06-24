# 1. Resumen ejecutivo del proyecto

El proyecto `survey-storytelling` es un sistema estático de visualización de resultados de encuestas de satisfacción destinado a la Universidad de Lima. Su principal objetivo es convertir archivos CSV crudos, exportados desde la plataforma Zoho Survey, en dashboards interactivos y analíticos. 

La característica más importante del sistema es su enfoque **"Static Site Generation" impulsado por un ETL de datos local**: no existe un backend activo, API en tiempo real ni base de datos tradicional. El pipeline extrae métricas (NPS, CSAT), aplica procesamiento de lenguaje natural (NLP) offline sobre comentarios abiertos, genera un conjunto de contratos JSON pre-computados (v2.0/v3.0) y los disponibiliza para ser consumidos por una Single Page Application (SPA) minimalista desarrollada en Vanilla JavaScript. El sistema final se despliega íntegramente de manera estática a través de GitHub Pages.

# 2. Stack tecnológico identificado

- **Backend / ETL Data Pipeline**: Python 3
- **Procesamiento y Machine Learning**: `pandas`, `scikit-learn`, `spacy` (para segmentación sintáctica), `sentence-transformers` (para análisis de sentimientos, intensidades y embeddings offline).
- **Validación de Datos**: `jsonschema` (usado para asegurar que los JSONs producidos cumplan los contratos).
- **Frontend**: Vanilla JavaScript (ES5/ES6 sin módulos transpilados, organizado en funciones IIFE bajo el namespace global `window.Survey*`), HTML5 nativo, Vanilla CSS (organizado modularmente con Design Tokens).
- **Dependencias de Desarrollo UI**: Ningún framework (ni React, ni Vue). Sin empaquetadores (webpack/vite). 
- **Gestión de Entorno y Tareas**: npm (utilizado exclusivamente como task runner en `package.json` para ejecutar comandos Python y levantar el servidor HTTP local).
- **Despliegue y CI/CD**: GitHub Actions (`.github/workflows/` para correr validaciones y publicar a GitHub Pages).

# 3. Arquitectura actual

El sistema implementa una arquitectura precomputada y desconectada que separa estrictamente la transformación de datos del renderizado visual:

1.  **Capa de Extracción y Transformación (ETL)**: Orquestada por Python, ingiere archivos CSV. Reconoce patrones de archivos para determinar niveles (pregrado, graduados, docentes). Calcula todas las métricas matemáticas y aplica IA para categorización cualitativa.
2.  **Capa de Transporte (Contratos JSON)**: Se generan diccionarios inmutables por cada periodo académico (`dashboard_data.json`, `filtros.json`, `dimensiones.json`, `sentimiento.json`, etc.). Son los "contratos de datos".
3.  **Capa de Orquestación Frontend (Loader)**: El punto de entrada público es `zoho-survey/index.html` y su `loader.js`. Este se encarga de determinar qué encuestas, niveles y periodos están disponibles e inyecta dinámicamente un `iframe` para aislar el contexto.
4.  **Capa de Presentación (Dashboard)**: Dentro del `iframe`, la página generada por periodo (basada en `zoho-survey/template/index.html`) delega la carga y visualización de datos al archivo `dashboard.js`. Este script distribuye responsabilidades en componentes puros (`radar-chart.js`, `sentiment-view.js`, `filter-controller.js`) que manipulan directamente el DOM para generar gráficas interactivas y tablas sin recalcular métricas base.

# 4. Estructura del repositorio

El repositorio sigue un patrón modular bastante atípico pero funcional:

```text
survey-storytelling/
├── data/                    # (Inputs) Archivos CSV crudos de Zoho Survey.
├── docs/                    # Documentación operativa, de negocio y changelog.
├── tests/                   # Pruebas unitarias adaptadas al navegador.
├── zoho-survey/             # Entorno principal del aplicativo.
│   ├── index.html           # (Punto de entrada) Loader SPA general.
│   ├── scripts/             # Core del ETL en Python y esquemas (schemas JSON).
│   │   └── lib/             # Submódulos Python (config, metrics, nlp, sentiment_engine, etc.).
│   ├── shared/              # Assets estáticos reutilizables del frontend.
│   │   ├── css/             # Capas CSS aisladas (tokens, layout, components).
│   │   ├── js/              # Componentes, utilidades y orquestador (dashboard.js).
│   │   └── img/             # Isotipos, logotipos y gráficos globales.
│   ├── template/            # Plantilla HTML "molde" inyectada para cada nuevo periodo procesado.
│   └── [audiencias]/        # e.g., students/, alumni/ Directorios generados dinámicamente.
│       └── [nivel]/         # e.g., undergraduate/, graduate/
│           └── [periodo]/   # El output final: HTML y subcarpeta json/ con la data procesada.
├── package.json             # Task runner y declarador de scripts NodeJS.
├── requirements.txt         # Dependencias del ecosistema Python.
└── [Archivos .md raíz]      # README.md, ARCHITECTURE.md, CONTRACTS.md, AGENTS.md (Documentación obligatoria).
```

# 5. Flujo principal de funcionamiento

1.  **Ingesta**: El usuario coloca un archivo exportado de Zoho (ej. `ENCUESTA DE SATISFACCIÓN ESTUDIANTIL- PREGRADO - 2026-1.csv`) en la carpeta `data/`.
2.  **Procesamiento (Build)**: Se ejecuta el comando `npm run build:json` (que invoca internamente `build_json.py`).
3.  **Transformación**: Python escanea el directorio, infiere que es de "pregrado", estandariza los nombres de columnas mediante mapeos predefinidos, y procede a calcular todas las matemáticas de NPS, CSAT y procesa los comentarios textuales extrayendo tópicos e intensidades.
4.  **Generación de Estructura**: El ETL crea el directorio `zoho-survey/students/undergraduate/2026-1/`. Copia el contenido de `zoho-survey/template/index.html` allí y aloja los resultados particionados en múltiples archivos dentro de la subcarpeta `/json/`.
5.  **Consumo**: En el navegador, el usuario entra al loader genérico (`zoho-survey/index.html`). Al seleccionar el periodo "2026-1", el loader apunta su `iframe` hacia el HTML recién copiado. Dicho HTML importa `dashboard.js`, el cual hace fetch a sus propios archivos JSON relativos y renderiza el dashboard final interactivo con filtros en cascada.

# 6. Componentes y archivos importantes

- **`zoho-survey/scripts/build_json.py`**: El gran orquestador (822+ líneas). Coordina toda la etapa del ETL, derivando cargas complejas a los scripts de `lib/`.
- **`zoho-survey/scripts/lib/config.py`**: El corazón del negocio a nivel backend. Contiene los diccionarios explícitos de estandarización, renombre de columnas e identificadores estables para facultades y carreras.
- **`zoho-survey/shared/js/dashboard.js`**: Controlador maestro del DOM (Frontend). Define flujos asíncronos para cargar los JSONs y poblar los controladores UI (`filter-controller.js`, renders de tablas y tarjetas).
- **`zoho-survey/shared/js/components/sentiment-view.js`**: El módulo más complejo a nivel visual, encarga de presentar la vista del análisis cualitativo, paginar comentarios y permitir la búsqueda textual combinada con filtros semánticos (sentimiento, intensidad).
- **`zoho-survey/shared/css/tokens.css`**: Define la paleta visual, espaciados y tipografías corporativas, garantizando la consistencia estética.

# 7. Dependencias y configuración

- **Sistema Gestor**: No utiliza NPM/NodeJS para dependencias en el proyecto real (el `package.json` solo almacena scripts). Todo el stack recae sobre Python.
- **Librerías Críticas (Python)**: `pandas` para estructurar la data, `spacy` y `sentence-transformers` para el pipeline profundo de NLP local, garantizando que el análisis de comentarios no requiera llamar a APIs externas como OpenAI y no genere latencia en la UI final.
- **Configuraciones de Entorno**: No existen archivos `.env`. Toda la configuración es determinística y está inyectada o descrita en `zoho-survey/scripts/lib/config.py` para el backend y `zoho-survey/shared/js/config/constants.js` para el frontend.

# 8. Hallazgos técnicos

## Hechos observados
- El frontend carece de dependencias modernas complejas (Virtual DOMs). Prioriza rendimiento puro, manipulación nativa de nodos (`document.createElement`, `innerHTML` tras sanitización) y eventos delegados.
- Existen componentes de visualización propios construidos de cero, como un gráfico de radar en SVG puro (`radar-chart.js`).
- El análisis cualitativo es avanzado y no solo mide NPS numérico, sino que incluye *Sentiment Analysis*, corrección tipográfica subyacente para facilitar lectura rápida y mapeo de "Temas Padre".

## Inferencias
- Dada la arquitectura altamente desacoplada y precalculada, el dashboard web es capaz de manejar miles de respuestas en el frontend sin latencia aparente, puesto que todo el peso computacional pesado (joins, promedios, NLP) ocurre a nivel local durante la construcción (build-time).

## Suposiciones pendientes
- La inmutabilidad de la estructura CSV de Zoho: Al depender fuertemente de mapeos explícitos (ej: "Net Promoter Score (de un total de 10)"), cualquier cambio menor de redacción que aplique un administrador en la encuesta origen en Zoho Survey hará fallar todo el pipeline de recolección Python a menos que se ajuste el `config.py`.

## Riesgos identificados
- **Alta sensibilidad del contrato ETL**: Cambios en las lógicas dentro de Python podrían afectar severamente los archivos JSON resultantes, rompiendo el renderizado de JS si no se cumplen los `CONTRACTS.md`.
- **Lógica de Ciclos externalizada**: La deuda técnica menciona y el código demuestra que la configuración de ciclos está acoplada al frontend en `constants.js` (SURVEY_CONFIG), restando cierto dinamismo puro dependiente de la data que viaja en el backend.

# 9. Diferencias entre documentación y código

El proyecto goza de una documentación (`ARCHITECTURE.md`, `CONTRACTS.md`, `AGENTS.md`) asombrosamente precisa, detallada y disciplinada. Todo lo documentado refleja el código real:

- **Coincidencias**: La estructura de capas CSS, la separación estricta entre el proceso de datos y el motor de renderizado JS, la existencia de los contratos v2.0/v3.0. Todo cuadra con su respectivo código o esquema de validación (`schemas/`).
- **Deuda Técnica Acertada (Código Legacy)**: El documento `ARCHITECTURE.md` advierte explícitamente sobre la existencia de código Legacy inactivo en `zoho-survey/scripts/lib/nlp.py`. Al auditar el archivo, en efecto existe una porción sustancial (aprox 19KB) con métodos de iteraciones antiguas que coexisten peligrosamente con los sistemas nuevos.
- **Placeholders reales**: `ARCHITECTURE.md` menciona `posgraduate/` como placeholder sin datos activos procesados, lo cual es comprobable al revisar el directorio en `zoho-survey/students/posgraduate`.

# 10. Recomendaciones iniciales (solo después del análisis)

1. **Eliminar y Purgar el Código Legacy Documentado**: Como primer paso para mejorar la mantenibilidad, es recomendable abordar la deuda documentada en el módulo `nlp.py`, purgando lógicas y rutinas deprecadas asegurando que no rompa el nuevo pipeline (`sentiment_engine.py` / `aspect_extraction.py`).
2. **Respetar la Arquitectura Estricta Vanilla**: Prohibido tajantemente sugerir migraciones a React/Vue. Las implementaciones futuras deben realizarse manipulando el DOM nativo e inyectando comportamientos mediante IIFEs.
3. **Manejar con Precaución las Constantes del Frontend (`constants.js`)**: Al momento de introducir nuevos tipos de encuestas, asegurar que exista total coherencia entre las llaves expuestas por el JSON generado en el backend y los diccionarios hardcodeados en el frontend para evitar fallos de renderizado. 

El análisis del repositorio ha concluido exitosamente y tengo una comprensión total de los componentes. Me encuentro a la espera de tus siguientes instrucciones.