# Investigación — Periodo 2025-2 con 0 análisis cualitativos

> **Fecha**: 2026-07-10
> **Estado**: Investigación estática completada. Fix requerido en Fase 2 o 3.
> **Alcance**: Análisis del problema reportado en CC-01 del plan de mejora.

## 1. Síntoma observado

El periodo `undergraduate/2025-2` tiene `total_analizados: 0` y `comentarios_invalidos: 3998` en `sentimiento.json`. La sección Cualitativo del dashboard 2025-2 se muestra vacía.

## 2. Evidencia verificada directamente

### 2.1 Análisis del CSV fuente (`data/ENCUESTA DE SATISFACCIÓN ESTUDIANTIL- PREGRADO - 2025-2.csv`)

| Métrica | Valor |
|---|---|
| Total de filas | 3998 |
| Columna de comentario (índice 43) | "Explica con tus palabras, las razones de la calificación que diste en la pregunt..." |
| Filas con comentario vacío | **3998 (100%)** |
| Filas con comentario con texto | **0 (0%)** |

**Conclusión**: El CSV de 2025-2 **no contiene ningún comentario** en la pregunta abierta NPS. Todos los encuestados dejaron la pregunta opcional sin responder.

### 2.2 Análisis del JSON generado (`sentimiento.json` de 2025-2)

```json
{
  "total_respuestas": 3998,
  "total_con_comentario": 3998,
  "total_analizados": 0,
  "comentarios_invalidos": 3998
}
```

**Inconsistencia detectada**: `total_con_comentario` reporta 3998 (100% del total) pero en realidad son 0 (todos los comentarios están vacíos).

### 2.3 Comparación con 2026-1

| Métrica | 2025-2 | 2026-1 |
|---|---|---|
| Total filas en CSV | 3998 | 4239 |
| Comentarios con texto en CSV | **0** | (no verificado, pero hay análisis) |
| `total_respuestas` en JSON | 3998 | **1009** ⚠️ |
| `total_con_comentario` en JSON | 3998 | 1009 |
| `total_analizados` en JSON | 0 | 1733 |
| `comentarios_invalidos` en JSON | 3998 | 138 |

**Discrepancia adicional**: `total_respuestas` de 2026-1 reporta 1009 pero el CSV tiene 4239 filas. Esto sugiere que el contador `total_respuestas` no cuenta todas las filas del CSV.

### 2.4 Diferencia estructural entre CSVs 2025-2 y 2026-1

Ambos CSVs tienen 44 columnas, pero hay 1 diferencia en el nombre de la columna 20:
- 2025-2: `"Información sobre tu récord académico"`
- 2026-1: `"La información sobre tu récord académico"`

Esta diferencia puede afectar el mapeo en `COLUMN_RENAME_PREGRADO` si la entrada espera un nombre exacto.

## 3. Causa raíz identificada

El problema tiene **2 componentes**:

### 3.1 Bug en detección de comentarios vacíos (causa principal de 2025-2)

El ETL cuenta respuestas vacías como "comentarios con texto". El contador `total_con_comentario` debería ser 0 para 2025-2 (ningún comentario tiene texto), pero reporta 3998.

**Hipótesis**: En `build_json.py`, el cálculo de `total_con_comentario` no filtra correctamente las celdas vacías o NaN. Posibles causas:
- `df["comentario"].count()` cuenta celdas no-NaN, incluyendo strings vacíos `""`.
- No hay filtro `df["comentario"].str.strip() != ""` antes de contar.
- Los NaN de pandas se convierten a string `"nan"` y no se filtran.

Luego, el motor IA recibe 3998 comentarios vacíos, los marca como inválidos (porque no tienen texto), y reporta `comentarios_invalidos: 3998`.

### 3.2 Discrepancia en `total_respuestas` de 2026-1 (bug secundario)

`total_respuestas` de 2026-1 es 1009 pero el CSV tiene 4239 filas. Esto sugiere que:
- O bien `total_respuestas` cuenta solo filas que pasaron algún filtro (e.g., NPS válido).
- O bien hay un bug en el cálculo.

Este bug no bloquea el dashboard (2026-1 funciona), pero los números no cuadran con el CSV.

### 3.3 Diferencia en nombre de columna 20 (riesgo futuro)

