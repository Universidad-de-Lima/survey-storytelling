import type { FastifyInstance } from 'fastify';
import rateLimit from '@fastify/rate-limit';

import { env } from '@/config/env';

export async function registerRateLimit(app: FastifyInstance): Promise<void> {
  await app.register(rateLimit, {
    max: env.RATE_LIMIT_MAX,
    timeWindow: env.RATE_LIMIT_WINDOW_MS,
  });
}
