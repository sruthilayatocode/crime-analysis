import { Link } from 'react-router-dom'
import PageHeader from '../components/PageHeader'
import StatCard from '../components/StatCard'
import Card from '../components/Card'
import CardHeader from '../components/CardHeader'
import CrimeTrendChart from '../components/CrimeTrendChart'
import RecentAlerts from '../components/RecentAlerts'
import CurrentLocationCard from '../components/CurrentLocationCard'
import SafetyStatusCard from '../components/SafetyStatusCard'
import NearestHotspotCard from '../components/NearestHotspotCard'
import { useAuth } from '../hooks/useAuth'
import { alertSummary } from '../data/alertsData'
import { accountStats } from '../data/profileData'
import {
  currentLocation,
  nearbyCrimeSummary,
  nearestHotspot,
  safetyStatus,
} from '../data/gpsData'
import { hotspots } from '../data/hotspotsData'

const quickLinks = [
  { to: '/map', label: 'Interactive Map', description: 'Explore crime hotspots around you' },
  { to: '/gps-tracking', label: 'GPS Tracking', description: 'Monitor your live location' },
  { to: '/alerts', label: 'My Alerts', description: 'Review recent safety notifications' },
  { to: '/crime-hotspots', label: 'Crime Hotspots', description: 'Browse high-risk zones' },
  { to: '/profile', label: 'Profile', description: 'Manage your account details' },
]

function UserDashboard() {
  const { user } = useAuth()

  const personalStats = [
    {
      id: 1,
      label: 'Nearby Crimes',
      value: nearbyCrimeSummary.totalCrimes,
      change: '-12%',
      trend: 'down',
      color: 'red',
    },
    {
      id: 2,
      label: 'High Priority Alerts',
      value: alertSummary.high,
      change: '+2',
      trend: 'up',
      color: 'yellow',
    },
    {
      id: 3,
      label: 'Reports Viewed',
      value: accountStats.crimeReportsViewed,
      change: '+18',
      trend: 'up',
      color: 'blue',
    },
    {
      id: 4,
      label: 'Tracked Zones',
      value: hotspots.length,
      change: '+3',
      trend: 'down',
      color: 'green',
    },
  ]

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Welcome back, ${user?.name || 'Citizen'}`}
        description="Your personal safety overview with nearby risks and recent alerts."
        badge={
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-gray-800/50 px-4 py-2">
              <p className="text-xs text-gray-500">Role</p>
              <p className="text-sm font-medium text-blue-400">User</p>
            </div>
            <div className="rounded-lg bg-gray-800/50 px-4 py-2">
              <p className="text-xs text-gray-500">Last Login</p>
              <p className="text-sm font-medium text-gray-300">{accountStats.lastLogin}</p>
            </div>
          </div>
        }
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {personalStats.map((stat) => (
          <StatCard key={stat.id} {...stat} />
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <CurrentLocationCard location={currentLocation} />
        <SafetyStatusCard safety={safetyStatus} />
        <NearestHotspotCard hotspot={nearestHotspot} />
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <CrimeTrendChart />
        <RecentAlerts />
      </div>

      <Card>
        <CardHeader
          title="Quick Actions"
          subtitle="Jump straight to the tools you use most"
          icon="M13 10V3L4 14h7v7l9-11h-7z"
        />

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {quickLinks.map((link) => (
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
    </div>
  )
}

export default UserDashboard
