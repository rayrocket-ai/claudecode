import { useEffect, useState } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { getPlatformName, getPlatformColor } from '../utils/platformColors';
import client from '../api/client';

export default function OAuthCallbackPage() {
  const { platform } = useParams<{ platform: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const code = searchParams.get('code');
    const state = searchParams.get('state');
    const error = searchParams.get('error');

    if (error) {
      setStatus('error');
      setMessage(searchParams.get('error_description') ?? `Authorization was denied: ${error}`);
      return;
    }

    if (!code || !platform) {
      setStatus('error');
      setMessage('Missing authorization code. Please try connecting again.');
      return;
    }

    // Get user ID from token
    const token = localStorage.getItem('token');
    if (!token) {
      setStatus('error');
      setMessage('Not logged in. Please log in and try again.');
      return;
    }

    // Parse user ID from JWT payload
    let userId = '';
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      userId = payload.sub;
    } catch {
      setStatus('error');
      setMessage('Invalid session. Please log in again.');
      return;
    }

    // Send code to backend for token exchange
    client.get(`/platforms/${platform}/callback`, {
      params: { code, state, user_id: userId },
    })
      .then((resp) => {
        setStatus('success');
        setMessage(`Connected to ${getPlatformName(platform)} as ${resp.data.username}`);
        // Redirect to settings after a short delay
        setTimeout(() => navigate('/settings'), 2000);
      })
      .catch((err) => {
        setStatus('error');
        setMessage(err.response?.data?.detail ?? 'Failed to connect. Please try again.');
      });
  }, [platform, searchParams, navigate]);

  const color = getPlatformColor(platform ?? '');
  const name = getPlatformName(platform ?? '');

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl p-8 shadow-lg border border-gray-100 max-w-md w-full text-center">
        <div
          className="w-16 h-16 rounded-2xl flex items-center justify-center text-white font-bold text-2xl mx-auto mb-6"
          style={{ backgroundColor: color }}
        >
          {name.charAt(0)}
        </div>

        {status === 'loading' && (
          <>
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 mx-auto mb-4" style={{ borderColor: color }} />
            <h2 className="text-xl font-bold text-gray-900 mb-2">Connecting {name}...</h2>
            <p className="text-sm text-gray-500">Exchanging authorization with {name}</p>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="w-12 h-12 rounded-full bg-emerald-100 flex items-center justify-center mx-auto mb-4">
              <svg className="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-xl font-bold text-gray-900 mb-2">Connected!</h2>
            <p className="text-sm text-gray-500">{message}</p>
            <p className="text-xs text-gray-400 mt-4">Redirecting to settings...</p>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center mx-auto mb-4">
              <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h2 className="text-xl font-bold text-gray-900 mb-2">Connection Failed</h2>
            <p className="text-sm text-gray-500 mb-6">{message}</p>
            <button
              onClick={() => navigate('/settings')}
              className="px-6 py-2.5 bg-gray-900 text-white rounded-xl text-sm font-medium hover:bg-gray-800 transition-colors"
            >
              Back to Settings
            </button>
          </>
        )}
      </div>
    </div>
  );
}
