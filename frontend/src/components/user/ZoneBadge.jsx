import React from 'react';
import { ShieldAlert, AlertTriangle, CheckCircle2, HelpCircle } from 'lucide-react';

/**
 * Accessible ZoneBadge component.
 * Distinguishable by color, icon, and textual label for maximum accessibility.
 */
export default function ZoneBadge({ zone = 'GREEN', size = 'md', className = '' }) {
  const normalizedZone = (zone || 'GREEN').toUpperCase();

  const configs = {
    RED: {
      label: 'RED ZONE',
      subtitle: 'High Risk',
      icon: ShieldAlert,
      bg: 'bg-red-50 border-red-200 text-red-800',
      badgeBg: 'bg-red-600 text-white',
      ring: 'ring-red-200',
      accentDot: 'bg-red-500',
    },
    YELLOW: {
      label: 'YELLOW ZONE',
      subtitle: 'Moderate Risk',
      icon: AlertTriangle,
      bg: 'bg-amber-50 border-amber-200 text-amber-800',
      badgeBg: 'bg-amber-500 text-white',
      ring: 'ring-amber-200',
      accentDot: 'bg-amber-500',
    },
    GREEN: {
      label: 'GREEN ZONE',
      subtitle: 'Low Risk / Safe',
      icon: CheckCircle2,
      bg: 'bg-emerald-50 border-emerald-200 text-emerald-800',
      badgeBg: 'bg-emerald-600 text-white',
      ring: 'ring-emerald-200',
      accentDot: 'bg-emerald-500',
    },
  };

  const current = configs[normalizedZone] || configs.GREEN;
  const Icon = current.icon;

  if (size === 'sm') {
    return (
      <span
        className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold border ${current.bg} ${className}`}
        role="status"
        aria-label={`${current.label}: ${current.subtitle}`}
      >
        <Icon className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
        <span>{current.label}</span>
      </span>
    );
  }

  if (size === 'lg') {
    return (
      <div
        className={`inline-flex items-center gap-2.5 px-4 py-2 rounded-xl border shadow-sm ${current.bg} ${className}`}
        role="status"
        aria-label={`${current.label}: ${current.subtitle}`}
      >
        <div className={`p-1.5 rounded-lg ${current.badgeBg} shrink-0`}>
          <Icon className="w-5 h-5" aria-hidden="true" />
        </div>
        <div className="flex flex-col text-left">
          <span className="text-xs font-black tracking-wider uppercase opacity-90">{current.label}</span>
          <span className="text-sm font-bold leading-tight">{current.subtitle}</span>
        </div>
      </div>
    );
  }

  // Default 'md'
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold border shadow-xs ${current.bg} ${className}`}
      role="status"
      aria-label={`${current.label}: ${current.subtitle}`}
    >
      <Icon className="w-4 h-4 shrink-0" aria-hidden="true" />
      <span>{current.label}</span>
      <span className="opacity-75 font-normal">· {current.subtitle}</span>
    </span>
  );
}
