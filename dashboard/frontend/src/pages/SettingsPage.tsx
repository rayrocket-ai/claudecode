import { useState, useEffect } from 'react';
import TopBar from '../components/layout/TopBar';
import PlatformCard from '../components/cards/PlatformCard';
import { getPlatforms, connectPlatform, disconnectPlatform } from '../api/platforms';
import type { PlatformStatus } from '../types';
import { Info } from 'lucide-react';

export default function SettingsPage() {
  const [platforms, setPlatforms] = useState<PlatformStatus[]>([]);
  const [loading, setLoading] = useState(true);

  const loadPlatforms = () => {
    getPlatforms()
      .then((data) => setPlatforms(data.platforms))
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadPlatforms(); }, []);

  const handleConnect = async (platform: string) => {
    try {
      await connectPlatform(platform);
      loadPlatforms();
    } catch (err: any) {
      alert(err.response?.data?.detail ?? 'Failed to connect');
    }
  };

  const handleDisconnect = async (platform: string) => {
    try {
      await disconnectPlatform(platform);
      loadPlatforms();
    } catch (err: any) {
      alert(err.response?.data?.detail ?? 'Failed to disconnect');
    }
  };

  return (
    <div>
      <TopBar title="Settings" subtitle="Manage your connected social media accounts" />

      {/* Demo Mode Banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6 flex items-start gap-3">
        <Info size={20} className="text-blue-500 mt-0.5 shrink-0" />
        <div>
          <p className="text-sm font-medium text-blue-800">Demo Mode Active</p>
          <p className="text-sm text-blue-600 mt-0.5">
            All platforms are connected with sample data. To use real data, configure API credentials in your .env file and set DEMO_MODE=false.
          </p>
        </div>
      </div>

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
              username={p.username}
              onConnect={() => handleConnect(p.platform)}
              onDisconnect={() => handleDisconnect(p.platform)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
