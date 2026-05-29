# packages/ui

Componentes React compartidos reutilizables entre features del frontend.

## Purpose

Proveer una biblioteca de componentes UI base con tipado estricto, siguiendo el diseño del dashboard (colores institucionales ULIMA, tipografía Roboto + Lusitana).

## Architecture Role

Capa de presentación base. Contiene componentes puramente visuales sin lógica de negocio. Consumido por `apps/frontend/` y potencialmente por otros frontends del monorepo.

## Components

| Component | Props          | Description                                                |
| --------- | -------------- | ---------------------------------------------------------- |
| `KpiCard` | `KpiCardProps` | Tarjeta KPI con valor, meta, tendencia y variante de color |

### KpiCard Props

```typescript
interface KpiCardProps {
  title: string; // KPI label
  value: number; // Current value
  suffix?: string; // Unit suffix (%, pts, etc.)
  meta?: number; // Target/goal value
  trend?: 'up' | 'down' | 'stable'; // Trend indicator
  variant?: 'primary' | 'success' | 'warning' | 'danger';
}
```

## Dependencies

- **Peer**: React 18, React DOM 18
- **Dev**: TypeScript, `@survey-storytelling/tsconfig`

## Usage

```tsx
import { KpiCard } from '@survey-storytelling/ui';

<KpiCard title="NPS" value={65.4} meta={50} trend="up" variant="success" />;
```

## AI Agent Notes

- Components use TailwindCSS classes (from the consumer app's setup).
- All components must have TypeScript interfaces for their props exported.
- Avoid adding business logic or data fetching here — those belong in feature modules.
- New components must be exported from `src/index.ts`.
