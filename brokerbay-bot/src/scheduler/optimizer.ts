import pino from 'pino';
import { config } from '../config';
import { geocodeAddresses, getDriveTimeMatrix, GeoLocation, DriveTime } from './geocoder';
import type { TourRequest, TourStop, TourSchedule, BookingConfirmation, FailedBooking } from '../types';

const logger = pino({ level: config.logLevel });

const BUFFER_MINUTES = 5;

interface OptimizedRoute {
  order: number[]; // indices into the original addresses array
  locations: GeoLocation[];
  driveTimeMatrix: DriveTime[][];
  startLocation: GeoLocation;
}

// Nearest neighbor TSP heuristic
function nearestNeighborTSP(
  startIndex: number,
  driveMatrix: DriveTime[][],
  numStops: number,
): number[] {
  const visited = new Set<number>([startIndex]);
  const route: number[] = [];
  let current = startIndex;

  while (route.length < numStops) {
    let bestNext = -1;
    let bestTime = Infinity;

    for (let i = 0; i < driveMatrix[current].length; i++) {
      if (i === startIndex && i !== current) continue; // skip start location (it's the office/home)
      if (visited.has(i)) continue;
      if (driveMatrix[current][i].durationSeconds < bestTime) {
        bestTime = driveMatrix[current][i].durationSeconds;
        bestNext = i;
      }
    }

    if (bestNext === -1) break;
    route.push(bestNext);
    visited.add(bestNext);
    current = bestNext;
  }

  return route;
}

export async function optimizeRoute(tour: TourRequest): Promise<OptimizedRoute> {
  logger.info({ addresses: tour.addresses.length }, 'Optimizing tour route');

  // Geocode all addresses + starting point
  const allAddresses = [tour.startingPoint, ...tour.addresses];
  const geoResults = await geocodeAddresses(allAddresses);

  // Check for failed geocodes
  const failedIndices: number[] = [];
  const validLocations: GeoLocation[] = [];
  const indexMap: number[] = []; // maps valid index back to original

  for (let i = 0; i < geoResults.length; i++) {
    if (geoResults[i]) {
      validLocations.push(geoResults[i]!);
      indexMap.push(i);
    } else {
      failedIndices.push(i);
      logger.warn({ address: allAddresses[i] }, 'Failed to geocode address');
    }
  }

  if (validLocations.length < 2) {
    throw new Error('Not enough valid addresses to build a route');
  }

  // Get drive time matrix
  const driveMatrix = await getDriveTimeMatrix(validLocations);

  // Run TSP from start point (index 0 in validLocations)
  const optimizedOrder = nearestNeighborTSP(0, driveMatrix, validLocations.length - 1);

  // Map back to original address indices (subtract 1 for the start point offset)
  const originalOrder = optimizedOrder.map((vi) => indexMap[vi] - 1);

  return {
    order: originalOrder,
    locations: validLocations,
    driveTimeMatrix: driveMatrix,
    startLocation: validLocations[0],
  };
}

export function buildSchedule(
  tour: TourRequest,
  optimizedRoute: OptimizedRoute,
  bookings: BookingConfirmation[],
  failedAddresses: FailedBooking[],
): TourSchedule {
  const { order, driveTimeMatrix, locations } = optimizedRoute;

  const startTimeParts = parseTimeString(tour.startTime);
  const tourDate = new Date(tour.date);
  tourDate.setHours(startTimeParts.hours, startTimeParts.minutes, 0, 0);

  let currentTime = new Date(tourDate);
  const stops: TourStop[] = [];

  for (let i = 0; i < order.length; i++) {
    const addressIndex = order[i];
    const booking = bookings.find(
      (b) => b.address.toLowerCase().includes(tour.addresses[addressIndex].toLowerCase()) ||
             tour.addresses[addressIndex].toLowerCase().includes(b.address.toLowerCase()),
    );

    if (!booking) continue;

    // Calculate drive time from previous stop (or start point)
    const fromIdx = i === 0 ? 0 : order[i - 1] + 1; // +1 because start point is at index 0
    const toIdx = addressIndex + 1;
    const driveSeconds = driveTimeMatrix[fromIdx]?.[toIdx]?.durationSeconds || 0;
    const driveMinutes = Math.ceil(driveSeconds / 60);

    // Add drive time + buffer
    if (i > 0) {
      currentTime = new Date(currentTime.getTime() + (driveMinutes + BUFFER_MINUTES) * 60 * 1000);
    }

    const arrivalTime = new Date(currentTime);
    const departureTime = new Date(
      currentTime.getTime() + tour.durationMinutes * 60 * 1000,
    );

    stops.push({
      ...booking,
      stopNumber: i + 1,
      arrivalTime,
      departureTime,
      driveTimeFromPrevious: driveMinutes,
    });

    currentTime = departureTime;
  }

  const totalMinutes = stops.length > 0
    ? Math.ceil((stops[stops.length - 1].departureTime.getTime() - tourDate.getTime()) / (60 * 1000))
    : 0;

  return {
    stops,
    totalDurationMinutes: totalMinutes,
    clientName: tour.clientName,
    date: tourDate,
    startingPoint: tour.startingPoint,
    failedAddresses,
  };
}

function parseTimeString(timeStr: string): { hours: number; minutes: number } {
  const normalized = timeStr.trim().toLowerCase();
  const match = normalized.match(/^(\d{1,2})(?::(\d{2}))?\s*(am|pm)?$/);

  if (!match) {
    throw new Error(`Cannot parse time: ${timeStr}`);
  }

  let hours = parseInt(match[1], 10);
  const minutes = parseInt(match[2] || '0', 10);
  const period = match[3];

  if (period === 'pm' && hours !== 12) hours += 12;
  if (period === 'am' && hours === 12) hours = 0;

  return { hours, minutes };
}

export function parseTimeWindow(input: string): { startTime: string; endTime: string } {
  const parts = input.split(/\s*[-–—]\s*/);
  if (parts.length !== 2) {
    throw new Error('Please provide a time window like "10am - 4pm"');
  }
  return { startTime: parts[0].trim(), endTime: parts[1].trim() };
}

// Try alternative time slots: +30, -30, +60 minutes
export function getAlternativeSlots(dateTime: Date): Date[] {
  return [
    new Date(dateTime.getTime() + 30 * 60 * 1000),
    new Date(dateTime.getTime() - 30 * 60 * 1000),
    new Date(dateTime.getTime() + 60 * 60 * 1000),
  ];
}
