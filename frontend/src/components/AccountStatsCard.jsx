import Card from './Card'
import CardHeader from './CardHeader'

function AccountStatsCard({ stats }) {
  return (
    <Card>
      <CardHeader
        title="Account Statistics"
        subtitle="Your activity overview"
        icon="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-lg bg-gray-800/50 p-4">
          <p className="text-xs text-gray-500">Alerts Received</p>
          <p className="mt-1 text-2xl font-bold text-red-400">{stats.alertsReceived}</p>
        </div>
        <div className="rounded-lg bg-gray-800/50 p-4">
          <p className="text-xs text-gray-500">Reports Viewed</p>
          <p className="mt-1 text-2xl font-bold text-blue-400">{stats.crimeReportsViewed}</p>
        </div>
        <div className="rounded-lg bg-gray-800/50 p-4">
          <p className="text-xs text-gray-500">Last Login</p>
          <p className="mt-1 text-sm font-medium text-gray-300">{stats.lastLogin}</p>
        </div>
      </div>
    </Card>
  )
}

export default AccountStatsCard