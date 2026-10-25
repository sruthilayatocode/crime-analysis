import React, { useState, useEffect } from 'react';
import {
  X,
  AlertTriangle,
  FileText,
  MapPin,
  Calendar,
  Clock,
  ShieldAlert,
  CheckCircle2,
  Clock3,
  XCircle,
  Loader2,
  PlusCircle,
  Eye,
} from 'lucide-react';
import { reportCrime, getMyReports } from '../../services/crimeService';

const CRIME_CATEGORIES = [
  'Theft',
  'Robbery',
  'Burglary',
  'Assault',
  'Chain Snatching',
  'Vehicle Theft',
  'Fraud / Cybercrime',
  'Harassment',
  'Vandalism',
  'Suspicious Activity',
  'Other',
];

const SEVERITIES = [
  { label: 'Low', value: 'Low', color: 'bg-emerald-50 text-emerald-700 border-emerald-300' },
  { label: 'Medium', value: 'Medium', color: 'bg-amber-50 text-amber-700 border-amber-300' },
  { label: 'High', value: 'High', color: 'bg-orange-50 text-orange-700 border-orange-300' },
  { label: 'Critical', value: 'Critical', color: 'bg-red-50 text-red-700 border-red-300' },
];

export default function CitizenReportModal({ isOpen, onClose, initialCoords, initialLocation }) {
  const [activeTab, setActiveTab] = useState('new'); // 'new' | 'my-reports'
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successReport, setSuccessReport] = useState(null);

  // Form fields
  const [crimeType, setCrimeType] = useState('Theft');
  const [customCrimeType, setCustomCrimeType] = useState('');
  const [locationName, setLocationName] = useState('');
  const [includeCoords, setIncludeCoords] = useState(true);
  const [latitude, setLatitude] = useState('');
  const [longitude, setLongitude] = useState('');
  const [crimeDate, setCrimeDate] = useState('');
  const [severity, setSeverity] = useState('Medium');
  const [description, setDescription] = useState('');

  // My Reports list state
  const [myReportsList, setMyReportsList] = useState([]);
  const [loadingReports, setLoadingReports] = useState(false);

  // Pre-fill on open
  useEffect(() => {
    if (isOpen) {
      setLocationName(initialLocation || '');
      if (initialCoords && initialCoords.lat && initialCoords.lng) {
        setLatitude(String(initialCoords.lat.toFixed(6)));
        setLongitude(String(initialCoords.lng.toFixed(6)));
      }
      // Current ISO date string formatted for datetime-local
      const now = new Date();
      now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
      setCrimeDate(now.toISOString().slice(0, 16));
      setErrorMsg('');
      setSuccessReport(null);
    }
  }, [isOpen, initialCoords, initialLocation]);

  // Load user's previous reports when switching to 'my-reports' tab
  const loadUserReports = async () => {
    setLoadingReports(true);
    try {
      const data = await getMyReports();
      setMyReportsList(data);
    } catch (err) {
      console.error('Failed to load user reports:', err);
    } finally {
      setLoadingReports(false);
    }
  };

  useEffect(() => {
    if (isOpen && activeTab === 'my-reports') {
      loadUserReports();
    }
  }, [isOpen, activeTab]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');

    const token =
      localStorage.getItem('crimesense_token') ||
      localStorage.getItem('token') ||
      localStorage.getItem('authToken');
    if (!token) {
      setErrorMsg('You must be logged in to report an incident. Please log in first.');
      return;
    }

    const resolvedCrimeType = crimeType === 'Other' && customCrimeType.trim()
      ? customCrimeType.trim()
      : crimeType;

    if (!resolvedCrimeType) {
      setErrorMsg('Please select or specify a crime category.');
      return;
    }
    if (!locationName.trim()) {
      setErrorMsg('Please specify the incident location name.');
      return;
    }
    if (!description.trim()) {
      setErrorMsg('Please provide a brief description of the incident.');
      return;
    }

    const payload = {
      crime_type: resolvedCrimeType,
      location_name: locationName.trim(),
      description: description.trim(),
      crime_date: crimeDate ? crimeDate.replace('T', ' ') : new Date().toISOString().slice(0, 19).replace('T', ' '),
      severity: severity,
    };

    if (includeCoords && latitude && longitude) {
      const latF = parseFloat(latitude);
      const lngF = parseFloat(longitude);
      if (!isNaN(latF) && !isNaN(lngF)) {
        payload.latitude = latF;
        payload.longitude = lngF;
      }
    }

    setSubmitting(true);
    try {
      const res = await reportCrime(payload);
      setSuccessReport(res.data || res);
      // Reset form
      setDescription('');
      setCustomCrimeType('');
    } catch (err) {
      setErrorMsg(err.message || 'Failed to submit incident report. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusBadge = (status) => {
    const s = (status || 'PENDING').toUpperCase();
    if (s === 'APPROVED') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> Approved
        </span>
      );
    }
    if (s === 'REJECTED') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-100 text-red-800">
          <XCircle className="w-3.5 h-3.5 text-red-600" /> Rejected
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800">
        <Clock3 className="w-3.5 h-3.5 text-amber-600" /> Pending Review
      </span>
    );
  };

  return (
    <div className="fixed inset-0 z-[1200] flex items-center justify-center p-3 bg-black/60 backdrop-blur-sm animate-in fade-in-50">
      <div className="relative w-full max-w-lg bg-white rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh] border border-slate-200">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-700 via-blue-800 to-indigo-900 text-white p-4 px-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-white/10 flex items-center justify-center backdrop-blur-md">
              <ShieldAlert className="w-5 h-5 text-blue-200" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white">Citizen Incident Reporting</h2>
              <p className="text-xs text-blue-200">Report suspicious events for police verification</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-white/80 hover:text-white rounded-xl hover:bg-white/10 transition-colors"
            aria-label="Close dialog"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab switcher */}
        <div className="flex border-b border-slate-200 bg-slate-50 px-6 pt-3 gap-2">
          <button
            type="button"
            onClick={() => { setActiveTab('new'); setSuccessReport(null); }}
            className={`pb-2.5 px-3 text-xs font-bold transition-all border-b-2 flex items-center gap-1.5 ${
              activeTab === 'new'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <PlusCircle className="w-3.5 h-3.5" />
            Report Incident
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('my-reports')}
            className={`pb-2.5 px-3 text-xs font-bold transition-all border-b-2 flex items-center gap-1.5 ${
              activeTab === 'my-reports'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            My Reported Incidents ({myReportsList.length})
          </button>
        </div>

        {/* Body content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {errorMsg && (
            <div className="p-3 rounded-2xl bg-red-50 border border-red-200 text-red-800 text-xs flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-red-600 shrink-0" />
                <span>{errorMsg}</span>
              </div>
              {(errorMsg.toLowerCase().includes('token') || errorMsg.toLowerCase().includes('auth')) && (
                <a
                  href="/login"
                  className="px-2.5 py-1 bg-red-600 hover:bg-red-700 text-white font-semibold rounded-lg text-[11px] whitespace-nowrap transition-colors"
                >
                  Log In Now
                </a>
              )}
            </div>
          )}

          {activeTab === 'new' && !successReport && (
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Category */}
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Incident Category *
                </label>
                <select
                  value={crimeType}
                  onChange={(e) => setCrimeType(e.target.value)}
                  className="w-full text-xs font-semibold p-2.5 rounded-xl border border-slate-300 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {CRIME_CATEGORIES.map((cat) => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
                {crimeType === 'Other' && (
                  <input
                    type="text"
                    placeholder="Specify crime type..."
                    value={customCrimeType}
                    onChange={(e) => setCustomCrimeType(e.target.value)}
                    className="mt-2 w-full text-xs p-2.5 rounded-xl border border-slate-300 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                )}
              </div>

              {/* Location Name */}
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Location / Landmark *
                </label>
                <div className="relative">
                  <MapPin className="w-4 h-4 text-slate-400 absolute left-3 top-3 pointer-events-none" />
                  <input
                    type="text"
                    required
                    placeholder="e.g. Katpadi Railway Junction, Main Road"
                    value={locationName}
                    onChange={(e) => setLocationName(e.target.value)}
                    className="w-full text-xs pl-9 pr-3 py-2.5 rounded-xl border border-slate-300 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              {/* GPS Coordinates toggler */}
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-2xl space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                    <MapPin className="w-3.5 h-3.5 text-blue-600" />
                    Attach Precise GPS Coordinates
                  </span>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={includeCoords}
                      onChange={(e) => setIncludeCoords(e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-8 h-4 bg-slate-300 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>

                {includeCoords && (
                  <div className="grid grid-cols-2 gap-2 pt-1 text-slate-700">
                    <div>
                      <span className="text-[10px] text-slate-500 uppercase font-semibold">Latitude</span>
                      <input
                        type="number"
                        step="any"
                        value={latitude}
                        onChange={(e) => setLatitude(e.target.value)}
                        placeholder="12.9806"
                        className="w-full text-xs p-2 rounded-lg border border-slate-300 bg-white"
                      />
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500 uppercase font-semibold">Longitude</span>
                      <input
                        type="number"
                        step="any"
                        value={longitude}
                        onChange={(e) => setLongitude(e.target.value)}
                        placeholder="79.1368"
                        className="w-full text-xs p-2 rounded-lg border border-slate-300 bg-white"
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Date & Severity Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Date & Time of Incident *
                  </label>
                  <input
                    type="datetime-local"
                    required
                    value={crimeDate}
                    onChange={(e) => setCrimeDate(e.target.value)}
                    className="w-full text-xs p-2.5 rounded-xl border border-slate-300 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Perceived Severity
                  </label>
                  <div className="grid grid-cols-4 gap-1">
                    {SEVERITIES.map((s) => (
                      <button
                        key={s.value}
                        type="button"
                        onClick={() => setSeverity(s.value)}
                        className={`text-[11px] font-bold py-2 rounded-xl border transition-all text-center ${
                          severity === s.value
                            ? `${s.color} ring-2 ring-blue-500/50 shadow-xs font-extrabold`
                            : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                        }`}
                      >
                        {s.label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Description */}
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Incident Description *
                </label>
                <textarea
                  rows={3}
                  required
                  placeholder="Describe what occurred, any suspect descriptions, vehicle details, etc."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full text-xs p-3 rounded-xl border border-slate-300 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Submit CTA */}
              <div className="pt-2 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2.5 rounded-xl text-xs font-bold text-slate-600 hover:bg-slate-100 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-5 py-2.5 rounded-xl text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 shadow-md shadow-blue-500/20 active:scale-95 transition-all flex items-center gap-2 disabled:opacity-50"
                >
                  {submitting ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      Submitting...
                    </>
                  ) : (
                    <>
                      <ShieldAlert className="w-3.5 h-3.5" />
                      Submit Crime Report
                    </>
                  )}
                </button>
              </div>
            </form>
          )}

          {/* Success Screen */}
          {activeTab === 'new' && successReport && (
            <div className="py-6 text-center space-y-4 animate-in zoom-in-95">
              <div className="w-16 h-16 bg-emerald-100 text-emerald-600 rounded-3xl mx-auto flex items-center justify-center shadow-lg shadow-emerald-500/20">
                <CheckCircle2 className="w-8 h-8" />
              </div>
              <div className="space-y-1">
                <h3 className="text-base font-bold text-slate-900">Incident Report Submitted</h3>
                <p className="text-xs text-slate-500 max-w-sm mx-auto">
                  Your report has been securely saved to the CrimeSense database. An administrator will review and verify your submission before adding it to public crime hotspot maps.
                </p>
              </div>

              <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 text-left max-w-sm mx-auto space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-slate-500">Report ID:</span>
                  <span className="font-mono font-bold text-slate-800">#{successReport.id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Category:</span>
                  <span className="font-semibold text-slate-800">{successReport.crime_type}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Location:</span>
                  <span className="font-semibold text-slate-800 truncate max-w-[180px]">{successReport.location_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Current Status:</span>
                  {getStatusBadge(successReport.status)}
                </div>
              </div>

              <div className="flex items-center justify-center gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => { setSuccessReport(null); setActiveTab('my-reports'); }}
                  className="px-4 py-2 bg-blue-600 text-white rounded-xl text-xs font-bold hover:bg-blue-700 transition-all shadow-sm"
                >
                  View in My Reports
                </button>
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 bg-slate-100 text-slate-700 rounded-xl text-xs font-bold hover:bg-slate-200 transition-all"
                >
                  Done
                </button>
              </div>
            </div>
          )}

          {/* My Reports Tab */}
          {activeTab === 'my-reports' && (
            <div className="space-y-3">
              {loadingReports ? (
                <div className="py-12 flex flex-col items-center justify-center text-slate-400 gap-2">
                  <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
                  <span className="text-xs">Loading your incident reports...</span>
                </div>
              ) : myReportsList.length === 0 ? (
                <div className="py-12 text-center text-slate-500 space-y-2">
                  <FileText className="w-8 h-8 text-slate-300 mx-auto" />
                  <p className="text-xs font-semibold">No reports submitted yet.</p>
                  <p className="text-[11px] text-slate-400 max-w-xs mx-auto">
                    Any incidents you report will show here along with their administrator approval status.
                  </p>
                  <button
                    type="button"
                    onClick={() => setActiveTab('new')}
                    className="mt-2 px-3 py-1.5 bg-blue-600 text-white rounded-xl text-xs font-bold hover:bg-blue-700 transition-all"
                  >
                    File a Report Now
                  </button>
                </div>
              ) : (
                myReportsList.map((rep) => (
                  <div
                    key={rep.id}
                    className="p-3.5 bg-white border border-slate-200 rounded-2xl shadow-xs space-y-2 hover:border-blue-200 transition-all"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-xs text-slate-900">{rep.crime_type}</span>
                          <span className="text-[10px] font-mono text-slate-400">#{rep.id}</span>
                        </div>
                        <p className="text-[11px] text-slate-500 flex items-center gap-1 mt-0.5">
                          <MapPin className="w-3 h-3 text-slate-400" />
                          {rep.location_name || 'Location not specified'}
                        </p>
                      </div>
                      {getStatusBadge(rep.status)}
                    </div>

                    <p className="text-xs text-slate-600 line-clamp-2 bg-slate-50 p-2 rounded-xl">
                      {rep.description}
                    </p>

                    {rep.admin_notes && (
                      <div className="p-2 rounded-xl bg-blue-50/70 border border-blue-100 text-[11px] text-blue-900">
                        <span className="font-bold">Admin Feedback: </span>
                        <span>{rep.admin_notes}</span>
                      </div>
                    )}

                    <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1">
                      <span>Date: {rep.crime_date ? new Date(rep.crime_date).toLocaleDateString() : 'N/A'}</span>
                      <span className="font-semibold text-slate-500 uppercase">{rep.severity || 'Medium'} Severity</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
