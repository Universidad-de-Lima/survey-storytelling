import Fastify from 'fastify';
import helmet from '@fastify/helmet';

import { env } from '@/config/env';
import { registerCors } from '@/middleware/cors';
import { errorHandler } from '@/middleware/error-handler';
import { registerRateLimit } from '@/middleware/rate-limit';
import { surveyRoutes } from '@/modules/surveys/survey.routes';

export async function buildApp() {
  const app = Fastify({
    logger: env.LOG_LEVEL === 'debug',
  });

  // Security
  await app.register(helmet, {
    contentSecurityPolicy: false, // Disabled for static JSON serving
  });

  // Global error handler
  app.setErrorHandler(errorHandler(app));

  // Middleware
  await registerCors(app);
  await registerRateLimit(app);

  // Health check
  app.get('/api/health', async () => ({
    status: 'ok',
    timestamp: new Date().toISOString(),
    environment: env.NODE_ENV,
    version: '2.0.0',
  }));

  // Routes
  await app.register(surveyRoutes);

  return app;
}
