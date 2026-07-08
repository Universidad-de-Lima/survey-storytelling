# Migración del Análisis Cualitativo a IA (DeepSeek)

Documento de referencia para el cambio del pipeline cualitativo local (spaCy + sentence-transformers) a un motor basado en DeepSeek, calibrado con metodologías de Análisis Cualitativo y validado contra el análisis manual humano de la encuesta 2026-1.

---

## 1. Diagnóstico: por qué migrar

### 1.1 Brecha cuantitativa del pipeline legacy vs análisis manual

La ejecución de `validar_ia_vs_manual.py` comparando el `dataset_cualitativo.json` actual (generado por el pipeline legacy) contra `analisis_nps_cualitativo.xlsx` (ground truth humano, 2119 fragmentos de 924 comentarios) arrojó:

| Métrica | Legacy vs Manual | Interpretación |
|---|---|---|
| Cobertura de comentarios | 90.97% | 9 de cada 10 comentarios del manual aparecen en el legacy |
| Promedio fragmentos/comentario | Manual 2.10 vs Legacy 2.50 | **Legacy sobre-segmenta** (+19%) |
| Accuracy sentimiento | **59.7%** | 4 de cada 10 unidades mal clasificadas |
| Cohen's Kappa (sentimiento) | **0.3357** | Concordancia "fair" (Landis & Koch) — insuficiente |
| Accuracy taxonomía (dimensión) | **32.58%** | Solo 1 de cada 3 unidades con dimensión correcta |
| Accuracy categoría padre | 50.05% | Apenas mejor que azar (4 categorías → 25% baseline) |
| Accuracy validez | 97.8% | Bien |
| Pendiente de Clasificación | Manual 34 vs Legacy **502** | Legacy deja **15x más** unidades sin clasificar |

### 1.2 Causas raíz identificadas en el código legacy

1. **`segmentacion_nps.py` (323 líneas)**: Dependencia frágil del parsing de spaCy (POS tags, dependency labels). Heurísticas como Right-Node Raising y Left-Node Raising fallan en español informal ("q", "xq", "megusta"). Ejemplos observados:
   - "cosas que mejorar" se divide en 2 fragmentos incorrectos.
   - "Falta de enchufes en las aulas" + "mal funcionamiento de los ascensores" se mergea en 1 solo.

2. **`sentiment_engine.py`**: Anclas semánticas + softmax con temperatura 10. El propio código admite el problema del **"argmax degenerado"**: cuando los 3 scores son iguales (0,0,0), argmax cae arbitrariamente en "positivo". Resultado: 1279 positivos vs 800 negativos, cuando el manual muestra 681 vs 1135 (inverso).

3. **`aspect_extraction.py`**: Alias dict (exact match) + embeddings con umbral cosine > 0.55. El 30% de unidades cae a "Pendiente de Clasificación" vs 5.3% en el manual. Las dimensiones catch-all ("Satisfacción estudiantil", "Espacios comunes") no se usan efectivamente.

4. **Reglas de contexto NPS NO implementadas**: el motor no sabe que un Promotor (NPS 9-10) no debería tener mayoría de unidades Negativas. Sin esta triangulación, el análisis es vulnerable al sesgo de deseabilidad social del comentario abierto.

5. **Cross-reference CSAT NO implementado**: cuando un estudiante menciona "las aulas" en su comentario, el motor no vincula esa mención con la calificación CSAT que el mismo estudiante dio a la pregunta "Las aulas de clase". Se pierde la triangulación cualitativa-cuantitativa.

6. **Dimensión "Espacios comunes" ausente**: el análisis manual la usa 237 veces para referencias genéricas a espacios del campus, pero no existe en `CATEGORIA_DIMENSION_PREGRADO`.

---

## 2. Camino recomendado

### 2.1 Arquitectura: Build-time AI en GitHub Actions

