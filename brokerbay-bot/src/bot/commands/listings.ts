import {
  ChatInputCommandInteraction,
  ButtonInteraction,
  ActionRowBuilder,
  ButtonBuilder,
  ButtonStyle,
  TextChannel,
} from 'discord.js';
import pino from 'pino';
import { config } from '../../config';
import { enqueue } from '../queue';
import {
  getMyListings,
  getPendingRequests,
  approveShowingRequest,
  declineShowingRequest,
  getListingDetails,
} from '../../browser/brokerbay';
import {
  formatMyListings,
  formatPendingRequests,
  formatApprovalResult,
  formatListingDetails,
} from '../../formatters/listing';

const logger = pino({ level: config.logLevel });

export async function handleListingsCommand(interaction: ChatInputCommandInteraction): Promise<void> {
  await interaction.deferReply();

  try {
    const listings = await enqueue('get-listings', () => getMyListings());
    const text = formatMyListings(listings);

    if (listings.length === 0) {
      await interaction.editReply(text);
      return;
    }

    // Build button rows (max 5 buttons per row, max 5 rows)
    const rows: ActionRowBuilder<ButtonBuilder>[] = [];
    for (let i = 0; i < Math.min(listings.length, 25); i++) {
      const rowIndex = Math.floor(i / 5);
      if (!rows[rowIndex]) {
        rows[rowIndex] = new ActionRowBuilder<ButtonBuilder>();
      }
      rows[rowIndex].addComponents(
        new ButtonBuilder()
          .setCustomId(`listing:${listings[i].id}`)
          .setLabel(listings[i].address.substring(0, 80))
          .setEmoji('🏠')
          .setStyle(ButtonStyle.Secondary),
      );
    }

    await interaction.editReply({ content: text, components: rows.slice(0, 5) });
  } catch (err) {
    logger.error({ err }, 'Failed to fetch listings');
    await interaction.editReply('❌ Failed to fetch listings. Please try again.');
  }
}

export async function handleListingButton(interaction: ButtonInteraction, listingId: string): Promise<void> {
  await interaction.deferUpdate();

  const rows = [
    new ActionRowBuilder<ButtonBuilder>().addComponents(
      new ButtonBuilder()
        .setCustomId(`listing_showings:${listingId}`)
        .setLabel('View Showings')
        .setEmoji('📅')
        .setStyle(ButtonStyle.Primary),
      new ButtonBuilder()
        .setCustomId(`listing_pending:${listingId}`)
        .setLabel('Pending Requests')
        .setEmoji('⏳')
        .setStyle(ButtonStyle.Primary),
    ),
    new ActionRowBuilder<ButtonBuilder>().addComponents(
      new ButtonBuilder()
        .setCustomId(`listing_instructions:${listingId}`)
        .setLabel('Update Instructions')
        .setEmoji('🔑')
        .setStyle(ButtonStyle.Secondary),
      new ButtonBuilder()
        .setCustomId(`listing_availability:${listingId}`)
        .setLabel('Set Availability')
        .setEmoji('⏰')
        .setStyle(ButtonStyle.Secondary),
    ),
  ];

  try {
    const details = await enqueue('get-listing-details', () => getListingDetails(listingId));
    const text = formatListingDetails(details);
    await interaction.editReply({ content: text, components: rows });
  } catch (err) {
    logger.error({ err, listingId }, 'Failed to get listing details');
    await interaction.editReply({ content: '❌ Failed to load listing details.', components: rows });
  }
}

export async function handlePendingCommand(interaction: ChatInputCommandInteraction): Promise<void> {
  await interaction.deferReply();

  try {
    const requests = await enqueue('get-pending', () => getPendingRequests());
    const text = formatPendingRequests(requests);

    if (requests.length === 0) {
      await interaction.editReply(text);
      return;
    }

    // Build approve/decline buttons (max 5 rows)
    const rows: ActionRowBuilder<ButtonBuilder>[] = [];
    for (let i = 0; i < Math.min(requests.length, 5); i++) {
      rows.push(
        new ActionRowBuilder<ButtonBuilder>().addComponents(
          new ButtonBuilder()
            .setCustomId(`approve:${requests[i].requestId}`)
            .setLabel(`Approve ${requests[i].listingAddress.substring(0, 40)}`)
            .setEmoji('✅')
            .setStyle(ButtonStyle.Success),
          new ButtonBuilder()
            .setCustomId(`decline:${requests[i].requestId}`)
            .setLabel('Decline')
            .setEmoji('❌')
            .setStyle(ButtonStyle.Danger),
        ),
      );
    }

    await interaction.editReply({ content: text, components: rows });
  } catch (err) {
    logger.error({ err }, 'Failed to fetch pending requests');
    await interaction.editReply('❌ Failed to fetch pending requests.');
  }
}

export async function handleApproveCommand(interaction: ChatInputCommandInteraction): Promise<void> {
  const requestId = interaction.options.getString('id', true);
  await interaction.deferReply();

  try {
    const success = await enqueue('approve-request', () => approveShowingRequest(requestId));
    const msg = formatApprovalResult(requestId, success);
    await interaction.editReply(msg);
  } catch (err) {
    logger.error({ err, requestId }, 'Failed to approve request');
    await interaction.editReply('❌ Failed to approve request.');
  }
}

export async function handleDeclineCommand(interaction: ChatInputCommandInteraction): Promise<void> {
  const requestId = interaction.options.getString('id', true);
  const reason = interaction.options.getString('reason') || undefined;
  await interaction.deferReply();

  try {
    const success = await enqueue('decline-request', () => declineShowingRequest(requestId, reason));
    const msg = formatApprovalResult(requestId, false);
    await interaction.editReply(msg);
  } catch (err) {
    logger.error({ err, requestId }, 'Failed to decline request');
    await interaction.editReply('❌ Failed to decline request.');
  }
}

export async function handleApproveButton(interaction: ButtonInteraction, requestId: string): Promise<void> {
  await interaction.deferUpdate();

  try {
    const success = await enqueue('approve-request', () => approveShowingRequest(requestId));
    const msg = formatApprovalResult(requestId, success);
    await interaction.editReply({ content: msg, components: [] });
  } catch (err) {
    logger.error({ err, requestId }, 'Failed to approve request');
    await interaction.followUp({ content: '❌ Failed to approve request.', ephemeral: true });
  }
}

export async function handleDeclineButton(interaction: ButtonInteraction, requestId: string): Promise<void> {
  await interaction.deferUpdate();

  try {
    const success = await enqueue('decline-request', () => declineShowingRequest(requestId));
    const msg = formatApprovalResult(requestId, false);
    await interaction.editReply({ content: msg, components: [] });
  } catch (err) {
    logger.error({ err, requestId }, 'Failed to decline request');
    await interaction.followUp({ content: '❌ Failed to decline request.', ephemeral: true });
  }
}
