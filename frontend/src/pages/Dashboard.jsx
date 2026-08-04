import StatCard from '../components/StatCard'
import CrimeTrendChart from '../components/CrimeTrendChart'
import MapPlaceholder from '../components/MapPlaceholder'
import RecentCrimeReports from '../components/RecentCrimeReports'
import RecentAlerts from '../components/RecentAlerts'
import PageHeader from '../components/PageHeader'
import { stats } from '../data/dashboardData'

function Dashboard() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Welcome back, Admin"
        description="Here's what's happening with crime hotspots and alerts today."
        badge={
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-gray-800/50 px-4 py-2">
              <p className="text-xs text-gray-500">Last Updated</p>
              <p className="text-sm font-medium text-gray-300">Dec 15, 2024 14:32</p>
            </div>
            <button className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700">
              Generate Report
            </button>
          </div>
        }
      />

      {/* Stat Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <StatCard key={stat.id} {...stat} />
        ))}
      </div>

      {/* Chart and Map */}
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <CrimeTrendChart />
        <MapPlaceholder />
      </div>

      {/* Reports and Alerts */}
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <div className="xl:col-span-2">
          <RecentCrimeReports />
        </div>
        <RecentAlerts />
      </div>
    </div>
  )
}

export default Dashboard