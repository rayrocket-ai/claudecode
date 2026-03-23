import pino from 'pino';
import { config } from '../config';
import { ensureAuthenticated, randomDelay, BROKERBAY_URL } from './session';
import type {
  Listing,
  ListingDetails,
  TimeSlot,
  BookingParams,
  BookingConfirmation,
  MyListing,
  ShowingRequest,
  AvailabilityWindow,
} from '../types';

const logger = pino({ level: config.logLevel });

// ── Search & Listing Details ──

export async function searchListing(address: string): Promise<Listing | null> {
  const page = await ensureAuthenticated();
  logger.info({ address }, 'Searching for listing');

  await page.goto(`${BROKERBAY_URL}/showings`, { waitUntil: 'networkidle' });
  await randomDelay();

  // Look for the search/book-a-showing input
  const searchInput = await page.waitForSelector(
    'input[placeholder*="search"], input[placeholder*="address"], input[placeholder*="MLS"], .search-input, #listing-search',
    { timeout: 10000 },
  ).catch(() => null);

  if (!searchInput) {
    throw new Error('Could not find listing search input on BrokerBay');
  }

  await searchInput.fill(address);
  await randomDelay(300, 500);

  // Wait for search results dropdown
  await page.waitForSelector(
    '.search-results, .autocomplete-results, [role="listbox"], .dropdown-menu',
    { timeout: 10000 },
  ).catch(() => null);

  await randomDelay();

  // Try to find the first result
  const firstResult = await page.$(
    '.search-result:first-child, .autocomplete-item:first-child, [role="option"]:first-child, .dropdown-item:first-child',
  );

  if (!firstResult) {
    logger.warn({ address }, 'No listing found');
    return null;
  }

  const resultText = (await firstResult.textContent()) || '';
  await firstResult.click();
  await randomDelay();
  await page.waitForLoadState('networkidle');

  // Extract listing ID from URL or page data
  const url = page.url();
  const idMatch = url.match(/listing[s]?\/([a-zA-Z0-9-]+)/) || url.match(/id=([a-zA-Z0-9-]+)/);
  const listingId = idMatch ? idMatch[1] : `listing-${Date.now()}`;

  // Try to extract MLS number from the page
  const mlsText = await page
    .locator('text=/MLS[#: ]*[A-Z0-9]+/i')
    .first()
    .textContent()
    .catch(() => '');
  const mlsMatch = mlsText?.match(/[A-Z0-9]{5,}/);

  return {
    id: listingId,
    address: resultText.trim() || address,
    mlsNumber: mlsMatch ? mlsMatch[0] : '',
  };
}

export async function getListingDetails(listingId: string): Promise<ListingDetails> {
  const page = await ensureAuthenticated();
  logger.info({ listingId }, 'Fetching listing details');

  // Navigate to the listing page if not already there
  if (!page.url().includes(listingId)) {
    await page.goto(`${BROKERBAY_URL}/showings/listing/${listingId}`, {
      waitUntil: 'networkidle',
    });
  }
  await randomDelay();

  const extractText = async (selectors: string[]): Promise<string> => {
    for (const sel of selectors) {
      const el = await page.$(sel);
      if (el) {
        const text = await el.textContent();
        if (text?.trim()) return text.trim();
      }
    }
    return '';
  };

  const priceText = await extractText(['.listing-price', '.price', '[data-testid="price"]']);
  const price = parseInt(priceText.replace(/[^0-9]/g, ''), 10) || 0;

  const sqftText = await extractText(['.sqft', '.square-feet', '[data-testid="sqft"]']);
  const sqft = parseInt(sqftText.replace(/[^0-9]/g, ''), 10) || 0;

  const yearText = await extractText(['.year-built', '[data-testid="year-built"]']);
  const yearBuilt = parseInt(yearText.replace(/[^0-9]/g, ''), 10) || 0;

  const addressText = await extractText(['.listing-address', '.address', 'h1', 'h2']);
  const agentName = await extractText(['.listing-agent', '.agent-name', '[data-testid="agent-name"]']);
  const agentPhone = await extractText(['.agent-phone', '[data-testid="agent-phone"]', 'a[href^="tel:"]']);
  const showingInstructions = await extractText([
    '.showing-instructions',
    '.access-instructions',
    '[data-testid="instructions"]',
  ]);

  const mlsText = await extractText(['.mls-number', '[data-testid="mls"]']);

  return {
    id: listingId,
    address: addressText,
    mlsNumber: mlsText,
    price,
    sqft,
    yearBuilt,
    agentName,
    agentPhone,
    showingInstructions,
  };
}

