import DataTable from './DataTable'
import StatusBadge from './StatusBadge'
import Card from './Card'
import CardHeader from './CardHeader'
import { recentCrimeReports } from '../data/dashboardData'

function RecentCrimeReports() {
  const columns = [
    { key: 'id', label: 'Report ID', cellClassName: 'font-mono text-xs text-gray-400' },
    { key: 'type', label: 'Type', cellClassName: 'font-medium text-gray-300' },
    { key: 'location', label: 'Location', cellClassName: 'text-gray-400' },
    { key: 'time', label: 'Time', cellClassName: 'text-gray-400' },
    {
      key: 'status',
      label: 'Status',
      render: (report) => <StatusBadge status={report.status} />,
    },
    {
      key: 'risk',
      label: 'Risk',
      render: (report) => <StatusBadge status={report.risk} />,
    },
  ]

  return (
    <Card>
      <CardHeader
        title="Recent Crime Reports"
        subtitle="Latest reported incidents"
        action={
          <button className="rounded-lg bg-gray-800 px-3 py-1.5 text-xs font-medium text-gray-400 transition-colors hover:bg-gray-700 hover:text-white">
            View All
          </button>
        }
      />
      <DataTable columns={columns} data={recentCrimeReports} />
    </Card>
  )
}

export default RecentCrimeReports