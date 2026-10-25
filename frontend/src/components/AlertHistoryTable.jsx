import DataTable from './DataTable'
import StatusBadge from './StatusBadge'
import Card from './Card'
import CardHeader from './CardHeader'

function AlertHistoryTable({ history }) {
  const columns = [
    { key: 'id', label: 'Alert ID', cellClassName: 'font-mono text-xs text-gray-400' },
    { key: 'location', label: 'Location', cellClassName: 'text-gray-300' },
    { key: 'crimeType', label: 'Crime Type', cellClassName: 'text-gray-400' },
    { key: 'time', label: 'Time', cellClassName: 'text-gray-400' },
    {
      key: 'status',
      label: 'Status',
      render: (record) => <StatusBadge status={record.status} />,
    },
  ]

  return (
    <Card>
      <CardHeader title="Alert History" subtitle="Past alert records" />
      <DataTable columns={columns} data={history} />
    </Card>
  )
}

export default AlertHistoryTable