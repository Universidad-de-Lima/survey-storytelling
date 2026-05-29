# infrastructure

Configuración de infraestructura para despliegue del sistema: Docker, Nginx y orquestación.

## Purpose

Proveer configuraciones listas para producción del frontend y backend empaquetados en contenedores Docker, con Nginx como reverse proxy.

## Architecture Role

Capa de despliegue. Permite ejecutar el sistema completo (frontend + backend) en cualquier entorno con Docker, sin dependencias de plataforma.

## Files

| File | Description |
|------|-------------|
| `docker-compose.yml` | Orquestación de servicios (backend + frontend) |
| `Dockerfile.backend` | Multi-stage build para Fastify API |
| `Dockerfile.frontend` | Build Vite + Nginx static serving |
| `nginx.conf` | Reverse proxy config con seguridad y caching |

## Services

### Backend

| Property | Value |
|----------|-------|
| Port | `3000` |
| Base image | `node:20-alpine` |
| Build | Multi-stage (deps → build → runner) |
| Healthcheck | `GET /api/health` |
| Data volume | `../zoho-survey:/app/data` |

### Frontend

| Property | Value |
|----------|-------|
| Port | `80` (mapped to `5173`) |
| Base image | `nginx:alpine` |
| Build | Multi-stage (deps → build → nginx) |
| Static files | Built Vite output served by Nginx |

## Nginx Config Highlights

- Security headers: X-Frame-Options, X-Content-Type-Options, CSP, Referrer-Policy
- Gzip compression for text assets
- Cache headers: 1 year for assets, 1 hour for data, no-cache for HTML
- SPA fallback (`try_files $uri /index.html`)
- CSP allows Google Fonts + self-hosted assets

## Usage

```bash
# Build and start all services
docker compose -f infrastructure/docker-compose.yml up --build

# Start in background
docker compose -f infrastructure/docker-compose.yml up -d

# Stop services
docker compose -f infrastructure/docker-compose.yml down
```

## Technical Debt

- No SSL/TLS termination (expected behind a reverse proxy like Cloudflare or AWS ALB).
- No healthcheck on frontend container (Nginx doesn't have a health endpoint).
- Environment variables are hardcoded in `docker-compose.yml`; should use `.env` file.

## AI Agent Notes

- The frontend Dockerfile expects `VITE_API_URL` build arg for API endpoint configuration.
- Backend data directory is mounted from the host `zoho-survey/` directory.
- For production, add `.env` support via `env_file` in docker-compose.
- The Nginx CSP must be updated if adding new external resources (analytics, fonts, etc.).