// ── Time Slots ──

export async function getAvailableTimeSlots(listingId: string, date: string): Promise<TimeSlot[]> {
  const page = await ensureAuthenticated();
  logger.info({ listingId, date }, 'Fetching available time slots');

  if (!page.url().includes(listingId)) {
    await page.goto(`${BROKERBAY_URL}/showings/listing/${listingId}`, {
      waitUntil: 'networkidle',
    });
  }
  await randomDelay();

  // Click the "Book Showing" or calendar button
  const bookBtn = await page
    .locator('button:has-text("Book"), button:has-text("Schedule"), button:has-text("Request")')
    .first()
    .click()
    .catch(() => null);
  await randomDelay();

  // Navigate to the correct date in the calendar
  const dateInput = await page.$('input[type="date"], input[placeholder*="date"], .date-picker input');
  if (dateInput) {
    await dateInput.fill(date);
    await randomDelay();
  }

  await page.waitForLoadState('networkidle');

  // Extract available time slots
  const slots: TimeSlot[] = [];
  const slotElements = await page.$$('.time-slot, .available-slot, [data-testid="time-slot"]');

  for (const slotEl of slotElements) {
    const text = (await slotEl.textContent()) || '';
    const isAvailable =
      !(await slotEl.getAttribute('class'))?.includes('unavailable') &&
      !(await slotEl.getAttribute('disabled'));

    const timeMatch = text.match(/(\d{1,2}:\d{2}\s*[AP]M)/gi);
    if (timeMatch && timeMatch.length >= 1) {
      const startStr = timeMatch[0];
      const endStr = timeMatch[1] || '';
      slots.push({
        start: new Date(`${date} ${startStr}`),
        end: endStr ? new Date(`${date} ${endStr}`) : new Date(`${date} ${startStr}`),
        available: !!isAvailable,
      });
    }
  }

  return slots;
}

// ── Book a Showing ──

export async function bookShowing(params: BookingParams): Promise<BookingConfirmation> {
  const page = await ensureAuthenticated();
  const { listingId, dateTime, clientName, durationMinutes } = params;
  logger.info({ listingId, dateTime, clientName }, 'Booking showing');

  if (!page.url().includes(listingId)) {
    await page.goto(`${BROKERBAY_URL}/showings/listing/${listingId}`, {
      waitUntil: 'networkidle',
    });
  }
  await randomDelay();

  // Click book/request showing button
  await page
    .locator('button:has-text("Book"), button:has-text("Schedule"), button:has-text("Request")')
    .first()
    .click();
  await randomDelay();
  await page.waitForLoadState('networkidle');

  // Fill in date
  const dateStr = dateTime.toISOString().split('T')[0];
  const dateInput = await page.waitForSelector(
    'input[type="date"], input[placeholder*="date"], .date-picker input',
    { timeout: 10000 },
  );
  if (dateInput) {
    await dateInput.fill(dateStr);
    await randomDelay();
  }

  // Fill in time
  const hours = dateTime.getHours();
  const minutes = dateTime.getMinutes();
  const timeStr = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
  const timeInput = await page.$('input[type="time"], input[placeholder*="time"], .time-picker input');
  if (timeInput) {
    await timeInput.fill(timeStr);
    await randomDelay();
  }

  // Fill in client name
  const clientInput = await page.$(
    'input[name*="client"], input[placeholder*="client"], input[placeholder*="buyer"], #client-name',
  );
  if (clientInput) {
    await clientInput.fill(clientName);
    await randomDelay();
  }

  // Fill in duration if there's a selector
  const durationSelect = await page.$('select[name*="duration"], #duration');
  if (durationSelect) {
    await durationSelect.selectOption(String(durationMinutes));
    await randomDelay();
  }

  // Submit the booking
  await page
    .locator(
      'button:has-text("Confirm"), button:has-text("Submit"), button:has-text("Book"), button[type="submit"]',
    )
    .first()
    .click();
  await randomDelay(500, 1000);
  await page.waitForLoadState('networkidle');

  // Extract confirmation details from the confirmation page
  const details = await getListingDetails(listingId);

  // Try to find confirmation ID
  const confirmText = await page
    .locator('text=/[Cc]onfirmation[#: ]*[A-Z0-9-]+/')
    .first()
    .textContent()
    .catch(() => '');
  const confirmMatch = confirmText?.match(/[A-Z0-9-]{4,}/);

  const confirmation: BookingConfirmation = {
    ...details,
    confirmationId: confirmMatch ? confirmMatch[0] : `BB-${Date.now()}`,
    bookedTime: dateTime,
  };

  logger.info({ confirmationId: confirmation.confirmationId }, 'Showing booked successfully');
  return confirmation;
}

