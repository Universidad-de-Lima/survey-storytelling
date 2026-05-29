import type { FastifyError, FastifyInstance, FastifyReply, FastifyRequest } from 'fastify';
import { ZodError } from 'zod';

interface ErrorResponse {
  success: false;
  error: string;
  details?: unknown;
  statusCode: number;
}

export function errorHandler(
  app: FastifyInstance,
): (error: FastifyError, request: FastifyRequest, reply: FastifyReply) => void {
  return (error: FastifyError, _request: FastifyRequest, reply: FastifyReply) => {
    app.log.error(error);

    // Zod validation errors
    if (error instanceof ZodError) {
      const response: ErrorResponse = {
        success: false,
        error: 'Validation error',
        details: error.flatten(),
        statusCode: 400,
      };
      return reply.status(400).send(response);
    }

    // Fastify built-in errors
    if (error.statusCode) {
      const response: ErrorResponse = {
        success: false,
        error: error.message,
        statusCode: error.statusCode,
      };
      return reply.status(error.statusCode).send(response);
    }

    // Unknown errors
    const response: ErrorResponse = {
      success: false,
      error: 'Internal server error',
      statusCode: 500,
    };
    return reply.status(500).send(response);
  };
}
