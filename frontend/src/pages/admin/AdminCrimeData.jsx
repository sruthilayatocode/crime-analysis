import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Database,
  Plus,
  Search,
  Filter,
  Download,
  Upload,
  Edit3,
  Trash2,
  MapPin,
  Flame,
  Layers,
  RefreshCw,
  X,
  CheckCircle2,
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  Clock3,
  XCircle,
  ShieldCheck,
} from 'lucide-react';
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { adminService } from '../../services/adminService';

// Fix Leaflet marker icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const getSeverityColor = (sev) => {
  const s = (sev || '').toUpperCase();
  if (s.includes('CRITICAL') || s.includes('HIGH')) return '#ef4444'; // Red
  if (s.includes('MEDIUM')) return '#f59e0b'; // Amber
  return '#10b981'; // Emerald
};

const createMarkerIcon = (sev) => {
  const color = getSeverityColor(sev);
  return L.divIcon({
    className: 'custom-crime-marker',
    html: `<div style="background-color: ${color}; width: 14px; height: 14px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 8px ${color};"></div>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  });
};

const CRIME_TYPES = [
  'All',
  'Theft',
  'Robbery',
  'Burglary',
  'Assault',
  'Chain Snatching',
  'Vehicle Theft',
  'Fraud',
  'Harassment',
  'Cybercrime',
  'Murder',
  'Vandalism',
  'Drug Offense',
  'Other',
];

const SEVERITIES = ['All', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];

export default function AdminCrimeData() {
  const [crimes, setCrimes] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [perPage, setPerPage] = useState(15);
  const [loading, setLoading] = useState(true);

  // Filters & Search
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState('All');
  const [selectedSeverity, setSelectedSeverity] = useState('All');
  const [sortBy, setSortBy] = useState('published_date');
  const [sortOrder, setSortOrder] = useState('desc');

  // View state: 'table' | 'map' | 'both'
  const [activeTab, setActiveTab] = useState('both'); // 'table' | 'map' | 'both'
  const [showHotspots, setShowHotspots] = useState(true);

  // Modals state
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingCrime, setEditingCrime] = useState(null);
  const [showImportModal, setShowImportModal] = useState(false);
  const [importFile, setImportFile] = useState(null);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState(null);
  const [toastMsg, setToastMsg] = useState('');

  // Pending Citizen Incident Triage State
  const [pendingCrimes, setPendingCrimes] = useState([]);
  const [loadingPending, setLoadingPending] = useState(false);
  const [triageNotes, setTriageNotes] = useState({});
  const [triageActionLoading, setTriageActionLoading] = useState(null);

  // Form state
  const [formData, setFormData] = useState({
    title: '',
    crime_type: 'Theft',
    published_date: new Date().toISOString().slice(0, 10),
    locality: 'Katpadi',
    district: 'Vellore',
    latitude: '12.9806',
    longitude: '79.1368',
    severity: 'HIGH',
    description: '',
    source: 'Tamil Nadu Police Portal',
    url: '',
  });
  const [saving, setSaving] = useState(false);

  const fetchCrimes = useCallback(async () => {
    setLoading(true);
    try {
      const res = await adminService.getCrimes({
        page,
        per_page: perPage,
        q: searchTerm,
        crime_type: selectedType,
        severity: selectedSeverity,
        sort_by: sortBy,
        order: sortOrder,
      });
      setCrimes(res.crimes || []);
      setTotal(res.total || 0);
      setPages(res.pages || 1);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [page, perPage, searchTerm, selectedType, selectedSeverity, sortBy, sortOrder]);

  const fetchPendingCrimes = useCallback(async () => {
    setLoadingPending(true);
    try {
      const res = await adminService.getPendingCrimes();
      setPendingCrimes(Array.isArray(res) ? res : res.data || []);
    } catch (err) {
      console.error('Failed to fetch pending reports:', err);
    } finally {
      setLoadingPending(false);
    }
  }, []);

  useEffect(() => {
    fetchCrimes();
    fetchPendingCrimes();
  }, [fetchCrimes, fetchPendingCrimes]);

  const showToast = (msg) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(''), 4000);
  };

  const handleApproveReport = async (crimeId) => {
    setTriageActionLoading(crimeId);
    try {
      const notes = triageNotes[crimeId] || '';
      await adminService.approveCrime(crimeId, notes);
      showToast(`Incident #${crimeId} approved and added to active registry!`);
      setPendingCrimes((prev) => prev.filter((c) => c.id !== crimeId));
      fetchCrimes();
    } catch (err) {
      showToast(`Failed to approve: ${err.message}`);
    } finally {
      setTriageActionLoading(null);
    }
  };

  const handleRejectReport = async (crimeId) => {
    setTriageActionLoading(crimeId);
    try {
      const notes = triageNotes[crimeId] || '';
      await adminService.rejectCrime(crimeId, notes);
      showToast(`Incident #${crimeId} rejected.`);
      setPendingCrimes((prev) => prev.filter((c) => c.id !== crimeId));
    } catch (err) {
      showToast(`Failed to reject: ${err.message}`);
    } finally {
      setTriageActionLoading(null);
    }
  };

  const handleOpenAdd = () => {
    setEditingCrime(null);
    setFormData({
      title: '',
      crime_type: 'Theft',
      published_date: new Date().toISOString().slice(0, 10),
      locality: 'Katpadi',
      district: 'Vellore',
      latitude: '12.9806',
      longitude: '79.1368',
      severity: 'HIGH',
      description: '',
      source: 'Tamil Nadu Police Portal',
      url: '',
    });
    setShowAddModal(true);
  };

  const handleOpenEdit = (c) => {
    setEditingCrime(c);
    setFormData({
      title: c.title || '',
      crime_type: c.crime_type || 'Theft',
      published_date: c.published_date || c.crime_date || '',
      locality: c.locality || c.location_name || '',
      district: c.district || 'Vellore',
      latitude: c.latitude ? String(c.latitude) : '',
      longitude: c.longitude ? String(c.longitude) : '',
      severity: (c.severity || c.risk_level || 'MEDIUM').toUpperCase(),
      description: c.description || '',
      source: c.source || '',
      url: c.url || '',
    });
    setShowAddModal(true);
  };

  const handleSaveCrime = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      if (editingCrime) {
        await adminService.updateCrime(editingCrime.id, formData);
        showToast('Incident updated successfully.');
      } else {
        await adminService.createCrime(formData);
        showToast('New crime incident added to registry.');
      }
      setShowAddModal(false);
      setEditingCrime(null);
      fetchCrimes();
    } catch (err) {
      alert(err.message || 'Failed to save incident');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteCrime = async (id, title) => {
    if (window.confirm(`Delete incident: "${title}"? This cannot be undone.`)) {
      try {
        await adminService.deleteCrime(id);
        showToast('Incident record deleted.');
        fetchCrimes();
      } catch (err) {
        alert(err.message || 'Failed to delete incident');
      }
    }
  };

  const handleImportSubmit = async (e) => {
    e.preventDefault();
    if (!importFile) return;
    setImporting(true);
    setImportResult(null);
    try {
      const res = await adminService.importCrimesCsv(importFile);
      setImportResult({
        success: true,
        message: res.message,
      });
      showToast(res.message);
      fetchCrimes();
      setTimeout(() => {
        setShowImportModal(false);
        setImportFile(null);
      }, 2000);
    } catch (err) {
      setImportResult({
        success: false,
        message: err.message || 'CSV Import failed',
      });
    } finally {
      setImporting(false);
    }
  };

  const handleExportCsv = () => {
    const url = adminService.getExportCsvUrl({
      q: searchTerm,
      crime_type: selectedType,
      severity: selectedSeverity,
    });
    window.open(url, '_blank');
  };

  // Filtered valid coordinates for map markers
  const mapCrimes = crimes.filter((c) => c.latitude && c.longitude);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-black tracking-tight text-white">Crime Incident Registry</h1>
            <span className="text-[10px] font-bold text-blue-400 bg-blue-950/80 px-2.5 py-0.5 rounded-full border border-blue-800">
              {total} Total Records
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Browse, search, edit, create, and import verified law enforcement crime records
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* View Tab Toggle */}
          <div className="bg-slate-900 border border-slate-800 p-1 rounded-xl flex gap-1 text-xs">
            {['both', 'table', 'map', 'pending'].map((tab) => (
              <button
                key={tab}
                type="button"
                onClick={() => setActiveTab(tab)}
                className={`px-3 py-1.5 rounded-lg font-bold capitalize transition-all flex items-center gap-1.5 ${
                  activeTab === tab ? 'bg-red-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
                }`}
              >
                <span>{tab === 'pending' ? 'Pending Triage' : tab}</span>
                {tab === 'pending' && pendingCrimes.length > 0 && (
                  <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-amber-400 text-slate-950 font-black animate-pulse">
                    {pendingCrimes.length}
                  </span>
                )}
              </button>
            ))}
          </div>

          <button
            type="button"
            onClick={handleExportCsv}
            className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold border border-slate-700 flex items-center gap-1.5 transition-colors"
          >
            <Download className="w-3.5 h-3.5 text-blue-400" />
            <span>Export CSV</span>
          </button>

          <button
            type="button"
            onClick={() => setShowImportModal(true)}
            className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold border border-slate-700 flex items-center gap-1.5 transition-colors"
          >
            <Upload className="w-3.5 h-3.5 text-emerald-400" />
            <span>Import CSV</span>
          </button>

          <button
            type="button"
            onClick={handleOpenAdd}
            className="px-3.5 py-2 rounded-xl bg-red-600 hover:bg-red-700 text-white text-xs font-bold shadow-md shadow-red-600/30 flex items-center gap-1.5 transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>Add Incident</span>
          </button>
        </div>
      </div>

      {toastMsg && (
        <div className="p-3 bg-emerald-950/90 border border-emerald-700 text-emerald-200 rounded-xl text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{toastMsg}</span>
        </div>
      )}

      {/* Filter & Search Bar */}
      <div className="p-4 bg-slate-900 border border-slate-800 rounded-2xl space-y-3">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {/* Search text */}
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
            <input
              type="text"
              placeholder="Search by locality, type, title..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setPage(1);
              }}
              className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-red-500"
            />
          </div>

          {/* Crime Type Select */}
          <div>
            <select
              value={selectedType}
              onChange={(e) => {
                setSelectedType(e.target.value);
                setPage(1);
              }}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-red-500"
            >
              {CRIME_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t === 'All' ? 'All Crime Types' : t}
                </option>
              ))}
            </select>
          </div>

          {/* Severity Select */}
          <div>
            <select
              value={selectedSeverity}
              onChange={(e) => {
                setSelectedSeverity(e.target.value);
                setPage(1);
              }}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-red-500"
            >
              {SEVERITIES.map((s) => (
                <option key={s} value={s}>
                  {s === 'All' ? 'All Severity Levels' : s}
                </option>
              ))}
            </select>
          </div>

          {/* Sort By */}
          <div className="flex gap-2">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="flex-1 px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-red-500"
            >
              <option value="published_date">Sort: Incident Date</option>
              <option value="crime_type">Sort: Crime Type</option>
              <option value="locality">Sort: Locality</option>
              <option value="severity">Sort: Severity</option>
            </select>
            <button
              type="button"
              onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
              className="px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs font-bold text-slate-300 hover:text-white"
            >
              {sortOrder.toUpperCase()}
            </button>
          </div>
        </div>
      </div>

      {/* Interactive Map Section (if activeTab is 'map' or 'both') */}
      {(activeTab === 'map' || activeTab === 'both') && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <MapPin className="w-4 h-4 text-red-500" />
              <h3 className="text-sm font-bold text-white">Geographic Map & Danger Clusters</h3>
              <span className="text-[10px] text-slate-400">({mapCrimes.length} incidents plotted)</span>
            </div>
            <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer">
              <input
                type="checkbox"
                checked={showHotspots}
                onChange={(e) => setShowHotspots(e.target.checked)}
                className="w-4 h-4 rounded text-red-600 accent-red-600"
              />
              <span>Render Hotspot Radius</span>
            </label>
          </div>

          <div className="h-80 sm:h-96 rounded-xl overflow-hidden border border-slate-800 z-10">
            <MapContainer
              center={[12.9165, 79.1325]}
              zoom={13}
              style={{ height: '100%', width: '100%', background: '#0f172a' }}
            >
              <TileLayer
                attribution="&copy; OpenStreetMap contributors"
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              {mapCrimes.map((c) => (
                <React.Fragment key={c.id}>
                  <Marker
                    position={[c.latitude, c.longitude]}
                    icon={createMarkerIcon(c.severity || c.risk_level)}
                  >
                    <Popup>
                      <div className="p-1 space-y-1 text-slate-900">
                        <span className="font-black text-xs block">{c.crime_type}</span>
                        <p className="text-[11px] text-slate-600">{c.locality || c.district}</p>
                        <span className="text-[10px] font-bold px-1.5 py-0.2 rounded bg-red-100 text-red-700">
                          {c.severity || 'HIGH'}
                        </span>
                        <p className="text-[10px] text-slate-500">{c.published_date}</p>
                      </div>
                    </Popup>
                  </Marker>
                  {showHotspots && (
                    <Circle
                      center={[c.latitude, c.longitude]}
                      radius={300}
                      pathOptions={{
                        color: getSeverityColor(c.severity || c.risk_level),
                        fillColor: getSeverityColor(c.severity || c.risk_level),
                        fillOpacity: 0.15,
                        weight: 1,
                      }}
                    />
                  )}
                </React.Fragment>
              ))}
            </MapContainer>
          </div>
        </div>
      )}

      {/* Paginated Table (if activeTab is 'table' or 'both') */}
      {(activeTab === 'table' || activeTab === 'both') && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
          <div className="p-4 border-b border-slate-800 flex items-center justify-between">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Database className="w-4 h-4 text-blue-400" />
              <span>Incident Records</span>
            </h3>
            <span className="text-xs text-slate-400">
              Showing {(page - 1) * perPage + 1} - {Math.min(page * perPage, total)} of {total}
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950/80 text-slate-400 font-bold border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Article ID / Ref</th>
                  <th className="py-3 px-4">Date</th>
                  <th className="py-3 px-4">Crime Type</th>
                  <th className="py-3 px-4">Locality / District</th>
                  <th className="py-3 px-4">Coordinates</th>
                  <th className="py-3 px-4">Severity</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {loading ? (
                  <tr>
                    <td colSpan={7} className="py-12 text-center text-slate-500">
                      <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-red-500" />
                      Loading incident database...
                    </td>
                  </tr>
                ) : crimes.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="py-12 text-center text-slate-500">
                      No matching incident records found.
                    </td>
                  </tr>
                ) : (
                  crimes.map((c) => (
                    <tr key={c.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-3 px-4 font-mono text-[11px] text-slate-400">
                        {c.article_id || `#${c.id}`}
                      </td>
                      <td className="py-3 px-4 whitespace-nowrap text-slate-200 font-medium">
                        {c.published_date || c.crime_date || 'N/A'}
                      </td>
                      <td className="py-3 px-4 font-bold text-white">{c.crime_type}</td>
                      <td className="py-3 px-4">
                        <span className="text-slate-200 block font-medium">{c.locality || 'Vellore'}</span>
                        <span className="text-[10px] text-slate-500 block">{c.district || 'Vellore'}</span>
                      </td>
                      <td className="py-3 px-4 font-mono text-[11px] text-slate-400">
                        {c.latitude && c.longitude ? (
                          <span>{c.latitude.toFixed(4)}, {c.longitude.toFixed(4)}</span>
                        ) : (
                          <span className="text-slate-600">No GPS</span>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`inline-block text-[10px] font-black px-2 py-0.5 rounded-full ${
                            (c.severity || c.risk_level || '').toUpperCase().includes('CRITICAL') ||
                            (c.severity || c.risk_level || '').toUpperCase().includes('HIGH')
                              ? 'bg-rose-950 text-rose-400 border border-rose-800'
                              : (c.severity || c.risk_level || '').toUpperCase().includes('MEDIUM')
                              ? 'bg-amber-950 text-amber-400 border border-amber-800'
                              : 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                          }`}
                        >
                          {c.severity || c.risk_level || 'MEDIUM'}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            type="button"
                            onClick={() => handleOpenEdit(c)}
                            className="p-1.5 text-slate-400 hover:text-blue-400 hover:bg-slate-800 rounded-lg transition-colors"
                            title="Edit incident"
                          >
                            <Edit3 className="w-4 h-4" />
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDeleteCrime(c.id, c.title || c.crime_type)}
                            className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-slate-800 rounded-lg transition-colors"
                            title="Delete incident"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
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
      )}

      {/* ===================================================================== */}
      {/* PENDING CITIZEN TRIAGE QUEUE (if activeTab is 'pending')              */}
      {/* ===================================================================== */}
      {activeTab === 'pending' && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden space-y-4 p-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-amber-400" />
                <span>Citizen Incident Triage Queue</span>
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-amber-400/10 text-amber-400 border border-amber-400/30 font-bold">
                  {pendingCrimes.length} Awaiting Verification
                </span>
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Review submitted citizen reports. Approving adds the incident to the active registry and feeds DBSCAN clustering and risk maps.
              </p>
            </div>
            <button
              type="button"
              onClick={fetchPendingCrimes}
              disabled={loadingPending}
              className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold border border-slate-700 flex items-center gap-1.5 transition-colors self-start sm:self-auto"
            >
              <RefreshCw className={`w-3.5 h-3.5 text-blue-400 ${loadingPending ? 'animate-spin' : ''}`} />
              <span>Refresh Queue</span>
            </button>
          </div>

          {loadingPending ? (
            <div className="py-16 text-center text-slate-400 text-xs">
              <RefreshCw className="w-6 h-6 animate-spin text-amber-400 mx-auto mb-2" />
              Loading pending reports...
            </div>
          ) : pendingCrimes.length === 0 ? (
            <div className="py-16 text-center text-slate-400 space-y-2">
              <div className="w-12 h-12 rounded-2xl bg-emerald-950/60 text-emerald-400 border border-emerald-800/60 mx-auto flex items-center justify-center">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <h4 className="text-sm font-bold text-slate-200">Triage Queue is Empty</h4>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                All citizen-submitted incident reports have been reviewed and verified. Newly filed reports will appear here automatically.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {pendingCrimes.map((crime) => (
                <div
                  key={crime.id}
                  className="bg-slate-950 border border-slate-800 rounded-2xl p-4 space-y-3 hover:border-slate-700 transition-colors"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/60 pb-3">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs text-slate-500 font-bold">#{crime.id}</span>
                      <span className="font-bold text-sm text-white">{crime.crime_type}</span>
                      <span
                        className="text-[10px] font-bold px-2 py-0.5 rounded-full"
                        style={{
                          backgroundColor: `${getSeverityColor(crime.severity)}20`,
                          color: getSeverityColor(crime.severity),
                          border: `1px solid ${getSeverityColor(crime.severity)}40`,
                        }}
                      >
                        {crime.severity || 'Medium'} Severity
                      </span>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-slate-400">
                      <span>Reported by: <strong className="text-slate-200">{crime.reported_by_name || 'Citizen'}</strong></span>
                      <span>Date: <strong className="text-slate-200">{crime.crime_date ? new Date(crime.crime_date).toLocaleDateString() : 'N/A'}</strong></span>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                    <div className="md:col-span-2 space-y-2">
                      <div className="flex items-center gap-1.5 text-slate-300 font-medium">
                        <MapPin className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                        <span>{crime.location_name || crime.locality || 'Location unverified'}</span>
                        {crime.latitude && crime.longitude && (
                          <span className="text-[10px] font-mono text-slate-500">
                            ({crime.latitude.toFixed(4)}, {crime.longitude.toFixed(4)})
                          </span>
                        )}
                      </div>
                      <p className="text-slate-400 bg-slate-900/80 p-3 rounded-xl border border-slate-800/80 text-xs leading-relaxed">
                        {crime.description || 'No additional narrative provided.'}
                      </p>
                    </div>

                    <div className="space-y-2 flex flex-col justify-between">
                      <div>
                        <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">
                          Admin Review Notes (Optional)
                        </label>
                        <textarea
                          rows={2}
                          placeholder="Feedback or rationale..."
                          value={triageNotes[crime.id] || ''}
                          onChange={(e) => setTriageNotes({ ...triageNotes, [crime.id]: e.target.value })}
                          className="w-full text-xs p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 focus:outline-none focus:border-blue-500"
                        />
                      </div>

                      <div className="flex items-center gap-2 pt-1">
                        <button
                          type="button"
                          disabled={triageActionLoading === crime.id}
                          onClick={() => handleApproveReport(crime.id)}
                          className="flex-1 py-2 px-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-xs active:scale-95 transition-all flex items-center justify-center gap-1.5 disabled:opacity-50"
                        >
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>Approve</span>
                        </button>
                        <button
                          type="button"
                          disabled={triageActionLoading === crime.id}
                          onClick={() => handleRejectReport(crime.id)}
                          className="flex-1 py-2 px-3 rounded-xl bg-red-600 hover:bg-red-500 text-white font-bold text-xs shadow-xs active:scale-95 transition-all flex items-center justify-center gap-1.5 disabled:opacity-50"
                        >
                          <XCircle className="w-3.5 h-3.5" />
                          <span>Reject</span>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ===================================================================== */}
      {/* MODAL: ADD / EDIT INCIDENT                                            */}
      {/* ===================================================================== */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl max-w-lg w-full p-6 space-y-4 shadow-2xl text-slate-200 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Database className="w-4 h-4 text-red-500" />
                <span>{editingCrime ? `Edit Incident #${editingCrime.id}` : 'Add New Crime Incident'}</span>
              </h3>
              <button
                type="button"
                onClick={() => setShowAddModal(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveCrime} className="space-y-3.5 text-xs">
              <div>
                <label className="text-[11px] font-bold text-slate-400 block mb-1">Crime Type *</label>
                <select
                  value={formData.crime_type}
                  onChange={(e) => setFormData({ ...formData, crime_type: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-red-500"
                >
                  {CRIME_TYPES.filter((t) => t !== 'All').map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] font-bold text-slate-400 block mb-1">Incident Date *</label>
                  <input
                    type="date"
                    required
                    value={formData.published_date}
                    onChange={(e) => setFormData({ ...formData, published_date: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-red-500"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-bold text-slate-400 block mb-1">Severity Rating *</label>
                  <select
                    value={formData.severity}
                    onChange={(e) => setFormData({ ...formData, severity: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-red-500"
                  >
                    <option value="CRITICAL">CRITICAL</option>
                    <option value="HIGH">HIGH</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="LOW">LOW</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] font-bold text-slate-400 block mb-1">Locality / Landmark *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Katpadi, Bagayam"
                    value={formData.locality}
                    onChange={(e) => setFormData({ ...formData, locality: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-red-500"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-bold text-slate-400 block mb-1">District</label>
                  <input
                    type="text"
                    value={formData.district}
                    onChange={(e) => setFormData({ ...formData, district: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-red-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] font-bold text-slate-400 block mb-1">Latitude</label>
                  <input
                    type="number"
                    step="any"
                    placeholder="12.9806"
                    value={formData.latitude}
                    onChange={(e) => setFormData({ ...formData, latitude: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-red-500"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-bold text-slate-400 block mb-1">Longitude</label>
                  <input
                    type="number"
                    step="any"
                    placeholder="79.1368"
                    value={formData.longitude}
                    onChange={(e) => setFormData({ ...formData, longitude: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-red-500"
                  />
                </div>
              </div>

              <div>
                <label className="text-[11px] font-bold text-slate-400 block mb-1">Description / Summary</label>
                <textarea
                  rows={2}
                  placeholder="Summary of incident reported..."
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-red-500"
                />
              </div>

              <div className="flex gap-2 pt-2">
                <button
                  type="submit"
                  disabled={saving}
                  className="flex-1 py-2.5 rounded-xl bg-red-600 hover:bg-red-700 text-white font-bold text-xs shadow-md shadow-red-600/30 transition-colors"
                >
                  {saving ? 'Saving Incident...' : editingCrime ? 'Update Incident' : 'Create Incident'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2.5 rounded-xl bg-slate-800 text-slate-300 font-bold text-xs"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ===================================================================== */}
      {/* MODAL: CSV IMPORT                                                     */}
      {/* ===================================================================== */}
      {showImportModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl max-w-md w-full p-6 space-y-4 shadow-2xl text-slate-200">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Upload className="w-4 h-4 text-emerald-400" />
                <span>Import Crime Records (CSV)</span>
              </h3>
              <button
                type="button"
                onClick={() => setShowImportModal(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleImportSubmit} className="space-y-4 text-xs">
              <p className="text-slate-400 leading-relaxed">
                Upload a CSV file containing columns: <code className="text-emerald-400 font-mono">crime_type, locality, published_date, severity, latitude, longitude</code>.
              </p>

              <div className="p-4 border-2 border-dashed border-slate-700 hover:border-emerald-500 rounded-2xl text-center space-y-2 cursor-pointer transition-colors bg-slate-950">
                <Upload className="w-8 h-8 text-slate-500 mx-auto" />
                <input
                  type="file"
                  accept=".csv"
                  required
                  onChange={(e) => setImportFile(e.target.files[0])}
                  className="w-full text-xs text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-slate-800 file:text-slate-200 hover:file:bg-slate-700"
                />
              </div>

              {importResult && (
                <div
                  className={`p-3 rounded-xl border text-xs ${
                    importResult.success
                      ? 'bg-emerald-950 border-emerald-800 text-emerald-300'
                      : 'bg-red-950 border-red-800 text-red-300'
                  }`}
                >
                  {importResult.message}
                </div>
              )}

              <div className="flex gap-2 pt-2">
                <button
                  type="submit"
                  disabled={importing || !importFile}
                  className="flex-1 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs disabled:opacity-40 transition-colors"
                >
                  {importing ? 'Processing CSV...' : 'Start Import'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowImportModal(false)}
                  className="px-4 py-2.5 rounded-xl bg-slate-800 text-slate-300 font-bold text-xs"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
