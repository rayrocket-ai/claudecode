export interface User {
  id: string;
  email: string;
  username: string;
  is_active: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface PlatformFollowers {
  platform: string;
  followers: number;
  change_percent: number;
}

export interface OverviewData {
  total_followers: number;
  followers_change_percent: number;
  total_views: number;
  views_change_percent: number;
  total_posts: number;
  engagement_rate: number;
  engagement_change_percent: number;
  platforms: PlatformFollowers[];
}

export interface PostMetric {
  id: string;
  platform: string;
  post_title: string | null;
  post_type: string;
  published_at: string;
  views: number;
  likes: number;
  comments: number;
  shares: number;
  engagement_rate: number;
}

export interface PostsData {
  posts: PostMetric[];
  total: number;
}

export interface GrowthPoint {
  date: string;
  followers: number;
}

export interface PlatformGrowth {
  platform: string;
  data: GrowthPoint[];
}

export interface GrowthData {
  platforms: PlatformGrowth[];
}

export interface EngagementPoint {
  date: string;
  rate: number;
}

export interface PlatformEngagement {
  platform: string;
  data: EngagementPoint[];
}

export interface EngagementData {
  platforms: PlatformEngagement[];
}

export interface PlatformStatus {
  platform: string;
  connected: boolean;
  username: string | null;
  connected_at: string | null;
  configured: boolean;
  profile_url: string | null;
}

export interface PlatformsListData {
  platforms: PlatformStatus[];
}
