import Card from './Card'
import CardHeader from './CardHeader'
import StatusBadge from './StatusBadge'

function RecentAlerts({ alerts = [] }) {
  return (
    <Card>
      <CardHeader
        title="Recent Alerts"
        subtitle="Derived from validated incidents"
        action={
          <span className="flex h-2 w-2">
            <span className="absolute inline-flex h-2 w-2 animate-ping rounded-full bg-red-400 opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-red-500" />
          </span>
        }
      />

      {alerts.length > 0 ? (
        <div className="space-y-3">
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className="rounded-lg border border-gray-800 bg-gray-800/30 p-4 transition-colors hover:bg-gray-800/50"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="text-sm font-medium text-gray-200">{alert.title}</h3>
                  <p className="mt-0.5 text-xs text-gray-500">{alert.description}</p>
                </div>
                <div className="flex shrink-0 flex-col items-end gap-1">
                  <StatusBadge status={alert.priority} />
                  <span className="text-[10px] text-gray-600">{alert.time}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="py-8 text-center text-sm text-gray-500">No alerts derived from current records.</p>
      )}

      <button className="mt-4 w-full rounded-lg bg-gray-800 px-3 py-2 text-xs font-medium text-gray-400 transition-colors hover:bg-gray-700 hover:text-white">
        View All Alerts
      </button>
    </Card>
  )
}

export default RecentAlerts