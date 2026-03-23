import type { TourSchedule, TourStop } from '../types';

// Telegram MarkdownV2 requires escaping these characters
function escapeMarkdownV2(text: string): string {
  return text.replace(/([_*\[\]()~`>#+\-=|{}.!\\])/g, '\\$1');
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });
}

function formatDate(date: Date): string {
  return date.toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  });
}

function formatPrice(price: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'CAD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(price);
}

const STOP_EMOJIS = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟'];
const SEPARATOR = '━━━━━━━━━━━━━━━━━━━━━━━';

function formatStop(stop: TourStop, isFirst: boolean): string {
  const emoji = STOP_EMOJIS[stop.stopNumber - 1] || `${stop.stopNumber}.`;
  const arrival = formatTime(stop.arrivalTime);
  const departure = formatTime(stop.departureTime);
  const price = formatPrice(stop.price);
  const driveLabel = isFirst ? 'Drive from start' : 'Drive from previous';
  const driveTime = stop.driveTimeFromPrevious || 0;

  const lines = [
    `${emoji}  *${escapeMarkdownV2(stop.address)}*`,
    `🕙 ${escapeMarkdownV2(arrival)} – ${escapeMarkdownV2(departure)}`,
    `💰 ${escapeMarkdownV2(price)} \\| 📐 ${escapeMarkdownV2(String(stop.sqft))} sqft \\| 🗓 Built ${stop.yearBuilt}`,
  ];

  if (stop.showingInstructions) {
    lines.push(`🔑 Access: ${escapeMarkdownV2(stop.showingInstructions)}`);
  }

  if (stop.agentName) {
    let agentLine = `👤 Agent: ${escapeMarkdownV2(stop.agentName)}`;
    if (stop.agentPhone) {
      agentLine += ` \\| 📞 ${escapeMarkdownV2(stop.agentPhone)}`;
    }
    lines.push(agentLine);
  }

  lines.push(`🚗 ${escapeMarkdownV2(driveLabel)}: ${driveTime} min`);

  return lines.join('\n');
}

export function formatTourSummary(schedule: TourSchedule): string {
  const lines: string[] = [];

  lines.push(`🏠 *SHOWING TOUR* — ${escapeMarkdownV2(schedule.clientName)}`);
  lines.push(`📅 ${escapeMarkdownV2(formatDate(schedule.date))}`);
  lines.push(`🚀 Start: ${escapeMarkdownV2(schedule.startingPoint)}`);
  lines.push(SEPARATOR);

  for (let i = 0; i < schedule.stops.length; i++) {
    lines.push(formatStop(schedule.stops[i], i === 0));
    lines.push(SEPARATOR);
  }

  const totalHours = Math.floor(schedule.totalDurationMinutes / 60);
  const totalMins = schedule.totalDurationMinutes % 60;
  const totalStr = totalHours > 0 ? `${totalHours}h ${totalMins}min` : `${totalMins}min`;
  lines.push(`⏱ Total tour: ~${escapeMarkdownV2(totalStr)}`);

  if (schedule.failedAddresses.length > 0) {
    lines.push('');
    lines.push('⚠️ *Could not book:*');
    for (const failed of schedule.failedAddresses) {
      lines.push(`  • ${escapeMarkdownV2(failed.address)}: ${escapeMarkdownV2(failed.reason)}`);
    }
  } else {
    lines.push('✅ All showings confirmed');
  }

  return lines.join('\n');
}

export function formatProposedSchedule(schedule: TourSchedule): string {
  const lines: string[] = [];

  lines.push(`📋 *Proposed Tour Schedule* — ${escapeMarkdownV2(schedule.clientName)}`);
  lines.push(`📅 ${escapeMarkdownV2(formatDate(schedule.date))}`);
  lines.push('');

  for (const stop of schedule.stops) {
    const time = formatTime(stop.arrivalTime);
    const drive = stop.driveTimeFromPrevious || 0;
    lines.push(
      `${stop.stopNumber}\\. ${escapeMarkdownV2(stop.address)} — ${escapeMarkdownV2(time)} \\(${drive} min drive\\)`,
    );
  }

  lines.push('');
  lines.push('Confirm to book all showings?');

  return lines.join('\n');
}
