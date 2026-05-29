import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';

import type { PeriodInfo } from '@survey-storytelling/shared-types';

async function fetchPeriods(): Promise<{ periods: PeriodInfo[]; levels: string[] }> {
  const response = await fetch('/api/surveys/periods');
  if (!response.ok) {
    throw new Error('Failed to fetch periods');
  }
  return response.json();
}

export function SurveyListPage() {
  const navigate = useNavigate();
  const { data, isLoading, error } = useQuery({
    queryKey: ['periods'],
    queryFn: fetchPeriods,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-4 border-ulima-orange border-t-transparent rounded-full mx-auto" />
          <p className="mt-4 text-gray-600">Cargando encuestas...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center max-w-md">
          <div className="text-4xl mb-4">⚠️</div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Error al cargar</h2>
          <p className="text-gray-600 mb-4">
            No se pudieron cargar los periodos. Verifica que el backend esté corriendo.
          </p>
          <p className="text-sm text-gray-500">
            Usa <code className="bg-gray-100 px-1 rounded">pnpm dev</code> para iniciar el backend.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-12">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Encuestas de Satisfacción</h1>
        <p className="mt-2 text-gray-600">
          Selecciona un periodo para ver los resultados.
        </p>
      </div>

      {data?.levels.map((level) => (
        <section key={level} className="mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4 capitalize">
            {level === 'undergraduate' ? 'Pregrado' : 'Posgrado'}
          </h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {data.periods
              .filter((p) => p.id.startsWith(level === 'undergraduate' ? '20' : 'pg-'))
              .map((period) => (
                <button
                  key={period.id}
                  onClick={() => navigate(`/${level}/${period.id}`)}
                  className="relative text-left p-4 rounded-lg border border-gray-200 bg-white hover:border-ulima-orange hover:shadow-md transition-all group"
                >
                  {period.isNew && (
                    <span className="absolute -top-2 -right-2 bg-green-500 text-white text-xs px-2 py-0.5 rounded-full">
                      Nuevo
                    </span>
                  )}
                  <h3 className="font-semibold text-gray-900 group-hover:text-ulima-orange transition-colors">
                    {period.label}
                  </h3>
                  <p className="text-sm text-gray-500 mt-1">
                    Ver resultados →
                  </p>
                </button>
              ))}
          </div>
        </section>
      ))}
    </div>
  );
}
