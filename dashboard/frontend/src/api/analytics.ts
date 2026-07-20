import client from './client';
import type { EngagementData, GrowthData, OverviewData, PostsData } from '../types';

export async function getOverview(): Promise<OverviewData> {
  const { data } = await client.get<OverviewData>('/analytics/overview');
  return data;
}

export async function getPosts(params?: {
  platform?: string;
  sort_by?: string;
  limit?: number;
  offset?: number;
}): Promise<PostsData> {
  const { data } = await client.get<PostsData>('/analytics/posts', { params });
  return data;
}

export async function getGrowth(params?: {
  platform?: string;
  days?: number;
}): Promise<GrowthData> {
  const { data } = await client.get<GrowthData>('/analytics/growth', { params });
  return data;
}

export async function getEngagement(params?: {
  platform?: string;
  days?: number;
}): Promise<EngagementData> {
  const { data } = await client.get<EngagementData>('/analytics/engagement', { params });
  return data;
}
