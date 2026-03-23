import {
  ChatInputCommandInteraction,
  Message,
  TextChannel,
  ActionRowBuilder,
  ButtonBuilder,
  ButtonStyle,
  ButtonInteraction,
  ComponentType,
} from 'discord.js';
import pino from 'pino';
import { config } from '../../config';
import { enqueue } from '../queue';
import { optimizeRoute, buildSchedule, parseTimeWindow, getAlternativeSlots } from '../../scheduler/optimizer';
import { searchListing, bookShowing } from '../../browser/brokerbay';
import { formatTourSummary, formatProposedSchedule } from '../../formatters/tour';
import type { ConversationState, TourRequest, BookingConfirmation, FailedBooking, TourStop } from '../../types';

const logger = pino({ level: config.logLevel });

// In-memory conversation state per user
const conversations = new Map<string, ConversationState>();

function getConversation(userId: string): ConversationState {
  if (!conversations.has(userId)) {
    conversations.set(userId, { step: 'idle' });
  }
  return conversations.get(userId)!;
}

function resetConversation(userId: string): void {
  conversations.set(userId, { step: 'idle' });
}

async function collectMessage(
  channel: TextChannel,
  userId: string,
  prompt: string,
  timeoutMs = 120000,
): Promise<string | null> {
  await channel.send(prompt);

  const collected = await channel
    .awaitMessages({
      filter: (m: Message) => m.author.id === userId,
      max: 1,
      time: timeoutMs,
    })
    .catch(() => null);

  if (!collected || collected.size === 0) {
    await channel.send('Timed out waiting for your response. Use /tour to start over.');
    return null;
  }

  return collected.first()!.content;
}

export async function handleTourCommand(interaction: ChatInputCommandInteraction): Promise<void> {
  const userId = interaction.user.id;
  const channel = interaction.channel as TextChannel;

  if (!channel || !channel.isTextBased()) {
    await interaction.reply({ content: 'This command must be used in a text channel.', ephemeral: true });
    return;
  }

  resetConversation(userId);
  const conv = getConversation(userId);
  conv.channelId = channel.id;

  await interaction.reply('Starting a new showing tour booking...');

  // Step 1: Addresses
  const addressText = await collectMessage(channel, userId, '📋 Paste your list of addresses (one per line):');
  if (!addressText) return resetConversation(userId);

  const addresses = addressText.split('\n').map((a) => a.trim()).filter((a) => a.length > 0);
  if (addresses.length === 0) {
    await channel.send('No valid addresses provided. Use /tour to start over.');
    return resetConversation(userId);
  }
  conv.addresses = addresses;

  // Step 2: Date
  const dateText = await collectMessage(channel, userId, `Got ${addresses.length} address(es). 📅 What date? (e.g. March 25)`);
  if (!dateText) return resetConversation(userId);
  conv.date = dateText.trim();

  // Step 3: Time window
  let timeText: string | null = null;
  while (true) {
    timeText = await collectMessage(channel, userId, '⏰ Preferred start time and latest end time? (e.g. 10am – 4pm)');
    if (!timeText) return resetConversation(userId);
    try {
      const { startTime, endTime } = parseTimeWindow(timeText);
      conv.startTime = startTime;
      conv.endTime = endTime;
      break;
    } catch {
      await channel.send('Please provide a time window like "10am - 4pm"');
    }
  }

  // Step 4: Client name
  const clientName = await collectMessage(channel, userId, '👤 Client name for these showings?');
  if (!clientName) return resetConversation(userId);
  conv.clientName = clientName.trim();

  // Step 5: Starting point
  const startingPoint = await collectMessage(channel, userId, '📍 Starting point? (your office address, home, or "first property")');
  if (!startingPoint) return resetConversation(userId);
  conv.startingPoint = startingPoint.trim();

  // Step 6: Duration
  const durationText = await collectMessage(channel, userId, '⏱ Minutes per showing? (default 25, or type 20/30)');
  if (!durationText) return resetConversation(userId);
  const duration = parseInt(durationText.trim(), 10);
  conv.durationMinutes = [20, 25, 30].includes(duration) ? duration : 25;

  // Step 7: Optimize and propose
  await channel.send('🔄 Optimizing your tour route...');

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

    const row = new ActionRowBuilder<ButtonBuilder>().addComponents(
      new ButtonBuilder()
        .setCustomId(`tour_confirm:${userId}`)
        .setLabel('Book All')
        .setEmoji('✅')
        .setStyle(ButtonStyle.Success),
      new ButtonBuilder()
        .setCustomId(`tour_cancel:${userId}`)
        .setLabel('Cancel')
        .setEmoji('✏️')
        .setStyle(ButtonStyle.Secondary),
    );

    const confirmMsg = await channel.send({ content: msg, components: [row] });

    // Wait for button press
    const btnInteraction = await confirmMsg
      .awaitMessageComponent({
        componentType: ComponentType.Button,
        filter: (i: ButtonInteraction) => i.user.id === userId,
        time: 120000,
      })
      .catch(() => null);

    if (!btnInteraction) {
      await channel.send('Timed out. Use /tour to start over.');
      return resetConversation(userId);
    }

    if (btnInteraction.customId === `tour_confirm:${userId}`) {
      await btnInteraction.update({ content: msg + '\n\n🔄 Booking all showings in BrokerBay... This may take a few minutes.', components: [] });

      try {
        await enqueue('book-tour', async () => {
          await bookTour(channel, conv);
        });
      } catch (err) {
        logger.error({ err }, 'Tour booking failed');
        await channel.send('❌ An error occurred while booking. Some showings may have been booked. Check BrokerBay for details.');
      }
    } else {
      await btnInteraction.update({ content: 'Tour cancelled. Use /tour to start over.', components: [] });
    }
  } catch (err) {
    logger.error({ err }, 'Route optimization failed');
    await channel.send('❌ Failed to optimize route. Please try again.');
  }

  resetConversation(userId);
}

async function bookTour(channel: TextChannel, conv: ConversationState): Promise<void> {
  const addresses = conv.addresses!;
  const bookings: BookingConfirmation[] = [];
  const failed: FailedBooking[] = [];

  for (let i = 0; i < addresses.length; i++) {
    const address = addresses[i];
    const stopInfo = conv.proposedSchedule?.stops[i];

    try {
      await channel.send(`🔍 Searching for listing: ${address}...`);

      const listing = await searchListing(address);
      if (!listing) {
        failed.push({ address, reason: 'Listing not found in BrokerBay' });
        continue;
      }

      const targetTime = stopInfo?.arrivalTime || new Date();

      let booking: BookingConfirmation | null = null;
      try {
        booking = await bookShowing({
          listingId: listing.id,
          dateTime: targetTime,
          clientName: conv.clientName!,
          durationMinutes: conv.durationMinutes!,
        });
      } catch {
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
        await channel.send(`✅ Booked: ${address}`);
      } else {
        failed.push({ address, reason: 'No available time slots' });
        await channel.send(`⚠️ Could not book: ${address} — no available time slots`);
      }
    } catch (err) {
      logger.error({ err, address }, 'Booking failed for address');
      failed.push({ address, reason: 'Booking error' });
      await channel.send(`❌ Error booking: ${address}`);
    }
  }

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

  await channel.send(summary);
}
