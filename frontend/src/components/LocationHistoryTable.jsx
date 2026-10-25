import DataTable from './DataTable'
import StatusBadge from './StatusBadge'
import Card from './Card'
import CardHeader from './CardHeader'

function LocationHistoryTable({ history }) {
  const columns = [
    { key: 'time', label: 'Time', cellClassName: 'font-mono text-gray-300' },
    { key: 'latitude', label: 'Latitude', cellClassName: 'font-mono text-gray-400' },
    { key: 'longitude', label: 'Longitude', cellClassName: 'font-mono text-gray-400' },
    {
      key: 'status',
      label: 'Status',
      render: (record) => <StatusBadge status={record.status} />,
    },
  ]

  return (
    <Card>
      <CardHeader
        title="Recent Location History"
        subtitle="Your GPS tracking records"
        action={
          <button className="rounded-lg bg-gray-800 px-3 py-1.5 text-xs font-medium text-gray-400 transition-colors hover:bg-gray-700 hover:text-white">
            View All
          </button>
        }
      />
      <DataTable columns={columns} data={history} />
    </Card>
  )
}

export default LocationHistoryTable