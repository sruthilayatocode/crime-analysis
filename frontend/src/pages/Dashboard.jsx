import { useMemo } from 'react'
import StatCard from '../components/StatCard'
import CrimeTrendChart from '../components/CrimeTrendChart'
import HotspotMap from '../components/HotspotMap'
import RecentCrimeReports from '../components/RecentCrimeReports'
import RecentAlerts from '../components/RecentAlerts'
import PageHeader from '../components/PageHeader'
import CrimeTypeDistribution from '../components/CrimeTypeDistribution'
import RiskIntelligence from '../components/RiskIntelligence'
import SeverityInsight from '../components/SeverityInsight'
import AffectedAreas from '../components/AffectedAreas'
import IntelligenceSummary from '../components/IntelligenceSummary'
import AdminSOSLiveAlerts from '../components/AdminSOSLiveAlerts'
import { useCrimeData } from '../hooks/useCrimeData'
import {
  buildKpis,
  trendByYear,
  toHotspotMarker,
  deriveAlerts,
} from '../utils/crimeInsights'
import {
  buildCrimeTypeDistribution,
  buildRiskDistribution,
  buildSeverityInsight,
  buildAffectedAreas,
  buildIntelligenceStatements,
} from '../utils/crimeIntelligence'

function Dashboard() {
  const { crimes, hotspots, loading, error } = useCrimeData()

  const kpis = useMemo(() => buildKpis(crimes), [crimes])
  const trend = useMemo(() => trendByYear(crimes), [crimes])
  const mapMarkers = useMemo(
    () => (Array.isArray(hotspots) ? hotspots : []).map(toHotspotMarker),
    [hotspots]
  )
  const recentAlerts = useMemo(() => deriveAlerts(crimes).slice(0, 5), [crimes])

  // Crime Intelligence Overview calculations (all derived from the live records).
  const crimeTypeDist = useMemo(() => buildCrimeTypeDistribution(crimes), [crimes])
  const riskDist = useMemo(() => buildRiskDistribution(crimes), [crimes])
  const severity = useMemo(() => buildSeverityInsight(crimes), [crimes])
  const affectedAreas = useMemo(() => buildAffectedAreas(crimes), [crimes])
  const intelligence = useMemo(() => buildIntelligenceStatements(crimes), [crimes])

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
      {/* Real-time SOS Alerts Banner */}
      <AdminSOSLiveAlerts />

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
          <StatCard key={stat.id} label={stat.label} value={stat.value}
                    color={stat.color} total={crimes.length} />
        ))}
      </div>

      {/* Chart and Map */}
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <CrimeTrendChart data={trend} loading={loading} error={error} />
        <HotspotMap markers={mapMarkers} />
      </div>

      {/* Crime Intelligence Overview */}
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <CrimeTypeDistribution data={crimeTypeDist} />
        <RiskIntelligence data={riskDist} total={crimes.length} />
      </div>
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <AffectedAreas data={affectedAreas} />
        <SeverityInsight insight={severity} />
      </div>
      <IntelligenceSummary statements={intelligence} total={crimes.length} />

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