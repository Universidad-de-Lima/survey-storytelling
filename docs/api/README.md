# API Documentation

## Base URL

- Development: `http://localhost:3000/api`
- Production: Configurable via `VITE_API_URL`

## Endpoints

### Health Check

```
GET /api/health
```

Returns server status.

### Periods

```
GET /api/surveys/periods
```

Returns all available periods grouped by level.

**Response:**
```json
{
  "success": true,
  "data": {
    "periods": [
      { "id": "2026-1", "label": "Periodo 2026-1", "isNew": true },
      { "id": "2025-2", "label": "Periodo 2025-2", "isNew": false }
    ],
    "levels": ["undergraduate", "postgraduate"]
  }
}
```

### Dashboard Data

```
GET /api/surveys/:level/:period/dashboard
```

**Parameters:**
- `level`: `undergraduate` | `postgraduate`
- `period`: `YYYY-S` (e.g., `2026-1`)

**Response:** `DashboardData` object with KPIs, distributions, and findings.

### Dimensions

```
GET /api/surveys/:level/:period/dimensions
```

Returns satisfaction data per faculty/career/cycle/dimension.

### Filters

```
GET /api/surveys/:level/:period/filters
```

Returns filter options: faculties, careers, cycles, and faculty→career mapping.

### Sentiment

```
GET /api/surveys/:level/:period/sentiment
```

Returns topic-based sentiment analysis of NPS comments.

### Response Counts

```
GET /api/surveys/:level/:period/ids
```

Returns response counts per faculty/career/cycle.

### NPS Cross

```
GET /api/surveys/:level/:period/nps-cross
```

Returns NPS scores cross-tabulated by career and cycle.

### CSAT Cross

```
GET /api/surveys/:level/:period/csat-cross
```

Returns CSAT scores cross-tabulated by career and cycle.
