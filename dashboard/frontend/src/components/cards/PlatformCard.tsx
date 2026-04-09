import { Check, Plus } from 'lucide-react';
import { getPlatformColor, getPlatformName, getPlatformLight } from '../../utils/platformColors';

interface PlatformCardProps {
  platform: string;
  connected: boolean;
  username?: string | null;
  onConnect: () => void;
  onDisconnect: () => void;
}

export default function PlatformCard({ platform, connected, username, onConnect, onDisconnect }: PlatformCardProps) {
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
          {connected && username && (
            <p className="text-sm text-gray-500">{username}</p>
          )}
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

        <button
          onClick={connected ? onDisconnect : onConnect}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            connected
              ? 'text-red-600 hover:bg-red-50'
              : 'text-white hover:opacity-90'
          }`}
          style={connected ? {} : { backgroundColor: color }}
        >
          {connected ? 'Disconnect' : (
            <span className="flex items-center gap-1">
              <Plus size={14} />
              Connect
            </span>
          )}
        </button>
      </div>
    </div>
  );
}
