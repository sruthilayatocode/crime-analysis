import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Menu,
  Bell,
  Shield,
  Smartphone,
  LogOut,
  AlertTriangle,
  Radio,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { adminService } from '../services/adminService';

export default function Navbar({ onMenuClick }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [activeSOSCount, setActiveSOSCount] = useState(0);

  useEffect(() => {
    async function fetchSOS() {
      try {
        const feed = await adminService.getSOSFeed({ status: 'active' });
        setActiveSOSCount(feed.active_count || 0);
      } catch {}
    }
    fetchSOS();
    const interval = setInterval(fetchSOS, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleLogout = async () => {
    if (logout) await logout();
    navigate('/login');
  };

  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/90 backdrop-blur-md sticky top-0 z-30 px-4 sm:px-6 flex items-center justify-between text-slate-100">
      <div className="flex items-center gap-3">
        {/* Mobile menu trigger */}
        <button
          type="button"
          onClick={onMenuClick}
          className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-xl lg:hidden"
          title="Toggle Navigation Menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-red-600 text-white flex items-center justify-center font-black shadow-sm">
            <Shield className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-sm sm:text-base text-white tracking-tight">
                CrimeSense Portal
              </span>
              <span className="hidden sm:inline-block text-[10px] font-bold text-red-400 bg-red-950/80 px-2 py-0.5 rounded-full border border-red-800/80">
                PROD v2.4
              </span>
            </div>
            <p className="hidden md:block text-[11px] text-slate-400">
              Law Enforcement & Safety Management Headquarters
            </p>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Active SOS alert indicator button */}
        {activeSOSCount > 0 ? (
          <Link
            to="/admin/alerts"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-red-600 text-white text-xs font-bold animate-pulse shadow-md shadow-red-600/30 hover:bg-red-700 transition-all"
          >
            <AlertTriangle className="w-4 h-4" />
            <span>{activeSOSCount} Active SOS Distress</span>
          </Link>
        ) : (
          <Link
            to="/admin/alerts"
            className="p-2 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors relative"
            title="SOS Alert Stream"
          >
            <Bell className="w-5 h-5" />
            <span className="w-2 h-2 rounded-full bg-emerald-500 absolute top-2 right-2 ring-2 ring-slate-900" />
          </Link>
        )}

        {/* Switch to citizen app view */}
        <Link
          to="/app"
          className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-colors"
        >
          <Smartphone className="w-3.5 h-3.5 text-emerald-400" />
          <span>Citizen App</span>
        </Link>

        {/* User badge */}
        <div className="flex items-center gap-2.5 border-l border-slate-800 pl-3">
          <div className="w-8 h-8 rounded-xl bg-red-700 text-white flex items-center justify-center font-bold text-xs">
            {user?.name ? user.name[0].toUpperCase() : 'A'}
          </div>
          <div className="hidden lg:block text-left">
            <p className="text-xs font-bold text-slate-200 leading-tight">{user?.name || 'Administrator'}</p>
            <p className="text-[10px] text-slate-400 leading-tight">Admin Privileges</p>
          </div>
        </div>

        {/* Logout */}
        <button
          type="button"
          onClick={handleLogout}
          className="p-2 text-slate-400 hover:text-red-400 hover:bg-slate-800 rounded-xl transition-colors"
          title="Sign Out"
        >
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
}