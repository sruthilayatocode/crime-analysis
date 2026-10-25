import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { Shield, CheckCircle2, XCircle, Loader2, ArrowRight, Mail, RefreshCw } from 'lucide-react';
import { authService } from '../services/authService';

export default function VerifyEmail() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || '';

  const [verifying, setVerifying] = useState(false);
  const [verified, setVerified] = useState(false);
  const [error, setError] = useState('');

  // Resend state
  const [resendEmail, setResendEmail] = useState('');
  const [resending, setResending] = useState(false);
  const [resendSuccess, setResendSuccess] = useState('');
  const [resendError, setResendError] = useState('');

  const handleVerify = async (tok) => {
    if (!tok) {
      setError('Verification token is missing. Please use the verification link sent to your email.');
      return;
    }
    setVerifying(true);
    setError('');

    try {
      await authService.verifyEmail(tok);
      setVerified(true);
    } catch (err) {
      setError(err.message || 'Email verification failed. The link may have expired or already been used.');
    } finally {
      setVerifying(false);
    }
  };

  useEffect(() => {
    if (token) {
      handleVerify(token);
    }
  }, [token]);

  const handleResend = async (e) => {
    e.preventDefault();
    if (!resendEmail) {
      setResendError('Please enter your email address.');
      return;
    }
    setResending(true);
    setResendError('');
    setResendSuccess('');

    try {
      const res = await authService.resendVerification(resendEmail.trim());
      setResendSuccess(res.message || 'If an unverified account exists, a new verification link has been sent.');
    } catch (err) {
      setResendError(err.message || 'Failed to resend verification email.');
    } finally {
      setResending(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-center py-8 px-4 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center mb-6">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 mb-3 shadow-lg shadow-cyan-500/10">
          <Shield className="w-8 h-8" />
        </div>
        <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
          Email <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">Verification</span>
        </h2>
        <p className="mt-2 text-sm text-slate-400">
          Confirming your CrimeSense account security
        </p>
      </div>

      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-800/80 shadow-2xl rounded-2xl p-6 sm:p-8">
          {verifying ? (
            <div className="py-8 text-center space-y-4">
              <Loader2 className="w-10 h-10 text-cyan-400 animate-spin mx-auto" />
              <p className="text-sm text-slate-300 font-medium">Validating verification token...</p>
            </div>
          ) : verified ? (
            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-sm flex items-start gap-3">
                <CheckCircle2 className="w-6 h-6 text-emerald-400 shrink-0 mt-0.5" />
                <div>
                  <p className="font-bold text-emerald-300 text-base">Email Verified Successfully!</p>
                  <p className="text-xs text-emerald-400/90 mt-1">
                    Your CrimeSense account is fully verified. Automated proximity alerts and citizen reporting are now active.
                  </p>
                </div>
              </div>
              <Link
                to="/app"
                className="w-full mt-4 py-3 px-4 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold rounded-xl shadow-lg shadow-cyan-500/25 flex items-center justify-center gap-2 transition"
              >
                <span>Proceed to CrimeSense App</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          ) : (
            <div className="space-y-6">
              {error && (
                <div className="p-3.5 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs sm:text-sm flex items-start gap-2">
                  <XCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                  <span>{error}</span>
                </div>
              )}

              {/* Resend Section */}
              <div className="pt-2 border-t border-slate-800">
                <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <RefreshCw className="w-3.5 h-3.5 text-cyan-400" /> Need a new verification link?
                </h3>
                <p className="text-xs text-slate-400 mb-3">
                  Enter your email address to receive a fresh verification link.
                </p>

                {resendSuccess && (
                  <div className="mb-3 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs">
                    {resendSuccess}
                  </div>
                )}
                {resendError && (
                  <div className="mb-3 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-xs">
                    {resendError}
                  </div>
                )}

                <form onSubmit={handleResend} className="space-y-3">
                  <div className="relative">
                    <Mail className="absolute left-3.5 top-3 w-4 h-4 text-slate-500" />
                    <input
                      type="email"
                      required
                      placeholder="name@example.com"
                      value={resendEmail}
                      onChange={(e) => setResendEmail(e.target.value)}
                      className="w-full pl-10 pr-4 py-2 bg-slate-950/80 border border-slate-800 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition"
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={resending}
                    className="w-full py-2.5 px-3 bg-slate-800 hover:bg-slate-700 text-cyan-300 text-xs font-semibold rounded-xl border border-slate-700 flex items-center justify-center gap-1.5 transition disabled:opacity-50"
                  >
                    {resending ? 'Sending...' : 'Resend Verification Email'}
                  </button>
                </form>
              </div>

              <div className="text-center pt-2">
                <Link to="/login" className="text-xs text-slate-400 hover:text-cyan-400 transition">
                  Return to Sign In
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
