import { Link } from 'react-router-dom'
import DataTable from './DataTable'
import StatusBadge from './StatusBadge'
import Card from './Card'
import CardHeader from './CardHeader'
import { recentCrimeReports as defaultReports } from '../data/dashboardData'

function RecentCrimeReports({ reports = null }) {
  const displayReports = reports && reports.length > 0 ? reports.slice(0, 6) : defaultReports

  const columns = [
    {
      key: 'id',
      label: 'ID',
      cellClassName: 'font-mono text-xs text-gray-400',
      render: (report) => `#${report.id}`,
    },
    {
      key: 'type',
      label: 'Incident Type',
      cellClassName: 'font-semibold text-gray-200',
      render: (report) => report.type || report.crime_type || 'Incident',
    },
    {
      key: 'location',
      label: 'Locality',
      cellClassName: 'text-gray-300',
      render: (report) => report.location || report.location_name || 'Vellore',
    },
    {
      key: 'time',
      label: 'Date / Time',
      cellClassName: 'text-xs text-gray-400',
      render: (report) => report.time || report.crime_date || '-',
    },
    {
      key: 'status',
      label: 'Status',
      render: (report) => <StatusBadge status={report.status || 'APPROVED'} />,
    },
    {
      key: 'risk',
      label: 'Severity',
      render: (report) => <StatusBadge status={report.risk || report.severity || 'Medium'} />,
    },
  ]

  return (
    <Card>
      <CardHeader
        title="Recent Verified Incidents"
        subtitle="Latest crime reports in jurisdiction"
        action={
          <Link
            to="/admin/crimes"
            className="rounded-lg bg-gray-800 px-3 py-1.5 text-xs font-medium text-gray-300 transition-colors hover:bg-gray-700 hover:text-white"
          >
            View All Records
          </Link>
        }
      />
      <DataTable
        columns={columns}
        data={displayReports}
        emptyMessage="No recent incidents to display."
      />
    </Card>
  )
}

export default RecentCrimeReports