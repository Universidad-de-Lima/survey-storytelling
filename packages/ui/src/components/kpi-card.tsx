import React from 'react';

export interface KpiCardProps {
  title: string;
  value: number;
  suffix?: string;
  meta?: number;
  trend?: 'up' | 'down' | 'stable';
  variant?: 'primary' | 'success' | 'warning' | 'danger';
}

const variantStyles: Record<string, string> = {
  primary: 'border-l-4 border-blue-500 bg-blue-50',
  success: 'border-l-4 border-green-500 bg-green-50',
  warning: 'border-l-4 border-yellow-500 bg-yellow-50',
  danger: 'border-l-4 border-red-500 bg-red-50',
};

const trendIcons: Record<string, string> = {
  up: '↑',
  down: '↓',
  stable: '→',
};

export function KpiCard({
  title,
  value,
  suffix = '',
  meta,
  trend,
  variant = 'primary',
}: KpiCardProps) {
  const progress = meta ? Math.min(Math.round((value / meta) * 100), 100) : null;

  return (
    <div className={`rounded-lg p-4 shadow-sm ${variantStyles[variant]}`}>
      <div className="text-sm font-medium text-gray-600 truncate">{title}</div>
      <div className="mt-1 flex items-baseline gap-1">
        <span className="text-3xl font-bold text-gray-900">
          {typeof value === 'number' ? value.toFixed(1) : value}
        </span>
        {suffix && <span className="text-lg text-gray-500">{suffix}</span>}
        {trend && (
          <span
            className={`ml-2 text-sm ${
              trend === 'up'
                ? 'text-green-600'
                : trend === 'down'
                  ? 'text-red-600'
                  : 'text-gray-400'
            }`}
          >
            {trendIcons[trend]}
          </span>
        )}
      </div>
      {progress !== null && (
        <div className="mt-2">
          <div className="h-2 rounded-full bg-gray-200">
            <div
              className="h-2 rounded-full bg-blue-500 transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
          <div className="mt-0.5 text-xs text-gray-500">
            Meta: {meta}
            {suffix}
          </div>
        </div>
      )}
    </div>
  );
}
