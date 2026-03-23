// ── Core Listing Types ──

export interface Listing {
  id: string;
  address: string;
  mlsNumber: string;
}

export interface ListingDetails extends Listing {
  price: number;
  sqft: number;
  yearBuilt: number;
  agentName: string;
  agentPhone: string;
  showingInstructions: string;
}

// ── Booking Types ──

export interface BookingParams {
  listingId: string;
  dateTime: Date;
  clientName: string;
  durationMinutes: number;
}

export interface BookingConfirmation extends ListingDetails {
  confirmationId: string;
  bookedTime: Date;
  driveTimeFromPrevious?: number;
}

export interface TourStop extends BookingConfirmation {
  stopNumber: number;
  arrivalTime: Date;
  departureTime: Date;
}

// ── Showing Request Types ──

export interface ShowingRequest {
  requestId: string;
  listingAddress: string;
  requestedTime: Date;
  agentName: string;
  agentPhone: string;
  clientName: string;
}

// ── My Listing Types ──

export interface MyListing extends Listing {
  status: string;
  price: number;
  showingCount: number;
}

export interface AvailabilityWindow {
  dayOfWeek: number; // 0=Sunday, 6=Saturday
  startTime: string; // "09:00"
  endTime: string;   // "17:00"
}

// ── Time Slot Types ──

export interface TimeSlot {
  start: Date;
  end: Date;
  available: boolean;
}

// ── Tour Types ──

export interface TourRequest {
  addresses: string[];
  date: string;
  startTime: string;
  endTime: string;
  clientName: string;
  startingPoint: string;
  durationMinutes: number;
}

export interface TourSchedule {
  stops: TourStop[];
  totalDurationMinutes: number;
  clientName: string;
  date: Date;
  startingPoint: string;
  failedAddresses: FailedBooking[];
}

export interface FailedBooking {
  address: string;
  reason: string;
}

// ── Messenger Interface (abstraction for future WhatsApp/Discord) ──

export interface IMessenger {
  sendMessage(chatId: string | number, text: string, parseMode?: string): Promise<void>;
  sendPhoto(chatId: string | number, photo: string | Buffer, caption?: string): Promise<void>;
  sendButtons(
    chatId: string | number,
    text: string,
    buttons: InlineButton[][],
    parseMode?: string,
  ): Promise<void>;
}

export interface InlineButton {
  text: string;
  callbackData: string;
}

// ── Conversation State ──

export type ConversationStep =
  | 'idle'
  | 'awaiting_addresses'
  | 'awaiting_date'
  | 'awaiting_time_window'
  | 'awaiting_client_name'
  | 'awaiting_starting_point'
  | 'awaiting_duration'
  | 'awaiting_confirmation';

export interface ConversationState {
  step: ConversationStep;
  addresses?: string[];
  date?: string;
  startTime?: string;
  endTime?: string;
  clientName?: string;
  startingPoint?: string;
  durationMinutes?: number;
  proposedSchedule?: TourSchedule;
}
