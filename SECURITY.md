# Security Policy — survey-storytelling

## Data Protection

This repository processes survey data from the **Universidad de Lima**. 
The following data types are handled:

| Type | Example | Status |
|---|---|---|
| **PII directa** | IP address, User Agent | 🟡 Sanitizada en CI (defensa en profundidad, CRIT-01). Política de ingesta requiere sanitización **pre-commit** (ver `docs/onboarding.md`): la sanitización en CI ocurre tras el push, por lo que un CSV no sanitizado podría quedar en el historial Git. |
| **PII cuasi-identificadora** | Free-text comments (comentarios NPS abiertos) | 🔴 En revisión. Los comentarios se envían a DeepSeek y `sentimiento.json` puede conservar `comentario_original`/`fragmento_original`. La caché IA (`ia_cache.json`) NO es un control de privacidad. Ver roadmap de mejora (IM-001/IM-002). |
| **Aggregated metrics** | NPS, CSAT scores | 🟢 No PII exposure |

## Reporting a Vulnerability

If you discover a PII exposure or security issue:

1. **Do not** open a public issue.
2. Contact the repository maintainer directly.
3. Or email: [survey-security@ulima.edu.pe]

## Runtime Security

- Zero runtime dependencies in production (static site on GitHub Pages).
- All processing happens in CI (GitHub Actions).
- CSV exports are sanitized against formula injection.
- HTML input is sanitized via `SurveySanitizer` (allowlist of 9 tags).

## Environment Variables

See `.env.example` for required environment variables.
