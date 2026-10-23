import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  Radio,
  MapPin,
  ExternalLink,
  PhoneCall,
  Clock,
  CheckCircle2,
  Users,
  AlertTriangle,
} from 'lucide-react';
import { sosService, playAlertBeep } from '../services/sosService';

export default function AdminSOSLiveAlerts() {
  const [events, setEvents] = useState([]);
  const [activeCount, setActiveCount] = useState(0);
  const [loading, setLoading] = useState(true);

  const fetchEvents = async () => {
    try {
      const data = await sosService.getAdminSOSEvents('all', 10);
      const newActive = data.active_count || 0;
      if (newActive > 0 && newActive > activeCount) {
        // Play beep when a new active alert arrives
        playAlertBeep(920, 0.25);
      }
      setActiveCount(newActive);
      setEvents(data.events || []);
    } catch {
      // Ignore background sync errors
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
    const interval = setInterval(fetchEvents, 6000); // poll every 6s for real-time monitoring
    return () => clearInterval(interval);
  }, [activeCount]);

  const activeEvents = events.filter((e) => e.status === 'active');

  if (activeEvents.length === 0) {
    return null;
  }

  return (
    <div className="space-y-3 animate-in fade-in-50 slide-in-from-top-4 duration-300">
      {activeEvents.map((evt) => {
        const mapsUrl =
          evt.maps_url || `https://maps.google.com/?q=${evt.latitude},${evt.longitude}`;
        const notified = evt.contacts_notified || [];

        return (
          <div
            key={evt.id}
            className="rounded-2xl bg-gradient-to-r from-red-950/90 via-red-900/90 to-rose-950/90 border-2 border-red-500/80 p-4 sm:p-5 shadow-[0_0_35px_rgba(239,68,68,0.35)] text-white relative overflow-hidden"
          >
            {/* Pulsing indicator background */}
            <div className="absolute top-0 right-0 w-32 h-32 bg-red-500/10 rounded-full blur-2xl pointer-events-none animate-pulse" />

            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <div className="flex items-start gap-3.5">
                <div className="w-12 h-12 rounded-2xl bg-red-600 border border-red-400 flex items-center justify-center shrink-0 shadow-lg animate-bounce">
                  <ShieldAlert className="w-7 h-7 text-white stroke-[2.5]" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-red-500/30 border border-red-400/50 text-red-200 text-[10px] font-black uppercase tracking-wider">
                      <Radio className="w-3 h-3 text-red-400 animate-ping" />
                      <span>Live SOS Distress Triggered</span>
                    </span>
                    <span className="text-xs text-red-200 font-mono">
                      #{evt.id} &bull; {new Date(evt.created_at).toLocaleTimeString()}
                    </span>
                  </div>

                  <h3 className="text-base sm:text-lg font-black text-white mt-1">
                    User: {evt.user_name || 'Anonymous User'}
                  </h3>
                  <p className="text-xs text-red-100/80">
                    Email: {evt.user_email || 'N/A'} &bull; Zone:{' '}
                    <strong className="text-white uppercase">{evt.zone || 'DANGER'}</strong>
                  </p>
                </div>
              </div>

              {/* Coordinates & Google Maps Link */}
              <div className="flex flex-wrap items-center gap-2">
                <a
                  href={mapsUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-3.5 py-2 rounded-xl bg-white text-red-900 font-bold text-xs shadow-md hover:bg-red-50 transition-all flex items-center gap-1.5 min-h-[38px]"
                >
                  <MapPin className="w-4 h-4 text-red-600" />
                  <span>
                    GPS ({evt.latitude.toFixed(4)}, {evt.longitude.toFixed(4)})
                  </span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>

                <div className="px-3 py-1.5 rounded-xl bg-red-900/60 border border-red-500/40 text-xs text-red-200 flex items-center gap-1.5">
                  <Users className="w-3.5 h-3.5 text-red-300" />
                  <span>{notified.length} Contacts Notified</span>
                </div>
              </div>
            </div>

            {/* Contacts Notified details */}
            {notified.length > 0 && (
              <div className="mt-3 pt-3 border-t border-red-800/60 flex flex-wrap gap-2 text-xs">
                <span className="text-red-300 text-[11px] font-bold self-center">Notified:</span>
                {notified.map((c, i) => (
                  <span
                    key={i}
                    className="px-2 py-0.5 rounded-lg bg-black/30 border border-red-700/50 text-red-100 text-[11px] flex items-center gap-1 font-mono"
                  >
                    <span>{c.contact_name}</span>
                    <span className="text-red-400">({c.contact_phone})</span>
                    <span className="text-emerald-400 text-[10px]">✓</span>
                  </span>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
