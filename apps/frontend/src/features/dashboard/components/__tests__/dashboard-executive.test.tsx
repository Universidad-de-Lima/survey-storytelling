import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';

import { DashboardExecutive } from '@/features/dashboard/components/dashboard-executive';
import type { DashboardData } from '@survey-storytelling/shared-types';

const mockData: DashboardData = {
  resumen: {
    año: '2026-1',
    encuestas: 1250,
    fecha_inicio: '2026-03-01',
    fecha_fin: '2026-04-30',
    nps: { score: 65.4 },
    csat: { score: 92.1 },
  },
  hallazgos: {
    csat_pct: 92.1,
    nps_score: 65.4,
    nps_tipo: 'Excelente',
    nps_etapas: '3',
    tendencia: 'up',
    delta: 5.2,
  },
  nps: {
    Promotores: 55,
    Pasivos: 25,
    Detractores: 20,
  },
  csat: {
    'Totalmente satisfecho': 45,
    'Muy satisfecho': 30,
    'Satisfecho': 17.1,
    'Insatisfecho': 5,
    'Totalmente insatisfecho': 2.9,
  },
};

describe('DashboardExecutive', () => {
  it('renders the NPS KPI card', () => {
    render(<DashboardExecutive data={mockData} />);
    expect(screen.getByText('NPS')).toBeInTheDocument();
    expect(screen.getByText('65.4')).toBeInTheDocument();
  });

  it('renders the CSAT KPI card', () => {
    render(<DashboardExecutive data={mockData} />);
    expect(screen.getByText('CSAT')).toBeInTheDocument();
    expect(screen.getByText('92.1')).toBeInTheDocument();
  });

  it('renders the period information', () => {
    render(<DashboardExecutive data={mockData} />);
    expect(screen.getByText('2026-1')).toBeInTheDocument();
    expect(screen.getByText('2026-03-01')).toBeInTheDocument();
    expect(screen.getByText('2026-04-30')).toBeInTheDocument();
  });

  it('renders NPS distribution sections', () => {
    render(<DashboardExecutive data={mockData} />);
    expect(screen.getByText(/Promotores/)).toBeInTheDocument();
    expect(screen.getByText(/Pasivos/)).toBeInTheDocument();
    expect(screen.getByText(/Detractores/)).toBeInTheDocument();
  });

  it('renders CSAT distribution labels', () => {
    render(<DashboardExecutive data={mockData} />);
    expect(screen.getByText('Totalmente satisfecho')).toBeInTheDocument();
    expect(screen.getByText('Muy satisfecho')).toBeInTheDocument();
  });
});
