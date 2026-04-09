import { Check, Plus, ExternalLink, AlertCircle } from 'lucide-react';
import { getPlatformColor, getPlatformName, getPlatformLight } from '../../utils/platformColors';

interface PlatformCardProps {
  platform: string;
  connected: boolean;
  configured: boolean;
  username?: string | null;
  loading?: boolean;
  onConnect: () => void;
  onDisconnect: () => void;
}

export default function PlatformCard({ platform, connected, configured, username, loading, onConnect, onDisconnect }: PlatformCardProps) {
  const color = getPlatformColor(platform);
  const name = getPlatformName(platform);
  const light = getPlatformLight(platform);

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
      <div className="flex items-center gap-4 mb-4">
        <div className="w-12 h-12 rounded-xl flex items-center justify-center text-white font-bold text-lg" style={{ backgroundColor: color }}>
          {name.charAt(0)}
        </div>
        <div>
          <h3 className="font-semibold text-gray-900">{name}</h3>
          {connected && username ? (
            <p className="text-sm text-gray-500">{username}</p>
          ) : !connected && !configured ? (
            <p className="text-xs text-amber-600 flex items-center gap-1">
              <AlertCircle size={11} />
              API keys required
            </p>
          ) : !connected ? (
            <p className="text-sm text-gray-400">Ready to connect</p>
          ) : null}
        </div>
      </div>

      <div className="flex items-center justify-between">
        <span
          className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium"
          style={{
            backgroundColor: connected ? light : '#F3F4F6',
            color: connected ? color : '#6B7280',
          }}
        >
          {connected ? (
            <>
              <Check size={12} />
              Connected
            </>
          ) : (
            'Not Connected'
          )}
        </span>

        {connected ? (
          <button
            onClick={onDisconnect}
            disabled={loading}
            className="px-4 py-2 rounded-lg text-sm font-medium text-red-600 hover:bg-red-50 transition-colors disabled:opacity-50"
          >
            Disconnect
          </button>
        ) : (
          <button
            onClick={onConnect}
            disabled={loading}
            className="px-4 py-2 rounded-lg text-sm font-medium text-white hover:opacity-90 transition-colors disabled:opacity-50 flex items-center gap-1.5"
            style={{ backgroundColor: configured ? color : '#9CA3AF' }}
          >
            {loading ? (
              <span className="animate-spin rounded-full h-3.5 w-3.5 border-b-2 border-white" />
            ) : configured ? (
              <>
                <ExternalLink size={14} />
                Connect
              </>
            ) : (
              <>
                <Plus size={14} />
                Setup
              </>
            )}
          </button>
        )}
      </div>
    </div>
  );
}
