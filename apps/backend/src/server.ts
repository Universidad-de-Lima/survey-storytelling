import { buildApp } from '@/app';
import { env } from '@/config/env';

async function main() {
  const app = await buildApp();

  try {
    await app.listen({ port: env.PORT, host: env.HOST });
    console.log(`
╔══════════════════════════════════════════════════╗
║  Survey Storytelling API                         ║
║  ─────────────────────                            ║
║  Environment : ${env.NODE_ENV.padEnd(25)}║
║  Port        : ${String(env.PORT).padEnd(25)}║
║  CORS Origin : ${env.CORS_ORIGIN.padEnd(25)}║
║  Data Dir    : ${env.DATA_DIR.padEnd(25)}║
╚══════════════════════════════════════════════════╝
    `);
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
}

main();
