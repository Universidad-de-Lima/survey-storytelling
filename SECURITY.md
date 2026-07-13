# Security Policy — survey-storytelling

## Data Protection

This repository processes survey data from the **Universidad de Lima**. 
The following data types are handled:

| Type | Example | Status |
|---|---|---|
| **PII directa** | IP address, User Agent | 🟡 Mitigada (FM-003 + FM-016). `sanitize_csv_pii.py` soporta modo `--check` (FM-003) para uso como gate pre-push: retorna exit code 1 si detecta PII no redactada. La activación del gate en CI (`tests.yml`) está pendiente de aprobación de cambios en workflows (zona de exclusión Fase 1.7); la sanitización en `build_zoho_survey.yml` se preserva como defensa secundaria. Política de ingesta requiere sanitización **pre-commit** (ver `docs/onboarding.md`). |
| **PII cuasi-identificadora** | Free-text comments (comentarios NPS abiertos) | 🟡 Mitigada (FM-001 + FM-002). `sentimiento.json` ya NO publica `comentario_original`/`fragmento_original` (FM-001 — schema `additionalProperties: false`); solo publica `fragmento_mostrar` redactado con `enmascarar_pii`. Antes de enviar a DeepSeek, los comentarios se redactan con `enmascarar_pii` (FM-002 — capa pre-LLM; la capa post-LLM se mantiene como defensa en profundidad). La caché IA (`ia_cache.json`) NO es un control de privacidad. |
| **Aggregated metrics** | NPS, CSAT scores | 🟢 No PII exposure |

## Reporting a Vulnerability

If you discover a PII exposure or security issue:

1. **Do not** open a public issue.
2. Contact the repository maintainer directly.
3. Or email: [survey-security@ulima.edu.pe]

## Secrets Hygiene

- `.env` está listado en `.gitignore` (patrón exacto `.env`) — el archivo local con `DEEPSEEK_API_KEY` nunca debe commitearse (FM-016, cierre parcial de R21).
- `.env.example` se commitea como documentación de variables requeridas (no contiene secrets).
- Si `.env` fue commiteado históricamente, rotar `DEEPSEEK_API_KEY` inmediatamente y ejecutar `git filter-repo` (ver FM-004, Fase 2).
- Validación pendiente para Fase 1.6+: ejecutar `git log --all --full-history -- .env` para confirmar historial limpio.

## Runtime Security

- Zero runtime dependencies in production (static site on GitHub Pages).
- All processing happens in CI (GitHub Actions).
- CSV exports are sanitized against formula injection.
- HTML input is sanitized via `SurveySanitizer` (allowlist of 9 tags).

## Environment Variables

See `.env.example` for required environment variables.
