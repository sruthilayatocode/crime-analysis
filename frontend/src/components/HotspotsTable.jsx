import { Link } from 'react-router-dom'
import DataTable from './DataTable'
import StatusBadge from './StatusBadge'

function HotspotsTable({ hotspots }) {
  const columns = [
    {
      key: 'zone',
      label: 'Zone / Locality',
      render: (spot) => {
        const name = spot.zone || spot.location || 'Unknown Area'
        const risk = spot.risk || spot.risk_level || 'Medium'
        return (
          <div className="flex items-center gap-3">
            <span
              className={`h-2.5 w-2.5 shrink-0 rounded-full ${
                risk === 'High'
                  ? 'bg-red-500'
                  : risk === 'Medium'
                    ? 'bg-yellow-500'
                    : 'bg-green-500'
              }`}
            />
            <span className="font-semibold text-gray-200">{name}</span>
          </div>
        )
      },
    },
    {
      key: 'risk',
      label: 'Risk Level',
      render: (spot) => (
        <StatusBadge status={spot.risk || spot.risk_level || 'Medium'} />
      ),
    },
    {
      key: 'crimeCount',
      label: 'Recorded Crimes',
      cellClassName: 'font-medium text-gray-200',
      render: (spot) => (
        <span className="rounded bg-gray-800/80 px-2.5 py-1 text-xs font-semibold text-gray-300">
          {spot.crimeCount ?? spot.crime_count ?? 0} incidents
        </span>
      ),
    },
    {
      key: 'coordinates',
      label: 'Coordinates',
      cellClassName: 'font-mono text-xs text-gray-400',
      render: (spot) => {
        const lat = spot.lat ?? spot.average_latitude
        const lng = spot.lng ?? spot.average_longitude
        if (lat != null && lng != null) {
          return `${Number(lat).toFixed(4)}, ${Number(lng).toFixed(4)}`
        }
        return spot.region || 'District jurisdiction'
      },
    },
    {
      key: 'action',
      label: 'Action',
      render: (spot) => {
        const lat = spot.lat ?? spot.average_latitude
        const lng = spot.lng ?? spot.average_longitude
        return (
          <Link
            to={lat && lng ? `/map?lat=${lat}&lng=${lng}` : '/map'}
            className="inline-flex items-center gap-1 rounded-lg bg-blue-600/10 border border-blue-500/30 px-2.5 py-1 text-xs font-medium text-blue-400 hover:bg-blue-600/20 hover:text-blue-300"
          >
            <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0zM15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            View Map
          </Link>
        )
      },
    },
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