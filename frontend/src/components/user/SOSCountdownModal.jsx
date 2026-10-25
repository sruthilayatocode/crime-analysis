import React from 'react';
import { ShieldAlert, X, Zap } from 'lucide-react';
import { useSOS } from '../../context/SOSContext';

export default function SOSCountdownModal() {
  const { isCountingDown, countdown, cancelCountdown, executeSOSTriggerNow } = useSOS();

  if (!isCountingDown) return null;

  const progressPercent = ((5 - countdown) / 5) * 100;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md animate-in fade-in duration-150">
      <div className="bg-white rounded-3xl p-6 max-w-sm w-full text-center space-y-5 shadow-2xl border-2 border-red-500/50">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-red-100 text-red-700 text-xs font-black uppercase tracking-wider animate-pulse">
            <ShieldAlert className="w-4 h-4" />
            <span>Emergency Distress Signal</span>
          </div>
          <h2 className="text-xl font-black text-slate-900 pt-1">
            Dispatching SOS in {countdown}s
          </h2>
          <p className="text-xs text-slate-500">
            Hold on! Emergency notifications will be sent to all your SOS contacts.
          </p>
        </div>

        {/* Circular Countdown Ring */}
        <div className="relative flex items-center justify-center w-36 h-36 mx-auto">
          {/* Animated pulsing outer waves */}
          <div className="absolute inset-0 rounded-full bg-red-500/20 animate-ping" />
          <div className="absolute -inset-2 rounded-full bg-red-500/10 animate-pulse" />

          {/* SVG Progress Circle */}
          <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
            <circle
              cx="50"
              cy="50"
              r="44"
              className="stroke-slate-200"
              strokeWidth="8"
              fill="transparent"
            />
            <circle
              cx="50"
              cy="50"
              r="44"
              className="stroke-red-600 transition-all duration-1000 ease-linear"
              strokeWidth="8"
              fill="transparent"
              strokeDasharray="276.46"
              strokeDashoffset={276.46 - (276.46 * progressPercent) / 100}
              strokeLinecap="round"
            />
          </svg>

          {/* Center Countdown Number */}
          <div className="absolute flex flex-col items-center justify-center">
            <span className="text-5xl font-black text-red-600 leading-none">
              {countdown}
            </span>
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mt-1">
              Seconds
            </span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="space-y-2 pt-2">
          <button
            type="button"
            onClick={cancelCountdown}
            className="w-full py-3.5 px-4 rounded-2xl bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold text-sm transition-all active:scale-98 min-h-[48px] flex items-center justify-center gap-2 border border-slate-300"
          >
            <X className="w-4 h-4 stroke-[2.5]" />
            <span>Cancel Alert (I'm Okay)</span>
          </button>

          <button
            type="button"
            onClick={executeSOSTriggerNow}
            className="w-full py-2.5 px-4 text-xs font-bold text-red-600 hover:text-red-700 flex items-center justify-center gap-1.5 transition-colors"
          >
            <Zap className="w-3.5 h-3.5" />
            <span>Send Alert Immediately</span>
          </button>
        </div>
      </div>
    </div>
  );
}
