import { Link } from 'react-router-dom'

function Navbar({ onMenuClick }) {
  return (
    <nav className="border-b border-gray-800 bg-gray-900/80 backdrop-blur-sm">
      <div className="flex items-center justify-between px-4 py-3 sm:px-6">
        <div className="flex items-center gap-3">
          {/* Mobile menu button */}
          <button
            onClick={onMenuClick}
            className="rounded-lg p-2 text-gray-400 transition-colors hover:bg-gray-800 hover:text-white lg:hidden"
            title="Open menu"
          >
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>

          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-600">
            <svg className="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 11c0 3.517-1.009 6.799-2.753 9.571m-3.44-2.04l.054-.09A13.916 13.916 0 008 8a4 4 0 118 0c0 1.017-.07 2.019-.203 3m-2.118 6.844A21.88 21.88 0 0015.171 17h3.839c.278 0 .554-.042.822-.125M19 9c0 1.017-.07 2.019-.203 3m-2.118 6.844A21.88 21.88 0 0112 21m0 0a21.88 21.88 0 01-4.679-1.281" />
            </svg>
          </div>
          <div>
            <h1 className="text-sm font-bold text-white sm:text-base">
              Crime Analysis System
            </h1>
            <p className="hidden text-xs text-gray-500 sm:block">
              AI-Powered Hotspot & Proximity Alert
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button className="relative rounded-lg p-2 text-gray-400 transition-colors hover:bg-gray-800 hover:text-white">
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
            <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-red-500" />
          </button>

          <div className="hidden items-center gap-3 border-l border-gray-800 pl-3 sm:flex">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gray-800 text-sm font-medium text-gray-300">
              AD
            </div>
            <div className="hidden md:block">
              <p className="text-xs font-medium text-gray-300">Admin</p>
              <p className="text-[10px] text-gray-500">System Administrator</p>
            </div>
          </div>

          <Link
            to="/login"
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
          >
            Sign Out
          </Link>
        </div>
      </div>
    </nav>
  )
}

export default Navbar