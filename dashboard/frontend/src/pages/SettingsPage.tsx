import { useState, useEffect } from 'react';
import TopBar from '../components/layout/TopBar';
import PlatformCard from '../components/cards/PlatformCard';
import { getPlatforms, connectPlatform, disconnectPlatform } from '../api/platforms';
import type { PlatformStatus } from '../types';
import { getPlatformColor, getPlatformName } from '../utils/platformColors';
import { ExternalLink, X } from 'lucide-react';

const PLATFORM_HINTS: Record<string, { placeholder: string; help: string; example: string }> = {
  facebook: {
    placeholder: 'Your page name or username',
    help: 'Enter your Facebook Page name or username',
    example: 'e.g. MyBrandOfficial',
  },
  instagram: {
    placeholder: 'Your Instagram handle',
    help: 'Enter your Instagram username (without the @)',
    example: 'e.g. mybrand',
  },
  twitter: {
    placeholder: 'Your X (Twitter) handle',
    help: 'Enter your X handle (without the @)',
    example: 'e.g. MyBrand',
  },
  youtube: {
    placeholder: 'Your YouTube channel name',
    help: 'Enter your YouTube channel name or handle',
    example: 'e.g. MyBrandTV',
  },
  tiktok: {
    placeholder: 'Your TikTok username',
    help: 'Enter your TikTok username (without the @)',
    example: 'e.g. mybrand',
  },
};

export default function SettingsPage() {
  const [platforms, setPlatforms] = useState<PlatformStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [connectModal, setConnectModal] = useState<string | null>(null);
  const [usernameInput, setUsernameInput] = useState('');
  const [connectError, setConnectError] = useState('');

  const loadPlatforms = () => {
    getPlatforms()
      .then((data) => setPlatforms(data.platforms))
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadPlatforms(); }, []);

  const openConnectModal = (platform: string) => {
    setConnectModal(platform);
    setUsernameInput('');
    setConnectError('');
  };

  const handleConnect = async () => {
    if (!connectModal) return;
    if (!usernameInput.trim()) {
      setConnectError('Please enter your username');
      return;
    }

    setActionLoading(connectModal);
    setConnectError('');
    try {
      const result = await connectPlatform(connectModal, usernameInput.trim());
      if (result.oauth_url) {
        window.location.href = result.oauth_url;
        return;
      }
      setConnectModal(null);
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

      {/* Connect Modal */}
      {connectModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => setConnectModal(null)}>
          <div className="bg-white rounded-2xl p-0 max-w-md w-full shadow-2xl overflow-hidden" onClick={(e) => e.stopPropagation()}>
            {/* Modal Header */}
            <div className="p-6 pb-0">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div
                    className="w-10 h-10 rounded-xl flex items-center justify-center text-white font-bold"
                    style={{ backgroundColor: getPlatformColor(connectModal) }}
                  >
                    {getPlatformName(connectModal).charAt(0)}
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-gray-900">
                      Connect {getPlatformName(connectModal)}
                    </h3>
                    <p className="text-xs text-gray-500">{PLATFORM_HINTS[connectModal]?.help}</p>
                  </div>
                </div>
                <button onClick={() => setConnectModal(null)} className="p-1 hover:bg-gray-100 rounded-lg">
                  <X size={18} className="text-gray-400" />
                </button>
              </div>
            </div>

            {/* Modal Body */}
            <div className="px-6 pb-6">
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Your {getPlatformName(connectModal)} Username
                </label>
                <div className="flex">
                  <span className="inline-flex items-center px-3 rounded-l-xl border border-r-0 border-gray-200 bg-gray-50 text-gray-500 text-sm">
                    @
                  </span>
                  <input
                    type="text"
                    value={usernameInput}
                    onChange={(e) => { setUsernameInput(e.target.value); setConnectError(''); }}
                    onKeyDown={(e) => e.key === 'Enter' && handleConnect()}
                    placeholder={PLATFORM_HINTS[connectModal]?.placeholder}
                    className="flex-1 px-4 py-3 border border-gray-200 rounded-r-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                    autoFocus
                  />
                </div>
                <p className="text-xs text-gray-400 mt-1.5">{PLATFORM_HINTS[connectModal]?.example}</p>
              </div>

              {connectError && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
                  {connectError}
                </div>
              )}

              <button
                onClick={handleConnect}
                disabled={actionLoading === connectModal}
                className="w-full py-3 rounded-xl text-sm font-semibold text-white transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                style={{ backgroundColor: getPlatformColor(connectModal) }}
              >
                {actionLoading === connectModal ? (
                  <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                ) : (
                  <>
                    <ExternalLink size={15} />
                    Connect {getPlatformName(connectModal)}
                  </>
                )}
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
              configured={true}
              username={p.username}
              loading={actionLoading === p.platform}
              onConnect={() => openConnectModal(p.platform)}
              onDisconnect={() => handleDisconnect(p.platform)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
