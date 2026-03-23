import type { MyListing, ShowingRequest, ListingDetails } from '../types';

function escapeMarkdownV2(text: string): string {
  return text.replace(/([_*\[\]()~`>#+\-=|{}.!\\])/g, '\\$1');
}

function formatPrice(price: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'CAD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(price);
}

function formatDateTime(date: Date): string {
  return date.toLocaleString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });
}

export function formatMyListings(listings: MyListing[]): string {
  if (listings.length === 0) {
    return 'No active listings found\\.';
  }

  const lines: string[] = ['🏘 *Your Active Listings*', ''];

  for (const listing of listings) {
    const price = formatPrice(listing.price);
    lines.push(
      `• *${escapeMarkdownV2(listing.address)}*\n  ${escapeMarkdownV2(price)} \\| MLS: ${escapeMarkdownV2(listing.mlsNumber)} \\| ${listing.showingCount} showings`,
    );
  }

  return lines.join('\n');
}

export function formatPendingRequests(requests: ShowingRequest[]): string {
  if (requests.length === 0) {
    return '✅ No pending showing requests\\.';
  }

  const lines: string[] = [`📬 *Pending Showing Requests* \\(${requests.length}\\)`, ''];

  for (const req of requests) {
    lines.push(
      `🏠 *${escapeMarkdownV2(req.listingAddress)}*\n` +
        `  🕐 ${escapeMarkdownV2(formatDateTime(req.requestedTime))}\n` +
        `  👤 ${escapeMarkdownV2(req.agentName)} \\| 📞 ${escapeMarkdownV2(req.agentPhone)}\n` +
        `  🏷 Client: ${escapeMarkdownV2(req.clientName)}\n` +
        `  ID: \`${escapeMarkdownV2(req.requestId)}\``,
    );
    lines.push('');
  }

  return lines.join('\n');
}

export function formatListingDetails(details: ListingDetails): string {
  const price = formatPrice(details.price);

  const lines = [
    `🏠 *${escapeMarkdownV2(details.address)}*`,
    `MLS: ${escapeMarkdownV2(details.mlsNumber)}`,
    '',
    `💰 ${escapeMarkdownV2(price)}`,
    `📐 ${details.sqft} sqft \\| 🗓 Built ${details.yearBuilt}`,
    '',
    `👤 Agent: ${escapeMarkdownV2(details.agentName)}`,
    `📞 ${escapeMarkdownV2(details.agentPhone)}`,
  ];

  if (details.showingInstructions) {
    lines.push('', `🔑 ${escapeMarkdownV2(details.showingInstructions)}`);
  }

  return lines.join('\n');
}

export function formatApprovalResult(requestId: string, approved: boolean): string {
  if (approved) {
    return `✅ Showing request \`${escapeMarkdownV2(requestId)}\` has been *approved*\\.`;
  }
  return `❌ Showing request \`${escapeMarkdownV2(requestId)}\` has been *declined*\\.`;
}

export function formatDaySummary(
  date: string,
  requests: ShowingRequest[],
): string {
  if (requests.length === 0) {
    return `📅 No confirmed showings for ${escapeMarkdownV2(date)}\\.`;
  }

  const lines: string[] = [`📅 *Showings for ${escapeMarkdownV2(date)}*`, ''];

  const sorted = [...requests].sort(
    (a, b) => a.requestedTime.getTime() - b.requestedTime.getTime(),
  );

  for (let i = 0; i < sorted.length; i++) {
    const req = sorted[i];
    lines.push(
      `${i + 1}\\. *${escapeMarkdownV2(req.listingAddress)}*\n` +
        `   🕐 ${escapeMarkdownV2(formatDateTime(req.requestedTime))}\n` +
        `   👤 ${escapeMarkdownV2(req.agentName)} — ${escapeMarkdownV2(req.clientName)}`,
    );
  }

  return lines.join('\n');
}
