import DataTable from './DataTable'
import StatusBadge from './StatusBadge'
import Card from './Card'
import CardHeader from './CardHeader'
import { formatDate } from '../utils/crimeInsights'

function RecentCrimeReports({ crimes = [] }) {
  const columns = [
    { key: 'id', label: 'Report ID', cellClassName: 'font-mono text-xs text-gray-400' },
    { key: 'type', label: 'Type', cellClassName: 'font-medium text-gray-300' },
    { key: 'location', label: 'Location', cellClassName: 'text-gray-400' },
    { key: 'time', label: 'Date', cellClassName: 'text-gray-400' },
    {
      key: 'risk',
      label: 'Risk',
      render: (report) => <StatusBadge status={report.risk} />,
    },
  ]

  const rows = crimes.map((crime) => ({
    id: crime.article_id || '—',
    type: crime.crime_type || 'Unknown',
    location: crime.location_name || crime.district || crime.locality || 'Unknown',
    time: formatDate(crime.published_date),
    risk: crime.risk_level || 'Unknown',
  }))

  return (
    <Card>
      <CardHeader
        title="Recent Crime Reports"
        subtitle="Latest validated incidents"
        action={
          <button className="rounded-lg bg-gray-800 px-3 py-1.5 text-xs font-medium text-gray-400 transition-colors hover:bg-gray-700 hover:text-white">
            View All
          </button>
        }
      />
      <DataTable columns={columns} data={rows} />
    </Card>
  )
}

export default RecentCrimeReports