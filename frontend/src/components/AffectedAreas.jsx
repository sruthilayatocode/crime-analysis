import Card from './Card'
import CardHeader from './CardHeader'

/**
 * Top areas by recorded incident count using locality first, then district.
 * Clearly framed as an incident-distribution view, NOT a geographic
 * hotspot / danger analysis.
 */
function AffectedAreas({ data = [] }) {
  const max = data.length ? Math.max(...data.map((d) => d.count)) : 0

  return (
    <Card className="h-full">
      <CardHeader
        title="Most Affected Areas"
        subtitle="Incident distribution by area"
      />

      <p className="mb-3 text-xs text-gray-500">
        Locality (falling back to district). Incident counts only — not a
        geographic hotspot or danger assessment.
      </p>

      {data.length === 0 ? (
        <p className="py-6 text-center text-sm text-gray-500">
          No area data available.
        </p>
      ) : (
        <ul className="space-y-2.5">
          {data.map((item) => (
            <li key={item.label} className="flex items-center gap-3">
              <span
                className="w-36 shrink-0 truncate text-xs text-gray-300"
                title={item.label}
              >
                {item.label}
              </span>
              <div className="h-3 flex-1 overflow-hidden rounded-full bg-gray-800/60">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-violet-600 to-fuchsia-400"
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

export default AffectedAreas