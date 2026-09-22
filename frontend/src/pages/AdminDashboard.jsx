import { Link } from 'react-router-dom'
import PageHeader from '../components/PageHeader'
import StatCard from '../components/StatCard'
import Card from '../components/Card'
import CardHeader from '../components/CardHeader'
import StatusBadge from '../components/StatusBadge'
import CrimeTrendChart from '../components/CrimeTrendChart'
import MapPlaceholder from '../components/MapPlaceholder'
import RecentCrimeReports from '../components/RecentCrimeReports'
import RecentAlerts from '../components/RecentAlerts'
import { useAuth } from '../hooks/useAuth'
import { stats } from '../data/dashboardData'
import { hotspots } from '../data/hotspotsData'

const adminLinks = [
  { to: '/dashboard', label: 'Full Crime Dashboard', description: 'Statistics, trends and reports' },
  { to: '/crime-hotspots', label: 'Hotspot Management', description: 'Review and filter detected zones' },
  { to: '/map', label: 'Interactive Map', description: 'Spatial view of every hotspot' },
  { to: '/alerts', label: 'Alert Centre', description: 'Monitor and triage notifications' },
  { to: '/gps-tracking', label: 'GPS Monitoring', description: 'Live location and proximity checks' },
  { to: '/admin/users', label: 'Manage Users', description: 'Review accounts and change roles' },
  { to: '/profile', label: 'Account Settings', description: 'Administrator profile and preferences' },
]

const topRiskZones = [...hotspots].sort((a, b) => b.crimeCount - a.crimeCount).slice(0, 5)

function AdminDashboard() {
  const { user } = useAuth()

  return (
    <div className="space-y-6">
      <PageHeader
        title="Administrator Console"
        description={`Signed in as ${user?.name || 'Administrator'} - system-wide crime intelligence and administration.`}
        badge={
          <div className="flex items-center gap-3">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-blue-500/30 bg-blue-500/10 px-3 py-1 text-xs font-medium text-blue-400">
              <span className="h-1.5 w-1.5 rounded-full bg-blue-400" />
              ADMIN
            </span>
            <Link
              to="/dashboard"
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
            >
              Open Reports
            </Link>
          </div>
        }
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <StatCard key={stat.id} {...stat} />
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <CrimeTrendChart />
        <MapPlaceholder />
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <div className="xl:col-span-2">
          <RecentCrimeReports />
        </div>
        <RecentAlerts />
      </div>

      <Card>
        <CardHeader
          title="Administration"
          subtitle="Privileged tools available to administrators only"
          icon="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
        />

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {adminLinks.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              className="rounded-lg border border-gray-800 bg-gray-800/30 p-4 transition-colors hover:border-blue-500/40 hover:bg-gray-800/60"
            >
              <p className="text-sm font-medium text-gray-200">{link.label}</p>
              <p className="mt-1 text-xs text-gray-500">{link.description}</p>
            </Link>
          ))}
        </div>
      </Card>

      <Card>
        <CardHeader
          title="Highest Risk Zones"
          subtitle="Top five zones by recorded incidents"
          icon="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          iconBg="bg-red-500/20"
          iconColor="text-red-400"
        />

        <div className="space-y-3">
          {topRiskZones.map((zone) => (
            <div
              key={zone.id}
              className="flex items-center justify-between rounded-lg border border-gray-800 bg-gray-800/30 p-4"
            >
              <div>
                <p className="text-sm font-medium text-gray-200">{zone.zone}</p>
                <p className="mt-0.5 text-xs text-gray-500">
                  {zone.region} region - {zone.incidents}
                </p>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-sm font-semibold text-gray-300">{zone.crimeCount}</span>
                <StatusBadge status={zone.risk} />
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}

export default AdminDashboard
