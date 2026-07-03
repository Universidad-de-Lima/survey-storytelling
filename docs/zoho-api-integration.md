# Investigación: Integración con Zoho Survey API

Documento de viabilidad para automatizar la descarga de respuestas desde Zoho Survey,
eliminando la necesidad de exportar CSVs manualmente.

**Fecha**: 2026-07-03 | **Estado**: Investigación (no implementado)

---

## 1. Contexto actual

Hoy el flujo de ingesta es manual:
1. Usuario entra a Zoho Survey → exporta CSV.
2. Coloca el archivo en `data/` del repositorio.
3. Hace push → GitHub Actions procesa.

**Problema**: depende de una persona, propenso a errores de naming, y no escala a múltiples tipos de encuesta.

---

## 2. Zoho Survey API — Capacidades relevantes

Zoho Survey expone una API REST documentada en:
https://www.zoho.com/survey/api/v2/

### Endpoints clave

| Endpoint | Método | Descripción |
|---|---|---|
| `/api/v2/surveys` | GET | Listar todas las encuestas del usuario |
| `/api/v2/surveys/{surveyId}/responses` | GET | Obtener respuestas de una encuesta específica |
| `/api/v2/surveys/{surveyId}/responses/export` | GET | Exportar respuestas en formato CSV/JSON |

### Autenticación

Zoho usa **OAuth 2.0** con los siguientes flujos:
- **Authorization Code Grant**: para aplicaciones web (requiere redirect URI).
- **Client Credentials Grant**: para aplicaciones server-to-server (recomendado para CI).

Se requiere:
1. Registrar una "Self Client" en Zoho API Console (https://api-console.zoho.com/).
2. Generar `client_id` y `client_secret`.
3. Generar un **refresh token** (válido por tiempo indefinido mientras se use).
4. Intercambiar refresh token por access token (válido por 1 hora).

### Rate Limits

- Plan gratuito: ~250 requests/día.
- Plan profesional: ~1000 requests/día.
- Plan enterprise: ~2500 requests/día.

Para una encuesta con ~5000 respuestas, se necesitan aproximadamente 2-3 requests (list surveys + fetch responses + export).

---

## 3. Esfuerzo estimado de implementación

### Script `fetch_zoho.py` (~150 líneas)

```python
# Pseudocódigo de lo que se necesitaría implementar

def fetch_zoho_responses(survey_name: str, output_dir: Path):
    """
    1. Autenticar con Zoho OAuth2 (refresh_token → access_token)
    2. GET /api/v2/surveys → encontrar survey por nombre
    3. GET /api/v2/surveys/{id}/responses/export → descargar CSV
    4. Guardar en data/ con naming consistente
    """
```

### Tareas necesarias

| Tarea | Esfuerzo | Complejidad |
|---|---|---|
| Registrar app en Zoho API Console | 1h | Baja (pasos documentados) |
| Implementar OAuth2 flow (refresh token) | 3h | Media (urllib, manejo de expiración) |
| Implementar fetch de respuestas | 2h | Baja (endpoint simple) |
| Manejo de errores y reintentos | 2h | Media |
| Integrar en `build_students.yml` (step previo) | 1h | Baja |
| Tests unitarios | 2h | Media |
| Documentación | 1h | Baja |
| **Total estimado** | **~12h (2-3 días)** | |

### Dependencias nuevas

- **Ninguna**. Zoho API es REST estándar. Se puede implementar con `urllib` (stdlib).
- Se necesita `client_id`, `client_secret`, `refresh_token` como GitHub Secrets.

---

## 4. Riesgos y consideraciones

| Riesgo | Mitigación |
|---|---|
| **Refresh token expira** | Zoho refresh tokens no expiran si se usan regularmente. Si expiran, hay que re-generarlos manualmente. |
| **Cambios en la API de Zoho** | La API v2 es estable desde 2022. Monitorear changelog. |
| **Rate limiting** | Para ~10 encuestas/año, ~30 requests/año — muy por debajo del límite gratuito. |
| **Columnas cambian entre versiones de encuesta** | El mapeo ya se maneja en `config.py` (`COLUMN_RENAME_PREGRADO`, `COLUMN_RENAME_GRADUADO`). Seguiría igual. |

---

## 5. Recomendación

**Viabilidad: ALTA**. Esfuerzo bajo (~12h), sin nuevas dependencias, riesgo controlado.

**Prioridad sugerida**: Media-Baja. El flujo manual actual funciona para los 2 tipos de encuesta activos (undergraduate, graduate). La automatización se vuelve crítica cuando se activen los 7 tipos restantes y el volumen de CSVs crezca.

**Próximo paso recomendado**: Solicitar a Zoho las credenciales API (client_id, client_secret) como paso previo a cualquier desarrollo. Sin ellas, no se puede avanzar.

---

## 6. Alternativas consideradas

| Alternativa | Pros | Contras |
|---|---|---|
| **Zoho Webhooks** | Notificación automática al cerrar encuesta | Solo notifica, no envía datos. Requiere endpoint público (no compatible con Pages estático). |
| **Zoho Reports API** | Datos ya agregados | No expone respuestas individuales, no compatible con nuestro ETL. |
| **Google Sheets + Zoho integration** | Fácil para no-técnicos | Introduce otra herramienta, pierde trazabilidad git. |
| **Mantener flujo manual** | Ya funciona, sin cambios | No escala, propenso a errores humanos. |
