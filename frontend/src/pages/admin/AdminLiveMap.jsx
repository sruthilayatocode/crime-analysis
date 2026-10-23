import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  MapPin,
  Radio,
  RefreshCw,
  Users,
  AlertTriangle,
  Shield,
  Clock,
  Compass,
  Eye,
  CheckCircle2,
} from 'lucide-react';
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { adminService } from '../../services/adminService';

// Fix default icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const getZoneColor = (zone = 'green', isEmergency = false) => {
  if (isEmergency) return '#dc2626'; // Deep Red Pulsing
  const z = (zone || 'green').toLowerCase();
  if (z === 'red') return '#ef4444';
  if (z === 'orange' || z === 'yellow') return '#f59e0b';
  return '#10b981';
};

const createLiveUserIcon = (zone, isEmergency, name) => {
  const color = getZoneColor(zone, isEmergency);
  const pulseClass = isEmergency ? 'animate-ping' : '';
  const initial = (name || 'U')[0].toUpperCase();

  return L.divIcon({
    className: 'custom-live-user-marker',
    html: `
      <div style="position: relative; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center;">
        ${isEmergency ? `<div style="position: absolute; width: 32px; height: 32px; border-radius: 50%; background-color: rgba(239,68,68,0.5);" class="${pulseClass}"></div>` : ''}
        <div style="width: 26px; height: 26px; border-radius: 50%; background-color: ${color}; border: 2px solid white; box-shadow: 0 0 10px ${color}; display: flex; align-items: center; justify-content: center; color: white; font-weight: 800; font-size: 11px;">
          ${initial}
        </div>
      </div>
    `,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
  });
};