**NO se recomienda** migrar a una app con backend runtime (Next.js API + DeepSeek llamado por el navegador). Razones:
- Rompería el modelo de despliegue actual (GitHub Pages, estático, gratis).
- Expondría la API key en el cliente o requeriría un backend always-on.
- Latencia en cada carga de dashboard.
- Costo recurrente por visita.

**SÍ se recomienda**: reemplazar los 3 módulos locales del ETL Python por una llamada a DeepSeek **en build time** (dentro del workflow de GitHub Actions). El dashboard sigue siendo estático; solo cambia cómo se generan los JSON.

```
Flujo actual:
  CSV (Zoho) → build_json.py → [segmentacion_nps + aspect_extraction + sentiment_engine] → JSON estático → GitHub Pages

Flujo migrado:
  CSV (Zoho) → build_json.py → [ia_cualitativo.py → DeepSeek API] → JSON estático → GitHub Pages
                                    ↑
                          DEEPSEEK_API_KEY (GitHub Secret)
                          + caché persistente (ia_cache.json)
                          + fallback automático al legacy si no hay key
```

### 2.2 Ventajas de este enfoque

| Aspecto | Beneficio |
|---|---|
| **Calidad** | 1 llamada LLM coherente reemplaza 3 módulos frágiles. Contexto NPS + CSAT disponibles simultáneamente. |
| **Costo** | ~924 comentarios × ~2.5K tokens × $0.28/1M out = **~$0.50 por build completo**. Con caché, builds subsiguientes cuestan ~$0.05. |
| **Determinismo** | `temperature=0.1` + JSON mode + caché por hash(comentario+contexto). Misma entrada → misma salida. |
| **Compatibilidad backward** | Si `DEEPSEEK_API_KEY` no está, el pipeline cae al legacy sin cambios. Cero riesgo de break. |
| **Trazabilidad** | Cada unidad incluye `justificacion_sentimiento` (razonamiento del LLM) + `motor: "deepseek"` en metadata. |
| **Sin nuevas dependencias** | El cliente DeepSeek usa `urllib` (stdlib). No se añade `openai` ni `requests` al `requirements.txt`. |

### 2.3 Cómo activarlo (3 pasos)

**Paso 1 — Obtener API key de DeepSeek**
- Ir a https://platform.deepseek.com/
- Crear cuenta, cargar crédito ($5 alcanzan para ~10 builds completos).
- Generar API key (`sk-...`).

**Paso 2 — Configurar GitHub Secret**
- En el repo: Settings → Secrets and variables → Actions → New repository secret.
- Name: `DEEPSEEK_API_KEY`
- Value: `sk-...`

**Paso 3 — Push a `data/` o `zoho-survey/`**
- El workflow `build_students.yml` ya está parcheado para inyectar el secret como env var.
- En el siguiente push, `build_json.py` detecta `DEEPSEEK_API_KEY`, activa el modo IA, y genera los JSON con DeepSeek.
- El caché `ia_cache.json` se persiste entre builds vía `actions/cache`.

---

## 3. Metodología cualitativa aplicada

Los prompts están fundamentados en tres metodologías de análisis cualitativo reconocidas, adaptadas al contexto de encuestas de satisfacción universitaria en Perú:

### 3.1 Análisis de Contenido — Bardin (2011)

**Aporte**: la **segmentación en Unidades de Significado** (Bardin las llama "unidades de registro"). La regla operativa: cada unidad debe expresar una idea, razón o argumento único, siendo autosuficiente semánticamente.

En el system prompt (sección 1), se codifican:
- Límites naturales: signos fuertes (. ; :), conjunciones contrastivas (pero, aunque, sin embargo).
- Anti-sobre-segmentación: no partir enumeraciones cortas con predicado compartido.
- Anti-sub-segmentación: no producir unidades de una sola palabra sin significado.
- Conservación del texto original del estudiante (errores ortográficos incluidos).

### 3.2 Análisis Temático — Braun & Clarke (2006)

**Aporte**: la **codificación contra una taxonomía deductiva** (la dimensión oficial de la encuesta), con reglas claras para el fallback ("Pendiente de Clasificación" en vez de invención).

