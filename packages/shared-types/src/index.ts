// ============================================================================
// Survey Storytelling — Shared Types
// ============================================================================
// These types define the data contracts between the ETL pipeline (Python),
// the backend API (Fastify), and the frontend (React).
// They mirror the JSON schemas documented in JSON_SCHEMA.md
// ============================================================================

// ─── Period ─────────────────────────────────────────────────────────────────

export interface PeriodInfo {
  id: string;
  label: string;
  isNew: boolean;
}

// ─── Dashboard Data ─────────────────────────────────────────────────────────

export interface DashboardData {
  resumen: SurveySummary;
  hallazgos: Findings;
  nps: NpsDistribution;
  csat: CsatDistribution;
}

export interface SurveySummary {
  año: string;
  encuestas: number;
  fecha_inicio: string;
  fecha_fin: string;
  nps: { score: number };
  csat: { score: number };
}

export interface Findings {
  csat_pct: number;
  nps_score: number;
  nps_tipo: 'Excelente' | 'Bueno' | 'Regular' | 'Malo';
  nps_etapas: string;
  tendencia: 'up' | 'down' | 'stable';
  delta: number;
}

export interface NpsDistribution {
  Promotores: number;
  Pasivos: number;
  Detractores: number;
}

export interface CsatDistribution {
  'Totalmente satisfecho': number;
  'Muy satisfecho': number;
  'Satisfecho': number;
  'Insatisfecho': number;
  'Totalmente insatisfecho': number;
}

// ─── Dimension ──────────────────────────────────────────────────────────────

export interface DimensionRow {
  facultad: string;
  carrera: string;
  ciclo: string;
  categoria: string;
  dimension: string;
  t3b: number;
  b2b: number;
  total: number;
  t3b_pct: number;
  no_utilizo: number;
  no_conozco: number;
  'Totalmente satisfecho': number;
  'Muy satisfecho': number;
  'Satisfecho': number;
  'Insatisfecho': number;
  'Totalmente insatisfecho': number;
  'No utilizo': number;
  'No conozco': number;
}

// ─── Filters ────────────────────────────────────────────────────────────────

export interface FilterOptions {
  facultades: string[];
  carreras: string[];
  ciclos: string[];
  facultad_carrera: Record<string, string[]>;
}

// ─── Response Counts ────────────────────────────────────────────────────────

export interface ResponseCount {
  facultad: string;
  carrera: string;
  ciclo: string;
  count: number;
}

// ─── NPS/CSAT Cross Tables ─────────────────────────────────────────────────

export interface NpsCrossRow {
  facultad: string;
  carrera: string;
  ciclo: string;
  Promotores: number;
  Pasivos: number;
  Detractores: number;
}

export interface CsatCrossRow {
  facultad: string;
  carrera: string;
  ciclo: string;
  'Totalmente satisfecho': number;
  'Muy satisfecho': number;
  'Satisfecho': number;
  'Insatisfecho': number;
  'Totalmente insatisfecho': number;
}

// ─── Sentiment ──────────────────────────────────────────────────────────────

export interface SentimentData {
  resumen: SentimentSummary;
  topicos: Topic[];
  por_carrera: Record<string, TopicCareerBreakdown>;
  por_ciclo: Record<string, TopicCycleBreakdown>;
}

export interface SentimentSummary {
  total_con_comentario: number;
  total_analizados: number;
  pasivos: number;
  detractores: number;
  nota: string;
}

export interface Topic {
  topico: string;
  tipo: 'negativo' | 'mejora' | 'positivo';
  icono: string;
  total_comentarios: number;
  por_facultad: Record<string, number>;
  por_carrera: Record<string, number>;
  por_ciclo: Record<string, number>;
  frases_representativas: string[];
}

export interface TopicCareerBreakdown {
  [topic: string]: number;
}

export interface TopicCycleBreakdown {
  [topic: string]: number;
}

// ─── Filter State ───────────────────────────────────────────────────────────

export type FilterSuffix = 'top3' | 'radar' | 'preguntas' | 'detalle' | 'visibilidad' | 'sent';

export interface FilterState {
  facultad: string | null;
  carrera: string | null;
  ciclo: string | string[] | null;
}

export type FilterGroup = Record<FilterSuffix, FilterState>;

// ─── API Responses ──────────────────────────────────────────────────────────

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  meta?: {
    period: string;
    level: 'undergraduate' | 'postgraduate';
    timestamp: string;
  };
}

export interface PeriodListResponse {
  periods: PeriodInfo[];
  current: string;
}

// ─── Constants ──────────────────────────────────────────────────────────────

export const SATISFACTION_KEYS = [
  'Totalmente satisfecho',
  'Muy satisfecho',
  'Satisfecho',
  'Insatisfecho',
  'Totalmente insatisfecho',
] as const;

export const NPS_THRESHOLDS = {
  PROMOTOR_MIN: 9,
  PASIVO_MIN: 7,
  DETRACTOR_MAX: 6,
} as const;

export const META_NPS = 50;
export const META_CSAT = 93;
