import { useState } from 'react'
import Card from './Card'
import CardHeader from './CardHeader'

function Toggle({ enabled, onChange }) {
  return (
    <button
      onClick={() => onChange(!enabled)}
      className={`relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors ${
        enabled ? 'bg-blue-600' : 'bg-gray-700'
      }`}
      role="switch"
      aria-checked={enabled}
    >
      <span
        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
          enabled ? 'translate-x-6' : 'translate-x-1'
        }`}
      />
    </button>
  )
}

function SettingsCard({ settings }) {
  const [notifications, setNotifications] = useState(settings.notifications)
  const [darkMode, setDarkMode] = useState(settings.darkMode)

  return (
    <Card>
      <CardHeader
        title="Settings"
        subtitle="Manage your preferences"
        icon="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065zM15 12a3 3 0 11-6 0 3 3 0 016 0z"
      />

      <div className="space-y-4">
        <div className="flex items-center justify-between rounded-lg bg-gray-800/50 p-4 transition-colors hover:bg-gray-800/70">
          <div>
            <p className="text-sm font-medium text-gray-300">Notifications</p>
            <p className="text-xs text-gray-500">Receive alert notifications</p>
          </div>
          <Toggle enabled={notifications} onChange={setNotifications} />
        </div>

        <div className="flex items-center justify-between rounded-lg bg-gray-800/50 p-4 transition-colors hover:bg-gray-800/70">
          <div>
            <p className="text-sm font-medium text-gray-300">Dark Mode</p>
            <p className="text-xs text-gray-500">Use dark theme (UI only)</p>
          </div>
          <Toggle enabled={darkMode} onChange={setDarkMode} />
        </div>

        <div className="flex items-center justify-between rounded-lg bg-gray-800/50 p-4 transition-colors hover:bg-gray-800/70">
          <div>
            <p className="text-sm font-medium text-gray-300">GPS Permission</p>
            <p className="text-xs text-gray-500">Location tracking access</p>
          </div>
          <span className="inline-flex items-center gap-1.5 rounded-full border border-green-500/30 bg-green-500/10 px-2.5 py-1 text-xs font-medium text-green-400">
            <span className="h-1.5 w-1.5 rounded-full bg-green-500" />
            {settings.gpsPermission}
          </span>
        </div>
      </div>
    </Card>
  )
}

export default SettingsCard