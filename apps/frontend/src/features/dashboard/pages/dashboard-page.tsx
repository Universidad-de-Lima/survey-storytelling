import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';

import type { DashboardData } from '@survey-storytelling/shared-types';
import { DashboardExecutive } from '@/features/dashboard/components/dashboard-executive';

async function fetchDashboardData(level: string, period: string): Promise<DashboardData> {
  const response = await fetch(`/api/surveys/${level}/${period}/dashboard`);
  if (!response.ok) {
    throw new Error(`Failed to fetch dashboard data: ${response.statusText}`);
  }
  return response.json();
}

export function DashboardPage() {
  const { level, period } = useParams<{ level: string; period: string }>();

  if (!level || !period) {
    return (
      <div className="p-8 text-center">
        <p className="text-red-600">Periodo no especificado</p>
      </div>
    );
  }

  return <DashboardShell level={level} period={period} />;
}

function DashboardShell({ level, period }: { level: string; period: string }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard', level, period],
    queryFn: () => fetchDashboardData(level, period),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-4 border-ulima-orange border-t-transparent rounded-full mx-auto" />
          <p className="mt-4 text-gray-600">Cargando dashboard...</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center max-w-md">
          <div className="text-4xl mb-4">📊</div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Sin datos disponibles</h2>
          <p className="text-gray-600">
            No hay datos para el periodo {period}. Ejecuta el pipeline ETL para generar los JSON.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard — Periodo {period}</h1>
        <p className="text-sm text-gray-500 capitalize">
          {level === 'undergraduate' ? 'Pregrado' : 'Posgrado'}
        </p>
      </div>

      <DashboardExecutive data={data} />
    </div>
  );
}
