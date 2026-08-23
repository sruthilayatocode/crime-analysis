import { useMemo } from 'react'
import StatCard from '../components/StatCard'
import CrimeTrendChart from '../components/CrimeTrendChart'
import HotspotMap from '../components/HotspotMap'
import RecentCrimeReports from '../components/RecentCrimeReports'
import RecentAlerts from '../components/RecentAlerts'
import PageHeader from '../components/PageHeader'
import { useCrimeData } from '../hooks/useCrimeData'
import {
  buildKpis,
  trendByYear,
  countByCrimeType,
  toHotspotMarker,
  deriveAlerts,
} from '../utils/crimeInsights'

function Dashboard() {
  const { crimes, hotspots, loading, error } = useCrimeData()

  const kpis = useMemo(() => buildKpis(crimes), [crimes])
  const trend = useMemo(() => trendByYear(crimes), [crimes])
  const crimeTypes = useMemo(() => countByCrimeType(crimes), [crimes])
  const mapMarkers = useMemo(
    () => (Array.isArray(hotspots) ? hotspots : []).map(toHotspotMarker),
    [hotspots]
  )
  const recentAlerts = useMemo(() => deriveAlerts(crimes).slice(0, 5), [crimes])

  if (loading) {
    return (
      <div className="space-y-6">
        <PageHeader title="Loading Dashboard" description="Fetching validated crime data from the backend..." />
        <p className="py-12 text-center text-sm text-gray-500">Loading crime data&hellip;</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <PageHeader title="Dashboard Unavailable" description="Could not reach the CrimeSense API." />
        <p className="py-12 text-center text-sm text-gray-400">{error}</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Welcome back, Admin"
        description="Live statistics computed from the validated CrimeSense dataset."
        badge={
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-gray-800/50 px-4 py-2">
              <p className="text-xs text-gray-500">Data</p>
              <p className="text-sm font-medium text-gray-300">{crimes.length} validated incidents</p>
            </div>
            <button className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700">
              Generate Report
            </button>
          </div>
        }
      />

      {/* Stat Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {kpis.map((stat) => (
          <StatCard key={stat.id} label={stat.label} value={stat.value} color={stat.color} />
        ))}
      </div>

      {/* Chart and Map */}
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <CrimeTrendChart data={trend} />
        <HotspotMap markers={mapMarkers} />
      </div>

      {/* Crime type distribution */}
      <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-6">
        <h2 className="text-lg font-semibold text-white">Crime Type Distribution</h2>
        <p className="text-sm text-gray-500">Incidents grouped by crime_type from the API records</p>
        <div className="mt-4 flex flex-wrap gap-2">
          {crimeTypes.map((item) => (
            <span
              key={item.label}
              className="rounded-lg border border-gray-800 bg-gray-800/40 px-3 py-1.5 text-sm text-gray-300"
            >
              <span className="font-medium text-white">{item.count}</span> {item.label}
            </span>
          ))}
        </div>
      </div>

      {/* Reports and Alerts */}
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <div className="xl:col-span-2">
          <RecentCrimeReports crimes={crimes.slice(0, 6)} />
        </div>
        <RecentAlerts alerts={recentAlerts} />
      </div>
    </div>
  )
}

export default Dashboard