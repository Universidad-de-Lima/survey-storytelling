import type { FastifyInstance } from 'fastify';

import { SurveyController } from '@/modules/surveys/survey.controller';

export async function surveyRoutes(app: FastifyInstance): Promise<void> {
  const controller = new SurveyController();

  // GET /api/surveys/periods — List all available periods across levels
  app.get('/api/surveys/periods', controller.getPeriods.bind(controller));

  // GET /api/surveys/:level/:period/dashboard — Get dashboard data for a period
  app.get('/api/surveys/:level/:period/dashboard', controller.getDashboard.bind(controller));

  // GET /api/surveys/:level/:period/dimensions — Get dimension data
  app.get('/api/surveys/:level/:period/dimensions', controller.getDimensions.bind(controller));

  // GET /api/surveys/:level/:period/filters — Get filter options
  app.get('/api/surveys/:level/:period/filters', controller.getFilters.bind(controller));

  // GET /api/surveys/:level/:period/sentiment — Get sentiment analysis
  app.get('/api/surveys/:level/:period/sentiment', controller.getSentiment.bind(controller));

  // GET /api/surveys/:level/:period/ids — Get response counts
  app.get('/api/surveys/:level/:period/ids', controller.getResponseCounts.bind(controller));

  // GET /api/surveys/:level/:period/nps-cross — Get NPS cross table
  app.get('/api/surveys/:level/:period/nps-cross', controller.getNpsCross.bind(controller));

  // GET /api/surveys/:level/:period/csat-cross — Get CSAT cross table
  app.get('/api/surveys/:level/:period/csat-cross', controller.getCsatCross.bind(controller));
}
