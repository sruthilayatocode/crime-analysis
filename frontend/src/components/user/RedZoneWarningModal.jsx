import React from 'react';
import { ShieldAlert, CheckCircle2, AlertTriangle, Radio, PhoneCall } from 'lucide-react';
import { useSOS } from '../../context/SOSContext';

export default function RedZoneWarningModal() {
  const { isWarningActive, warningCountdown, confirmSafetyCheckin, executeSOSTriggerNow } = useSOS();

  if (!isWarningActive) return null;

  const progressPct = ((60 - warningCountdown) / 60) * 100;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-amber-950/85 backdrop-blur-md animate-in fade-in duration-150">
      <div className="bg-white rounded-3xl p-6 max-w-sm w-full text-center space-y-4 shadow-2xl border-2 border-amber-500">
        {/* Header Alert Badge */}
        <div className="space-y-1">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-100 text-amber-900 text-xs font-black uppercase tracking-wider animate-pulse">
            <AlertTriangle className="w-4 h-4 text-amber-600" />
            <span>Red Zone Safety Check</span>
          </div>
          <h2 className="text-xl font-black text-slate-900 pt-1">
            Are you safe?
          </h2>
          <p className="text-xs text-slate-600 leading-relaxed">
            You have remained stationary in a <strong className="text-red-600">HIGH-RISK RED ZONE</strong> without movement or activity.
          </p>
        </div>

        {/* 60s Circular Countdown */}
        <div className="relative flex items-center justify-center w-32 h-32 mx-auto">
          <div className="absolute inset-0 rounded-full bg-amber-400/20 animate-ping" />
          <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
            <circle
              cx="50"
              cy="50"
              r="44"
              className="stroke-slate-100"
              strokeWidth="8"
              fill="transparent"
            />
            <circle
              cx="50"
              cy="50"
              r="44"
              className="stroke-amber-500 transition-all duration-1000 ease-linear"
              strokeWidth="8"
              fill="transparent"
              strokeDasharray="276.46"
              strokeDashoffset={(276.46 * progressPct) / 100}
              strokeLinecap="round"
            />
          </svg>

          <div className="absolute flex flex-col items-center justify-center">
            <span className="text-4xl font-black text-amber-700 leading-none">
              {warningCountdown}s
            </span>
            <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider mt-0.5">
              Auto SOS in
            </span>
          </div>
        </div>

        <p className="text-[11px] text-slate-500 bg-slate-50 p-2.5 rounded-xl border border-slate-200/70">
          If you don't respond, an <strong>Automatic SOS Alert</strong> with your location will be dispatched to your emergency contacts.
        </p>

        {/* Action Buttons */}
        <div className="space-y-2 pt-1">
          <button
            type="button"
            onClick={confirmSafetyCheckin}
            className="w-full py-3.5 px-4 rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white font-black text-sm shadow-[0_4px_15px_rgba(16,185,129,0.35)] active:scale-98 transition-all flex items-center justify-center gap-2 min-h-[48px]"
          >
            <CheckCircle2 className="w-5 h-5 stroke-[2.5]" />
            <span>I'm Safe &ndash; Reset Timer</span>
          </button>

          <button
            type="button"
            onClick={executeSOSTriggerNow}
            className="w-full py-2.5 px-4 text-xs font-bold text-red-600 hover:text-red-700 flex items-center justify-center gap-1.5 transition-colors"
          >
            <ShieldAlert className="w-4 h-4" />
            <span>Need Help? Trigger SOS Now</span>
          </button>
        </div>
      </div>
    </div>
  );
}
