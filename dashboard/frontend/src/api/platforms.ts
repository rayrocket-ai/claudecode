import client from './client';
import type { PlatformsListData } from '../types';

export async function getPlatforms(): Promise<PlatformsListData> {
  const { data } = await client.get<PlatformsListData>('/platforms');
  return data;
}

export async function connectPlatform(platform: string): Promise<{ oauth_url?: string; message?: string; platform: string }> {
  const { data } = await client.post(`/platforms/${platform}/connect`);
  return data;
}

export async function disconnectPlatform(platform: string): Promise<{ message: string; platform: string }> {
  const { data } = await client.post(`/platforms/${platform}/disconnect`);
  return data;
}
