import DataTable from './DataTable'
import StatusBadge from './StatusBadge'

function HotspotsTable({ hotspots }) {
  const columns = [
    {
      key: 'zone',
      label: 'Zone',
      render: (spot) => (
        <div className="flex items-center gap-3">
          <span className={`h-2 w-2 shrink-0 rounded-full ${
            spot.risk === 'Critical' || spot.risk === 'High' ? 'bg-red-500' : spot.risk === 'Medium' ? 'bg-yellow-500' : 'bg-green-500'
          }`} />
          <span className="font-medium text-gray-200">{spot.zone}</span>
        </div>
      ),
    },
    {
      key: 'risk',
      label: 'Risk Level',
      render: (spot) => <StatusBadge status={spot.risk} />,
    },
    { key: 'crimeCount', label: 'Incidents', cellClassName: 'font-medium text-gray-300' },
    { key: 'incidents', label: 'Dominant Crime', cellClassName: 'text-gray-400' },
  ]

  return (
    <DataTable
      columns={columns}
      data={hotspots}
      emptyMessage="No hotspots found matching your search criteria."
    />
  )
}

export default HotspotsTable