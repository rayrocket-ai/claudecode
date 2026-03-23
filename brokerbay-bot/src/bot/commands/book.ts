import { Context } from 'grammy';
import pino from 'pino';
import { config } from '../../config';
import { enqueue } from '../queue';
import { optimizeRoute, buildSchedule, parseTimeWindow, getAlternativeSlots } from '../../scheduler/optimizer';
import { searchListing, bookShowing, getListingDetails } from '../../browser/brokerbay';
import { formatTourSummary, formatProposedSchedule } from '../../formatters/tour';
import type { ConversationState, TourRequest, BookingConfirmation, FailedBooking, TourStop } from '../../types';

const logger = pino({ level: config.logLevel });

// In-memory conversation state per user
const conversations = new Map<number, ConversationState>();

export function getConversation(userId: number): ConversationState {
  if (!conversations.has(userId)) {
    conversations.set(userId, { step: 'idle' });
  }
  return conversations.get(userId)!;
}

export function resetConversation(userId: number): void {
  conversations.set(userId, { step: 'idle' });
}

export async function handleTourCommand(ctx: Context): Promise<void> {
  const userId = ctx.from?.id;
  if (!userId) return;

  resetConversation(userId);
  const conv = getConversation(userId);
  conv.step = 'awaiting_addresses';

  await ctx.reply('📋 Paste your list of addresses (one per line):');
}

export async function handleConversationMessage(ctx: Context): Promise<boolean> {
  const userId = ctx.from?.id;
  const text = ctx.message?.text;
  if (!userId || !text) return false;

  const conv = getConversation(userId);
  if (conv.step === 'idle') return false;

  switch (conv.step) {
    case 'awaiting_addresses': {
      const addresses = text
        .split('\n')
        .map((a) => a.trim())
        .filter((a) => a.length > 0);

      if (addresses.length === 0) {
        await ctx.reply('Please provide at least one address.');
        return true;
      }

      conv.addresses = addresses;
      conv.step = 'awaiting_date';
      await ctx.reply(`Got ${addresses.length} address(es). 📅 What date? (e.g. March 25)`);
      return true;
    }

    case 'awaiting_date': {
      conv.date = text.trim();
      conv.step = 'awaiting_time_window';
      await ctx.reply('⏰ Preferred start time and latest end time? (e.g. 10am – 4pm)');
      return true;
    }

    case 'awaiting_time_window': {
      try {
        const { startTime, endTime } = parseTimeWindow(text);
        conv.startTime = startTime;
        conv.endTime = endTime;
        conv.step = 'awaiting_client_name';
        await ctx.reply('👤 Client name for these showings?');
      } catch {
        await ctx.reply('Please provide a time window like "10am - 4pm"');
      }
      return true;
    }

    case 'awaiting_client_name': {
      conv.clientName = text.trim();
      conv.step = 'awaiting_starting_point';
      await ctx.reply('📍 Starting point? (your office address, home, or "first property")');
      return true;
    }

    case 'awaiting_starting_point': {
      conv.startingPoint = text.trim();
      conv.step = 'awaiting_duration';
      await ctx.reply('⏱ Minutes per showing? (default 25, or type 20/30)');
      return true;
    }

    case 'awaiting_duration': {
      const duration = parseInt(text.trim(), 10);
      conv.durationMinutes = [20, 25, 30].includes(duration) ? duration : 25;
      conv.step = 'awaiting_confirmation';

      await ctx.reply('🔄 Optimizing your tour route...');

      try {
        const tourRequest: TourRequest = {
          addresses: conv.addresses!,
          date: conv.date!,
          startTime: conv.startTime!,
          endTime: conv.endTime!,
          clientName: conv.clientName!,
          startingPoint: conv.startingPoint === 'first property' ? conv.addresses![0] : conv.startingPoint!,
          durationMinutes: conv.durationMinutes,
        };

        const optimizedRoute = await optimizeRoute(tourRequest);

        // Build a preliminary schedule (before actual bookings) to show the user
        const prelimStops: TourStop[] = optimizedRoute.order.map((addressIndex, i) => ({
          id: '',
          address: conv.addresses![addressIndex],
          mlsNumber: '',
          price: 0,
          sqft: 0,
          yearBuilt: 0,
          agentName: '',
          agentPhone: '',
          showingInstructions: '',
          confirmationId: '',
          bookedTime: new Date(),
          stopNumber: i + 1,
          arrivalTime: new Date(),
          departureTime: new Date(),
          driveTimeFromPrevious: 0,
        }));

        const prelimSchedule = buildSchedule(tourRequest, optimizedRoute, prelimStops as unknown as BookingConfirmation[], []);
        conv.proposedSchedule = prelimSchedule;

        const msg = formatProposedSchedule(prelimSchedule);
        await ctx.reply(msg + '\n\nReply *✅ Book All* to confirm or *✏️ Adjust* to modify\\.', {
          parse_mode: 'MarkdownV2',
        });
      } catch (err) {
        logger.error({ err }, 'Route optimization failed');
        await ctx.reply('❌ Failed to optimize route. Please try again.');
        resetConversation(userId);
      }
      return true;
    }

    case 'awaiting_confirmation': {
      const lower = text.toLowerCase().trim();
      if (lower.includes('book') || lower.includes('confirm') || lower === '✅' || lower === 'yes') {
        await ctx.reply('🔄 Booking all showings in BrokerBay... This may take a few minutes.');

        try {
          await enqueue('book-tour', async () => {
            await bookTour(ctx, conv);
          });
        } catch (err) {
          logger.error({ err }, 'Tour booking failed');
          await ctx.reply('❌ An error occurred while booking. Some showings may have been booked. Check BrokerBay for details.');
        }

        resetConversation(userId);
      } else if (lower.includes('adjust') || lower.includes('cancel') || lower === '✏️') {
        await ctx.reply('Tour cancelled. Use /tour to start over.');
        resetConversation(userId);
      } else {
        await ctx.reply('Reply ✅ *Book All* or ✏️ *Adjust*', { parse_mode: 'MarkdownV2' });
      }
      return true;
    }

    default:
      return false;
  }
}

