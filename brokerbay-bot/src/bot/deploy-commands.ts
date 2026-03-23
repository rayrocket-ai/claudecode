/**
 * Deploy Discord slash commands.
 * Run once after setup: npm run deploy-commands
 */

import { REST, Routes, SlashCommandBuilder } from 'discord.js';
import { config } from '../config';

const commands = [
  new SlashCommandBuilder()
    .setName('tour')
    .setDescription('Book a showing tour for multiple properties'),
  new SlashCommandBuilder()
    .setName('book')
    .setDescription('Book a showing tour (alias for /tour)'),
  new SlashCommandBuilder()
    .setName('listings')
    .setDescription('View your active brokerage listings'),
  new SlashCommandBuilder()
    .setName('pending')
    .setDescription('View pending showing requests'),
  new SlashCommandBuilder()
    .setName('approve')
    .setDescription('Approve a showing request')
    .addStringOption((opt) =>
      opt.setName('id').setDescription('The showing request ID').setRequired(true),
    ),
  new SlashCommandBuilder()
    .setName('decline')
    .setDescription('Decline a showing request')
    .addStringOption((opt) =>
      opt.setName('id').setDescription('The showing request ID').setRequired(true),
    )
    .addStringOption((opt) =>
      opt.setName('reason').setDescription('Reason for declining').setRequired(false),
    ),
  new SlashCommandBuilder()
    .setName('summary')
    .setDescription('View showings for a date')
    .addStringOption((opt) =>
      opt.setName('date').setDescription('Date (e.g. March 25). Defaults to today.').setRequired(false),
    ),
  new SlashCommandBuilder()
    .setName('status')
    .setDescription('Check bot and BrokerBay session status'),
].map((cmd) => cmd.toJSON());

async function deploy(): Promise<void> {
  const rest = new REST({ version: '10' }).setToken(config.discordBotToken);

  console.log(`Deploying ${commands.length} slash commands...`);

  if (config.discordGuildId) {
    // Guild-specific (instant, good for dev)
    await rest.put(
      Routes.applicationGuildCommands(config.discordClientId, config.discordGuildId),
      { body: commands },
    );
    console.log(`Commands deployed to guild ${config.discordGuildId}`);
  } else {
    // Global (takes up to 1 hour to propagate)
    await rest.put(Routes.applicationCommands(config.discordClientId), {
      body: commands,
    });
    console.log('Commands deployed globally (may take up to 1 hour to appear)');
  }
}

deploy().catch((err) => {
  console.error('Failed to deploy commands:', err);
  process.exit(1);
});
