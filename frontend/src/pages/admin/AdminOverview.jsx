import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldAlert,
  Users,
  Radio,
  Flame,
  AlertTriangle,
  Database,
  TrendingUp,
  MapPin,
  RefreshCw,
  ArrowUpRight,
  Activity,
  CheckCircle2,
  FileSpreadsheet,
} from 'lucide-react';
import { adminService } from '../../services/adminService';

export default function AdminOverview() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchOverview = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await adminService.getOverview();
      setData(res);
    } catch (err) {
      setError(err.message || 'Failed to load overview data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
    const interval = setInterval(fetchOverview, 30000); // 30s auto refresh
    return () => clearInterval(interval);
  }, []);

  if (loading && !data) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-slate-400 space-y-3">
        <RefreshCw className="w-8 h-8 animate-spin text-red-500" />
        <p className="text-sm font-semibold">Loading Law Enforcement Intelligence Overview...</p>
      </div>
    );
  }

  const kpis = data?.kpis || {};
  const charts = data?.charts || {};

  const kpiCards = [
    {
      label: 'Total Incidents',
      value: kpis.total_crimes ?? 0,
      sub: `${kpis.high_severity_count || 0} high-severity`,
      icon: Database,
      color: 'text-blue-400 bg-blue-950/60 border-blue-800/60',
      badgeColor: 'text-blue-400 bg-blue-900/40',
    },
    {
      label: 'High-Severity Cases',
      value: kpis.high_severity_count ?? 0,
      sub: 'Critical / High Risk',
      icon: ShieldAlert,
      color: 'text-rose-400 bg-rose-950/60 border-rose-800/60',
      badgeColor: 'text-rose-400 bg-rose-900/40',
    },
    {
      label: 'Active Hotspots',
      value: kpis.active_hotspots ?? 0,
      sub: 'High-risk clusters',
      icon: Flame,
      color: 'text-amber-400 bg-amber-950/60 border-amber-800/60',
      badgeColor: 'text-amber-400 bg-amber-900/40',
    },
    {
      label: 'Registered Citizens',
      value: kpis.total_users ?? 0,
      sub: `${kpis.active_users_now || 0} active currently`,
      icon: Users,
      color: 'text-emerald-400 bg-emerald-950/60 border-emerald-800/60',
      badgeColor: 'text-emerald-400 bg-emerald-900/40',
    },
    {
      label: 'Active Live Sharers',
      value: kpis.active_users_now ?? 0,
      sub: 'GPS active (last 15m)',
      icon: Radio,
      color: 'text-cyan-400 bg-cyan-950/60 border-cyan-800/60',
      badgeColor: 'text-cyan-400 bg-cyan-900/40',
    },
    {
      label: 'Active SOS Distress',
      value: kpis.active_sos_events ?? 0,
      sub: kpis.active_sos_events > 0 ? 'Requires Action!' : 'All Clear',
      icon: AlertTriangle,
      color: kpis.active_sos_events > 0 ? 'text-red-400 bg-red-950 border-red-600 animate-pulse' : 'text-slate-400 bg-slate-900 border-slate-800',
      badgeColor: kpis.active_sos_events > 0 ? 'text-white bg-red-600' : 'text-slate-400 bg-slate-800',
    },
    {
      label: 'Red-Zone Users',
      value: kpis.red_zone_users ?? 0,
      sub: 'Stationary in danger zone',
      icon: Activity,
      color: 'text-orange-400 bg-orange-950/60 border-orange-800/60',
      badgeColor: 'text-orange-400 bg-orange-900/40',
    },
  ];

  // Helper for line chart coordinates
  const trendData = charts.monthly_trend || [];
  const maxTrend = Math.max(...trendData.map((d) => d.count), 10);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-black tracking-tight text-white">Command Center Overview</h1>
            <span className="text-[10px] font-bold text-emerald-400 bg-emerald-950/80 px-2.5 py-0.5 rounded-full border border-emerald-800 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" /> Live Telemetry
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time crime intelligence, citizen safety tracking, and emergency incident dispatch
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={fetchOverview}
            disabled={loading}
            className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold border border-slate-700 flex items-center gap-1.5 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>

          <Link
            to="/admin/crimes"
            className="px-3.5 py-2 rounded-xl bg-red-600 hover:bg-red-700 text-white text-xs font-bold shadow-md shadow-red-600/30 flex items-center gap-1.5 transition-colors"
          >
            <span>Manage Incidents</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-950/80 border border-red-800 text-red-200 rounded-2xl text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* 7 KPI Cards Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-7 gap-3">
        {kpiCards.map((c, idx) => {
          const Icon = c.icon;
          return (
            <div
              key={idx}
              className={`p-3.5 rounded-2xl border ${c.color} flex flex-col justify-between transition-all hover:scale-102`}
            >
              <div className="flex items-center justify-between mb-2">
                <Icon className="w-4 h-4" />
                <span className={`text-[9px] font-black px-1.5 py-0.5 rounded-full ${c.badgeColor}`}>
                  {c.sub}
                </span>
              </div>
              <div>
                <span className="text-2xl font-black text-white block leading-tight">{c.value}</span>
                <span className="text-[11px] font-bold text-slate-300 block truncate mt-0.5">{c.label}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Quick Action Shortcuts */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Link
          to="/admin/live-map"
          className="p-3.5 bg-slate-900/80 hover:bg-slate-800/90 border border-slate-800 rounded-2xl flex items-center justify-between text-slate-200 transition-all group"
        >
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-cyan-950 text-cyan-400 flex items-center justify-center border border-cyan-800">
              <MapPin className="w-4 h-4" />
            </div>
            <div>
              <span className="text-xs font-bold block group-hover:text-cyan-400 transition-colors">Live User Map</span>
              <span className="text-[10px] text-slate-400">Consented location sharers</span>
            </div>
          </div>
          <ArrowUpRight className="w-4 h-4 text-slate-500 group-hover:text-cyan-400 transition-colors" />
        </Link>

        <Link
          to="/admin/alerts"
          className="p-3.5 bg-slate-900/80 hover:bg-slate-800/90 border border-slate-800 rounded-2xl flex items-center justify-between text-slate-200 transition-all group"
        >
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-red-950 text-red-400 flex items-center justify-center border border-red-800">
              <AlertTriangle className="w-4 h-4" />
            </div>
            <div>
              <span className="text-xs font-bold block group-hover:text-red-400 transition-colors">SOS Alerts Feed</span>
              <span className="text-[10px] text-slate-400">Live distress emergencies</span>
            </div>
          </div>
          <ArrowUpRight className="w-4 h-4 text-slate-500 group-hover:text-red-400 transition-colors" />
        </Link>

        <Link
          to="/admin/trends"
          className="p-3.5 bg-slate-900/80 hover:bg-slate-800/90 border border-slate-800 rounded-2xl flex items-center justify-between text-slate-200 transition-all group"
        >
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-purple-950 text-purple-400 flex items-center justify-center border border-purple-800">
              <TrendingUp className="w-4 h-4" />
            </div>
            <div>
              <span className="text-xs font-bold block group-hover:text-purple-400 transition-colors">History & Trends</span>
              <span className="text-[10px] text-slate-400">Multi-year YoY comparison</span>
            </div>
          </div>
          <ArrowUpRight className="w-4 h-4 text-slate-500 group-hover:text-purple-400 transition-colors" />
        </Link>

        <Link
          to="/admin/audit-logs"
          className="p-3.5 bg-slate-900/80 hover:bg-slate-800/90 border border-slate-800 rounded-2xl flex items-center justify-between text-slate-200 transition-all group"
        >
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-emerald-950 text-emerald-400 flex items-center justify-center border border-emerald-800">
              <CheckCircle2 className="w-4 h-4" />
            </div>
            <div>
              <span className="text-xs font-bold block group-hover:text-emerald-400 transition-colors">Security Audit</span>
              <span className="text-[10px] text-slate-400">Admin operation logs</span>
            </div>
          </div>
          <ArrowUpRight className="w-4 h-4 text-slate-500 group-hover:text-emerald-400 transition-colors" />
        </Link>
      </div>

      {/* Analytics Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Monthly Incident Trends Line Chart */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-red-500" />
                <span>Monthly Crime Incident Trajectory</span>
              </h3>
              <p className="text-xs text-slate-400">Rolling 12-month verified crime volume</p>
            </div>
            <span className="text-[10px] font-bold text-slate-400 bg-slate-800 px-2.5 py-1 rounded-lg border border-slate-700">
              {trendData.length} Data Points
            </span>
          </div>

          {trendData.length > 0 ? (
            <div className="space-y-2">
              <div className="h-44 flex items-end gap-2 pt-4 border-b border-slate-800 pb-2">
                {trendData.map((d, idx) => {
                  const heightPct = Math.max(8, (d.count / maxTrend) * 100);
                  return (
                    <div key={idx} className="flex-1 flex flex-col items-center gap-1 group relative h-full justify-end">
                      {/* Tooltip */}
                      <div className="absolute -top-7 opacity-0 group-hover:opacity-100 transition-opacity bg-slate-950 text-white text-[10px] font-bold px-2 py-0.5 rounded border border-slate-700 whitespace-nowrap z-10 pointer-events-none">
                        {d.month}: {d.count} crimes
                      </div>
                      <div
                        style={{ height: `${heightPct}%` }}
                        className="w-full bg-gradient-to-t from-red-600 to-rose-400 rounded-t-md transition-all group-hover:brightness-125"
                      />
                    </div>
                  );
                })}
              </div>
              <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                <span>{trendData[0]?.month}</span>
                <span>{trendData[Math.floor(trendData.length / 2)]?.month}</span>
                <span>{trendData[trendData.length - 1]?.month}</span>
              </div>
            </div>
          ) : (
            <div className="h-36 flex items-center justify-center text-xs text-slate-500">
              No historical trend data available.
            </div>
          )}
        </div>

        {/* Severity Distribution */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-rose-400" />
            <span>Severity Classification</span>
          </h3>
          <p className="text-xs text-slate-400">Incident breakdown by threat level</p>

          <div className="space-y-3 pt-2">
            {(charts.severity_breakdown || []).map((s, idx) => {
              const totalCrimes = kpis.total_crimes || 1;
              const pct = Math.round((s.count / totalCrimes) * 100);
              const colorClass =
                s.severity.toLowerCase().includes('critical') || s.severity.toLowerCase().includes('high')
                  ? 'bg-rose-500'
                  : s.severity.toLowerCase().includes('medium')
                  ? 'bg-amber-500'
                  : 'bg-emerald-500';

              return (
                <div key={idx} className="space-y-1">
                  <div className="flex justify-between text-xs font-bold">
                    <span className="text-slate-300">{s.severity}</span>
                    <span className="text-white">
                      {s.count} <span className="text-slate-500 font-normal">({pct}%)</span>
                    </span>
                  </div>
                  <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                    <div style={{ width: `${pct}%` }} className={`h-full ${colorClass} rounded-full`} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Crime Types Breakdown */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Database className="w-4 h-4 text-blue-400" />
            <span>Top Incident Categories</span>
          </h3>
          <p className="text-xs text-slate-400">Most frequent offense types in the registry</p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
            {(charts.crimes_by_type || []).map((t, idx) => {
              const totalCrimes = kpis.total_crimes || 1;
              const pct = Math.round((t.count / totalCrimes) * 100);
              return (
                <div key={idx} className="p-3 bg-slate-950/60 rounded-xl border border-slate-800/80 space-y-1.5">
                  <div className="flex justify-between text-xs font-bold">
                    <span className="text-slate-200 truncate">{t.type}</span>
                    <span className="text-blue-400 font-mono shrink-0">{t.count}</span>
                  </div>
                  <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                    <div style={{ width: `${pct}%` }} className="h-full bg-blue-500 rounded-full" />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Risk Zone Spread */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Flame className="w-4 h-4 text-orange-400" />
            <span>Zone Threat Distribution</span>
          </h3>
          <p className="text-xs text-slate-400">Sample risk evaluation of monitored coordinates</p>

          <div className="grid grid-cols-2 gap-2.5 pt-2">
            {(charts.zone_distribution || []).map((z, idx) => {
              const zoneBg =
                z.zone === 'RED'
                  ? 'bg-red-950/70 border-red-800 text-red-400'
                  : z.zone === 'ORANGE'
                  ? 'bg-orange-950/70 border-orange-800 text-orange-400'
                  : z.zone === 'YELLOW'
                  ? 'bg-amber-950/70 border-amber-800 text-amber-400'
                  : 'bg-emerald-950/70 border-emerald-800 text-emerald-400';

              return (
                <div key={idx} className={`p-3 rounded-xl border ${zoneBg} text-center space-y-0.5`}>
                  <span className="text-xs font-extrabold block">{z.zone} ZONE</span>
                  <span className="text-xl font-black text-white block">{z.count}</span>
                  <span className="text-[10px] opacity-75">Incidents</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
