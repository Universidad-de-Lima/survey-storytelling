import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock repository
vi.mock('@/modules/surveys/survey.repository', () => ({
  SurveyRepository: vi.fn().mockImplementation(() => ({
    getPeriods: vi.fn(),
    readJson: vi.fn(),
  })),
}));

describe('SurveyService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns periods from repository', async () => {
    const { SurveyRepository } = await import('@/modules/surveys/survey.repository');
    const { SurveyService } = await import('@/modules/surveys/survey.service');

    const mockPeriods = [
      { id: '2026-1', label: 'Periodo 2026-1', isNew: true },
      { id: '2025-2', label: 'Periodo 2025-2', isNew: false },
    ];

    vi.mocked(SurveyRepository).prototype.getPeriods.mockResolvedValue(mockPeriods);

    const service = new SurveyService();
    const result = await service.getAllPeriods();

    expect(result.periods).toHaveLength(2);
    expect(result.levels).toContain('undergraduate');
    expect(result.levels).toContain('postgraduate');
  });

  it('handles levels without data gracefully', async () => {
    const { SurveyRepository } = await import('@/modules/surveys/survey.repository');
    const { SurveyService } = await import('@/modules/surveys/survey.service');

    // Postgraduate throws, undergraduate returns data
    vi.mocked(SurveyRepository).prototype.getPeriods
      .mockResolvedValueOnce([{ id: '2026-1', label: 'Periodo 2026-1', isNew: true }])
      .mockRejectedValueOnce(new Error('Not found'));

    const service = new SurveyService();
    const result = await service.getAllPeriods();

    expect(result.periods).toHaveLength(1);
  });
});
