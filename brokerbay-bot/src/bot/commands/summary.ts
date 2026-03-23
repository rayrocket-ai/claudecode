import { Context } from 'grammy';
import pino from 'pino';
import { config } from '../../config';
import { enqueue } from '../queue';
import { getPendingRequests } from '../../browser/brokerbay';
import { formatDaySummary } from '../../formatters/listing';

const logger = pino({ level: config.logLevel });

function parseDate(input: string): string {
  const trimmed = input.trim();
  if (!trimmed) {
    return new Date().toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    });
  }

  // Try parsing the user's date input
  const parsed = new Date(trimmed);
  if (!isNaN(parsed.getTime())) {
    return parsed.toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    });
  }

  // Return as-is if we can't parse it
  return trimmed;
}

export async function handleSummaryCommand(ctx: Context): Promise<void> {
  const text = ctx.message?.text || '';
  const dateInput = text.replace(/^\/summary\s*/i, '').trim();
  const dateStr = parseDate(dateInput);

  await ctx.reply(`🔄 Fetching showings for ${dateStr}...`);

  try {
    // Note: BrokerBay may need filtering by date — getPendingRequests gets all,
    // then we filter client-side. A more sophisticated implementation would
    // navigate to the correct date view in BrokerBay.
    const allRequests = await enqueue('get-summary', () => getPendingRequests());

    const targetDate = new Date(dateStr);
    const filtered = allRequests.filter((req) => {
      const reqDate = new Date(req.requestedTime);
      return (
        reqDate.getFullYear() === targetDate.getFullYear() &&
        reqDate.getMonth() === targetDate.getMonth() &&
        reqDate.getDate() === targetDate.getDate()
      );
    });

    const summary = formatDaySummary(dateStr, filtered);
    await ctx.reply(summary, { parse_mode: 'MarkdownV2' });
  } catch (err) {
    logger.error({ err }, 'Failed to fetch summary');
    await ctx.reply('❌ Failed to fetch showing summary.');
  }
}
