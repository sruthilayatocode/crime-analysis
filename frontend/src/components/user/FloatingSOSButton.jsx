import React, { useState, useRef, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { ShieldAlert, AlertTriangle } from 'lucide-react';
import { useSOS } from '../../context/SOSContext';

/**
 * Floating SOS button with Press-and-Hold (2 seconds) or Double-Tap safety confirmation.
 * Once activated, starts the 5-second countdown with sound and abort option.
 */
export default function FloatingSOSButton() {
  const location = useLocation();
  const { startSOSCountdown, isCountingDown, activeSosEvent } = useSOS();

  const [isHolding, setIsHolding] = useState(false);
  const [holdProgress, setHoldProgress] = useState(0);
  const holdTimerRef = useRef(null);
  const holdIntervalRef = useRef(null);
  const lastTapRef = useRef(0);

  // If already counting down or on active SOS screen, do not show button
  if (isCountingDown || activeSosEvent) return null;

  // Handle Press and Hold (2000ms duration)
  const startHold = () => {
    setIsHolding(true);
    setHoldProgress(0);
    const startTime = Date.now();
    const duration = 2000;

    holdIntervalRef.current = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const pct = Math.min(100, (elapsed / duration) * 100);
      setHoldProgress(pct);
    }, 40);

    holdTimerRef.current = setTimeout(() => {
      clearHold();
      startSOSCountdown();
    }, duration);
  };

  const clearHold = () => {
    setIsHolding(false);
    setHoldProgress(0);
    if (holdTimerRef.current) {
      clearTimeout(holdTimerRef.current);
      holdTimerRef.current = null;
    }
    if (holdIntervalRef.current) {
      clearInterval(holdIntervalRef.current);
      holdIntervalRef.current = null;
    }
  };

  // Double tap handler as alternative for rapid emergency trigger
  const handleTap = (e) => {
    const now = Date.now();
    const DOUBLE_TAP_DELAY = 450;
    if (now - lastTapRef.current < DOUBLE_TAP_DELAY) {
      clearHold();
      startSOSCountdown();
    }
    lastTapRef.current = now;
  };

  return (
    <div className="fixed bottom-20 right-4 sm:right-[calc(50%-195px)] z-40 select-none">
      <div className="relative flex flex-col items-center">
        {/* Tooltip hint when holding */}
        {isHolding && (
          <div className="absolute -top-10 bg-slate-900 text-white text-[11px] font-black px-2.5 py-1 rounded-xl shadow-lg animate-bounce border border-red-500 whitespace-nowrap">
            Hold for 2s to Alert ({Math.round(holdProgress)}%)
          </div>
        )}

        <button
          type="button"
          aria-label="Emergency SOS - Press and hold 2 seconds to activate"
          onMouseDown={startHold}
          onMouseUp={clearHold}
          onMouseLeave={clearHold}
          onTouchStart={startHold}
          onTouchEnd={clearHold}
          onClick={handleTap}
          className="group relative flex items-center justify-center w-14 h-14 rounded-full bg-gradient-to-tr from-red-600 to-red-500 text-white shadow-[0_8px_25px_rgba(239,68,68,0.45)] hover:shadow-[0_10px_30px_rgba(239,68,68,0.6)] hover:scale-105 active:scale-95 transition-all duration-200 focus:outline-none focus:ring-4 focus:ring-red-300"
        >
          {/* Animated pulsing outer ring when idle */}
          {!isHolding && (
            <span className="absolute -inset-1 rounded-full bg-red-500/30 animate-ping pointer-events-none" />
          )}

          {/* SVG Circular Progress Ring on Hold */}
          {isHolding && (
            <svg className="absolute -inset-1 w-16 h-16 transform -rotate-90 pointer-events-none" viewBox="0 0 100 100">
              <circle
                cx="50"
                cy="50"
                r="46"
                className="stroke-white"
                strokeWidth="7"
                fill="transparent"
                strokeDasharray="289"
                strokeDashoffset={289 - (289 * holdProgress) / 100}
                strokeLinecap="round"
              />
            </svg>
          )}

          <div className="flex flex-col items-center justify-center pointer-events-none">
            <ShieldAlert className="w-5 h-5 stroke-[2.5]" aria-hidden="true" />
            <span className="text-[10px] font-black tracking-wider uppercase leading-none mt-0.5">
              SOS
            </span>
          </div>
        </button>

        <span className="text-[9px] font-bold text-slate-400 mt-1 uppercase tracking-tighter drop-shadow-xs">
          Hold 2s / 2x Tap
        </span>
      </div>
    </div>
  );
}
