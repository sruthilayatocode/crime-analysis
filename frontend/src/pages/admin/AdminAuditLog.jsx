import React, { useState, useEffect, useCallback } from 'react';
import {
  ScrollText,
  Search,
  Filter,
  Shield,
  Clock,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  User,
  Globe,
  Database,
  Radio,
  Lock,
} from 'lucide-react';
import { adminService } from '../../services/adminService';

const getActionColor = (act = '') => {
  const a = act.toUpperCase();
  if (a.includes('DELETE')) return 'bg-red-950 text-red-400 border-red-800';
  if (a.includes('CREATE') || a.includes('IMPORT')) return 'bg-emerald-950 text-emerald-400 border-emerald-800';
  if (a.includes('UPDATE') || a.includes('ROLE') || a.includes('STATUS')) return 'bg-amber-950 text-amber-400 border-amber-800';
  if (a.includes('LIVE_MAP') || a.includes('LOCATION')) return 'bg-cyan-950 text-cyan-400 border-cyan-800';
  return 'bg-blue-950 text-blue-400 border-blue-800';
};

const ACTION_FILTERS = [
  'all',
  'CREATE_INCIDENT',
  'UPDATE_INCIDENT',
  'DELETE_INCIDENT',
  'IMPORT_CSV',
  'EXPORT_CSV',
  'VIEW_LIVE_MAP',
  'VIEW_USER_DETAILS',
  'CHANGE_USER_ROLE',
  'TOGGLE_USER_ACTIVE',
  'DELETE_USER',
  'RESOLVE_SOS_EVENT',
  'ADD_SOS_NOTES',
];

export default function AdminAuditLog() {
  const [logs, setLogs] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [perPage, setPerPage] = useState(25);
  const [loading, setLoading] = useState(true);

  const [actionFilter, setActionFilter] = useState('all');
  const [adminFilter, setAdminFilter] = useState('');

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    try {
      const res = await adminService.getAuditLogs({
        page,
        per_page: perPage,
        action: actionFilter,
        admin: adminFilter,
      });
      setLogs(res.logs || []);
      setTotal(res.total || 0);
      setPages(res.pages || 1);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [page, perPage, actionFilter, adminFilter]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-black tracking-tight text-white">Security & Audit Log Trail</h1>
            <span className="text-[10px] font-bold text-cyan-400 bg-cyan-950/80 px-2.5 py-0.5 rounded-full border border-cyan-800">
              {total} Log Entries
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Immutable audit record of administrative actions, incident modifications, and sensitive user location lookups
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={fetchLogs}
            disabled={loading}
            className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold border border-slate-700 flex items-center gap-1.5 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh Logs</span>
          </button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="p-4 bg-slate-900 border border-slate-800 rounded-2xl flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
          <input
            type="text"
            placeholder="Filter by admin name or email..."
            value={adminFilter}
            onChange={(e) => {
              setAdminFilter(e.target.value);
              setPage(1);
            }}
            className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
          />
        </div>

        <div className="w-full sm:w-64">
          <select
            value={actionFilter}
            onChange={(e) => {
              setActionFilter(e.target.value);
              setPage(1);
            }}
            className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 font-bold focus:outline-none focus:border-cyan-500"
          >
            <option value="all">All Action Types</option>
            {ACTION_FILTERS.filter((a) => a !== 'all').map((a) => (
              <option key={a} value={a}>
                {a.replace(/_/g, ' ')}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/80 text-slate-400 font-bold border-b border-slate-800">
              <tr>
                <th className="py-3.5 px-4">Timestamp</th>
                <th className="py-3.5 px-4">Admin Operator</th>
                <th className="py-3.5 px-4">Action</th>
                <th className="py-3.5 px-4">Target Entity</th>
                <th className="py-3.5 px-4">Details & Notes</th>
                <th className="py-3.5 px-4">IP Address</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-500">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-cyan-500" />
                    Loading audit trail...
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-500">
                    No matching audit log entries recorded.
                  </td>
                </tr>
              ) : (
                logs.map((l) => (
                  <tr key={l.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3.5 px-4 font-mono text-[11px] text-slate-400 whitespace-nowrap">
                      {l.created_at ? l.created_at.replace('T', ' ').slice(0, 19) : 'N/A'}
                    </td>

                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-2">
                        <div className="w-6 h-6 rounded-lg bg-slate-800 text-slate-300 font-bold flex items-center justify-center text-[10px] shrink-0">
                          {l.admin_name ? l.admin_name[0].toUpperCase() : 'A'}
                        </div>
                        <div>
                          <span className="font-bold text-white block leading-tight">{l.admin_name || 'System'}</span>
                          <span className="text-[10px] text-slate-400 block leading-tight">{l.admin_email}</span>
                        </div>
                      </div>
                    </td>

                    <td className="py-3.5 px-4">
                      <span className={`inline-block text-[10px] font-black px-2 py-0.5 rounded-full border ${getActionColor(l.action)}`}>
                        {l.action}
                      </span>
                    </td>

                    <td className="py-3.5 px-4 font-bold text-slate-200">
                      {l.target_entity || '—'}
                    </td>

                    <td className="py-3.5 px-4 text-slate-400 max-w-xs truncate">
                      {l.details || '—'}
                    </td>

                    <td className="py-3.5 px-4 font-mono text-[11px] text-slate-500">
                      {l.ip_address || '127.0.0.1'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="p-4 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <span>
            Page {page} of {pages}
          </span>
          <div className="flex items-center gap-1.5">
            <button
              type="button"
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
              className="p-2 rounded-xl bg-slate-950 border border-slate-800 hover:bg-slate-800 text-slate-300 disabled:opacity-40"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              type="button"
              disabled={page >= pages}
              onClick={() => setPage(page + 1)}
              className="p-2 rounded-xl bg-slate-950 border border-slate-800 hover:bg-slate-800 text-slate-300 disabled:opacity-40"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
