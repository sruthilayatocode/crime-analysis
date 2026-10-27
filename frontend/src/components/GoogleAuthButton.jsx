import React, { useState } from 'react';
import { GoogleLogin } from '@react-oauth/google';
import { AlertCircle, Loader2, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, useLocation } from 'react-router-dom';

function GoogleIcon({ className = "w-4 h-4" }) {
  return (
    <svg className={className} viewBox="0 0 24 24">
      <path
        fill="#4285F4"
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
      />
      <path
        fill="#34A853"
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
      />
      <path
        fill="#FBBC05"
        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
      />
      <path
        fill="#EA4335"
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
      />
    </svg>
  );
}

export default function GoogleAuthButton({ onError: parentOnError, mode = 'signin' }) {
  const { googleAuth, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [loading, setLoading] = useState(false);
  const [internalError, setInternalError] = useState('');

  const rawClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';
  const clientId = rawClientId.trim();
  const isConfigured = Boolean(
    clientId &&
    clientId !== 'your_actual_google_client_id' &&
    clientId !== 'your-google-client-id.apps.googleusercontent.com' &&
    clientId !== 'your-google-oauth-client-id.apps.googleusercontent.com' &&
    clientId !== 'not-configured' &&
    !clientId.startsWith('your_') &&
    !clientId.startsWith('your-')
  );

  const from = location.state?.from?.pathname;

  const handleDemoGoogleLogin = async () => {
    setLoading(true);
    setInternalError('');
    try {
      const user = await login('user@crimesense.com', 'User@123');
      if (from) {
        navigate(from, { replace: true });
      } else if (user?.role === 'admin') {
        navigate('/admin', { replace: true });
      } else {
        navigate('/app', { replace: true });
      }
    } catch (err) {
      const errMsg = err.message || 'Demo Google sign-in failed.';
      setInternalError(errMsg);
      if (parentOnError) parentOnError(errMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleSuccess = async (credentialResponse) => {
    if (!credentialResponse?.credential) {
      setInternalError('No credential received from Google. Please try again.');
      return;
    }

    setLoading(true);
    setInternalError('');

    try {
      const data = await googleAuth(credentialResponse.credential);
      const user = data?.user || data;

      // Handle post-login redirection
      if (from) {
        navigate(from, { replace: true });
      } else if (user?.role === 'admin') {
        navigate('/admin', { replace: true });
      } else {
        navigate('/app', { replace: true });
      }
    } catch (err) {
      const errMsg = err.message || '';
      let formattedMsg = errMsg || 'Google authentication failed. Please try again.';

      if (errMsg.toLowerCase().includes('popup')) {
        formattedMsg = 'Google popup was blocked or closed. Please allow popups and try again.';
      } else if (errMsg.toLowerCase().includes('unverified') || errMsg.toLowerCase().includes('not verified')) {
        formattedMsg = 'Your Google account email is not verified. Please verify it with Google before signing in.';
      } else if (errMsg.toLowerCase().includes('deactivated')) {
        formattedMsg = 'Your account has been deactivated. Please contact support or administrator.';
      } else if (errMsg.toLowerCase().includes('network') || errMsg.toLowerCase().includes('fetch')) {
        formattedMsg = 'Network error contacting authentication server. Please check your internet connection.';
      }

      setInternalError(formattedMsg);
      if (parentOnError) {
        parentOnError(formattedMsg);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleError = () => {
    const msg = 'Google Sign-In was cancelled or popup was blocked by browser.';
    setInternalError(msg);
    if (parentOnError) {
      parentOnError(msg);
    }
  };

  // If VITE_GOOGLE_CLIENT_ID is not configured, offer active Demo Mode Google Sign-In with guidance
  if (!isConfigured) {
    return (
      <div className="w-full space-y-2.5">
        <button
          type="button"
          onClick={handleDemoGoogleLogin}
          disabled={loading}
          className="w-full py-2.5 px-4 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-100 font-medium flex items-center justify-center gap-2.5 shadow-sm transition active:scale-[0.99] text-sm group"
          title="Click to sign in with Google Demo Account"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin text-cyan-400" />
              <span>Signing in with Google Demo...</span>
            </>
          ) : (
            <>
              <GoogleIcon className="w-4 h-4" />
              <span>Continue with Google <span className="text-[11px] font-semibold text-cyan-400 bg-cyan-950/80 border border-cyan-800/60 px-1.5 py-0.5 rounded ml-1">Demo</span></span>
            </>
          )}
        </button>
        <div className="px-3 py-2 rounded-lg bg-slate-900/90 border border-slate-800 text-slate-400 text-[11px] leading-relaxed flex items-center justify-between gap-2">
          <div className="flex items-center gap-1.5 text-emerald-400">
            <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
            <span>One-click Google Demo ready</span>
          </div>
          <span className="text-[10px] text-slate-500">Live @gmail requires Google Client ID in .env</span>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full space-y-3">
      {internalError && (
        <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs flex items-start gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <span>{internalError}</span>
        </div>
      )}

      {loading ? (
        <div className="w-full py-2.5 px-4 rounded-xl bg-slate-900 border border-slate-800 text-cyan-400 text-sm font-medium flex items-center justify-center gap-2 animate-pulse">
          <Loader2 className="w-4 h-4 animate-spin" />
          <span>Authenticating with Google...</span>
        </div>
      ) : (
        <div className="w-full flex justify-center [&>div]:w-full [&_iframe]:w-full [&_iframe]:min-h-[44px]">
          <GoogleLogin
            onSuccess={handleSuccess}
            onError={handleError}
            theme="filled_black"
            shape="rectangular"
            text="continue_with"
            size="large"
            width="100%"
          />
        </div>
      )}
    </div>
  );
}
