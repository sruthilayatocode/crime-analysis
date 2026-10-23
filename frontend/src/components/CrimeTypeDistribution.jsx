import Card from './Card'
import CardHeader from './CardHeader'

/**
 * Horizontal bar chart of incident counts per real crime_type.
 * Data is derived from /api/crimes and sorted highest -> lowest.
 */
function CrimeTypeDistribution({ data = [] }) {
  const max = data.length ? Math.max(...data.map((d) => d.count)) : 0

  return (
    <Card className="h-full">
      <CardHeader
        title="Crime Type Distribution"
        subtitle="Incidents grouped by crime type"
      />

      {data.length === 0 ? (
        <p className="py-8 text-center text-sm text-gray-500">
          No crime type data available.
        </p>
      ) : (
        <ul className="space-y-2.5">
          {data.map((item) => (
            <li key={item.label} className="flex items-center gap-3">
              <span
                className="w-32 shrink-0 truncate text-xs text-gray-300"
                title={item.label}
              >
                {item.label}
              </span>
              <div className="h-3 flex-1 overflow-hidden rounded-full bg-gray-800/60">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-blue-600 to-cyan-400"
                  style={{ width: `${max ? (item.count / max) * 100 : 0}%` }}
                />
              </div>
              <span className="w-7 shrink-0 text-right text-xs font-semibold text-white">
                {item.count}
              </span>
            </li>
          ))}
        </ul>
      )}
    </Card>
  )
}

export default CrimeTypeDistribution
