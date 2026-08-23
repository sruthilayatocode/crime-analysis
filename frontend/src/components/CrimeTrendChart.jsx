import Card from './Card'
import CardHeader from './CardHeader'

function CrimeTrendChart({ data = [] }) {
  const maxCrimes = data.length ? Math.max(...data.map((d) => d.count)) : 0
  const totalCrimes = data.reduce((acc, d) => acc + d.count, 0)
  const average = data.length ? Math.round(totalCrimes / data.length) : 0
  const peak = data.reduce((acc, d) => (d.count > (acc.count || 0) ? d : acc), data[0] || {})
  const hasData = data.length > 0

  return (
    <Card>
      <CardHeader
        title="Crime Trend"
        subtitle="Incidents by publication year"
      />

      {hasData ? (
        <div className="flex h-48 items-end gap-2 sm:h-56">
          {data.map((item) => (
            <div key={item.label} className="group flex flex-1 flex-col items-center gap-2">
              <div className="relative flex w-full flex-1 items-end justify-center">
                <div
                  className="w-full max-w-[28px] rounded-t-md bg-gradient-to-t from-blue-600 to-cyan-400 transition-all duration-300 group-hover:from-blue-500 group-hover:to-cyan-300"
                  style={{ height: `${maxCrimes ? (item.count / maxCrimes) * 100 : 0}%` }}
                >
                  <span className="absolute -top-6 left-1/2 -translate-x-1/2 rounded bg-gray-800 px-2 py-0.5 text-xs text-white opacity-0 transition-opacity group-hover:opacity-100">
                    {item.count}
                  </span>
                </div>
              </div>
              <span className="text-xs text-gray-500">{item.label}</span>
            </div>
          ))}
        </div>
      ) : (
        <p className="py-10 text-center text-sm text-gray-500">No trend data available.</p>
      )}

      <div className="mt-4 border-t border-gray-800 pt-4">
        <div className="flex items-center gap-6 text-sm text-gray-400">
          <span className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-blue-500" />
            {hasData ? `Peak: ${peak.label} (${peak.count} incidents)` : 'Peak: n/a'}
          </span>
          <span className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-cyan-400" />
            {hasData ? `Average: ${average} incidents/year` : 'Average: n/a'}
          </span>
        </div>
      </div>
    </Card>
  )
}

export default CrimeTrendChart