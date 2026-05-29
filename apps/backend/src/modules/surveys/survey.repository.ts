import fs from 'fs/promises';
import path from 'path';

import type { PeriodInfo } from '@survey-storytelling/shared-types';

const DATA_BASE_DIR = path.resolve(process.cwd(), '../../zoho-survey/students');

export class SurveyRepository {
  /**
   * Read and parse a JSON file from the survey data directory.
   * Falls back to the original zoho-survey/students/{level}/{period}/json/ path.
   */
  async readJson<T>(level: string, period: string, filename: string): Promise<T | null> {
    // Try legacy path first (zoho-survey/students/{level}/{period}/json/)
    const legacyPath = path.join(DATA_BASE_DIR, level, period, 'json', filename);

    try {
      const content = await fs.readFile(legacyPath, 'utf-8');
      return JSON.parse(content) as T;
    } catch {
      // Legacy path not found, try apps/frontend/public/data/ path
      const publicPath = path.resolve(
        process.cwd(),
        `../../apps/frontend/public/data/${level}/${period}/${filename}`,
      );
      try {
        const content = await fs.readFile(publicPath, 'utf-8');
        return JSON.parse(content) as T;
      } catch {
        return null;
      }
    }
  }

  /**
   * Get period list for a given level.
   */
  async getPeriods(level: string): Promise<PeriodInfo[]> {
    // Try legacy periodos.json path
    const legacyPath = path.join(DATA_BASE_DIR, level, 'periodos.json');

    try {
      const content = await fs.readFile(legacyPath, 'utf-8');
      const parsed = JSON.parse(content);

      // Handle both array format and { periods: [...] } format
      if (Array.isArray(parsed)) {
        return parsed;
      }
      if (parsed.periods && Array.isArray(parsed.periods)) {
        return parsed.periods;
      }
      return [];
    } catch {
      // Fallback: scan directory for periods
      const levelPath = path.join(DATA_BASE_DIR, level);
      try {
        const entries = await fs.readdir(levelPath, { withFileTypes: true });
        const periods = entries
          .filter((entry) => entry.isDirectory() && /^\d{4}-\d$/.test(entry.name))
          .map((entry) => ({
            id: entry.name,
            label: `Periodo ${entry.name}`,
            isNew: false,
          }));

        return periods.sort((a, b) => b.id.localeCompare(a.id));
      } catch {
        return [];
      }
    }
  }
}