En el system prompt (sección 3), se codifican:
- Priorización de dimensión específica sobre catch-all.
- Dimensiones catch-all explícitas: "Satisfacción estudiantil", "Espacios comunes".
- Prohibición de inventar dimensiones fuera de la lista oficial.

### 3.3 Triangulación mixta cualitativa-cuantitativa

**Aporte**: la **REGLA DE CONTEXTO NPS** y el **cross-reference CSAT**. Estas son adaptaciones específicas para encuestas NPS donde se dispone tanto del score cuantitativo (0-10) como del comentario abierto.

**Regla de contexto NPS** (system prompt, sección 2):

| NPS | Segmento | Predominio esperado | Excepción | Intensidad excepción |
|---|---|---|---|---|
| 9-10 | Promotor | Positivo | Negativa = "mención de mejora" | 1-2 (sube a 3 con adjetivos fuertes) |
| 7-8 | Pasivo | Neutro o mixto | — | ≤ 3 (salvo extremo emocional) |
| 0-6 | Detractor | Negativo | Positiva = "salvavidas" | 2-3 (moderada) |

**Justificación teórica**: el NPS cuantitativo ya expresó la tendencia global del estudiante. El comentario abierto debe interpretarse EN COHERENCIA con ese NPS. Un detractor que escribe algo positivo está reconociendo un aspecto rescatable (salvavidas), no cambiando de parecer. Un promotor que escribe algo negativo está sugiriendo una mejora menor, no traicionando su recomendación. Sin esta regla, el análisis es vulnerable al sesgo de deseabilidad social del comentario abierto.

**Cross-reference CSAT** (system prompt, sección 5): cuando la unidad menciona una dimensión que el estudiante calificó, se reporta esa calificación en `dimension_evaluada_rating` y `dimension_evaluada_score`. Esto permite al dashboard responder preguntas como: *"los estudiantes que mencionaron 'Aulas de clase' negativamente en su NPS, ¿qué calificación CSAT le dieron a esa dimensión?"* — triangulando cuali + cuanti.

---

## 4. Los prompts exactos

### 4.1 Dónde están

**Fuente canónica** (Python, para el pipeline de GitHub Actions):
```
zoho-survey/scripts/lib/prompts_cualitativo.py
```

**Mirror en TypeScript** (para el playground Next.js interactivo):
```
/home/z/my-project/src/lib/qualitative-prompts.ts
```

Ambos deben mantenerse sincronizados. El playground sirve para verificar los prompts en vivo antes de desplegarlos al pipeline.

### 4.2 Estructura del system prompt (~18,300 caracteres, ~2,200 palabras)

El system prompt se construye con `build_system_prompt(taxonomia, categorias_padre)` y contiene:

1. **Rol + misión** (~200 palabras): analista cualitativo senior, 5 tareas.
2. **Metodología** (~1,500 palabras):
   - Sección 1: Segmentación en Unidades de Significado (Bardin).
   - Sección 2: Clasificación de Sentimiento con Regla de Contexto NPS (tabla + escala 1-5 + flags `es_mencion_mejora`/`es_salvavidas`).
   - Sección 3: Clasificación Taxonómica (criterios + catch-alls).
   - Sección 4: Validez (8 motivos de invalidez permitidos).
   - Sección 5: Cross-reference CSAT.
3. **Taxonomía oficial** (~400 palabras): inyectada dinámicamente desde `config.py`, agrupada por categoría padre.
4. **Formato de salida JSON** (~300 palabras): schema estricto con 14 campos por unidad.
5. **5 ejemplos calibrados few-shot** (~1,800 palabras):
   - Ejemplo 1: Promotor (NPS 10), comentario corto, 2 unidades positivas.
   - Ejemplo 2: Detractor (NPS 3) con salvavidas, 3 unidades.
   - Ejemplo 3: Pasivo (NPS 8) mixto, 2 unidades.
   - Ejemplo 4: Detractor (NPS 1) con queja fuerte, 3 unidades + adjetivo intenso.
   - Ejemplo 5: Ruido (".."), 1 unidad inválida.

