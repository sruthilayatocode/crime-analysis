import StatusBadge from './StatusBadge'
import Card from './Card'
import CardHeader from './CardHeader'

function NearestHotspotCard({ hotspot }) {
  return (
    <Card>
      <CardHeader
        title="Nearest Crime Hotspot"
        subtitle="Closest risk zone to you"
        icon="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0zM15 11a3 3 0 11-6 0 3 3 0 016 0z"
        iconBg="bg-red-500/20"
        iconColor="text-red-400"
      />

      <div className="space-y-3">
        <div>
          <p className="text-xs text-gray-500">Hotspot Name</p>
          <p className="text-lg font-semibold text-gray-200">{hotspot.name}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Crime Type</p>
          <p className="text-sm text-gray-300">{hotspot.crimeType}</p>
        </div>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs text-gray-500">Distance</p>
            <p className="text-lg font-bold text-blue-400">{hotspot.distance} km</p>
          </div>
          <div>
            <p className="mb-1 text-xs text-gray-500">Risk Level</p>
            <StatusBadge status={hotspot.risk} />
          </div>
        </div>
      </div>
    </Card>
  )
}

export default NearestHotspotCard