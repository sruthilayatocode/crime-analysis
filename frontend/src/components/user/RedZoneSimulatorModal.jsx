import React, { useState } from 'react';
import {
  Sliders,
  Play,
  RotateCcw,
  ShieldAlert,
  AlertTriangle,
  Clock,
  Radio,
  CheckCircle2,
  X,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { useSOS } from '../../context/SOSContext';
import { sosService } from '../../services/sosService';

export default function RedZoneSimulatorModal() {
  // Only render simulator if explicitly enabled in environment
  const isSimulatorEnabled = import.meta.env.VITE_ENABLE_SIMULATOR === 'true';
  if (!isSimulatorEnabled) return null;

  const {
    redZoneState,
    setRedZoneState,
    currentZone,
    isWarningActive,
    warningCountdown,
    triggerWarningPrompt,
    confirmSafetyCheckin,
    refreshContacts,
  } = useSOS();

  const [isOpen, setIsOpen] = useState(false);
  const [loadingAction, setLoadingAction] = useState('');
  const [simLog, setSimLog] = useState('');
  const [thresholdMin, setThresholdMin] = useState(1);

  const runSimulation = async (action) => {
    setLoadingAction(action);
    setSimLog('Executing simulation...');
    try {
      const data = await sosService.simulateRedZone(action, thresholdMin);
      setSimLog(data.message || 'Action executed successfully.');
      if (data.state) {
        setRedZoneState(data.state.state);
        if (data.state.state === 'WARNING') {
          triggerWarningPrompt(data.state.seconds_remaining || 60);
        } else if (data.state.state === 'SAFE') {
          confirmSafetyCheckin();
        }
      }
    } catch (err) {
      setSimLog(`Error: ${err.message}`);
    } finally {
      setLoadingAction('');
    }
  };

  return (
    <div className="fixed top-3 left-4 z-40">
      {/* Mini Toggle Pill */}
      {!isOpen ? (
        <button
          type="button"
          onClick={() => setIsOpen(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-900/90 text-amber-400 text-[11px] font-black shadow-lg border border-amber-500/40 hover:bg-slate-900 transition-all"
        >
          <Sliders className="w-3.5 h-3.5 text-amber-400" />
          <span>Dev Red Zone Simulator</span>
          <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse ml-0.5" />
        </button>
      ) : (
        <div className="w-80 bg-slate-900/95 text-white rounded-2xl p-4 shadow-2xl border border-slate-700 space-y-3 backdrop-blur-md animate-in fade-in-50">
          {/* Header */}
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <Sliders className="w-4 h-4 text-amber-400" />
              <span className="text-xs font-bold text-white uppercase tracking-wider">
                Red Zone Simulator
              </span>
            </div>
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="p-1 text-slate-400 hover:text-white rounded-lg"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Current State Indicator */}
          <div className="bg-slate-800/80 rounded-xl p-2.5 flex items-center justify-between text-xs">
            <div>
              <span className="text-[10px] font-bold text-slate-400 uppercase block">State</span>
              <span
                className={`font-black uppercase tracking-wider ${
                  redZoneState === 'AUTO_ALERT_SENT'
                    ? 'text-red-400'
                    : redZoneState === 'WARNING'
                    ? 'text-amber-400'
                    : redZoneState === 'IN_RED'
                    ? 'text-rose-400'
                    : 'text-emerald-400'
                }`}
              >
                {redZoneState}
              </span>
            </div>
            <div className="text-right">
              <span className="text-[10px] font-bold text-slate-400 uppercase block">Threshold</span>
              <span className="font-mono text-slate-200">{thresholdMin} Min</span>
            </div>
          </div>

          {/* Action Simulation Buttons */}
          <div className="space-y-1.5 pt-1">
            <button
              type="button"
              disabled={loadingAction !== ''}
              onClick={() => runSimulation('enter_red')}
              className="w-full py-2 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold flex items-center justify-between transition-colors border border-slate-700"
            >
              <span>1. Enter RED Zone</span>
              <Radio className="w-3.5 h-3.5 text-red-400" />
            </button>

            <button
              type="button"
              disabled={loadingAction !== ''}
              onClick={() => runSimulation('simulate_inactivity')}
              className="w-full py-2 px-3 rounded-xl bg-amber-950/40 hover:bg-amber-900/60 text-amber-200 text-xs font-bold flex items-center justify-between transition-colors border border-amber-600/40"
            >
              <span>2. Simulate Inactivity ({thresholdMin}m)</span>
              <Clock className="w-3.5 h-3.5 text-amber-400" />
            </button>

            <button
              type="button"
              disabled={loadingAction !== ''}
              onClick={() => runSimulation('trigger_warning')}
              className="w-full py-2 px-3 rounded-xl bg-amber-600/20 hover:bg-amber-600/30 text-amber-300 text-xs font-bold flex items-center justify-between transition-colors border border-amber-500/50"
            >
              <span>3. Trigger 60s Warning</span>
              <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
            </button>

            <button
              type="button"
              disabled={loadingAction !== ''}
              onClick={() => runSimulation('simulate_timeout')}
              className="w-full py-2 px-3 rounded-xl bg-red-600 hover:bg-red-700 text-white text-xs font-black flex items-center justify-between transition-colors shadow-sm"
            >
              <span>4. Simulate Timeout &rarr; Auto SOS</span>
              <ShieldAlert className="w-3.5 h-3.5 text-white" />
            </button>

            <button
              type="button"
              disabled={loadingAction !== ''}
              onClick={() => runSimulation('reset')}
              className="w-full py-1.5 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white text-[11px] font-bold flex items-center justify-center gap-1 transition-colors"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Reset State to SAFE</span>
            </button>
          </div>

          {/* Feedback Log */}
          {simLog && (
            <p className="text-[10px] text-slate-400 font-mono bg-black/40 p-2 rounded-lg border border-slate-800 leading-tight">
              {simLog}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
