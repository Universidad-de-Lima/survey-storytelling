import { describe, it, expect, vi, beforeEach } from 'vitest';

import { SurveyRepository } from '@/modules/surveys/survey.repository';
import { SurveyService } from '@/modules/surveys/survey.service';

// Mock repository: replace module with factory
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
    const mockPeriods = [
      { id: '2026-1', label: 'Periodo 2026-1', isNew: true },
      { id: '2025-2', label: 'Periodo 2025-2', isNew: false },
    ];

    // Type assertion: vi.mock replaces getPeriods with vi.fn() at runtime
    (SurveyRepository.prototype.getPeriods as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockPeriods,
    );

    const service = new SurveyService();
    const result = await service.getAllPeriods();

    expect(result.periods).toHaveLength(2);
    expect(result.levels).toContain('undergraduate');
    expect(result.levels).toContain('postgraduate');
  });

  it('handles levels without data gracefully', async () => {
    const mockPeriods = [{ id: '2026-1', label: 'Periodo 2026-1', isNew: true }];

    // Type assertion for chained mock methods
    const mockGetPeriods = SurveyRepository.prototype.getPeriods as ReturnType<typeof vi.fn>;
    mockGetPeriods.mockResolvedValueOnce(mockPeriods).mockRejectedValueOnce(new Error('Not found'));

    const service = new SurveyService();
    const result = await service.getAllPeriods();

    expect(result.periods).toHaveLength(1);
  });
});
