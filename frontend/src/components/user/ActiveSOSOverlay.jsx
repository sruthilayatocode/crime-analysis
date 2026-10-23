import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  CheckCircle2,
  PhoneCall,
  MapPin,
  ExternalLink,
  Radio,
  Clock,
  Users,
  AlertTriangle,
  RefreshCw,
} from 'lucide-react';
import { useSOS } from '../../context/SOSContext';

export default function ActiveSOSOverlay() {
  const {
    activeSosEvent,
    resolveSOS,
    extendLiveLocationSharing,
    isLiveTracking,
    sosStatusMessage,
  } = useSOS();

  const [resolving, setResolving] = useState(false);
  const [elapsedMinutes, setElapsedMinutes] = useState(0);

  useEffect(() => {
    if (!activeSosEvent) return;
    const interval = setInterval(() => {
      if (activeSosEvent.created_at) {
        const diffMs = Date.now() - new Date(activeSosEvent.created_at).getTime();
        setElapsedMinutes(Math.floor(diffMs / 60000));
      }
    }, 10000);
    return () => clearInterval(interval);
  }, [activeSosEvent]);

  if (!activeSosEvent) return null;

  const handleResolve = async () => {
    if (window.confirm("Are you sure you want to mark yourself SAFE? This will send an all-clear notification to your contacts.")) {
      setResolving(true);
      try {
        await resolveSOS();
      } finally {
        setResolving(false);
      }
    }
  };

  const notifiedContacts = activeSosEvent.contacts_notified || [];
  const mapsUrl =
    activeSosEvent.maps_url ||
    `https://maps.google.com/?q=${activeSosEvent.latitude},${activeSosEvent.longitude}`;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-red-950/90 backdrop-blur-lg overflow-y-auto animate-in fade-in duration-200">
      <div className="bg-white rounded-3xl max-w-md w-full my-auto shadow-2xl border-2 border-red-500 overflow-hidden flex flex-col">
        {/* Pulsing Emergency Banner */}
        <div className="bg-gradient-to-r from-red-600 via-rose-600 to-red-600 text-white p-5 text-center relative overflow-hidden">
          <div className="absolute inset-0 bg-white/10 animate-pulse pointer-events-none" />
          <div className="relative z-10 flex flex-col items-center">
            <div className="w-14 h-14 rounded-full bg-white/20 border border-white/40 flex items-center justify-center mb-2 animate-bounce">
              <ShieldAlert className="w-8 h-8 text-white stroke-[2.5]" />
            </div>
            <span className="inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full bg-black/25 text-[11px] font-black tracking-wider uppercase mb-1">
              <Radio className="w-3 h-3 text-red-300 animate-ping" />
              <span>SOS Signal Broadcast Active</span>
            </span>
            <h2 className="text-xl font-black tracking-tight">
              Emergency Distress Active
            </h2>
            <p className="text-xs text-red-100 mt-1 max-w-xs">
              Your location & emergency details have been sent to your trusted contacts.
            </p>
          </div>
        </div>

        {/* Content Body */}
        <div className="p-4 sm:p-5 space-y-4 max-h-[70vh] overflow-y-auto">
          {/* Quick Emergency 112 Call Card */}
          <a
            href="tel:112"
            className="w-full p-3.5 rounded-2xl bg-gradient-to-r from-red-700 to-rose-700 text-white font-bold flex items-center justify-between shadow-md hover:brightness-110 active:scale-98 transition-all min-h-[52px]"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center shrink-0">
                <PhoneCall className="w-5 h-5 text-white" />
              </div>
              <div className="text-left">
                <span className="text-sm font-black block">Call Emergency Helpline (112)</span>
                <span className="text-[11px] text-red-100 font-normal">Immediate Police / Ambulance Dispatch</span>
              </div>
            </div>
            <span className="text-xs font-black bg-white text-red-700 px-3 py-1.5 rounded-xl shadow-xs shrink-0">
              Dial 112
            </span>
          </a>

          {/* Location & Risk Zone Status */}
          <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                <MapPin className="w-4 h-4 text-red-500" />
                <span>Last Broadcast Coordinates</span>
              </span>
              <span className="text-[10px] font-black uppercase px-2 py-0.5 rounded-full bg-red-100 text-red-700">
                {activeSosEvent.zone || 'High Risk'} Zone
              </span>
            </div>

            <div className="flex items-center justify-between text-xs text-slate-600 font-mono bg-white p-2 rounded-xl border border-slate-200/70">
              <span>
                {activeSosEvent.latitude?.toFixed(5)}, {activeSosEvent.longitude?.toFixed(5)}
              </span>
              <a
                href={mapsUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-800 font-sans font-bold flex items-center gap-1 text-[11px]"
              >
                <span>Google Maps</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>

            <div className="flex items-center justify-between text-[11px] text-slate-500 pt-0.5">
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                <span>Active for {elapsedMinutes}m</span>
              </span>
              {isLiveTracking && (
                <span className="text-emerald-700 font-semibold flex items-center gap-1">
                  <RefreshCw className="w-3 h-3 animate-spin text-emerald-600" />
                  <span>Live GPS Syncing (1hr)</span>
                </span>
              )}
            </div>
          </div>

          {/* Contacts Notified List */}
          <div className="space-y-2">
            <span className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
              <Users className="w-4 h-4 text-slate-500" />
              <span>Notified Contacts ({notifiedContacts.length})</span>
            </span>

            <div className="space-y-1.5">
              {notifiedContacts.length > 0 ? (
                notifiedContacts.map((c, i) => (
                  <div
                    key={i}
                    className="p-2.5 rounded-xl bg-white border border-slate-200 flex items-center justify-between text-xs shadow-2xs"
                  >
                    <div>
                      <span className="font-bold text-slate-800">{c.contact_name}</span>
                      <span className="text-[11px] text-slate-500 font-mono block">
                        {c.contact_phone}
                      </span>
                    </div>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200">
                      SMS Sent
                    </span>
                  </div>
                ))
              ) : (
                <p className="text-xs text-slate-400 italic">Contacts dispatch queued.</p>
              )}
            </div>
          </div>

          {/* Action Buttons: "I'm Safe" and "Share Live Location" */}
          <div className="pt-2 space-y-2.5">
            {/* "I'm Safe" Button */}
            <button
              type="button"
              onClick={handleResolve}
              disabled={resolving}
              className="w-full py-3.5 px-4 rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-600 text-white font-black text-sm shadow-[0_4px_15px_rgba(16,185,129,0.35)] hover:shadow-[0_6px_20px_rgba(16,185,129,0.45)] active:scale-98 transition-all flex items-center justify-center gap-2 min-h-[48px]"
            >
              {resolving ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Resolving Alert...</span>
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-5 h-5 stroke-[2.5]" />
                  <span>I'm Safe &ndash; Resolve Alert</span>
                </>
              )}
            </button>

            {/* "Share Live Location" Button */}
            <button
              type="button"
              onClick={extendLiveLocationSharing}
              className="w-full py-3 px-4 rounded-2xl bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 font-bold text-xs transition-all active:scale-98 flex items-center justify-center gap-2 min-h-[44px]"
            >
              <Radio className="w-4 h-4 text-blue-600" />
              <span>Share Live Location (Extend 1 Hour)</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