La columna 20 cambió de nombre entre 2025-2 y 2026-1. Si `COLUMN_RENAME_PREGRADO` en `config.py` espera un nombre exacto, el mapeo de esa dimensión puede fallar en uno de los dos periodos. Esto no afecta al análisis cualitativo (que usa la columna de comentario, no la 20), pero puede afectar a las dimensiones CSAT.

## 4. Recomendación de fix

### 4.1 Fix inmediato (Fase 2 o 3)

Corregir la detección de comentarios vacíos en `build_json.py`:

1. **Identificar dónde se calcula `total_con_comentario`**: buscar en `build_json.py` la línea que asigna este valor al JSON.
2. **Aplicar filtro correcto**:
   - `total_respuestas` = total de filas en el CSV (sin contar header).
   - `total_con_comentario` = filas donde la columna de comentario tiene texto no vacío (no NaN, no `""`, no solo espacios, no `"nan"` string).
   - `total_analizados` = comentarios que pasaron el filtro de ruido y la IA procesó.
   - `comentarios_invalidos` = comentarios con texto que la IA marcó como inválidos.
3. **Verificar**: tras el fix, 2025-2 debe reportar `total_con_comentario: 0` y la sección Cualitativo debe ocultarse (no mostrar "0 comentarios analizados").

### 4.2 Fix de `total_respuestas` (Fase 2 o 3)

Investigar por qué `total_respuestas` de 2026-1 es 1009 en lugar de 4239. Posibles causas:
- Se cuenta solo filas con NPS válido (no NaN).
- Se cuenta solo filas con carrera válida.
- Hay un filtro que reduce el total antes de contar.

### 4.3 Fix de mapeo de columna 20 (Fase 3 con ARQ-03)

Cuando se externalicen los catálogos a JSON (ARQ-03), manejar variaciones de nombres de columnas (e.g., "Información sobre..." vs "La información sobre..."). Opciones:
- Normalizar nombres en el script de sanitización antes del ETL.
- Añadir alias en `COLUMN_RENAME_PREGRADO`.
- Hacer el mapeo case-insensitive y sin artículos ("el", "la").

### 4.4 Frontend (Fase 2 o 3)

Cuando `total_con_comentario = 0`, el dashboard debe:
- Ocultar la sección Cualitativo con mensaje "Esta encuesta no incluyó comentarios abiertos" o "No hubo comentarios en este periodo".
- No mostrar "0 comentarios analizados" (que sugiere error).

## 5. Validación requerida tras el fix

1. Regenerar JSONs de 2025-2 y verificar:
   - `total_con_comentario: 0`
   - `comentarios_invalidos: 0`
   - `total_analizados: 0`
   - Sección Cualitativo oculta en dashboard.
2. Regenerar JSONs de 2026-1 y verificar:
   - `total_con_comentario` refleja correctamente el número de respuestas con texto.
   - `total_respuestas` refleja correctamente el total de filas.
3. Regenerar JSONs de graduate/2026 y verificar consistencia.

## 6. Notas operativas

- **No requiere re-procesamiento con DeepSeek**: Como 2025-2 no tiene comentarios, no hay llamadas a la API. El fix es puramente en el cálculo de contadores.
- **Coherente con la indicación del usuario**: "No todos los CSVs tienen datos en la pregunta abierta ya que es libre y los encuestados pueden llenar o no la respuesta." Esto confirma que `total_con_comentario` puede ser legítimamente 0 o menor que `total_respuestas`.
- **No se aplica fix en Fase 1**: El fix requiere modificar `build_json.py` en el área de cálculo de métricas, que se refactoriza en Fase 3 (ARQ-02). Aplicar el fix en Fase 2 (investigación) o Fase 3 (refactor) para no mezclar con quick wins.

## 7. Conclusión

La causa raíz de 2025-2 es un **bug en la detección de comentarios vacíos** en `build_json.py`. El CSV legítimamente no tiene comentarios (todos los encuestados dejaron la pregunta opcional sin responder), pero el ETL los cuenta como "comentarios con texto" y luego los marca como inválidos.

El fix es de complejidad media (modificar el cálculo de `total_con_comentario` en `build_json.py`) y se pospone a Fase 2 o 3 para no mezclar con los quick wins de Fase 1.