export default function AdminLiveMap() {
  const [liveUsers, setLiveUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lastSyncTime, setLastSyncTime] = useState(new Date());
  const [countdown, setCountdown] = useState(12);
  const [selectedUser, setSelectedUser] = useState(null);
  const mapRef = useRef(null);

  const fetchLiveMap = useCallback(async () => {
    try {
      const res = await adminService.getLiveMapUsers();
      setLiveUsers(res.users || []);
      setLastSyncTime(new Date());
      setCountdown(12);
    } catch (err) {
      console.error('Live map fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchLiveMap();
    const interval = setInterval(fetchLiveMap, 12000); // Poll every 12 seconds
    return () => clearInterval(interval);
  }, [fetchLiveMap]);

  // Countdown timer effect
  useEffect(() => {
    const timer = setInterval(() => {
      setCountdown((prev) => (prev <= 1 ? 12 : prev - 1));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const redZoneCount = liveUsers.filter((u) => u.zone === 'red').length;
  const emergencyCount = liveUsers.filter((u) => u.is_emergency).length;

  const defaultCenter =
    liveUsers.length > 0 && liveUsers[0].latitude && liveUsers[0].longitude
      ? [liveUsers[0].latitude, liveUsers[0].longitude]
      : [12.9165, 79.1325];

  return (
    <div className="space-y-5 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-black tracking-tight text-white">Live Citizen Location Map</h1>
            <span className="text-[10px] font-bold text-cyan-400 bg-cyan-950/80 px-2.5 py-0.5 rounded-full border border-cyan-800 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
              <span>Auto-refresh in {countdown}s</span>
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time GPS tracking stream strictly limited to citizens who granted live location sharing consent
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={fetchLiveMap}
            disabled={loading}
            className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold border border-slate-700 flex items-center gap-1.5 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Sync GPS Now</span>
          </button>
        </div>
      </div>

      {/* Summary KPI Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-3.5 bg-slate-900 border border-slate-800 rounded-2xl flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-cyan-950 text-cyan-400 flex items-center justify-center border border-cyan-800 shrink-0">
            <Radio className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <span className="text-2xl font-black text-white block">{liveUsers.length}</span>
            <span className="text-[11px] text-slate-400 block font-medium">Consented Broadcasters</span>
          </div>
        </div>

        <div className="p-3.5 bg-slate-900 border border-slate-800 rounded-2xl flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-red-950 text-red-400 flex items-center justify-center border border-red-800 shrink-0">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div>
            <span className="text-2xl font-black text-white block">{emergencyCount}</span>
            <span className="text-[11px] text-slate-400 block font-medium">Active Emergencies</span>
          </div>
        </div>

        <div className="p-3.5 bg-slate-900 border border-slate-800 rounded-2xl flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-orange-950 text-orange-400 flex items-center justify-center border border-orange-800 shrink-0">
            <Compass className="w-5 h-5" />
          </div>
          <div>
            <span className="text-2xl font-black text-white block">{redZoneCount}</span>
            <span className="text-[11px] text-slate-400 block font-medium">Inside RED Zones</span>
          </div>
        </div>

        <div className="p-3.5 bg-slate-900 border border-slate-800 rounded-2xl flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-950 text-emerald-400 flex items-center justify-center border border-emerald-800 shrink-0">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <span className="text-xs font-bold text-emerald-400 block">Strict Privacy Filter</span>
            <span className="text-[10px] text-slate-400 block">Non-consenting users excluded</span>
          </div>
        </div>
      </div>

      {/* Main Live Map & Sidebar Container */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Map View */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl p-4 space-y-3">
          <div className="h-[520px] rounded-xl overflow-hidden border border-slate-800 z-10">
            <MapContainer
              center={defaultCenter}
              zoom={13}
              ref={mapRef}
              style={{ height: '100%', width: '100%', background: '#0f172a' }}
            >
              <TileLayer
                attribution="&copy; OpenStreetMap"
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              {liveUsers.map((u) => (
                <React.Fragment key={u.user_id}>
                  <Marker
                    position={[u.latitude, u.longitude]}
                    icon={createLiveUserIcon(u.zone, u.is_emergency, u.name)}
                    eventHandlers={{
                      click: () => setSelectedUser(u),
                    }}
                  >
                    <Popup>
                      <div className="p-1 text-slate-900 space-y-1">
                        <span className="font-bold text-xs block">{u.name}</span>
                        <p className="text-[11px] text-slate-600">{u.email}</p>
                        <span
                          className={`text-[10px] font-black px-1.5 py-0.2 rounded-full ${
                            u.is_emergency
                              ? 'bg-red-600 text-white'
                              : u.zone === 'red'
                              ? 'bg-red-100 text-red-700'
                              : 'bg-emerald-100 text-emerald-700'
                          }`}
                        >
                          {u.is_emergency ? 'SOS DISTRESS' : `${(u.zone || 'green').toUpperCase()} ZONE`}
                        </span>
                        <p className="text-[10px] text-slate-400 mt-1">
                          Updated {u.time_ago_seconds}s ago
                        </p>
                      </div>
                    </Popup>
                  </Marker>
                  <Circle
                    center={[u.latitude, u.longitude]}
                    radius={u.accuracy || 30}
                    pathOptions={{
                      color: getZoneColor(u.zone, u.is_emergency),
                      fillColor: getZoneColor(u.zone, u.is_emergency),
                      fillOpacity: 0.15,
                      weight: 1,
                    }}
                  />
                </React.Fragment>
              ))}
            </MapContainer>
          </div>
        </div>

        {/* Live Users Stream Sidebar */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 space-y-3 flex flex-col h-[560px]">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800 shrink-0">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Users className="w-4 h-4 text-cyan-400" />
              <span>Active Broadcasters</span>
            </h3>
            <span className="text-xs font-bold text-slate-400">{liveUsers.length} online</span>
          </div>

          <div className="flex-1 overflow-y-auto space-y-2 pr-1">
            {liveUsers.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center text-slate-500 space-y-2">
                <Radio className="w-8 h-8 text-slate-700" />
                <p className="text-xs">No active users currently broadcasting live coordinates.</p>
              </div>
            ) : (
              liveUsers.map((u) => {
                const isSelected = selectedUser?.user_id === u.user_id;
                return (
                  <div
                    key={u.user_id}
                    onClick={() => {
                      setSelectedUser(u);
                      if (mapRef.current) {
                        mapRef.current.setView([u.latitude, u.longitude], 15);
                      }
                    }}
                    className={`p-3 rounded-xl border transition-all cursor-pointer space-y-1.5 ${
                      isSelected
                        ? 'bg-slate-800 border-cyan-500 ring-1 ring-cyan-500'
                        : u.is_emergency
                        ? 'bg-red-950/70 border-red-800 animate-pulse'
                        : 'bg-slate-950/80 border-slate-800/80 hover:bg-slate-800/50'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div
                          className={`w-2.5 h-2.5 rounded-full ${
                            u.is_emergency
                              ? 'bg-red-500 animate-ping'
                              : u.zone === 'red'
                              ? 'bg-red-500'
                              : u.zone === 'orange' || u.zone === 'yellow'
                              ? 'bg-amber-500'
                              : 'bg-emerald-500'
                          }`}
                        />
                        <span className="font-bold text-xs text-white truncate max-w-[140px]">{u.name}</span>
                      </div>
                      <span
                        className={`text-[9px] font-black px-2 py-0.5 rounded-full ${
                          u.is_emergency
                            ? 'bg-red-600 text-white'
                            : u.zone === 'red'
                            ? 'bg-red-950 text-red-400 border border-red-800'
                            : 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                        }`}
                      >
                        {u.is_emergency ? 'DISTRESS' : `${u.zone.toUpperCase()} ZONE`}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-[11px] text-slate-400">
                      <span className="font-mono">{u.latitude.toFixed(4)}, {u.longitude.toFixed(4)}</span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3 text-slate-500" />
                        <span>{u.time_ago_seconds}s ago</span>
                      </span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