async function bookTour(ctx: Context, conv: ConversationState): Promise<void> {
  const addresses = conv.addresses!;
  const bookings: BookingConfirmation[] = [];
  const failed: FailedBooking[] = [];

  for (let i = 0; i < addresses.length; i++) {
    const address = addresses[i];
    const stopInfo = conv.proposedSchedule?.stops[i];

    try {
      await ctx.reply(`🔍 Searching for listing: ${address}...`);

      const listing = await searchListing(address);
      if (!listing) {
        failed.push({ address, reason: 'Listing not found in BrokerBay' });
        continue;
      }

      const targetTime = stopInfo?.arrivalTime || new Date();

      // Try booking at the planned time
      let booking: BookingConfirmation | null = null;
      try {
        booking = await bookShowing({
          listingId: listing.id,
          dateTime: targetTime,
          clientName: conv.clientName!,
          durationMinutes: conv.durationMinutes!,
        });
      } catch {
        // Try alternative time slots
        const alternatives = getAlternativeSlots(targetTime);
        for (const altTime of alternatives) {
          try {
            booking = await bookShowing({
              listingId: listing.id,
              dateTime: altTime,
              clientName: conv.clientName!,
              durationMinutes: conv.durationMinutes!,
            });
            break;
          } catch {
            continue;
          }
        }
      }

      if (booking) {
        bookings.push(booking);
        await ctx.reply(`✅ Booked: ${address}`);
      } else {
        failed.push({ address, reason: 'No available time slots' });
        await ctx.reply(`⚠️ Could not book: ${address} — no available time slots`);
      }
    } catch (err) {
      logger.error({ err, address }, 'Booking failed for address');
      failed.push({ address, reason: 'Booking error' });
      await ctx.reply(`❌ Error booking: ${address}`);
    }
  }

  // Build and send final summary
  const tourRequest: TourRequest = {
    addresses: conv.addresses!,
    date: conv.date!,
    startTime: conv.startTime!,
    endTime: conv.endTime!,
    clientName: conv.clientName!,
    startingPoint: conv.startingPoint!,
    durationMinutes: conv.durationMinutes!,
  };

  const optimizedRoute = await optimizeRoute(tourRequest);
  const finalSchedule = buildSchedule(tourRequest, optimizedRoute, bookings, failed);
  const summary = formatTourSummary(finalSchedule);

  await ctx.reply(summary, { parse_mode: 'MarkdownV2' });
}
