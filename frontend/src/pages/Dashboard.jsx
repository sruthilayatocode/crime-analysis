import { useEffect, useState, useCallback } from 'react'
import StatCard from '../components/StatCard'
import CrimeTrendChart from '../components/CrimeTrendChart'
import MapPlaceholder from '../components/MapPlaceholder'
import RecentCrimeReports from '../components/RecentCrimeReports'
import PageHeader from '../components/PageHeader'
import { useAuth } from '../hooks/useAuth'
import { getStatistics, getAllCrimes, getHotspots } from '../services/api'

function Dashboard() {
  const { user } = useAuth()
  const [stats, setStats] = useState(null)
  const [crimes, setCrimes] = useState([])
  const [hotspots, setHotspots] = useState([])
  const [loading, setLoading] = useState(true)

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const [sRes, cRes, hRes] = await Promise.all([
        getStatistics().catch(() => ({ data: null })),
        getAllCrimes('APPROVED').catch(() => ({ data: [] })),
        getHotspots().catch(() => ({ data: [] })),
      ])
      setStats(sRes?.data || null)
      setCrimes(cRes?.data || [])
      setHotspots(hRes?.data || [])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  const highCount = (stats?.by_severity?.High || 0) + (stats?.by_severity?.Critical || 0)
  const medCount = stats?.by_severity?.Medium || 0

  const liveStats = [
    {
      id: 1,
      label: 'Total Crime Records',
      value: stats?.total_crimes ?? crimes.length,
      change: 'Verified database',
      trend: 'up',
      color: 'blue',
    },
    {
      id: 2,
      label: 'High/Critical Incidents',
      value: highCount,
      change: 'Priority review',
      trend: 'up',
      color: 'red',
    },
    {
      id: 3,
      label: 'Medium Severity',
      value: medCount,
      change: 'Moderate risk',
      trend: 'down',
      color: 'yellow',
    },
    {
      id: 4,
      label: 'Active Hotspots',
      value: hotspots.length,
      change: 'Spatial clusters',
      trend: 'up',
      color: 'green',
    },
  ]

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Crime Intelligence Overview`}
        description={`Statistical analytics and verified crime records for ${user?.name || 'Administrator'}.`}
        badge={
          <div className="flex items-center gap-3">
            <button
              onClick={loadData}
              disabled={loading}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Refreshing...' : 'Refresh Analytics'}
            </button>
          </div>
        }
      />

      {/* Live Stat Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {liveStats.map((stat) => (
          <StatCard key={stat.id} {...stat} />
        ))}
      </div>

      {/* Real Trend Chart and Mini Map */}
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <CrimeTrendChart monthlyData={stats?.by_month} />
        <MapPlaceholder />
      </div>

      {/* Reports and Analytics */}
      <div className="grid grid-cols-1 gap-6">
        <RecentCrimeReports reports={crimes} />
      </div>
    </div>
  )
}

export default Dashboard