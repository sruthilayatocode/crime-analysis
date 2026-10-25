import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ShieldAlert,
  ShieldCheck,
  MapPin,
  ExternalLink,
  Clock,
  Radio,
  AlertTriangle,
  Navigation,
  RefreshCw,
  Compass,
  ArrowRight,
} from 'lucide-react';
import { savedPlacesService } from '../services/savedPlacesService';

export default function PublicSharedLocation() {
  const { token } = useParams();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [userCoords, setUserCoords] = useState(null);
  const [distanceM, setDistanceM] = useState(null);

  const fetchLocation = async () => {
    try {
      const res = await savedPlacesService.getPublicShareLocation(token);
      if (res.success && res.link) {
        setData(res);
      } else {
        setError(res.error || 'This link has expired or was stopped by the sender.');
      }
    } catch (err) {
      setError(err.message || 'Could not load shared location.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLocation();
    // Poll updates if live
    const interval = setInterval(fetchLocation, 20000);
    return () => clearInterval(interval);
  }, [token]);

  // Request viewer's position to compute distance
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setUserCoords({
            latitude: pos.coords.latitude,
            longitude: pos.coords.longitude,
          });
        },
        () => {}
      );
    }
  }, []);

  // Distance computation
  useEffect(() => {
    if (userCoords && data?.link?.latitude && data?.link?.longitude) {
      const R = 6371000;
      const dLat = ((data.link.latitude - userCoords.latitude) * Math.PI) / 180;
      const dLon = ((data.link.longitude - userCoords.longitude) * Math.PI) / 180;
      const a =
        Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos((userCoords.latitude * Math.PI) / 180) *
          Math.cos((data.link.latitude * Math.PI) / 180) *
          Math.sin(dLon / 2) *
          Math.sin(dLon / 2);
      const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
      setDistanceM(Math.round(R * c));
    }
  }, [userCoords, data]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4 text-white">
        <div className="text-center space-y-3">
          <div className="w-10 h-10 border-3 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs text-slate-400 font-mono">Loading CrimeSense Safety View...</p>
        </div>
      </div>
    );
  }

  if (error || !data?.link?.is_active) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
        <div className="bg-slate-800 text-white rounded-3xl max-w-sm w-full p-6 text-center space-y-4 shadow-2xl border border-slate-700">
          <div className="w-12 h-12 rounded-2xl bg-amber-500/20 text-amber-400 flex items-center justify-center mx-auto">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <h1 className="text-lg font-bold">Link Inactive or Expired</h1>
          <p className="text-xs text-slate-400 leading-relaxed">
            {error || 'This location link has reached its expiration time or was stopped by the sender.'}
          </p>
          <button
            type="button"
            onClick={() => navigate('/app')}
            className="w-full py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition-all min-h-[44px]"
          >
            Open CrimeSense
          </button>
        </div>
      </div>
    );
  }

  const { link, zone_details } = data;
  const zoneUpper = (link.zone || 'GREEN').toUpperCase();
  const mapsUrl =
    link.maps_url || `https://maps.google.com/?q=${link.latitude},${link.longitude}`;

  return (
    <div className="min-h-screen bg-slate-900 flex justify-center items-stretch antialiased selection:bg-blue-600 selection:text-white">
      <div className="w-full max-w-[430px] min-h-screen bg-slate-50 text-slate-900 flex flex-col relative shadow-2xl overflow-x-hidden border-x border-slate-200/80">
        {/* Top Public Header */}
        <header className="bg-white border-b border-slate-200 px-4 py-3 flex items-center justify-between shadow-2xs">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-blue-600 text-white flex items-center justify-center shadow-xs">
              <ShieldCheck className="w-4 h-4 stroke-[2.5]" />
            </div>
            <div>
              <span className="text-xs font-black tracking-tight text-slate-900 block leading-tight">
                CrimeSense
              </span>
              <span className="text-[10px] text-slate-500 font-medium">Shared Safety Location</span>
            </div>
          </div>
          {link.is_live && (
            <span className="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
              <Radio className="w-2.5 h-2.5 text-emerald-600 animate-ping" />
              <span>Live GPS</span>
            </span>
          )}
        </header>

        {/* Main Body */}
        <main className="flex-1 p-4 space-y-4 pb-12">
          {/* Destination & Zone Hero Card */}
          <div
            className={`rounded-3xl p-5 text-white shadow-xl space-y-3 relative overflow-hidden ${
              zoneUpper === 'RED'
                ? 'bg-gradient-to-br from-red-600 to-rose-700'
                : zoneUpper === 'YELLOW'
                ? 'bg-gradient-to-br from-amber-600 to-orange-600'
                : 'bg-gradient-to-br from-emerald-600 to-teal-700'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-black uppercase tracking-wider bg-black/20 px-2.5 py-0.5 rounded-full">
                Safety Verified
              </span>
              <span className="text-xs font-black uppercase tracking-wider bg-white/20 px-2.5 py-0.5 rounded-full">
                {zoneUpper} ZONE
              </span>
            </div>

            <div>
              <h1 className="text-xl font-black tracking-tight">{link.label}</h1>
              <p className="text-xs text-white/90 mt-0.5">{link.address}</p>
            </div>

            <div className="flex items-center justify-between pt-1 text-[11px] text-white/80 border-t border-white/20">
              <span className="font-mono">
                {link.latitude?.toFixed(5)}, {link.longitude?.toFixed(5)}
              </span>
              {distanceM !== null && (
                <span className="font-bold bg-white/20 px-2 py-0.5 rounded-lg">
                  {distanceM >= 1000 ? `${(distanceM / 1000).toFixed(1)} km away` : `${distanceM} m away`}
                </span>
              )}
            </div>
          </div>

          {/* Interactive Map Visual Box */}
          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs">
            <div className="h-44 bg-slate-100 relative flex items-center justify-center">
              {/* Map Canvas styling preview */}
              <div className="absolute inset-0 bg-blue-50/50 flex items-center justify-center">
                <div className="relative flex flex-col items-center">
                  <div className="w-10 h-10 rounded-full bg-red-600 text-white flex items-center justify-center shadow-lg animate-bounce border-2 border-white">
                    <MapPin className="w-5 h-5" />
                  </div>
                  <span className="text-[10px] font-black bg-slate-900 text-white px-2 py-0.5 rounded-md mt-1 shadow-sm">
                    {link.label}
                  </span>
                </div>
              </div>

              <div className="absolute bottom-2 right-2">
                <a
                  href={mapsUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-3 py-1.5 rounded-xl bg-white/95 text-slate-800 text-[11px] font-bold shadow-md hover:bg-white flex items-center gap-1.5 border border-slate-200"
                >
                  <span>Google Maps</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </div>
          </div>

          {/* Zone Safety Intelligence Card */}
          <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-xs space-y-2.5">
            <div className="flex items-center justify-between">
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Live Zone Intelligence
              </h2>
              <span className="text-[10px] text-slate-400">1 km Perimeter</span>
            </div>

            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/60 flex items-start gap-2.5">
              <ShieldCheck className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
              <div>
                <span className="text-xs font-bold text-slate-800 block">
                  {zoneUpper === 'RED'
                    ? 'Caution: High crime density reported in this area'
                    : zoneUpper === 'YELLOW'
                    ? 'Moderate safety score: standard alertness recommended'
                    : 'Safe zone: low crime density reported in verified dataset'}
                </span>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Calculated using CrimeSense law enforcement dataset with Haversine distance decay.
                </p>
              </div>
            </div>
          </div>

          {/* Directions / Open Navigation Button */}
          <a
            href={mapsUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="w-full py-3.5 px-4 rounded-2xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-md transition-all flex items-center justify-center gap-2 min-h-[48px]"
          >
            <Navigation className="w-4 h-4 fill-current" />
            <span>Get Directions in Google Maps</span>
          </a>

          {/* CrimeSense promo footer */}
          <div className="text-center pt-2">
            <button
              type="button"
              onClick={() => navigate('/app')}
              className="text-xs font-bold text-blue-600 hover:underline inline-flex items-center gap-1"
            >
              <span>Explore live safety heatmaps on CrimeSense</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </main>
      </div>
    </div>
  );
}
