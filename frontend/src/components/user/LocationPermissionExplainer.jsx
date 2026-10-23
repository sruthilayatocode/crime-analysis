import React from 'react';
import { MapPin, ShieldAlert, Navigation, Search, CheckCircle2, Lock, X } from 'lucide-react';

/**
 * Friendly full-screen location permission explainer dialog.
 * Displayed on first entry to clearly articulate why location access is requested
 * and provide an effortless manual fallback.
 */
export default function LocationPermissionExplainer({ onEnable, onSkip, isRequesting }) {
  return (
    <div
      className="fixed inset-0 z-[9990] bg-slate-900/85 backdrop-blur-md flex items-center justify-center p-4 animate-in fade-in-50"
      role="dialog"
      aria-modal="true"
      aria-labelledby="perm-title"
    >
      <div className="relative w-full max-w-[380px] max-h-[90vh] overflow-y-auto bg-white rounded-3xl p-6 shadow-2xl border border-slate-100 flex flex-col items-center text-center space-y-4 animate-in zoom-in-95 duration-200">
        {/* Top-right Skip Button */}
        <button
          type="button"
          onClick={onSkip}
          className="absolute top-4 right-4 p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-full transition-all min-h-[32px] min-w-[32px] flex items-center justify-center"
          aria-label="Skip location access"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Animated Icon Header */}
        <div className="relative flex items-center justify-center w-16 h-16 rounded-full bg-blue-50 text-blue-600 mt-1 mb-0.5">
          <div className="absolute -inset-1.5 rounded-full bg-blue-100/60 animate-ping pointer-events-none" />
          <Navigation className="w-8 h-8 stroke-[2.2]" />
          <div className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-emerald-500 text-white flex items-center justify-center border-2 border-white shadow-xs">
            <ShieldAlert className="w-3.5 h-3.5" />
          </div>
        </div>

        {/* Title & Subtitle */}
        <div>
          <h2 id="perm-title" className="text-lg font-black text-slate-900 tracking-tight">
            Enable Safe Zone Proximity
          </h2>
          <p className="text-xs text-slate-500 mt-1 leading-relaxed px-1">
            CrimeSense uses your GPS location to calculate real-time crime risk zones and keep you protected on the move.
          </p>
        </div>

        {/* Benefits Checklist */}
        <div className="w-full bg-slate-50 rounded-2xl p-3 text-left space-y-2 border border-slate-100 text-xs text-slate-700">
          <div className="flex items-start gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 mt-0.5 shrink-0" />
            <div>
              <strong className="text-slate-900 font-bold block text-xs">Real-Time Risk Alerts</strong>
              <span className="text-[11px] text-slate-500">
                Receive warnings whenever you enter elevated danger perimeters.
              </span>
            </div>
          </div>

          <div className="flex items-start gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 mt-0.5 shrink-0" />
            <div>
              <strong className="text-slate-900 font-bold block text-xs">Instant Emergency SOS</strong>
              <span className="text-[11px] text-slate-500">
                Share exact coordinates with emergency contacts during distress.
              </span>
            </div>
          </div>

          <div className="flex items-start gap-2">
            <Lock className="w-4 h-4 text-blue-600 mt-0.5 shrink-0" />
            <div>
              <strong className="text-slate-900 font-bold block text-xs">Privacy Guaranteed</strong>
              <span className="text-[11px] text-slate-500">
                Coordinates are encrypted and never sold or exposed to third parties.
              </span>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="w-full space-y-2 pt-1">
          <button
            type="button"
            onClick={onEnable}
            disabled={isRequesting}
            className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-2xl bg-blue-600 hover:bg-blue-700 active:scale-98 text-white text-sm font-bold shadow-md shadow-blue-500/20 transition-all min-h-[46px] focus:outline-none focus:ring-4 focus:ring-blue-200"
          >
            {isRequesting ? (
              <span>Requesting GPS Access...</span>
            ) : (
              <>
                <MapPin className="w-4 h-4" />
                <span>Enable Location Access</span>
              </>
            )}
          </button>

          <button
            type="button"
            onClick={onSkip}
            className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-2xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition-all min-h-[42px]"
          >
            <Search className="w-3.5 h-3.5 text-slate-500" />
            <span>Search Manually Instead</span>
          </button>
        </div>
      </div>
    </div>
  );
}
