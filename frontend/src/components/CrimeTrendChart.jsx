import Card from './Card'
import CardHeader from './CardHeader'

function CrimeTrendChart({ data = [], loading = false, error = '' }) {
  const maxCrimes = data.length ? Math.max(...data.map((d) => d.count)) : 0
  const totalCrimes = data.reduce((acc, d) => acc + d.count, 0)
  const average = data.length ? Math.round(totalCrimes / data.length) : 0
  const peak = data.reduce((acc, d) => (d.count > (acc.count || 0) ? d : acc), data[0] || {})
  const hasData = data.length > 0

  let body

  if (loading) {
    body = <p className="py-10 text-center text-sm text-gray-500">Loading trend data&hellip;</p>
  } else if (error) {
    body = (
      <div className="py-10 text-center text-sm text-red-400" role="alert">
        {error}
      </div>
    )
  } else if (hasData) {
    body = (
      <div className="flex items-end gap-1 sm:gap-2">
        {data.map((item) => {
          const ratio = maxCrimes ? item.count / maxCrimes : 0
          return (
            <div
              key={item.label}
              className="group flex flex-1 flex-col items-center gap-1 sm:gap-2"
            >
              {/* Explicitly-sized bar track: the percentage height below always
                  resolves against this definite height (not a flex-derived one),
                  so the bar reliably renders in every browser. */}
              <div className="relative h-36 w-full sm:h-44">
                <div
                  className="absolute bottom-0 left-1/2 w-full max-w-[28px] -translate-x-1/2 rounded-t-md bg-gradient-to-t from-blue-600 to-cyan-400 transition-all duration-300 group-hover:from-blue-500 group-hover:to-cyan-300"
                  style={{ height: `${ratio * 100}%` }}
                >
                  <span className="absolute -top-6 left-1/2 -translate-x-1/2 whitespace-nowrap rounded bg-gray-800 px-2 py-0.5 text-xs text-white opacity-0 transition-opacity group-hover:opacity-100">
                    {item.count}
                  </span>
                </div>
              </div>
              <span className="text-[10px] text-gray-500 sm:text-xs">{item.label}</span>
            </div>
          )
        })}
      </div>
    )
  } else {
    body = <p className="py-10 text-center text-sm text-gray-500">No trend data available.</p>
  }

  return (
    <Card>
      <CardHeader title="Crime Trend" subtitle="Incidents by publication year" />

      {body}

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