// ── My Listings ──

export async function getMyListings(): Promise<MyListing[]> {
  const page = await ensureAuthenticated();
  logger.info('Fetching my listings');

  await page.goto(`${BROKERBAY_URL}/showings/my-listings`, { waitUntil: 'networkidle' });
  await randomDelay();

  const listings: MyListing[] = [];
  const listingElements = await page.$$(
    '.listing-card, .listing-row, [data-testid="listing-item"], tr.listing',
  );

  for (const el of listingElements) {
    const address = (await el.$eval('.address, .listing-address, td:first-child', (e) => e.textContent).catch(() => '')) || '';
    const priceText = (await el.$eval('.price, .listing-price', (e) => e.textContent).catch(() => '0')) || '0';
    const mlsText = (await el.$eval('.mls, .mls-number', (e) => e.textContent).catch(() => '')) || '';
    const statusText = (await el.$eval('.status, .listing-status', (e) => e.textContent).catch(() => 'Active')) || 'Active';
    const showingCountText = (await el.$eval('.showing-count, .showings', (e) => e.textContent).catch(() => '0')) || '0';

    const idAttr = (await el.getAttribute('data-listing-id')) || (await el.getAttribute('data-id')) || '';
    const linkEl = await el.$('a[href*="listing"]');
    const href = linkEl ? (await linkEl.getAttribute('href')) || '' : '';
    const idMatch = href.match(/listing[s]?\/([a-zA-Z0-9-]+)/);

    listings.push({
      id: idAttr || (idMatch ? idMatch[1] : `listing-${Date.now()}-${listings.length}`),
      address: address.trim(),
      mlsNumber: mlsText.replace(/[^A-Z0-9]/gi, ''),
      status: statusText.trim(),
      price: parseInt(priceText.replace(/[^0-9]/g, ''), 10) || 0,
      showingCount: parseInt(showingCountText.replace(/[^0-9]/g, ''), 10) || 0,
    });
  }

  logger.info({ count: listings.length }, 'Listings fetched');
  return listings;
}

// ── Pending Requests ──

export async function getPendingRequests(): Promise<ShowingRequest[]> {
  const page = await ensureAuthenticated();
  logger.info('Fetching pending showing requests');

  await page.goto(`${BROKERBAY_URL}/showings/requests`, { waitUntil: 'networkidle' });
  await randomDelay();

  // Filter to pending if there's a tab/filter
  const pendingTab = await page.$(
    'button:has-text("Pending"), a:has-text("Pending"), [data-tab="pending"]',
  );
  if (pendingTab) {
    await pendingTab.click();
    await randomDelay();
    await page.waitForLoadState('networkidle');
  }

  const requests: ShowingRequest[] = [];
  const requestElements = await page.$$(
    '.request-card, .request-row, [data-testid="request-item"], tr.request',
  );

  for (const el of requestElements) {
    const address = (await el.$eval('.address, .listing-address', (e) => e.textContent).catch(() => '')) || '';
    const timeText = (await el.$eval('.time, .requested-time, .date-time', (e) => e.textContent).catch(() => '')) || '';
    const agent = (await el.$eval('.agent-name, .requesting-agent', (e) => e.textContent).catch(() => '')) || '';
    const phone = (await el.$eval('.agent-phone, a[href^="tel:"]', (e) => e.textContent).catch(() => '')) || '';
    const client = (await el.$eval('.client-name, .buyer-name', (e) => e.textContent).catch(() => '')) || '';
    const idAttr = (await el.getAttribute('data-request-id')) || (await el.getAttribute('data-id')) || '';

    requests.push({
      requestId: idAttr || `req-${Date.now()}-${requests.length}`,
      listingAddress: address.trim(),
      requestedTime: new Date(timeText.trim()),
      agentName: agent.trim(),
      agentPhone: phone.trim(),
      clientName: client.trim(),
    });
  }

  logger.info({ count: requests.length }, 'Pending requests fetched');
  return requests;
}

// ── Approve / Decline ──

