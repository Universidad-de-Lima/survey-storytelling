import { SurveyRepository } from '@/modules/surveys/survey.repository';
import type {
  DashboardData,
  DimensionRow,
  FilterOptions,
  ResponseCount,
  NpsCrossRow,
  CsatCrossRow,
  SentimentData,
  PeriodInfo,
} from '@survey-storytelling/shared-types';

export class SurveyService {
  private repository: SurveyRepository;

  constructor() {
    this.repository = new SurveyRepository();
  }

  async getAllPeriods(): Promise<{ periods: PeriodInfo[]; levels: string[] }> {
    const levels = ['undergraduate', 'postgraduate'] as const;
    const allPeriods: PeriodInfo[] = [];

    for (const level of levels) {
      try {
        const periods = await this.repository.getPeriods(level);
        allPeriods.push(...periods);
      } catch {
        // Level may not have data yet (e.g., postgraduate)
        continue;
      }
    }

    return {
      periods: allPeriods,
      levels: [...levels],
    };
  }

  async getDashboardData(level: string, period: string): Promise<DashboardData> {
    const data = await this.repository.readJson<DashboardData>(
      level,
      period,
      'dashboard_data.json',
    );
    if (!data) {
      throw new Error(`Dashboard data not found for ${level}/${period}`);
    }
    return data;
  }

  async getDimensions(level: string, period: string): Promise<DimensionRow[]> {
    const data = await this.repository.readJson<DimensionRow[]>(level, period, 'dimensiones.json');
    if (!data || !Array.isArray(data)) {
      throw new Error(`Dimensions not found for ${level}/${period}`);
    }
    return data;
  }

  async getFilters(level: string, period: string): Promise<FilterOptions> {
    const data = await this.repository.readJson<FilterOptions>(level, period, 'filtros.json');
    if (!data) {
      throw new Error(`Filters not found for ${level}/${period}`);
    }
    return data;
  }

  async getSentiment(level: string, period: string): Promise<SentimentData> {
    const data = await this.repository.readJson<SentimentData>(level, period, 'sentimiento.json');
    if (!data) {
      throw new Error(`Sentiment data not found for ${level}/${period}`);
    }
    return data;
  }

  async getResponseCounts(level: string, period: string): Promise<ResponseCount[]> {
    const data = await this.repository.readJson<ResponseCount[]>(level, period, 'ids.json');
    if (!data || !Array.isArray(data)) {
      throw new Error(`Response counts not found for ${level}/${period}`);
    }
    return data;
  }

  async getNpsCross(level: string, period: string): Promise<NpsCrossRow[]> {
    const data = await this.repository.readJson<NpsCrossRow[]>(
      level,
      period,
      'nps_ciclo_carrera.json',
    );
    if (!data || !Array.isArray(data)) {
      throw new Error(`NPS cross data not found for ${level}/${period}`);
    }
    return data;
  }

  async getCsatCross(level: string, period: string): Promise<CsatCrossRow[]> {
    const data = await this.repository.readJson<CsatCrossRow[]>(
      level,
      period,
      'csat_ciclo_carrera.json',
    );
    if (!data || !Array.isArray(data)) {
      throw new Error(`CSAT cross data not found for ${level}/${period}`);
    }
    return data;
  }
}
