import Card from './Card'
import CardHeader from './CardHeader'

const RISK_SEGMENT = {
  Critical: 'bg-red-500',
  High: 'bg-orange-500',
  Medium: 'bg-yellow-500',
  Low: 'bg-green-500',
  Unknown: 'bg-gray-500',
}

const RISK_DOT = {
  Critical: 'bg-red-400',
  High: 'bg-orange-400',
  Medium: 'bg-yellow-400',
  Low: 'bg-green-400',
  Unknown: 'bg-gray-400',
}

/**
 * Compact risk distribution using the stored risk_level field.
 * Each segment/row is sized purely from the actual record counts.
 */
function RiskIntelligence({ data = [], total = 0 }) {
  return (
    <Card className="h-full">
      <CardHeader
        title="Risk Intelligence"
        subtitle="Distribution by stored risk level"
      />

      {data.length === 0 ? (
        <p className="py-8 text-center text-sm text-gray-500">
          No risk data available.
        </p>
      ) : (
        <>
          <div className="flex h-3 w-full overflow-hidden rounded-full bg-gray-800/60">
            {data.map((d) => (
              <div
                key={d.label}
                className={RISK_SEGMENT[d.label] || 'bg-gray-500'}
                style={{ width: `${total ? (d.count / total) * 100 : 0}%` }}
                title={`${d.label}: ${d.count}`}
              />
            ))}
          </div>

          <ul className="mt-4 space-y-2">
            {data.map((d) => (
              <li key={d.label} className="flex items-center justify-between text-xs">
                <span className="flex items-center gap-2 text-gray-300">
                  <span
                    className={`h-2.5 w-2.5 rounded-full ${RISK_DOT[d.label] || 'bg-gray-400'}`}
                  />
                  {d.label}
                </span>
                <span className="flex items-center gap-2">
                  <span className="font-semibold text-white">{d.count}</span>
                  <span className="w-10 text-right text-gray-500">
                    {total ? Math.round((d.count / total) * 100) : 0}%
                  </span>
                </span>
              </li>
            ))}
          </ul>
        </>
      )}
    </Card>
  )
}

export default RiskIntelligence