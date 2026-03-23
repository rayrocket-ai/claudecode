import { Bot } from 'grammy';
import pino from 'pino';
import { config } from '../config';
import { isSessionValid } from '../browser/session';
import { handleTourCommand, handleConversationMessage } from './commands/book';
import {
  handleListingsCommand,
  handlePendingCommand,
  handleApproveCommand,
  handleDeclineCommand,
  handleListingCallback,
  handleApproveCallback,
  handleDeclineCallback,
} from './commands/listings';
import { handleSummaryCommand } from './commands/summary';
import { TelegramMessenger } from './messenger';

const logger = pino({ level: config.logLevel });

export function createBot(): Bot {
  const bot = new Bot(config.telegramBotToken);

  // ── Auth Middleware: whitelist check ──
  bot.use(async (ctx, next) => {
    const userId = ctx.from?.id;
    if (!userId || !config.telegramAllowedUserIds.includes(userId)) {
      logger.warn({ userId }, 'Unauthorized access attempt');
      await ctx.reply('Unauthorized.');
      return;
    }
    await next();
  });

  // ── Commands ──
  bot.command('start', async (ctx) => {
    await ctx.reply(
      '👋 Welcome to the BrokerBay Showing Bot!\n\n' +
        'Commands:\n' +
        '/tour or /book — Book a showing tour\n' +
        '/listings — View your active listings\n' +
        '/pending — View pending showing requests\n' +
        '/approve <id> — Approve a showing request\n' +
        '/decline <id> [reason] — Decline a showing request\n' +
        '/summary [date] — View showings for a date\n' +
        '/status — Check bot & session status',
    );
  });

  bot.command('help', async (ctx) => {
    await ctx.reply(
      '📖 *BrokerBay Bot Commands*\n\n' +
        '🏠 *Showing Tours*\n' +
        '/tour — Start booking a showing tour\n' +
        '/book — Same as /tour\n\n' +
        '📋 *Listing Management*\n' +
        '/listings — View your active listings\n' +
        '/pending — View pending showing requests\n' +
        '/approve <id> — Approve a request\n' +
        '/decline <id> \\[reason\\] — Decline a request\n\n' +
        '📅 *Summary*\n' +
        '/summary \\[date\\] — Showings for a date \\(default: today\\)\n\n' +
        '⚙️ *System*\n' +
        '/status — Check bot and session status',
      { parse_mode: 'MarkdownV2' },
    );
  });

  bot.command(['tour', 'book'], handleTourCommand);
  bot.command('listings', handleListingsCommand);
  bot.command('pending', handlePendingCommand);
  bot.command('approve', handleApproveCommand);
  bot.command('decline', handleDeclineCommand);
  bot.command('summary', handleSummaryCommand);

  bot.command('status', async (ctx) => {
    const sessionValid = await isSessionValid().catch(() => false);
    const statusEmoji = sessionValid ? '✅' : '❌';
    await ctx.reply(
      `🤖 Bot Status: Running\n` +
        `🔑 BrokerBay Session: ${statusEmoji} ${sessionValid ? 'Active' : 'Expired'}\n` +
        `⏰ Server Time: ${new Date().toLocaleString()}`,
    );
  });

  // ── Callback Queries (inline button presses) ──
  bot.on('callback_query:data', async (ctx) => {
    const data = ctx.callbackQuery.data;

    if (data.startsWith('listing:')) {
      await handleListingCallback(ctx, data.replace('listing:', ''));
    } else if (data.startsWith('approve:')) {
      await handleApproveCallback(ctx, data.replace('approve:', ''));
    } else if (data.startsWith('decline:')) {
      await handleDeclineCallback(ctx, data.replace('decline:', ''));
    } else if (data.startsWith('listing_showings:') || data.startsWith('listing_pending:')) {
      // These would navigate to sub-views — placeholder for now
      await ctx.answerCallbackQuery('Coming soon!');
    } else {
      await ctx.answerCallbackQuery();
    }
  });

  // ── Text Messages (conversation flow) ──
  bot.on('message:text', async (ctx) => {
    const handled = await handleConversationMessage(ctx);
    if (!handled) {
      await ctx.reply('Use /tour to book a showing tour or /help for all commands.');
    }
  });

  // ── Error Handler ──
  bot.catch((err) => {
    logger.error({ err: err.error, ctx: err.ctx?.update?.update_id }, 'Bot error');
  });

  return bot;
}

// Export the messenger factory
export function createMessenger(bot: Bot): TelegramMessenger {
  return new TelegramMessenger(bot);
}
