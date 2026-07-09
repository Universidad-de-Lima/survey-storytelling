# Security Policy — survey-storytelling

## Data Protection

This repository processes survey data from the **Universidad de Lima**. 
The following data types are handled:

| Type | Example | Status |
|---|---|---|
| **PII directa** | IP address, User Agent | 🟢 Sanitized (CRIT-01, 2026-07-09) |
| **PII cuasi-identificadora** | Free-text comments | 🟢 Managed via CI cache (`ia_cache.json`) |
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