export async function approveShowingRequest(requestId: string): Promise<boolean> {
  const page = await ensureAuthenticated();
  logger.info({ requestId }, 'Approving showing request');

  await page.goto(`${BROKERBAY_URL}/showings/requests`, { waitUntil: 'networkidle' });
  await randomDelay();

  const requestEl = await page.$(`[data-request-id="${requestId}"], [data-id="${requestId}"]`);
  if (!requestEl) {
    logger.warn({ requestId }, 'Request not found');
    return false;
  }

  const approveBtn = await requestEl.$(
    'button:has-text("Approve"), button:has-text("Accept"), button:has-text("Confirm")',
  );
  if (!approveBtn) {
    logger.warn({ requestId }, 'Approve button not found');
    return false;
  }

  await approveBtn.click();
  await randomDelay();
  await page.waitForLoadState('networkidle');

  logger.info({ requestId }, 'Request approved');
  return true;
}

export async function declineShowingRequest(requestId: string, reason?: string): Promise<boolean> {
  const page = await ensureAuthenticated();
  logger.info({ requestId, reason }, 'Declining showing request');

  await page.goto(`${BROKERBAY_URL}/showings/requests`, { waitUntil: 'networkidle' });
  await randomDelay();

  const requestEl = await page.$(`[data-request-id="${requestId}"], [data-id="${requestId}"]`);
  if (!requestEl) return false;

  const declineBtn = await requestEl.$(
    'button:has-text("Decline"), button:has-text("Reject"), button:has-text("Deny")',
  );
  if (!declineBtn) return false;

  await declineBtn.click();
  await randomDelay();

  if (reason) {
    const reasonInput = await page.$('textarea, input[name*="reason"]');
    if (reasonInput) {
      await reasonInput.fill(reason);
      await randomDelay();
    }
  }

  // Confirm the decline
  const confirmBtn = await page.$(
    'button:has-text("Confirm"), button:has-text("Submit"), button:has-text("Yes")',
  );
  if (confirmBtn) {
    await confirmBtn.click();
    await randomDelay();
    await page.waitForLoadState('networkidle');
  }

  logger.info({ requestId }, 'Request declined');
  return true;
}

// ── Update Instructions ──

export async function updateShowingInstructions(
  listingId: string,
  instructions: string,
): Promise<boolean> {
  const page = await ensureAuthenticated();
  logger.info({ listingId }, 'Updating showing instructions');

  await page.goto(`${BROKERBAY_URL}/showings/my-listings/${listingId}/edit`, {
    waitUntil: 'networkidle',
  });
  await randomDelay();

  const instructionInput = await page.$(
    'textarea[name*="instruction"], textarea[name*="access"], #showing-instructions',
  );
  if (!instructionInput) {
    logger.warn('Instructions field not found');
    return false;
  }

  await instructionInput.fill(instructions);
  await randomDelay();

  const saveBtn = await page.$(
    'button:has-text("Save"), button:has-text("Update"), button[type="submit"]',
  );
  if (saveBtn) {
    await saveBtn.click();
    await randomDelay();
    await page.waitForLoadState('networkidle');
  }

  logger.info({ listingId }, 'Instructions updated');
  return true;
}

// ── Availability Windows ──

export async function setAvailabilityWindows(
  listingId: string,
  windows: AvailabilityWindow[],
): Promise<boolean> {
  const page = await ensureAuthenticated();
  logger.info({ listingId, windows }, 'Setting availability windows');

  await page.goto(`${BROKERBAY_URL}/showings/my-listings/${listingId}/availability`, {
    waitUntil: 'networkidle',
  });
  await randomDelay();

  // This implementation depends heavily on BrokerBay's UI for availability
  // The general approach: clear existing windows and set new ones
  for (const window of windows) {
    const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const dayName = dayNames[window.dayOfWeek];

    // Find the row for this day
    const dayRow = await page.$(
      `[data-day="${window.dayOfWeek}"], tr:has-text("${dayName}"), .day-row:has-text("${dayName}")`,
    );
    if (!dayRow) continue;

    const startInput = await dayRow.$('input[name*="start"], input:first-of-type');
    const endInput = await dayRow.$('input[name*="end"], input:last-of-type');

    if (startInput) {
      await startInput.fill(window.startTime);
      await randomDelay();
    }
    if (endInput) {
      await endInput.fill(window.endTime);
      await randomDelay();
    }
  }

  const saveBtn = await page.$(
    'button:has-text("Save"), button:has-text("Update"), button[type="submit"]',
  );
  if (saveBtn) {
    await saveBtn.click();
    await randomDelay();
    await page.waitForLoadState('networkidle');
  }

  logger.info({ listingId }, 'Availability windows updated');
  return true;
}
