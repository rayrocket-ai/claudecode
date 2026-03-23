import { Context, InlineKeyboard } from 'grammy';
import pino from 'pino';
import { config } from '../../config';
import { enqueue } from '../queue';
import {
  getMyListings,
  getPendingRequests,
  approveShowingRequest,
  declineShowingRequest,
  getListingDetails,
  updateShowingInstructions,
} from '../../browser/brokerbay';
import { formatMyListings, formatPendingRequests, formatApprovalResult, formatListingDetails } from '../../formatters/listing';

const logger = pino({ level: config.logLevel });

export async function handleListingsCommand(ctx: Context): Promise<void> {
  await ctx.reply('🔄 Fetching your listings...');

  try {
    const listings = await enqueue('get-listings', () => getMyListings());
    const text = formatMyListings(listings);

    if (listings.length === 0) {
      await ctx.reply(text, { parse_mode: 'MarkdownV2' });
      return;
    }

    // Build inline buttons for each listing
    const keyboard = new InlineKeyboard();
    for (const listing of listings) {
      keyboard.text(`🏠 ${listing.address}`, `listing:${listing.id}`).row();
    }

    await ctx.reply(text, {
      parse_mode: 'MarkdownV2',
      reply_markup: keyboard,
    });
  } catch (err) {
    logger.error({ err }, 'Failed to fetch listings');
    await ctx.reply('❌ Failed to fetch listings. Please try again.');
  }
}

export async function handleListingCallback(ctx: Context, listingId: string): Promise<void> {
  await ctx.answerCallbackQuery();

  const keyboard = new InlineKeyboard()
    .text('📅 View Showings', `listing_showings:${listingId}`)
    .text('⏳ Pending Requests', `listing_pending:${listingId}`)
    .row()
    .text('🔑 Update Instructions', `listing_instructions:${listingId}`)
    .text('⏰ Set Availability', `listing_availability:${listingId}`)
    .row()
    .text('📢 Message Co-op Agents', `listing_message:${listingId}`)
    .text('💰 Offer Instructions', `listing_offers:${listingId}`);

  try {
    const details = await enqueue('get-listing-details', () => getListingDetails(listingId));
    const text = formatListingDetails(details);

    await ctx.editMessageText(text, {
      parse_mode: 'MarkdownV2',
      reply_markup: keyboard,
    });
  } catch (err) {
    logger.error({ err, listingId }, 'Failed to get listing details');
    await ctx.editMessageText('❌ Failed to load listing details.', {
      reply_markup: keyboard,
    });
  }
}

export async function handlePendingCommand(ctx: Context): Promise<void> {
  await ctx.reply('🔄 Fetching pending requests...');

  try {
    const requests = await enqueue('get-pending', () => getPendingRequests());
    const text = formatPendingRequests(requests);

    if (requests.length === 0) {
      await ctx.reply(text, { parse_mode: 'MarkdownV2' });
      return;
    }

    // Add approve/decline buttons for each request
    const keyboard = new InlineKeyboard();
    for (const req of requests) {
      keyboard
        .text('✅ Approve', `approve:${req.requestId}`)
        .text('❌ Decline', `decline:${req.requestId}`)
        .row();
    }

    await ctx.reply(text, {
      parse_mode: 'MarkdownV2',
      reply_markup: keyboard,
    });
  } catch (err) {
    logger.error({ err }, 'Failed to fetch pending requests');
    await ctx.reply('❌ Failed to fetch pending requests.');
  }
}

export async function handleApproveCommand(ctx: Context): Promise<void> {
  const text = ctx.message?.text || '';
  const parts = text.split(/\s+/);
  const requestId = parts[1];

  if (!requestId) {
    await ctx.reply('Usage: /approve <request_id>');
    return;
  }

  await ctx.reply(`🔄 Approving request ${requestId}...`);

  try {
    const success = await enqueue('approve-request', () => approveShowingRequest(requestId));
    const msg = formatApprovalResult(requestId, success);
    await ctx.reply(msg, { parse_mode: 'MarkdownV2' });
  } catch (err) {
    logger.error({ err, requestId }, 'Failed to approve request');
    await ctx.reply('❌ Failed to approve request.');
  }
}

export async function handleDeclineCommand(ctx: Context): Promise<void> {
  const text = ctx.message?.text || '';
  const parts = text.split(/\s+/);
  const requestId = parts[1];
  const reason = parts.slice(2).join(' ') || undefined;

  if (!requestId) {
    await ctx.reply('Usage: /decline <request_id> [reason]');
    return;
  }

  await ctx.reply(`🔄 Declining request ${requestId}...`);

  try {
    const success = await enqueue('decline-request', () => declineShowingRequest(requestId, reason));
    const msg = formatApprovalResult(requestId, false);
    await ctx.reply(msg, { parse_mode: 'MarkdownV2' });
  } catch (err) {
    logger.error({ err, requestId }, 'Failed to decline request');
    await ctx.reply('❌ Failed to decline request.');
  }
}

export async function handleApproveCallback(ctx: Context, requestId: string): Promise<void> {
  await ctx.answerCallbackQuery('Approving...');

  try {
    const success = await enqueue('approve-request', () => approveShowingRequest(requestId));
    const msg = formatApprovalResult(requestId, success);
    await ctx.editMessageText(msg, { parse_mode: 'MarkdownV2' });
  } catch (err) {
    logger.error({ err, requestId }, 'Failed to approve request');
    await ctx.answerCallbackQuery('Failed to approve');
  }
}

export async function handleDeclineCallback(ctx: Context, requestId: string): Promise<void> {
  await ctx.answerCallbackQuery('Declining...');

  try {
    const success = await enqueue('decline-request', () => declineShowingRequest(requestId));
    const msg = formatApprovalResult(requestId, false);
    await ctx.editMessageText(msg, { parse_mode: 'MarkdownV2' });
  } catch (err) {
    logger.error({ err, requestId }, 'Failed to decline request');
    await ctx.answerCallbackQuery('Failed to decline');
  }
}