Los ejemplos están calibrados contra el análisis manual humano (extraídos de `analisis_nps_cualitativo.xlsx`).

### 4.3 Estructura del user prompt (~350 caracteres por comentario)

Construido con `build_user_prompt(comentario, nps_score, csat_ratings, id_encuesta)`:

```
Analiza el siguiente comentario del estudiante.

ID encuesta: jetUMWiK
NPS: 10 → Segmento: Promotor
CSAT por dimensión (lo que el estudiante calificó):
{
  "Aulas de clase": "Totalmente satisfecho",
  "Calidad de la enseñanza en la carrera": "Muy satisfecho"
}

Comentario: "Muy buena infraestructura, enseñanza."

Devuelve el JSON con la lista de unidades de significado.
```

### 4.4 Schema JSON de salida (14 campos por unidad)

```json
{
  "unidades": [
    {
      "orden": 1,
      "texto": "Muy buena infraestructura",
      "es_valido": true,
      "motivo_invalidez": null,
      "sentimiento": "Positivo",
      "intensidad": 4,
      "justificacion_sentimiento": "Promotor; adjetivo intenso 'muy buena'...",
      "dimension": "Aulas de clase",
      "categoria_padre": "Infraestructura",
      "es_mencion_mejora": false,
      "es_salvavidas": false,
      "dimension_evaluada_rating": "Totalmente satisfecho",
      "dimension_evaluada_score": 5,
      "sub_aspectos": ["infraestructura", "aulas"]
    }
  ]
}
```

Campos nuevos vs pipeline legacy:
- `es_valido` + `motivo_invalidez`: flag de validez (nuevo).
- `es_mencion_mejora` + `es_salvavidas`: flags de la regla NPS (nuevo).
- `dimension_evaluada_rating` + `dimension_evaluada_score`: cross-reference CSAT (nuevo).
- `justificacion_sentimiento`: trazabilidad del razonamiento LLM (nuevo).
- `sentimiento_display`: con mayúscula inicial (para display; `sentimiento` queda en minúscula por compat backward).

### 4.5 Parámetros de la llamada DeepSeek

```python
{
  "model": "deepseek-v4-flash",        # V4 Flash, fast + cheap, ideal para structured output
  "temperature": 0.1,              # bajísima para determinismo
  "max_tokens": 2000,              # suficiente para 8 unidades
  "response_format": {"type": "json_object"},  # JSON mode garantizado
  "stream": false
}
```

---

## 5. Archivos modificados/creados

### 5.1 Nuevos

| Archivo | Propósito |
|---|---|
| `zoho-survey/scripts/lib/prompts_cualitativo.py` | **Los prompts exactos** (system + user + schema + few-shot). Fuente canónica. |
| `zoho-survey/scripts/lib/ia_cualitativo.py` | Cliente DeepSeek + caché + validación + función de alto nivel `generar_salidas_cualitativas_ia()`. |
| `zoho-survey/scripts/validar_ia_vs_manual.py` | Script de validación: compara salida IA vs `analisis_nps_cualitativo.xlsx`. Reporta accuracy, kappa, matriz de confusión, etc. |
| `docs/MIGRACION_IA_CUALITATIVO.md` | Este documento. |

### 5.2 Modificados

| Archivo | Cambio |
|---|---|
| `zoho-survey/scripts/lib/config.py` | + dimensión `"Espacios comunes": "Infraestructura"` (en PREGRADO y GRADUADO). + `DIMENSIONES_SIN_CSAT` (set de dimensiones catch-all sin pregunta CSAT directa). |
| `zoho-survey/scripts/build_json.py` | + branch IA antes del bloque cualitativo legacy. Si `DEEPSEEK_API_KEY` está → usa `generar_salidas_cualitativas_ia()`. Si no → cae al legacy (re-indentado bajo `if not _use_ia_cualitativo:`). Merge de columnas CSAT en `df_sent` para el cross-reference. |
| `requirements.txt` | + comentarios explicando la activación del modo IA (sin nuevas dependencias). |
| `.github/workflows/build_students.yml` | + step `Cache IA Cualitativo (DeepSeek)` para persistir `ia_cache.json`. + `env: DEEPSEEK_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}` en el step `Run build_json.py`. |

