import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import PageHeader from '../components/PageHeader'
import StatCard from '../components/StatCard'
import Card from '../components/Card'
import CardHeader from '../components/CardHeader'
import StatusBadge from '../components/StatusBadge'
import CrimeTrendChart from '../components/CrimeTrendChart'
import MapPlaceholder from '../components/MapPlaceholder'
import RecentCrimeReports from '../components/RecentCrimeReports'
import { useAuth } from '../hooks/useAuth'
import {
  getStatistics,
  getPendingReports,
  getAllCrimes,
  getHotspots,
} from '../services/api'

const adminLinks = [
  { to: '/admin/approvals', label: 'Pending Approvals', description: 'Review and triage citizen incident reports' },
  { to: '/admin/crimes', label: 'Crime Records', description: 'Browse and filter verified crime records' },
  { to: '/crime-hotspots', label: 'Hotspot Analysis', description: 'Cluster detection and high-risk zones' },
  { to: '/map', label: 'Interactive Map', description: 'Spatial GIS view of every hotspot and pin' },
  { to: '/admin/users', label: 'Manage Users', description: 'Review user accounts and change roles' },
  { to: '/alerts', label: 'Alert Center', description: 'Monitor high-severity community alerts' },
]

function AdminDashboard() {
  const { user, token } = useAuth()

  const [stats, setStats] = useState(null)
  const [pendingReports, setPendingReports] = useState([])
  const [approvedCrimes, setApprovedCrimes] = useState([])
  const [hotspots, setHotspots] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadDashboardData = useCallback(async () => {
    setLoading(true)
    setError('')

    try {
      const [statsRes, pendingRes, crimesRes, hotspotsRes] = await Promise.all([
        getStatistics().catch(() => ({ data: null })),
        getPendingReports(token).catch(() => ({ data: [] })),
        getAllCrimes('APPROVED').catch(() => ({ data: [] })),
        getHotspots().catch(() => ({ data: [] })),
      ])

      setStats(statsRes?.data || null)
      setPendingReports(pendingRes?.data || [])
      setApprovedCrimes(crimesRes?.data || [])
      setHotspots(hotspotsRes?.data || [])
    } catch (err) {
      setError(err.message || 'Failed to load administrator dashboard data.')
    } finally {
      setLoading(false)
    }
  }, [token])

  useEffect(() => {
    loadDashboardData()
  }, [loadDashboardData])

  const highSeverityCount =
    (stats?.by_severity?.High || 0) +
    (stats?.by_severity?.Critical || 0)

  const statCards = [
    {
      id: 'total-crimes',
      label: 'Verified Crime Records',
      value: stats?.total_crimes ?? approvedCrimes.length,
      change: 'Active DB',
      trend: 'up',
      color: 'blue',
    },
    {
      id: 'pending-triage',
      label: 'Pending Incident Approvals',
      value: pendingReports.length,
      change: pendingReports.length > 0 ? 'Requires action' : 'Queue clear',
      trend: pendingReports.length > 0 ? 'up' : 'down',
      color: pendingReports.length > 0 ? 'yellow' : 'green',
    },
    {
      id: 'high-severity',
      label: 'High/Critical Incidents',
      value: highSeverityCount,
      change: 'Jurisdiction',
      trend: 'down',
      color: 'red',
    },
    {
      id: 'hotspot-clusters',
      label: 'Detected Hotspot Zones',
      value: hotspots.length,
      change: 'Vellore area',
      trend: 'up',
      color: 'green',
    },
  ]

  const topRiskZones = [...hotspots]
    .sort((a, b) => (b.crime_count || b.crimeCount || 0) - (a.crime_count || a.crimeCount || 0))
    .slice(0, 5)

  return (
    <div className="space-y-6">
      <PageHeader
        title="Administrator Console"
        description={`Signed in as ${user?.name || 'Administrator'} — system-wide crime intelligence and verification triage.`}
        badge={
          <div className="flex items-center gap-3">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-blue-500/30 bg-blue-500/10 px-3 py-1 text-xs font-semibold text-blue-400">
              <span className="h-1.5 w-1.5 rounded-full bg-blue-400" />
              ADMIN PRIVILEGES
            </span>
            <button
              onClick={loadDashboardData}
              disabled={loading}
              className="rounded-lg bg-gray-800 px-3.5 py-1.5 text-xs font-medium text-gray-300 transition-colors hover:bg-gray-700 hover:text-white flex items-center gap-1.5 disabled:opacity-50"
            >
              <svg className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              {loading ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>
        }
      />

      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* Alert banner if pending approvals exist */}
      {pendingReports.length > 0 && (
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-xl border border-yellow-500/30 bg-yellow-500/10 p-4">
          <div className="flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-yellow-500/20 text-yellow-400">
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </span>
            <div>
              <p className="text-sm font-bold text-yellow-300">
                {pendingReports.length} Citizen Crime Report{pendingReports.length === 1 ? '' : 's'} Awaiting Verification
              </p>
              <p className="text-xs text-yellow-400/80">
                Unreviewed citizen reports do not enter hotspot analysis until approved.
              </p>
            </div>
          </div>
          <Link
            to="/admin/approvals"
            className="inline-flex items-center justify-center rounded-lg bg-yellow-500 px-4 py-2 text-xs font-bold text-gray-950 transition-colors hover:bg-yellow-400"
          >
            Review Reports Queue
          </Link>
        </div>
      )}

      {/* Live Stat Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {statCards.map((stat) => (
          <StatCard key={stat.id} {...stat} />
        ))}
      </div>

      {/* Monthly Chart and Real Mini Map */}
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <CrimeTrendChart monthlyData={stats?.by_month} />
        <MapPlaceholder />
      </div>

      {/* Live Recent Reports */}
      <div className="grid grid-cols-1 gap-6">
        <RecentCrimeReports reports={approvedCrimes} />
      </div>

      {/* Admin Quick Tool Shortcuts */}
      <Card>
        <CardHeader
          title="Administrative Tools"
          subtitle="Privileged functions available to administrators only"
          icon="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
        />

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {adminLinks.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              className="rounded-lg border border-gray-800 bg-gray-800/30 p-4 transition-colors hover:border-blue-500/40 hover:bg-gray-800/60"
            >
              <p className="text-sm font-semibold text-gray-200">{link.label}</p>
              <p className="mt-1 text-xs text-gray-500">{link.description}</p>
            </Link>
          ))}
        </div>
      </Card>

      {/* Top 5 Hotspot Zones by Volume */}
      <Card>
        <CardHeader
          title="Highest Incident Hotspot Zones"
          subtitle="Top localities ranked by recorded crime frequency"
          icon="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          iconBg="bg-red-500/20"
          iconColor="text-red-400"
          action={
            <Link
              to="/crime-hotspots"
              className="rounded-lg bg-gray-800 px-3 py-1.5 text-xs font-medium text-gray-300 hover:bg-gray-700"
            >
              View All Hotspots
            </Link>
          }
        />

        {topRiskZones.length === 0 ? (
          <p className="py-6 text-center text-sm text-gray-500">
            No hotspot clusters recorded in the database yet.
          </p>
        ) : (
          <div className="space-y-3">
            {topRiskZones.map((zone, idx) => {
              const name = zone.location || zone.zone || 'Unknown Zone'
              const count = zone.crime_count || zone.crimeCount || 0
              const risk = zone.risk_level || zone.risk || 'Medium'
              const lat = zone.average_latitude ?? zone.lat
              const lng = zone.average_longitude ?? zone.lng

              return (
                <div
                  key={idx}
                  className="flex items-center justify-between rounded-lg border border-gray-800 bg-gray-800/30 p-4"
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs text-gray-500">#{idx + 1}</span>
                      <p className="text-sm font-bold text-gray-200">{name}</p>
                    </div>
                    <p className="mt-0.5 text-xs text-gray-500">
                      {lat && lng ? `${Number(lat).toFixed(4)}, ${Number(lng).toFixed(4)}` : 'Vellore District Area'}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="rounded bg-gray-900 px-2.5 py-1 font-mono text-xs font-semibold text-gray-300">
                      {count} incidents
                    </span>
                    <StatusBadge status={risk} />
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </Card>
    </div>
  )
}

export default AdminDashboard
