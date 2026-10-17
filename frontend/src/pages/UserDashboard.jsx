import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import PageHeader from '../components/PageHeader'
import StatCard from '../components/StatCard'
import Card from '../components/Card'
import CardHeader from '../components/CardHeader'
import StatusBadge from '../components/StatusBadge'
import MapPlaceholder from '../components/MapPlaceholder'
import CrimeTrendChart from '../components/CrimeTrendChart'
import { useAuth } from '../hooks/useAuth'
import { getMyReports, getStatistics, getHotspots } from '../services/api'

const quickLinks = [
  { to: '/report-crime', label: 'Report Incident', description: 'Submit a new crime report for verification', primary: true },
  { to: '/my-reports', label: 'My Reports', description: 'Check approval status and admin notes' },
  { to: '/map', label: 'Interactive Map', description: 'Explore verified crime hotspots in Vellore' },
  { to: '/gps-tracking', label: 'GPS Safety Check', description: 'Live location monitoring and proximity alerts' },
  { to: '/alerts', label: 'Safety Alerts', description: 'Review high-severity local advisories' },
  { to: '/profile', label: 'My Profile', description: 'Manage account details and preferences' },
]

function UserDashboard() {
  const { user, token } = useAuth()

  const [myReports, setMyReports] = useState([])
  const [stats, setStats] = useState(null)
  const [hotspots, setHotspots] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadData = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [reportsRes, statsRes, hotspotsRes] = await Promise.all([
        getMyReports(token).catch(() => ({ data: [] })),
        getStatistics().catch(() => ({ data: null })),
        getHotspots().catch(() => ({ data: [] })),
      ])

      setMyReports(reportsRes?.data || [])
      setStats(statsRes?.data || null)
      setHotspots(hotspotsRes?.data || [])
    } catch (err) {
      setError(err.message || 'Unable to load citizen dashboard data.')
    } finally {
      setLoading(false)
    }
  }, [token])

  useEffect(() => {
    loadData()
  }, [loadData])

  const pendingCount = myReports.filter((r) => r.status === 'PENDING').length
  const approvedCount = myReports.filter((r) => r.status === 'APPROVED').length

  const personalStats = [
    {
      id: 'my-reports',
      label: 'My Submitted Reports',
      value: myReports.length,
      change: pendingCount > 0 ? `${pendingCount} pending` : 'All reviewed',
      trend: pendingCount > 0 ? 'up' : 'down',
      color: 'blue',
    },
    {
      id: 'approved-reports',
      label: 'Approved Incidents',
      value: approvedCount,
      change: 'Active on map',
      trend: 'up',
      color: 'green',
    },
    {
      id: 'area-crimes',
      label: 'Verified Area Incidents',
      value: stats?.total_crimes ?? 0,
      change: 'Vellore jurisdiction',
      trend: 'down',
      color: 'red',
    },
    {
      id: 'hotspots-detected',
      label: 'Active Hotspot Zones',
      value: hotspots.length,
      change: 'DBSCAN clusters',
      trend: 'up',
      color: 'yellow',
    },
  ]

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Welcome, ${user?.name || 'Citizen'}`}
        description="Your personal safety overview, submitted incident statuses, and local crime alerts."
        badge={
          <div className="flex items-center gap-3">
            <Link
              to="/report-crime"
              className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-xs font-semibold text-white shadow-lg shadow-blue-600/20 transition-colors hover:bg-blue-700"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
              </svg>
              Report Incident
            </Link>
            <button
              onClick={loadData}
              className="rounded-lg bg-gray-800 px-3 py-2 text-xs font-medium text-gray-300 hover:bg-gray-700"
              title="Refresh dashboard"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
          </div>
        }
      />

      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* Citizen Submission Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {personalStats.map((stat) => (
          <StatCard key={stat.id} {...stat} />
        ))}
      </div>

      {/* Spatial Overview Mini Map and Incident Trends */}
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <MapPlaceholder />
        <CrimeTrendChart monthlyData={stats?.by_month} />
      </div>

      {/* Quick Actions Grid */}
      <Card>
        <CardHeader
          title="Quick Actions & Safety Tools"
          subtitle="Direct shortcuts to crime reporting and spatial monitoring"
          icon="M13 10V3L4 14h7v7l9-11h-7z"
        />

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {quickLinks.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              className={`rounded-lg border p-4 transition-all ${
                link.primary
                  ? 'border-blue-500/40 bg-blue-600/10 hover:bg-blue-600/20'
                  : 'border-gray-800 bg-gray-800/30 hover:border-gray-700 hover:bg-gray-800/60'
              }`}
            >
              <p className={`text-sm font-semibold ${link.primary ? 'text-blue-300' : 'text-gray-200'}`}>
                {link.label}
              </p>
              <p className="mt-1 text-xs text-gray-500">{link.description}</p>
            </Link>
          ))}
        </div>
      </Card>

      {/* My Recent Submitted Reports */}
      <Card>
        <CardHeader
          title="My Recent Incident Reports"
          subtitle="Verification tracking for reports submitted from your account"
          icon="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          action={
            <Link
              to="/my-reports"
              className="text-xs font-semibold text-blue-400 hover:text-blue-300"
            >
              View All ({myReports.length})
            </Link>
          }
        />

        {loading ? (
          <p className="py-8 text-center text-sm text-gray-500">Loading your submissions...</p>
        ) : myReports.length === 0 ? (
          <div className="py-8 text-center">
            <p className="text-sm text-gray-400">You have not submitted any crime incidents yet.</p>
            <p className="mt-1 text-xs text-gray-500">
              Help your community stay safe by reporting witnessed incidents with locality or GPS coordinates.
            </p>
            <Link
              to="/report-crime"
              className="mt-4 inline-block rounded-lg bg-blue-600 px-4 py-2 text-xs font-semibold text-white hover:bg-blue-700"
            >
              Report Your First Incident
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-gray-800">
            {myReports.slice(0, 4).map((report) => (
              <div key={report.id} className="py-3.5 first:pt-0 last:pb-0 flex items-center justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs text-gray-500">#{report.id}</span>
                    <span className="text-sm font-semibold text-gray-200">{report.crime_type}</span>
                    <StatusBadge status={report.status} />
                  </div>
                  <p className="mt-1 text-xs text-gray-400 line-clamp-1">{report.description}</p>
                  <p className="mt-0.5 text-[11px] text-gray-500">
                    {report.location_name || 'Vellore'} &bull; {report.crime_date || '-'}
                  </p>
                </div>
                <Link
                  to="/my-reports"
                  className="shrink-0 text-xs text-blue-400 hover:text-blue-300 font-medium"
                >
                  Details &rarr;
                </Link>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}

export default UserDashboard
