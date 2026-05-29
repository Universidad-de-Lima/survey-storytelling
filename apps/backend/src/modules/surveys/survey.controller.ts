import type { FastifyReply, FastifyRequest } from 'fastify';
import { z } from 'zod';

import { SurveyService } from '@/modules/surveys/survey.service';
import type { ApiResponse } from '@survey-storytelling/shared-types';

const periodParamsSchema = z.object({
  level: z.enum(['undergraduate', 'postgraduate']),
  period: z.string().regex(/^\d{4}-\d$/, 'Period must match YYYY-S format'),
});

export class SurveyController {
  private service: SurveyService;

  constructor() {
    this.service = new SurveyService();
  }

  async getPeriods(_request: FastifyRequest, reply: FastifyReply): Promise<void> {
    try {
      const data = await this.service.getAllPeriods();
      const response: ApiResponse<typeof data> = { success: true, data };
      reply.send(response);
    } catch (error) {
      reply.status(500).send({
        success: false,
        error: 'Failed to fetch periods',
      } satisfies ApiResponse<never>);
    }
  }

  async getDashboard(
    request: FastifyRequest<{ Params: { level: string; period: string } }>,
    reply: FastifyReply,
  ): Promise<void> {
    const params = periodParamsSchema.safeParse(request.params);

    if (!params.success) {
      return reply.status(400).send({
        success: false,
        error: 'Invalid parameters',
        details: params.error.flatten(),
      } satisfies ApiResponse<never>);
    }

    try {
      const data = await this.service.getDashboardData(params.data.level, params.data.period);
      const response: ApiResponse<typeof data> = { success: true, data };
      reply.send(response);
    } catch (error) {
      reply.status(404).send({
        success: false,
        error: `No dashboard data found for ${params.data.level}/${params.data.period}`,
      } satisfies ApiResponse<never>);
    }
  }

  async getDimensions(
    request: FastifyRequest<{ Params: { level: string; period: string } }>,
    reply: FastifyReply,
  ): Promise<void> {
    const params = periodParamsSchema.safeParse(request.params);
    if (!params.success) {
      return reply.status(400).send({ success: false, error: 'Invalid parameters' });
    }

    try {
      const data = await this.service.getDimensions(params.data.level, params.data.period);
      reply.send({ success: true, data });
    } catch {
      reply.status(404).send({ success: false, error: 'Dimensions not found' });
    }
  }

  async getFilters(
    request: FastifyRequest<{ Params: { level: string; period: string } }>,
    reply: FastifyReply,
  ): Promise<void> {
    const params = periodParamsSchema.safeParse(request.params);
    if (!params.success) {
      return reply.status(400).send({ success: false, error: 'Invalid parameters' });
    }

    try {
      const data = await this.service.getFilters(params.data.level, params.data.period);
      reply.send({ success: true, data });
    } catch {
      reply.status(404).send({ success: false, error: 'Filters not found' });
    }
  }

  async getSentiment(
    request: FastifyRequest<{ Params: { level: string; period: string } }>,
    reply: FastifyReply,
  ): Promise<void> {
    const params = periodParamsSchema.safeParse(request.params);
    if (!params.success) {
      return reply.status(400).send({ success: false, error: 'Invalid parameters' });
    }

    try {
      const data = await this.service.getSentiment(params.data.level, params.data.period);
      reply.send({ success: true, data });
    } catch {
      reply.status(404).send({ success: false, error: 'Sentiment data not found' });
    }
  }

  async getResponseCounts(
    request: FastifyRequest<{ Params: { level: string; period: string } }>,
    reply: FastifyReply,
  ): Promise<void> {
    const params = periodParamsSchema.safeParse(request.params);
    if (!params.success) {
      return reply.status(400).send({ success: false, error: 'Invalid parameters' });
    }

    try {
      const data = await this.service.getResponseCounts(params.data.level, params.data.period);
      reply.send({ success: true, data });
    } catch {
      reply.status(404).send({ success: false, error: 'Response counts not found' });
    }
  }

  async getNpsCross(
    request: FastifyRequest<{ Params: { level: string; period: string } }>,
    reply: FastifyReply,
  ): Promise<void> {
    const params = periodParamsSchema.safeParse(request.params);
    if (!params.success) {
      return reply.status(400).send({ success: false, error: 'Invalid parameters' });
    }

    try {
      const data = await this.service.getNpsCross(params.data.level, params.data.period);
      reply.send({ success: true, data });
    } catch {
      reply.status(404).send({ success: false, error: 'NPS cross data not found' });
    }
  }

  async getCsatCross(
    request: FastifyRequest<{ Params: { level: string; period: string } }>,
    reply: FastifyReply,
  ): Promise<void> {
    const params = periodParamsSchema.safeParse(request.params);
    if (!params.success) {
      return reply.status(400).send({ success: false, error: 'Invalid parameters' });
    }

    try {
      const data = await this.service.getCsatCross(params.data.level, params.data.period);
      reply.send({ success: true, data });
    } catch {
      reply.status(404).send({ success: false, error: 'CSAT cross data not found' });
    }
  }
}
