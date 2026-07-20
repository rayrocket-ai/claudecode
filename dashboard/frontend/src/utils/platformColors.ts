export const PLATFORM_COLORS: Record<string, { primary: string; light: string; name: string }> = {
  facebook: { primary: '#1877F2', light: '#E7F3FF', name: 'Facebook' },
  instagram: { primary: '#E4405F', light: '#FFEEF1', name: 'Instagram' },
  twitter: { primary: '#1DA1F2', light: '#E8F5FD', name: 'X (Twitter)' },
  youtube: { primary: '#FF0000', light: '#FFE8E8', name: 'YouTube' },
  tiktok: { primary: '#69C9D0', light: '#E8F8F9', name: 'TikTok' },
};

export const getPlatformColor = (platform: string): string =>
  PLATFORM_COLORS[platform]?.primary ?? '#6B7280';

export const getPlatformName = (platform: string): string =>
  PLATFORM_COLORS[platform]?.name ?? platform;

export const getPlatformLight = (platform: string): string =>
  PLATFORM_COLORS[platform]?.light ?? '#F3F4F6';