### 5.3 Playground Next.js (verificación interactiva)

En `/home/z/my-project/` (sandbox de desarrollo, NO parte del repo survey-storytelling):

| Archivo | Propósito |
|---|---|
| `src/lib/qualitative-prompts.ts` | Mirror TS de `prompts_cualitativo.py`. |
| `src/app/api/analyze/route.ts` | API route que llama a DeepSeek con los prompts. |
| `src/app/page.tsx` | UI del playground (formulario + panel de resultados + visor de prompts). |
| `src/components/qualitative/*.tsx` | `NpsSlider`, `CsatDimensionSelector`, `UnidadCard`, `PromptViewer`. |

El playground permite pegar tu API key de DeepSeek, cargar ejemplos calibrados, y ver la salida JSON visualizada antes de desplegar al pipeline.

---

## 6. Validación y métricas esperadas

### 6.1 Línea base (legacy vs manual)

Ejecutar (sin necesidad de API key):
```bash
python zoho-survey/scripts/validar_ia_vs_manual.py \
  --xlsx upload/analisis_nps_cualitativo.xlsx \
  --ia-json zoho-survey/students/undergraduate/2026-1/json/dataset_cualitativo.json \
  --output reporte_brecha_legacy_vs_manual.json
```

Resultado actual (encuesta 2026-1):
- Accuracy sentimiento: 59.7% | Kappa: 0.3357
- Accuracy taxonomía: 32.58% | Categoría padre: 50.05%
- Pendiente de Clasificación: 502 (legacy) vs 34 (manual)

### 6.2 Validación IA (con API key)

```bash
export DEEPSEEK_API_KEY=sk-...
python zoho-survey/scripts/validar_ia_vs_manual.py \
  --csv "data/ENCUESTA DE SATISFACCIÓN ESTUDIANTIL- PREGRADO - 2026-1.csv" \
  --xlsx upload/analisis_nps_cualitativo.xlsx \
  --output reporte_validacion_ia.json \
  --limit 100   # empezar con 100 comentarios para no gastar todo el crédito
```

### 6.3 Métricas objetivo

Con los prompts calibrados y `temperature=0.1`, se espera:

| Métrica | Legacy (actual) | Objetivo IA | Cómo medirlo |
|---|---|---|---|
| Accuracy sentimiento | 59.7% | **≥ 80%** | `validar_ia_vs_manual.py` |
| Cohen's Kappa | 0.3357 | **≥ 0.70** (sustancial) | `validar_ia_vs_manual.py` |
| Accuracy taxonomía | 32.58% | **≥ 70%** | `validar_ia_vs_manual.py` |
| Pendiente de Clasificación | 502 (21.8%) | **≤ 150 (6.5%)** | `validar_ia_vs_manual.py` |
| Regla NPS respetada | N/A | **100%** | `metricas_reglas_nps` en el reporte |
| Cross-reference CSAT | N/A | **≥ 90%** de unidades con dimensión evaluable | revisión manual del JSON |
| Costo por build | $0 (local) | **~$0.50** primer build, **~$0.05** builds con caché | `usage` en metadata |
| Tiempo de build | ~2 min | **~30 min** primer build, **~3 min** con caché | GitHub Actions log |

### 6.4 Validación 3 vías (legacy vs IA vs manual)

