import Card from './Card'
import CardHeader from './CardHeader'

function RecentActivityCard({ activities }) {
  return (
    <Card>
      <CardHeader
        title="Recent Activity"
        subtitle="Your latest actions"
        icon="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
      />

      <div className="space-y-4">
        {activities.map((activity) => (
          <div key={activity.id} className="flex items-start gap-3">
            <div className="relative flex flex-col items-center">
              <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-blue-500" />
              {activity.id < activities.length && (
                <span className="mt-1 h-full w-px bg-gray-800" />
              )}
            </div>
            <div className="flex-1 pb-4">
              <p className="text-sm text-gray-300">{activity.action}</p>
              <p className="mt-0.5 text-xs text-gray-500">{activity.time}</p>
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}

export default RecentActivityCard