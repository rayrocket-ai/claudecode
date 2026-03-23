import { ChatInputCommandInteraction } from 'discord.js';
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

  const parsed = new Date(trimmed);
  if (!isNaN(parsed.getTime())) {
    return parsed.toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    });
  }

  return trimmed;
}

export async function handleSummaryCommand(interaction: ChatInputCommandInteraction): Promise<void> {
  const dateInput = interaction.options.getString('date') || '';
  const dateStr = parseDate(dateInput);

  await interaction.deferReply();

  try {
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
    await interaction.editReply(summary);
  } catch (err) {
    logger.error({ err }, 'Failed to fetch summary');
    await interaction.editReply('❌ Failed to fetch showing summary.');
  }
}
