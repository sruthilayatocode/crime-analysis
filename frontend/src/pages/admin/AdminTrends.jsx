import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  Calendar,
  BarChart3,
  MapPin,
  Flame,
  RefreshCw,
  Layers,
  ArrowUpRight,
  ArrowDownRight,
  Activity,
} from 'lucide-react';
import { adminService } from '../../services/adminService';

export default function AdminTrends() {
  const [selectedYear, setSelectedYear] = useState('all');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchTrends = async (year) => {
    setLoading(true);
    try {
      const res = await adminService.getHistoricalTrends(year);
      setData(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTrends(selectedYear);
  }, [selectedYear]);

  const yearChart = data?.year_chart || [];
  const monthlyData = data?.monthly_breakdown || [];
  const districtData = data?.district_breakdown || [];
  const localityData = data?.locality_breakdown || [];
  const typeTrends = data?.type_trends || {};
  const availableYears = data?.available_years || [];

  const maxMonthly = Math.max(...monthlyData.map((d) => d.count), 1);
  const maxYearly = Math.max(...yearChart.map((d) => d.count), 1);
  const maxLocality = Math.max(...localityData.map((d) => d.count), 1);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header & Year Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-black tracking-tight text-white">Historical Trends & Analytics</h1>
            <span className="text-[10px] font-bold text-purple-400 bg-purple-950/80 px-2.5 py-0.5 rounded-full border border-purple-800">
              Multi-Year Engine
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Analyze longitudinal crime patterns, seasonal spikes, YoY variances, and geographic distributions
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-slate-400">Filter Year:</span>
          <select
            value={selectedYear}
            onChange={(e) => setSelectedYear(e.target.value)}
            className="px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-xs text-white font-bold focus:outline-none focus:border-purple-500"
          >
            <option value="all">All Recorded Years (2018–Present)</option>
            {availableYears.map((y) => (
              <option key={y} value={y}>
                Year {y}
              </option>
            ))}
          </select>

          <button
            type="button"
            onClick={() => fetchTrends(selectedYear)}
            disabled={loading}
            className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl border border-slate-700"
            title="Refresh analytics"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {loading && !data ? (
        <div className="flex flex-col items-center justify-center min-h-[50vh] text-slate-400 space-y-3">
          <RefreshCw className="w-8 h-8 animate-spin text-purple-500" />
          <p className="text-sm font-semibold">Computing historical data aggregates...</p>
        </div>
      ) : (
        <>
          {/* Top Analytics Cards */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            {/* Year-over-Year Trajectory */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-purple-400" />
                    <span>Annual Incident Volume (YoY)</span>
                  </h3>
                  <p className="text-xs text-slate-400">Total reported cases recorded per year</p>
                </div>
              </div>

              <div className="h-44 flex items-end gap-3 pt-4 border-b border-slate-800 pb-2">
                {yearChart.map((d, idx) => {
                  const heightPct = Math.max(12, (d.count / maxYearly) * 100);
                  const isSelected = selectedYear === d.year;
                  return (
                    <div
                      key={idx}
                      onClick={() => setSelectedYear(d.year)}
                      className="flex-1 flex flex-col items-center gap-1 group relative h-full justify-end cursor-pointer"
                    >
                      <div className="absolute -top-7 opacity-0 group-hover:opacity-100 transition-opacity bg-slate-950 text-white text-[10px] font-bold px-2 py-0.5 rounded border border-slate-700 whitespace-nowrap z-10 pointer-events-none">
                        {d.year}: {d.count} cases
                      </div>
                      <div
                        style={{ height: `${heightPct}%` }}
                        className={`w-full rounded-t-lg transition-all ${
                          isSelected
                            ? 'bg-gradient-to-t from-purple-600 to-indigo-400 ring-2 ring-purple-300'
                            : 'bg-gradient-to-t from-slate-700 to-slate-500 hover:from-purple-700 hover:to-purple-500'
                        }`}
                      />
                    </div>
                  );
                })}
              </div>

              <div className="flex justify-between text-xs text-slate-400 font-mono font-bold">
                {yearChart.map((d, idx) => (
                  <span key={idx} className={selectedYear === d.year ? 'text-purple-400 font-black' : ''}>
                    {d.year}
                  </span>
                ))}
              </div>
            </div>

            {/* Monthly Breakdown in Selected Year / Range */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <BarChart3 className="w-4 h-4 text-cyan-400" />
                    <span>Monthly Distribution ({selectedYear === 'all' ? 'All Years' : selectedYear})</span>
                  </h3>
                  <p className="text-xs text-slate-400">Monthly case variance and peak risk periods</p>
                </div>
                <span className="text-[10px] font-bold text-cyan-400 bg-cyan-950 px-2.5 py-1 rounded-lg border border-cyan-800">
                  {monthlyData.length} Months
                </span>
              </div>

              <div className="h-44 flex items-end gap-1.5 pt-4 border-b border-slate-800 pb-2 overflow-x-auto">
                {monthlyData.map((d, idx) => {
                  const heightPct = Math.max(10, (d.count / maxMonthly) * 100);
                  return (
                    <div key={idx} className="flex-1 min-w-[20px] flex flex-col items-center gap-1 group relative h-full justify-end">
                      <div className="absolute -top-7 opacity-0 group-hover:opacity-100 transition-opacity bg-slate-950 text-white text-[10px] font-bold px-2 py-0.5 rounded border border-slate-700 whitespace-nowrap z-10 pointer-events-none">
                        {d.month}: {d.count}
                      </div>
                      <div
                        style={{ height: `${heightPct}%` }}
                        className="w-full bg-gradient-to-t from-cyan-600 to-teal-400 rounded-t-md hover:brightness-125 transition-all"
                      />
                    </div>
                  );
                })}
              </div>

              <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                <span>{monthlyData[0]?.month || 'Start'}</span>
                <span>{monthlyData[monthlyData.length - 1]?.month || 'End'}</span>
              </div>
            </div>
          </div>

          {/* Geographic Breakdown: Localities & Districts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            {/* Top Localities Breakdown */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <MapPin className="w-4 h-4 text-red-500" />
                <span>Top High-Frequency Localities</span>
              </h3>
              <p className="text-xs text-slate-400">Geographic clusters ranked by total incidents</p>

              <div className="space-y-3 pt-1">
                {localityData.map((l, idx) => {
                  const pct = Math.round((l.count / maxLocality) * 100);
                  return (
                    <div key={idx} className="space-y-1">
                      <div className="flex justify-between text-xs font-bold">
                        <span className="text-slate-200">
                          {idx + 1}. {l.locality}
                        </span>
                        <span className="text-red-400 font-mono">{l.count} cases</span>
                      </div>
                      <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                        <div
                          style={{ width: `${pct}%` }}
                          className="h-full bg-gradient-to-r from-red-600 to-rose-400 rounded-full"
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Per-Crime-Type Multi-Year Matrix */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Flame className="w-4 h-4 text-amber-500" />
                <span>Crime-Type Annual Trajectory Matrix</span>
              </h3>
              <p className="text-xs text-slate-400">Progression across crime types by year</p>

              <div className="space-y-2 pt-1 max-h-72 overflow-y-auto pr-1">
                {Object.entries(typeTrends).map(([cType, yearMap], idx) => {
                  const totalTypeCount = Object.values(yearMap).reduce((a, b) => a + b, 0);
                  return (
                    <div key={idx} className="p-3 bg-slate-950/70 rounded-xl border border-slate-800 space-y-2">
                      <div className="flex justify-between text-xs font-bold">
                        <span className="text-white">{cType}</span>
                        <span className="text-amber-400 font-mono">{totalTypeCount} total</span>
                      </div>
                      <div className="flex gap-2 flex-wrap text-[10px]">
                        {Object.entries(yearMap).map(([yr, cnt]) => (
                          <span key={yr} className="px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 border border-slate-700 font-mono">
                            {yr}: <strong className="text-white">{cnt}</strong>
                          </span>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
