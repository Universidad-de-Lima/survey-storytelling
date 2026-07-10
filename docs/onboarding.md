# Onboarding — survey-storytelling

Guía para nuevos desarrolladores o analistas que necesitan entender y operar el sistema.

---

## ¿Qué es survey-storytelling?

Sistema de dashboards estáticos para visualizar encuestas de satisfacción de la **Universidad de Lima**. Toma archivos CSV exportados de Zoho Survey y los convierte en dashboards web interactivos, sin backend ni base de datos. Todo se despliega gratuitamente en GitHub Pages.

**No necesitas instalar nada en tu computadora.** Todo el procesamiento ocurre en GitHub Actions.

---

## Flujo de trabajo completo

```
1. Exportar CSV desde Zoho Survey
         ↓
2. (Opcional, recomendado) Sanitizar PII localmente:
   python zoho-survey/scripts/sanitize_csv_pii.py --all
   Redacta columnas Direccion IP, Agente Usuario, URL de la encuesta.
         ↓
3. Colocar CSV en la carpeta data/ del repositorio y hacer commit
   (data/ NO esta gitignored; los CSVs se commitean sanitizados)
         ↓
4. Hacer git push a main
         ↓
5. GitHub Actions ejecuta el pipeline automaticamente:   - Sanitiza PII de los CSVs (defensa en profundidad)
   - Ejecuta build_json.py (ETL)
   - Valida JSONs generados
   - Despliega a GitHub Pages
         ↓
6. El dashboard se actualiza en GitHub Pages (~3-5 min)
         ↓
7. Verificar en: https://universidad-de-lima.github.io/survey-storytelling/zoho-survey/
```

---

## ¿Dónde está cada cosa?

| Si necesitas... | Ve a... |
|---|---|
| Ver los dashboards | `zoho-survey/` en GitHub Pages |
| Agregar un nuevo periodo | `data/` → colocar CSV |
| Cambiar metas (NPS, CSAT) | `zoho-survey/shared/js/config/constants.js` |
| Cambiar cómo se clasifican los comentarios | `zoho-survey/scripts/config/alias_aspectos.json` |
| Ver si todo está bien | `zoho-survey/health.html` en GitHub Pages |
| Ver historial de cambios | `docs/CHANGELOG.md` |
| Entender la arquitectura | `ARCHITECTURE.md` |
| Entender los datos | `CONTRACTS.md` |
| Reglas para código | `AGENTS.md` |

---

## Roles y responsabilidades

| Rol | Qué hace | Frecuencia |
|---|---|---|
| **Analista / Dueño de encuesta** | Exporta CSV de Zoho Survey, lo coloca en `data/`, hace push | Por cada periodo nuevo (~2-4 veces/año) |
| **Desarrollador** | Mantiene el código (ETL, frontend), agrega features, corrige bugs | Según necesidad |
| **Revisor cualitativo** | Usa la skill `qualitative_research_synthesis` para validar clasificaciones dudosas | Mensual (opcional) |
| **GitHub Actions (bot)** | Ejecuta el pipeline, genera JSONs, despliega | Automático en cada push |

---

## Troubleshooting común

### 1. "El dashboard no muestra el nuevo periodo"

**Causa probable**: El CSV no tiene el nombre correcto.
**Solución**: El archivo debe contener el patrón `ENCUESTA` y el periodo (`2026-1`, `2026`). Ej: `ENCUESTA DE SATISFACCIÓN ESTUDIANTIL- PREGRADO - 2026-1.csv`.

### 2. "El build falló en GitHub Actions"

**Causa probable**: Columnas faltantes en el CSV.
**Solución**: Verificar que el CSV tenga las columnas requeridas: `ID de respuesta`, `Net Promoter Score (de un total de 10)`, `La Universidad de Lima`, y la columna de carrera correspondiente. Revisar logs del workflow para el error específico.

### 3. "La sección cualitativa no carga"

**Causa probable**: `sentimiento.json` no se generó.
**Solución**: Verificar que el CSV tenga la columna `Comentario NPS` con texto. Si está vacía, el análisis cualitativo se omite (comportamiento esperado).

### 4. "El health check muestra ❌"

**Causa probable**: JSONs no se generaron para algún periodo.
**Solución**: Ir a GitHub Actions → Build and Deploy Survey → Run workflow para forzar re-generación.

### 5. "Quiero volver a la versión anterior"

**Solución**: Ver sección "Rollback de Emergencia" en `docs/developer-guide.md`.

### 6. "La sección Cualitativo aparece vacía o con 0 comentarios"

**Causa probable**: La pregunta abierta NPS es **opcional**. No todos los encuestados responden.
**Solución**: Esto es comportamiento esperado cuando ning��n encuestado dejó comentario.
El dashboard debe ocultar la sección Cualitativo en lugar de mostrar "0 comentarios analizados".
Si la sección aparece con error, verificar que `sentimiento.json` existe y que
`total_con_comentario > 0` en el resumen.

---

## Comandos útiles (solo para referencia — todo corre en CI)

Estos comandos están documentados en `package.json`. No necesitas ejecutarlos localmente; GitHub Actions los ejecuta por ti.

```bash
# Generar JSONs desde CSVs
npm run build:json

# Validar estructura de JSONs
npm run validate:json

# Iniciar servidor local (para desarrollo)
npm start

# Ejecutar tests
npm run test:js
```

---

## Glosario

| Término | Significado |
|---|---|
| **NPS** | Net Promoter Score — mide lealtad (0-10). Promotores ≥9, Pasivos 7-8, Detractores ≤6 |
| **CSAT** | Customer Satisfaction — % de respuestas positivas (Top 3 Box) |
| **T2B / T3B** | Top 2 Box / Top 3 Box — agrupaciones de respuestas más positivas |
| **Meaning Unit** | Fragmento mínimo de un comentario que expresa una sola idea evaluable |
| **ETL** | Extract, Transform, Load — pipeline que convierte CSV en JSON |
| **IIFE** | Immediately Invoked Function Expression — patrón JS usado en todos los módulos |
| **Draft-07** | Versión del estándar JSON Schema usada para validar contratos |
