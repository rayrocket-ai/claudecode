import pino from 'pino';
import { config } from './config';
import { createBot } from './bot';
import { initBrowser, closeBrowser, ensureAuthenticated } from './browser/session';

const logger = pino({
  level: config.logLevel,
  transport:
    config.nodeEnv === 'development'
      ? { target: 'pino-pretty', options: { colorize: true } }
      : undefined,
});

async function main(): Promise<void> {
  logger.info('Starting BrokerBay Showing Bot...');

  // Initialize browser and verify session
  try {
    await initBrowser();
    logger.info('Browser initialized');
    await ensureAuthenticated();
    logger.info('BrokerBay session is active');
  } catch (err) {
    logger.error({ err }, 'Failed to initialize browser session. Run `npm run login` first.');
    process.exit(1);
  }

  // Create and start the Telegram bot
  const bot = createBot();

  // Graceful shutdown
  const shutdown = async (signal: string) => {
    logger.info({ signal }, 'Shutting down...');
    bot.stop();
    await closeBrowser();
    process.exit(0);
  };

  process.on('SIGINT', () => shutdown('SIGINT'));
  process.on('SIGTERM', () => shutdown('SIGTERM'));

  // Start polling
  logger.info('Bot is starting...');
  await bot.start({
    onStart: () => {
      logger.info('Bot is running! Waiting for messages...');
    },
  });
}

main().catch((err) => {
  logger.fatal({ err }, 'Fatal error');
  process.exit(1);
});
