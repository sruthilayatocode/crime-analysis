import React from 'react';
import { NavLink } from 'react-router-dom';
import { Compass, Bookmark, ShieldAlert, Settings } from 'lucide-react';

const navItems = [
  {
    to: '/app',
    end: true,
    label: 'Home',
    icon: Compass,
    ariaLabel: 'Home tab: search and map navigation',
  },
  {
    to: '/app/saved',
    end: false,
    label: 'Saved',
    icon: Bookmark,
    ariaLabel: 'Saved places tab',
  },
  {
    to: '/app/sos',
    end: false,
    label: 'SOS',
    icon: ShieldAlert,
    ariaLabel: 'Emergency SOS tab',
    highlight: true,
  },
  {
    to: '/app/settings',
    end: false,
    label: 'Settings',
    icon: Settings,
    ariaLabel: 'Settings and preferences tab',
  },
];

export default function UserBottomNav() {
  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-40 bg-white/95 backdrop-blur-md border-t border-slate-200/80 shadow-[0_-4px_20px_rgba(0,0,0,0.05)] transition-all max-w-[430px] mx-auto"
      aria-label="User navigation"
    >
      <div className="flex items-center justify-around h-16 px-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              aria-label={item.ariaLabel}
              className={({ isActive }) =>
                `flex flex-col items-center justify-center flex-1 min-h-[48px] min-w-[48px] py-1 px-2 rounded-xl transition-all duration-200 select-none ${
                  isActive
                    ? item.highlight
                      ? 'text-red-600 font-bold'
                      : 'text-blue-600 font-bold'
                    : 'text-slate-500 hover:text-slate-800 font-medium'
                } active:scale-95`
              }
            >
              {({ isActive }) => (
                <>
                  <div
                    className={`relative p-1 rounded-lg transition-transform ${
                      isActive
                        ? item.highlight
                          ? 'bg-red-50 text-red-600 scale-110'
                          : 'bg-blue-50 text-blue-600 scale-110'
                        : ''
                    }`}
                  >
                    <Icon className="w-5 h-5 stroke-[2.2]" aria-hidden="true" />
                    {item.highlight && (
                      <span className="absolute top-0.5 right-0.5 w-2 h-2 rounded-full bg-red-500 ring-2 ring-white animate-pulse" />
                    )}
                  </div>
                  <span className="text-[11px] mt-0.5 tracking-tight leading-none">
                    {item.label}
                  </span>
                </>
              )}
            </NavLink>
          );
        })}
      </div>
    </nav>
  );
}
