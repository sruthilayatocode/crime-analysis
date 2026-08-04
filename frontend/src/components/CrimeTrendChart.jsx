import Card from './Card'
import CardHeader from './CardHeader'
import { crimeTrendData } from '../data/dashboardData'

function CrimeTrendChart() {
  const maxCrimes = Math.max(...crimeTrendData.map((d) => d.crimes))

  return (
    <Card>
      <CardHeader
        title="Crime Trend"
        subtitle="Monthly crime incidents - 2024"
        action={
          <div className="flex gap-2">
            <button className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-medium text-white">
              Yearly
            </button>
            <button className="rounded-lg bg-gray-800 px-3 py-1.5 text-xs font-medium text-gray-400 hover:text-white">
              Monthly
            </button>
          </div>
        }
      />

      <div className="flex h-48 items-end gap-2 sm:h-56">
        {crimeTrendData.map((item) => (
          <div key={item.month} className="group flex flex-1 flex-col items-center gap-2">
            <div className="relative flex w-full flex-1 items-end justify-center">
              <div
                className="w-full max-w-[28px] rounded-t-md bg-gradient-to-t from-blue-600 to-cyan-400 transition-all duration-300 group-hover:from-blue-500 group-hover:to-cyan-300"
                style={{ height: `${(item.crimes / maxCrimes) * 100}%` }}
              >
                <span className="absolute -top-6 left-1/2 -translate-x-1/2 rounded bg-gray-800 px-2 py-0.5 text-xs text-white opacity-0 transition-opacity group-hover:opacity-100">
                  {item.crimes}
                </span>
              </div>
            </div>
            <span className="text-xs text-gray-500">{item.month}</span>
          </div>
        ))}
      </div>

      <div className="mt-4 border-t border-gray-800 pt-4">
        <div className="flex items-center gap-6 text-sm text-gray-400">
          <span className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-blue-500" />
            Peak: December ({crimeTrendData[11].crimes} crimes)
          </span>
          <span className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-cyan-400" />
            Average: {Math.round(crimeTrendData.reduce((acc, d) => acc + d.crimes, 0) / crimeTrendData.length)} crimes/month
          </span>
        </div>
      </div>
    </Card>
  )
}

export default CrimeTrendChart