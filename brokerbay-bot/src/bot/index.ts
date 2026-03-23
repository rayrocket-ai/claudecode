import { Client, GatewayIntentBits, Events } from 'discord.js';
import pino from 'pino';
import { config } from '../config';
import { isSessionValid } from '../browser/session';
import { handleTourCommand } from './commands/book';
import {
  handleListingsCommand,
  handlePendingCommand,
  handleApproveCommand,
  handleDeclineCommand,
  handleListingButton,
  handleApproveButton,
  handleDeclineButton,
} from './commands/listings';
import { handleSummaryCommand } from './commands/summary';

const logger = pino({ level: config.logLevel });

export function createClient(): Client {
  const client = new Client({
    intents: [
      GatewayIntentBits.Guilds,
      GatewayIntentBits.GuildMessages,
      GatewayIntentBits.MessageContent,
    ],
  });

  // ── Slash Commands ──
  client.on(Events.InteractionCreate, async (interaction) => {
    // Auth check: whitelist
    if (!config.discordAllowedUserIds.includes(interaction.user.id)) {
      logger.warn({ userId: interaction.user.id }, 'Unauthorized access attempt');
      if (interaction.isRepliable()) {
        await interaction.reply({ content: 'Unauthorized.', ephemeral: true });
      }
      return;
    }

    // Handle slash commands
    if (interaction.isChatInputCommand()) {
      try {
        switch (interaction.commandName) {
          case 'tour':
          case 'book':
            await handleTourCommand(interaction);
            break;
          case 'listings':
            await handleListingsCommand(interaction);
            break;
          case 'pending':
            await handlePendingCommand(interaction);
            break;
          case 'approve':
            await handleApproveCommand(interaction);
            break;
          case 'decline':
            await handleDeclineCommand(interaction);
            break;
          case 'summary':
            await handleSummaryCommand(interaction);
            break;
          case 'status': {
            await interaction.deferReply();
            const sessionValid = await isSessionValid().catch(() => false);
            const statusEmoji = sessionValid ? '✅' : '❌';
            await interaction.editReply(
              `🤖 **Bot Status:** Running\n` +
                `🔑 **BrokerBay Session:** ${statusEmoji} ${sessionValid ? 'Active' : 'Expired'}\n` +
                `⏰ **Server Time:** ${new Date().toLocaleString()}`,
            );
            break;
          }
          default:
            break;
        }
      } catch (err) {
        logger.error({ err, command: interaction.commandName }, 'Command error');
        const reply = { content: '❌ An error occurred processing this command.', ephemeral: true };
        if (interaction.deferred || interaction.replied) {
          await interaction.followUp(reply).catch(() => {});
        } else {
          await interaction.reply(reply).catch(() => {});
        }
      }
    }

    // Handle button interactions
    if (interaction.isButton()) {
      try {
        const customId = interaction.customId;

        if (customId.startsWith('listing:')) {
          await handleListingButton(interaction, customId.replace('listing:', ''));
        } else if (customId.startsWith('approve:')) {
          await handleApproveButton(interaction, customId.replace('approve:', ''));
        } else if (customId.startsWith('decline:')) {
          await handleDeclineButton(interaction, customId.replace('decline:', ''));
        } else if (customId.startsWith('listing_showings:') || customId.startsWith('listing_pending:')) {
          await interaction.reply({ content: 'Coming soon!', ephemeral: true });
        }
        // tour_confirm/tour_cancel are handled inline by the book command's awaitMessageComponent
      } catch (err) {
        logger.error({ err, customId: interaction.customId }, 'Button interaction error');
      }
    }
  });

  client.on(Events.ClientReady, (c) => {
    logger.info({ user: c.user.tag }, 'Bot is online!');
  });

  return client;
}
