import { z } from 'zod';

const envSchema = z.object({
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
  PORT: z.coerce.number().positive().default(3000),
  HOST: z.string().default('0.0.0.0'),
  CORS_ORIGIN: z.string().default('http://localhost:5173'),
  DATA_DIR: z.string().default('./data'),
  LOG_LEVEL: z.enum(['debug', 'info', 'warn', 'error']).default('info'),
  RATE_LIMIT_MAX: z.coerce.number().positive().default(100),
  RATE_LIMIT_WINDOW_MS: z.coerce.number().positive().default(60000),
});

function validateEnv() {
  const result = envSchema.safeParse(process.env);

  if (!result.success) {
    console.error('❌ Invalid environment variables:', result.error.flatten().fieldErrors);
    process.exit(1);
  }

  return result.data;
}

export const env = validateEnv();

export type Env = z.infer<typeof envSchema>;
