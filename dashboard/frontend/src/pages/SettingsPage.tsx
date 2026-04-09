import { useState, useEffect } from 'react';
import TopBar from '../components/layout/TopBar';
import PlatformCard from '../components/cards/PlatformCard';
import { getPlatforms, connectPlatform, disconnectPlatform } from '../api/platforms';
import type { PlatformStatus } from '../types';
import { Info, Key, ExternalLink } from 'lucide-react';
import { getPlatformName } from '../utils/platformColors';

const SETUP_LINKS: Record<string, { name: string; url: string; envKeys: string[] }> = {
  facebook: {
    name: 'Meta for Developers',
    url: 'https://developers.facebook.com/apps/',
    envKeys: ['FACEBOOK_APP_ID', 'FACEBOOK_APP_SECRET'],
  },
  instagram: {
    name: 'Meta for Developers',
    url: 'https://developers.facebook.com/apps/',
    envKeys: ['INSTAGRAM_APP_ID', 'INSTAGRAM_APP_SECRET'],
  },
  twitter: {
    name: 'Twitter Developer Portal',
    url: 'https://developer.x.com/en/portal/dashboard',
    envKeys: ['TWITTER_CLIENT_ID', 'TWITTER_CLIENT_SECRET'],
  },
  youtube: {
    name: 'Google Cloud Console',
    url: 'https://console.cloud.google.com/apis/credentials',
    envKeys: ['YOUTUBE_CLIENT_ID', 'YOUTUBE_CLIENT_SECRET'],
  },
  tiktok: {
    name: 'TikTok for Developers',
    url: 'https://developers.tiktok.com/',
    envKeys: ['TIKTOK_CLIENT_KEY', 'TIKTOK_CLIENT_SECRET'],
  },
};

export default function SettingsPage() {
  const [platforms, setPlatforms] = useState<PlatformStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [setupInfo, setSetupInfo] = useState<string | null>(null);

  const loadPlatforms = () => {
    getPlatforms()
      .then((data) => setPlatforms(data.platforms))
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadPlatforms(); }, []);

  const handleConnect = async (platform: string) => {
    // If not configured, show setup instructions
    const plat = platforms.find((p) => p.platform === platform);
    if (plat && !plat.configured) {
      setSetupInfo(platform);
      return;
    }

    setActionLoading(platform);
    try {
      const result = await connectPlatform(platform);
      if (result.oauth_url) {
        // Redirect to the platform's OAuth page
        window.location.href = result.oauth_url;
        return;
      }
      loadPlatforms();
    } catch (err: any) {
      const detail = err.response?.data?.detail ?? 'Failed to connect';
      // If the error mentions .env setup, show setup info instead
      if (detail.includes('.env')) {
        setSetupInfo(platform);
      } else {
        alert(detail);
      }
    } finally {
      setActionLoading(null);
    }
  };

  const handleDisconnect = async (platform: string) => {
    setActionLoading(platform);
    try {
      await disconnectPlatform(platform);
      loadPlatforms();
    } catch (err: any) {
      alert(err.response?.data?.detail ?? 'Failed to disconnect');
    } finally {
      setActionLoading(null);
    }
  };

  const anyConfigured = platforms.some((p) => p.configured);

  return (
    <div>
      <TopBar title="Settings" subtitle="Manage your connected social media accounts" />

      {/* Info Banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6 flex items-start gap-3">
        <Info size={20} className="text-blue-500 mt-0.5 shrink-0" />
        <div>
          <p className="text-sm font-medium text-blue-800">Connect Your Real Accounts</p>
          <p className="text-sm text-blue-600 mt-0.5">
            Click <strong>Connect</strong> on any platform to sign in with your real social media account.
            {!anyConfigured && (
              <> You'll need to set up API credentials first - click <strong>Setup</strong> on any platform for instructions.</>
            )}
          </p>
        </div>
      </div>

      {/* Setup Instructions Modal */}
      {setupInfo && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => setSetupInfo(null)}>
          <div className="bg-white rounded-2xl p-6 max-w-lg w-full shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-bold text-gray-900 mb-2">
              Connect {getPlatformName(setupInfo)}
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              To connect your {getPlatformName(setupInfo)} account, you need to create a developer app and add the API credentials to your <code className="bg-gray-100 px-1.5 py-0.5 rounded text-xs">.env</code> file.
            </p>

            <div className="bg-gray-50 rounded-xl p-4 mb-4">
              <p className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                <Key size={14} />
                Step 1: Create a Developer App
              </p>
              <a
                href={SETUP_LINKS[setupInfo]?.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 text-sm text-blue-600 hover:underline"
              >
                Go to {SETUP_LINKS[setupInfo]?.name}
                <ExternalLink size={13} />
              </a>
            </div>

            <div className="bg-gray-50 rounded-xl p-4 mb-4">
              <p className="text-sm font-medium text-gray-700 mb-2">
                Step 2: Add credentials to your .env file
              </p>
              <pre className="bg-gray-900 text-green-400 text-xs rounded-lg p-3 overflow-x-auto">
                {SETUP_LINKS[setupInfo]?.envKeys.map((k) => `${k}=your_value_here`).join('\n')}
              </pre>
            </div>

            <div className="bg-gray-50 rounded-xl p-4 mb-6">
              <p className="text-sm font-medium text-gray-700 mb-1">
                Step 3: Restart the server
              </p>
              <p className="text-xs text-gray-500">
                After adding credentials, restart the backend server and come back here to connect.
              </p>
            </div>

            <button
              onClick={() => setSetupInfo(null)}
              className="w-full bg-gray-900 text-white py-2.5 rounded-xl text-sm font-medium hover:bg-gray-800 transition-colors"
            >
              Got it
            </button>
          </div>
        </div>
      )}

      {/* Platform Cards */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {platforms.map((p) => (
            <PlatformCard
              key={p.platform}
              platform={p.platform}
              connected={p.connected}
              configured={p.configured}
              username={p.username}
              loading={actionLoading === p.platform}
              onConnect={() => handleConnect(p.platform)}
              onDisconnect={() => handleDisconnect(p.platform)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
