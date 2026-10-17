import Card from './Card'
import CardHeader from './CardHeader'

function AccountStatsCard({ stats }) {
  return (
    <Card>
      <CardHeader
        title="Account Activity Summary"
        subtitle="Verified jurisdictional records and status"
        icon="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-lg bg-gray-800/50 p-4">
          <p className="text-xs text-gray-500">{stats?.stat1Label || 'Reports Submitted'}</p>
          <p className="mt-1 text-2xl font-bold text-blue-400">{stats?.alertsReceived ?? 0}</p>
        </div>
        <div className="rounded-lg bg-gray-800/50 p-4">
          <p className="text-xs text-gray-500">{stats?.stat2Label || 'Approved Incidents'}</p>
          <p className="mt-1 text-2xl font-bold text-green-400">{stats?.crimeReportsViewed ?? 0}</p>
        </div>
        <div className="rounded-lg bg-gray-800/50 p-4">
          <p className="text-xs text-gray-500">{stats?.stat3Label || 'Auth Session'}</p>
          <p className="mt-1 text-sm font-semibold text-gray-200">{stats?.lastLogin || 'Active'}</p>
        </div>
      </div>
    </Card>
  )
}

export default AccountStatsCard