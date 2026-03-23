import type { MyListing, ShowingRequest, ListingDetails } from '../types';

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
    return 'No active listings found.';
  }

  const lines: string[] = ['🏘 **Your Active Listings**', ''];

  for (const listing of listings) {
    const price = formatPrice(listing.price);
    lines.push(
      `• **${listing.address}**\n  ${price} | MLS: ${listing.mlsNumber} | ${listing.showingCount} showings`,
    );
  }

  return lines.join('\n');
}

export function formatPendingRequests(requests: ShowingRequest[]): string {
  if (requests.length === 0) {
    return '✅ No pending showing requests.';
  }

  const lines: string[] = [`📬 **Pending Showing Requests** (${requests.length})`, ''];

  for (const req of requests) {
    lines.push(
      `🏠 **${req.listingAddress}**\n` +
        `  🕐 ${formatDateTime(req.requestedTime)}\n` +
        `  👤 ${req.agentName} | 📞 ${req.agentPhone}\n` +
        `  🏷 Client: ${req.clientName}\n` +
        `  ID: \`${req.requestId}\``,
    );
    lines.push('');
  }

  return lines.join('\n');
}

export function formatListingDetails(details: ListingDetails): string {
  const price = formatPrice(details.price);

  const lines = [
    `🏠 **${details.address}**`,
    `MLS: ${details.mlsNumber}`,
    '',
    `💰 ${price}`,
    `📐 ${details.sqft} sqft | 🗓 Built ${details.yearBuilt}`,
    '',
    `👤 Agent: ${details.agentName}`,
    `📞 ${details.agentPhone}`,
  ];

  if (details.showingInstructions) {
    lines.push('', `🔑 ${details.showingInstructions}`);
  }

  return lines.join('\n');
}

export function formatApprovalResult(requestId: string, approved: boolean): string {
  if (approved) {
    return `✅ Showing request \`${requestId}\` has been **approved**.`;
  }
  return `❌ Showing request \`${requestId}\` has been **declined**.`;
}

export function formatDaySummary(date: string, requests: ShowingRequest[]): string {
  if (requests.length === 0) {
    return `📅 No confirmed showings for ${date}.`;
  }

  const lines: string[] = [`📅 **Showings for ${date}**`, ''];

  const sorted = [...requests].sort(
    (a, b) => a.requestedTime.getTime() - b.requestedTime.getTime(),
  );

  for (let i = 0; i < sorted.length; i++) {
    const req = sorted[i];
    lines.push(
      `${i + 1}. **${req.listingAddress}**\n` +
        `   🕐 ${formatDateTime(req.requestedTime)}\n` +
        `   👤 ${req.agentName} — ${req.clientName}`,
    );
  }

  return lines.join('\n');
}
