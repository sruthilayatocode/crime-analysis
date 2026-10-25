import React, { useState } from 'react';
import {
  ChevronUp,
  ChevronDown,
  MapPin,
  AlertCircle,
  AlertTriangle,
  Info,
  Bookmark,
  Share2,
  Clock,
  Compass,
  Check,
  Activity,
  ShieldCheck,
  ShieldAlert,
  ShieldX,
} from 'lucide-react';
import ZoneBadge from './ZoneBadge';

/**
 * Bottom Status Card displaying:
 * - Zone color & badge (RED, YELLOW, GREEN)
 * - Score explanation (e.g. 100/100, why it is rated red/yellow/green)
 * - Nearby incidents breakdown (type, date, distance)
 * - Safety tip
 * - Save location button
 * - Share location button (Web Share API or clipboard copy)
 */
export default function ZoneStatusCard({
  zoneData,
  loading,
  onSaveLocation,
  currentLocality,
  coords,
}) {
  const [expanded, setExpanded] = useState(false);
  const [sharedToast, setSharedToast] = useState(false);
  const [savedToast, setSavedToast] = useState(false);

  if (loading) {
    return (
      <div className="bg-white/95 backdrop-blur-md rounded-2xl border border-slate-200/90 p-4 shadow-lg animate-pulse mx-3 mb-2">
        <div className="flex items-center justify-between mb-3">
          <div className="h-6 w-32 bg-slate-200 rounded-full" />
          <div className="h-4 w-20 bg-slate-200 rounded-md" />
        </div>
        <div className="h-4 w-3/4 bg-slate-200 rounded mb-2" />
        <div className="h-3 w-1/2 bg-slate-200 rounded" />
      </div>
    );
  }

  if (!zoneData) return null;

  const zone = zoneData.zone || 'GREEN';
  const score = Math.round(zoneData.score || 0);
  const incidentCount = zoneData.incident_count || 0;
  const safetyTip = zoneData.safety_tip || 'Maintain regular situational awareness.';
  const topCrimeTypes = zoneData.top_3_crime_types || zoneData.top_crime_types || [];
  const nearestDistance = zoneData.nearest_incident_distance;
  const mostSevere = zoneData.most_severe_recent_incident;
  const nearbyIncidents = zoneData.nearby_incidents || [];
  const isLimited = zoneData.confidence === 'low' || incidentCount === 0;

  // Score description explanation
  const getScoreExplanation = (z, s) => {
    if (z === 'RED') {
      return `Elevated risk index (${s}/100) due to frequent or severe recent incidents in this ${Math.round((zoneData.radius || 1000) / 1000)}km radius.`;
    }
    if (z === 'YELLOW') {
      return `Moderate risk index (${s}/100) reflecting occasional reported crime activity nearby.`;
    }
    if (isLimited) {
      return `Low risk rating (${s}/100) with limited historical crime records available in this perimeter.`;
    }
    return `Low risk index (${s}/100) indicating very low crime activity in this perimeter.`;
  };

  const ZoneIcon = zone === 'RED' ? ShieldX : zone === 'YELLOW' ? ShieldAlert : ShieldCheck;
  const zoneIconColor = zone === 'RED' ? 'text-red-500' : zone === 'YELLOW' ? 'text-amber-500' : 'text-emerald-500';

  const handleShare = async (e) => {
    e.stopPropagation();
    const lat = coords?.lat || zoneData.lat;
    const lng = coords?.lng || zoneData.lng;
    const shareUrl = `${window.location.origin}/app?lat=${lat}&lng=${lng}&place=${encodeURIComponent(currentLocality || 'Location')}`;
    const shareText = `🛡️ CrimeSense Zone Report\n📍 ${currentLocality || 'This location'}\n🔴 Zone: ${zone} (Risk Score: ${score}/100)\n${incidentCount} incident${incidentCount !== 1 ? 's' : ''} within ${Math.round((zoneData.radius || 1000))}m\n\n${safetyTip}`;

    if (navigator.share) {
      try {
        await navigator.share({
          title: 'CrimeSense Zone Safety Alert',
          text: shareText,
          url: shareUrl,
        });
        return;
      } catch (err) {
        // Fall back to copy
      }
    }

    navigator.clipboard.writeText(`${shareText}\n${shareUrl}`);
    setSharedToast(true);
    setTimeout(() => setSharedToast(false), 2500);
  };

  const handleSave = (e) => {
    e.stopPropagation();
    if (onSaveLocation) {
      onSaveLocation(currentLocality || 'Inspected Location');
      setSavedToast(true);
      setTimeout(() => setSavedToast(false), 2500);
    }
  };

  /** Format date string to a compact human-readable form */
  const fmtDate = (d) => {
    if (!d) return 'Unknown';
    try {
      return new Date(d).toLocaleDateString('en-IN', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
      });
    } catch {
      return String(d).split('T')[0];
    }
  };

  /** Distance badge color based on proximity */
  const distBadgeClass = (distM) => {
    if (!distM) return 'bg-slate-100 text-slate-500';
    if (distM < 200) return 'bg-red-50 text-red-700 border border-red-200';
    if (distM < 500) return 'bg-amber-50 text-amber-700 border border-amber-200';
    return 'bg-slate-50 text-slate-600 border border-slate-200';
  };

  return (
    <div className="bg-white/95 backdrop-blur-md rounded-2xl border border-slate-200/90 shadow-[0_8px_30px_rgb(0,0,0,0.08)] mx-3 mb-2 transition-all duration-300 overflow-hidden">
      {/* Top Banner / Header */}
      <div
        className="p-3.5 cursor-pointer select-none"
        onClick={() => setExpanded(!expanded)}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') setExpanded(!expanded);
        }}
        aria-expanded={expanded}
        aria-label="Zone status summary. Tap to toggle detailed safety insights."
      >
        <div className="flex items-center justify-between gap-2 mb-2">
          <div className="flex items-center gap-2">
            <ZoneBadge zone={zone} size="md" />
            <span className="text-xs font-semibold text-slate-500">
              Risk: <strong className="text-slate-800">{score}/100</strong>
            </span>
          </div>

          <div className="flex items-center gap-1.5">
            <span
              className={`text-xs font-bold px-2.5 py-0.5 rounded-full ${
                incidentCount > 0
                  ? 'bg-slate-100 text-slate-700 border border-slate-200'
                  : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
              }`}
            >
              {incidentCount} {incidentCount === 1 ? 'incident' : 'incidents'}
            </span>
            <button
              type="button"
              className="p-1 text-slate-400 hover:text-slate-700 min-h-[32px] min-w-[32px] flex items-center justify-center rounded-lg"
              aria-label={expanded ? 'Collapse details' : 'Expand details'}
            >
              {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {/* One-line safety tip */}
        <p className="text-xs text-slate-700 leading-snug line-clamp-2">
          {safetyTip}
        </p>

        {/* Distance snippet & Action buttons */}
        <div className="flex items-center justify-between text-[11px] text-slate-500 mt-2 pt-2 border-t border-slate-100">
          <div className="flex items-center gap-1.5 truncate">
            <MapPin className="w-3.5 h-3.5 text-blue-600 shrink-0" />
            <span className="truncate">{currentLocality || 'Selected Area'} (1km radius)</span>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {/* Quick Share button */}
            <button
              type="button"
              onClick={handleShare}
              className="flex items-center gap-1 text-[11px] font-bold text-slate-600 hover:text-blue-600 bg-slate-100 hover:bg-blue-50 px-2 py-1 rounded-lg transition-colors min-h-[32px]"
              aria-label="Share this zone safety status"
            >
              {sharedToast ? <Check className="w-3 h-3 text-emerald-600" /> : <Share2 className="w-3 h-3" />}
              <span>{sharedToast ? 'Link Copied' : 'Share'}</span>
            </button>

            {/* Quick Save button */}
            <button
              type="button"
              onClick={handleSave}
              className="flex items-center gap-1 text-[11px] font-bold text-slate-600 hover:text-blue-600 bg-slate-100 hover:bg-blue-50 px-2 py-1 rounded-lg transition-colors min-h-[32px]"
              aria-label="Save this place"
            >
              {savedToast ? <Check className="w-3 h-3 text-emerald-600" /> : <Bookmark className="w-3 h-3" />}
              <span>{savedToast ? 'Saved' : 'Save'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Expandable Detailed Safety Drawer */}
      {expanded && (
        <div className="px-3.5 pb-3.5 pt-1 border-t border-slate-100 bg-slate-50/60 space-y-3">
          {/* Score Explanation */}
          <div className="p-2.5 rounded-xl bg-white border border-slate-200/80 text-xs flex items-start gap-2">
            <ZoneIcon className={`w-4 h-4 mt-0.5 shrink-0 ${zoneIconColor}`} />
            <div>
              <span className="font-bold text-slate-700 block mb-0.5">Score Analysis</span>
              <p className="text-slate-500 text-[11px] leading-relaxed">
                {getScoreExplanation(zone, score)}
              </p>
            </div>
          </div>

          {/* Top Crime Types */}
          {topCrimeTypes.length > 0 && (
            <div>
              <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1.5 flex items-center gap-1">
                <Activity className="w-3 h-3" /> Top Reported Crime Types
              </p>
              <div className="flex flex-wrap gap-1.5">
                {topCrimeTypes.map((crime, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center px-2 py-0.5 rounded-md bg-white border border-slate-200 text-[11px] font-medium text-slate-700 shadow-sm"
                  >
                    {crime}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* ── Nearby Incidents List ── */}
          {nearbyIncidents.length > 0 && (
            <div>
              <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1.5 flex items-center gap-1">
                <AlertCircle className="w-3 h-3" /> Nearby Incidents
              </p>
              <div className="space-y-1.5">
                {nearbyIncidents.map((inc, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between gap-2 bg-white rounded-xl border border-slate-200/80 px-2.5 py-2 shadow-sm"
                  >
                    {/* Type + date */}
                    <div className="min-w-0 flex-1">
                      <p className="text-[11px] font-semibold text-slate-800 truncate">
                        {inc.crime_type}
                      </p>
                      <p className="text-[10px] text-slate-400 flex items-center gap-1 mt-0.5">
                        <Clock className="w-2.5 h-2.5" />
                        <span>{fmtDate(inc.date)}</span>
                        {inc.title && inc.title !== 'Incident Record' && (
                          <>
                            <span>·</span>
                            <span className="truncate max-w-[120px]" title={inc.title}>
                              {inc.title}
                            </span>
                          </>
                        )}
                      </p>
                    </div>
                    {/* Distance badge */}
                    <span
                      className={`text-[10px] font-bold px-1.5 py-0.5 rounded-lg shrink-0 ${distBadgeClass(inc.distance_m)}`}
                    >
                      {inc.distance_m < 1000
                        ? `${Math.round(inc.distance_m)}m`
                        : `${(inc.distance_m / 1000).toFixed(1)}km`}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Most Severe Incident (only when not already covered by nearbyIncidents) */}
          {mostSevere && mostSevere.title && nearbyIncidents.length === 0 && (
            <div className="p-2.5 rounded-xl bg-white border border-slate-200/80 shadow-sm space-y-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                Most Severe Recent Incident
              </span>
              <div className="flex items-start gap-2">
                <AlertCircle className="w-3.5 h-3.5 text-amber-600 mt-0.5 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-[11px] font-semibold text-slate-800 line-clamp-1">
                    {mostSevere.title}
                  </p>
                  <p className="text-[10px] text-slate-500 flex items-center gap-1 mt-0.5">
                    <Clock className="w-3 h-3" />
                    <span>{fmtDate(mostSevere.date)}</span>
                    <span>·</span>
                    <span>Severity {mostSevere.severity_score}/10</span>
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Nearest Incident Distance */}
          {nearestDistance !== null && nearestDistance !== undefined && (
            <div className="flex items-center justify-between text-xs p-2 rounded-lg bg-white border border-slate-200">
              <span className="text-slate-500 flex items-center gap-1.5">
                <Compass className="w-3.5 h-3.5 text-blue-600" /> Nearest Recorded Incident:
              </span>
              <span className="font-bold text-slate-800">
                {nearestDistance < 1000
                  ? `${Math.round(nearestDistance)}m away`
                  : `${(nearestDistance / 1000).toFixed(1)}km away`}
              </span>
            </div>
          )}

          {/* Limited Data Notice */}
          {isLimited && (
            <div className="flex items-center gap-2 p-2 rounded-lg bg-emerald-50/80 border border-emerald-200/80 text-[11px] text-emerald-800">
              <Info className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
              <span>Low risk with limited historical incidents recorded in this perimeter.</span>
            </div>
          )}

          {/* Action Row */}
          <div className="grid grid-cols-2 gap-2 pt-1">
            <button
              type="button"
              onClick={handleSave}
              className="flex items-center justify-center gap-2 py-2.5 px-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-sm active:scale-[0.98] transition-all min-h-[44px]"
            >
              <Bookmark className="w-4 h-4" />
              <span>{savedToast ? 'Saved!' : 'Save Place'}</span>
            </button>
            <button
              type="button"
              onClick={handleShare}
              className="flex items-center justify-center gap-2 py-2.5 px-3 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold active:scale-[0.98] transition-all min-h-[44px]"
            >
              <Share2 className="w-4 h-4" />
              <span>{sharedToast ? 'Link Copied' : 'Share Zone'}</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
