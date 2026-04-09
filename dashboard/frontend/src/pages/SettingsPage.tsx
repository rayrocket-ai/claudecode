import { useState, useEffect } from 'react';
import TopBar from '../components/layout/TopBar';
import PlatformCard from '../components/cards/PlatformCard';
import { getPlatforms, connectPlatform, disconnectPlatform } from '../api/platforms';
import type { PlatformStatus } from '../types';
import { getPlatformColor, getPlatformName } from '../utils/platformColors';
import { X } from 'lucide-react';

const PLATFORM_HINTS: Record<string, { placeholder: string; example: string }> = {
  facebook: { placeholder: 'Your Facebook page or username', example: 'e.g. MyBrandOfficial' },
  instagram: { placeholder: 'Your Instagram handle', example: 'e.g. mybrand' },
  twitter: { placeholder: 'Your X handle', example: 'e.g. MyBrand' },
  youtube: { placeholder: 'Your YouTube channel name', example: 'e.g. MyBrandTV' },
  tiktok: { placeholder: 'Your TikTok username', example: 'e.g. mybrand' },
};

export default function SettingsPage() {
  const [platforms, setPlatforms] = useState<PlatformStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  // Manual connect modal (only shown when OAuth is not configured)
  const [manualModal, setManualModal] = useState<string | null>(null);
  const [usernameInput, setUsernameInput] = useState('');
  const [connectError, setConnectError] = useState('');

  const loadPlatforms = () => {
    getPlatforms()
      .then((data) => setPlatforms(data.platforms))
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadPlatforms(); }, []);

  const handleConnect = async (platform: string) => {
    const plat = platforms.find((p) => p.platform === platform);

    // If OAuth is configured, call connect to get the OAuth URL and redirect
    if (plat?.configured) {
      setActionLoading(platform);
      try {
        const result = await connectPlatform(platform);
        if (result.oauth_url) {
          // Redirect to the platform's login page
          window.location.href = result.oauth_url;
          return;
        }
        loadPlatforms();
      } catch (err: any) {
        alert(err.response?.data?.detail ?? 'Failed to connect');
      } finally {
        setActionLoading(null);
      }
      return;
    }

    // No OAuth configured - show manual connect modal
    setManualModal(platform);
    setUsernameInput('');
    setConnectError('');
  };

  const handleManualConnect = async () => {
    if (!manualModal || !usernameInput.trim()) {
      setConnectError('Please enter your username');
      return;
    }
    setActionLoading(manualModal);
    setConnectError('');
    try {
      await connectPlatform(manualModal, usernameInput.trim());
      setManualModal(null);
      loadPlatforms();
    } catch (err: any) {
      setConnectError(err.response?.data?.detail ?? 'Failed to connect');
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

  return (
    <div>
      <TopBar title="Settings" subtitle="Manage your connected social media accounts" />

      {/* Manual Connect Modal (fallback when OAuth not configured) */}
      {manualModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => setManualModal(null)}>
          <div className="bg-white rounded-2xl max-w-md w-full shadow-2xl overflow-hidden" onClick={(e) => e.stopPropagation()}>
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div
                    className="w-10 h-10 rounded-xl flex items-center justify-center text-white font-bold"
                    style={{ backgroundColor: getPlatformColor(manualModal) }}
                  >
                    {getPlatformName(manualModal).charAt(0)}
                  </div>
                  <h3 className="text-lg font-bold text-gray-900">
                    Connect {getPlatformName(manualModal)}
                  </h3>
                </div>
                <button onClick={() => setManualModal(null)} className="p-1 hover:bg-gray-100 rounded-lg">
                  <X size={18} className="text-gray-400" />
                </button>
              </div>

              <p className="text-sm text-gray-500 mb-4">
                Enter your {getPlatformName(manualModal)} username to connect your account.
              </p>

              <div className="mb-4">
                <div className="flex">
                  <span className="inline-flex items-center px-3 rounded-l-xl border border-r-0 border-gray-200 bg-gray-50 text-gray-500 text-sm">@</span>
                  <input
                    type="text"
                    value={usernameInput}
                    onChange={(e) => { setUsernameInput(e.target.value); setConnectError(''); }}
                    onKeyDown={(e) => e.key === 'Enter' && handleManualConnect()}
                    placeholder={PLATFORM_HINTS[manualModal]?.placeholder}
                    className="flex-1 px-4 py-3 border border-gray-200 rounded-r-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                    autoFocus
                  />
                </div>
                <p className="text-xs text-gray-400 mt-1.5">{PLATFORM_HINTS[manualModal]?.example}</p>
              </div>

              {connectError && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">{connectError}</div>
              )}

              <button
                onClick={handleManualConnect}
                disabled={actionLoading === manualModal}
                className="w-full py-3 rounded-xl text-sm font-semibold text-white transition-colors disabled:opacity-50"
                style={{ backgroundColor: getPlatformColor(manualModal) }}
              >
                {actionLoading === manualModal ? 'Connecting...' : `Connect ${getPlatformName(manualModal)}`}
              </button>
            </div>
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
