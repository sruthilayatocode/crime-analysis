import Card from './Card'
import CardHeader from './CardHeader'

function CurrentLocationCard({ location }) {
  return (
    <Card>
      <CardHeader
        title="Current Location"
        subtitle="Your real-time GPS position"
        icon="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0zM15 11a3 3 0 11-6 0 3 3 0 016 0z"
      />

      <div className="grid grid-cols-2 gap-4">
        <div className="rounded-lg bg-gray-800/50 p-4">
          <p className="text-xs text-gray-500">Latitude</p>
          <p className="mt-1 font-mono text-lg font-semibold text-blue-400">
            {location.latitude.toFixed(4)}
          </p>
        </div>
        <div className="rounded-lg bg-gray-800/50 p-4">
          <p className="text-xs text-gray-500">Longitude</p>
          <p className="mt-1 font-mono text-lg font-semibold text-blue-400">
            {location.longitude.toFixed(4)}
          </p>
        </div>
        <div className="rounded-lg bg-gray-800/50 p-4">
          <p className="text-xs text-gray-500">Accuracy</p>
          <p className="mt-1 text-lg font-semibold text-gray-300">
            ±{location.accuracy} m
          </p>
        </div>
        <div className="rounded-lg bg-gray-800/50 p-4">
          <p className="text-xs text-gray-500">Last Updated</p>
          <p className="mt-1 text-sm font-semibold text-gray-300">
            {location.lastUpdated}
          </p>
        </div>
      </div>
    </Card>
  )
}

export default CurrentLocationCard