```bash
# Primero generar el JSON legacy (sin DEEPSEEK_API_KEY)
python zoho-survey/scripts/build_json.py
cp zoho-survey/students/undergraduate/2026-1/json/dataset_cualitativo.json \
   /tmp/dataset_cualitativo_legacy.json

# Luego generar el JSON IA (con DEEPSEEK_API_KEY)
export DEEPSEEK_API_KEY=sk-...
python zoho-survey/scripts/build_json.py

# Comparar los tres
python zoho-survey/scripts/validar_ia_vs_manual.py \
  --ia-json zoho-survey/students/undergraduate/2026-1/json/dataset_cualitativo.json \
  --legacy-json /tmp/dataset_cualitativo_legacy.json \
  --xlsx upload/analisis_nps_cualitativo.xlsx \
  --output reporte_3_vias.json
```

---

## 7. Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| DeepSeek API caída en build | Media | Build falla | Fallback automático al legacy (`IA_CUALITATIVO_FALLBACK=0` default). El pipeline nunca rompe por la API. |
| Rate limit (429) | Media | Build lento | Backoff exponencial + rate limit configurable (`IA_CUALITATIVO_MAX_RPM=50`). 924 comentarios @ 50 RPM = ~18 min. |
| Costo inesperado | Baja | Presupuesto | Caché persistente por hash(comentario+contexto). Builds subsiguientes solo procesan comentarios nuevos/cambiados. Monitorear `usage` en metadata del JSON. |
| Alucinación de dimensiones | Media | Datos sucios | Prohibición explícita en prompt + validación post-LLM (`_validar_unidad` rechaza dimensiones fuera de la taxonomía). |
| Inconsistencia prompt Python vs TS | Baja | Playground ≠ pipeline | Mirror manual. TODO: generar el TS desde el Python automáticamente (script codegen). |
| Cambio de modelo DeepSeek | Baja | Resultados diferentes | `model` se fija en `deepseek-v4-flash`. Si DeepSeek depreca el modelo, actualizar `DEFAULT_MODEL` y re-validar. |
| Comentario > 100 chars | Baja (Zoho limita) | Token overflow | `max_tokens=2000` en la respuesta. El system prompt soporta comentarios largos; el few-shot usa ejemplos de ≤100 chars como la encuesta real. |

---

## 8. Próximos pasos sugeridos

1. **Probar el playground** (`/home/z/my-project/`, ver Preview Panel): pega tu API key, carga los 3 ejemplos, verifica que la salida se ve coherente. Ajusta el prompt si encuentras casos patológicos.

2. **Validar con 100 comentarios**: ejecuta `validar_ia_vs_manual.py --limit 100` con tu key. Revisa el reporte: si accuracy sentimiento < 70%, ajusta los few-shot examples en `prompts_cualitativo.py`.

3. **Validación completa (924 comentarios)**: cuando el reporte de 100 comentarios sea satisfactorio, ejecuta sin `--limit`. Costo estimado: ~$0.50.

4. **Configurar el GitHub Secret** `DEEPSEEK_API_KEY` y hacer un push de prueba a una rama. Verificar que el workflow completa y los JSON generados tienen `motor: "deepseek"` en metadata.

5. **Actualizar el frontend** (`dashboard.js`) para consumir los campos nuevos: `es_valido`, `motivo_invalidez`, `es_mencion_mejora`, `es_salvavidas`, `dimension_evaluada_rating`. Sugerencia: añadir un filtro "Solo válidos" y un badge "Salvavidas" en las tarjetas de comentarios.

6. **Considerar batching futuro**: si el costo o tiempo son problema, se puede procesar N comentarios por llamada API (en lugar de 1). Requiere pasar N contextos CSAT en el user prompt y devolver N listas de unidades. No recomendado para v1 (complejidad vs ahorro marginal).

---

## 9. Referencias

- Bardin, L. (2011). *Análisis de contenido*. Ediciones Akal.
- Braun, V., & Clarke, V. (2006). Using thematic analysis in psychology. *Qualitative Research in Psychology*, 3(2), 77-101.
- Landis, J. R., & Koch, G. G. (1977). The measurement of observer agreement for categorical data. *Biometrics*, 33(1), 159-174.
- Reichheld, F. F. (2003). The One Number You Need to Grow. *Harvard Business Review*.
- DeepSeek API documentation: https://api-docs.deepseek.com/
