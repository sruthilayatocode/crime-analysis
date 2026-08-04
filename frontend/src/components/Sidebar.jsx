import { Link, useLocation } from 'react-router-dom'

const navItems = [
  { to: '/', label: 'Dashboard', icon: 'M3 12l9-9 9 9M5 10v10a1 1 0 001 1h3a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1h3a1 1 0 001-1V10' },
  { to: '/crime-hotspots', label: 'Crime Hotspots', icon: 'M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0zM15 11a3 3 0 11-6 0 3 3 0 016 0z' },
  { to: '/map', label: 'Interactive Map', icon: 'M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7' },
  { to: '/gps-tracking', label: 'GPS Tracking', icon: 'M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0zM15 11a3 3 0 11-6 0 3 3 0 016 0z' },
  { to: '/alerts', label: 'Alerts', icon: 'M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9' },
  { to: '/profile', label: 'Profile', icon: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z' },
]

function Sidebar({ collapsed, onToggle, mobileOpen, onMobileClose }) {
  const location = useLocation()

  return (
    <>
      {/* Mobile sidebar */}
      <div
        className={`fixed inset-0 z-40 bg-black/60 backdrop-blur-sm transition-opacity duration-300 lg:hidden ${
          mobileOpen ? 'opacity-100' : 'pointer-events-none opacity-0'
        }`}
        onClick={onMobileClose}
      />
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex shrink-0 flex-col border-r border-gray-800 bg-gray-900/95 backdrop-blur-sm transition-all duration-300 lg:static ${
          collapsed ? 'lg:w-16' : 'lg:w-64'
        } ${
          mobileOpen ? 'w-64 translate-x-0' : 'w-64 -translate-x-full lg:translate-x-0'
        }`}
      >
        <div className="flex items-center justify-between border-b border-gray-800 p-4">
          {!collapsed && (
            <span className="text-sm font-semibold text-gray-400">Navigation</span>
          )}
          <div className="flex items-center gap-1">
            {/* Collapse toggle - desktop only */}
            <button
              onClick={onToggle}
              className="hidden rounded-lg p-2 text-gray-400 transition-colors hover:bg-gray-800 hover:text-white lg:block"
              title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            >
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                {collapsed ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
                )}
              </svg>
            </button>
            {/* Close button on mobile */}
            <button
              onClick={onMobileClose}
              className="rounded-lg p-2 text-gray-400 transition-colors hover:bg-gray-800 hover:text-white lg:hidden"
              title="Close sidebar"
            >
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <nav className="flex flex-1 flex-col gap-1 p-3">
          {navItems.map((item) => {
            const isActive = location.pathname === item.to
            return (
              <Link
                key={item.to}
                to={item.to}
                onClick={onMobileClose}
                className={`group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-blue-600/20 text-blue-400'
                    : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                }`}
                title={collapsed ? item.label : undefined}
              >
                <svg
                  className={`h-5 w-5 shrink-0 ${isActive ? 'text-blue-400' : 'text-gray-500 group-hover:text-gray-300'}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d={item.icon} />
                </svg>
                <span className="truncate lg:hidden">{item.label}</span>
                {!collapsed && (
                  <>
                    <span className="hidden truncate lg:inline">{item.label}</span>
                    {isActive && (
                      <span className="ml-auto hidden h-1.5 w-1.5 rounded-full bg-blue-400 lg:block" />
                    )}
                  </>
                )}
              </Link>
            )
          })}
        </nav>

        <div className="border-t border-gray-800 p-3">
          {!collapsed ? (
            <div className="rounded-lg bg-gray-800/50 p-3">
              <p className="text-xs font-medium text-gray-300">System Status</p>
              <div className="mt-2 flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-green-500" />
                <span className="text-xs text-gray-500">All systems operational</span>
              </div>
            </div>
          ) : (
            <div className="flex justify-center">
              <span className="h-2 w-2 rounded-full bg-green-500" />
            </div>
          )}
        </div>
      </aside>
    </>
  )
}

export default Sidebar