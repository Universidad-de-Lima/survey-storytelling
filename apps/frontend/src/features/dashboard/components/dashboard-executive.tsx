import type { DashboardData } from '@survey-storytelling/shared-types';
import { META_NPS, META_CSAT } from '@survey-storytelling/shared-types';
import { KpiCard } from '@survey-storytelling/ui';

interface DashboardExecutiveProps {
  data: DashboardData;
}

function getNpsVariant(nps: number): 'success' | 'warning' | 'danger' {
  if (nps >= META_NPS) return 'success';
  if (nps >= 0) return 'warning';
  return 'danger';
}

function getCsatVariant(csat: number): 'success' | 'warning' | 'danger' {
  if (csat >= META_CSAT) return 'success';
  if (csat >= 70) return 'warning';
  return 'danger';
}

export function DashboardExecutive({ data }: DashboardExecutiveProps) {
  const { resumen, hallazgos, nps, csat } = data;

  return (
    <section id="ejecutivo">
      {/* KPI Row */}
      <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        <KpiCard
          title="NPS"
          value={hallazgos.nps_score}
          meta={META_NPS}
          trend={hallazgos.tendencia}
          variant={getNpsVariant(hallazgos.nps_score)}
        />
        <KpiCard
          title="CSAT"
          value={hallazgos.csat_pct}
          suffix="%"
          meta={META_CSAT}
          variant={getCsatVariant(hallazgos.csat_pct)}
        />
        <KpiCard title="Tipo NPS" value={0} variant="primary" />
        <KpiCard title="Respuestas" value={resumen.encuestas} variant="primary" />
      </div>

      {/* Period Info */}
      <div className="grid gap-4 grid-cols-1 sm:grid-cols-3 mb-8">
        <div className="p-4 bg-white rounded-lg border">
          <span className="text-sm text-gray-500">Periodo</span>
          <p className="text-lg font-semibold">{resumen.año}</p>
        </div>
        <div className="p-4 bg-white rounded-lg border">
          <span className="text-sm text-gray-500">Inicio</span>
          <p className="text-lg font-semibold">{resumen.fecha_inicio}</p>
        </div>
        <div className="p-4 bg-white rounded-lg border">
          <span className="text-sm text-gray-500">Fin</span>
          <p className="text-lg font-semibold">{resumen.fecha_fin}</p>
        </div>
      </div>

      {/* NPS Distribution */}
      <div className="p-6 bg-white rounded-lg border mb-8">
        <h2 className="text-lg font-semibold mb-4">Distribución NPS</h2>
        <div className="flex gap-2 h-8 rounded-full overflow-hidden">
          <div
            className="bg-green-500 transition-all"
            style={{ width: `${nps.Promotores}%` }}
            title={`Promotores: ${nps.Promotores}%`}
          />
          <div
            className="bg-yellow-400 transition-all"
            style={{ width: `${nps.Pasivos}%` }}
            title={`Pasivos: ${nps.Pasivos}%`}
          />
          <div
            className="bg-red-500 transition-all"
            style={{ width: `${nps.Detractores}%` }}
            title={`Detractores: ${nps.Detractores}%`}
          />
        </div>
        <div className="flex justify-between mt-2 text-sm">
          <span className="text-green-700">Promotores: {nps.Promotores}%</span>
          <span className="text-yellow-700">Pasivos: {nps.Pasivos}%</span>
          <span className="text-red-700">Detractores: {nps.Detractores}%</span>
        </div>
      </div>

      {/* CSAT Distribution */}
      <div className="p-6 bg-white rounded-lg border mb-8">
        <h2 className="text-lg font-semibold mb-4">Distribución CSAT</h2>
        <div className="space-y-2">
          {(Object.entries(csat) as [string, number][]).map(([label, value]) => (
            <div key={label}>
              <div className="flex justify-between text-sm mb-1">
                <span>{label}</span>
                <span className="font-medium">{value}%</span>
              </div>
              <div className="h-4 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500 rounded-full transition-all"
                  style={{ width: `${value}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
