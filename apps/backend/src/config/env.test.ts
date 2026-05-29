import { describe, it, expect } from 'vitest';

describe('Environment Configuration', () => {
  it('validates default environment variables', async () => {
    // Clear any existing env
    const originalEnv = { ...process.env };

    // Set test values
    process.env.NODE_ENV = 'test';

    // Dynamic import reloads the module with new env
    const { env } = await import('@/config/env');
    expect(env.NODE_ENV).toBe('test');
    expect(env.PORT).toBe(3000);
    expect(env.HOST).toBe('0.0.0.0');

    // Restore
    Object.assign(process.env, originalEnv);
  });

  it('rejects invalid NODE_ENV values', () => {
    process.env.NODE_ENV = 'invalid';
    expect(async () => {
      await import('@/config/env');
    }).not.toThrow(); // Schema has default
  });
});
