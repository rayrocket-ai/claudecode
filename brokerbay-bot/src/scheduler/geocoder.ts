import pino from 'pino';
import { config } from '../config';

const logger = pino({ level: config.logLevel });

const GEOCODE_URL = 'https://maps.googleapis.com/maps/api/geocode/json';
const DISTANCE_MATRIX_URL = 'https://maps.googleapis.com/maps/api/distancematrix/json';

export interface GeoLocation {
  lat: number;
  lng: number;
  formattedAddress: string;
}

export interface DriveTime {
  fromIndex: number;
  toIndex: number;
  durationSeconds: number;
  durationText: string;
  distanceMeters: number;
  distanceText: string;
}

export async function geocodeAddress(address: string): Promise<GeoLocation | null> {
  const url = new URL(GEOCODE_URL);
  url.searchParams.set('address', address);
  url.searchParams.set('key', config.googleMapsApiKey);

  const response = await fetch(url.toString());
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const data: any = await response.json();

  if (data.status !== 'OK' || !data.results?.length) {
    logger.warn({ address, status: data.status }, 'Geocoding failed');
    return null;
  }

  const result = data.results[0];
  return {
    lat: result.geometry.location.lat,
    lng: result.geometry.location.lng,
    formattedAddress: result.formatted_address,
  };
}

export async function geocodeAddresses(addresses: string[]): Promise<(GeoLocation | null)[]> {
  return Promise.all(addresses.map((addr) => geocodeAddress(addr)));
}

export async function getDriveTimeMatrix(locations: GeoLocation[]): Promise<DriveTime[][]> {
  if (locations.length === 0) return [];

  const origins = locations.map((l) => `${l.lat},${l.lng}`).join('|');
  const destinations = origins; // same set of locations

  const url = new URL(DISTANCE_MATRIX_URL);
  url.searchParams.set('origins', origins);
  url.searchParams.set('destinations', destinations);
  url.searchParams.set('key', config.googleMapsApiKey);
  url.searchParams.set('departure_time', 'now');

  const response = await fetch(url.toString());
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const data: any = await response.json();

  if (data.status !== 'OK') {
    logger.error({ status: data.status }, 'Distance Matrix API failed');
    throw new Error(`Distance Matrix API error: ${data.status}`);
  }

  const matrix: DriveTime[][] = [];

  for (let i = 0; i < data.rows.length; i++) {
    const row: DriveTime[] = [];
    for (let j = 0; j < data.rows[i].elements.length; j++) {
      const element = data.rows[i].elements[j];
      if (element.status === 'OK') {
        row.push({
          fromIndex: i,
          toIndex: j,
          durationSeconds: element.duration_in_traffic?.value || element.duration.value,
          durationText: element.duration_in_traffic?.text || element.duration.text,
          distanceMeters: element.distance.value,
          distanceText: element.distance.text,
        });
      } else {
        row.push({
          fromIndex: i,
          toIndex: j,
          durationSeconds: 0,
          durationText: 'N/A',
          distanceMeters: 0,
          distanceText: 'N/A',
        });
      }
    }
    matrix.push(row);
  }

  return matrix;
}

export async function getDriveTimeBetween(
  from: GeoLocation,
  to: GeoLocation,
): Promise<DriveTime> {
  const matrix = await getDriveTimeMatrix([from, to]);
  return matrix[0][1];
}
