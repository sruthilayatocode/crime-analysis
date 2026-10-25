import React, { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Database,
  TrendingUp,
  Users,
  MapPin,
  BellRing,
  ScrollText,
  ChevronLeft,
  ChevronRight,
  Shield,
  Smartphone,
  LogOut,
  X,
  Radio,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { adminService } from '../services/adminService';

const ADMIN_NAV_ITEMS = [
  { to: '/admin/overview', label: 'Overview', icon: LayoutDashboard },
  { to: '/admin/crimes', label: 'Crime Data', icon: Database },
  { to: '/admin/trends', label: 'History & Trends', icon: TrendingUp },
  { to: '/admin/users', label: 'Users', icon: Users },
  { to: '/admin/live-map', label: 'Live Map', icon: MapPin },
  { to: '/admin/alerts', label: 'Alerts & SOS', icon: BellRing, badge: true },
  { to: '/admin/audit-logs', label: 'Audit Log', icon: ScrollText },
];

export default function Sidebar({ collapsed, onToggle, mobileOpen, onMobileClose }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [activeSOSCount, setActiveSOSCount] = useState(0);

  // Poll active SOS count for sidebar badge every 15s
  useEffect(() => {
    async function checkSOS() {
      try {
        const feed = await adminService.getSOSFeed({ status: 'active' });
        setActiveSOSCount(feed.active_count || 0);
      } catch {}
    }
    checkSOS();
    const interval = setInterval(checkSOS, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleLogout = async () => {
    if (logout) await logout();
    navigate('/login');
  };

  return (
    <>
      {/* Mobile backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-950/70 backdrop-blur-xs lg:hidden transition-opacity"
          onClick={onMobileClose}
        />
      )}

      {/* Sidebar container */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex flex-col bg-slate-900 border-r border-slate-800 text-slate-300 transition-all duration-300 select-none lg:static ${
          collapsed ? 'lg:w-20' : 'lg:w-64'
        } ${mobileOpen ? 'w-64 translate-x-0' : 'w-64 -translate-x-full lg:translate-x-0'}`}
      >
        {/* Brand header */}
        <div className="h-16 px-4 flex items-center justify-between border-b border-slate-800 shrink-0">
          <div className="flex items-center gap-2.5 overflow-hidden">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-red-600 to-rose-500 text-white flex items-center justify-center font-black shadow-md shrink-0">
              <Shield className="w-5 h-5" />
            </div>
            {!collapsed && (
              <div className="truncate">
                <span className="font-extrabold text-white text-sm tracking-tight block">
                  CrimeSense<span className="text-red-500 font-bold ml-1 text-xs uppercase px-1.5 py-0.2 bg-red-950/60 rounded border border-red-800/60">Admin</span>
                </span>
                <span className="text-[10px] text-slate-400 block -mt-0.5">Control & Intelligence</span>
              </div>
            )}
          </div>

          <div className="flex items-center gap-1">
            {/* Desktop collapse toggle */}
            <button
              type="button"
              onClick={onToggle}
              className="hidden lg:flex p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
              title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            >
              {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
            </button>

            {/* Mobile close */}
            <button
              type="button"
              onClick={onMobileClose}
              className="lg:hidden p-1.5 text-slate-400 hover:text-white rounded-lg"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Navigation list */}
        <nav className="flex-1 overflow-y-auto p-3 space-y-1">
          {ADMIN_NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive =
              location.pathname === item.to ||
              (item.to === '/admin/overview' && (location.pathname === '/admin' || location.pathname === '/admin/dashboard'));

            return (
              <Link
                key={item.to}
                to={item.to}
                onClick={onMobileClose}
                className={`group relative flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                  isActive
                    ? 'bg-red-600 text-white shadow-md shadow-red-600/20'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/70'
                }`}
                title={collapsed ? item.label : undefined}
              >
                <Icon className={`w-4 h-4 shrink-0 transition-transform group-hover:scale-110 ${isActive ? 'text-white' : 'text-slate-400 group-hover:text-slate-200'}`} />

                {!collapsed && (
                  <span className="truncate flex-1">{item.label}</span>
                )}

                {item.badge && activeSOSCount > 0 && (
                  <span
                    className={`shrink-0 flex items-center justify-center px-1.5 py-0.5 rounded-full text-[10px] font-black animate-pulse ${
                      isActive ? 'bg-white text-red-700' : 'bg-red-600 text-white'
                    }`}
                  >
                    {activeSOSCount}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>

        {/* Switch to User View & Admin Profile Footer */}
        <div className="p-3 border-t border-slate-800 shrink-0 space-y-2">
          {/* Switch to User Mobile App */}
          <Link
            to="/app"
            className={`flex items-center gap-2 px-3 py-2 rounded-xl bg-slate-800/80 hover:bg-slate-800 text-slate-300 hover:text-white text-xs font-semibold transition-all border border-slate-700/60 ${
              collapsed ? 'justify-center' : ''
            }`}
            title="Open Citizen Safety App"
          >
            <Smartphone className="w-4 h-4 text-emerald-400 shrink-0" />
            {!collapsed && <span className="truncate">Citizen App View</span>}
          </Link>

          {/* Admin profile snippet & logout */}
          <div className="flex items-center justify-between pt-1">
            <div className="flex items-center gap-2 overflow-hidden">
              <div className="w-8 h-8 rounded-lg bg-red-700 text-white flex items-center justify-center font-bold text-xs shrink-0">
                {user?.name ? user.name[0].toUpperCase() : 'A'}
              </div>
              {!collapsed && (
                <div className="truncate text-left min-w-0">
                  <p className="text-xs font-bold text-white truncate">{user?.name || 'Administrator'}</p>
                  <p className="text-[10px] text-slate-400 truncate">{user?.email || 'admin@crimesense.com'}</p>
                </div>
              )}
            </div>

            {!collapsed && (
              <button
                type="button"
                onClick={handleLogout}
                className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-slate-800 rounded-lg transition-colors"
                title="Log out"
              >
                <LogOut className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </aside>
    </>
  );
}