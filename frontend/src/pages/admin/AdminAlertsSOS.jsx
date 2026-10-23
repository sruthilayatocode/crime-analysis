import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  BellRing,
  AlertTriangle,
  CheckCircle2,
  PhoneCall,
  MapPin,
  Clock,
  ExternalLink,
  MessageSquare,
  RefreshCw,
  Search,
  Filter,
  ShieldCheck,
  X,
  Volume2,
  VolumeX,
} from 'lucide-react';
import { adminService } from '../../services/adminService';
import { playAlertBeep } from '../../services/sosService';

export default function AdminAlertsSOS() {
  const [events, setEvents] = useState([]);
  const [activeCount, setActiveCount] = useState(0);
  const [loading, setLoading] = useState(true);

  // Filters
  const [statusFilter, setStatusFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [soundEnabled, setSoundEnabled] = useState(true);

  // Resolution modal state
  const [resolvingEvent, setResolvingEvent] = useState(null);
  const [resolutionNotes, setResolutionNotes] = useState('');
  const [resolving, setResolving] = useState(false);

  // Add notes modal state
  const [editingNotesEvent, setEditingNotesEvent] = useState(null);
  const [noteText, setNoteText] = useState('');
  const [savingNotes, setSavingNotes] = useState(false);

  const prevActiveCountRef = useRef(0);

  const fetchFeed = useCallback(async () => {
    try {
      const res = await adminService.getSOSFeed({
        status: statusFilter,
        type: typeFilter,
      });
      setEvents(res.events || []);
      const newActive = res.active_count || 0;
      setActiveCount(newActive);

      // Play sound if active count increased
      if (newActive > prevActiveCountRef.current && soundEnabled) {
        playAlertBeep(920, 0.4);
      }
      prevActiveCountRef.current = newActive;
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [statusFilter, typeFilter, soundEnabled]);

  useEffect(() => {
    fetchFeed();
    const interval = setInterval(fetchFeed, 8000); // 8s live poll
    return () => clearInterval(interval);
  }, [fetchFeed]);

  const handleOpenResolve = (e) => {
    setResolvingEvent(e);
    setResolutionNotes('Police unit dispatched and verified citizen is safe.');
  };

  const handleConfirmResolve = async () => {
    if (!resolvingEvent) return;
    setResolving(true);
    try {
      await adminService.resolveSOSEvent(resolvingEvent.id, resolutionNotes);
      setResolvingEvent(null);
      fetchFeed();
    } catch (err) {
      alert(err.message || 'Failed to resolve SOS event');
    } finally {
      setResolving(false);
    }
  };

  const handleOpenNotes = (e) => {
    setEditingNotesEvent(e);
    setNoteText('');
  };

  const handleSaveNotes = async () => {
    if (!editingNotesEvent || !noteText.trim()) return;
    setSavingNotes(true);
    try {
      await adminService.addSOSNotes(editingNotesEvent.id, noteText.trim());
      setEditingNotesEvent(null);
      fetchFeed();
    } catch (err) {
      alert(err.message || 'Failed to attach notes');
    } finally {
      setSavingNotes(false);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-black tracking-tight text-white">Emergency SOS Incident Feed</h1>
            {activeCount > 0 ? (
              <span className="text-xs font-black text-white bg-red-600 px-3 py-1 rounded-full animate-pulse flex items-center gap-1.5 shadow-lg shadow-red-600/40">
                <AlertTriangle className="w-4 h-4" />
                <span>{activeCount} Active Distress Events</span>
              </span>
            ) : (
              <span className="text-xs font-bold text-emerald-400 bg-emerald-950 px-3 py-1 rounded-full border border-emerald-800">
                All Safe & Clear
              </span>
            )}
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time emergency distress alerts from manual triggers and automated Red-Zone stationary timeouts
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Sound toggle */}
          <button
            type="button"
            onClick={() => setSoundEnabled(!soundEnabled)}
            className={`px-3 py-2 rounded-xl text-xs font-bold border transition-colors flex items-center gap-1.5 ${
              soundEnabled
                ? 'bg-slate-800 text-slate-200 border-slate-700'
                : 'bg-slate-900 text-slate-500 border-slate-800'
            }`}
          >
            {soundEnabled ? <Volume2 className="w-3.5 h-3.5 text-emerald-400" /> : <VolumeX className="w-3.5 h-3.5" />}
            <span>{soundEnabled ? 'Sound On' : 'Muted'}</span>
          </button>

          <button
            type="button"
            onClick={fetchFeed}
            disabled={loading}
            className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold border border-slate-700 flex items-center gap-1.5 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Poll Feed</span>
          </button>
        </div>
      </div>

      {/* Filters Bar */}
      <div className="p-4 bg-slate-900 border border-slate-800 rounded-2xl flex flex-wrap gap-3">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-slate-400">Status:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 font-bold focus:outline-none focus:border-red-500"
          >
            <option value="all">All Events</option>
            <option value="active">Active Only</option>
            <option value="resolved">Resolved</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-slate-400">Trigger Type:</span>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 font-bold focus:outline-none focus:border-red-500"
          >
            <option value="all">All Trigger Modes</option>
            <option value="manual">Manual SOS Button</option>
            <option value="auto_red_zone">Auto Red-Zone Inactivity</option>
          </select>
        </div>
      </div>

      {/* Events Feed Grid */}
      <div className="space-y-3">
        {loading && events.length === 0 ? (
          <div className="p-12 text-center text-slate-500 bg-slate-900 rounded-2xl border border-slate-800">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2 text-red-500" />
            <p className="text-xs">Connecting to real-time SOS broadcast stream...</p>
          </div>
        ) : events.length === 0 ? (
          <div className="p-12 text-center text-slate-400 bg-slate-900 rounded-2xl border border-slate-800 space-y-2">
            <ShieldCheck className="w-10 h-10 text-emerald-400 mx-auto" />
            <p className="text-sm font-bold text-white">No Emergency SOS Distress Incidents Found</p>
            <p className="text-xs text-slate-500">All registered citizens are safe and within normal thresholds.</p>
          </div>
        ) : (
          events.map((e) => {
            const isActive = e.status === 'active';
            const mapsUrl = `https://maps.google.com/?q=${e.latitude},${e.longitude}`;

            return (
              <div
                key={e.id}
                className={`p-5 rounded-2xl border transition-all ${
                  isActive
                    ? 'bg-red-950/80 border-red-700 shadow-xl shadow-red-950/50 ring-1 ring-red-600'
                    : 'bg-slate-900 border-slate-800'
                }`}
              >
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                  {/* Left info */}
                  <div className="space-y-2">
                    <div className="flex items-center gap-2.5 flex-wrap">
                      <span
                        className={`text-xs font-black px-2.5 py-0.5 rounded-full ${
                          isActive
                            ? 'bg-red-600 text-white animate-pulse'
                            : 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                        }`}
                      >
                        {isActive ? '🚨 ACTIVE DISTRESS' : 'RESOLVED'}
                      </span>

                      <span className="text-xs font-bold text-white">
                        SOS Event #{e.id}
                      </span>

                      <span className="text-[10px] font-bold text-slate-300 bg-slate-800 px-2 py-0.5 rounded-md">
                        Mode: {e.type === 'auto_red_zone' ? 'Automated Red-Zone Inactivity' : 'Manual SOS Trigger'}
                      </span>

                      <span
                        className={`text-[10px] font-black px-2 py-0.5 rounded-md ${
                          e.zone === 'red'
                            ? 'bg-red-900/60 text-red-300 border border-red-700'
                            : 'bg-slate-800 text-slate-300'
                        }`}
                      >
                        {(e.zone || 'green').toUpperCase()} ZONE
                      </span>
                    </div>

                    {/* User info */}
                    <div className="flex items-center gap-3 text-xs">
                      <span className="font-bold text-white">{e.user_name || 'Citizen'}</span>
                      <span className="text-slate-400 font-mono">({e.user_email || 'user@crimesense.com'})</span>
                    </div>

                    {/* Coordinates & Location link */}
                    <div className="flex items-center gap-3 text-xs text-slate-300">
                      <span className="font-mono">
                        Coords: {e.latitude.toFixed(5)}, {e.longitude.toFixed(5)}
                      </span>
                      <a
                        href={mapsUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="text-cyan-400 hover:text-cyan-300 font-bold flex items-center gap-1"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                        <span>Open in Google Maps</span>
                      </a>
                    </div>

                    {/* Notified Contacts */}
                    {e.contacts_notified && e.contacts_notified.length > 0 && (
                      <div className="flex items-center gap-2 text-[11px] text-slate-400 pt-1">
                        <PhoneCall className="w-3.5 h-3.5 text-emerald-400" />
                        <span>Notified {e.contacts_notified.length} contacts:</span>
                        <div className="flex gap-1.5 flex-wrap">
                          {e.contacts_notified.map((c, idx) => (
                            <span key={idx} className="px-1.5 py-0.2 rounded bg-slate-950 text-slate-300 font-mono border border-slate-800">
                              {c.contact_name || c.name} ({c.status || 'sent'})
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Admin Notes */}
                    {e.admin_notes && (
                      <div className="p-2.5 bg-slate-950 rounded-xl border border-slate-800 text-xs space-y-1 mt-2">
                        <span className="font-bold text-amber-400 flex items-center gap-1">
                          <MessageSquare className="w-3.5 h-3.5" />
                          <span>Police & Admin Operational Notes:</span>
                        </span>
                        <pre className="text-[11px] text-slate-300 whitespace-pre-wrap font-sans">
                          {e.admin_notes}
                        </pre>
                      </div>
                    )}
                  </div>

                  {/* Right actions */}
                  <div className="flex flex-col sm:flex-row lg:flex-col items-end gap-2 shrink-0">
                    <span className="text-[11px] text-slate-400 flex items-center gap-1 font-mono">
                      <Clock className="w-3.5 h-3.5" />
                      <span>{e.created_at}</span>
                    </span>

                    <div className="flex gap-2 w-full sm:w-auto">
                      <button
                        type="button"
                        onClick={() => handleOpenNotes(e)}
                        className="px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold border border-slate-700 flex items-center gap-1.5 transition-colors"
                      >
                        <MessageSquare className="w-3.5 h-3.5" />
                        <span>Add Note</span>
                      </button>

                      {isActive && (
                        <button
                          type="button"
                          onClick={() => handleOpenResolve(e)}
                          className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-md shadow-emerald-600/30 flex items-center gap-1.5 transition-colors"
                        >
                          <CheckCircle2 className="w-4 h-4" />
                          <span>Mark Resolved</span>
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* ===================================================================== */}
      {/* MODAL: RESOLVE SOS EVENT                                              */}
      {/* ===================================================================== */}
      {resolvingEvent && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl max-w-md w-full p-6 space-y-4 shadow-2xl text-slate-200">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                <span>Resolve SOS Distress Event #{resolvingEvent.id}</span>
              </h3>
              <button
                type="button"
                onClick={() => setResolvingEvent(null)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <p className="text-slate-400">
                Confirming resolution will resolve the distress signal and attach law enforcement notes.
              </p>

              <div>
                <label className="text-[11px] font-bold text-slate-400 block mb-1">Resolution Summary Notes</label>
                <textarea
                  rows={3}
                  value={resolutionNotes}
                  onChange={(e) => setResolutionNotes(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-emerald-500 text-xs"
                />
              </div>

              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={handleConfirmResolve}
                  disabled={resolving}
                  className="flex-1 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-md shadow-emerald-600/30 transition-colors"
                >
                  {resolving ? 'Resolving...' : 'Confirm Resolution'}
                </button>
                <button
                  type="button"
                  onClick={() => setResolvingEvent(null)}
                  className="px-4 py-2.5 rounded-xl bg-slate-800 text-slate-300 font-bold text-xs"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ===================================================================== */}
      {/* MODAL: ADD POLICE / ADMIN NOTES                                       */}
      {/* ===================================================================== */}
      {editingNotesEvent && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl max-w-md w-full p-6 space-y-4 shadow-2xl text-slate-200">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <MessageSquare className="w-5 h-5 text-amber-400" />
                <span>Attach Notes to Event #{editingNotesEvent.id}</span>
              </h3>
              <button
                type="button"
                onClick={() => setEditingNotesEvent(null)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="text-[11px] font-bold text-slate-400 block mb-1">Operational Observation / Notes</label>
                <textarea
                  rows={3}
                  required
                  placeholder="e.g. Patrol unit 44 dispatched to coordinates..."
                  value={noteText}
                  onChange={(e) => setNoteText(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-amber-500 text-xs"
                />
              </div>

              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={handleSaveNotes}
                  disabled={savingNotes || !noteText.trim()}
                  className="flex-1 py-2.5 rounded-xl bg-amber-600 hover:bg-amber-700 text-white font-bold text-xs transition-colors"
                >
                  {savingNotes ? 'Saving Note...' : 'Save Note'}
                </button>
                <button
                  type="button"
                  onClick={() => setEditingNotesEvent(null)}
                  className="px-4 py-2.5 rounded-xl bg-slate-800 text-slate-300 font-bold text-xs"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
