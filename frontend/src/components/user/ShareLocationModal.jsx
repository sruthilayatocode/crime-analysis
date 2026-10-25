import React, { useState } from 'react';
import {
  Share2,
  Copy,
  Check,
  ExternalLink,
  Clock,
  Radio,
  MapPin,
  X,
  StopCircle,
  MessageCircle,
  ShieldAlert,
} from 'lucide-react';
import { savedPlacesService } from '../../services/savedPlacesService';

export default function ShareLocationModal({ location, onClose }) {
  const [mode, setMode] = useState('static'); // 'static' | 'live'
  const [expiryHours, setExpiryHours] = useState(1); // 1, 8, 24
  const [generating, setGenerating] = useState(false);
  const [generatedLink, setGeneratedLink] = useState(null);
  const [copied, setCopied] = useState(false);
  const [revoking, setRevoking] = useState(false);

  if (!location) return null;

  const lat = location.latitude || location.lat || 12.9165;
  const lng = location.longitude || location.lng || 79.1325;
  const label = location.label || location.name || 'Current Location';
  const zone = (location.zone || 'GREEN').toUpperCase();
  const address = location.address || `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
  const googleMapsUrl = `https://maps.google.com/?q=${lat},${lng}`;

  const handleWhatsAppShare = () => {
    const linkUrl = generatedLink
      ? `${window.location.origin}${generatedLink.url}`
      : googleMapsUrl;

    const message = `📍 CrimeSense Safety Share: ${label}\n🛡️ Risk Zone: ${zone}\n📍 Coordinates: ${lat.toFixed(5)}, ${lng.toFixed(5)}\n🗺️ View Location: ${linkUrl}`;
    const waUrl = `https://wa.me/?text=${encodeURIComponent(message)}`;
    window.open(waUrl, '_blank');
  };

  const handleNativeShare = async () => {
    const linkUrl = generatedLink
      ? `${window.location.origin}${generatedLink.url}`
      : googleMapsUrl;

    if (navigator.share) {
      try {
        await navigator.share({
          title: `CrimeSense: ${label}`,
          text: `Check safety zone status for ${label} (${zone} Zone):`,
          url: linkUrl,
        });
      } catch {}
    } else {
      handleCopy(linkUrl);
    }
  };

  const handleGenerateCrimeSenseLink = async () => {
    setGenerating(true);
    try {
      const data = await savedPlacesService.createShareLink({
        latitude: lat,
        longitude: lng,
        label,
        address,
        zone: zone.toLowerCase(),
        is_live: mode === 'live',
        expiry_hours: expiryHours,
      });
      setGeneratedLink(data);
    } catch (err) {
      alert(`Could not create link: ${err.message}`);
    } finally {
      setGenerating(false);
    }
  };

  const handleCopy = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    });
  };

  const handleRevoke = async () => {
    if (!generatedLink?.token) return;
    if (window.confirm("Stop sharing this location? The public link will be deactivated immediately.")) {
      setRevoking(true);
      try {
        await savedPlacesService.revokeShareLink(generatedLink.token);
        setGeneratedLink(null);
        alert("Location sharing stopped successfully.");
      } catch (err) {
        alert(err.message);
      } finally {
        setRevoking(false);
      }
    }
  };

  const fullShareUrl = generatedLink ? `${window.location.origin}${generatedLink.url}` : '';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="bg-white rounded-3xl max-w-sm w-full p-5 shadow-2xl border border-slate-200 space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between pb-2 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
              <Share2 className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-800">Share Location</h2>
              <p className="text-[11px] text-slate-500">{label}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Location & Zone Snapshot */}
        <div className="p-3 bg-slate-50 rounded-2xl border border-slate-200/70 flex items-center justify-between text-xs">
          <div className="space-y-0.5">
            <span className="font-bold text-slate-800 flex items-center gap-1">
              <MapPin className="w-3.5 h-3.5 text-red-500" />
              <span>{address}</span>
            </span>
            <span className="text-[10px] text-slate-400 font-mono block">
              {lat.toFixed(4)}, {lng.toFixed(4)}
            </span>
          </div>
          <span
            className={`px-2 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider ${
              zone === 'RED'
                ? 'bg-red-100 text-red-700'
                : zone === 'YELLOW'
                ? 'bg-amber-100 text-amber-800'
                : 'bg-emerald-100 text-emerald-700'
            }`}
          >
            {zone} Zone
          </span>
        </div>

        {/* Quick Social Share Options */}
        <div className="grid grid-cols-2 gap-2">
          {/* WhatsApp Button */}
          <button
            type="button"
            onClick={handleWhatsAppShare}
            className="py-2.5 px-3 rounded-2xl bg-[#25D366]/10 hover:bg-[#25D366]/20 text-[#128C7E] font-bold text-xs flex items-center justify-center gap-2 transition-all border border-[#25D366]/30 min-h-[44px]"
          >
            <MessageCircle className="w-4 h-4 fill-current" />
            <span>WhatsApp</span>
          </button>

          {/* Web Share / Device Button */}
          <button
            type="button"
            onClick={handleNativeShare}
            className="py-2.5 px-3 rounded-2xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs flex items-center justify-center gap-1.5 transition-all min-h-[44px]"
          >
            <Share2 className="w-4 h-4" />
            <span>Share Sheet</span>
          </button>
        </div>

        {/* CrimeSense Secure Token Link Generator */}
        <div className="pt-1 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-700">CrimeSense Token Link</span>
            <span className="text-[10px] text-slate-400">Public &bull; Unguessable</span>
          </div>

          {!generatedLink ? (
            <div className="space-y-3 bg-slate-50 p-3.5 rounded-2xl border border-slate-200/80">
              {/* Mode: Static vs Live */}
              <div>
                <label className="block text-[11px] font-bold text-slate-600 mb-1.5">
                  Sharing Mode
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setMode('static')}
                    className={`py-1.5 px-2 rounded-xl text-xs font-bold transition-all ${
                      mode === 'static'
                        ? 'bg-blue-600 text-white shadow-xs'
                        : 'bg-white border border-slate-200 text-slate-600'
                    }`}
                  >
                    Static Place
                  </button>
                  <button
                    type="button"
                    onClick={() => setMode('live')}
                    className={`py-1.5 px-2 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1 ${
                      mode === 'live'
                        ? 'bg-blue-600 text-white shadow-xs'
                        : 'bg-white border border-slate-200 text-slate-600'
                    }`}
                  >
                    <Radio className="w-3 h-3" />
                    <span>Live GPS</span>
                  </button>
                </div>
              </div>

              {/* Expiry Selector */}
              <div>
                <label className="block text-[11px] font-bold text-slate-600 mb-1.5">
                  Link Expiry
                </label>
                <div className="grid grid-cols-3 gap-1.5">
                  {[1, 8, 24].map((hrs) => (
                    <button
                      key={hrs}
                      type="button"
                      onClick={() => setExpiryHours(hrs)}
                      className={`py-1.5 rounded-xl text-xs font-bold transition-all ${
                        expiryHours === hrs
                          ? 'bg-slate-800 text-white'
                          : 'bg-white border border-slate-200 text-slate-600'
                      }`}
                    >
                      {hrs} Hour{hrs > 1 ? 's' : ''}
                    </button>
                  ))}
                </div>
              </div>

              {/* Generate Button */}
              <button
                type="button"
                onClick={handleGenerateCrimeSenseLink}
                disabled={generating}
                className="w-full py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-xs transition-all min-h-[40px] flex items-center justify-center gap-1.5"
              >
                {generating ? 'Generating Link...' : 'Create Share Link'}
              </button>
            </div>
          ) : (
            <div className="space-y-2.5 bg-emerald-50/70 p-3.5 rounded-2xl border border-emerald-200 animate-in fade-in-50">
              <div className="flex items-center justify-between text-[11px] text-emerald-800 font-bold">
                <span className="flex items-center gap-1">
                  <Check className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Link Active ({generatedLink.expiry_hours}h)</span>
                </span>
                <span className="text-[10px] text-emerald-600 font-mono">
                  {generatedLink.is_live ? 'Live GPS' : 'Static'}
                </span>
              </div>

              {/* URL Display & Copy */}
              <div className="flex items-center gap-1.5 bg-white p-2 rounded-xl border border-emerald-200">
                <input
                  type="text"
                  readOnly
                  value={fullShareUrl}
                  className="w-full text-xs font-mono text-slate-700 bg-transparent focus:outline-none select-all"
                />
                <button
                  type="button"
                  onClick={() => handleCopy(fullShareUrl)}
                  className="p-1.5 rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 shrink-0"
                  title="Copy link"
                >
                  {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
              </div>

              {copied && (
                <p className="text-[10px] text-emerald-700 font-bold text-center">
                  Link copied to clipboard!
                </p>
              )}

              {/* Stop Sharing Button */}
              <button
                type="button"
                onClick={handleRevoke}
                disabled={revoking}
                className="w-full py-2 rounded-xl bg-white border border-red-200 text-red-600 hover:bg-red-50 text-xs font-bold transition-colors flex items-center justify-center gap-1.5 min-h-[36px]"
              >
                <StopCircle className="w-3.5 h-3.5" />
                <span>Stop Sharing / Deactivate Link</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
