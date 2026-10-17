import Card from './Card'
import CardHeader from './CardHeader'
import { crimeTrendData as defaultData } from '../data/dashboardData'

function formatMonthlyData(input) {
  if (!input) return defaultData

  if (Array.isArray(input)) {
    return input.length > 0 ? input : defaultData
  }

  if (typeof input === 'object') {
    const entries = Object.entries(input).filter(([k]) => k !== 'Unknown')
    if (entries.length === 0) return defaultData

    return entries.slice(-12).map(([monthStr, count]) => {
      // monthStr is typically YYYY-MM
      const parts = monthStr.split('-')
      const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
      const label = parts.length >= 2 && parseInt(parts[1], 10) >= 1 && parseInt(parts[1], 10) <= 12
        ? `${monthNames[parseInt(parts[1], 10) - 1]} '${parts[0].slice(2)}`
        : monthStr

      return {
        month: label,
        crimes: count,
      }
    })
  }

  return defaultData
}

function CrimeTrendChart({ monthlyData = null }) {
  const chartData = formatMonthlyData(monthlyData)
  const maxCrimes = Math.max(1, ...chartData.map((d) => d.crimes))
  const totalCrimes = chartData.reduce((acc, d) => acc + d.crimes, 0)
  const avgCrimes = Math.round(totalCrimes / Math.max(1, chartData.length))

  // Find peak
  const peakItem = [...chartData].sort((a, b) => b.crimes - a.crimes)[0]

  return (
    <Card>
      <CardHeader
        title="Crime Incident Trends"
        subtitle="Historical incident frequency over time"
        action={
          <span className="rounded-lg bg-blue-600/10 border border-blue-500/30 px-2.5 py-1 text-xs font-semibold text-blue-400">
            Verified Data
          </span>
        }
      />

      <div className="flex h-48 items-end gap-2 sm:h-56">
        {chartData.map((item) => (
          <div key={item.month} className="group flex flex-1 flex-col items-center gap-2">
            <div className="relative flex w-full flex-1 items-end justify-center">
              <div
                className="w-full max-w-[28px] rounded-t-md bg-gradient-to-t from-blue-600 to-cyan-400 transition-all duration-300 group-hover:from-blue-500 group-hover:to-cyan-300"
                style={{ height: `${Math.max(8, (item.crimes / maxCrimes) * 100)}%` }}
              >
                <span className="absolute -top-6 left-1/2 -translate-x-1/2 rounded bg-gray-800 px-2 py-0.5 text-xs text-white opacity-0 transition-opacity group-hover:opacity-100 z-10 pointer-events-none whitespace-nowrap shadow">
                  {item.crimes} incident{item.crimes === 1 ? '' : 's'}
                </span>
              </div>
            </div>
            <span className="text-[11px] font-medium text-gray-500 truncate max-w-full text-center">
              {item.month}
            </span>
          </div>
        ))}
      </div>

      <div className="mt-4 border-t border-gray-800 pt-4">
        <div className="flex flex-wrap items-center gap-6 text-xs sm:text-sm text-gray-400">
          {peakItem && (
            <span className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-blue-500" />
              Peak: <strong className="text-gray-200">{peakItem.month}</strong> ({peakItem.crimes} incidents)
            </span>
          )}
          <span className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-cyan-400" />
            Average: <strong className="text-gray-200">{avgCrimes}</strong> incidents / period
          </span>
        </div>
      </div>
    </Card>
  )
}

export default CrimeTrendChart