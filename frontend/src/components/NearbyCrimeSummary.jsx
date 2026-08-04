import Card from './Card'
import CardHeader from './CardHeader'

function NearbyCrimeSummary({ summary }) {
  return (
    <Card>
      <CardHeader
        title="Nearby Crime Summary"
        subtitle="Crime statistics in your area"
        icon="M13 10V3L4 14h7v7l9-11h-7z"
        iconBg="bg-red-500/20"
        iconColor="text-red-400"
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-lg bg-gray-800/50 p-4">
          <p className="text-xs text-gray-500">Total Nearby Crimes</p>
          <p className="mt-1 text-2xl font-bold text-red-400">{summary.totalCrimes}</p>
        </div>
        <div className="rounded-lg bg-gray-800/50 p-4">
          <p className="text-xs text-gray-500">Most Common Crime</p>
          <p className="mt-1 text-lg font-semibold text-gray-300">{summary.mostCommonCrime}</p>
        </div>
        <div className="rounded-lg bg-gray-800/50 p-4">
          <p className="text-xs text-gray-500">Last Reported Incident</p>
          <p className="mt-1 text-sm font-medium text-gray-300">{summary.lastReported}</p>
        </div>
      </div>
    </Card>
  )
}

export default NearbyCrimeSummary