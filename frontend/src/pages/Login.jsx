import React, { useState } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Shield, Lock, Mail, Eye, EyeOff, AlertCircle, ArrowRight, CheckCircle2 } from 'lucide-react';
import GoogleAuthButton from '../components/GoogleAuthButton';


export default function Login() {
  const { login, googleAuth } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const from = location.state?.from?.pathname;

  const handleLoginSuccess = (user) => {
    if (from) {
      navigate(from, { replace: true });
    } else if (user.role === 'admin') {
      navigate('/admin', { replace: true });
    } else {
      navigate('/app', { replace: true });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please fill in both email and password.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const user = await login(email, password);
      handleLoginSuccess(user);
    } catch (err) {
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSuccess = async (credentialResponse) => {
    if (!credentialResponse?.credential) return;
    setLoading(true);
    setError('');
    try {
      const user = await googleAuth(credentialResponse.credential);
      handleLoginSuccess(user);
    } catch (err) {
      setError(err.message || 'Google authentication failed');
    } finally {
      setLoading(false);
    }
  };

  const fillDemoUser = () => {
    setEmail('user@crimesense.com');
    setPassword('User@123');
  };

  const fillDemoAdmin = () => {
    setEmail('admin@crimesense.com');
    setPassword('Admin@123');
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-center py-8 px-4 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center mb-6">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 mb-3 shadow-lg shadow-cyan-500/10">
          <Shield className="w-8 h-8" />
        </div>
        <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
          Welcome to <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">CrimeSense</span>
        </h2>
        <p className="mt-2 text-sm text-slate-400">
          AI-Powered Crime Analytics & Real-Time Safety System
        </p>
      </div>

      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-800/80 shadow-2xl rounded-2xl p-6 sm:p-8">

          {/* Demo Quick Fill Buttons */}
          <div className="mb-6 p-3 bg-slate-950/70 border border-slate-800 rounded-xl text-xs space-y-2">
            <div className="flex justify-between items-center text-slate-400 font-medium">
              <span>Quick Fill Demo Credentials:</span>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={fillDemoAdmin}
                className="px-2.5 py-1.5 bg-cyan-950/60 hover:bg-cyan-900/60 border border-cyan-800/50 text-cyan-300 rounded-lg transition font-medium flex items-center justify-center gap-1"
              >
                <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400" /> Admin Demo
              </button>
              <button
                type="button"
                onClick={fillDemoUser}
                className="px-2.5 py-1.5 bg-blue-950/60 hover:bg-blue-900/60 border border-blue-800/50 text-blue-300 rounded-lg transition font-medium flex items-center justify-center gap-1"
              >
                <CheckCircle2 className="w-3.5 h-3.5 text-blue-400" /> User Demo
              </button>
            </div>
          </div>

          {error && (
            <div className="mb-5 p-3.5 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs sm:text-sm flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-3 w-4 h-4 text-slate-500" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@example.com"
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-950/80 border border-slate-800 rounded-xl text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-3 w-4 h-4 text-slate-500" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-10 pr-10 py-2.5 bg-slate-950/80 border border-slate-800 rounded-xl text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-3 text-slate-500 hover:text-slate-300"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-2 py-3 px-4 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold rounded-xl shadow-lg shadow-cyan-500/25 flex items-center justify-center gap-2 transition disabled:opacity-50"
            >
              {loading ? (
                <span>Signing in...</span>
              ) : (
                <>
                  <span>Sign In</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-800"></div>
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-slate-900 px-3 text-slate-400 font-medium">Or continue with</span>
            </div>
          </div>

          {/* Mobile-Friendly Full-Width Google Sign-In */}
          <div className="w-full">
            <GoogleAuthButton onError={setError} mode="signin" />
          </div>


          <p className="mt-6 text-center text-xs text-slate-400">
            Don't have an account?{' '}
            <Link to="/signup" className="text-cyan-400 hover:text-cyan-300 font-semibold underline underline-offset-4">
              Sign up here
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}